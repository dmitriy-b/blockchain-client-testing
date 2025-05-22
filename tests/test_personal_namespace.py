import pytest
from web3 import Web3
import secrets

def ensure_account_exists(client, account, password, private_key):
    """Helper function to ensure account exists, importing it if necessary."""
    # Check if account exists in personal_listAccounts
    response = client.call("personal_listAccounts", [])
    if account not in response['result']:
        # Import account with a new private key
        import_response = client.call("personal_importRawKey", [private_key, password])
        assert 'result' in import_response, f"Failed to import account: {import_response.get('error', {}).get('message', 'Unknown error')}"
        account = import_response['result']
    return account

def ensure_account_unlocked(client, account, password):
    """Helper function to ensure account is unlocked."""
    # Try to unlock account
    response = client.call("personal_unlockAccount", [account, password])
    if not response.get('result', False):
        # If unlock failed, try locking and unlocking again
        client.call("personal_lockAccount", [account])
        response = client.call("personal_unlockAccount", [account, password])
        assert response.get('result', False), f"Failed to unlock account: {response.get('error', {}).get('message', 'Unknown error')}"

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
def test_personal_unlock_account(client, configuration):
    """Test personal_unlockAccount unlocks an account."""
    password = configuration["personal_account_password"]
    account = configuration["personal_account"]
    private_key = configuration["personal_account_private_key"]
    
    # Ensure account exists
    account = ensure_account_exists(client, account, password, private_key)
    
    # First lock the account to ensure we're testing unlock
    client.call("personal_lockAccount", [account])
    
    # Unlock account
    response = client.call("personal_unlockAccount", [account, password])
    assert 'result' in response
    assert response['result'] is True

@pytest.mark.api
@pytest.mark.personal
def test_personal_lock_account(client, configuration):
    """Test personal_lockAccount locks an account."""
    password = configuration["personal_account_password"]
    account = configuration["personal_account"]
    private_key = configuration["personal_account_private_key"]
    
    # Ensure account exists
    account = ensure_account_exists(client, account, password, private_key)
    
    # Lock account
    response = client.call("personal_lockAccount", [account])
    assert 'result' in response
    assert response['result'] is True

@pytest.mark.api
@pytest.mark.personal
def test_personal_sign(client, configuration):
    """Test personal_sign signs a message."""
    password = configuration["personal_account_password"]
    account = configuration["personal_account"]
    private_key = configuration["personal_account_private_key"]
    
    # Ensure account exists and is unlocked
    account = ensure_account_exists(client, account, password, private_key)
    ensure_account_unlocked(client, account, password)
    
    message = "0x48656c6c6f20576f726c64"  # "Hello World" in hex
    
    # Sign message
    response = client.call("personal_sign", [message, account, password])
    assert 'result' in response
    signature = response['result']
    
    # Verify signature format
    assert isinstance(signature, str)
    assert signature.startswith('0x')
    assert len(signature) == 132  # Standard Ethereum signature length (0x + 65 bytes including v)

@pytest.mark.api
@pytest.mark.personal
def test_personal_ec_recover(client, configuration):
    """Test personal_ecRecover recovers address from signed message."""
    password = configuration["personal_account_password"]
    account = configuration["personal_account"]
    private_key = configuration["personal_account_private_key"]
    
    # Ensure account exists and is unlocked
    account = ensure_account_exists(client, account, password, private_key)
    ensure_account_unlocked(client, account, password)
    
    message = "0x48656c6c6f20576f726c64"  # "Hello World" in hex
    
    # First sign the message
    sign_response = client.call("personal_sign", [message, account, password])
    assert 'result' in sign_response, f"Failed to sign message: {sign_response.get('error', {}).get('message', 'Unknown error')}"
    signature = sign_response['result']
    
    # personal_sign now includes 'v' in the signature, so we pass it directly
    response = client.call("personal_ecRecover", [message, signature])
    recovered_address = None
    if 'result' in response and response['result'].lower() == account.lower():
        recovered_address = response['result']

    assert recovered_address is not None, f"Failed to recover the correct address. Signature: {signature}, Response: {response}"
  