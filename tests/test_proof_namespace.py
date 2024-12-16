import pytest
from web3 import Web3
from eth_account import Account
from conftest import create_transaction_if_not_exist

@pytest.mark.api
@pytest.mark.proof
def test_proof_get_transaction_by_hash(client, configuration, ensure_transaction):
    """Test proof_getTransactionByHash returns transaction with proof."""
    tx_hash = create_transaction_if_not_exist(client, ensure_transaction)['transactions'][0]['hash']
    
    # Wait for transaction receipt
    web3_client: Web3 = client.web3  # type: ignore
    receipt = web3_client.eth.wait_for_transaction_receipt(tx_hash)
    assert receipt['status'] == 1, "Transaction failed"
    
    # Call proof_getTransactionByHash with transaction hash and includeHeader flag
    response = client.call("proof_getTransactionByHash", [tx_hash, True])
    assert 'result' in response
    result = response['result']
    
    # Verify transaction structure
    assert isinstance(result, dict)
    assert 'transaction' in result
    tx = result['transaction']
    
    # Verify transaction fields
    assert 'blockHash' in tx
    assert 'blockNumber' in tx
    assert 'from' in tx
    assert 'gas' in tx
    assert 'gasPrice' in tx
    assert 'hash' in tx
    assert 'input' in tx
    assert 'nonce' in tx
    assert 'to' in tx
    assert 'transactionIndex' in tx
    assert 'value' in tx
    assert 'v' in tx
    assert 'r' in tx
    assert 's' in tx
    
    # Verify proof fields
    assert 'blockHeader' in result
    assert isinstance(result['blockHeader'], str)
    assert result['blockHeader'].startswith('0x')
    
    assert 'txProof' in result
    assert isinstance(result['txProof'], list)
    for proof in result['txProof']:
        assert isinstance(proof, str)
        assert proof.startswith('0x')

@pytest.mark.api
@pytest.mark.proof
def test_proof_get_transaction_receipt(client, configuration, ensure_transaction):
    """Test proof_getTransactionReceipt returns receipt with proof."""
    tx_hash = create_transaction_if_not_exist(client, ensure_transaction)['transactions'][0]['hash']
    
    # Wait for transaction receipt
    web3_client: Web3 = client.web3  # type: ignore
    receipt = web3_client.eth.wait_for_transaction_receipt(tx_hash)
    assert receipt['status'] == 1, "Transaction failed"
    
    # Call proof_getTransactionReceipt with transaction hash and includeHeader flag
    response = client.call("proof_getTransactionReceipt", [tx_hash, True])
    assert 'result' in response
    result = response['result']
    
    # Verify receipt structure
    assert isinstance(result, dict)
    assert 'receipt' in result
    receipt = result['receipt']
    
    # Verify receipt fields
    assert 'blockHash' in receipt
    assert 'blockNumber' in receipt
    assert 'contractAddress' in receipt
    assert 'cumulativeGasUsed' in receipt
    assert 'from' in receipt
    assert 'gasUsed' in receipt
    assert 'logs' in receipt
    assert isinstance(receipt['logs'], list)
    assert 'logsBloom' in receipt
    assert 'status' in receipt
    assert 'to' in receipt
    assert 'transactionHash' in receipt
    assert 'transactionIndex' in receipt
    
    # Verify proof fields
    assert 'blockHeader' in result
    assert isinstance(result['blockHeader'], str)
    assert result['blockHeader'].startswith('0x')
    
    assert 'txProof' in result
    assert isinstance(result['txProof'], list)
    for proof in result['txProof']:
        assert isinstance(proof, str)
        assert proof.startswith('0x')