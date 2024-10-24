import rlp
from typing import List, Union, Dict, Any, Tuple, Optional
from eth_utils import decode_hex, encode_hex, int_to_big_endian, remove_0x_prefix, keccak
from eth_typing import HexStr
import json
import argparse
import os
import sys
import logging

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from utils.json_rpc_client import JsonRpcClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Header(rlp.Serializable):
    fields = [
        ('parentHash', rlp.sedes.binary),
        ('uncleHash', rlp.sedes.binary),
        ('coinbase', rlp.sedes.binary),
        ('stateRoot', rlp.sedes.binary),
        ('transactionRoot', rlp.sedes.binary),
        ('receiptRoot', rlp.sedes.binary),
        ('bloom', rlp.sedes.binary),
        ('difficulty', rlp.sedes.big_endian_int),
        ('number', rlp.sedes.big_endian_int),
        ('gasLimit', rlp.sedes.big_endian_int),
        ('gasUsed', rlp.sedes.big_endian_int),
        ('time', rlp.sedes.big_endian_int),
        ('extra', rlp.sedes.binary),
        ('mixDigest', rlp.sedes.binary),
        ('nonce', rlp.sedes.binary),
        ('baseFee', rlp.sedes.big_endian_int),
        ('withdrawalsRoot', rlp.sedes.binary),
        ('blobGasUsed', rlp.sedes.big_endian_int),
        ('excessBlobGas', rlp.sedes.big_endian_int),
        ('parentBeaconRoot', rlp.sedes.binary),
    ]

    def __init__(self,
                 parentHash: bytes,
                 uncleHash: bytes,
                 coinbase: bytes,
                 stateRoot: bytes,
                 transactionRoot: bytes,
                 receiptRoot: bytes,
                 bloom: bytes,
                 difficulty: int,
                 number: int,
                 gasLimit: int,
                 gasUsed: int,
                 time: int,
                 extra: bytes,
                 mixDigest: bytes,
                 nonce: bytes,
                 baseFee: Optional[int] = None,
                 withdrawalsRoot: Optional[bytes] = None,
                 blobGasUsed: Optional[int] = None,
                 excessBlobGas: Optional[int] = None,
                 parentBeaconRoot: Optional[bytes] = None):
        super().__init__(
            parentHash,
            uncleHash,
            coinbase,
            stateRoot,
            transactionRoot,
            receiptRoot,
            bloom,
            difficulty,
            number,
            gasLimit,
            gasUsed,
            time,
            extra,
            mixDigest,
            nonce,
            baseFee,
            withdrawalsRoot,
            blobGasUsed,
            excessBlobGas,
            parentBeaconRoot
        )

class Block(rlp.Serializable):
    fields = [
        ('header', Header),
        ('transactions', rlp.sedes.CountableList(rlp.sedes.binary)),
        ('uncles', rlp.sedes.CountableList(Header))
    ]

def encode_scalar(value: Union[int, str, None], field_name: str = '') -> bytes:
    if value is None or value == '':
        return b''
    try:
        if isinstance(value, str):
            # Remove any extra '0x' prefixes
            while value.startswith('0x0x'):
                value = '0x' + value[4:]
            
            if value.startswith('0x'):
                # Ensure the hex string has an even length
                if len(value) % 2 != 0:
                    value = '0x0' + value[2:]
                if field_name == 'logsBloom':
                    # Ensure logsBloom is always 256 bytes
                    return bytes.fromhex(remove_0x_prefix(HexStr(value)).zfill(512))
                return decode_hex(value)
            else:
                # If it's a string but doesn't start with '0x', try to interpret as hex
                return bytes.fromhex(value)
        elif isinstance(value, int):
            if value == 0:
                return b''
            return remove_leading_zeros(int_to_big_endian(value))
        else:
            raise ValueError(f"Unsupported scalar type for {field_name}: {type(value)}")
    except Exception as e:
        logger.error(f"Error encoding {field_name}: {value}")
        raise ValueError(f"Error encoding {field_name}: {value}") from e

def remove_leading_zeros(byte_string: bytes) -> bytes:
    return byte_string.lstrip(b'\x00') or b'\x00'

def calculate_trie_root(items):
    """Calculate the root of a Merkle Patricia Trie."""
    trie = {}
    for i, item in enumerate(items):
        key = rlp.encode(i)
        value = rlp.encode(item)
        trie[key] = value
    sorted_trie = [trie[k] for k in sorted(trie.keys())]
    return keccak(rlp.encode(sorted_trie))

def convert_block_to_rlp(block: Dict[str, Any]) -> bytes:
    """
    Convert a block dictionary to RLP encoding.
    
    :param block: The block dictionary
    :return: RLP encoded bytes of the full block
    """
    header = block['header']
    header_rlp = [
        encode_scalar(header['parentHash'], 'parentHash'),
        encode_scalar(header['sha3Uncles'], 'sha3Uncles'),
        encode_scalar(header['miner'], 'miner'),
        encode_scalar(header['stateRoot'], 'stateRoot'),
        encode_scalar(header['transactionsRoot'], 'transactionsRoot'),
        encode_scalar(header['receiptsRoot'], 'receiptsRoot'),
        encode_scalar(header['logsBloom'], 'logsBloom'),
        encode_scalar(int(header['difficulty'], 16), 'difficulty'),
        encode_scalar(int(header['number'], 16), 'number'),
        encode_scalar(int(header['gasLimit'], 16), 'gasLimit'),
        encode_scalar(int(header['gasUsed'], 16), 'gasUsed'),
        encode_scalar(int(header['timestamp'], 16), 'timestamp'),
        encode_scalar(header['extraData'], 'extraData'),
        encode_scalar(header['mixHash'], 'mixHash'),
        encode_scalar(header['nonce'], 'nonce'),
    ]

    if 'baseFeePerGas' in header:
        header_rlp.append(encode_scalar(int(header['baseFeePerGas'], 16), 'baseFeePerGas'))
    if 'withdrawalsRoot' in header:
        header_rlp.append(encode_scalar(header['withdrawalsRoot'], 'withdrawalsRoot'))
    if 'blobGasUsed' in header:
        header_rlp.append(encode_scalar(int(header['blobGasUsed'], 16), 'blobGasUsed'))
    if 'excessBlobGas' in header:
        header_rlp.append(encode_scalar(int(header['excessBlobGas'], 16), 'excessBlobGas'))
    if 'parentBeaconBlockRoot' in header:
        header_rlp.append(encode_scalar(header['parentBeaconBlockRoot'], 'parentBeaconBlockRoot'))

    # Encode transactions
    transactions = []
    if block.get('Txs'):
        transactions = [
            rlp.encode([
                encode_scalar(tx.get('nonce', 0), 'nonce'),
                encode_scalar(tx.get('gasPrice', '0x0'), 'gasPrice'),
                encode_scalar(tx.get('gas', 0), 'gas'),
                encode_scalar(tx.get('to', ''), 'to') if tx.get('to') else b'',
                encode_scalar(tx.get('value', '0x0'), 'value'),
                encode_scalar(tx.get('input', ''), 'input'),
                encode_scalar(tx.get('v', '0x0'), 'v'),
                encode_scalar(tx.get('r', '0x0'), 'r'),
                encode_scalar(tx.get('s', '0x0'), 's')
            ]) for tx in block['Txs']
        ]

    # Encode uncles
    uncles = [rlp.encode([]) for _ in block['uncles']]

    # Encode the full block
    full_block = [header_rlp, transactions, uncles]

    return rlp.encode(full_block)

def read_blocks_from_file(file_path: str) -> List[Dict[str, Any]]:
    with open(file_path, 'r') as f:
        blocks = json.load(f)
    for block in blocks:
        if 'transactions' in block:
            block['Txs'] = block.pop('transactions')
    return blocks if isinstance(blocks, list) else [blocks]

def save_rlp_to_file(blocks: List[Dict[str, Any]], output_file: str):
    """
    Convert blocks to RLP and save to a file.
    
    :param blocks: List of block dictionaries
    :param output_file: Path to the output file
    """
    with open(output_file, 'wb') as f:
        for block in blocks:
            rlp_block = convert_block_to_rlp(block)
            f.write(rlp_block)
    
    print(f"RLP encoded blocks have been saved to {output_file}")
    print(f"Total blocks: {len(blocks)}")

def read_and_decode_rlp(file_path: str):
    """
    Read an RLP encoded file, decode it, and print the results.
    
    :param file_path: Path to the RLP encoded file
    """
    with open(file_path, 'rb') as f:
        rlp_data = f.read()
    
    print(f"File size: {len(rlp_data)} bytes")
    try:
        decoded_data = rlp.decode(rlp_data)
        print(f"Decoded {len(decoded_data)} blocks")
        for i, block in enumerate(decoded_data):
            print(f"Block {i}:")
            print_decoded_data(block, max_depth=2)
            print()
    except Exception as e:
        print(f"Error decoding RLP data: {e}")
        # Try to decode as much as possible
        offset = 0
        while offset < len(rlp_data):
            try:
                item, consumed = rlp.codec.consume_item(rlp_data[offset:])
                print(f"Decoded item at offset {offset}:")
                print_decoded_data(item, max_depth=2)
                print()
                offset += consumed
            except Exception as e:
                print(f"Error decoding at offset {offset}: {e}")
                offset += 1

def print_decoded_data(data: Any, indent: int = 0, max_depth: int = 3):
    """
    Recursively print decoded RLP data.
    
    :param data: Decoded RLP data
    :param indent: Indentation level for nested structures
    :param max_depth: Maximum depth to print for nested structures
    """
    if indent > max_depth:
        print("  " * indent + "...")
        return
    
    if isinstance(data, (list, tuple)):
        print("  " * indent + "[")
        for item in data:
            print_decoded_data(item, indent + 1, max_depth)
        print("  " * indent + "]")
    elif isinstance(data, bytes):
        if len(data) == 1 and data[0] <= 0x7f:
            print("  " * indent + f"{data[0]}")  # Print as integer if it's a single byte
        elif len(data) <= 32:  # Print short byte strings
            print("  " * indent + f"0x{encode_hex(data)}")
        else:  # Summarize long byte strings
            print("  " * indent + f"0x{encode_hex(data[:16])}...{encode_hex(data[-16:])} (length: {len(data)})")
    else:
        print("  " * indent + str(data))

def calculate_block_hash(block: Dict[str, Any]) -> str:
    """
    Calculate the hash of a block.
    
    :param block: The block dictionary
    :return: Calculated block hash as a hex string
    """
    try:
        header = block['header']
        header_rlp = Header(
            parentHash=encode_scalar(header['parentHash'], 'parentHash'),
            uncleHash=encode_scalar(header['sha3Uncles'], 'sha3Uncles'),
            coinbase=encode_scalar(header['miner'], 'miner'),
            stateRoot=encode_scalar(header['stateRoot'], 'stateRoot'),
            transactionRoot=encode_scalar(header['transactionsRoot'], 'transactionsRoot'),
            receiptRoot=encode_scalar(header['receiptsRoot'], 'receiptsRoot'),
            bloom=encode_scalar(header['logsBloom'], 'logsBloom'),
            difficulty=int(header['difficulty'], 16),
            number=int(header['number'], 16),
            gasLimit=int(header['gasLimit'], 16),
            gasUsed=int(header['gasUsed'], 16),
            time=int(header['timestamp'], 16),
            extra=encode_scalar(header['extraData'], 'extraData'),
            mixDigest=encode_scalar(header['mixHash'], 'mixHash'),
            nonce=encode_scalar(header['nonce'], 'nonce'),
            baseFee=int(header['baseFeePerGas'], 16) if 'baseFeePerGas' in header else None,
            withdrawalsRoot=encode_scalar(header.get('withdrawalsRoot'), 'withdrawalsRoot'),
            blobGasUsed=int(header['blobGasUsed'], 16) if 'blobGasUsed' in header else None,
            excessBlobGas=int(header['excessBlobGas'], 16) if 'excessBlobGas' in header else None,
            parentBeaconRoot=encode_scalar(header.get('parentBeaconBlockRoot'), 'parentBeaconBlockRoot'),
        )
        
        rlp_encoded = rlp.encode(header_rlp)
        return '0x' + encode_hex(keccak(rlp_encoded))
    except Exception as e:
        logger.error(f"Error calculating block hash: {e}")
        logger.error(f"Problematic block: {json.dumps(block, indent=2)}")
        raise

def recalculate_block_hashes(blocks: List[Dict[str, Any]], genesis_hash: str) -> List[Dict[str, Any]]:
    """
    Recalculate hashes for a list of blocks, starting from a given genesis hash.
    
    :param blocks: List of block dictionaries
    :param genesis_hash: Hash of the genesis block
    :return: List of blocks with recalculated hashes
    """
    recalculated_blocks = []
    parent_hash = genesis_hash

    for block in blocks:
        # Update the parent hash
        block['header']['parentHash'] = parent_hash
        
        # Recalculate the block hash
        new_hash = calculate_block_hash(block)
        block['header']['hash'] = new_hash
        block['hash'] = new_hash
        
        recalculated_blocks.append(block)
        parent_hash = new_hash

    return recalculated_blocks

def fetch_last_n_blocks(client: JsonRpcClient, n: int, genesis_hash: str) -> List[Dict[str, Any]]:
    """
    Fetch the last N blocks from the Ethereum network and recalculate their hashes.
    
    :param client: JsonRpcClient instance
    :param n: Number of blocks to fetch
    :param genesis_hash: Hash of the genesis block
    :return: List of block dictionaries with recalculated hashes
    """
    blocks = []
    
    # Get the latest block
    latest_block = client.call("eth_getBlockByNumber", ["latest", True])['result']
    blocks.append(latest_block)
    
    current_hash = latest_block['parentHash']
    
    # Fetch the remaining N-1 blocks
    for _ in range(n - 1):
        block = client.call("eth_getBlockByHash", [current_hash, True])['result']
        if block is None:
            break
        blocks.append(block)
        current_hash = block['parentHash']
    
    # Reverse the list so that the oldest block comes first
    blocks = list(reversed(blocks))
    
    # Recalculate hashes starting from the genesis hash
    return recalculate_block_hashes(blocks, genesis_hash)

def print_rlp_hexdump(file_path: str, num_bytes: int = 100):
    """
    Print a hexdump of the first num_bytes of an RLP file.
    
    :param file_path: Path to the RLP file
    :param num_bytes: Number of bytes to print (default: 100)
    """
    with open(file_path, 'rb') as f:
        data = f.read(num_bytes)
    
    print(f"Hexdump of first {num_bytes} bytes of {file_path}:")
    for i in range(0, len(data), 16):
        hex_values = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_values = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f'{i:04x}: {hex_values:<48} {ascii_values}')

def read_rlp_file(file_path: str) -> List[Any]:
    with open(file_path, 'rb') as f:
        rlp_data = f.read()
    
    logger.debug(f"Read {len(rlp_data)} bytes from {file_path}")
    
    blocks = []
    offset = 0
    while offset < len(rlp_data):
        try:
            result = rlp.codec.consume_item(rlp_data, offset)
            logger.debug(f"consume_item returned: {result}")
            if isinstance(result, tuple):
                if len(result) == 2:
                    block, consumed = result
                else:
                    block = result[0]
                    consumed = result[-1]  # Assume the last value is the consumed bytes
            else:
                block = result
                consumed = len(rlp_data) - offset
            blocks.append(block)
            offset += consumed
            logger.debug(f"Processed block at offset {offset}, consumed {consumed} bytes")
        except rlp.exceptions.DecodingError as e:
            logger.error(f"Error decoding at offset {offset}: {e}")
            break
    
    logger.debug(f"Decoded {len(blocks)} blocks")
    return blocks

def rlp_to_json(rlp_blocks: List[Any]) -> List[Dict[str, Any]]:
    json_blocks = []
    for block in rlp_blocks:
        try:
            if isinstance(block, list) and len(block) >= 3:
                header, transactions, uncles = block[:3]
            else:
                print(f"Unexpected block structure: {block}")
                continue
            
            json_block = {
                "header": {
                    "parentHash": '0x' + encode_hex(header[0]),
                    "sha3Uncles": '0x' + encode_hex(header[1]),
                    "miner": '0x' + encode_hex(header[2]),
                    "stateRoot": '0x' + encode_hex(header[3]),
                    "transactionsRoot": '0x' + encode_hex(header[4]),
                    "receiptsRoot": '0x' + encode_hex(header[5]),
                    "logsBloom": '0x' + encode_hex(header[6]),
                    "difficulty": hex(int.from_bytes(header[7], 'big')),
                    "number": hex(int.from_bytes(header[8], 'big')),
                    "gasLimit": hex(int.from_bytes(header[9], 'big')),
                    "gasUsed": hex(int.from_bytes(header[10], 'big')),
                    "timestamp": hex(int.from_bytes(header[11], 'big')),
                    "extraData": '0x' + encode_hex(header[12]),
                    "mixHash": '0x' + encode_hex(header[13]),
                    "nonce": '0x' + encode_hex(header[14]),
                },
                "Txs": [],
                "uncles": [],
            }
            
            # Add optional fields if they exist
            if len(header) > 15:
                json_block["header"]["baseFeePerGas"] = hex(int.from_bytes(header[15], 'big'))
            if len(header) > 16:
                json_block["header"]["withdrawalsRoot"] = '0x' + encode_hex(header[16])
            if len(header) > 17:
                json_block["header"]["blobGasUsed"] = hex(int.from_bytes(header[17], 'big'))
            if len(header) > 18:
                json_block["header"]["excessBlobGas"] = hex(int.from_bytes(header[18], 'big'))
            if len(header) > 19:
                json_block["header"]["parentBeaconBlockRoot"] = '0x' + encode_hex(header[19])
            
            for tx in transactions:
                json_tx = {
                    "nonce": hex(int.from_bytes(tx[0], 'big')),
                    "gasPrice": hex(int.from_bytes(tx[1], 'big')),
                    "gas": hex(int.from_bytes(tx[2], 'big')),
                    "to": '0x' + encode_hex(tx[3]) if tx[3] else None,
                    "value": hex(int.from_bytes(tx[4], 'big')),
                    "input": '0x' + encode_hex(tx[5]),
                    "v": hex(int.from_bytes(tx[6], 'big')),
                    "r": hex(int.from_bytes(tx[7], 'big')),
                    "s": hex(int.from_bytes(tx[8], 'big')),
                }
                json_block["Txs"].append(json_tx)
            
            json_blocks.append(json_block)
        except Exception as e:
            print(f"Error processing block: {e}")
            print(f"Problematic block: {block}")
    
    return json_blocks

def save_json_blocks(blocks: List[Dict[str, Any]], output_file: str):
    with open(output_file, 'w') as f:
        json.dump(blocks, f, indent=2)
    print(f"JSON blocks have been saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Fetch last N blocks, recalculate hashes, and convert to RLP or decode RLP file")
    parser.add_argument("output_file", help="Path to the output file")
    parser.add_argument("--decode", action="store_true", help="Decode RLP file instead of encoding")
    parser.add_argument("--rpc-url", help="Ethereum RPC URL", required=False)
    parser.add_argument("--num-blocks", type=int, default=10, help="Number of blocks to fetch (default: 10)")
    parser.add_argument("--genesis-hash", default="0x0000000000000000000000000000000000000000000000000000000000000000", 
                        help="Hash of the genesis block (default is zero hash)")
    parser.add_argument("--blocks-file", help="Path to the blocks file (default: scripts/blocks.json)")
    parser.add_argument("--compare", action="store_true", help="Compare chain.rlp and chain1.rlp files")
    parser.add_argument("--to-json", action="store_true", help="Convert RLP to JSON")
    parser.add_argument("--to-rlp", action="store_true", help="Convert JSON to RLP")
    args = parser.parse_args()

    if args.decode:
        read_and_decode_rlp(args.output_file)
    elif args.to_json:
        rlp_blocks = read_rlp_file(args.blocks_file)
        json_blocks = rlp_to_json(rlp_blocks)
        save_json_blocks(json_blocks, args.output_file)
    elif args.to_rlp:
        blocks = read_blocks_from_file(args.blocks_file)
        recalculated_blocks = recalculate_block_hashes(blocks, args.genesis_hash)
        save_rlp_to_file(recalculated_blocks, args.output_file)
    elif args.blocks_file:
        blocks = read_blocks_from_file(args.blocks_file)
        recalculated_blocks = recalculate_block_hashes(blocks, args.genesis_hash)
        save_rlp_to_file(recalculated_blocks, args.output_file)
    else:
        client = JsonRpcClient(args.rpc_url)
        blocks = fetch_last_n_blocks(client, args.num_blocks, args.genesis_hash)
        save_rlp_to_file(blocks, args.output_file)

    if args.compare:
        print_rlp_hexdump("scripts/chain.rlp")
        print()
        print_rlp_hexdump("scripts/chain1.rlp")

if __name__ == "__main__":
    main()
