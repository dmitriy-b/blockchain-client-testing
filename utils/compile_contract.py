import json
from solcx import compile_source, set_solc_version, install_solc

try:
    set_solc_version('0.8.28')
except Exception as e:
    install_solc('0.8.28')
    set_solc_version('0.8.28')

# Solidity source code
contract_source_code = '''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

contract HelloQA {
    function sayHello() public pure returns (string memory) {
        return "Hello, QA!";
    }
}
'''

# Compile the contract
compiled_sol = compile_source(contract_source_code)
contract_interface = compiled_sol['<stdin>:HelloQA']

# Extract bytecode and ABI
bytecode = contract_interface['bin']
abi = contract_interface['abi']

# Print bytecode and ABI
print("Bytecode:", bytecode)
print("ABI:", abi)

# Write bytecode and ABI to files
with open('contracts/HelloWorld.bin', 'w') as bin_file:
    bin_file.write(bytecode)

with open('contracts/HelloWorld.abi', 'w') as abi_file:
    abi_file.write(json.dumps(abi))  # Convert ABI list to JSON string