from loguru import logger
import os, sys
from dotenv import load_dotenv
from utils.json_rpc_client import JsonRpcClient
from eth_account import Account
from web3 import Web3
import time
import configparser

import pytest
import secrets
from utils.slack_report import send_to_slack
import json
from pathlib import Path

def create_transaction_if_not_exist(client, ensure_transaction):
    hash = ["latest", True]
    block = client.call("eth_getBlockByNumber", hash)
    if len(block['result']['transactions']) == 0:
        tr = ensure_transaction()
        hash = [tr, True]
        block = client.call("eth_getBlockByHash", hash)
    while block['result'] is None or len(block['result']['transactions']) == 0:
        time.sleep(5)
        block = client.call("eth_getBlockByHash", hash)
    return block['result']

def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="general",
        help="Environment to run tests against")

def pytest_unconfigure(config):
    try:
        ini_config = config.configuration 
        if bool(int(ini_config.get("send_slack_webhook"))):
            logger.info(f"slack_notify_only_failed: {bool(int(ini_config.get('slack_notify_only_failed')))}")
            send_to_slack(
                webhook_url=ini_config.get("slack_webhook_link"), 
                description=f"Daily run for {config.env_name.upper()} network", 
                post_only_failed=bool(int(ini_config.get("slack_notify_only_failed"))), 
                job_url=ini_config.get("ci_job_url"),
                report_name=ini_config.get("json_report"))

    except AttributeError:
        print("Make sure to use configuration fixture")

@pytest.fixture(scope="session")
def configuration(request):
    env = request.config.getoption("--env")
    cfg = configparser.ConfigParser()
    cfg.read("pytest.ini")
    logger.info(f"Environment: {env}")
    if env not in cfg:
        # workaround for running tests inside docker
        cfg.read("../pytest.ini")
        if env not in cfg:
            raise ValueError(f"Invalid environment: {env}")
    for k, v in cfg["general"].items():
        if k not in cfg[env]:
            cfg[env][k] = v
    # read from .env file
    load_dotenv()
    for k, v in os.environ.items():
        for key in cfg[env].keys():
            # to store variables like GENERAL_BASE_URL
            if str(k).lower().startswith(f"{env}_"):
                cfg[env][str(k).lower().replace(f"{env}_", "")] = v
            if str(k).lower() == str(key).lower():
                cfg[env][str(k).lower()] = v
    # manky patching to pass config to teardown step
    request.config.configuration = cfg[env]
    request.config.env_name = env
    cfg[env]["env_name"] = env
    cfg[env].context = {}
    logger.remove()
    # Use enqueue=False to prevent buffering but remove flush parameter
    logger.add(sys.stdout, level=cfg[env]['log_stdout_level'], enqueue=False)
    logger.add(f"reports/{cfg[env]['log_file_name']}.log", level=cfg[env]['log_file_level'], enqueue=False)
    logger.debug("Updated configuration ...")
    logger.debug(f"Base URL: {cfg[env]['base_url']}")
    return cfg[env]

@pytest.fixture(scope="session")
def client(configuration) -> JsonRpcClient:
    cl = JsonRpcClient(configuration["base_url"])
    return cl

@pytest.fixture(scope="session")
def generate_ethereum_account():
    # Generate a random private key
    private_key = "0x" + secrets.token_hex(32)

    # Create an account from the private key
    account = Account.from_key(private_key)

    # Get the public key (address)
    public_key = account.address
    print("New Ethereum Account Generated:")
    print(f"Private Key: {private_key}")
    print(f"Public Key (Address): {public_key}")

    return {
        "private_key": private_key,
        "public_key": public_key
    }


@pytest.fixture(scope="session")
def create_transaction(client: JsonRpcClient, configuration):
    def _create_transaction():
        web3_client: Web3 = client.web3 # type: ignore
        # Use the first account from the node as the funding account
        funding_account_address = configuration["public_key"]
        funding_balance = web3_client.eth.get_balance(funding_account_address)

        if funding_balance == 0:
            raise ValueError(f"Funding account {funding_account_address} has no balance. Please ensure there's an account with funds.")

        # Generate a random private key for the transaction account
        private_key = "0x" + secrets.token_hex(32)
        account = Account.from_key(private_key)

        # Create a funding transaction
        funding_tx = {
            'to': account.address,
            'value': web3_client.to_wei(0.001, 'ether'),
            'gas': 21000,
            'gasPrice': web3_client.eth.gas_price,
            # Nonce will be set in the retry loop
            # 'nonce': web3_client.eth.get_transaction_count(funding_account_address),
            'chainId': web3_client.eth.chain_id,
        }

        # Sign the funding transaction (you'll need the private key of the funding account)
        funding_account_private_key = configuration["private_key"]  # Replace with actual private key
        # signed_funding_tx = Account.sign_transaction(funding_tx, funding_account_private_key)

        # Send the signed funding transaction
        # funding_tx_hash = web3_client.eth.send_raw_transaction(signed_funding_tx.raw_transaction)
        
        # Attempt to send the funding transaction with retries on nonce issues
        max_attempts = 5
        attempt = 0
        funding_tx_hash = None
        last_exception = None
        while attempt < max_attempts:
            try:
                current_nonce = web3_client.eth.get_transaction_count(funding_account_address)
                funding_tx['nonce'] = current_nonce # Ensure nonce is fresh for this attempt
                signed_funding_tx = Account.sign_transaction(funding_tx, funding_account_private_key)
                logger.info(f"Attempt {attempt + 1} of {max_attempts} to send funding TX with nonce {current_nonce} from {funding_account_address} to {account.address}")
                funding_tx_hash = web3_client.eth.send_raw_transaction(signed_funding_tx.raw_transaction)
                logger.info(f"Funding TX sent, hash: {funding_tx_hash.hex()}")
                break # Success
            except Exception as e: # Broad exception to catch web3 errors
                last_exception = e
                logger.warning(f"Funding TX attempt {attempt + 1} failed: {e}")
                if "ReplacementNotAllowed" in str(e) or "nonce too low" in str(e).lower() or "known transaction" in str(e).lower():
                    time.sleep(3)
                    attempt += 1
                else:
                    raise e # Re-raise if it's not a known nonce issue
        
        if funding_tx_hash is None:
            logger.error(f"Failed to send funding transaction after {max_attempts} attempts. Last error: {last_exception}")
            if last_exception is not None: # Ensure last_exception is not None before raising
                raise last_exception # Re-raise the last exception if all attempts failed
            else: # Fallback if last_exception was somehow not set (shouldn't happen)
                raise RuntimeError("Failed to send funding transaction after multiple attempts, unknown error.")

        web3_client.eth.wait_for_transaction_receipt(funding_tx_hash, timeout=int(configuration["transaction_timeout"]))

        # Create the main transaction
        transaction = {
            'to': Web3.to_checksum_address('0x742d35Cc6634C0532925a3b844Bc454e4438f44e'),  # Example address
            'value': web3_client.to_wei(0.00001, 'ether'),
            'gas': 21000,
            'gasPrice': web3_client.eth.gas_price,
            'nonce': web3_client.eth.get_transaction_count(account.address),
            'chainId': web3_client.eth.chain_id,
        }
        # Sign the main transaction
        signed_txn = account.sign_transaction(transaction)
        # Send the pre-signed transaction
        tr = client.call("eth_sendRawTransaction", [signed_txn.raw_transaction.hex()])
        if 'result' not in tr:
            logger.error(f"Failed to send transaction from {account.address} to 0x742d35Cc6634C0532925a3b844Bc454e4438f44e. Balance: {web3_client.eth.get_balance(account.address)}")
            raise ValueError(f"Transaction failed: {tr['error']}")
        tx_hash = tr['result']
        # tx_hash = web3_client.eth.send_raw_transaction(signed_txn.raw_transaction)
        logger.info(f"Transaction hash: {tx_hash}")
        return tx_hash

    return _create_transaction

@pytest.fixture(scope="session")
def ensure_transaction(client: JsonRpcClient, configuration, create_transaction):
    def _ensure_transaction():
        tx_hash = create_transaction()
        receipt = client.call("eth_getTransactionReceipt", [tx_hash])
        logger.info(f"Transaction receipt: {receipt}")
        while receipt['result'] is None:
            time.sleep(5)
            receipt = client.call("eth_getTransactionReceipt", [tx_hash])
        return receipt['result']['blockHash']

    return _ensure_transaction


@pytest.fixture(scope="function")
def run_with_network(request, configuration):
    marker = request.node.get_closest_marker("run_with_network")
    logger.info("Test requires network: " + str(marker.kwargs["network"]))
    if configuration["env_name"] not in marker.kwargs["network"]:
        pytest.skip(f"Skipping test for {configuration['env_name']} network. The test is designed to run only for {marker.kwargs['network']} networks")

@pytest.fixture(scope="session")
def deploy_contract(client: JsonRpcClient, configuration):
    def _deploy_contract(binary_path: str):
        # Read contract binary
        contract_path = Path(binary_path)
        if not contract_path.exists():
            raise FileNotFoundError(f"Contract binary not found at {binary_path}")
            
        with open(binary_path, 'r') as f:
            contract_bin = f.read().strip()
        
        if not contract_bin.startswith('0x'):
            contract_bin = '0x' + contract_bin

        # Prepare deployment transaction
        web3_client = client.web3
        deployer_address = configuration["public_key"]
        
        deploy_tx = {
            'from': deployer_address,
            'data': contract_bin,
            'gas': 2000000,  # Adjust gas limit as needed
            'gasPrice': web3_client.eth.gas_price,
            'nonce': web3_client.eth.get_transaction_count(deployer_address),
            'chainId': web3_client.eth.chain_id,
        }

        # Sign and send deployment transaction
        signed_tx = Account.sign_transaction(
            deploy_tx,
            configuration["private_key"]
        )
        
        send_tx_response = client.call(
            "eth_sendRawTransaction",
            [signed_tx.raw_transaction.hex()]
        )
        
        if 'result' in send_tx_response:
            tx_hash = send_tx_response['result']
            logger.info(f"Contract deployment transaction sent: {tx_hash}")
        elif 'error' in send_tx_response:
            logger.error(f"Failed to send contract deployment transaction. Error: {send_tx_response['error']}")
            raise ValueError(f"Failed to send contract deployment transaction: {send_tx_response['error']}")
        else:
            logger.error(f"Unexpected response when sending contract deployment transaction: {send_tx_response}")
            raise ValueError(f"Unexpected response when sending contract deployment transaction: {send_tx_response}")
        
        # Wait for deployment to complete
        receipt_polling_attempts = 30
        last_receipt_response = None
        actual_receipt_data = None

        for attempt in range(receipt_polling_attempts):
            logger.info(f"Polling for transaction receipt {tx_hash}, attempt {attempt + 1}/{receipt_polling_attempts}")
            last_receipt_response = client.call("eth_getTransactionReceipt", [tx_hash])
            if last_receipt_response.get('result') is not None:
                actual_receipt_data = last_receipt_response['result']
                logger.info(f"Transaction receipt found for {tx_hash}: {actual_receipt_data}")
                break
            elif last_receipt_response.get('error'):
                logger.warning(f"Error polling for receipt for tx {tx_hash} (attempt {attempt + 1}/{receipt_polling_attempts}): {last_receipt_response['error']}. Retrying...")
            else:
                 logger.warning(f"Unexpected response while polling for receipt for tx {tx_hash} (attempt {attempt + 1}/{receipt_polling_attempts}): {last_receipt_response}. Retrying...")
            time.sleep(2)
            
        if actual_receipt_data is None:
            logger.error(f"Contract deployment transaction {tx_hash} was not mined or receipt retrieval failed after {receipt_polling_attempts} attempts. Last response: {last_receipt_response}")
            raise TimeoutError(f"Contract deployment transaction {tx_hash} was not mined or receipt retrieval failed. Last response: {last_receipt_response}")
            
        contract_address = actual_receipt_data.get('contractAddress')
        if not contract_address:
            logger.error(f"'contractAddress' not found in receipt for transaction {tx_hash}. Receipt: {actual_receipt_data}")
            raise ValueError(f"'contractAddress' not found in receipt for transaction {tx_hash}. Receipt: {actual_receipt_data}")
        
        logger.info(f"Contract deployed successfully. Address: {contract_address}, TxHash: {tx_hash}")
        return {
            'address': contract_address,
            'transaction_hash': tx_hash,
            'receipt': actual_receipt_data
        }
        
    return _deploy_contract
