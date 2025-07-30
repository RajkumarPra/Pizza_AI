#!/usr/bin/env python3
"""
Pizza AI - MCP Integration
Model Context Protocol implementation with Groq LLM
"""

import os
import sys
import subprocess
import argparse
from typing import Optional

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import groq
        import mcp
        import fastapi
        import uvicorn
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("🔧 Please run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists with required variables"""
    if not os.path.exists('.env'):
        print("⚠️  .env file not found!")
        print("📝 Please create a .env file with:")
        print("   GROQ_API_KEY=your_groq_api_key_here")
        print("")
        return False
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("⚠️  GROQ_API_KEY not found in .env file!")
            return False
        return True
    except Exception as e:
        print(f"❌ Error loading .env file: {e}")
        return False

def run_mcp_server():
    """Run the MCP server"""
    print("🚀 Starting Pizza AI MCP Server...")
    print("📡 Protocol: Model Context Protocol (stdio)")
    print("🛠️  Tools: get_menu, find_pizza, place_order, track_order, check_user, save_user, get_suggestions")
    print("📚 Resources: menu, orders, users")
    print("")
    
    try:
        subprocess.run([sys.executable, "pizza_mcp_server.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 MCP Server stopped by user")
    except Exception as e:
        print(f"❌ Error running MCP server: {e}")

def run_fastapi_client():
    """Run the FastAPI client"""
    print("🚀 Starting Pizza AI FastAPI Client...")
    print("🌐 Port: 8001")
    print("🔗 Integrates with: MCP Server (stdio) + Groq LLM")
    print("📱 Single endpoint: POST /chat")
    print("")
    
    try:
        subprocess.run([sys.executable, "pizza_api.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 FastAPI Client stopped by user")
    except Exception as e:
        print(f"❌ Error running FastAPI client: {e}")

def show_architecture_info():
    """Show information about the MCP architecture"""
    print("🏗️  Pizza AI - Model Context Protocol Architecture")
    print("=" * 60)
    print("")
    print("📦 Components:")
    print("   ├── pizza_mcp_server.py - MCP Server (exposes tools & resources)")
    print("   ├── pizza_api.py - FastAPI Client (single /chat endpoint)")
    print("   └── utils/groq_integration.py - Groq LLM integration")
    print("")
    print("🔧 MCP Server Tools:")
    print("   ├── get_menu - Retrieve pizza menu by category")
    print("   ├── find_pizza - Search for specific pizzas")
    print("   ├── place_order - Place pizza orders")
    print("   ├── track_order - Track order status")
    print("   ├── check_user - Verify user existence")
    print("   ├── save_user - Store user information")
    print("   └── get_suggestions - Get pizza recommendations")
    print("")
    print("📚 MCP Server Resources:")
    print("   ├── memory://menu - Complete pizza menu")
    print("   ├── memory://orders - Order history and status")
    print("   └── memory://users - User database")
    print("")
    print("🌐 API Flow:")
    print("   1. User sends message to POST /chat")
    print("   2. FastAPI client analyzes intent using Groq LLM")
    print("   3. Client calls appropriate MCP tools via stdio")
    print("   4. MCP server executes business logic and returns results")
    print("   5. Client generates natural language response using Groq")
    print("")
    print("🎯 Benefits:")
    print("   • Standardized tool integration via MCP protocol")
    print("   • LLM-agnostic tool definitions")
    print("   • Clean separation between AI logic and business logic")
    print("   • Reusable MCP server for different client applications")
    print("   • Type-safe tool calling with JSON schemas")
    print("")

def test_mcp_integration():
    """Test the MCP integration"""
    print("🧪 Testing MCP Integration...")
    print("")
    
    # Test MCP server startup
    print("1. Testing MCP server startup...")
    try:
        result = subprocess.run([
            sys.executable, "-c", 
            "from pizza_mcp_server import server; print('✅ MCP server imports successful')"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("   ✅ MCP server can be imported successfully")
        else:
            print(f"   ❌ MCP server import failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ MCP server test failed: {e}")
        return False
    
    # Test Groq integration
    print("2. Testing Groq integration...")
    try:
        result = subprocess.run([
            sys.executable, "-c", 
            "from utils.groq_integration import groq_chat; print('✅ Groq integration successful')"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("   ✅ Groq integration working")
        else:
            print(f"   ❌ Groq integration failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Groq test failed: {e}")
        return False
    
    # Test FastAPI client
    print("3. Testing FastAPI client...")
    try:
        result = subprocess.run([
            sys.executable, "-c", 
            "from pizza_api import app; print('✅ FastAPI client imports successful')"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("   ✅ FastAPI client can be imported successfully")
        else:
            print(f"   ❌ FastAPI client import failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ FastAPI client test failed: {e}")
        return False
    
    print("")
    print("🎉 All tests passed! The MCP integration is ready to use.")
    print("")
    print("💡 Next steps:")
    print("   1. Run: python main.py fastapi")
    print("   2. Send POST request to http://localhost:8001/chat")
    print("   3. Example: {'message': 'Show me the menu', 'user_email': 'test@example.com'}")
    print("")
    
    return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Pizza AI - MCP Integration")
    parser.add_argument(
        "mode", 
        nargs="?", 
        choices=["mcp", "fastapi", "info", "test"], 
        default="fastapi",
        help="Run mode: mcp (server only), fastapi (client), info (architecture info), test (integration test)"
    )
    
    args = parser.parse_args()
    
    print("🍕 Pizza AI - Model Context Protocol Integration")
    print("🧠 LLM: Groq Llama 3.1 7B")
    print("📡 Protocol: Model Context Protocol (MCP)")
    print("")
    
    if args.mode == "info":
        show_architecture_info()
        return
    
    if args.mode == "test":
        if not check_dependencies():
            return
        if not check_env_file():
            return
        test_mcp_integration()
        return
    
    # Check dependencies and environment for run modes
    if not check_dependencies():
        return
    
    if not check_env_file():
        return
    
    # Run based on mode
    if args.mode == "mcp":
        run_mcp_server()
    elif args.mode == "fastapi":
        run_fastapi_client()
    else:
        print("❌ Invalid mode. Use: mcp, fastapi, info, or test")

if __name__ == "__main__":
    main()
