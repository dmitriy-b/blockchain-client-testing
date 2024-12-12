import pytest
from eth_account import Account
from web3 import Web3

@pytest.mark.api
@pytest.mark.txpool
def test_txpool_status_with_pending(client, create_transaction):
    """Test txpool_status shows pending transaction."""
    # Create a transaction that should stay in the pool
    tx_hash = create_transaction()
    
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
def test_txpool_content_with_pending(client, create_transaction):
    """Test txpool_content shows pending transaction details."""
    # Create a transaction that should stay in the pool
    tx_hash = create_transaction()
    
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
                if tx.get('hash') == tx_hash:
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
def test_txpool_inspect_with_pending(client, create_transaction):
    """Test txpool_inspect shows pending transaction summary."""
    # Create a transaction that should stay in the pool
    tx_hash = create_transaction()
    
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