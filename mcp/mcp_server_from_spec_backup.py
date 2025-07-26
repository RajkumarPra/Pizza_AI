import yaml
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import uuid
import json
from utils.config import FLASH_MODEL
from utils.menu import (
    MENU, 
    find_menu_item, 
    suggest_similar_items, 
    get_menu_by_category, 
    get_all_categories,
    is_pizza_available, 
    suggest_similar_pizza
)

# MCP Server - Core Protocol for Pizza AI
app = FastAPI(title="Pizza AI MCP Server", description="Model Context Protocol server for Pizza AI system")

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (your Lovable frontend)
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

# Menu data now imported from utils/menu.py

# In-memory storage for orders, pending confirmations, and users
ORDERS = {}
PENDING_CONFIRMATIONS = {}
USERS = {}  # Email-based user storage

# Pydantic models for MCP protocol
class MCPChatRequest(BaseModel):
    message: str
    user_id: str = "default"
    context: Optional[dict] = None

class MCPChatResponse(BaseModel):
    response: str
    intent: str
    action: Optional[str] = None
    suggested_items: Optional[List[dict]] = None
    error: Optional[str] = None
    context: Optional[dict] = None
    pending_order: Optional[dict] = None  # Add pending order data

class MCPOrderRequest(BaseModel):
    items: List[str]
    address: str
    phone: str
    user_id: str = "default"
    email: Optional[str] = None  # Add email to orders

class MCPOrderResponse(BaseModel):
    order_id: str
    estimated_time: str
    total_price: float
    status: str = "placed"

class MCPUserRequest(BaseModel):
    email: str
    name: Optional[str] = None

class MCPUserResponse(BaseModel):
    email: str
    name: Optional[str] = None
    exists: bool
    orders_count: int = 0
    last_order_date: Optional[str] = None

# Gemini Integration Functions for MCP
def extract_item_info_via_gemini(user_input: str) -> dict:
    """Extract item information from order string using Gemini through MCP"""
    prompt = f"""
You are a smart AI pizza assistant. Extract item information from this order string: "{user_input}"

The order might contain:
- Quantity (like "2x", "3 pizzas")
- Item name (like "BBQ Chicken", "Margherita", "Coke")
- Size (like "Large", "Medium", "500ml", "6 pieces")

Available items in our menu:
PIZZAS: Margherita, Veggie Supreme, Paneer Tikka, Mushroom Delight, Pepperoni Classic, BBQ Chicken, Meat Lovers, Chicken Supreme
DRINKS: Coca Cola, Fresh Orange Juice, Sparkling Water  
SIDES: Garlic Bread, Chicken Wings, Mozzarella Sticks

Respond ONLY in JSON format:
{{
    "name": "item name",
    "size": "size if mentioned", 
    "quantity": 1,
    "category": "pizza|drink|side"
}}

If you can't extract clear information, respond with:
{{ "error": "Could not parse item information" }}
"""
    
    try:
        response = FLASH_MODEL.generate_content(prompt)
        result_text = response.text.strip()
        
        # Clean JSON response
        if result_text.startswith("```"):
            result_text = result_text.replace("```json", "").replace("```", "").strip()
        
        # Parse JSON response
        import json
        item_data = json.loads(result_text)
        
        return item_data
        
    except Exception as e:
        print(f"Error extracting item info: {e}")
        return {"error": f"Failed to parse item information: {e}"}

def interpret_intent_via_gemini(user_input: str) -> dict:
    """Enhanced Gemini-powered intent recognition for MCP routing"""
    prompt = f"""
You are an advanced AI assistant for a pizza restaurant. Analyze this user message and determine the intent and routing:

User message: "{user_input}"

Analyze for these intents and respond in JSON format:
{{
    "intent": "order|menu|track|schedule|health|casual|greeting|confirm",
    "confidence": 0.8,
    "specific_item": "item name if mentioned",
    "category": "veg|non-veg|none",
    "action": "show_menu|process_order|show_tracking|show_schedule|suggest_healthy|chat|confirm_order|none",
    "agent_route": "ordering_agent|scheduler_agent|menu_handler|gemini_chat|order_confirmation",
    "keywords": ["extracted", "keywords"],
    "context": {{
        "is_question": true/false,
        "mentions_health": true/false,
        "mentions_price": true/false,
        "is_greeting": true/false,
        "is_casual": true/false,
        "is_confirmation": true/false
    }}
}}

Intent definitions with priority for voice input:
- "confirm": User is confirming an order (keywords: yes, confirm, place order, proceed, do it, go ahead)
  * Voice patterns: "yes", "confirm", "place order", "proceed", "do it"
- "order": User wants to place an order (keywords: order, buy, get, purchase, I want, I'll have, I need, give me)
  * Voice patterns: "order large BBQ", "I want pizza", "get me a", "I'll have"
- "track": User wants to track existing order (keywords: track, check, status, where is, delivery, my order)
  * Voice patterns: "track my order", "where is my order", "order status", "check my order"
- "menu": User wants to see menu/options (keywords: menu, show, what do you have, options, list)
- "schedule": User wants to schedule delivery (keywords: schedule, when, time, later)
- "health": User asks about healthy options (keywords: healthy, diet, calories, nutrition, vegan, vegetarian)
- "casual": General conversation, jokes, or non-food related (keywords: how are you, tell me, what's up)
- "greeting": Greetings and introductions (keywords: hi, hello, hey, good morning)

CRITICAL RULES:
1. If message contains "yes", "confirm", "place order", "proceed", "do it" -> ALWAYS set intent="confirm" and agent_route="order_confirmation"
2. If message contains "track", "status", "where is", "my order", "check order" -> ALWAYS set intent="track" and agent_route="scheduler_agent"
3. If message contains order words + item name -> ALWAYS set intent="order" and agent_route="ordering_agent"
4. Voice input is often shorter - be flexible with matching
5. Only veg and non-veg pizza categories are available - no drinks or sides

Be precise with intent classification and confidence scoring.
"""
    
    try:
        response = FLASH_MODEL.generate_content(prompt)
        result_text = response.text.strip()
        
        # Clean JSON response
        if result_text.startswith("```"):
            result_text = result_text.replace("```json", "").replace("```", "").strip()
        
        # Parse JSON response
        import json
        intent_data = json.loads(result_text)
        
        # Validate and set defaults
        intent_data["confidence"] = intent_data.get("confidence", 0.5)
        intent_data["agent_route"] = intent_data.get("agent_route", "gemini_chat")
        intent_data["context"] = intent_data.get("context", {})
        
        return intent_data
        
    except Exception as e:
        print(f"Intent analysis error: {e}")
        # Enhanced fallback for voice input
        user_lower = user_input.lower()
        
        # Priority 1: Confirmation intent - must be caught first
        if any(word in user_lower for word in ["yes", "confirm", "place order", "proceed", "do it", "go ahead", "okay"]):
            return {
                "intent": "confirm",
                "confidence": 0.9,
                "action": "confirm_order",
                "agent_route": "order_confirmation",
                "context": {"fallback": True, "voice_optimized": True, "is_confirmation": True}
            }
        # Priority 2: Track intent - must be caught second
        elif any(word in user_lower for word in ["track", "status", "where is", "my order", "check order", "delivery"]):
            return {
                "intent": "track",
                "confidence": 0.8,
                "action": "show_tracking",
                "agent_route": "scheduler_agent",
                "context": {"fallback": True, "voice_optimized": True}
            }
        # Priority 3: Order intent with item detection
        elif any(word in user_lower for word in ["order", "buy", "get", "purchase", "want", "need", "i'll have"]):
            # Check if there's a pizza mentioned
            pizza_items = ["bbq", "margherita", "pepperoni", "veggie", "paneer", "mushroom", "chicken", "meat"]
            has_item = any(item in user_lower for item in pizza_items)
            
            return {
                "intent": "order",
                "confidence": 0.8 if has_item else 0.6,
                "action": "process_order",
                "agent_route": "ordering_agent",
                "context": {"fallback": True, "voice_optimized": True, "has_item": has_item}
            }
        elif any(word in user_lower for word in ["menu", "show", "options", "list"]):
            return {
                "intent": "menu",
                "confidence": 0.6,
                "action": "show_menu",
                "agent_route": "menu_handler",
                "context": {"fallback": True}
            }
        else:
            return {
                "intent": "casual",
                "confidence": 0.4,
                "action": "chat",
                "agent_route": "gemini_chat",
                "context": {"fallback": True}
            }

def route_to_ordering_agent(user_input: str, context: dict = None) -> dict:
    """Route order requests to ordering_agent.py through MCP"""
    try:
        # Import ordering agent functions  
        agents_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'agents'))
        if agents_path not in sys.path:
            sys.path.insert(0, agents_path)
        from ordering_agent import extract_pizza_info, place_order
        
        # Extract item information using the agent
        extracted_info = extract_pizza_info(user_input)
        
        if "error" in extracted_info:
            return {
                "status": "error",
                "message": "I couldn't understand what you'd like to order. Could you please specify the pizza name and size?",
                "suggestion": "Try saying something like 'I want a large BBQ Chicken pizza'"
            }
        
        # Validate using menu functions
        item_name = extracted_info.get("name", "")
        item_size = extracted_info.get("size", "")
        
        found_item = find_menu_item_in_mcp(item_name, item_size)
        if found_item:
            # Store pending confirmation instead of immediately confirming
            user_id = context.get("user_id", "default") if context else "default"
            user_email = context.get("user_email") if context else None
            user_name = context.get("user_name") if context else None
            
            print(f"📝 Storing pending order for user: {user_id} (email: {user_email})")
            
            # Store the pending order for confirmation with user context
            PENDING_CONFIRMATIONS[user_id] = {
                "items": [found_item],
                "address": "123 Main Street",  # Default for demo
                "phone": "555-0123",  # Default for demo
                "user_id": user_id,
                "email": user_email,  # Include email in pending order
                "name": user_name     # Include name in pending order
            }
            
            # Generate dynamic confirmation request using Gemini
            confirmation_prompt = f"""
            User wants to order: {found_item['name']} ({found_item['size']}) for ${found_item['price']}
            
            Generate an engaging confirmation message that:
            1. Confirms you found their requested item
            2. Shows the item details (name, size, price)
            3. Asks them to confirm the order
            4. Mentions they can say "yes" or "confirm" to proceed
            5. Uses appropriate food emojis
            
            Be enthusiastic and clear about the confirmation process.
            """
            
            try:
                response = FLASH_MODEL.generate_content(confirmation_prompt)
                dynamic_message = response.text.strip()
            except:
                dynamic_message = f"🍕 Great choice! I found {found_item['name']} ({found_item['size']}) for ${found_item['price']}.\n\nWould you like me to place this order? Just say 'yes' or 'confirm' to proceed! 🎯"
            
            return {
                "status": "pending_confirmation",
                "message": dynamic_message,
                "item": found_item,
                "action": "await_confirmation",
                "pending_order": PENDING_CONFIRMATIONS[user_id]
            }
        else:
            suggestions = suggest_similar_items_via_mcp(item_name, item_size)
            if suggestions:
                return {
                    "status": "suggestion",
                    "message": f"I couldn't find '{item_size} {item_name}' exactly. Here are similar items:",
                    "suggestions": suggestions[:3]
                }
            else:
                return {
                    "status": "not_found",
                    "message": f"Sorry, '{item_size} {item_name}' isn't available. Let me show you our menu!",
                    "action": "show_menu"
                }
                
    except Exception as e:
        return {
            "status": "error",
            "message": "I'm having trouble processing your order right now. Please try again!",
            "error": str(e)
        }

def route_to_scheduler_agent(user_input: str, context: dict = None) -> dict:
    """Route tracking/scheduling requests to scheduler_agent.py through MCP"""
    try:
        agents_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'agents'))
        if agents_path not in sys.path:
            sys.path.insert(0, agents_path)
        from scheduler_agent import schedule_delivery, get_eta
        
        user_email = context.get("user_email") if context else None
        user_name = context.get("user_name", "") if context else ""
        
        # Extract order ID if present (more flexible patterns)
        import re
        order_id_patterns = [
            r'(MCP-ORD-[\w\d]+)',  # Standard format
            r'order\s+(\w+)',      # "track order 123"
            r'#(\w+)',             # "track #123"
            r'\b(\d{3,8})\b'       # Any 3-8 digit number
        ]
        
        order_id = None
        for pattern in order_id_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                extracted_id = match.group(1)
                # If it's just a number, format it as MCP order
                if extracted_id.isdigit():
                    order_id = f"MCP-ORD-{extracted_id}"
                else:
                    order_id = extracted_id if extracted_id.startswith('MCP-ORD-') else f"MCP-ORD-{extracted_id}"
                break
        
        # If no specific order ID and user has email, find their most recent order
        if not order_id and user_email:
            user_orders = []
            for order_id_key, order in ORDERS.items():
                if order.get("email", "") and order.get("email", "").lower() == user_email.lower():
                    user_orders.append((order_id_key, order))
            
            if user_orders:
                # Sort by timestamp and get most recent
                user_orders.sort(key=lambda x: x[1].get("timestamp", ""), reverse=True)
                order_id, order_data = user_orders[0]
                print(f"🔍 Found most recent order for {user_email}: {order_id}")
            else:
                print(f"❌ No orders found for user email: {user_email}")
                # Generate personalized "no orders" message
                user_check = check_user_email(user_email)
                user_name = user_check.get("name") if user_check.get("exists") else None
                
                no_orders_prompt = f"""
                User with email {user_email} and name "{user_name}" wants to track an order but has no orders yet. Generate a friendly response that:
                1. Greets them by name if available
                2. Explains they haven't placed any orders yet
                3. Uses a welcoming, encouraging tone
                4. Suggests they browse the menu or place an order
                5. Makes them feel welcome
                
                Be warm and helpful, encouraging them to try our delicious pizzas.
                """
                
                try:
                    response = FLASH_MODEL.generate_content(no_orders_prompt)
                    dynamic_message = response.text.strip()
                except:
                    if user_name:
                        dynamic_message = f"Hi {user_name}! 👋 Looks like you haven't placed any orders yet. Hungry? Let's fix that! 🍕 Check out our delicious menu and place your first order!"
                    else:
                        dynamic_message = "Looks like you haven't placed any orders yet. Hungry? Let's fix that! 🍕 Check out our delicious menu and place your first order!"
                
                return {
                    "status": "no_orders_for_user",
                    "message": dynamic_message,
                    "action": "show_menu",
                    "user_name": user_name
                }
        
        if order_id:
            # Check if order exists (try both formatted and original)
            order_data = None
            for check_id in [order_id, order_id.replace('MCP-ORD-', ''), f"MCP-ORD-{order_id}"]:
                if check_id in ORDERS:
                    order_data = ORDERS[check_id]
                    order_id = check_id
                    break
            
            if order_data:
                # Get ETA information from scheduler agent
                try:
                    eta_info = get_eta(order_data)
                    schedule_result = schedule_delivery(order_data)
                    
                    eta_minutes = eta_info.get("eta_minutes", 25)
                    eta_text = eta_info.get("eta_text", "25 minutes")
                    current_status = eta_info.get("current_status", order_data.get("status", "placed"))
                    
                    print(f"📊 Order {order_id} - Status: {current_status}, ETA: {eta_text}")
                    
                except Exception as e:
                    print(f"⚠️ Error getting ETA: {e}")
                    eta_minutes = 25
                    eta_text = "25 minutes"
                    current_status = order_data.get("status", "placed")
                    eta_info = {"eta_minutes": eta_minutes, "eta_text": eta_text, "current_status": current_status}
                    schedule_result = {"message": f"Estimated delivery in {eta_text}"}
                
                # Generate dynamic tracking response using Gemini with ETA
                items_list = ", ".join([f"{item['name']} ({item['size']})" for item in order_data.get("items", [])])
                greeting = f"Hi {user_name}, " if user_name else ""
                
                tracking_prompt = f"""
                {greeting}User is tracking order {order_id}. Generate a helpful response that:
                1. Greets them by name if available
                2. Confirms the order is found
                3. Lists the items they ordered: {items_list}
                4. Provides current status: {current_status}
                5. Gives precise ETA: {eta_text}
                6. Is encouraging and informative
                7. Uses appropriate emojis
                
                Order details: {order_data}
                Current status: {current_status}
                ETA: {eta_text}
                
                Be specific and helpful about their order status and delivery time.
                """
                
                try:
                    response = FLASH_MODEL.generate_content(tracking_prompt)
                    dynamic_message = response.text.strip()
                except:
                    status_emoji = {"placed": "📋", "preparing": "👨‍🍳", "cooking": "🔥", "ready": "✅", "delivered": "🚚"}.get(current_status, "📦")
                    dynamic_message = f"{greeting}You have one ongoing order for {items_list}. {status_emoji} Status: {current_status.title()}. ETA: {eta_text}."
                
                return {
                    "status": "success",
                    "message": dynamic_message,
                    "order_data": order_data,
                    "schedule_info": schedule_result,
                    "eta_info": eta_info,
                    "order_id": order_id
                }
            else:
                # Generate dynamic "not found" response using Gemini
                not_found_prompt = f"""
                User tried to track order "{order_id}" but it wasn't found. Generate a helpful response that:
                1. Politely explains the order wasn't found
                2. Suggests they double-check the order number
                3. Offers to help them place a new order
                4. Is understanding and supportive
                
                Be helpful and guide them to next steps.
                """
                
                try:
                    response = FLASH_MODEL.generate_content(not_found_prompt)
                    dynamic_message = response.text.strip()
                except:
                    dynamic_message = f"I couldn't find order {order_id}. Please double-check your order number, or I can help you place a new order!"
                
                return {
                    "status": "not_found",
                    "message": dynamic_message,
                    "suggested_order_id": order_id
                }
        else:
            # No order ID provided and no email - check if there are recent orders
            if ORDERS:
                # Get the most recent order
                recent_orders = sorted(ORDERS.items(), key=lambda x: x[1].get("timestamp", ""), reverse=True)
                most_recent_id, most_recent_order = recent_orders[0]
                
                # Get ETA for the most recent order
                try:
                    eta_info = get_eta(most_recent_order)
                    eta_text = eta_info.get("eta_text", "25 minutes")
                except:
                    eta_text = "25 minutes"
                
                # Generate response about recent order using Gemini
                recent_order_prompt = f"""
                User asked: "{user_input}"
                
                They want to track an order but didn't specify which one. We have a recent order {most_recent_id}. Generate a helpful response that:
                1. Mentions we found their recent order
                2. Provides the current status
                3. Gives the ETA: {eta_text}
                4. Asks if this is the order they want to track
                5. Offers to help with a different order if needed
                
                Recent order details: {most_recent_order}
                ETA: {eta_text}
                
                Be helpful and proactive.
                """
                
                try:
                    response = FLASH_MODEL.generate_content(recent_order_prompt)
                    dynamic_message = response.text.strip()
                    
                    return {
                        "status": "success",
                        "message": dynamic_message,
                        "order_data": most_recent_order,
                        "order_id": most_recent_id,
                        "eta_info": eta_info,
                        "schedule_info": schedule_delivery(most_recent_order)
                    }
                except:
                    return {
                        "status": "success",
                        "message": f"I found your recent order {most_recent_id}. Status: {most_recent_order.get('status', 'Processing')}. ETA: {eta_text}. Is this the order you'd like to track?",
                        "order_data": most_recent_order,
                        "order_id": most_recent_id
                    }
            else:
                # No orders found at all
                no_orders_prompt = f"""
                User said: "{user_input}"
                
                They want to track an order but there are no orders in the system. Generate a helpful response that:
                1. Explains there are no current orders
                2. Offers to help them place a new order
                3. Suggests they check if they have the right order number
                
                Be understanding and helpful.
                """
                
                try:
                    response = FLASH_MODEL.generate_content(no_orders_prompt)
                    dynamic_message = response.text.strip()
                except:
                    dynamic_message = "I don't see any orders in the system right now. Would you like to place a new order, or do you have an order number I can look up?"
                
                return {
                    "status": "no_orders",
                    "message": dynamic_message
                }
            
    except Exception as e:
        error_prompt = f"""
        There was a technical issue tracking the order. Generate a helpful response that:
        1. Apologizes for the technical difficulty
        2. Asks them to try again
        3. Offers alternative help
        
        Be understanding and helpful.
        """
        
        try:
            response = FLASH_MODEL.generate_content(error_prompt)
            dynamic_message = response.text.strip()
        except:
            dynamic_message = "I'm having trouble accessing order information right now. Please try again in a moment, or I can help you with something else!"
        
        return {
            "status": "error",
            "message": dynamic_message,
            "error": str(e)
        }

def handle_health_queries(user_input: str, context: dict = None) -> dict:
    """Handle health-related queries and suggest appropriate menu items"""
    # Get vegetarian items as they're typically healthier
    healthy_options = get_menu_by_category("veg")
    
    # Add specific health-focused response using Gemini
    health_prompt = f"""
User asked: "{user_input}"

They're interested in healthy options. Based on our vegetarian menu items, provide a helpful response that:
1. Acknowledges their health consciousness
2. Recommends 2-3 specific vegetarian pizzas as healthier options
3. Mentions why they're healthier (fresh vegetables, less processed meat, etc.)
4. Offers to show the full menu or answer questions about ingredients

Available vegetarian options:
{[f"{item['name']} ({item['size']}) - {item['description']}" for item in healthy_options]}

Be encouraging and informative about healthy eating while staying pizza-focused.
"""
    
    try:
        response = FLASH_MODEL.generate_content(health_prompt)
        dynamic_response = response.text.strip()
        
        return {
            "status": "success",
            "message": dynamic_response,
            "suggested_items": healthy_options[:3],
            "action": "show_healthy_options"
        }
    except:
        # Only use fallback if Gemini completely fails
        veggie_names = [item['name'] for item in healthy_options[:2]]
        return {
            "status": "success", 
            "message": f"Great choice focusing on healthy options! Our vegetarian pizzas like {' and '.join(veggie_names)} are packed with fresh vegetables and are healthier choices. They're made with fresh ingredients and no processed meats!",
            "suggested_items": healthy_options[:3],
            "action": "show_healthy_options"
        }

def handle_casual_conversation(user_input: str, context: dict = None) -> dict:
    """Handle casual conversation and general queries using Gemini"""
    casual_prompt = f"""
User said: "{user_input}"

You are a friendly pizza restaurant AI assistant. This seems like casual conversation or a general question. Respond naturally and conversationally while:

1. Being warm and engaging
2. Staying on-brand for a pizza restaurant
3. Gently steering toward pizza-related topics when appropriate
4. Being helpful and informative
5. Matching the user's tone (casual, formal, etc.)

If they ask about the restaurant, mention we serve delicious pizzas, drinks, and sides.
If they make jokes, be playful but professional.
If they ask general questions, answer helpfully while being a pizza-focused assistant.
If they express hunger or food cravings, suggest looking at our menu.

Keep responses concise but friendly. Never use generic phrases like "I'm here to help with anything pizza-related" - be specific and conversational.
"""
    
    try:
        response = FLASH_MODEL.generate_content(casual_prompt)
        dynamic_response = response.text.strip()
        
        return {
            "status": "success",
            "message": dynamic_response,
            "action": "continue_chat"
        }
    except:
        # Only use fallback if Gemini completely fails - make it contextual
        user_lower = user_input.lower()
        if any(word in user_lower for word in ['hungry', 'food', 'eat']):
            return {
                "status": "success",
                "message": "Sounds like you're ready for some delicious pizza! Want to see what we've got cooking?",
                "action": "continue_chat"
            }
        elif any(word in user_lower for word in ['hello', 'hi', 'hey']):
            return {
                "status": "success", 
                "message": "Hey there! Welcome to our pizza place. What's got your taste buds excited today?",
                "action": "continue_chat"
            }
        else:
            return {
                "status": "success",
                "message": "That's interesting! Speaking of which, have you checked out our latest pizza creations?",
                "action": "continue_chat"
            }

def handle_order_confirmation(user_input: str, user_id: str = "default", context: dict = None) -> dict:
    """Handle order confirmation through MCP"""
    try:
        print(f"🔍 Confirming order for user: {user_id}")
        
        # Check if there's a pending confirmation for this user
        if user_id in PENDING_CONFIRMATIONS:
            print(f"✅ Found pending order, processing...")
            pending_order = PENDING_CONFIRMATIONS[user_id]
            
            # Generate order ID and process the order
            order_id = f"MCP-ORD-{str(uuid.uuid4())[:8]}"
            
            # Create the order through MCP
            validated_items = []
            total_price = 0
            
            for item in pending_order.get("items", []):
                found_item = find_menu_item_in_mcp(item.get("name", ""), item.get("size", ""))
                if found_item:
                    validated_items.append(found_item)
                    total_price += found_item["price"]
            
            if validated_items:
                # Store order through MCP
                ORDERS[order_id] = {
                    "id": order_id,
                    "items": validated_items,
                    "address": pending_order.get("address", "123 Main Street"),
                    "phone": pending_order.get("phone", "555-0123"),
                    "user_id": user_id,
                    "email": pending_order.get("email"),  # Include email from pending order
                    "name": pending_order.get("name"),    # Include name from pending order
                    "status": "placed",
                    "total_price": total_price,
                    "progress": 25,
                    "mcp_processed": True,
                    "timestamp": str(uuid.uuid4())  # Simple timestamp
                }
                
                # Get ETA from scheduler agent
                try:
                    agents_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'agents'))
                    if agents_path not in sys.path:
                        sys.path.insert(0, agents_path)
                    from scheduler_agent import get_eta, schedule_delivery
                    
                    # Get initial ETA for the placed order
                    eta_info = get_eta(ORDERS[order_id])
                    eta_minutes = eta_info.get("eta_minutes", 25)
                    eta_text = eta_info.get("eta_text", "25 minutes")
                    
                    # Schedule delivery
                    schedule_info = schedule_delivery(ORDERS[order_id])
                    
                    print(f"🎉 Order {order_id} placed successfully! ETA: {eta_text}")
                    
                except Exception as e:
                    print(f"⚠️ Could not get ETA from scheduler: {e}")
                    eta_minutes = 25
                    eta_text = "25 minutes"
                    eta_info = {"eta_minutes": eta_minutes, "eta_text": eta_text}
                    schedule_info = {"message": f"Estimated delivery in {eta_text}"}
                
                # Clear pending confirmation
                del PENDING_CONFIRMATIONS[user_id]
                
                # Generate dynamic thank you response using Gemini with ETA
                user_name = pending_order.get("name", "")
                name_greeting = f", {user_name}" if user_name else ""
                
                thank_you_prompt = f"""
                User just confirmed their order and it was successfully placed. Generate a warm, exciting thank you response that:
                1. Thanks the user by name if available: "{user_name if user_name else 'valued customer'}"
                2. Confirms the order was placed successfully
                3. Mentions the specific items they ordered: {[item['name'] + ' (' + item['size'] + ')' for item in validated_items]}
                4. Provides the order ID: {order_id}
                5. Gives the estimated delivery time: {eta_text}
                6. Uses pizza and food emojis appropriately
                7. Mentions they can track the order by saying "track my order"
                
                Order details: {ORDERS[order_id]}
                ETA: {eta_text}
                User name: {user_name}
                
                Be enthusiastic and helpful! Include the delivery time prominently and use their name naturally.
                """
                
                try:
                    response = FLASH_MODEL.generate_content(thank_you_prompt)
                    dynamic_message = response.text.strip()
                except:
                    item_names = [f"{item['name']} ({item['size']})" for item in validated_items]
                    if user_name:
                        dynamic_message = f"🎉 Thanks for ordering, {user_name}! Your order has been placed successfully!\n\n📋 Order ID: {order_id}\n🍕 Items: {', '.join(item_names)}\n💰 Total: ${total_price:.2f}\n⏰ Your pizza will be delivered in {eta_text}!\n\nSay 'track my order' anytime to check status! 🚀"
                    else:
                        dynamic_message = f"🎉 Thanks for ordering! Your order has been placed successfully!\n\n📋 Order ID: {order_id}\n🍕 Items: {', '.join(item_names)}\n💰 Total: ${total_price:.2f}\n⏰ Your pizza will be delivered in {eta_text}!\n\nSay 'track my order' anytime to check status! 🚀"
                
                return {
                    "status": "success",
                    "message": dynamic_message,
                    "order_id": order_id,
                    "order_data": ORDERS[order_id],
                    "eta_info": eta_info,
                    "schedule_info": schedule_info,
                    "action": "order_placed"
                }
            else:
                print(f"❌ No validated items found")
                return {
                    "status": "error",
                    "message": "Sorry, there was an issue with your order items. Please try ordering again.",
                    "action": "retry_order"
                }
        else:
            print(f"❌ No pending order found for user: {user_id}")
            # No pending order to confirm
            no_pending_prompt = f"""
            User said: "{user_input}"
            
            They're trying to confirm an order but there's no pending order. Generate a helpful response that:
            1. Explains there's no pending order to confirm
            2. Offers to help them place a new order
            3. Suggests they tell you what they'd like to order
            
            Be helpful and guide them to place an order.
            """
            
            try:
                response = FLASH_MODEL.generate_content(no_pending_prompt)
                dynamic_message = response.text.strip()
            except:
                dynamic_message = "I don't see any pending order to confirm. Would you like to place a new order? Just tell me what you'd like!"
            
            return {
                "status": "no_pending",
                "message": dynamic_message,
                "action": "suggest_order"
            }
            
    except Exception as e:
        print(f"❌ Error in confirmation: {e}")
        return {
            "status": "error",
            "message": "I'm having trouble processing your confirmation. Please try again!",
            "error": str(e),
            "action": "retry"
        }

def find_menu_item_in_mcp(name: str, size: str = None) -> Optional[dict]:
    """Find a menu item by name and optionally size through MCP"""
    return find_menu_item(name, size)

def suggest_similar_items_via_mcp(name: str, size: str = None) -> List[dict]:
    """Suggest similar items when exact match not found through MCP"""
    return suggest_similar_items(name, size)

# User Management Functions for MCP
def check_user_email(email: str) -> dict:
    """Check if email exists in user database"""
    email_lower = email.lower().strip()
    
    if email_lower in USERS:
        user_data = USERS[email_lower]
        # Count orders for this user
        user_orders = [order for order in ORDERS.values() if order.get("email", "").lower() == email_lower]
        
        return {
            "exists": True,
            "email": email_lower,
            "name": user_data.get("name"),
            "orders_count": len(user_orders),
            "last_order_date": max([order.get("timestamp", "") for order in user_orders], default=None) if user_orders else None,
            "orders": user_orders
        }
    else:
        return {
            "exists": False,
            "email": email_lower,
            "name": None,
            "orders_count": 0,
            "last_order_date": None,
            "orders": []
        }

def save_user_data(email: str, name: str = None) -> dict:
    """Save user data to the database"""
    email_lower = email.lower().strip()
    
    if email_lower in USERS:
        # Update existing user
        if name:
            USERS[email_lower]["name"] = name
        return {
            "success": True,
            "message": "User data updated successfully",
            "user": USERS[email_lower]
        }
    else:
        # Create new user
        USERS[email_lower] = {
            "email": email_lower,
            "name": name,
            "created_at": str(uuid.uuid4()),  # Simple timestamp
            "mcp_processed": True
        }
        return {
            "success": True,
            "message": "New user created successfully",
            "user": USERS[email_lower]
        }

def get_user_order_history(email: str) -> dict:
    """Get complete order history for a user"""
    email_lower = email.lower().strip()
    user_orders = []
    
    for order_id, order in ORDERS.items():
        if order.get("email", "") and order.get("email", "").lower() == email_lower:
            user_orders.append({
                "order_id": order_id,
                "items": order.get("items", []),
                "status": order.get("status", "unknown"),
                "total_price": order.get("total_price", 0),
                "timestamp": order.get("timestamp", ""),
                "progress": order.get("progress", 0)
            })
    
    # Sort by timestamp (most recent first)
    user_orders.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Categorize orders
    current_orders = [order for order in user_orders if order["status"] in ["placed", "preparing", "cooking", "ready"]]
    completed_orders = [order for order in user_orders if order["status"] in ["delivered", "completed"]]
    
    return {
        "email": email_lower,
        "total_orders": len(user_orders),
        "current_orders": current_orders,
        "completed_orders": completed_orders,
        "all_orders": user_orders
    }

def generate_personalized_greeting(email: str, context: str = "general") -> str:
    """Generate personalized greeting based on user data"""
    user_check = check_user_email(email)
    
    if user_check["exists"] and user_check["name"]:
        name = user_check["name"]
        orders_count = user_check["orders_count"]
        
        if context == "returning":
            if orders_count > 0:
                return f"Welcome back, {name}! Ready for another delicious pizza? 🍕"
            else:
                return f"Hi {name}! Thanks for returning. What sounds good today? 😊"
        elif context == "ordering":
            if orders_count > 0:
                return f"Hi {name}! Would you like to repeat your last order or try something new today? 🤔"
            else:
                return f"Hi {name}! What delicious pizza can I get started for you? 🍕"
        elif context == "general":
            if orders_count > 0:
                return f"Hello {name}! How can I help you today? Need to track an order or ready for more pizza? 😄"
            else:
                return f"Hello {name}! How can I help you today? Ready to try our delicious pizzas? 🍕"
        else:
            return f"Hello {name}! How can I help you today?"
    elif user_check["exists"]:
        # User exists but no name saved
        if context == "returning":
            return "Welcome back! What can I get for you today? 😊"
        else:
            return "Hello! How can I help you today?"
    else:
        # New user
        return "Hello! Welcome to our pizza place. How can I help you today?"

# MCP API Routes
@app.get("/api/menu")
async def get_menu_via_mcp():
    """Get the complete menu through MCP"""
    return {"pizzas": MENU, "protocol": "MCP", "server": "Pizza AI MCP Server"}

# User Management Endpoints
@app.post("/api/user/check", response_model=MCPUserResponse)
async def check_user_email_endpoint(user_request: MCPUserRequest):
    """Check if user email exists in the system"""
    result = check_user_email(user_request.email)
    
    return MCPUserResponse(
        email=result["email"],
        name=result["name"],
        exists=result["exists"],
        orders_count=result["orders_count"],
        last_order_date=result["last_order_date"]
    )

@app.post("/api/user/save")
async def save_user_endpoint(user_request: MCPUserRequest):
    """Save or update user data"""
    result = save_user_data(user_request.email, user_request.name)
    
    return {
        "success": result["success"],
        "message": result["message"],
        "user": result["user"],
        "mcp_processed": True
    }

@app.get("/api/user/{email}/orders")
async def get_user_orders_endpoint(email: str):
    """Get order history for a specific user email"""
    result = get_user_order_history(email)
    
    return {
        "email": result["email"],
        "total_orders": result["total_orders"],
        "current_orders": result["current_orders"],
        "completed_orders": result["completed_orders"],
        "all_orders": result["all_orders"],
        "mcp_processed": True
    }

@app.get("/api/user/{email}/greeting")
async def get_personalized_greeting_endpoint(email: str, context: str = "general"):
    """Get personalized greeting for user"""
    greeting = generate_personalized_greeting(email, context)
    user_check = check_user_email(email)
    
    return {
        "greeting": greeting,
        "user_exists": user_check["exists"],
        "user_name": user_check["name"],
        "orders_count": user_check["orders_count"],
        "mcp_processed": True
    }

@app.post("/api/chat", response_model=MCPChatResponse)
async def chat_via_mcp(chat_request: MCPChatRequest):
    """Enhanced MCP chat handler with dynamic Gemini integration and agent routing"""
    message = chat_request.message.strip()
    user_email = chat_request.context.get("email") if chat_request.context else None
    
    # Get actual user name from saved data, not just email prefix
    user_name = None
    if user_email:
        user_check = check_user_email(user_email)
        if user_check["exists"]:
            user_name = user_check["name"]
    
    # Use enhanced Gemini to analyze intent and determine routing
    intent_analysis = interpret_intent_via_gemini(message)
    
    intent = intent_analysis.get("intent", "casual")
    confidence = intent_analysis.get("confidence", 0.5)
    agent_route = intent_analysis.get("agent_route", "gemini_chat")
    specific_item = intent_analysis.get("specific_item")
    category = intent_analysis.get("category", "none")
    context = intent_analysis.get("context", {})
    
    # Add user email to context for personalization
    if user_email:
        context["user_email"] = user_email
        context["personalized"] = True
    
    # Initialize enhanced_context for all agent routing
    enhanced_context = context.copy() if context else {}
    enhanced_context["user_email"] = user_email
    enhanced_context["user_name"] = user_name  # Use actual saved name
    
    print(f"🔍 MCP Intent Analysis: {intent} (confidence: {confidence}) -> Route: {agent_route}")
    print(f"📝 Message: '{message}' | User: {user_name or user_email or 'anonymous'} | Context: {context}")
    
    # PRIORITY ROUTING: Track intent takes precedence over order intent
    if intent == "track" or agent_route == "scheduler_agent":
        # Route to scheduler agent for tracking/scheduling        
        tracking_result = route_to_scheduler_agent(message, enhanced_context)
        
        if tracking_result["status"] == "success":
            return MCPChatResponse(
                response=tracking_result["message"],
                intent=intent,
                action="show_tracking",
                context={
                    "mcp_processed": True, 
                    "agent_used": "scheduler_agent",
                    "order_data": tracking_result.get("order_data"),
                    "schedule_info": tracking_result.get("schedule_info"),
                    "eta_info": tracking_result.get("eta_info"),
                    "order_id": tracking_result.get("order_id")
                }
            )
        elif tracking_result["status"] == "no_orders_for_user":
            return MCPChatResponse(
                response=tracking_result["message"],
                intent=intent,
                action="show_menu",
                context={"mcp_processed": True, "agent_used": "scheduler_agent", "user_name": tracking_result.get("user_name")}
            )
        else:
            return MCPChatResponse(
                response=tracking_result["message"],
                intent=intent,
                action="show_tracking" if tracking_result["status"] == "need_order_id" else "none",
                context={"mcp_processed": True, "agent_used": "scheduler_agent"}
            )
    
    elif intent == "order" or agent_route == "ordering_agent":
        # Route to ordering agent for order processing
        # Ensure user_id is included in context
        enhanced_context["user_id"] = chat_request.user_id
        
        order_result = route_to_ordering_agent(message, enhanced_context)
        
        if order_result["status"] == "success":
            return MCPChatResponse(
                response=order_result["message"],
                intent=intent,
                action="confirm_order",
                suggested_items=[order_result["item"]] if "item" in order_result else None,
                context={"mcp_processed": True, "agent_used": "ordering_agent", "order_ready": True}
            )
        elif order_result["status"] == "pending_confirmation":
            return MCPChatResponse(
                response=order_result["message"],
                intent=intent,
                action="await_confirmation",
                pending_order=order_result["pending_order"],
                context={"mcp_processed": True, "agent_used": "ordering_agent", "order_ready": True, "user_id": chat_request.user_id}
            )
        elif order_result["status"] == "suggestion":
            return MCPChatResponse(
                response=order_result["message"],
                intent=intent,
                action="show_menu",
                suggested_items=order_result.get("suggestions", []),
                context={"mcp_processed": True, "agent_used": "ordering_agent", "suggestions_provided": True}
            )
        else:
            return MCPChatResponse(
                response=order_result["message"],
                intent=intent,
                action="show_menu" if order_result.get("action") == "show_menu" else "none",
                context={"mcp_processed": True, "agent_used": "ordering_agent", "error": True}
            )
    
    elif intent == "health":
        # Handle health-related queries
        health_result = handle_health_queries(message, context)
        return MCPChatResponse(
            response=health_result["message"],
            intent=intent,
            action="show_menu",
            suggested_items=health_result.get("suggested_items", []),
            context={"mcp_processed": True, "health_focused": True}
        )
    
    elif agent_route == "menu_handler" or intent == "menu":
        # Handle menu requests using enhanced menu functions
        if category in ["veg", "non-veg"]:
            category_items = get_menu_by_category(category)
            category_names = {"veg": "vegetarian", "non-veg": "non-vegetarian"}
            category_name = category_names.get(category, category)
            
            response_text = f"Here are our {len(category_items)} delicious {category_name} options:\n"
            for item in category_items:
                response_text += f"• {item['name']} ({item['size']}) - ${item['price']} - {item['description']}\n"
            
            return MCPChatResponse(
                response=response_text.strip(),
                intent=intent,
                action="show_menu",
                suggested_items=category_items,
                context={"mcp_processed": True, "category": category, "agent_used": "menu_handler"}
            )
        else:
            # Show complete menu using Gemini for personalized response
            menu_prompt = f"""
            User asked: "{message}"
            
            They want to see our pizza menu. Create a welcoming response that:
            1. Acknowledges their request
            2. Briefly introduces our pizza categories
            3. Mentions we have delicious vegetarian and non-vegetarian pizzas
            4. Invites them to ask about specific categories or items
            
            Be friendly and helpful, encouraging them to explore our pizza selection.
            """
            
            try:
                response = FLASH_MODEL.generate_content(menu_prompt)
                dynamic_response = response.text.strip()
            except:
                dynamic_response = "Here's our delicious pizza menu! We have amazing vegetarian and non-vegetarian pizzas. What sounds good to you today?"
            
            return MCPChatResponse(
                response=dynamic_response,
                intent=intent,
                action="show_menu",
                suggested_items=MENU,
                context={"mcp_processed": True, "category": "all", "agent_used": "menu_handler"}
            )
    
    elif intent == "greeting":
        # Generate dynamic greeting using Gemini or personalized greeting
        if user_email:
            # Use personalized greeting
            personalized_greeting = generate_personalized_greeting(user_email, "general")
            return MCPChatResponse(
                response=personalized_greeting,
                intent=intent,
                action="none",
                context={"mcp_processed": True, "conversation_started": True, "agent_used": "gemini_chat", "personalized": True}
            )
        else:
            # Generate dynamic greeting using Gemini
            greeting_prompt = f"""
            User said: "{message}"
            
            Generate a warm, personalized greeting that:
            1. Responds naturally to their specific greeting
            2. Introduces yourself as the Pizza AI assistant
            3. Offers to help with orders, menu, or questions
            4. Matches their tone and energy
            
            Be welcoming and set a positive tone for the conversation.
            """
            
            try:
                response = FLASH_MODEL.generate_content(greeting_prompt)
                dynamic_response = response.text.strip()
            except:
                dynamic_response = "Hello! I'm your Pizza AI assistant. I'm here to help you order delicious pizzas, explore our menu, track orders, or answer any questions. What can I do for you today?"
            
            return MCPChatResponse(
                response=dynamic_response,
                intent=intent,
                action="none",
                context={"mcp_processed": True, "conversation_started": True, "agent_used": "gemini_chat"}
            )
    
    elif intent == "confirm" or agent_route == "order_confirmation":
        # Handle order confirmation
        confirmation_result = handle_order_confirmation(message, chat_request.user_id, context)
        
        if confirmation_result["status"] == "success":
            return MCPChatResponse(
                response=confirmation_result["message"],
                intent=intent,
                action="order_placed",
                context={
                    "mcp_processed": True,
                    "agent_used": "order_confirmation",
                    "order_placed": True,
                    "order_id": confirmation_result["order_id"],
                    "order_data": confirmation_result["order_data"],
                    "eta_info": confirmation_result.get("eta_info"),
                    "schedule_info": confirmation_result.get("schedule_info")
                }
            )
        elif confirmation_result["status"] == "no_pending":
            return MCPChatResponse(
                response=confirmation_result["message"],
                intent="casual",
                action="suggest_order",
                context={"mcp_processed": True, "agent_used": "order_confirmation"}
            )
        else:
            return MCPChatResponse(
                response=confirmation_result["message"],
                intent=intent,
                action="retry",
                context={"mcp_processed": True, "agent_used": "order_confirmation", "error": True}
            )
    
    else:
        # Handle casual conversation and general queries with Gemini
        casual_result = handle_casual_conversation(message, context)
        return MCPChatResponse(
            response=casual_result["message"],
            intent=intent,
            action="continue_chat",
            context={"mcp_processed": True, "agent_used": "gemini_chat", "casual_chat": True}
        )

@app.post("/api/order", response_model=MCPOrderResponse)
async def place_order_via_mcp(order_request: MCPOrderRequest):
    """Place a new pizza order with item validation through MCP"""
    order_id = f"MCP-ORD-{str(uuid.uuid4())[:8]}"
    
    # Validate each item in the order through MCP
    validated_items = []
    total_price = 0
    
    for item_name in order_request.items:
        # Try to extract item info using Gemini through MCP
        item_info = extract_item_info_via_gemini(item_name)
        
        if "error" in item_info:
            # If Gemini fails, try simple matching through MCP
            found_item = find_menu_item_in_mcp(item_name)
        else:
            found_item = find_menu_item_in_mcp(item_info.get("name", ""), item_info.get("size", ""))
        
        if found_item:
            validated_items.append(found_item)
            total_price += found_item["price"]
        else:
            # Item not found, suggest alternatives through MCP
            suggestions = suggest_similar_items_via_mcp(item_name)
            error_msg = f"Sorry, '{item_name}' is not available."
            if suggestions:
                error_msg += f" Did you mean: {', '.join([f'{s['name']} ({s['size']})' for s in suggestions[:2]])}?"
            
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": error_msg,
                    "suggestions": suggestions,
                    "mcp_processed": True
                }
            )
    
    # Store order through MCP with email association
    ORDERS[order_id] = {
        "id": order_id,
        "items": validated_items,
        "address": order_request.address,
        "phone": order_request.phone,
        "user_id": order_request.user_id,
        "email": order_request.email,  # Associate order with email
        "status": "placed",
        "total_price": total_price,
        "progress": 25,
        "mcp_processed": True,
        "timestamp": str(uuid.uuid4())  # Simple timestamp
    }
    
    # If email is provided, ensure user exists in system
    if order_request.email:
        user_check = check_user_email(order_request.email)
        if not user_check["exists"]:
            # Create user record for email
            save_user_data(order_request.email)
    
    return MCPOrderResponse(
        order_id=order_id,
        estimated_time="20-30 minutes",
        total_price=total_price,
        status="placed"
    )

@app.get("/api/order/{order_id}")
async def get_order_status_via_mcp(order_id: str):
    """Get order status with progress information through MCP"""
    if order_id not in ORDERS:
        raise HTTPException(status_code=404, detail={"error": "Order not found", "mcp_processed": True})
    
    order = ORDERS[order_id]
    
    # Simulate progress updates through MCP
    import random
    progress_options = [25, 50, 75, 100]
    progress = random.choice(progress_options)
    
    status_map = {
        25: "Order Placed",
        50: "Preparing",
        75: "Cooking",
        100: "Ready for Delivery"
    }
    
    order["progress"] = progress
    order["status"] = status_map[progress]
    order["mcp_processed"] = True
    
    return {
        "order": order,
        "progress": progress,
        "status": status_map[progress],
        "estimated_time": "20-30 minutes",
        "mcp_processed": True
    }

@app.get("/api/health")
async def health_check_mcp():
    """Health check endpoint for MCP"""
    return {
        "status": "healthy", 
        "message": "Pizza AI MCP Server is running",
        "protocol": "MCP",
        "gemini_integration": True
    }

# Legacy MCP endpoints for compatibility
@app.get("/menu")
def get_menu():
    """Legacy MCP endpoint"""
    return MENU

@app.post("/order")
async def place_order(request: Request):
    """Legacy MCP endpoint"""
    data = await request.json()
    order_id = f"MCP-{str(uuid.uuid4())[:8]}"
    data["order_id"] = order_id
    data["mcp_processed"] = True
    ORDERS[order_id] = data
    return {"order_id": order_id, "message": "Order placed successfully via MCP"}

@app.get("/order/{order_id}")
def get_order(order_id: str):
    """Legacy MCP endpoint"""
    if order_id not in ORDERS:
        return {"error": "Order not found", "mcp_processed": True}
    order = ORDERS[order_id]
    order["mcp_processed"] = True
    return order

# Load OpenAPI spec for MCP validation
def load_openapi_spec():
    path = os.path.join(os.path.dirname(__file__), "openapi.yaml")
    if os.path.exists(path):
        with open(path, "r") as f:
            spec = yaml.safe_load(f)
            print("✅ MCP OpenAPI spec loaded:", spec["info"]["title"])
    else:
        print("⚠️ OpenAPI spec not found, using dynamic MCP configuration")

if __name__ == "__main__":
    load_openapi_spec()
    print("🚀 Starting Pizza AI MCP Server...")
    print("🔗 Protocol: Model Context Protocol (MCP)")
    print("🤖 AI Integration: Gemini Flash")
    print("📡 Port: 8001 (avoiding permission conflicts)")
    uvicorn.run(app, host="0.0.0.0", port=8001)
