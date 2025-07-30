#!/usr/bin/env python3
"""
Infrastructure - FastAPI Web Server
Clean architecture implementation of the web API using dependency injection.
"""

import sys
import os
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..di_container import container
from ...application.use_cases.order_use_cases import OrderRequest


# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    user_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    response: str
    intent: str
    tools_used: List[str] = []
    context: Dict[str, Any] = {}


class MenuResponse(BaseModel):
    success: bool
    category: str
    items: List[Dict[str, Any]]
    total_items: int


class OrderResponse(BaseModel):
    success: bool
    order_id: Optional[str] = None
    message: str
    order_details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# FastAPI app with lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Pizza AI Clean Architecture FastAPI Server...")
    print("🏗️ Using Clean Architecture with Dependency Injection")
    print("🧠 LLM: Groq Integration")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Pizza AI FastAPI Server...")


app = FastAPI(
    title="Pizza AI - Clean Architecture API",
    description="Pizza ordering system using Clean Architecture principles",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint - handles natural language pizza ordering"""
    try:
        # Get dependencies from container
        llm_service = container.get_llm_service()
        order_use_cases = container.get_order_use_cases()
        
        # Parse user intent using LLM
        context = {
            "user_email": request.user_email,
            "user_name": request.user_name,
            "user_id": request.user_id
        }
        
        intent_data = await llm_service.parse_user_intent(request.message, context)
        intent = intent_data.get("intent", "general_chat")
        parameters = intent_data.get("parameters", {})
        
        tools_used = []
        response_message = ""
        response_context = {"intent": intent}
        
        # Route based on intent
        if intent == "get_menu":
            category = parameters.get("category", "all")
            result = await order_use_cases.get_menu(category)
            tools_used.append("get_menu")
            
            if result["success"]:
                response_message = await llm_service.generate_response(
                    f"Generate a friendly message about showing the {category} pizza menu with {result['total_items']} items"
                )
                response_context["menu_items"] = result["items"]
            else:
                response_message = await llm_service.generate_error_message(
                    result.get("error", "Menu unavailable"), context
                )
        
        elif intent == "find_pizza":
            name = parameters.get("name", "")
            size = parameters.get("size", "large")
            
            if not name:
                response_message = "What pizza are you looking for? I can help you find it!"
            else:
                result = await order_use_cases.find_pizza(name, size)
                tools_used.append("find_pizza")
                
                if result["success"]:
                    pizza = result["pizza"]
                    response_message = f"🍕 Great! I found {pizza['name']} for {pizza['price']}. {pizza['description']} Would you like to order this?"
                    response_context["pizza_found"] = pizza
                else:
                    response_message = await llm_service.generate_error_message(
                        result.get("error", "Pizza not found"), context
                    )
        
        elif intent == "place_order":
            # For full order placement, we need more structured data
            if not request.user_email or not request.user_name:
                response_message = "To place an order, I'll need your email and name. Could you provide those?"
            else:
                # This is a simplified order - in real implementation, 
                # would need more sophisticated parameter extraction
                items = parameters.get("items", ["margherita"])
                
                try:
                    order_request = OrderRequest(
                        customer_name=request.user_name,
                        customer_email=request.user_email,
                        customer_phone="555-0123",  # Default for demo
                        customer_address="123 Main Street",  # Default for demo
                        items=items
                    )
                    
                    result = await order_use_cases.place_order(order_request)
                    tools_used.append("place_order")
                    
                    if result.success:
                        response_message = result.message
                        response_context["order"] = result.order_details
                    else:
                        response_message = await llm_service.generate_error_message(
                            result.error or "Order failed", context
                        )
                except Exception as e:
                    response_message = f"I need a bit more information to place your order. What pizza would you like?"
        
        elif intent == "track_order":
            order_id = parameters.get("order_id")
            result = await order_use_cases.track_order(order_id, request.user_email)
            tools_used.append("track_order")
            
            if result.success:
                response_message = result.message
                response_context["order_status"] = result.order_details
            else:
                response_message = await llm_service.generate_error_message(
                    result.error or "Order not found", context
                )
        
        elif intent == "get_suggestions":
            preferences = parameters.get("preferences", "popular")
            result = await order_use_cases.get_suggestions(request.user_email, preferences)
            tools_used.append("get_suggestions")
            
            if result["success"]:
                response_message = result["message"]
                response_context["suggestions"] = result["suggestions"]
            else:
                response_message = await llm_service.generate_error_message(
                    result.get("error", "No suggestions available"), context
                )
        
        else:  # general_chat
            response_message = await llm_service.generate_welcome_message(
                request.user_name, 
                is_new_user=True  # Could check this via user repository
            )
        
        return ChatResponse(
            response=response_message,
            intent=intent,
            tools_used=tools_used,
            context=response_context
        )
        
    except Exception as e:
        print(f"❌ Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/menu", response_model=MenuResponse)
async def get_menu_endpoint(category: str = "all"):
    """Get pizza menu by category"""
    try:
        order_use_cases = container.get_order_use_cases()
        result = await order_use_cases.get_menu(category)
        
        return MenuResponse(
            success=result["success"],
            category=result["category"],
            items=result["items"],
            total_items=result["total_items"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/order", response_model=OrderResponse)
async def place_order_endpoint(request: OrderRequest):
    """Place a direct order"""
    try:
        order_use_cases = container.get_order_use_cases()
        result = await order_use_cases.place_order(request)
        
        return OrderResponse(
            success=result.success,
            order_id=result.order_id,
            message=result.message,
            order_details=result.order_details,
            error=result.error
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/order/{order_id}")
async def track_order_endpoint(order_id: str):
    """Track order by ID"""
    try:
        order_use_cases = container.get_order_use_cases()
        result = await order_use_cases.track_order(order_id)
        
        return {
            "success": result.success,
            "order_id": result.order_id,
            "message": result.message,
            "order_details": result.order_details,
            "error": result.error
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test that our dependencies are working
        pizza_repo = container.get_pizza_repository()
        pizzas = await pizza_repo.get_available_pizzas()
        
        return {
            "status": "healthy",
            "message": "Pizza AI Clean Architecture API is running",
            "architecture": "Clean Architecture with Dependency Injection",
            "available_pizzas": len(pizzas),
            "llm_integration": "Groq Llama 3.1 7B",
            "version": "2.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {e}")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "🍕 Pizza AI - Clean Architecture API",
        "description": "Modern pizza ordering system built with Clean Architecture principles",
        "architecture": {
            "pattern": "Clean Architecture",
            "layers": ["Domain", "Application", "Infrastructure"],
            "principles": ["Dependency Inversion", "Single Responsibility", "Interface Segregation"]
        },
        "endpoints": {
            "chat": "POST /chat - Natural language pizza ordering",
            "menu": "GET /menu?category={all|veg|non-veg} - Get menu",
            "order": "POST /order - Place structured order",
            "track": "GET /order/{order_id} - Track order",
            "health": "GET /health - Health check"
        },
        "version": "2.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    print("🍕 Starting Pizza AI Clean Architecture FastAPI Server...")
    print("🌐 API will be available at: http://localhost:8001")
    print("🏗️ Built with Clean Architecture principles")
    print("🧠 Powered by: Groq LLM + Domain-Driven Design")
    uvicorn.run(app, host="0.0.0.0", port=8001) 