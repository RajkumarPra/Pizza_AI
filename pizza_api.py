#!/usr/bin/env python3
"""
Pizza AI FastAPI Client
Single endpoint that integrates Groq LLM with MCP Server tools
"""

import asyncio
import json
import os
import subprocess
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# MCP Client imports
from mcp.client.stdio import stdio_client
from mcp.types import CallToolRequest, ListToolsRequest, ReadResourceRequest, ListResourcesRequest

# Groq integration
from utils.groq_integration import groq_chat

# FastAPI setup
app = FastAPI(title="Pizza AI", description="AI-powered pizza ordering with MCP integration")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend if it exists
if os.path.exists("Frontend"):
    app.mount("/", StaticFiles(directory="Frontend", html=True), name="frontend")

# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    user_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    tools_used: List[str] = []
    context: Optional[Dict[str, Any]] = None

# MCP Client Manager
class MCPClientManager:
    def __init__(self):
        self.mcp_process = None
        self.client = None
        self.available_tools = []
    
    async def start_mcp_server(self):
        """Start the MCP server process"""
        try:
            self.mcp_process = await asyncio.create_subprocess_exec(
                sys.executable, "pizza_mcp_server.py",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            print("🔧 MCP Server started")
            return True
        except Exception as e:
            print(f"❌ Failed to start MCP server: {e}")
            return False
    
    async def connect_client(self):
        """Connect to the MCP server"""
        try:
            if not self.mcp_process:
                await self.start_mcp_server()
            
            # Create stdio client
            self.client = stdio_client(self.mcp_process.stdin, self.mcp_process.stdout)
            
            # Initialize connection
            await self.client.__aenter__()
            
            # List available tools
            tools_result = await self.client.call(ListToolsRequest())
            self.available_tools = [tool.name for tool in tools_result.tools]
            
            print(f"🛠️  Connected to MCP server. Available tools: {self.available_tools}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to MCP server: {e}")
            return False
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server"""
        try:
            if not self.client:
                await self.connect_client()
            
            result = await self.client.call(
                CallToolRequest(name=tool_name, arguments=arguments)
            )
            
            # Extract text content from result
            if result.content and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    return json.loads(content.text)
            
            return {"error": "No content returned from tool"}
            
        except Exception as e:
            print(f"❌ Error calling tool {tool_name}: {e}")
            return {"error": str(e)}
    
    async def get_menu(self, category: str = "all") -> Dict[str, Any]:
        """Get pizza menu"""
        return await self.call_tool("get_menu", {"category": category})
    
    async def find_pizza(self, name: str, size: str = "") -> Dict[str, Any]:
        """Find a specific pizza"""
        return await self.call_tool("find_pizza", {"name": name, "size": size})
    
    async def place_order(self, pizza_name: str, size: str, customer_email: str, 
                         customer_name: str = "", address: str = "123 Main Street", 
                         phone: str = "555-0123") -> Dict[str, Any]:
        """Place a pizza order"""
        return await self.call_tool("place_order", {
            "pizza_name": pizza_name,
            "size": size,
            "customer_email": customer_email,
            "customer_name": customer_name,
            "address": address,
            "phone": phone
        })
    
    async def track_order(self, order_id: str = "", customer_email: str = "") -> Dict[str, Any]:
        """Track an order"""
        return await self.call_tool("track_order", {
            "order_id": order_id,
            "customer_email": customer_email
        })
    
    async def check_user(self, email: str) -> Dict[str, Any]:
        """Check if user exists"""
        return await self.call_tool("check_user", {"email": email})
    
    async def save_user(self, email: str, name: str) -> Dict[str, Any]:
        """Save user information"""
        return await self.call_tool("save_user", {"email": email, "name": name})
    
    async def get_suggestions(self, preference: str) -> Dict[str, Any]:
        """Get pizza suggestions"""
        return await self.call_tool("get_suggestions", {"preference": preference})
    
    async def cleanup(self):
        """Clean up MCP client and server"""
        try:
            if self.client:
                await self.client.__aexit__(None, None, None)
            if self.mcp_process:
                self.mcp_process.terminate()
                await self.mcp_process.wait()
        except Exception as e:
            print(f"⚠️ Error during cleanup: {e}")

# Global MCP client manager
mcp_manager = MCPClientManager()

class PizzaAIAgent:
    """AI Agent that uses Groq LLM with MCP tools"""
    
    def __init__(self, mcp_manager: MCPClientManager):
        self.mcp_manager = mcp_manager
        self.groq_client = groq_chat
    
    async def process_message(self, message: str, user_email: str = None, user_name: str = None) -> Dict[str, Any]:
        """Process user message and determine which tools to use"""
        
        # First, analyze intent using Groq
        intent_prompt = f"""
        Analyze this pizza ordering message and determine the user's intent.
        
        Message: "{message}"
        
        Respond with a JSON object containing:
        - "intent": one of [order, track, menu, greeting, recommendation, user_check]
        - "action": specific action to take
        - "parameters": any parameters extracted from the message
        
        Examples:
        - "I want a pepperoni pizza" → {{"intent": "order", "action": "find_pizza", "parameters": {{"name": "pepperoni"}}}}
        - "Show me the menu" → {{"intent": "menu", "action": "get_menu", "parameters": {{}}}}
        - "Track my order" → {{"intent": "track", "action": "track_order", "parameters": {{}}}}
        
        JSON only:
        """
        
        try:
            intent_response = self.groq_client._generate_response(intent_prompt, max_tokens=200)
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', intent_response, re.DOTALL)
            if json_match:
                intent_data = json.loads(json_match.group())
            else:
                # Fallback intent detection
                intent_data = self._fallback_intent_detection(message)
        except:
            intent_data = self._fallback_intent_detection(message)
        
        # Execute the appropriate action
        tools_used = []
        result_data = {}
        
        intent = intent_data.get("intent")
        action = intent_data.get("action")
        parameters = intent_data.get("parameters", {})
        
        if intent == "menu":
            category = parameters.get("category", "all")
            result = await self.mcp_manager.get_menu(category)
            tools_used.append("get_menu")
            result_data = result
        
        elif intent == "order":
            if action == "find_pizza":
                pizza_name = parameters.get("name", "")
                size = parameters.get("size", "")
                
                if pizza_name:
                    result = await self.mcp_manager.find_pizza(pizza_name, size)
                    tools_used.append("find_pizza")
                    result_data = result
                    
                    if result.get("found"):
                        # Ask for confirmation
                        pizza = result["pizza"]
                        confirmation_msg = f"Great! I found {pizza['name']} ({pizza['size']}) for ${pizza['price']:.2f}. "
                        if user_email:
                            confirmation_msg += "Would you like me to place this order for you?"
                        else:
                            confirmation_msg += "Please provide your email address to place the order."
                        
                        return {
                            "response": confirmation_msg,
                            "tools_used": tools_used,
                            "context": {
                                "pending_order": pizza,
                                "user_email": user_email,
                                "user_name": user_name
                            }
                        }
            
            elif action == "place_order":
                # Extract order details
                pizza_name = parameters.get("pizza_name", "")
                size = parameters.get("size", "")
                
                if not pizza_name or not size or not user_email:
                    return {
                        "response": "To place an order, I need the pizza name, size, and your email address. Please provide these details.",
                        "tools_used": [],
                        "context": {}
                    }
                
                result = await self.mcp_manager.place_order(
                    pizza_name=pizza_name,
                    size=size,
                    customer_email=user_email,
                    customer_name=user_name or ""
                )
                tools_used.append("place_order")
                result_data = result
        
        elif intent == "track":
            if user_email:
                result = await self.mcp_manager.track_order(customer_email=user_email)
            else:
                order_id = parameters.get("order_id", "")
                result = await self.mcp_manager.track_order(order_id=order_id)
            
            tools_used.append("track_order")
            result_data = result
        
        elif intent == "recommendation":
            preference = parameters.get("preference", "popular")
            result = await self.mcp_manager.get_suggestions(preference)
            tools_used.append("get_suggestions")
            result_data = result
        
        elif intent == "user_check" and user_email:
            result = await self.mcp_manager.check_user(user_email)
            tools_used.append("check_user")
            result_data = result
        
        # Generate natural language response using Groq
        response_text = await self._generate_natural_response(message, intent_data, result_data, user_name)
        
        return {
            "response": response_text,
            "tools_used": tools_used,
            "context": {
                "intent": intent,
                "tool_results": result_data,
                "user_email": user_email,
                "user_name": user_name
            }
        }
    
    def _fallback_intent_detection(self, message: str) -> Dict[str, Any]:
        """Fallback intent detection if Groq fails"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["menu", "options", "available", "show"]):
            return {"intent": "menu", "action": "get_menu", "parameters": {}}
        elif any(word in message_lower for word in ["order", "want", "get", "pizza"]):
            return {"intent": "order", "action": "find_pizza", "parameters": {"name": "margherita"}}
        elif any(word in message_lower for word in ["track", "status", "where"]):
            return {"intent": "track", "action": "track_order", "parameters": {}}
        elif any(word in message_lower for word in ["recommend", "suggest", "popular"]):
            return {"intent": "recommendation", "action": "get_suggestions", "parameters": {"preference": "popular"}}
        else:
            return {"intent": "greeting", "action": "none", "parameters": {}}
    
    async def _generate_natural_response(self, original_message: str, intent_data: Dict, 
                                       tool_result: Dict, user_name: str = None) -> str:
        """Generate a natural language response using Groq"""
        
        name_part = f" {user_name}" if user_name else ""
        
        if intent_data.get("intent") == "menu":
            if tool_result.get("items"):
                items = tool_result["items"]
                items_text = ", ".join([f"{item['name']} ({item['size']}) - ${item['price']}" for item in items[:5]])
                return f"Here's our menu{name_part}! {items_text}. What sounds good to you? 🍕"
            else:
                return f"I'm having trouble getting the menu right now{name_part}. Please try again!"
        
        elif intent_data.get("intent") == "order":
            if tool_result.get("success"):
                order = tool_result["order"]
                return f"🎉 Great{name_part}! Your order has been placed successfully!\n\n📋 Order ID: {order['order_id']}\n🍕 Items: {order['items'][0]['name']} ({order['items'][0]['size']})\n💰 Total: ${order['total_price']:.2f}\n⏰ ETA: {order['eta']}\n\nThank you for choosing Pizza Planet! 🚀"
            elif not tool_result.get("found"):
                suggestions = tool_result.get("suggestions", [])
                if suggestions:
                    items_text = ", ".join([item["name"] for item in suggestions[:3]])
                    return f"I couldn't find that exact pizza{name_part}. Here are some similar options: {items_text}. Which one would you like?"
                else:
                    return f"I couldn't find that pizza{name_part}. Would you like to see our full menu?"
        
        elif intent_data.get("intent") == "track":
            if tool_result.get("found"):
                order = tool_result["order"]
                return f"📋 Here's your order status{name_part}:\n\n🆔 Order: {order['order_id']}\n📊 Status: {order['status'].title()}\n🍕 Items: {order['items'][0]['name']} ({order['items'][0]['size']})\n⏰ ETA: {order.get('eta', 'Calculating...')}"
            else:
                return f"I couldn't find any orders{name_part}. Would you like to place a new order?"
        
        elif intent_data.get("intent") == "recommendation":
            if tool_result.get("suggestions"):
                suggestions = tool_result["suggestions"]
                items_text = ", ".join([f"{item['name']} (${item['price']})" for item in suggestions])
                return f"{tool_result.get('message', 'Here are my recommendations')}{name_part}: {items_text}. Which one catches your eye? 🍕"
        
        # Default response
        return f"Hi{name_part}! I'm here to help you order delicious pizzas. You can ask me to show the menu, place an order, or track existing orders. What would you like to do? 🍕"

# Global AI agent
ai_agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize MCP connection on startup"""
    global ai_agent
    
    print("🚀 Starting Pizza AI...")
    success = await mcp_manager.connect_client()
    if success:
        ai_agent = PizzaAIAgent(mcp_manager)
        print("✅ Pizza AI ready!")
    else:
        print("❌ Failed to initialize MCP connection")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    await mcp_manager.cleanup()

# Main endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Single chat endpoint that processes messages with MCP tools"""
    
    if not ai_agent:
        raise HTTPException(status_code=500, detail="AI agent not initialized")
    
    try:
        result = await ai_agent.process_message(
            message=request.message,
            user_email=request.user_email,
            user_name=request.user_name
        )
        
        return ChatResponse(
            response=result["response"],
            tools_used=result["tools_used"],
            context=result["context"]
        )
        
    except Exception as e:
        print(f"❌ Error processing message: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Pizza AI is running",
        "mcp_connected": ai_agent is not None,
        "architecture": "FastAPI + MCP + Groq"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "🍕 Pizza AI - Powered by MCP and Groq",
        "endpoint": "/chat",
        "example": {
            "message": "I want a pepperoni pizza",
            "user_email": "user@example.com",
            "user_name": "John"
        }
    }

if __name__ == "__main__":
    print("🍕 Starting Pizza AI FastAPI Server...")
    print("🔗 Architecture: FastAPI + MCP Server + Groq LLM")
    print("📡 Single endpoint: POST /chat")
    print("🌐 Port: 8001")
    uvicorn.run(app, host="0.0.0.0", port=8001) 