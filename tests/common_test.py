from tests.conftest import generate_ethereum_account

def test_create_account(generate_ethereum_account):
    account = generate_ethereum_account
    assert account['private_key'] is not None
    assert account['public_key'] is not None
