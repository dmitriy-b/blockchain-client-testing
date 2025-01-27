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
    logger.add(sys.stdout, level=cfg[env]['log_stdout_level'])
    logger.add(f"reports/{cfg[env]['log_file_name']}.log", level=cfg[env]['log_file_level'])
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
            'value': web3_client.to_wei(0.0001, 'ether'),
            'gas': 21000,
            'gasPrice': web3_client.eth.gas_price,
            'nonce': web3_client.eth.get_transaction_count(funding_account_address),
            'chainId': web3_client.eth.chain_id,
        }

        # Sign the funding transaction (you'll need the private key of the funding account)
        funding_account_private_key = configuration["private_key"]  # Replace with actual private key
        signed_funding_tx = Account.sign_transaction(funding_tx, funding_account_private_key)

        # Send the signed funding transaction
        funding_tx_hash = web3_client.eth.send_raw_transaction(signed_funding_tx.raw_transaction)
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
        tx_hash = client.call("eth_sendRawTransaction", [signed_txn.raw_transaction.hex()])['result']
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
        
        tx_hash = client.call(
            "eth_sendRawTransaction",
            [signed_tx.raw_transaction.hex()]
        )['result']
        
        # Wait for deployment to complete
        receipt = None
        for _ in range(30):  # 30 attempts with 2-second intervals
            receipt = client.call("eth_getTransactionReceipt", [tx_hash])
            if receipt['result'] is not None:
                break
            time.sleep(2)
            
        if receipt is None or receipt['result'] is None:
            raise TimeoutError("Contract deployment transaction was not mined")
            
        contract_address = receipt['result']['contractAddress']
        return {
            'address': contract_address,
            'transaction_hash': tx_hash,
            'receipt': receipt['result']
        }
        
    return _deploy_contract
