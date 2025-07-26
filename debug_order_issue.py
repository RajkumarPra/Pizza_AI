#!/usr/bin/env python3
"""
Debug the ordering issue step by step
"""

import requests
import json

def debug_order_flow():
    base_url = "http://localhost:8001/api"
    
    print("🔍 Debugging Pizza Planet Order Flow...")
    print("=" * 50)
    
    # Test 1: Menu lookup
    print("\n1. Testing menu lookup...")
    try:
        response = requests.get(f"{base_url}/menu")
        if response.status_code == 200:
            menu_data = response.json()
            print(f"✅ Menu loaded: {len(menu_data['pizzas'])} pizzas")
            
            # Show available pizzas
            print("Available pizzas:")
            for pizza in menu_data['pizzas']:
                print(f"  - {pizza['name']} ({pizza['size']}) - ${pizza['price']}")
        else:
            print(f"❌ Menu failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Menu error: {e}")
        return
    
    # Test 2: Chat order initiation
    print("\n2. Testing chat order initiation...")
    test_messages = [
        "I want BBQ Chicken large",
        "I want a large BBQ Chicken",
        "Order BBQ Chicken",
        "Can I get BBQ Chicken large size"
    ]
    
    for message in test_messages:
        print(f"\nTesting: '{message}'")
        try:
            chat_payload = {
                "message": message,
                "user_id": "debug_user",
                "context": {
                    "email": "debug@test.com",
                    "name": "Debug User"
                }
            }
            
            response = requests.post(f"{base_url}/chat", json=chat_payload)
            if response.status_code == 200:
                data = response.json()
                print(f"  Intent: {data['intent']}")
                print(f"  Action: {data['action']}")
                print(f"  Response: {data['response'][:80]}...")
                
                if data['action'] == 'await_confirmation':
                    print("  ✅ Order ready for confirmation")
                    
                    # Test confirmation
                    print("\n  Testing confirmation...")
                    confirm_payload = {
                        "message": "yes confirm",
                        "user_id": "debug_user",
                        "context": {
                            "email": "debug@test.com",
                            "name": "Debug User"
                        }
                    }
                    
                    confirm_response = requests.post(f"{base_url}/chat", json=confirm_payload)
                    if confirm_response.status_code == 200:
                        confirm_data = confirm_response.json()
                        print(f"  Confirm Intent: {confirm_data['intent']}")
                        print(f"  Confirm Action: {confirm_data['action']}")
                        print(f"  Confirm Response: {confirm_data['response'][:80]}...")
                        
                        if confirm_data['action'] == 'order_placed':
                            print("  🎉 Order successfully placed!")
                            if confirm_data.get('context', {}).get('order_id'):
                                order_id = confirm_data['context']['order_id']
                                print(f"  Order ID: {order_id}")
                                
                                # Test order tracking
                                print(f"\n  Testing order tracking for {order_id}...")
                                track_response = requests.get(f"{base_url}/order/{order_id}")
                                if track_response.status_code == 200:
                                    track_data = track_response.json()
                                    print(f"  ✅ Order tracked: {track_data['status']}")
                                    print(f"  ETA: {track_data['estimated_time']}")
                                else:
                                    print(f"  ❌ Track failed: {track_response.status_code}")
                            break
                        else:
                            print(f"  ❌ Confirmation failed - unexpected action: {confirm_data['action']}")
                    else:
                        print(f"  ❌ Confirmation request failed: {confirm_response.status_code}")
                        print(f"  Error: {confirm_response.text}")
                else:
                    print(f"  ❌ Order not ready for confirmation - action: {data['action']}")
                    if data.get('suggested_items'):
                        print(f"  Suggested items: {len(data['suggested_items'])}")
            else:
                print(f"  ❌ Chat failed: {response.status_code}")
                print(f"  Error: {response.text}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Test 3: Direct API order test
    print("\n3. Testing direct API order...")
    try:
        order_payload = {
            "items": ["BBQ Chicken"],
            "address": "123 Debug Street",
            "phone": "555-DEBUG",
            "user_id": "debug_user",
            "email": "debug@test.com"
        }
        
        response = requests.post(f"{base_url}/order", json=order_payload)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            order_data = response.json()
            print(f"✅ Direct order successful!")
            print(f"  Order ID: {order_data['order_id']}")
            print(f"  Total: ${order_data['total_price']}")
            print(f"  ETA: {order_data['estimated_time']}")
        else:
            print(f"❌ Direct order failed")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Direct order error: {e}")

if __name__ == "__main__":
    debug_order_flow() 