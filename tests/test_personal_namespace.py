import pytest
from web3 import Web3
import secrets

@pytest.mark.api
@pytest.mark.personal
def test_personal_list_accounts(client):
    """Test personal_listAccounts returns a list of accounts."""
    response = client.call("personal_listAccounts", [])
    assert 'result' in response
    result = response['result']
    
    # Result should be a list of addresses
    assert isinstance(result, list)
    for address in result:
        assert isinstance(address, str)
        assert address.startswith('0x')
        assert len(address) == 42  # Standard Ethereum address length (0x + 40 hex chars)

@pytest.mark.api
@pytest.mark.personal
def test_personal_new_account(client, configuration):
    """Test personal_newAccount creates a new account."""
    # Create a test password
    password = configuration["personal_account_password"]
    
    # Create new account
    response = client.call("personal_newAccount", [password])
    assert 'result' in response
    address = response['result']
    
    # Verify address format
    assert isinstance(address, str)
    assert address.startswith('0x')
    assert len(address) == 42
    
    # Verify account appears in list
    list_response = client.call("personal_listAccounts", [])
    assert address in list_response['result']

@pytest.mark.api
@pytest.mark.personal
@pytest.mark.order(1) # Run this test first
def test_personal_import_raw_key(client, configuration):
    """Test personal_importRawKey imports a private key."""
    # Generate a random private key
    private_key = secrets.token_hex(32)
    password = configuration["personal_account_password"]
    
    # Import private key
    response = client.call("personal_importRawKey", [private_key, password])
    assert 'result' in response
    address = response['result']
    
    # Verify address format
    assert isinstance(address, str)
    assert address.startswith('0x')
    assert len(address) == 42
    
    # Verify account appears in list
    list_response = client.call("personal_listAccounts", [])
    assert address in list_response['result']

@pytest.mark.api
@pytest.mark.personal
@pytest.mark.order(5)  # Run this test first
def test_personal_unlock_account(client, configuration):
    """Test personal_unlockAccount unlocks an account."""
    try:
        password = configuration["personal_account_password"]
    except KeyError:
        pytest.skip("Account password not configured")
        
    account = configuration["personal_account"]
    
    # Unlock account
    response = client.call("personal_unlockAccount", [account, password])
    assert 'result' in response
    assert response['result'] is True

@pytest.mark.api
@pytest.mark.personal
@pytest.mark.order(4)
def test_personal_lock_account(client, configuration):
    """Test personal_lockAccount locks an account."""
    account = configuration["personal_account"]
    
    # Lock account
    response = client.call("personal_lockAccount", [account])
    assert 'result' in response
    assert response['result'] is True

@pytest.mark.api
@pytest.mark.personal
@pytest.mark.order(3)
def test_personal_sign(client, configuration):
    """Test personal_sign signs a message."""
    try:
        password = configuration["personal_account_password"]
    except KeyError:
        pytest.skip("Account password not configured")
        
    account = configuration["personal_account"]
    message = "0x48656c6c6f20576f726c64"  # "Hello World" in hex
    
    # Sign message
    response = client.call("personal_sign", [message, account, password])
    assert 'result' in response
    signature = response['result']
    
    # Verify signature format
    assert isinstance(signature, str)
    assert signature.startswith('0x')
    assert len(signature) == 130  # Standard Ethereum signature length (0x + 128 hex chars)

@pytest.mark.api
@pytest.mark.personal
@pytest.mark.order(3)
def test_personal_ec_recover(client, configuration):
    """Test personal_ecRecover recovers address from signed message."""
    try:
        password = configuration["personal_account_password"]
    except KeyError:
        pytest.skip("Account password not configured")
        
    account = configuration["personal_account"]
    message = "0x48656c6c6f20576f726c64"  # "Hello World" in hex
    
    # First sign the message
    sign_response = client.call("personal_sign", [message, account, password])
    signature = sign_response['result']
    
    # Add recovery id (v) to the signature
    # The signature from personal_sign is r + s, we need to add v (recovery id)
    # v is either 27 or 28
    signature_with_v = signature + "1b"  # Adding recovery id 27 (0x1b)
    
    # Recover address from signature
    response = client.call("personal_ecRecover", [message, signature_with_v])
    assert 'result' in response
    recovered_address = response['result']
    
    # Verify recovered address matches original signer
    assert recovered_address.lower() == account.lower()
  