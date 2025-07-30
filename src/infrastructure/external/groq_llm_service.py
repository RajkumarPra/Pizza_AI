"""
Infrastructure - Groq LLM Service Implementation
Concrete implementation of LLM service using Groq API.
"""

import os
import json
import re
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from ...application.interfaces import ILLMService
from ...domain.entities import Order, Pizza

# Load environment variables
load_dotenv()


class GroqLLMService(ILLMService):
    """Groq implementation of LLM service"""
    
    def __init__(self):
        """Initialize Groq client"""
        try:
            from groq import Groq
            
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment variables")
            
            self.client = Groq(api_key=api_key)
            self.model = "llama-3.1-7b-instant"
            
        except ImportError:
            raise ImportError("Groq library not installed. Run: pip install groq")
    
    async def parse_user_intent(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Parse user message to determine intent and extract parameters"""
        
        if context is None:
            context = {}
        
        intent_prompt = f"""
        Analyze this pizza ordering message and determine the user's intent: "{message}"
        
        Context: {json.dumps(context)}
        
        Available intents:
        - get_menu: User wants to see the menu (categories: all/veg/non-veg)
        - find_pizza: User wants to find a specific pizza (extract: name, size)
        - place_order: User wants to place an order (extract: items, customer info)
        - track_order: User wants to track an order (extract: order_id or email)
        - check_user: User wants to check if they exist (extract: email)
        - save_user: User wants to save their info (extract: email, name)
        - get_suggestions: User wants recommendations (extract: preferences)
        - general_chat: General conversation or greetings
        
        Return ONLY a valid JSON object:
        {{
            "intent": "intent_name",
            "parameters": {{"param1": "value1", "param2": "value2"}},
            "confidence": 0.95,
            "explanation": "brief explanation"
        }}
        """
        
        try:
            response = self._generate_sync_response(intent_prompt, max_tokens=300)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback intent detection
                return self._fallback_intent_detection(message)
                
        except Exception as e:
            print(f"Intent parsing error: {e}")
            return self._fallback_intent_detection(message)
    
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Generate a response using the LLM"""
        return self._generate_sync_response(prompt)
    
    async def generate_order_confirmation_message(self, order: Order) -> str:
        """Generate order confirmation message"""
        
        items_list = ", ".join([item.display_name for item in order.items])
        
        prompt = f"""
        Generate a friendly order confirmation message for a pizza order.
        
        Order details:
        - Order ID: {order.id}
        - Customer: {order.customer.name}
        - Items: {items_list}
        - Total: {order.formatted_total}
        - ETA: {order.estimated_eta}
        
        Make it enthusiastic, include emojis, and mention the estimated delivery time.
        Keep it concise but warm.
        """
        
        return self._generate_sync_response(prompt, max_tokens=200)
    
    async def generate_tracking_message(self, order: Order) -> str:
        """Generate order tracking message"""
        
        items_list = ", ".join([item.display_name for item in order.items])
        
        prompt = f"""
        Generate a helpful order tracking message.
        
        Order details:
        - Order ID: {order.id}
        - Status: {order.status.value}
        - Items: {items_list}
        - ETA: {order.estimated_eta}
        - Customer: {order.customer.name}
        
        Make it informative, include appropriate emojis for the status, and reassuring.
        If the order is ready, be excited. If it's still cooking, be encouraging.
        """
        
        return self._generate_sync_response(prompt, max_tokens=200)
    
    async def generate_suggestions_message(self, pizzas: List[Pizza], preferences: str) -> str:
        """Generate pizza suggestions message"""
        
        pizza_list = []
        for pizza in pizzas[:5]:  # Limit to 5 suggestions
            pizza_list.append(f"{pizza.display_name} - {pizza.formatted_price} ({pizza.description})")
        
        suggestions_text = "\n".join(pizza_list)
        
        prompt = f"""
        Generate an enthusiastic message about pizza recommendations.
        
        Preferences: {preferences}
        Suggested pizzas:
        {suggestions_text}
        
        Make it appetizing, use food emojis, and encourage the customer to try something new.
        Be friendly and helpful.
        """
        
        return self._generate_sync_response(prompt, max_tokens=200)
    
    async def generate_welcome_message(self, user_name: Optional[str] = None, is_new_user: bool = False) -> str:
        """Generate welcome message"""
        
        name_part = f" {user_name}" if user_name else ""
        user_type = "new customer" if is_new_user else "returning customer"
        
        prompt = f"""
        Generate a warm welcome message for a pizza ordering system.
        
        Customer name: {user_name or "Customer"}
        User type: {user_type}
        
        Make it friendly, include pizza emojis, and mention what they can do (see menu, order, track orders).
        Keep it brief but welcoming.
        """
        
        return self._generate_sync_response(prompt, max_tokens=150)
    
    async def generate_error_message(self, error: str, context: Dict[str, Any] = None) -> str:
        """Generate user-friendly error message"""
        
        prompt = f"""
        Convert this technical error into a friendly, helpful message for a pizza customer:
        
        Error: {error}
        Context: {json.dumps(context or {})}
        
        Make it apologetic, suggest what they can try instead, and keep the tone light.
        Don't include technical details.
        """
        
        return self._generate_sync_response(prompt, max_tokens=100)
    
    def _generate_sync_response(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate response synchronously"""
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a helpful assistant for a pizza ordering system. Be friendly, concise, and use appropriate emojis."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return completion.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Groq API error: {e}")
            return "I'm having trouble generating a response right now. Please try again!"
    
    def _fallback_intent_detection(self, message: str) -> Dict[str, Any]:
        """Simple fallback intent detection"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["menu", "show", "list", "what do you have"]):
            return {"intent": "get_menu", "parameters": {"category": "all"}, "confidence": 0.8}
        elif any(word in message_lower for word in ["track", "order", "status", "where is"]):
            return {"intent": "track_order", "parameters": {}, "confidence": 0.8}
        elif any(word in message_lower for word in ["suggest", "recommend", "popular", "best"]):
            return {"intent": "get_suggestions", "parameters": {"preferences": "popular"}, "confidence": 0.8}
        elif any(word in message_lower for word in ["pizza", "want", "order", "buy"]):
            return {"intent": "find_pizza", "parameters": {"name": "margherita", "size": "large"}, "confidence": 0.7}
        else:
            return {"intent": "general_chat", "parameters": {}, "confidence": 0.6} 