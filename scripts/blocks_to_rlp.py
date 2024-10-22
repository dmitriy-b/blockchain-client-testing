import rlp
from typing import List, Union, Dict, Any, Tuple
from eth_utils import decode_hex, encode_hex, int_to_big_endian, remove_0x_prefix
from eth_typing import HexStr
import json
import argparse

class Header(rlp.Serializable):
    fields = [
        ('parentHash', rlp.sedes.binary),
        ('sha3Uncles', rlp.sedes.binary),
        ('miner', rlp.sedes.binary),
        ('stateRoot', rlp.sedes.binary),
        ('transactionsRoot', rlp.sedes.binary),
        ('receiptsRoot', rlp.sedes.binary),
        ('logsBloom', rlp.sedes.binary),
        ('difficulty', rlp.sedes.big_endian_int),
        ('number', rlp.sedes.big_endian_int),
        ('gasLimit', rlp.sedes.big_endian_int),
        ('gasUsed', rlp.sedes.big_endian_int),
        ('timestamp', rlp.sedes.big_endian_int),
        ('extraData', rlp.sedes.binary),
        ('mixHash', rlp.sedes.binary),
        ('nonce', rlp.sedes.binary),
        ('baseFeePerGas', rlp.sedes.big_endian_int),
        ('withdrawalsRoot', rlp.sedes.binary),
        ('blobGasUsed', rlp.sedes.big_endian_int),
        ('excessBlobGas', rlp.sedes.big_endian_int),
        ('parentBeaconBlockRoot', rlp.sedes.binary),
    ]

class Block(rlp.Serializable):
    fields = [
        ('header', Header),
        ('transactions', rlp.sedes.CountableList(rlp.sedes.binary)),
        ('uncles', rlp.sedes.CountableList(Header))
    ]

def encode_scalar(value: Union[int, str], field_name: str = '') -> Union[int, bytes]:
    if isinstance(value, str) and value.startswith('0x'):
        if field_name == 'logsBloom':
            # Ensure logsBloom is always 256 bytes
            return bytes.fromhex(remove_0x_prefix(HexStr(value)).zfill(512))
        return decode_hex(value)
    elif isinstance(value, int):
        return value
    else:
        raise ValueError(f"Unsupported scalar type: {type(value)}")

def convert_block_to_rlp(block: Dict[str, Any]) -> bytes:
    """
    Convert a block dictionary to RLP encoding.
    
    :param block: The block dictionary
    :return: RLP encoded bytes
    """
    header = Header(
        parentHash=encode_scalar(block['parentHash']),
        sha3Uncles=encode_scalar(block['sha3Uncles']),
        miner=encode_scalar(block['miner']),
        stateRoot=encode_scalar(block['stateRoot']),
        transactionsRoot=encode_scalar(block['transactionsRoot']),
        receiptsRoot=encode_scalar(block['receiptsRoot']),
        logsBloom=encode_scalar(block['logsBloom'], 'logsBloom'),
        difficulty=int(block['difficulty'], 16),
        number=int(block['number'], 16),
        gasLimit=int(block['gasLimit'], 16),
        gasUsed=int(block['gasUsed'], 16),
        timestamp=int(block['timestamp'], 16),
        extraData=encode_scalar(block['extraData']),
        mixHash=encode_scalar(block['mixHash']),
        nonce=encode_scalar(block['nonce']),
        baseFeePerGas=int(block['baseFeePerGas'], 16) if 'baseFeePerGas' in block else 0,
        withdrawalsRoot=encode_scalar(block['withdrawalsRoot']) if 'withdrawalsRoot' in block else b'',
        blobGasUsed=int(block['blobGasUsed'], 16) if 'blobGasUsed' in block else 0,
        excessBlobGas=int(block['excessBlobGas'], 16) if 'excessBlobGas' in block else 0,
        parentBeaconBlockRoot=encode_scalar(block['parentBeaconBlockRoot']) if 'parentBeaconBlockRoot' in block else b'',
    )
    
    full_block = Block(
        header=header,
        transactions=[],  # Empty for now
        uncles=[]  # Empty for now
    )
    
    return rlp.encode(full_block)

def read_blocks_from_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Read blocks from a file.
    
    :param file_path: Path to the file containing block data
    :return: List of block dictionaries
    """
    with open(file_path, 'r') as f:
        blocks = json.load(f)
    return blocks

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
        print_decoded_data(decoded_data)
    except Exception as e:
        print(f"Error decoding RLP data: {e}")

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
    
    if isinstance(data, List):
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

def main():
    parser = argparse.ArgumentParser(description="Convert blocks to RLP or decode RLP file")
    parser.add_argument("input_file", help="Path to the input file (JSON blocks or RLP)")
    parser.add_argument("output_file", help="Path to the output file")
    parser.add_argument("--decode", action="store_true", help="Decode RLP file instead of encoding")
    args = parser.parse_args()

    if args.decode:
        read_and_decode_rlp(args.input_file)
    else:
        blocks = read_blocks_from_file(args.input_file)
        save_rlp_to_file(blocks, args.output_file)

if __name__ == "__main__":
    main()
