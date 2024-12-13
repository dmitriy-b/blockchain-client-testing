import pytest
from web3 import Web3
import time
from conftest import create_transaction_if_not_exist
from eth_account import Account
import secrets

@pytest.mark.api
@pytest.mark.trace
def test_trace_block(client):
    """Test trace_block returns traces for a given block."""
    # Get latest block number
    block_number = client.call("eth_blockNumber", [])['result']
    
    # Call trace_block with the latest block
    response = client.call("trace_block", [block_number])
    assert 'result' in response
    result = response['result']
    
    # Result should be an array
    assert isinstance(result, list)
    
    # If there are traces, verify their structure
    for trace in result:
        assert isinstance(trace, dict)
        # Common fields for all trace types
        assert 'action' in trace
        assert 'blockHash' in trace
        assert 'blockNumber' in trace
        assert 'subtraces' in trace
        assert 'traceAddress' in trace
        assert 'type' in trace
        
        # Verify action structure based on type
        action = trace['action']
        assert isinstance(action, dict)
        
        if trace['type'] == 'reward':
            # Reward trace specific fields
            assert 'author' in action
            assert 'rewardType' in action
            assert 'value' in action
        else:
            # Transaction trace specific fields
            assert 'result' in trace
            assert 'transactionHash' in trace
            assert 'transactionPosition' in trace
            
            # Common action fields for transaction traces
            assert 'from' in action
            if 'callType' in action:
                assert action['callType'] in ['call', 'staticcall', 'delegatecall']
            if 'value' in action:
                assert isinstance(action['value'], str)
                assert action['value'].startswith('0x')

@pytest.mark.api
@pytest.mark.trace
def test_trace_transaction(client, ensure_transaction):
    """Test trace_transaction returns traces for a given transaction."""
    # Create a transaction and get its hash
    tx_hash = create_transaction_if_not_exist(client, ensure_transaction)['transactions'][0]['hash']
    
    # Call trace_transaction
    response = client.call("trace_transaction", [tx_hash])
    assert 'result' in response
    result = response['result']
    
    # Result should be an array
    assert isinstance(result, list)
    
    # Verify trace structure
    for trace in result:
        assert isinstance(trace, dict)
        assert 'action' in trace
        assert 'result' in trace
        assert 'subtraces' in trace
        assert 'traceAddress' in trace
        assert 'type' in trace
        
        # Verify action structure
        action = trace['action']
        assert isinstance(action, dict)
        assert 'from' in action
        assert 'gas' in action
        assert 'value' in action
        
        # Verify result structure if present
        if trace['result']:
            assert isinstance(trace['result'], dict)
            assert 'gasUsed' in trace['result']

@pytest.mark.api
@pytest.mark.trace
def test_trace_call(client):
    """Test trace_call returns traces for a call."""
    # Prepare call parameters
    tx = {
        "from": "0x0000000000000000000000000000000000000000",
        "to": "0x0000000000000000000000000000000000000000",
        "gas": "0x76c0",
        "gasPrice": "0x9184e72a000",
        "value": "0x0"
    }
    block_parameter = "latest"
    trace_types = ["trace", "vmTrace", "stateDiff"]
    
    # Call trace_call
    response = client.call("trace_call", [tx, trace_types, block_parameter])
    assert 'result' in response
    result = response['result']
    
    # Verify result structure
    assert isinstance(result, dict)
    
    # Check trace types if present
    if 'trace' in result:
        assert isinstance(result['trace'], list)
    if 'vmTrace' in result:
        assert isinstance(result['vmTrace'], dict)
    if 'stateDiff' in result:
        assert isinstance(result['stateDiff'], dict)

@pytest.mark.api
@pytest.mark.trace
def test_trace_raw_transaction(client, configuration):
    """Test trace_rawTransaction returns traces for a raw transaction."""

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
    
    
    # Sign transaction
    raw_tx = signed_funding_tx.raw_transaction.hex()
    
    # Call trace_rawTransaction
    trace_types = ["trace", "vmTrace", "stateDiff"]
    response = client.call("trace_rawTransaction", [raw_tx, trace_types])
    assert 'result' in response
    result = response['result']
    
    # Verify result structure
    assert isinstance(result, dict)
    
    # Check trace types if present
    if 'trace' in result:
        assert isinstance(result['trace'], list)
    if 'vmTrace' in result:
        assert isinstance(result['vmTrace'], dict)
    if 'stateDiff' in result:
        assert isinstance(result['stateDiff'], dict)

@pytest.mark.api
@pytest.mark.trace
def test_trace_replay_transaction(client, ensure_transaction):
    """Test trace_replayTransaction returns traces for a transaction."""
    # Create a transaction and get its hash
    tx_hash = create_transaction_if_not_exist(client, ensure_transaction)['transactions'][0]['hash']
        
    # Call trace_replayTransaction
    trace_types = ["trace", "vmTrace", "stateDiff"]
    response = client.call("trace_replayTransaction", [tx_hash, trace_types])
    assert 'result' in response
    result = response['result']
    
    # Verify result structure
    assert isinstance(result, dict)
    
    # Check trace types if present
    if 'trace' in result:
        assert isinstance(result['trace'], list)
    if 'vmTrace' in result:
        assert isinstance(result['vmTrace'], dict)
    if 'stateDiff' in result:
        assert isinstance(result['stateDiff'], dict) 

@pytest.mark.api
@pytest.mark.trace
def test_trace_get(client, ensure_transaction):
    """Test trace_get returns trace at given position."""
    # Create a transaction and get its hash
    tx_hash = create_transaction_if_not_exist(client, ensure_transaction)['transactions'][0]['hash']
    
    # Wait for transaction receipt
    web3_client: Web3 = client.web3  # type: ignore
    receipt = web3_client.eth.wait_for_transaction_receipt(tx_hash)
    assert receipt['status'] == 1, "Transaction failed"
    
    # Get block number
    block_number = receipt['blockNumber']
    tx_position = receipt['transactionIndex']
    
    # Call trace_get with position [0] (first trace)
    response = client.call("trace_get", [tx_hash, [0]])
    assert 'result' in response
    result = response['result']
    
    # Result can be empty array if no traces at position
    if result:
        # If we have a trace, verify its structure
        assert isinstance(result, dict)
        assert 'action' in result
        assert 'result' in result
        assert 'subtraces' in result
        assert 'traceAddress' in result
        assert 'type' in result
        
        # Verify action structure
        action = result['action']
        assert isinstance(action, dict)
        if result['type'] == 'call':
            assert 'from' in action
            assert 'to' in action
            assert 'value' in action
            assert 'gas' in action
            assert 'input' in action
        elif result['type'] == 'create':
            assert 'from' in action
            assert 'value' in action
            assert 'gas' in action
            assert 'init' in action
        elif result['type'] == 'suicide':
            assert 'address' in action
            assert 'refundAddress' in action
            assert 'balance' in action
    else:
        # If no trace at position, result should be empty array
        assert isinstance(result, list)
        assert len(result) == 0

@pytest.mark.api
@pytest.mark.trace
def test_trace_filter(client, ensure_transaction):
    """Test trace_filter returns traces matching filter criteria."""
    # Create a transaction and get its hash
    tx_hash = ensure_transaction()
    
    # Wait for transaction receipt
    web3_client: Web3 = client.web3  # type: ignore
    receipt = web3_client.eth.wait_for_transaction_receipt(tx_hash)
    assert receipt['status'] == 1, "Transaction failed"
    
    # Create filter for the block range
    filter_params = {
        "fromBlock": hex(receipt['blockNumber']),
        "toBlock": hex(receipt['blockNumber']),
        "after": 0,
        "count": 10
    }
    
    # Call trace_filter
    response = client.call("trace_filter", [filter_params])
    assert 'result' in response
    result = response['result']
    
    # Result should be an array
    assert isinstance(result, list)
    
    # Verify trace structure if any traces found
    for trace in result:
        assert isinstance(trace, dict)
        assert 'action' in trace
        assert 'blockHash' in trace
        assert 'blockNumber' in trace
        assert 'subtraces' in trace
        assert 'traceAddress' in trace
        assert 'transactionHash' in trace
        assert 'transactionPosition' in trace
        assert 'type' in trace

@pytest.mark.api
@pytest.mark.trace
def test_trace_call_many(client):
    """Test trace_callMany returns traces for multiple calls."""
    # Prepare multiple call parameters
    calls = [
        [
            {
                "from": "0x0000000000000000000000000000000000000000",
                "to": "0x0000000000000000000000000000000000000000",
                "gas": "0x76c0",
                "gasPrice": "0x9184e72a000",
                "value": "0x0"
            },
            ["trace"]
        ],
        [
            {
                "from": "0x0000000000000000000000000000000000000000",
                "to": "0x0000000000000000000000000000000000000001",
                "gas": "0x76c0",
                "gasPrice": "0x9184e72a000",
                "value": "0x0"
            },
            ["trace", "vmTrace"]
        ]
    ]
    block_parameter = "latest"
    
    # Call trace_callMany
    response = client.call("trace_callMany", [calls, block_parameter])
    assert 'result' in response
    result = response['result']
    
    # Result should be an array
    assert isinstance(result, list)
    assert len(result) == len(calls)
    
    # Verify each result
    for trace_result in result:
        assert isinstance(trace_result, dict)
        # Trace can be list or None
        if 'trace' in trace_result:
            assert isinstance(trace_result['trace'], (list, type(None)))
        # vmTrace can be dict or None
        if 'vmTrace' in trace_result:
            assert isinstance(trace_result['vmTrace'], (dict, type(None)))
        # stateDiff can be dict or None
        if 'stateDiff' in trace_result:
            assert isinstance(trace_result['stateDiff'], (dict, type(None)))

@pytest.mark.api
@pytest.mark.trace
def test_trace_replay_block_transactions(client, ensure_transaction):
    """Test trace_replayBlockTransactions returns traces for all transactions in a block."""
    # Create a transaction and get its hash
    tx_hash = create_transaction_if_not_exist(client, ensure_transaction)['transactions'][0]['hash']
    
    # Wait for transaction receipt
    web3_client: Web3 = client.web3  # type: ignore
    receipt = web3_client.eth.wait_for_transaction_receipt(tx_hash)
    assert receipt['status'] == 1, "Transaction failed"
    
    # Get block number
    block_number = hex(receipt['blockNumber'])
    
    # Call trace_replayBlockTransactions
    trace_types = ["trace", "vmTrace", "stateDiff"]
    response = client.call("trace_replayBlockTransactions", [block_number, trace_types])
    assert 'result' in response
    result = response['result']
    
    # Result should be an array
    assert isinstance(result, list)
    
    # Verify each transaction trace
    for tx_trace in result:
        assert isinstance(tx_trace, dict)
        if 'trace' in tx_trace:
            assert isinstance(tx_trace['trace'], list)
        if 'vmTrace' in tx_trace:
            assert isinstance(tx_trace['vmTrace'], dict)
        if 'stateDiff' in tx_trace:
            assert isinstance(tx_trace['stateDiff'], dict)
        assert 'transactionHash' in tx_trace