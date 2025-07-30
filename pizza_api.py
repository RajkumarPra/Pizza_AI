#!/usr/bin/env python3
"""
Pizza AI FastAPI Client - MCP Host with Groq LLM
Acts as MCP client/host that communicates with pizza_mcp_server.py
"""

import os
import sys
import asyncio
import subprocess
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# MCP client imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Groq integration
from utils.groq_integration import groq_chat

# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    user_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    response: str
    tools_used: List[str] = []
    context: Dict[str, Any] = {}

class MCPClientManager:
    """Manages connection to MCP server via stdio"""
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.server_process: Optional[subprocess.Popen] = None
        self.available_tools: List[Dict[str, Any]] = []
        
    async def start_and_connect(self):
        """Start MCP server and establish connection"""
        try:
            # Set up server parameters for stdio connection
            server_params = StdioServerParameters(
                command="python",
                args=["pizza_mcp_server.py"],
                env=None
            )
            
            print("🔄 Starting MCP server and establishing connection...")
            
            # Create stdio client connection
            self.stdio_transport = await stdio_client(server_params).__aenter__()
            read_stream, write_stream = self.stdio_transport
            
            # Create client session
            self.session = ClientSession(read_stream, write_stream)
            await self.session.__aenter__()
            
            # Initialize the connection
            await self.session.initialize()
            print("✅ Connected to MCP server")
            
            # List available tools
            tools_response = await self.session.list_tools()
            self.available_tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                } 
                for tool in tools_response.tools
            ]
            
            print(f"📡 Available tools: {[tool['name'] for tool in self.available_tools]}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to MCP server: {e}")
            await self.cleanup()
            return False
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected")
        
        try:
            result = await self.session.call_tool(tool_name, arguments)
            return {
                "success": True,
                "content": result.content[0].text if result.content else "No content",
                "tool_name": tool_name
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name
            }
    
    # Convenience methods for each MCP tool
    async def get_menu(self, category: str = "all") -> Dict[str, Any]:
        return await self.call_tool("get_menu", {"category": category})
    
    async def find_pizza(self, name: str, size: str = "large") -> Dict[str, Any]:
        return await self.call_tool("find_pizza", {"name": name, "size": size})
    
    async def place_order(self, customer_name: str, customer_email: str, 
                         customer_phone: str, customer_address: str,
                         items: List[str]) -> Dict[str, Any]:
        return await self.call_tool("place_order", {
            "customer_name": customer_name,
            "customer_email": customer_email,
            "customer_phone": customer_phone,
            "customer_address": customer_address,
            "items": items
        })
    
    async def track_order(self, order_id: Optional[str] = None, 
                         customer_email: Optional[str] = None) -> Dict[str, Any]:
        return await self.call_tool("track_order", {
            "order_id": order_id,
            "customer_email": customer_email
        })
    
    async def check_user(self, email: str) -> Dict[str, Any]:
        return await self.call_tool("check_user", {"email": email})
    
    async def save_user(self, email: str, name: str) -> Dict[str, Any]:
        return await self.call_tool("save_user", {"email": email, "name": name})
    
    async def get_suggestions(self, preferences: str = "popular") -> Dict[str, Any]:
        return await self.call_tool("get_suggestions", {"preferences": preferences})
    
    async def cleanup(self):
        """Clean up MCP session and server process"""
        try:
            if self.session:
                await self.session.__aexit__(None, None, None)
            if hasattr(self, 'stdio_transport'):
                await self.stdio_transport.__aexit__(None, None, None)
            print("🧹 Cleaned up MCP client connection")
        except Exception as e:
            print(f"⚠️  Error during cleanup: {e}")

class PizzaAIAgent:
    """AI agent that processes user messages and calls appropriate MCP tools"""
    
    def __init__(self, mcp_manager: MCPClientManager):
        self.mcp_manager = mcp_manager
    
    async def process_message(self, message: str, user_email: Optional[str] = None, 
                            user_name: Optional[str] = None) -> Dict[str, Any]:
        """Process user message and execute appropriate actions"""
        
        # Use Groq to analyze intent and extract parameters
        intent_prompt = f"""
        Analyze this user message for pizza ordering intent: "{message}"
        
        Available actions:
        - get_menu: Show pizza menu (category: all/veg/non-veg)
        - find_pizza: Search for specific pizza (name, size)
        - place_order: Place an order (needs customer info and items)
        - track_order: Track existing order (order_id or email)
        - check_user: Check if user exists (email)
        - save_user: Save user information (email, name)
        - get_suggestions: Get pizza recommendations
        - general_chat: For greetings and general conversation
        
        Return JSON with:
        {{
            "intent": "action_name",
            "parameters": {{"param1": "value1", "param2": "value2"}},
            "requires_user_info": true/false,
            "explanation": "brief explanation"
        }}
        """
        
        try:
            intent_analysis = groq_chat._generate_response(intent_prompt)
            
            # Extract JSON from response
            import json
            import re
            
            json_match = re.search(r'\{.*\}', intent_analysis, re.DOTALL)
            if json_match:
                intent_data = json.loads(json_match.group())
            else:
                intent_data = self._fallback_intent_detection(message)
                
        except Exception as e:
            print(f"⚠️  Intent analysis failed: {e}")
            intent_data = self._fallback_intent_detection(message)
        
        # Execute the appropriate action based on intent
        tools_used = []
        context = {
            "intent": intent_data.get("intent", "unknown"),
            "user_email": user_email,
            "user_name": user_name
        }
        
        try:
            if intent_data["intent"] == "get_menu":
                category = intent_data.get("parameters", {}).get("category", "all")
                result = await self.mcp_manager.get_menu(category)
                tools_used.append("get_menu")
                response = await self._generate_natural_response(intent_data["intent"], result, user_name)
                
            elif intent_data["intent"] == "find_pizza":
                params = intent_data.get("parameters", {})
                name = params.get("name", "")
                size = params.get("size", "large")
                
                result = await self.mcp_manager.find_pizza(name, size)
                tools_used.append("find_pizza")
                response = await self._generate_natural_response(intent_data["intent"], result, user_name)
                
            elif intent_data["intent"] == "track_order":
                params = intent_data.get("parameters", {})
                order_id = params.get("order_id")
                
                result = await self.mcp_manager.track_order(order_id, user_email)
                tools_used.append("track_order")
                response = await self._generate_natural_response(intent_data["intent"], result, user_name)
                
            elif intent_data["intent"] == "get_suggestions":
                preferences = intent_data.get("parameters", {}).get("preferences", "popular")
                result = await self.mcp_manager.get_suggestions(preferences)
                tools_used.append("get_suggestions")
                response = await self._generate_natural_response(intent_data["intent"], result, user_name)
                
            elif intent_data["intent"] == "check_user" and user_email:
                result = await self.mcp_manager.check_user(user_email)
                tools_used.append("check_user")
                response = await self._generate_natural_response(intent_data["intent"], result, user_name)
                
            else:
                # General conversation or unsupported action
                response = await self._generate_natural_response("general_chat", 
                                                               {"message": message}, user_name)
        
        except Exception as e:
            print(f"❌ Error executing action: {e}")
            response = f"I apologize, but I encountered an error while processing your request. Please try again."
        
        return {
            "response": response,
            "tools_used": tools_used,
            "context": context
        }
    
    def _fallback_intent_detection(self, message: str) -> Dict[str, Any]:
        """Simple fallback intent detection"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["menu", "show", "list", "what do you have"]):
            return {"intent": "get_menu", "parameters": {"category": "all"}}
        elif any(word in message_lower for word in ["track", "order", "status", "where is"]):
            return {"intent": "track_order", "parameters": {}}
        elif any(word in message_lower for word in ["suggest", "recommend", "popular", "best"]):
            return {"intent": "get_suggestions", "parameters": {"preferences": "popular"}}
        elif any(word in message_lower for word in ["pizza", "want", "order", "buy"]):
            return {"intent": "find_pizza", "parameters": {"name": "margherita", "size": "large"}}
        else:
            return {"intent": "general_chat", "parameters": {}}
    
    async def _generate_natural_response(self, intent: str, tool_result: Dict[str, Any], 
                                       user_name: Optional[str] = None) -> str:
        """Generate natural language response based on intent and tool results"""
        
        name_prefix = f"{user_name}, " if user_name else ""
        
        if intent == "get_menu":
            if tool_result.get("success"):
                return f"🍕 {name_prefix}Here's our delicious pizza menu! What catches your eye?"
            else:
                return f"Sorry {name_prefix}I'm having trouble accessing our menu right now. Please try again!"
        
        elif intent == "find_pizza":
            if tool_result.get("success") and "found" in tool_result.get("content", "").lower():
                return f"Great choice{', ' + user_name if user_name else ''}! I found that pizza for you. Would you like to place an order?"
            else:
                return f"I couldn't find that exact pizza{', ' + user_name if user_name else ''}. Let me show you our full menu instead!"
        
        elif intent == "track_order":
            if tool_result.get("success"):
                return f"{name_prefix}Here's your order status! Your pizza is on its way! 🚚"
            else:
                return f"I couldn't find any orders{', ' + user_name if user_name else ''}. Could you double-check your order number?"
        
        elif intent == "get_suggestions":
            if tool_result.get("success"):
                return f"🌟 {name_prefix}Based on what's popular, here are my top recommendations for you!"
            else:
                return f"Let me suggest our classic Margherita pizza{', ' + user_name if user_name else ''} - it's always a crowd favorite!"
        
        else:
            return f"Hello{', ' + user_name if user_name else ''}! I'm here to help you with pizza orders. You can ask me about our menu, place orders, or track existing orders. What can I do for you today? 🍕"

# Global instances
mcp_manager = MCPClientManager()
ai_agent = PizzaAIAgent(mcp_manager)

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Pizza AI FastAPI Client...")
    success = await mcp_manager.start_and_connect()
    if not success:
        print("❌ Failed to start MCP server connection")
        # Continue anyway for basic functionality
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Pizza AI FastAPI Client...")
    await mcp_manager.cleanup()

# FastAPI app
app = FastAPI(
    title="Pizza AI - MCP Client",
    description="FastAPI client that integrates Groq LLM with MCP pizza tools",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint - single point of interaction"""
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
        print(f"❌ Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    mcp_status = "connected" if mcp_manager.session else "disconnected"
    available_tools = [tool["name"] for tool in mcp_manager.available_tools]
    
    return {
        "status": "healthy",
        "mcp_server": mcp_status,
        "available_tools": available_tools,
        "groq_integration": True
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Pizza AI - MCP Client API",
        "description": "FastAPI client integrating Groq LLM with MCP pizza server",
        "endpoints": {
            "chat": "POST /chat - Main interaction endpoint",
            "health": "GET /health - Health check and status"
        },
        "mcp_tools": [tool["name"] for tool in mcp_manager.available_tools],
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    print("🍕 Starting Pizza AI FastAPI Client...")
    print("🌐 API will be available at: http://localhost:8001")
    print("📡 Single endpoint: POST /chat")
    print("🧠 Powered by: Groq LLM + MCP Protocol")
    uvicorn.run(app, host="0.0.0.0", port=8001) 