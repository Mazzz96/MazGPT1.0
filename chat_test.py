import requests

url = "http://127.0.0.1:8000/chat/send/"
session = requests.Session()

# Get CSRF token from /ping
resp = session.get("http://127.0.0.1:8000/ping")
csrf_token = resp.cookies.get("mazgpt-csrf")
print("CSRF token:", csrf_token)

headers = {"X-CSRF-Token": csrf_token}
cookies = {"mazgpt-csrf": csrf_token}
payload = {"message": "Hello! Which model are you?"}
response = session.post(url, json=payload, headers=headers, cookies=cookies)
print("Status:", response.status_code)
print("Response:", response.text)
