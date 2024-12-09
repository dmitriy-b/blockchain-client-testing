import pytest
import re

@pytest.mark.api
@pytest.mark.net
def test_net_version(client):
    """Test net_version returns a valid network ID."""
    response = client.call("net_version", [])
    assert 'result' in response
    assert isinstance(response['result'], str)
    # Network ID should be a string representing a number
    assert response['result'].isdigit()

@pytest.mark.api
@pytest.mark.net
def test_net_listening(client):
    """Test net_listening returns a boolean indicating if node is listening."""
    response = client.call("net_listening", [])
    assert 'result' in response
    assert isinstance(response['result'], bool)

@pytest.mark.api
@pytest.mark.net
def test_net_peer_count(client):
    """Test net_peerCount returns number of connected peers in hex format."""
    response = client.call("net_peerCount", [])
    assert 'result' in response
    assert isinstance(response['result'], str)
    # Result should be a hex string starting with "0x"
    assert response['result'].startswith('0x')
    # Convert hex to int to verify it's a valid number
    peer_count = int(response['result'], 16)
    assert isinstance(peer_count, int)
    assert peer_count >= 0  # Peer count cannot be negative

@pytest.mark.api
@pytest.mark.net
def test_net_local_address(client):
    """Test net_localAddress returns the local node address."""
    response = client.call("net_localAddress", [])
    assert 'result' in response
    assert isinstance(response['result'], str)
    # Local address should be a hex string starting with "0x" followed by 40 characters (20 bytes)
    hex_pattern = r'^0x[0-9a-fA-F]{40}$'
    assert re.match(hex_pattern, response['result']), "Local address should be a 20-byte hex string starting with 0x"

@pytest.mark.api
def test_net_local_enode(client):
    """Test net_localEnode returns the enode URL of the node."""
    response = client.call("net_localEnode", [])
    assert 'result' in response
    assert isinstance(response['result'], str)
    # Enode URL format: enode://pubkey@ip:port
    enode_pattern = r'^enode://[0-9a-fA-F]{128}@[\d\.:]+$'
    assert re.match(enode_pattern, response['result']), "Enode URL should match format 'enode://pubkey@ip:port'"