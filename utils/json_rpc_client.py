import requests

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
        response = requests.post(self.url, json=payload)
        response.raise_for_status()
        return response.json()
