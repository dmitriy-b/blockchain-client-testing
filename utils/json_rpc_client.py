import requests
from loguru import logger
from web3 import Web3

class JsonRpcClient:
    def __init__(self, url):
        self.url = url
        
        # Configure Web3 provider with proper connection handling for macOS issues
        request_kwargs = {
            "timeout": 30,
            "headers": {
                "Content-Type": "application/json",
                "Connection": "close"  # Crucial for macOS connection issues
            }
        }
        
        # Create the Web3 provider with explicit connection closing
        self.web3 = Web3(Web3.HTTPProvider(url, request_kwargs=request_kwargs))

    def call(self, method, params=None, call_id=1):
        """Make a direct JSON-RPC call with proper connection handling"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params if params is not None else [],
            "id": call_id
        }
        logger.info(f"Sending {method} jsonrpc request to {self.url} with payload:\n {payload}")
        
        # Create a fresh session for each request
        session = None
        try:
            session = requests.Session()
            session.headers.update({
                "Content-Type": "application/json",
                "Connection": "close"  # Critical for macOS
            })
            
            # Make the request with an explicit timeout
            response = session.post(
                self.url, 
                json=payload, 
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            logger.info("Response: {}", result)
            return result
            
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            # Return a proper JSON-RPC error response
            return {
                "jsonrpc": "2.0",
                "id": call_id,
                "error": {
                    "code": -32000,
                    "message": f"Request failed: {str(e)}"
                }
            }
        finally:
            # Always close the session in a finally block
            if session:
                try:
                    session.close()
                except:
                    pass  # Ignore errors when closing
