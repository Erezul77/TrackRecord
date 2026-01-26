#!/usr/bin/env python3
import requests

# Simulate browser preflight request
url = "https://api.trackrecord.life/api/community/register"

print("=== Testing OPTIONS preflight ===")
response = requests.options(url, headers={
    "Origin": "https://trackrecord.life",
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type"
})
print(f"Status: {response.status_code}")
print(f"CORS Headers:")
for k, v in response.headers.items():
    if 'access-control' in k.lower() or 'origin' in k.lower():
        print(f"  {k}: {v}")

print("\n=== Testing actual POST ===")
response = requests.post(url, 
    json={"username": "corstest123", "email": "corstest123@test.com", "password": "test123"},
    headers={"Origin": "https://trackrecord.life"}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
print(f"CORS Headers:")
for k, v in response.headers.items():
    if 'access-control' in k.lower() or 'origin' in k.lower():
        print(f"  {k}: {v}")
