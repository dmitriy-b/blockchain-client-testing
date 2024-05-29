import requests
from loguru import logger

class JsonRpcClient:
    def __init__(self, url):
        self.url = url

    def call(self, method, params=None, call_id=1):
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params if params is not None else [],
            "id": call_id
        }
        logger.info(f"Sending {method} jsonrpc request to {self.url} with payload:\n {payload}")
        response = requests.post(self.url, json=payload)
        response.raise_for_status()
        result = response.json()
        logger.info("Response: {}", result)
        return result
