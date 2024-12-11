import pytest
import re

@pytest.mark.api
@pytest.mark.web3
def test_web3_client_version(client):
    """Test web3_clientVersion returns the current client version."""
    response = client.call("web3_clientVersion", [])
    assert 'result' in response
    assert isinstance(response['result'], str)
    # Client version should be a non-empty string
    assert len(response['result']) > 0
    # Should contain Nethermind and version number
    assert 'Nethermind' in response['result']
    assert re.search(r'\d+\.\d+\.\d+', response['result']), "Version number should be in format x.x.x"

@pytest.mark.api
@pytest.mark.web3
def test_web3_sha3(client):
    """Test web3_sha3 returns Keccak-256 hash of the given data."""
    # Test with a known input/output pair
    test_input = "0x68656c6c6f20776f726c64"  # "hello world" in hex
    expected_output = "0x47173285a8d7341e5e972fc677286384f802f8ef42a5ec5f03bbfa254cb01fad"
    
    response = client.call("web3_sha3", [test_input])
    assert 'result' in response
    assert isinstance(response['result'], str)
    assert response['result'] == expected_output

    # Test with empty string
    response_empty = client.call("web3_sha3", ["0x"])
    assert 'result' in response_empty
    assert isinstance(response_empty['result'], str)
    assert response_empty['result'].startswith("0x")
    assert len(response_empty['result']) == 66  # "0x" + 64 hex chars

@pytest.mark.api
@pytest.mark.web3
def test_web3_sha3_invalid_input(client):
    """Test web3_sha3 with invalid input formats."""
    # Test with missing input parameter
    response = client.call("web3_sha3", [])
    assert 'error' in response

    # Test with null input
    response = client.call("web3_sha3", [None])
    assert 'error' in response

    # Test with invalid parameter type (number instead of string)
    response = client.call("web3_sha3", [123])
    assert 'error' in response

    # Test with array input instead of string
    response = client.call("web3_sha3", [[]])
    assert 'error' in response