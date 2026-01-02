import requests
import base64

API_URL = "http://localhost:4566/restapis/3tc6jlumhp/dev/_user_request_/images"
IMAGE_PATH = "./BeKind.jpeg" # Make sure this file exists

with open(IMAGE_PATH, "rb") as image_file:
    # Read and encode to base64 string
    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

payload = {
    "filename": "./BeKind.jpeg",
    "data": encoded_string,
    "owner": "bob3",
    "category": "travel3"
}

response = requests.post(API_URL, json=payload)
print(response.status_code)
print(response.json())