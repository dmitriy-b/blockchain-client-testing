import pytest
from web3 import Web3
from eth_account import Account

@pytest.mark.api
@pytest.mark.proof
def test_proof_get_transaction_by_hash(client, configuration):
    """Test proof_getTransactionByHash returns transaction with proof."""
    web3_client: Web3 = client.web3  # type: ignore
    # Use the first account from the node as the funding account
    funding_account_address = configuration["public_key"]
    funding_balance = web3_client.eth.get_balance(funding_account_address)

    if funding_balance == 0:
        raise ValueError(f"Funding account {funding_account_address} has no balance. Please ensure there's an account with funds.")

    # Create a simple transaction
    transaction = {
        'to': Web3.to_checksum_address('0x742d35Cc6634C0532925a3b844Bc454e4438f44e'),
        'value': web3_client.to_wei(0.00001, 'ether'),
        'gas': 21000,
        'gasPrice': web3_client.eth.gas_price,
        'nonce': web3_client.eth.get_transaction_count(funding_account_address),
        'chainId': web3_client.eth.chain_id,
    }

    # Sign and send transaction
    signed_txn = Account.sign_transaction(transaction, configuration["private_key"])
    tx_hash = web3_client.eth.send_raw_transaction(signed_txn.raw_transaction)
    
    # Wait for transaction receipt
    receipt = web3_client.eth.wait_for_transaction_receipt(tx_hash)
    assert receipt['status'] == 1, "Transaction failed"
    
    # Call proof_getTransactionByHash with transaction hash and includeHeader flag
    response = client.call("proof_getTransactionByHash", [tx_hash.hex(), True])
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
def test_proof_get_transaction_receipt(client, configuration):
    """Test proof_getTransactionReceipt returns receipt with proof."""
    web3_client: Web3 = client.web3  # type: ignore
    # Use the first account from the node as the funding account
    funding_account_address = configuration["public_key"]
    funding_balance = web3_client.eth.get_balance(funding_account_address)

    if funding_balance == 0:
        raise ValueError(f"Funding account {funding_account_address} has no balance. Please ensure there's an account with funds.")

    # Create a simple transaction
    transaction = {
        'to': Web3.to_checksum_address('0x742d35Cc6634C0532925a3b844Bc454e4438f44e'),
        'value': web3_client.to_wei(0.00001, 'ether'),
        'gas': 21000,
        'gasPrice': web3_client.eth.gas_price,
        'nonce': web3_client.eth.get_transaction_count(funding_account_address),
        'chainId': web3_client.eth.chain_id,
    }

    # Sign and send transaction
    signed_txn = Account.sign_transaction(transaction, configuration["private_key"])
    tx_hash = web3_client.eth.send_raw_transaction(signed_txn.raw_transaction)
    
    # Wait for transaction receipt
    receipt = web3_client.eth.wait_for_transaction_receipt(tx_hash)
    assert receipt['status'] == 1, "Transaction failed"
    
    # Call proof_getTransactionReceipt with transaction hash and includeHeader flag
    response = client.call("proof_getTransactionReceipt", [tx_hash.hex(), True])
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