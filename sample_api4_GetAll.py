import requests

API_URL = "http://localhost:4566/restapis/3tc6jlumhp/dev/_user_request_/images"
response = requests.get(API_URL)
print(response.status_code)
print(response.json())