import requests


class AriProxyClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def post_end_call(self, call_id, timestamp):
        url = f"{self.base_url}/ari-proxy/event"  # Replace with the actual endpoint path
        data = {
            "type": "END_CALL",
            "callId": call_id,
            "timestamp": timestamp
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(url, json=data, headers=headers)

        if response.status_code != 200:
            raise Exception(f"Failed to post data: {response.status_code} {response.text}")

        return response.json()
