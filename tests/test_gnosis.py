import pytest
import time
from eth_account import Account
from web3 import Web3
from loguru import logger
from tests.conftest import create_transaction_if_not_exist, run_with_network

@pytest.mark.api
@pytest.mark.run_with_network(network=["chiado", "gnosis"])
def test_gnosis_fee_collector(client, ensure_transaction, run_with_network):
    fee_collector_address = "0x1559000000000000000000000000000000000000"
    # Get balance using eth_getBalance
    balance_wei = client.call("eth_getBalance", [fee_collector_address, "latest"])['result']
    logger.info(f"Balance of {fee_collector_address}: {balance_wei} Wei")
    transaction_count = client.call("eth_getTransactionCount", [fee_collector_address])['result']
    logger.info(f"Transaction count of {fee_collector_address}: {transaction_count}")
    # Convert balance from Wei to Ether
    balance_eth = float(Web3.from_wei(Web3.to_int(hexstr=balance_wei), 'ether'))
    logger.info(f"Balance of {fee_collector_address}: {balance_eth} ETH")
    # Assertions
    assert Web3.to_int(hexstr=balance_wei) >= 0, "Balance should be non-negative"
    assert isinstance(balance_eth, float), "Balance in ETH should be a float"
    create_transaction_if_not_exist(client, ensure_transaction)
    block = client.call("eth_getBlockByNumber", ["latest", True])
    assert len(block['result']['transactions']) > 0, "Block should have transactions"

    # Poll for balance change with timeout
    timeout = 600  # 10 minutes timeout
    start_time = time.time()
    while True:
        balance_wei_updated = client.call("eth_getBalance", [fee_collector_address, "latest"])['result']
        balance_eth_updated = float(Web3.from_wei(Web3.to_int(hexstr=balance_wei_updated), 'ether'))
        transaction_count_updated = client.call("eth_getTransactionCount", [fee_collector_address])['result']
        
        if balance_eth_updated > balance_eth:
            break
            
        if time.time() - start_time > timeout:
            pytest.fail(f"Timeout waiting for balance to increase. Initial: {balance_eth}, Current: {balance_eth_updated}")
            
        time.sleep(5)  # Poll every 5 seconds

    assert transaction_count_updated == transaction_count, "There should be no new transactions for fee collector"
