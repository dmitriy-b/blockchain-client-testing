import secrets
from loguru import logger
import pytest
from eth_account import Account
from web3 import Web3
import time

def get_pool_transaction(client) -> tuple[bool, str]:
    """Check if pool has transactions and return first transaction hash if found."""
    response = client.call("txpool_content", [])
    if 'result' not in response:
        return False, ""
        
    result = response['result']
    if not isinstance(result, dict):
        return False, ""
        
    # Look for any transaction in pending or queued
    for status in ['pending', 'queued']:
        for address, nonce_dict in result[status].items():
            for nonce, tx in nonce_dict.items():
                return True, tx['hash']
    
    return False, ""

def create_transaction_for_pool(client, configuration) -> str:
    """Create a transaction and return its hash without waiting for receipt."""

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
        'nonce': web3_client.eth.get_transaction_count(funding_account_address, 'latest'),
        'chainId': web3_client.eth.chain_id,
    }
    
    # Sign the funding transaction (you'll need the private key of the funding account)
    funding_account_private_key = configuration["private_key"]  # Replace with actual private key
    signed_funding_tx = Account.sign_transaction(funding_tx, funding_account_private_key)

    # Send the signed funding transaction
    funding_tx_hash = web3_client.eth.send_raw_transaction(signed_funding_tx.raw_transaction)
    # web3_client.eth.wait_for_transaction_receipt(funding_tx_hash, timeout=int(configuration["transaction_timeout"]))

    logger.info(f"Transaction hash: {funding_tx_hash.hex()}") 
    return "0x" + funding_tx_hash.hex()

@pytest.mark.api
@pytest.mark.txpool
def test_txpool_status_with_pending(client, configuration):
    """Test txpool_status shows pending transaction."""
    # Check if pool already has transactions
    has_tx, tx_hash = get_pool_transaction(client)
    
    # Create new transaction only if pool is empty
    if not has_tx:
        tx_hash = create_transaction_for_pool(client, configuration)
        time.sleep(1)  # Give txpool a moment to process the transaction
    
    response = client.call("txpool_status", [])
    assert 'result' in response
    result = response['result']
    
    # Check structure
    assert isinstance(result, dict)
    assert 'pending' in result
    assert 'queued' in result
    
    # Convert values to integers
    total_txs = 0
    for key in ['pending', 'queued']:
        value = result[key]
        if isinstance(value, str):
            assert value.startswith('0x'), f"{key} should be a hex string starting with 0x"
            total_txs += int(value, 16)
        else:
            assert isinstance(value, (int, float)), f"{key} should be a number"
            total_txs += int(value)
    
    # Verify we have at least one transaction
    assert total_txs > 0, "Expected at least one transaction in the pool"

@pytest.mark.api
@pytest.mark.txpool
def test_txpool_content_with_pending(client, configuration):
    """Test txpool_content shows pending transaction details."""
    # Check if pool already has transactions
    has_tx, tx_hash = get_pool_transaction(client)
    
    # Create new transaction only if pool is empty
    if not has_tx:
        tx_hash = create_transaction_for_pool(client, configuration)
        time.sleep(1)  # Give txpool a moment to process the transaction
    
    response = client.call("txpool_content", [])
    assert 'result' in response
    result = response['result']
    
    # Check structure
    assert isinstance(result, dict)
    assert 'pending' in result
    assert 'queued' in result
    
    # Find our transaction
    tx_found = False
    for status in ['pending', 'queued']:
        for address, nonce_dict in result[status].items():
            for nonce, tx in nonce_dict.items():
                if not tx_hash or tx.get('hash') == tx_hash:
                    tx_found = True
                    # Verify transaction fields
                    assert isinstance(tx, dict)
                    
                    # Fields that must be hex strings
                    hex_fields = ['from', 'gas', 'gasPrice', 'hash', 'input', 'nonce', 'to', 
                                'value', 'type', 'v', 'r', 's']
                    for field in hex_fields:
                        assert field in tx
                        assert isinstance(tx[field], str)
                        assert tx[field].startswith('0x')
                    
                    # Fields that can be None for pending transactions
                    nullable_fields = ['blockHash', 'blockNumber', 'transactionIndex']
                    for field in nullable_fields:
                        assert field in tx
                        assert tx[field] is None or isinstance(tx[field], str)
                    break
            if tx_found:
                break
        if tx_found:
            break
    
    assert tx_found, "Transaction not found in the pool"

@pytest.mark.api
@pytest.mark.txpool
def test_txpool_inspect_with_pending(client, configuration):
    """Test txpool_inspect shows pending transaction summary."""
    # Check if pool already has transactions
    has_tx, tx_hash = get_pool_transaction(client)
    
    # Create new transaction only if pool is empty
    if not has_tx:
        tx_hash = create_transaction_for_pool(client, configuration)
        time.sleep(1)  # Give txpool a moment to process the transaction
    
    response = client.call("txpool_inspect", [])
    assert 'result' in response
    result = response['result']
    
    # Check structure
    assert isinstance(result, dict)
    assert 'pending' in result
    assert 'queued' in result
    
    # Find our transaction's summary
    summary_found = False
    for status in ['pending', 'queued']:
        for address, nonce_dict in result[status].items():
            for nonce, tx_summary in nonce_dict.items():
                summary_found = True
                # Verify summary format
                assert isinstance(tx_summary, str)
                assert ': ' in tx_summary
                # Value should be in the summary
                assert 'wei' in tx_summary.lower() or 'eth' in tx_summary.lower(), "Value should be in summary"
                break
            if summary_found:
                break
        if summary_found:
            break
    
    assert summary_found, "Transaction summary not found in the pool"