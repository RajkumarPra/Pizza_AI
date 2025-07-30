"""
Groq LLM Integration for Pizza AI
Replaces Gemini with Groq's Llama-7B model
"""

import os
from typing import Dict, List, Optional, Any
from groq import Groq
from dotenv import load_dotenv
import json
import re

# Load environment variables
load_dotenv()

class GroqChat:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.1-8b-instant"  # Using Llama 7B model
    
    def _generate_response(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate response using Groq API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ Groq API error: {e}")
            return "I'm having trouble processing your request. Please try again!"
    
    def parse_user_intent(self, message: str, context: Dict[str, Any]) -> Dict[str, str]:
        """Parse user intent using Groq"""
        user_name = context.get("user_name", "")
        
        prompt = f"""
        Analyze this pizza ordering message and determine the user's intent.
        
        Message: "{message}"
        User name: {user_name}
        
        Return ONLY a JSON object with these fields:
        - "intent": one of [order, track, menu, confirm, greeting, recommendation, casual]
        - "action": suggested next action
        - "category": if menu intent, specify "veg", "non-veg", or null
        
        Examples:
        - "I want a pepperoni pizza" → {{"intent": "order", "action": "process_order", "category": null}}
        - "show me veg options" → {{"intent": "menu", "action": "show_menu", "category": "veg"}}
        - "track my order" → {{"intent": "track", "action": "track_order", "category": null}}
        - "yes" or "confirm" → {{"intent": "confirm", "action": "confirm_order", "category": null}}
        
        JSON only:
        """
        
        try:
            response = self._generate_response(prompt, max_tokens=200)
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback parsing
                return self._fallback_intent_parsing(message)
        except:
            return self._fallback_intent_parsing(message)
    
    def _fallback_intent_parsing(self, message: str) -> Dict[str, str]:
        """Fallback intent parsing if Groq fails"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["yes", "confirm", "ok", "proceed"]):
            return {"intent": "confirm", "action": "confirm_order", "category": None}
        elif any(word in message_lower for word in ["track", "status", "order", "check"]):
            return {"intent": "track", "action": "track_order", "category": None}
        elif any(word in message_lower for word in ["menu", "options", "available", "veg", "non-veg"]):
            category = "veg" if "veg" in message_lower and "non-veg" not in message_lower else "non-veg" if "non-veg" in message_lower else None
            return {"intent": "menu", "action": "show_menu", "category": category}
        elif any(word in message_lower for word in ["recommend", "suggest", "popular", "best"]):
            return {"intent": "recommendation", "action": "show_recommendations", "category": None}
        elif any(word in message_lower for word in ["pizza", "order", "want", "get"]):
            return {"intent": "order", "action": "process_order", "category": None}
        elif any(word in message_lower for word in ["hello", "hi", "hey", "welcome"]):
            return {"intent": "greeting", "action": "continue_chat", "category": None}
        else:
            return {"intent": "casual", "action": "continue_chat", "category": None}
    
    def generate_contextual_response(self, context_type: str, user_context: Dict[str, Any], **kwargs) -> str:
        """Generate contextual responses for different scenarios"""
        user_name = user_context.get("user_name", "")
        name_part = f" {user_name}" if user_name else ""
        
        if context_type == "order confirmation request":
            item = kwargs.get("item", {})
            return f"Great choice{name_part}! I found {item.get('name', 'a pizza')} ({item.get('size', 'regular')}) for ${item.get('price', 0):.2f}. Would you like to confirm this order? 🍕"
        
        elif context_type == "latest order status update":
            order_id = kwargs.get("order_id", "")
            status = kwargs.get("status", "placed")
            items = kwargs.get("items", [])
            items_text = ", ".join([f"{item.get('name', '')} ({item.get('size', '')})" for item in items])
            
            status_messages = {
                "placed": f"📋 Great news{name_part}! Your latest order #{order_id} has been placed successfully! Items: {items_text}",
                "preparing": f"⏲️ Your latest order #{order_id} is being prepared{name_part}! Our chefs are getting started on: {items_text}",
                "cooking": f"🔥 Your latest order #{order_id} is cooking{name_part}! The oven is working its magic on: {items_text}",
                "ready": f"📦 Excellent news{name_part}! Your latest order #{order_id} is ready for pickup/delivery! Items: {items_text}",
                "delivered": f"🚚 Order #{order_id} has been delivered{name_part}! Enjoy your: {items_text}"
            }
            return status_messages.get(status, f"Your latest order #{order_id} is {status}{name_part}!")
        
        elif context_type == "no orders found - suggest new order":
            return f"Hi{name_part}! I don't see any recent orders for you. Would you like to browse our menu and place a new order? 🍕"
        
        elif context_type == "order not found":
            return f"I couldn't find that order{name_part}. Would you like to see our menu or check your recent orders? 🍕"
        
        elif context_type == "no pending order":
            return f"Hi{name_part}! There's no pending order to confirm. Would you like to browse our menu and start a new order? 🍕"
        
        elif context_type == "pizza recommendations":
            items = kwargs.get("items", [])
            items_text = ", ".join([item.get("name", "") for item in items[:4]])
            return f"Here are my top recommendations{name_part}: {items_text}! All of these are customer favorites. What sounds good to you? 🍕"
        
        elif context_type == "casual conversation":
            original_message = kwargs.get("original_message", "")
            return f"Thanks for chatting{name_part}! I'm here to help with pizza orders. Would you like to see our menu or place an order? 🍕"
        
        else:
            return f"How can I help you today{name_part}? 🍕"
    
    def generate_welcome_message(self, user_name: str, is_new_user: bool) -> str:
        """Generate welcome message"""
        if is_new_user:
            return f"🍕 Welcome to Pizza Planet, {user_name}! Thanks for joining us. What delicious pizza can I help you order today?"
        else:
            return f"🍕 Welcome back, {user_name}! Ready for another amazing pizza experience? What can I get for you today?"
    
    def generate_order_confirmation_response(self, order_data: Dict[str, Any], user_name: str = "") -> str:
        """Generate order confirmation message"""
        name_part = f" {user_name}" if user_name else ""
        order_id = order_data.get("order_id", "")
        items = order_data.get("items", [])
        total_price = order_data.get("total_price", 0)
        eta = order_data.get("eta", "being calculated")
        
        items_text = ", ".join([f"{item.get('name', '')} ({item.get('size', '')})" for item in items])
        
        return f"""🎉 Awesome{name_part}! Your order has been confirmed!

📋 Order #{order_id}
🍕 Items: {items_text}
💰 Total: ${total_price:.2f}
⏰ ETA: {eta}

Thank you for choosing Pizza Planet! We'll keep you updated on your order status. 🚀"""

# Create global instance
groq_chat = GroqChat()