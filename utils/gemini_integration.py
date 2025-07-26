"""
Gemini Integration Module for Pizza AI
Handles all Gemini Flash model interactions for intent parsing and response generation
"""

import json
from typing import Dict, Any, Optional
from .config import FLASH_MODEL

class GeminiChatHandler:
    """Handles Gemini-powered chat interactions"""
    
    def __init__(self):
        self.model = FLASH_MODEL
    
    def parse_user_intent(self, message: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Parse user message using Gemini to determine intent and extract relevant information
        """
        user_name = user_context.get("user_name", "") if user_context else ""
        user_email = user_context.get("user_email", "") if user_context else ""
        
        prompt = f"""
        You are an AI assistant for Pizza Planet, a pizza restaurant. Analyze this user message and determine their intent.
        
        User message: "{message}"
        User context: Name: {user_name}, Email: {user_email}
        
        Available pizza categories: veg, non-veg
        Available pizzas:
        VEG: Margherita, Veggie Supreme, Paneer Tikka, Mushroom Delight
        NON-VEG: Pepperoni Classic, BBQ Chicken, Meat Lovers, Chicken Supreme
        
        CONFIRMATION PHRASES - These should be classified as "confirm" intent:
        - "I want BBQ large", "please order this only", "yes please order this"
        - "I want this only", "confirm the order", "okay go ahead"
        - "yes", "confirm", "place order", "proceed", "order this"
        - "go ahead", "that's right", "correct", "book it"
        
        TRACKING PHRASES - These should be classified as "track" intent:
        - "Where is my order?", "What is the status of my order?"
        - "Track my order", "Give me order update", "Show delivery progress"
        - "Check my order", "Order status", "Delivery update"
        
        ORDER PHRASES - These should be classified as "order" intent:
        - "I want [pizza name]", "Order [pizza]", "Get me [pizza]"
        - "Can I have [pizza]", "I'll take [pizza]"
        
        Respond in JSON format:
        {{
            "intent": "greeting|menu|order|track|confirm|recommendation|casual",
            "action": "show_menu|process_order|show_tracking|confirm_order|provide_recommendation|continue_chat",
            "category": "veg|non-veg|all|null",
            "specific_items": ["item1", "item2"],
            "confidence": 0.8,
            "extracted_pizza": "pizza_name_if_mentioned",
            "extracted_size": "size_if_mentioned",
            "response_context": {{
                "friendly_tone": true,
                "personalized": true,
                "include_emojis": true
            }}
        }}
        
        Intent definitions:
        - "greeting": Hi, hello, welcome messages
        - "menu": Show menu, what options, what do you have
        - "order": I want, order, buy, get (specific pizza) - NEW ORDER REQUEST
        - "confirm": Confirmation of existing order (yes, confirm, go ahead, order this)
        - "track": Track order, order status, where is my order
        - "recommendation": What do you recommend, suggest something
        - "casual": General conversation, questions about restaurant
        
        Category detection:
        - If user mentions "veg", "vegetarian", "plant-based" → category: "veg"
        - If user mentions "non-veg", "meat", "chicken", "pepperoni" → category: "non-veg"
        - If general menu request → category: "all"
        
        Be precise with intent classification. ALWAYS distinguish between "order" (new order) and "confirm" (confirming existing order).
        """
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Clean JSON response
            if result_text.startswith("```"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()
            
            intent_data = json.loads(result_text)
            
            # Validate and set defaults
            intent_data["confidence"] = intent_data.get("confidence", 0.7)
            intent_data["category"] = intent_data.get("category", "all")
            intent_data["specific_items"] = intent_data.get("specific_items", [])
            intent_data["extracted_pizza"] = intent_data.get("extracted_pizza", "")
            intent_data["extracted_size"] = intent_data.get("extracted_size", "")
            
            print(f"🧠 Gemini Intent Analysis: '{message}' → {intent_data}")
            return intent_data
            
        except Exception as e:
            print(f"⚠️ Gemini intent parsing failed: {e}")
            # Enhanced fallback logic
            return self._fallback_intent_detection(message)
    
    def _fallback_intent_detection(self, message: str) -> Dict[str, Any]:
        """Fallback intent detection when Gemini fails"""
        message_lower = message.lower()
        
        # Enhanced confirmation detection
        confirmation_phrases = [
            "yes", "confirm", "place order", "proceed", "go ahead", 
            "that's right", "correct", "book it", "order this",
            "please order this", "i want this only", "okay go ahead"
        ]
        
        # Enhanced tracking detection
        tracking_phrases = [
            "track", "status", "where is", "my order", "delivery progress",
            "order update", "check my order", "delivery update"
        ]
        
        if any(phrase in message_lower for phrase in confirmation_phrases):
            return {"intent": "confirm", "action": "confirm_order", "category": "all", "confidence": 0.9}
        elif any(phrase in message_lower for phrase in tracking_phrases):
            return {"intent": "track", "action": "show_tracking", "category": "all", "confidence": 0.8}
        elif any(word in message_lower for word in ["order", "buy", "get", "want", "need"]):
            return {"intent": "order", "action": "process_order", "category": "all", "confidence": 0.7}
        elif any(word in message_lower for word in ["menu", "show", "options", "pizzas"]):
            # Detect category in fallback
            if any(word in message_lower for word in ["non-veg", "meat", "chicken", "pepperoni"]):
                category = "non-veg"
            elif any(word in message_lower for word in ["veg", "vegetarian"]):
                category = "veg"
            else:
                category = "all"
            return {"intent": "menu", "action": "show_menu", "category": category, "confidence": 0.6}
        elif any(word in message_lower for word in ["hi", "hello", "hey"]):
            return {"intent": "greeting", "action": "greet", "category": "all", "confidence": 0.8}
        else:
            return {"intent": "casual", "action": "continue_chat", "category": "all", "confidence": 0.5}
    
    def generate_welcome_message(self, user_name: str, is_new_user: bool = False) -> str:
        """Generate personalized welcome message using Gemini"""
        
        prompt = f"""
        Generate a warm, friendly welcome message for Pizza Planet restaurant.
        
        User name: {user_name}
        Is new user: {is_new_user}
        
        If new user: Welcome them like "Welcome [Name]! Glad to have you at Pizza Planet!"
        If returning user: Welcome them back warmly
        
        Make it:
        - Warm and personal
        - Pizza restaurant themed
        - Include appropriate emojis
        - 1-2 sentences max
        - Enthusiastic but not overwhelming
        
        Just return the welcome message text, no JSON.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"⚠️ Gemini welcome message failed: {e}")
            # Fallback welcome messages
            if is_new_user:
                return f"🍕 Welcome {user_name}! Glad to have you at Pizza Planet! Ready to explore our delicious menu?"
            else:
                return f"🍕 Welcome back, {user_name}! Ready for another amazing pizza experience?"
    
    def generate_contextual_response(self, context: str, user_data: Optional[Dict] = None, **kwargs) -> str:
        """Generate contextual responses using Gemini"""
        
        user_name = user_data.get("user_name", "") if user_data else ""
        
        prompt = f"""
        You are a friendly Pizza Planet restaurant assistant. Generate an appropriate response.
        
        Context: {context}
        User name: {user_name}
        Additional context: {kwargs}
        
        Make the response:
        - Friendly and conversational
        - Pizza restaurant themed
        - Use the user's name naturally if provided
        - Include appropriate emojis
        - Helpful and engaging
        
        Just return the response text, no JSON.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"⚠️ Gemini response generation failed: {e}")
            # Fallback responses
            if "order confirmed" in context:
                return f"🎉 Thanks{f', {user_name}' if user_name else ''}! Your order is confirmed and being prepared! 🍕"
            elif "no orders" in context:
                return f"Hi{f' {user_name}' if user_name else ''}! You don't have any ongoing orders. Try one of our delicious specials? 🍕"
            else:
                return "How can I help you with your pizza order today? 🍕"

    def generate_order_confirmation_response(self, order_data: Dict, user_name: str = "") -> str:
        """Generate order confirmation response using Gemini"""
        
        items_text = ", ".join([f"{item['name']} ({item['size']})" for item in order_data.get('items', [])])
        
        prompt = f"""
        Generate an enthusiastic order confirmation message for Pizza Planet.
        
        Order details:
        - Items: {items_text}
        - Total: ${order_data.get('total_price', 0):.2f}
        - Order ID: {order_data.get('order_id', 'N/A')}
        - User name: {user_name}
        - ETA: {order_data.get('eta', 'being calculated')}
        
        Create a response that:
        - Celebrates the order confirmation with 🎉
        - Uses the user's name if provided
        - Mentions the specific items ordered
        - Includes the order ID
        - Mentions the ETA
        - Is enthusiastic but professional
        - Uses appropriate pizza emojis
        
        Example: "Great! Your order has been confirmed 🎉 [Name], your [items] will be ready in [ETA]!"
        
        Just return the confirmation message, no JSON.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"⚠️ Gemini confirmation response failed: {e}")
            # Fallback confirmation message
            user_part = f", {user_name}" if user_name else ""
            return f"🎉 Great! Your order has been confirmed{user_part}! Order #{order_data.get('order_id', 'N/A')} - {items_text}. ETA: {order_data.get('eta', 'being calculated')} 🍕"

# Global instance
gemini_chat = GeminiChatHandler() 