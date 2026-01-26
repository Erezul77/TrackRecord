#!/usr/bin/env python3
import requests
import json

# Test via HTTPS
url = "https://api.trackrecord.life/api/community/register"
data = {
    "username": "testuser888",
    "email": "testuser888@example.com",
    "password": "testpass123"
}

print(f"Testing: {url}")
response = requests.post(url, json=data)
print(f"Status: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
print(f"Response: {response.text}")
