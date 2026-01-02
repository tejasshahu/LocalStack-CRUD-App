import requests

API_URL = "http://localhost:4566/restapis/3tc6jlumhp/dev/_user_request_/images"

payload = {
    "image_id": "5dcb98af-958d-4ee6-82f3-7a3c6c6e9550",
}

response = requests.delete(API_URL, json=payload)
print(response.status_code)
print(response.json())