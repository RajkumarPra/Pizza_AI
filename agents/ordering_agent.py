import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.config import FLASH_MODEL
from utils.menu import find_menu_item, suggest_similar_items, MENU
import requests
import json

def extract_pizza_info(user_input: str) -> dict:
    """Extract pizza name and size from user input using Gemini"""
    prompt = f"""
    You are a smart AI pizza assistant for Pizza Planet.

    Extract the pizza name and size from: "{user_input}"

    Available pizzas:
    VEG: Margherita, Veggie Supreme, Paneer Tikka, Mushroom Delight
    NON-VEG: Pepperoni Classic, BBQ Chicken, Meat Lovers, Chicken Supreme

    Available sizes: Small, Medium, Large

    Respond ONLY in JSON format:
    {{ "name": "BBQ Chicken", "size": "Large" }}

    If you can't determine the size, use "Large" as default.
    Match pizza names closely to the available options.
    """
    
    try:
        response = FLASH_MODEL.generate_content(prompt)
        cleaned = response.text.strip()

        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()

        # Use json.loads instead of eval for safety
        parsed = json.loads(cleaned)
        
        print(f"🧠 Gemini extracted: {parsed}")
        return parsed
        
    except Exception as e:
        print(f"❌ Error extracting pizza info: {e}")
        return {"error": f"Failed to parse order: {e}"}

def place_order(user_input: str):
    """Place order using MCP server (not used directly anymore)"""
    parsed = extract_pizza_info(user_input)

    if "error" in parsed:
        return {
            "status": "error",
            "message": "Sorry, we couldn't understand your order. Please specify the pizza name and size!",
            "raw": parsed
        }

    if not isinstance(parsed, dict) or "name" not in parsed or "size" not in parsed:
        return {
            "status": "error",
            "message": "Sorry, we couldn't understand your order. Please try rephrasing it!",
            "raw": parsed
        }

    # Check if pizza is available using new MCP functions
    found_item = find_menu_item(parsed["name"], parsed["size"])
    if not found_item:
        # Get suggestions
        suggestions = suggest_similar_items(parsed["name"])
        if suggestions:
            suggestion_text = ", ".join([f"{item['name']} ({item['size']})" for item in suggestions[:2]])
            return {
                "status": "error",
                "message": f"Sorry, '{parsed['size']} {parsed['name']}' is not available. Did you mean: {suggestion_text}?"
            }
        else:
            return {
                "status": "error",
                "message": f"Sorry, '{parsed['size']} {parsed['name']}' is not on our menu."
            }

    print(f"✅ Found pizza: {found_item}")

    try:
        # Use correct port 8001 for MCP server
        res = requests.post("http://localhost:8001/api/order", json={
            "items": [found_item["name"]],
            "address": "123 Main Street",
            "phone": "555-0123"
        })
        
        if res.status_code != 200:
            return {"status": "error", "message": "Server error while placing order"}
        return res.json()
    except Exception as e:
        print(f"❌ Order request failed: {e}")
        return {"status": "error", "message": f"Request failed: {e}"}

def track_order(order_id: str):
    """Track order using MCP server"""
    try:
        # Use correct port 8001 for MCP server  
        res = requests.get(f"http://localhost:8001/api/order/{order_id}")
        if res.status_code == 200:
            return res.json()
        else:
            return {"status": "error", "message": "Order not found or server error"}
    except Exception as e:
        return {"status": "error", "message": f"Request failed: {e}"}
