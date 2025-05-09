import pytest
import time
from eth_account import Account
from web3 import Web3
from loguru import logger
from tests.conftest import create_transaction_if_not_exist, run_with_network
from eth_abi import encode

from web3 import Web3
from eth_account import Account
from eth_utils import to_hex
from web3 import Web3, HTTPProvider

# Replace with your Infura project URL or local node URL


@pytest.mark.api
@pytest.mark.run_with_network(network=["chiado", "gnosis", "pectra-devnet"])
def test_gnosis_fee_collector(client, ensure_transaction, run_with_network, configuration):

    web3 = Web3(Web3.HTTPProvider(configuration["base_url"]))
    fee_collector_address = "0x1559000000000000000000000000000000000000"
    
    # Get initial state
    initial_block = client.call("eth_getBlockByNumber", ["latest", False])['result']
    initial_block_number = Web3.to_int(hexstr=initial_block['number'])
    balance_wei = client.call("eth_getBalance", [fee_collector_address, "latest"])['result']
    balance_eth = float(Web3.from_wei(Web3.to_int(hexstr=balance_wei), 'ether'))
    transaction_count = client.call("eth_getTransactionCount", [fee_collector_address])['result']
    
    logger.info(f"Initial block number: {initial_block_number}")
    logger.info(f"Initial balance: {balance_eth} ETH")

    # Create and wait for transaction to be included
    tx_hash = create_transaction_if_not_exist(client, ensure_transaction)['transactions'][-1]['hash']
    logger.info(f"Created transaction: {tx_hash}")
    
    # Wait for transaction to be mined
    timeout = int(configuration["block_creation_timeout"])
    start_time = time.time()
    tx_included = False
    
    while time.time() - start_time < timeout:
        try:
            response = client.call("eth_getTransactionReceipt", [tx_hash])
            tr = web3.eth.get_transaction(tx_hash)
            if response is None or 'result' not in response:
                logger.debug(f"Transaction {tx_hash} not yet created. Waiting...")
                time.sleep(5)
                continue
                
            tx_receipt = response['result']
            if tx_receipt is not None:
                tx_included = True
                tx_block_number = Web3.to_int(hexstr=tx_receipt['blockNumber'])
                logger.info(f"Transaction included in block {tx_block_number}")
                logger.info(f"Transaction status: {tx_receipt['status']}")
                
                # Verify transaction was successful
                if tx_receipt['status'] != "0x1":
                    pytest.fail("Transaction failed - check gas settings and account balance")
                break
        except Exception as e:
            logger.debug(f"Error checking transaction receipt: {e}")
            time.sleep(5)
            continue
        
        time.sleep(5)
    
    if not tx_included:
        pytest.fail(f"Transaction not included in block after {timeout} seconds")

    # Wait a few blocks after transaction inclusion to ensure fee distribution
    wait_blocks = 2
    target_block_number = tx_block_number + wait_blocks
    
    while time.time() - start_time < timeout:
        current_block = client.call("eth_getBlockByNumber", ["latest", False])['result']
        current_block_number = Web3.to_int(hexstr=current_block['number'])
        
        if current_block_number >= target_block_number:
            balance_wei_updated = client.call("eth_getBalance", [fee_collector_address, "latest"])['result']
            balance_eth_updated = float(Web3.from_wei(Web3.to_int(hexstr=balance_wei_updated), 'ether'))
            
            logger.info(f"Current block: {current_block_number}")
            logger.info(f"Updated balance: {balance_eth_updated} ETH")
            logger.info(f"Balance difference: {balance_eth_updated - balance_eth} ETH")
            
            if balance_eth_updated > balance_eth:
                break
                
        if time.time() - start_time > timeout:
            # Get transaction details for debugging
            tx = client.call("eth_getTransactionByHash", [tx_hash])['result']
            logger.error(f"Transaction details: {tx}")
            logger.error(f"Blocks passed since tx: {current_block_number - tx_block_number}")
            pytest.fail(f"Fee collector balance didn't increase. Initial: {balance_eth}, Current: {balance_eth_updated}")
            
        time.sleep(5)

    transaction_count_updated = client.call("eth_getTransactionCount", [fee_collector_address])['result']
    assert transaction_count_updated == transaction_count, "There should be no new transactions for fee collector"



@pytest.mark.api
@pytest.mark.run_with_network(network=[ "pectra-devnet", "chiado"])
def test_gnosis_blob_fee_collector(client, ensure_transaction, run_with_network, configuration):

    web3 = Web3(Web3.HTTPProvider(configuration["base_url"]))
    fee_collector_address = "0x1559000000000000000000000000000000000000"
    
    # Get initial state
    initial_block = client.call("eth_getBlockByNumber", ["latest", False])['result']
    initial_block_number = Web3.to_int(hexstr=initial_block['number'])
    balance_wei = client.call("eth_getBalance", [fee_collector_address, "latest"])['result']
    balance_eth = float(Web3.from_wei(Web3.to_int(hexstr=balance_wei), 'ether'))
    transaction_count = client.call("eth_getTransactionCount", [fee_collector_address])['result']
    
    logger.info(f"Initial block number: {initial_block_number}")
    logger.info(f"Initial balance: {balance_eth} ETH")

    # Create and wait for transaction to be included
    # tx_hash = create_transaction_if_not_exist(client, ensure_transaction)['transactions'][-1]['hash']

    # Your data to include in the blob
    text = "<( o.O )>"
    encoded_text = encode(["string"], [text])

    # Calculate the necessary padding
    padding_bytes = (b"\x00" * 32 * (4096 - len(encoded_text) // 32))

    # Combine padding and encoded text to form the blob data
    BLOB_DATA = padding_bytes + encoded_text

    tx = {
        "type": 3,  # Indicates a blob transaction
        "chainId": 10209,
        "from": configuration["public_key"],
        'gas': 21000,
        "to": "0x9813a4Db195f413B34840386D605B2d99A69016d",  # Typically zeroed out
        "value": 0,
        "maxFeePerGas": client.web3.to_wei(1, 'gwei'),
        "maxPriorityFeePerGas": client.web3.to_wei(1, 'gwei'),
        "maxFeePerBlobGas": to_hex(client.web3.to_wei(1, 'gwei')),
        "nonce": client.web3.eth.get_transaction_count(configuration["public_key"]),
    }

    # Sign the transaction, including the blob data
    signed = Account.sign_transaction(tx, configuration["private_key"], blobs=[BLOB_DATA])

    # Send the signed transaction
    tx_hash = client.web3.eth.send_raw_transaction(signed.raw_transaction)

    logger.info(f"Created transaction: {tx_hash}")
    
    # Wait for transaction to be mined
    timeout = int(configuration["block_creation_timeout"])
    start_time = time.time()
    tx_included = False
    
    while time.time() - start_time < timeout:
        try:
            response = client.call("eth_getTransactionReceipt", [tx_hash])
            tr = web3.eth.get_transaction(tx_hash)
            if response is None or 'result' not in response:
                logger.debug(f"Transaction {tx_hash} not yet created. Waiting...")
                time.sleep(5)
                continue
                
            tx_receipt = response['result']
            if tx_receipt is not None:
                tx_included = True
                tx_block_number = Web3.to_int(hexstr=tx_receipt['blockNumber'])
                logger.info(f"Transaction included in block {tx_block_number}")
                logger.info(f"Transaction status: {tx_receipt['status']}")
                
                # Verify transaction was successful
                if tx_receipt['status'] != "0x1":
                    pytest.fail("Transaction failed - check gas settings and account balance")
                break
        except Exception as e:
            logger.debug(f"Error checking transaction receipt: {e}")
            time.sleep(5)
            continue
        
        time.sleep(5)
    
    if not tx_included:
        pytest.fail(f"Transaction not included in block after {timeout} seconds")

    # Wait a few blocks after transaction inclusion to ensure fee distribution
    wait_blocks = 2
    target_block_number = tx_block_number + wait_blocks
    
    while time.time() - start_time < timeout:
        current_block = client.call("eth_getBlockByNumber", ["latest", False])['result']
        current_block_number = Web3.to_int(hexstr=current_block['number'])
        
        if current_block_number >= target_block_number:
            balance_wei_updated = client.call("eth_getBalance", [fee_collector_address, "latest"])['result']
            balance_eth_updated = float(Web3.from_wei(Web3.to_int(hexstr=balance_wei_updated), 'ether'))
            
            logger.info(f"Current block: {current_block_number}")
            logger.info(f"Updated balance: {balance_eth_updated} ETH")
            logger.info(f"Balance difference: {balance_eth_updated - balance_eth} ETH")
            
            if balance_eth_updated > balance_eth:
                break
                
        if time.time() - start_time > timeout:
            # Get transaction details for debugging
            tx = client.call("eth_getTransactionByHash", [tx_hash])['result']
            logger.error(f"Transaction details: {tx}")
            logger.error(f"Blocks passed since tx: {current_block_number - tx_block_number}")
            pytest.fail(f"Fee collector balance didn't increase. Initial: {balance_eth}, Current: {balance_eth_updated}")
            
        time.sleep(5)

    transaction_count_updated = client.call("eth_getTransactionCount", [fee_collector_address])['result']
    assert transaction_count_updated == transaction_count, "There should be no new transactions for fee collector"
