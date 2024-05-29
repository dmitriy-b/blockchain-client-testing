import pytest

@pytest.mark.api
def test_eth_block_number(client):
    response = client.call("eth_blockNumber")
    assert 'result' in response
    assert response['result'] is not None

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

@pytest.mark.api
def test_eth_get_balance(client):
    # Use a known address for the test
    address = "0x0000000000000000000000000000000000000000"
    response = client.call("eth_getBalance", [address, "latest"])
    assert 'result' in response
    assert response['result'] is not None

@pytest.mark.api
def test_eth_get_transaction_by_hash(client):
    # Use a known transaction hash for the test
    tx_hash = "0x0000000000000000000000000000000000000000000000000000000000000000"
    response = client.call("eth_getTransactionByHash", [tx_hash])
    assert 'result' in response

@pytest.mark.api
def test_eth_call(client):
    # Use a dummy call object
    call_object = {
        "to": "0x0000000000000000000000000000000000000000",
        "data": "0x"
    }
    response = client.call("eth_call", [call_object, "latest"])
    assert 'result' in response
    assert response['result'] is not None

@pytest.mark.api
def test_eth_estimate_gas(client):
    # Use a dummy transaction object
    tx_object = {
        "to": "0x0000000000000000000000000000000000000000",
        "data": "0x"
    }
    response = client.call("eth_estimateGas", [tx_object])
    assert 'result' in response
    assert response['result'] is not None


# net
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