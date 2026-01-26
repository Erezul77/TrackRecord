#!/usr/bin/env python3
import requests
import json

url = "http://127.0.0.1:8000/api/community/register"
data = {
    "username": "testuser999",
    "email": "testuser999@example.com",
    "password": "testpass123"
}

response = requests.post(url, json=data)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
