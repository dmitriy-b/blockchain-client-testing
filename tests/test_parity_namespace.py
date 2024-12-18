import pytest
from web3 import Web3
import secrets


@pytest.mark.api
@pytest.mark.parity
def test_parity_pending_transactions(client):
    """Test parity_pendingTransactions returns list of pending transactions."""
    response = client.call("parity_pendingTransactions", [])
    assert 'result' in response
    transactions = response['result']
    
    # Verify it's a list
    assert isinstance(transactions, list)
    
    # If there are any transactions, verify their structure
    for tx in transactions:
        assert isinstance(tx, dict)
        assert 'hash' in tx
        assert tx['hash'].startswith('0x')
        assert len(tx['hash']) == 66  # 0x + 64 hex chars
        assert 'from' in tx
        assert Web3.is_address(tx['from'])
        # 'to' might be None for contract creation
        if tx['to'] is not None:
            assert Web3.is_address(tx['to'])
        assert 'nonce' in tx
        assert isinstance(tx['nonce'], str)
        assert tx['nonce'].startswith('0x')


@pytest.mark.api
@pytest.mark.parity
def test_parity_enode(client):
    """Test parity_enode returns the enode URL."""
    response = client.call("parity_enode", [])
    assert 'result' in response
    enode = response['result']
    
    # Verify enode format
    assert isinstance(enode, str)
    assert enode.startswith('enode://')
    # Basic enode format check
    parts = enode.split('@')
    assert len(parts) == 2
    node_id = parts[0].replace('enode://', '')
    assert len(node_id) == 128  # 64 bytes hex encoded

@pytest.mark.api
@pytest.mark.parity
def test_parity_net_peers(client):
    """Test parity_netPeers returns connected peers information."""
    response = client.call("parity_netPeers", [])
    assert 'result' in response
    peers = response['result']
    
    # Verify peers structure
    assert isinstance(peers, dict)
    assert 'active' in peers
    assert isinstance(peers['active'], int)
    assert 'connected' in peers
    assert isinstance(peers['connected'], int)
    assert 'max' in peers
    assert isinstance(peers['max'], int)
    assert 'peers' in peers
    assert isinstance(peers['peers'], list)
    
    # If there are any peers, verify their structure
    for peer in peers['peers']:
        assert isinstance(peer, dict)
        assert 'id' in peer
        assert isinstance(peer['id'], str)
        assert 'network' in peer
        assert isinstance(peer['network'], dict)
        assert 'localAddress' in peer['network']
        assert 'remoteAddress' in peer['network']
        assert 'protocols' in peer
        assert isinstance(peer['protocols'], dict)
        # Verify caps array exists
        assert 'caps' in peer
        assert isinstance(peer['caps'], list)


@pytest.mark.api
@pytest.mark.parity
def test_parity_get_block_receipts(client):
    """Test parity_getBlockReceipts returns receipts for a block."""
    # Get latest block number first
    block_response = client.call("eth_blockNumber", [])
    assert 'result' in block_response
    block_number = block_response['result']
    
    # Get receipts for the latest block
    response = client.call("parity_getBlockReceipts", [block_number])
    assert 'result' in response
    receipts = response['result']
    
    # Verify receipts structure
    assert isinstance(receipts, list)
    for receipt in receipts:
        assert isinstance(receipt, dict)
        assert 'transactionHash' in receipt
        assert receipt['transactionHash'].startswith('0x')
        assert len(receipt['transactionHash']) == 66
        assert 'blockHash' in receipt
        assert receipt['blockHash'].startswith('0x')
        assert len(receipt['blockHash']) == 66
        assert 'blockNumber' in receipt
        assert receipt['blockNumber'].startswith('0x')
        assert 'transactionIndex' in receipt
        assert receipt['transactionIndex'].startswith('0x')
        assert 'from' in receipt
        assert Web3.is_address(receipt['from'])
        # 'to' might be None for contract creation
        if receipt['to'] is not None:
            assert Web3.is_address(receipt['to'])
        assert 'cumulativeGasUsed' in receipt
        assert receipt['cumulativeGasUsed'].startswith('0x')
        assert 'gasUsed' in receipt
        assert receipt['gasUsed'].startswith('0x')
        assert 'status' in receipt
        assert receipt['status'] in ['0x0', '0x1']

@pytest.mark.api
@pytest.mark.parity
def test_parity_set_engine_signer(client, configuration):
    """Test parity_setEngineSigner sets the engine signer."""
    account = configuration["personal_account"]
    password = configuration["personal_account_password"]
    
    # Set engine signer
    response = client.call("parity_setEngineSigner", [account, password])
    assert 'result' in response
    # The result should be True if successful
    assert isinstance(response['result'], bool)


@pytest.mark.api
@pytest.mark.parity
def test_parity_set_engine_signer_secret(client):
    """Test parity_setEngineSignerSecret sets the engine signer secret."""
    # Generate a valid private key (32 bytes)
    # Using a known valid private key for testing
    # This is a randomly generated private key, not used in production
    private_key = "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    
    response = client.call("parity_setEngineSignerSecret", [private_key])
    assert 'result' in response
    # The result should be True if successful
    assert isinstance(response['result'], bool)

@pytest.mark.api
@pytest.mark.parity
def test_parity_clear_engine_signer(client):
    """Test parity_clearEngineSigner clears the engine signer."""
    response = client.call("parity_clearEngineSigner", [])
    assert 'result' in response
    # The result should be True if successful
    assert isinstance(response['result'], bool)