"""
Pizza AI MCP Server - Clean & Focused Implementation
Only essential Pizza ordering features: Menu, Order, Track, User Management
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import uuid

from utils.config import FLASH_MODEL
from utils.menu import MENU, find_menu_item, suggest_similar_items, get_menu_by_category
from utils.mcp_helpers import create_order_id, extract_order_id_from_message
from utils.gemini_integration import gemini_chat

# FastAPI setup
app = FastAPI(title="Pizza AI MCP Server", description="Clean MCP server for Pizza ordering")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

# Storage
ORDERS = {}
PENDING_CONFIRMATIONS = {}
USERS = {}

# Models
class ChatRequest(BaseModel):
    message: str
    user_id: str = "default"
    context: Optional[dict] = None

class ChatResponse(BaseModel):
    response: str
    intent: str
    action: Optional[str] = None
    suggested_items: Optional[List[dict]] = None
    context: Optional[dict] = None
    pending_order: Optional[dict] = None

class OrderRequest(BaseModel):
    items: List[str]
    address: str
    phone: str
    user_id: str = "default"
    email: Optional[str] = None

class OrderResponse(BaseModel):
    order_id: str
    estimated_time: str
    total_price: float
    status: str = "placed"

class UserRequest(BaseModel):
    email: str
    name: Optional[str] = None

class UserResponse(BaseModel):
    email: str
    name: Optional[str] = None
    exists: bool
    orders_count: int = 0

# Core Functions
def get_dynamic_eta(order_data: dict) -> str:
    """Get dynamic ETA from scheduler agent"""
    try:
        agents_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'agents'))
        if agents_path not in sys.path:
            sys.path.insert(0, agents_path)
        from scheduler_agent import get_eta
        
        eta_info = get_eta(order_data)
        return eta_info.get('eta_text', 'being calculated')
    except Exception as e:
        print(f"⚠️ ETA calculation failed: {e}")
        return "We're preparing your order. Details will be shared shortly."

def process_order(message: str, context: dict) -> dict:
    """Process pizza order"""
    try:
        # Import ordering agent
        agents_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'agents'))
        if agents_path not in sys.path:
            sys.path.insert(0, agents_path)
        from ordering_agent import extract_pizza_info
        
        order_info = extract_pizza_info(message)
        if "error" in order_info:
            return {
                "status": "error", 
                "message": "Could you specify the pizza name and size?",
                "action": "continue_chat"
            }
        
        found_item = find_menu_item(order_info.get("name", ""), order_info.get("size", ""))
        if found_item:
            user_id = context.get("user_id", "default")
            PENDING_CONFIRMATIONS[user_id] = {
                "items": [found_item],
                "address": "123 Main Street",
                "phone": "555-0123",
                "user_id": user_id,
                "email": context.get("user_email"),
                "name": context.get("user_name")
            }
            
            # Use Gemini for confirmation message
            confirmation_msg = gemini_chat.generate_contextual_response(
                "order confirmation request",
                {"user_name": context.get("user_name")},
                item=found_item
            )
            
            return {
                "status": "pending_confirmation",
                "message": confirmation_msg,
                "item": found_item,
                "action": "await_confirmation"
            }
        else:
            suggestions = suggest_similar_items(order_info.get("name", ""))
            
            # If no direct suggestions, provide category-based alternatives
            if not suggestions:
                user_message_lower = message.lower()
                if any(word in user_message_lower for word in ["chicken", "meat", "pepperoni", "bbq"]):
                    suggestions = get_menu_by_category("non-veg")[:3]
                    suggestion_msg = "I couldn't find that exact item. Here are our popular non-veg pizzas:"
                elif any(word in user_message_lower for word in ["veg", "vegetarian", "paneer"]):
                    suggestions = get_menu_by_category("veg")[:3]
                    suggestion_msg = "I couldn't find that exact item. Here are our popular veg pizzas:"
                else:
                    suggestions = MENU[:3]
                    suggestion_msg = "I couldn't find that exact item. Here are our popular pizzas:"
            else:
                suggestion_msg = f"I couldn't find that exact item. Here are similar options:"
            
            return {
                "status": "suggestion",
                "message": suggestion_msg,
                "suggestions": suggestions,
                "action": "show_menu"
            }
    except Exception as e:
        return {
            "status": "error", 
            "message": "I'm having trouble processing your order. Please try again!",
            "action": "continue_chat"
        }

def track_order(message: str, context: dict) -> dict:
    """Track pizza order - prioritize most recent order"""
    user_email = context.get("user_email")
    user_name = context.get("user_name", "")
    
    # Find user's most recent order or extract order ID
    order_id = extract_order_id_from_message(message)
    
    if not order_id and user_email:
        user_orders = [(oid, order) for oid, order in ORDERS.items() 
                      if order.get("email", "").lower() == user_email.lower()]
        
        if user_orders:
            user_orders.sort(key=lambda x: x[1].get("timestamp", ""), reverse=True)
            order_id, order_data = user_orders[0]
            
            # Generate response focusing on latest order
            latest_order_msg = gemini_chat.generate_contextual_response(
                "latest order status update",
                {"user_name": user_name},
                order_id=order_id,
                status=order_data.get('status', 'placed'),
                items=order_data.get('items', [])
            )
        else:
            no_orders_msg = gemini_chat.generate_contextual_response(
                "no orders found - suggest new order", 
                {"user_name": user_name}
            )
            return {
                "status": "no_orders",
                "message": no_orders_msg,
                "action": "show_menu"
            }
    
    if order_id and order_id in ORDERS:
        order_data = ORDERS[order_id]
        
        # Get updated ETA from scheduler
        eta_text = get_dynamic_eta(order_data)
        
        # Update order with latest ETA
        ORDERS[order_id]["eta"] = eta_text
        
        # Generate status progression data
        status_progression = get_order_status_progression(order_data.get('status', 'placed'))
        
        # Use Gemini for tracking response - emphasize latest order
        tracking_prompt = f"""
        Generate a tracking update message for Pizza Planet's LATEST ORDER.
        
        Order details:
        - Order ID: {order_id}
        - Status: {order_data.get('status', 'placed')}
        - Items: {', '.join([f"{item['name']} ({item['size']})" for item in order_data.get('items', [])])}
        - ETA: {eta_text}
        - User name: {user_name}
        
        Status progression: {status_progression}
        
        Create a response that:
        - Emphasizes this is their LATEST order
        - Updates on current status with excitement
        - Mentions ETA prominently
        - Uses user's name if provided
        - Includes appropriate emojis
        - Keeps focus on this ONE order (not historical orders)
        
        Example: "Here's your latest order update! Order #{order_id} is [status]..."
        """
        
        try:
            tracking_msg = gemini_chat.model.generate_content(tracking_prompt).text.strip()
        except:
            # Fallback tracking message - emphasize latest
            status_emoji = {"placed": "✅", "preparing": "⏲️", "cooking": "🔥", "ready": "📦", "delivered": "🚚"}.get(order_data.get('status'), "⏲️")
            tracking_msg = f"📋 Here's your latest order update! {status_emoji} Order #{order_id} is {order_data.get('status', 'being processed')}! ETA: {eta_text} 🍕"
        
        return {
            "status": "success",
            "message": tracking_msg,
            "order_data": {
                **order_data, 
                "eta": eta_text, 
                "status_progression": status_progression,
                "is_latest": True  # Flag to indicate this is the most recent order
            },
            "action": "show_tracking"
        }
    else:
        not_found_msg = gemini_chat.generate_contextual_response(
            "order not found",
            {"user_name": user_name}
        )
        return {
            "status": "not_found",
            "message": not_found_msg,
            "action": "show_menu"
        }

def get_order_status_progression(current_status: str) -> dict:
    """Get order status progression data"""
    statuses = ["placed", "preparing", "cooking", "ready", "delivered"]
    current_index = statuses.index(current_status) if current_status in statuses else 0
    
    progression = []
    for i, status in enumerate(statuses):
        progression.append({
            "status": status,
            "completed": i <= current_index,
            "active": i == current_index,
            "emoji": {"placed": "✅", "preparing": "⏲️", "cooking": "🔥", "ready": "📦", "delivered": "🚚"}[status],
            "label": status.title()
        })
    
    return {
        "current_status": current_status,
        "progress_percentage": int((current_index / (len(statuses) - 1)) * 100),
        "steps": progression
    }

def confirm_order(user_id: str, context: dict) -> dict:
    """Confirm pending order"""
    if user_id not in PENDING_CONFIRMATIONS:
        no_pending_msg = gemini_chat.generate_contextual_response(
            "no pending order",
            {"user_name": context.get("user_name", "")}
        )
        return {
            "status": "no_pending",
            "message": no_pending_msg,
            "action": "suggest_order"
        }
    
    pending_order = PENDING_CONFIRMATIONS[user_id]
    order_id = create_order_id()
    total_price = sum(item["price"] for item in pending_order["items"])
    
    # Create order data
    order_data = {
        "id": order_id,
        "order_id": order_id,
        "items": pending_order["items"],
        "address": pending_order["address"],
        "phone": pending_order["phone"],
        "user_id": user_id,
        "email": pending_order.get("email"),
        "name": pending_order.get("name"),
        "status": "placed",
        "total_price": total_price,
        "timestamp": str(uuid.uuid4())
    }
    
    # Get dynamic ETA from scheduler
    eta_text = get_dynamic_eta(order_data)
    order_data["eta"] = eta_text
    
    # Store order
    ORDERS[order_id] = order_data
    del PENDING_CONFIRMATIONS[user_id]
    
    # Use Gemini for confirmation message
    thank_you_msg = gemini_chat.generate_order_confirmation_response(
        order_data, 
        pending_order.get("name", "")
    )
    
    return {
        "status": "success",
        "message": thank_you_msg,
        "order_id": order_id,
        "order_data": order_data,
        "action": "order_placed"
    }

# User Management (simplified from previous version)
def check_user_email(email: str) -> dict:
    """Check if email exists"""
    email_lower = email.lower().strip()
    if email_lower in USERS:
        user_data = USERS[email_lower]
        user_orders = [order for order in ORDERS.values() if order.get("email", "").lower() == email_lower]
        return {
            "exists": True,
            "email": email_lower,
            "name": user_data.get("name"),
            "orders_count": len(user_orders)
        }
    else:
        return {"exists": False, "email": email_lower, "name": None, "orders_count": 0}

def save_user_data(email: str, name: str = None) -> dict:
    """Save user data"""
    email_lower = email.lower().strip()
    USERS[email_lower] = {"email": email_lower, "name": name, "created_at": str(uuid.uuid4())}
    return {"success": True, "message": "User data saved successfully", "user": USERS[email_lower]}

def get_user_order_history(email: str) -> dict:
    """Get user order history"""
    email_lower = email.lower().strip()
    user_orders = []
    
    for order_id, order in ORDERS.items():
        if order.get("email", "").lower() == email_lower:
            user_orders.append({
                "order_id": order_id,
                "items": order.get("items", []),
                "status": order.get("status", "unknown"),
                "total_price": order.get("total_price", 0),
                "timestamp": order.get("timestamp", "")
            })
    
    user_orders.sort(key=lambda x: x["timestamp"], reverse=True)
    current_orders = [order for order in user_orders if order["status"] in ["placed", "preparing", "cooking", "ready"]]
    completed_orders = [order for order in user_orders if order["status"] in ["delivered", "completed"]]
    
    return {
        "email": email_lower,
        "total_orders": len(user_orders),
        "current_orders": current_orders,
        "completed_orders": completed_orders,
        "all_orders": user_orders
    }

# API Routes
@app.get("/api/menu")
async def get_menu():
    """Get pizza menu"""
    return {"pizzas": MENU, "categories": ["all", "veg", "non-veg"]}

@app.post("/api/user/check", response_model=UserResponse)
async def check_user_endpoint(user_request: UserRequest):
    """Check if user email exists"""
    result = check_user_email(user_request.email)
    return UserResponse(
        email=result["email"],
        name=result["name"],
        exists=result["exists"],
        orders_count=result["orders_count"]
    )

@app.post("/api/user/save")
async def save_user_endpoint(user_request: UserRequest):
    """Save user data"""
    return save_user_data(user_request.email, user_request.name)

@app.get("/api/user/{email}/orders")
async def get_user_orders_endpoint(email: str):
    """Get user order history"""
    return get_user_order_history(email)

@app.get("/api/user/{email}/greeting")
async def get_personalized_greeting_endpoint(email: str, context: str = "general"):
    """Get personalized greeting using Gemini"""
    user_check = check_user_email(email)
    
    if user_check["exists"] and user_check["name"]:
        is_new_user = user_check["orders_count"] == 0
        greeting = gemini_chat.generate_welcome_message(user_check["name"], is_new_user)
    else:
        greeting = "Welcome to Pizza Planet! How can I help you today?"
    
    return {
        "greeting": greeting,
        "user_exists": user_check["exists"],
        "user_name": user_check["name"],
        "orders_count": user_check["orders_count"]
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest):
    """Main chat endpoint with Gemini integration"""
    message = chat_request.message.strip()
    user_email = chat_request.context.get("email") if chat_request.context else None
    
    # Get user name from database
    user_name = None
    if user_email:
        user_check = check_user_email(user_email)
        if user_check["exists"]:
            user_name = user_check["name"]
    
    # Enhanced context for Gemini
    user_context = {
        "user_email": user_email,
        "user_name": user_name,
        "user_id": chat_request.user_id
    }
    
    # Use Gemini for intent analysis
    intent_data = gemini_chat.parse_user_intent(message, user_context)
    intent = intent_data.get("intent")
    action = intent_data.get("action")
    category = intent_data.get("category")
    
    # Route based on Gemini's analysis
    if intent == "confirm":
        result = confirm_order(chat_request.user_id, user_context)
        return ChatResponse(
            response=result["message"],
            intent=intent,
            action=result["action"],
            context={"order_id": result.get("order_id")}
        )
    
    elif intent == "order":
        result = process_order(message, user_context)
        return ChatResponse(
            response=result["message"],
            intent=intent,
            action=result["action"],
            suggested_items=[result["item"]] if "item" in result else result.get("suggestions", []),
            pending_order=result.get("item")
        )
    
    elif intent == "track":
        result = track_order(message, user_context)
        return ChatResponse(
            response=result["message"],
            intent=intent,
            action=result["action"],
            context={"order_data": result.get("order_data")}
        )
    
    elif intent == "menu":
        if category == "veg":
            items = get_menu_by_category("veg")
            response_msg = f"🥗 Here are our {len(items)} delicious vegetarian pizzas! Perfect for those who love fresh vegetables and cheese!"
        elif category == "non-veg":
            items = get_menu_by_category("non-veg")
            response_msg = f"🍖 Here are our {len(items)} amazing non-vegetarian pizzas! Loaded with meat and packed with flavor!"
        else:
            items = MENU
            response_msg = "🍕 Here's our complete pizza menu! What looks good to you?\n\n💡 Tip: Say 'veg options' or 'non-veg options' to filter the menu!"
        
        return ChatResponse(
            response=response_msg,
            intent=intent,
            action="show_menu",
            suggested_items=items,
            context={"category": category or "all", "filter_applied": bool(category)}
        )
    
    elif intent == "greeting":
        if user_name:
            greeting = gemini_chat.generate_welcome_message(user_name, False)
        else:
            greeting = "🍕 Hello! Welcome to Pizza Planet! How can I help you today?"
        
        return ChatResponse(
            response=greeting,
            intent=intent,
            action="continue_chat"
        )
    
    elif intent == "recommendation":
        # Get popular items from each category
        veg_items = get_menu_by_category("veg")[:2]
        non_veg_items = get_menu_by_category("non-veg")[:2]
        recommended_items = veg_items + non_veg_items
        
        recommendation_msg = gemini_chat.generate_contextual_response(
            "pizza recommendations",
            {"user_name": user_name},
            items=recommended_items
        )
        
        return ChatResponse(
            response=recommendation_msg,
            intent=intent,
            action="show_menu",
            suggested_items=recommended_items
        )
    
    else:  # casual conversation
        casual_response = gemini_chat.generate_contextual_response(
            "casual conversation",
            {"user_name": user_name},
            original_message=message
        )
        return ChatResponse(
            response=casual_response,
            intent=intent,
            action="continue_chat"
        )

@app.post("/api/order", response_model=OrderResponse)
async def place_order_endpoint(order_request: OrderRequest):
    """Place pizza order directly"""
    order_id = create_order_id()
    validated_items = []
    total_price = 0
    
    for item_name in order_request.items:
        # Try to find exact match in menu first
        found_item = None
        
        # Look for exact match by name (regardless of size)
        for menu_item in MENU:
            if menu_item["name"].lower() == item_name.lower():
                found_item = menu_item
                break
        
        # If not found, try with aliases
        if not found_item:
            for menu_item in MENU:
                if "aliases" in menu_item:
                    for alias in menu_item["aliases"]:
                        if alias.lower() == item_name.lower():
                            found_item = menu_item
                            break
                    if found_item:
                        break
        
        if found_item:
            validated_items.append(found_item)
            total_price += found_item["price"]
        else:
            raise HTTPException(status_code=400, detail=f"Item '{item_name}' not found in menu")
    
    if not validated_items:
        raise HTTPException(status_code=400, detail="No valid items in order")
    
    ORDERS[order_id] = {
        "id": order_id,
        "order_id": order_id,
        "items": validated_items,
        "address": order_request.address,
        "phone": order_request.phone,
        "user_id": order_request.user_id,
        "email": order_request.email,
        "status": "placed",
        "total_price": total_price,
        "timestamp": str(uuid.uuid4())
    }
    
    eta_text = get_dynamic_eta(ORDERS[order_id])
    
    return OrderResponse(
        order_id=order_id,
        estimated_time=eta_text,
        total_price=total_price,
        status="placed"
    )

@app.get("/api/order/{order_id}")
async def get_order_status_endpoint(order_id: str):
    """Get order status"""
    if order_id not in ORDERS:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = ORDERS[order_id]
    eta_text = get_dynamic_eta(order)
    
    return {
        "order": order,
        "status": order["status"],
        "estimated_time": eta_text
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Pizza Planet MCP Server is running",
        "gemini_integration": True
    }

if __name__ == "__main__":
    print("🚀 Starting Pizza Planet MCP Server...")
    print("🍕 Features: Menu, Ordering, Tracking, User Management")
    print("🧠 AI: Gemini Flash Integration")
    print("📡 Port: 8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
