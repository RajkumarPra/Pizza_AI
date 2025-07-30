#!/usr/bin/env python3
"""
Pizza AI MCP Server
Exposes pizza ordering tools to LLMs via Model Context Protocol
"""

import asyncio
import json
import sys
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from mcp.server import Server
from mcp.types import (
    Resource, 
    Tool, 
    TextContent, 
    CallToolResult,
    ReadResourceResult,
    ListResourcesResult,
    ListToolsResult
)
from mcp.server.stdio import stdio_server

# Import existing business logic
from utils.menu import MENU, find_menu_item, suggest_similar_items, get_menu_by_category
from utils.mcp_helpers import create_order_id, extract_order_id_from_message

# In-memory storage (in a real implementation, this would be a database)
ORDERS = {}
USERS = {}
PENDING_CONFIRMATIONS = {}

# Create MCP server instance
server = Server("pizza-ai-server")

# --- RESOURCES ---
@server.list_resources()
async def list_resources() -> ListResourcesResult:
    """List available resources"""
    return ListResourcesResult(
        resources=[
            Resource(
                uri="memory://menu",
                name="Pizza Menu",
                description="Complete pizza menu with all available items",
                mimeType="application/json"
            ),
            Resource(
                uri="memory://orders",
                name="Order History",
                description="All pizza orders placed through the system",
                mimeType="application/json"
            ),
            Resource(
                uri="memory://users",
                name="User Database",
                description="User information and preferences",
                mimeType="application/json"
            )
        ]
    )

@server.read_resource()
async def read_resource(uri: str) -> ReadResourceResult:
    """Read resource content"""
    if uri == "memory://menu":
        return ReadResourceResult(
            contents=[
                TextContent(
                    type="text",
                    text=json.dumps({
                        "menu": MENU,
                        "categories": ["all", "veg", "non-veg"],
                        "total_items": len(MENU)
                    }, indent=2)
                )
            ]
        )
    elif uri == "memory://orders":
        return ReadResourceResult(
            contents=[
                TextContent(
                    type="text", 
                    text=json.dumps(ORDERS, indent=2, default=str)
                )
            ]
        )
    elif uri == "memory://users":
        return GetResourceResult(
            contents=[
                TextContent(
                    type="text",
                    text=json.dumps(USERS, indent=2, default=str)
                )
            ]
        )
    else:
        raise ValueError(f"Unknown resource: {uri}")

# --- TOOLS ---
@server.list_tools()
async def list_tools() -> ListToolsResult:
    """List available tools"""
    return ListToolsResult(
        tools=[
            Tool(
                name="get_menu",
                description="Get the pizza menu, optionally filtered by category",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["all", "veg", "non-veg"],
                            "description": "Filter menu by category (default: all)"
                        }
                    }
                }
            ),
            Tool(
                name="find_pizza",
                description="Find a specific pizza by name and size",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Pizza name to search for"
                        },
                        "size": {
                            "type": "string",
                            "description": "Pizza size (optional)"
                        }
                    },
                    "required": ["name"]
                }
            ),
            Tool(
                name="place_order",
                description="Place a pizza order",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pizza_name": {
                            "type": "string",
                            "description": "Name of the pizza to order"
                        },
                        "size": {
                            "type": "string",
                            "description": "Size of the pizza"
                        },
                        "customer_email": {
                            "type": "string",
                            "description": "Customer email address"
                        },
                        "customer_name": {
                            "type": "string",
                            "description": "Customer name (optional)"
                        },
                        "address": {
                            "type": "string",
                            "description": "Delivery address",
                            "default": "123 Main Street"
                        },
                        "phone": {
                            "type": "string", 
                            "description": "Customer phone number",
                            "default": "555-0123"
                        }
                    },
                    "required": ["pizza_name", "size", "customer_email"]
                }
            ),
            Tool(
                name="track_order",
                description="Track an existing order by order ID or customer email",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "Order ID to track (optional)"
                        },
                        "customer_email": {
                            "type": "string",
                            "description": "Customer email to find recent orders (optional)"
                        }
                    }
                }
            ),
            Tool(
                name="check_user",
                description="Check if a user exists and get their information",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string",
                            "description": "User email address"
                        }
                    },
                    "required": ["email"]
                }
            ),
            Tool(
                name="save_user",
                description="Save or update user information",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string",
                            "description": "User email address"
                        },
                        "name": {
                            "type": "string",
                            "description": "User full name"
                        }
                    },
                    "required": ["email", "name"]
                }
            ),
            Tool(
                name="get_suggestions",
                description="Get pizza suggestions based on preferences",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "preference": {
                            "type": "string",
                            "description": "User preference (e.g., 'vegetarian', 'spicy', 'chicken')"
                        }
                    },
                    "required": ["preference"]
                }
            )
        ]
    )

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls"""
    
    if name == "get_menu":
        category = arguments.get("category", "all")
        if category == "all":
            items = MENU
        else:
            items = get_menu_by_category(category)
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps({
                        "category": category,
                        "items": items,
                        "count": len(items)
                    }, indent=2)
                )
            ]
        )
    
    elif name == "find_pizza":
        pizza_name = arguments["name"]
        size = arguments.get("size", "")
        
        found_item = find_menu_item(pizza_name, size)
        if found_item:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "found": True,
                            "pizza": found_item
                        }, indent=2)
                    )
                ]
            )
        else:
            suggestions = suggest_similar_items(pizza_name)
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "found": False,
                            "suggestions": suggestions,
                            "message": f"Pizza '{pizza_name}' not found. Here are some suggestions:"
                        }, indent=2)
                    )
                ]
            )
    
    elif name == "place_order":
        pizza_name = arguments["pizza_name"]
        size = arguments["size"]
        customer_email = arguments["customer_email"]
        customer_name = arguments.get("customer_name", "")
        address = arguments.get("address", "123 Main Street")
        phone = arguments.get("phone", "555-0123")
        
        # Find the pizza item
        found_item = find_menu_item(pizza_name, size)
        if not found_item:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "error": f"Pizza '{pizza_name}' in size '{size}' not found",
                            "suggestions": suggest_similar_items(pizza_name)
                        }, indent=2)
                    )
                ]
            )
        
        # Create order
        order_id = create_order_id()
        order = {
            "order_id": order_id,
            "items": [found_item],
            "customer_email": customer_email,
            "customer_name": customer_name,
            "address": address,
            "phone": phone,
            "status": "placed",
            "total_price": found_item["price"],
            "timestamp": datetime.now().isoformat(),
            "eta": "25-30 minutes"
        }
        
        ORDERS[order_id] = order
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "order": order,
                        "message": f"Order placed successfully! Order ID: {order_id}"
                    }, indent=2)
                )
            ]
        )
    
    elif name == "track_order":
        order_id = arguments.get("order_id")
        customer_email = arguments.get("customer_email")
        
        if order_id and order_id in ORDERS:
            order = ORDERS[order_id]
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "found": True,
                            "order": order
                        }, indent=2)
                    )
                ]
            )
        elif customer_email:
            # Find most recent order for this email
            user_orders = [order for order in ORDERS.values() 
                          if order.get("customer_email", "").lower() == customer_email.lower()]
            
            if user_orders:
                # Sort by timestamp, get most recent
                user_orders.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                latest_order = user_orders[0]
                
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=json.dumps({
                                "found": True,
                                "order": latest_order,
                                "total_orders": len(user_orders)
                            }, indent=2)
                        )
                    ]
                )
            else:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=json.dumps({
                                "found": False,
                                "message": f"No orders found for email: {customer_email}"
                            }, indent=2)
                        )
                    ]
                )
        else:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "found": False,
                            "message": "Please provide either order_id or customer_email to track an order"
                        }, indent=2)
                    )
                ]
            )
    
    elif name == "check_user":
        email = arguments["email"]
        email_lower = email.lower().strip()
        
        if email_lower in USERS:
            user = USERS[email_lower]
            user_orders = [order for order in ORDERS.values() 
                          if order.get("customer_email", "").lower() == email_lower]
            
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "exists": True,
                            "user": user,
                            "orders_count": len(user_orders)
                        }, indent=2)
                    )
                ]
            )
        else:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "exists": False,
                            "email": email_lower
                        }, indent=2)
                    )
                ]
            )
    
    elif name == "save_user":
        email = arguments["email"]
        name = arguments["name"]
        email_lower = email.lower().strip()
        
        user = {
            "email": email_lower,
            "name": name,
            "created_at": datetime.now().isoformat()
        }
        
        USERS[email_lower] = user
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "user": user,
                        "message": "User saved successfully"
                    }, indent=2)
                )
            ]
        )
    
    elif name == "get_suggestions":
        preference = arguments["preference"].lower()
        
        if any(word in preference for word in ["veg", "vegetarian", "paneer"]):
            suggestions = get_menu_by_category("veg")[:3]
            message = "Here are our popular vegetarian pizzas:"
        elif any(word in preference for word in ["chicken", "meat", "pepperoni", "non-veg"]):
            suggestions = get_menu_by_category("non-veg")[:3]
            message = "Here are our popular non-vegetarian pizzas:"
        elif "spicy" in preference:
            suggestions = [item for item in MENU if "spicy" in item.get("description", "").lower()][:3]
            message = "Here are our spicy pizza options:"
        else:
            suggestions = MENU[:3]
            message = "Here are our most popular pizzas:"
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps({
                        "preference": preference,
                        "suggestions": suggestions,
                        "message": message
                    }, indent=2)
                )
            ]
        )
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Run the MCP server"""
    print("🍕 Starting Pizza AI MCP Server...")
    print("🔧 Protocol: Model Context Protocol (MCP)")
    print("📡 Transport: stdio")
    print("🛠️  Available tools: get_menu, find_pizza, place_order, track_order, check_user, save_user, get_suggestions")
    print("📚 Available resources: menu, orders, users")
    print("")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main()) 