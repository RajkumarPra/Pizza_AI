#!/usr/bin/env python3
"""
Test the order flow to verify it's working correctly
"""

import requests
import json

# Test the order flow
def test_order_flow():
    base_url = "http://localhost:8001/api"
    
    print("🍕 Testing Pizza Planet Order Flow...")
    
    # Test 1: Check health
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Server is healthy")
        else:
            print("❌ Server health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # Test 2: Get menu
    try:
        response = requests.get(f"{base_url}/menu")
        if response.status_code == 200:
            menu_data = response.json()
            print(f"✅ Menu loaded: {len(menu_data['pizzas'])} pizzas available")
        else:
            print("❌ Failed to load menu")
            return
    except Exception as e:
        print(f"❌ Menu request failed: {e}")
        return
    
    # Test 3: Test chat-based ordering
    try:
        chat_payload = {
            "message": "I want BBQ Chicken large",
            "user_id": "test_user",
            "context": {
                "email": "test@example.com",
                "name": "Test User"
            }
        }
        
        response = requests.post(f"{base_url}/chat", json=chat_payload)
        if response.status_code == 200:
            chat_data = response.json()
            print(f"✅ Chat order initiation: {chat_data['intent']}")
            print(f"📝 Response: {chat_data['response'][:100]}...")
            
            if chat_data['intent'] == 'order' and chat_data['action'] == 'await_confirmation':
                print("✅ Order awaiting confirmation as expected")
                
                # Test 4: Confirm the order
                confirm_payload = {
                    "message": "yes confirm",
                    "user_id": "test_user",
                    "context": {
                        "email": "test@example.com",
                        "name": "Test User"
                    }
                }
                
                confirm_response = requests.post(f"{base_url}/chat", json=confirm_payload)
                if confirm_response.status_code == 200:
                    confirm_data = confirm_response.json()
                    print(f"✅ Order confirmation: {confirm_data['intent']}")
                    print(f"📝 Confirmation: {confirm_data['response'][:100]}...")
                    
                    if confirm_data['action'] == 'order_placed':
                        print("🎉 Order successfully placed!")
                        return True
                    else:
                        print(f"❌ Unexpected action: {confirm_data['action']}")
                else:
                    print(f"❌ Confirmation failed: {confirm_response.status_code}")
            else:
                print(f"❌ Unexpected intent/action: {chat_data['intent']}/{chat_data['action']}")
        else:
            print(f"❌ Chat request failed: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Chat order test failed: {e}")
        return False
    
    # Test 5: Direct API order (should work now)
    try:
        order_payload = {
            "items": ["BBQ Chicken"],
            "address": "123 Test Street",
            "phone": "555-TEST",
            "user_id": "test_user",
            "email": "test@example.com"
        }
        
        response = requests.post(f"{base_url}/order", json=order_payload)
        if response.status_code == 200:
            order_data = response.json()
            print(f"✅ Direct API order successful: Order #{order_data['order_id']}")
            print(f"💰 Total: ${order_data['total_price']}")
            print(f"⏰ ETA: {order_data['estimated_time']}")
        else:
            print(f"❌ Direct API order failed: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Direct API order test failed: {e}")

if __name__ == "__main__":
    test_order_flow() 