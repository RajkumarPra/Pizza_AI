#!/usr/bin/env python3
"""
Test to debug frontend vs Postman payload differences
"""

import requests
import json

def test_different_payloads():
    base_url = "http://localhost:8001/api"
    
    print("🔍 Testing Different Payload Formats...")
    print("=" * 60)
    
    # Test 1: Postman-style payload (what works)
    print("\n1. Testing Postman-style payload (should work):")
    postman_payload = {
        "items": ["BBQ Chicken"],
        "address": "123 Main Street",
        "phone": "555-0123",
        "user_id": "postman_user",
        "email": "postman@test.com"
    }
    
    print("Payload:", json.dumps(postman_payload, indent=2))
    
    try:
        response = requests.post(f"{base_url}/order", json=postman_payload)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Postman-style: SUCCESS")
            print(f"Response: {response.json()}")
        else:
            print("❌ Postman-style: FAILED")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: Frontend-style payload (what should work after our fixes)
    print("\n2. Testing Frontend-style payload (should work now):")
    frontend_payload = {
        "items": ["BBQ Chicken"],
        "address": "123 Main Street",
        "phone": "555-0123",
        "user_id": "frontend_user",
        "email": "frontend@pizza-planet.com"
    }
    
    print("Payload:", json.dumps(frontend_payload, indent=2))
    
    try:
        response = requests.post(f"{base_url}/order", json=frontend_payload)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Frontend-style: SUCCESS")
            print(f"Response: {response.json()}")
        else:
            print("❌ Frontend-style: FAILED")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 3: Bad payload (missing required fields)
    print("\n3. Testing Bad payload (missing user_id and email):")
    bad_payload = {
        "items": ["BBQ Chicken"],
        "address": "123 Main Street",
        "phone": "555-0123"
        # Missing user_id and email
    }
    
    print("Payload:", json.dumps(bad_payload, indent=2))
    
    try:
        response = requests.post(f"{base_url}/order", json=bad_payload)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Bad payload: SUCCESS (unexpected)")
        else:
            print("❌ Bad payload: FAILED (expected)")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

    # Test 4: Check what's in the server logs
    print("\n4. Server should show debug info in the terminal running the MCP server")
    print("Check the server terminal for any error messages when placing orders from frontend")

if __name__ == "__main__":
    test_different_payloads() 