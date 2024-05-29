import pytest

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


# negative tests

@pytest.mark.api
def test_eth_syncing_wrong_param(client):
    response = client.call("eth_syncing", ["test_param"])
    assert 'error' in response
    assert 'id' in response 
    assert response['error']['message'] == 'Invalid params'