import requests

API_URL = "http://localhost:4566/restapis/3tc6jlumhp/dev/_user_request_/images"

payload = {
    "image_id": "a4021347-5749-4c1b-a858-6163854430b5"
}

response = requests.get(API_URL, json=payload)
print(response.status_code)
print(response.json())