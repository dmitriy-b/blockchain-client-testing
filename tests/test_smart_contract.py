import pytest
from pathlib import Path
from eth_account import Account
from web3 import Web3

@pytest.fixture(scope="module")
def deployed_contract_address(deploy_contract, client, configuration):
    # Deploy the contract
    contract_path = "contracts/HelloWorld.bin"
    
    # Deploy contract
    deployment = deploy_contract(contract_path)
    contract_address = deployment['address']
    
    # Verify deployment
    # Get the code at the contract address
    code = client.call("eth_getCode", [contract_address, "latest"])['result']
    # Assert that the code is not '0x', which means the contract is deployed
    assert code != '0x', "Contract is not deployed at the specified address"
    
    # Log deployment details
    print(f"\nContract deployed successfully:")
    print(f"Address: {contract_address}")
    print(f"Transaction Hash: {deployment['transaction_hash']}") 

    configuration["hello_world_contract_address"] = contract_address
    return contract_address

@pytest.mark.api
@pytest.mark.contract
def test_deploy_and_verify_contract(deployed_contract_address):
    # The deployment and verification is handled by the fixture
    assert deployed_contract_address is not None, "Contract address should not be None"


@pytest.mark.api
@pytest.mark.contract
def test_contract_deployed(client, deployed_contract_address):
    # Address of the contract comes directly from the fixture
    contract_address = deployed_contract_address
    
    # Get the code at the contract address
    code = client.call("eth_getCode", [contract_address, "latest"])['result']
    # Assert that the code is not '0x', which means the contract is deployed
    assert code != '0x', f"Contract {contract_address} is not deployed at the specified address."

    # Interact with the contract
    contract_instance = client.web3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=open("contracts/HelloWorld.abi", "r").read())
    result = contract_instance.functions.sayHello().call()
    assert result == "Hello, QA!", "Contract did not return the expected message"