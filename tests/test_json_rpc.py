import pytest
import time
from eth_account import Account
from web3 import Web3

from tests.conftest import create_transaction_if_not_exist


@pytest.mark.api
def test_eth_block_number(client):
    response = client.call("eth_blockNumber")
    assert 'result' in response
    assert response['result'] is not None
    assert 'id' in response 
    assert response['jsonrpc'] == '2.0'

@pytest.mark.api
def test_eth_get_block_by_number(client):
    block_number = client.call("eth_blockNumber", call_id=1)['result']
    response = client.call("eth_getBlockByNumber", [block_number, True])
    assert 'result' in response
    assert response['result'] is not None
    assert response['result']['author'] is not None
    assert response['result']['difficulty'] is not None
    assert response['result']['extraData'] is not None
    assert response['result']['gasLimit'] is not None
    assert response['result']['gasUsed'] is not None
    assert response['result']['hash'] is not None
    assert response['result']['logsBloom'] is not None
    assert response['result']['miner'] is not None
    assert response['result']['mixHash'] is not None
    assert response['result']['nonce'] is not None
    assert response['result']['number'] is not None
    assert response['result']['parentHash'] is not None
    assert response['result']['receiptsRoot'] is not None
    assert response['result']['sha3Uncles'] is not None
    assert response['result']['size'] is not None
    assert response['result']['stateRoot'] is not None
    assert response['result']['totalDifficulty'] is not None
    assert response['result']['baseFeePerGas'] is not None
    assert response['result']['transactions'] is not None
    assert response['result']['withdrawalsRoot'] is not None
    assert response['result']['blobGasUsed'] is not None
    assert response['result']['excessBlobGas'] is not None
    assert response['result']['parentBeaconBlockRoot'] is not None


# Add more test cases as needed

@pytest.mark.api
def test_eth_syncing(client):
    response = client.call("eth_syncing")
    assert 'result' in response
    assert 'id' in response
    assert response['jsonrpc'] == '2.0'


@pytest.mark.api
def test_eth_gas_price(client):
    response = client.call("eth_gasPrice")
    assert 'result' in response
    assert 'id' in response
    assert response['jsonrpc'] == '2.0'


@pytest.mark.api
def test_eth_chain_id(client):
    response = client.call("eth_chainId", call_id=0)
    assert 'result' in response
    assert 'id' in response
    assert response['jsonrpc'] == '2.0'
    assert int(response['result'], 16) >= 0

# net endpoint
@pytest.mark.api
def test_net_version(client):
    response = client.call("net_version")
    assert 'result' in response
    assert response['result'] is not None

@pytest.mark.api
def test_net_listening(client):
    response = client.call("net_listening")
    assert 'result' in response
    assert response['result'] in [True, False]

@pytest.mark.api
def test_net_peer_count(client):
    response = client.call("net_peerCount")
    assert 'result' in response
    assert response['result'] is not None
    assert int(response['result'], 16) >= 0


@pytest.mark.debug
@pytest.mark.api
def test_get_raw_receipts(client):
    response = client.call("debug_getRawReceipts", ["0x0"])
    assert 'result' in response
    assert response['result'] is not None


@pytest.mark.debug
@pytest.mark.api
def test_get_raw_block(client):
    response = client.call("debug_getRawBlock", ["0x0"])
    assert 'result' in response
    assert response['result'] is not None
# negative tests
@pytest.mark.api
def test_eth_syncing_wrong_param(client):
    response = client.call("eth_syncing", ["test_param"])
    assert 'error' in response
    assert 'id' in response
    assert response['error']['message'] == 'Invalid params'


# Debug namespace tests
@pytest.mark.api
@pytest.mark.debug
def test_debug_trace_transaction(client, ensure_transaction):
    # First, get a transaction hash from a recent block
    tx_hash = create_transaction_if_not_exist(client, ensure_transaction)['transactions'][0]['hash']
    response = client.call("debug_traceTransaction", [tx_hash])
    assert 'result' in response
    assert 'gas' in response['result']
    assert 'returnValue' in response['result']
    assert 'structLogs' in response['result']

@pytest.mark.api
@pytest.mark.debug
def test_debug_trace_block_by_number(client):
    block_number = client.call("eth_blockNumber")['result']
    response = client.call("debug_traceBlockByNumber", [block_number, {"tracer": "callTracer"}])
    assert 'result' in response
    assert isinstance(response['result'], list)
    if len(response['result']) > 0:
        assert 'type' in response['result'][0]
        assert 'from' in response['result'][0]
        assert 'to' in response['result'][0]

@pytest.mark.api
@pytest.mark.debug
def test_debug_trace_call(client):
    # Example transaction call
    tx_call = {
        "from": "0x0000000000000000000000000000000000000001",
        "to": "0x0000000000000000000000000000000000000002",
        "gas": "0x5208",  # 21000
        "gasPrice": "0x1",
        "value": "0x1",
        "data": "0x"
    }
    block_number = "latest"
    response = client.call("debug_traceCall", [tx_call, block_number, {"tracer": "callTracer"}])
    assert 'result' in response
    assert 'type' in response['result']
    assert 'from' in response['result']
    assert 'to' in response['result']

@pytest.mark.api
@pytest.mark.debug
def test_debug_trace_block_by_hash(client):
    # First, get the latest block hash
    block = client.call("eth_getBlockByNumber", ["latest", False])
    block_hash = block['result']['hash']

    response = client.call("debug_traceBlockByHash", [block_hash, {"tracer": "callTracer"}])
    assert 'result' in response
    assert isinstance(response['result'], list)
    if len(response['result']) > 0:
        assert 'type' in response['result'][0]
        assert 'from' in response['result'][0]
        assert 'to' in response['result'][0]


@pytest.mark.api
@pytest.mark.debug
def test_debug_trace_block_by_hash_with_options(client, ensure_transaction):
    block_hash = create_transaction_if_not_exist(client, ensure_transaction)['hash']

    # Define tracing options
    options = {
        "tracer": "callTracer",
        "timeout": "10s",
        "disableStorage": True,
        "disableStack": True,
        "enableMemory": False,
        "enableReturnData": True
    }

    response = client.call("debug_traceBlockByHash", [block_hash, options])
    assert 'result' in response
    assert isinstance(response['result'], list)
    if len(response['result']) > 0:
        assert 'type' in response['result'][0]
        assert 'from' in response['result'][0]
        assert 'to' in response['result'][0]
        assert 'input' in response['result'][0]
        # Check for either 'output' or 'result' field
        # assert 'output' in response['result'][0] or 'result' in response['result'][0]

        # Additional checks to provide more information
        print(f"Response keys: {response['result'][0].keys()}")
        if 'output' not in response['result'][0]:
            print("'output' field not found. Available fields:")
            for key in response['result'][0]:
                print(f"- {key}: {response['result'][0][key]}")

@pytest.mark.api
@pytest.mark.debug
def test_debug_trace_transaction_with_custom_tracer(client, ensure_transaction):
    tx_hash = create_transaction_if_not_exist(client, ensure_transaction)['transactions'][0]['hash']

    # Define a custom JavaScript tracer
    custom_tracer = """
    {
        step: function(log, db) { },
        fault: function(log, db) { },
        result: function(ctx, db) {
            return {
                gasUsed: ctx.gasUsed,
                returnValue: ctx.returnValue
            }
        }
    }
    """

    response = client.call("debug_traceTransaction", [tx_hash, {"tracer": custom_tracer}])
    assert 'result' in response
    assert 'gasUsed' in response['result']
    assert 'returnValue' in response['result']

    # Print additional information for debugging
    print(f"Transaction hash: {tx_hash}")
    print(f"Response: {response}")

@pytest.mark.api
@pytest.mark.debug
def test_debug_trace_call_with_state_overrides(client):
    # Example transaction call
    tx_call = {
        "from": "0x0000000000000000000000000000000000000001",
        "to": "0x0000000000000000000000000000000000000002",
        "gas": "0x5208",  # 21000
        "gasPrice": "0x1",
        "value": "0x1",
        "data": "0x"
    }
    block_number = "latest"
    # State overrides
    state_overrides = {
        "0x0000000000000000000000000000000000000002": {
            "balance": "0x1000000000000000000"
        }
    }
    response = client.call("debug_traceCall", [tx_call, block_number, {"tracer": "callTracer", "stateOverrides": state_overrides}])
    assert 'result' in response
    assert 'type' in response['result']
    assert 'from' in response['result']
    assert 'to' in response['result']
    assert 'value' in response['result']
    assert response['result']['value'] == '0x1'

@pytest.mark.api
@pytest.mark.debug
def test_debug_trace_block_by_number_with_tracer_config(client):
    block_number = client.call("eth_blockNumber")['result']
    tracer_config = {
        "onlyTopCall": True,
        "withLog": True
    }
    response = client.call("debug_traceBlockByNumber", [block_number, {"tracer": "callTracer", "tracerConfig": tracer_config}])
    assert 'result' in response
    assert isinstance(response['result'], list)
    if len(response['result']) > 0:
        assert 'type' in response['result'][0]
        assert 'from' in response['result'][0]
        assert 'to' in response['result'][0]
        assert 'calls' not in response['result'][0]  # Ensure only top-level call is returned

@pytest.mark.api
def test_get_balance(client, configuration):
    # Address to check balance
    address = configuration["public_key"]
    # Get balance using eth_getBalance
    balance_wei = client.call("eth_getBalance", [address, "latest"])['result']
    print(f"Balance of {address}: {balance_wei} Wei")

    # Convert balance from Wei to Ether
    balance_eth = float(Web3.from_wei(Web3.to_int(hexstr=balance_wei), 'ether'))
    print(f"Balance of {address}: {balance_eth} ETH")
    # Assertions
    assert Web3.to_int(hexstr=balance_wei) >= 0, "Balance should be non-negative"
    assert isinstance(balance_eth, float), "Balance in ETH should be a float"

@pytest.mark.api
def test_contract_deployed(client, configuration):
    # Address of the contract to check
    contract_address = configuration["hello_world_contract_address"]
    # Get the code at the contract address
    code = client.call("eth_getCode", [contract_address, "latest"])['result']
    # Assert that the code is not '0x', which means the contract is deployed
    assert code != '0x', "Contract is not deployed at the specified address"

        # Interact with the contract
    contract_instance = client.web3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=open("contracts/HelloWorld.abi", "r").read())
    result = contract_instance.functions.sayHello().call()
    assert result == "Hello, World!", "Contract did not return the expected message"


