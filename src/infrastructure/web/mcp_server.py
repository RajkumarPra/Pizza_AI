#!/usr/bin/env python3
"""
Infrastructure - MCP Server
Clean architecture implementation of Model Context Protocol server.
"""

import asyncio
import json
import sys
import os
from typing import Any, Dict, List, Optional

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

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

from ..di_container import container
from ...application.use_cases.order_use_cases import OrderRequest
from ...domain.entities import PizzaCategory


# Create MCP server instance
server = Server("pizza-ai-clean-architecture")


# --- RESOURCES ---
@server.list_resources()
async def list_resources() -> ListResourcesResult:
    """List available resources"""
    return ListResourcesResult(
        resources=[
            Resource(
                uri="memory://menu",
                name="Pizza Menu",
                description="Complete pizza menu with all available items using domain entities",
                mimeType="application/json"
            ),
            Resource(
                uri="memory://orders",
                name="Order History", 
                description="All pizza orders placed through the clean architecture system",
                mimeType="application/json"
            ),
            Resource(
                uri="memory://users",
                name="User Database",
                description="User information managed by domain entities",
                mimeType="application/json"
            )
        ]
    )


@server.read_resource()
async def read_resource(uri: str) -> ReadResourceResult:
    """Read resource content using clean architecture"""
    
    if uri == "memory://menu":
        # Get menu from clean architecture
        pizza_repo = container.get_pizza_repository()
        pizzas = await pizza_repo.get_available_pizzas()
        
        menu_data = []
        for pizza in pizzas:
            menu_data.append({
                "id": pizza.id,
                "name": pizza.display_name,
                "price": pizza.formatted_price,
                "category": pizza.category.value,
                "description": pizza.description,
                "ingredients": pizza.ingredients,
                "available": pizza.is_available
            })
        
        return ReadResourceResult(
            contents=[
                TextContent(
                    type="text",
                    text=json.dumps({
                        "menu": menu_data,
                        "categories": ["all", "veg", "non-veg"],
                        "total_items": len(menu_data),
                        "architecture": "Clean Architecture with Domain Entities"
                    }, indent=2)
                )
            ]
        )
    
    elif uri == "memory://orders":
        # Get orders from clean architecture
        order_repo = container.get_order_repository()
        orders = await order_repo.get_recent_orders(50)  # Last 50 orders
        
        orders_data = []
        for order in orders:
            orders_data.append({
                "order_id": order.id,
                "customer_email": order.customer.email,
                "customer_name": order.customer.name,
                "status": order.status.value,
                "total_amount": order.formatted_total,
                "items_count": order.total_items,
                "created_at": order.created_at.isoformat(),
                "estimated_eta": order.estimated_eta
            })
        
        return ReadResourceResult(
            contents=[
                TextContent(
                    type="text",
                    text=json.dumps({
                        "orders": orders_data,
                        "total_orders": len(orders_data),
                        "architecture": "Clean Architecture with Domain Aggregates"
                    }, indent=2)
                )
            ]
        )
    
    elif uri == "memory://users":
        # Get users from clean architecture
        user_repo = container.get_user_repository()
        users = await user_repo.get_all_active()
        
        users_data = []
        for user in users:
            users_data.append({
                "id": user.id,
                "email": user.email,
                "name": user.display_name,
                "total_orders": user.total_orders,
                "is_frequent_customer": user.is_frequent_customer,
                "created_at": user.created_at.isoformat()
            })
        
        return ReadResourceResult(
            contents=[
                TextContent(
                    type="text",
                    text=json.dumps({
                        "users": users_data,
                        "total_users": len(users_data),
                        "architecture": "Clean Architecture with Domain Entities"
                    }, indent=2)
                )
            ]
        )
    
    else:
        raise ValueError(f"Unknown resource: {uri}")


# --- TOOLS ---
@server.list_tools()
async def list_tools() -> ListToolsResult:
    """List available tools using clean architecture"""
    return ListToolsResult(
        tools=[
            Tool(
                name="get_menu",
                description="Get the pizza menu using clean architecture, optionally filtered by category",
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
                description="Find a specific pizza using domain entities and search capabilities",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Pizza name to search for"
                        },
                        "size": {
                            "type": "string",
                            "description": "Pizza size preference (optional)"
                        }
                    },
                    "required": ["name"]
                }
            ),
            Tool(
                name="place_order",
                description="Place a pizza order using clean architecture use cases",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "customer_name": {
                            "type": "string",
                            "description": "Customer full name"
                        },
                        "customer_email": {
                            "type": "string",
                            "description": "Customer email address"
                        },
                        "customer_phone": {
                            "type": "string",
                            "description": "Customer phone number",
                            "default": "555-0123"
                        },
                        "customer_address": {
                            "type": "string",
                            "description": "Delivery address",
                            "default": "123 Main Street"
                        },
                        "items": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of pizza names to order"
                        }
                    },
                    "required": ["customer_name", "customer_email", "items"]
                }
            ),
            Tool(
                name="track_order",
                description="Track an existing order using clean architecture",
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
                description="Check if a user exists using domain entities",
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
                description="Save or update user information using clean architecture",
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
                description="Get pizza suggestions using domain logic and customer preferences",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "customer_email": {
                            "type": "string",
                            "description": "Customer email for personalized suggestions (optional)"
                        },
                        "preferences": {
                            "type": "string",
                            "description": "User preferences (e.g., 'vegetarian', 'spicy', 'popular')",
                            "default": "popular"
                        }
                    }
                }
            )
        ]
    )


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls using clean architecture use cases"""
    
    try:
        if name == "get_menu":
            order_use_cases = container.get_order_use_cases()
            category = arguments.get("category", "all")
            result = await order_use_cases.get_menu(category)
            
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": result["success"],
                            "category": result["category"],
                            "items": result["items"],
                            "total_items": result["total_items"],
                            "architecture": "Clean Architecture - Application Use Cases"
                        }, indent=2)
                    )
                ]
            )
        
        elif name == "find_pizza":
            order_use_cases = container.get_order_use_cases()
            pizza_name = arguments["name"]
            size = arguments.get("size", "large")
            
            result = await order_use_cases.find_pizza(pizza_name, size)
            
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": result["success"],
                            "pizza": result.get("pizza"),
                            "error": result.get("error"),
                            "architecture": "Clean Architecture - Domain Entity Search"
                        }, indent=2)
                    )
                ]
            )
        
        elif name == "place_order":
            order_use_cases = container.get_order_use_cases()
            
            # Create order request using clean architecture models
            order_request = OrderRequest(
                customer_name=arguments["customer_name"],
                customer_email=arguments["customer_email"],
                customer_phone=arguments.get("customer_phone", "555-0123"),
                customer_address=arguments.get("customer_address", "123 Main Street"),
                items=arguments["items"]
            )
            
            result = await order_use_cases.place_order(order_request)
            
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": result.success,
                            "order_id": result.order_id,
                            "message": result.message,
                            "order_details": result.order_details,
                            "error": result.error,
                            "architecture": "Clean Architecture - Domain Aggregates & Use Cases"
                        }, indent=2)
                    )
                ]
            )
        
        elif name == "track_order":
            order_use_cases = container.get_order_use_cases()
            order_id = arguments.get("order_id")
            customer_email = arguments.get("customer_email")
            
            result = await order_use_cases.track_order(order_id, customer_email)
            
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": result.success,
                            "order_id": result.order_id,
                            "message": result.message,
                            "order_details": result.order_details,
                            "error": result.error,
                            "architecture": "Clean Architecture - Order Aggregate"
                        }, indent=2)
                    )
                ]
            )
        
        elif name == "check_user":
            user_repo = container.get_user_repository()
            email = arguments["email"]
            
            user = await user_repo.get_by_email(email)
            order_count = await user_repo.get_customer_order_count(email) if user else 0
            
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "exists": user is not None,
                            "user": {
                                "email": user.email,
                                "name": user.display_name,
                                "total_orders": user.total_orders,
                                "is_frequent_customer": user.is_frequent_customer
                            } if user else None,
                            "orders_count": order_count,
                            "architecture": "Clean Architecture - User Entity"
                        }, indent=2)
                    )
                ]
            )
        
        elif name == "save_user":
            user_repo = container.get_user_repository()
            email = arguments["email"]
            name = arguments["name"]
            
            # Check if user exists
            existing_user = await user_repo.get_by_email(email)
            
            if existing_user:
                # Update existing user
                existing_user.update_profile(name=name)
                saved_user = await user_repo.save(existing_user)
            else:
                # Create new user using domain entity
                from ...domain.entities import User
                new_user = User(email=email, name=name)
                saved_user = await user_repo.save(new_user)
            
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "user": {
                                "email": saved_user.email,
                                "name": saved_user.display_name,
                                "is_new_customer": saved_user.is_new_customer
                            },
                            "message": "User saved successfully using domain entity",
                            "architecture": "Clean Architecture - User Entity & Repository"
                        }, indent=2)
                    )
                ]
            )
        
        elif name == "get_suggestions":
            order_use_cases = container.get_order_use_cases()
            customer_email = arguments.get("customer_email")
            preferences = arguments.get("preferences", "popular")
            
            result = await order_use_cases.get_suggestions(customer_email, preferences)
            
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": result["success"],
                            "message": result["message"],
                            "suggestions": result["suggestions"],
                            "preferences": preferences,
                            "architecture": "Clean Architecture - Domain Service Logic"
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
                            "error": f"Unknown tool: {name}",
                            "available_tools": [
                                "get_menu", "find_pizza", "place_order", 
                                "track_order", "check_user", "save_user", "get_suggestions"
                            ]
                        }, indent=2)
                    )
                ]
            )
    
    except Exception as e:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Tool execution failed: {str(e)}",
                        "tool": name,
                        "architecture": "Clean Architecture - Error Handling"
                    }, indent=2)
                )
            ]
        )


async def main():
    """Run the MCP server using clean architecture"""
    print("🍕 Starting Pizza AI Clean Architecture MCP Server...")
    print("🏗️ Architecture: Clean Architecture with Dependency Injection")
    print("🔧 Protocol: Model Context Protocol (MCP)")
    print("📡 Transport: stdio")
    print("🛠️  Tools: get_menu, find_pizza, place_order, track_order, check_user, save_user, get_suggestions")
    print("📚 Resources: menu (domain entities), orders (aggregates), users (entities)")
    print("🧠 LLM Integration: Groq Llama 3.1 7B via application layer")
    print("🎯 Benefits: Testable, Maintainable, Framework-Independent")
    print("")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main()) 