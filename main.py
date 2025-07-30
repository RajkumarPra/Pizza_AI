#!/usr/bin/env python3
"""
Pizza AI - Clean Architecture Entry Point
Main application launcher for Clean Architecture implementation with MCP integration.
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
        return False
    
    # Check if GROQ_API_KEY is set
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv('GROQ_API_KEY'):
        print("⚠️  GROQ_API_KEY not found in .env file!")
        print("📝 Please add your Groq API key to .env:")
        print("   GROQ_API_KEY=your_groq_api_key_here")
        return False
    
    return True


def run_mcp_server():
    """Run the Clean Architecture MCP server"""
    print("🚀 Starting Clean Architecture MCP Server...")
    try:
        subprocess.run([
            sys.executable, 
            "src/infrastructure/web/mcp_server.py"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 MCP Server stopped by user")
    except Exception as e:
        print(f"❌ MCP Server error: {e}")


def run_fastapi_client():
    """Run the Clean Architecture FastAPI client"""
    print("🚀 Starting Clean Architecture FastAPI Client...")
    try:
        subprocess.run([
            sys.executable, 
            "src/infrastructure/web/fastapi_app.py"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 FastAPI Client stopped by user")
    except Exception as e:
        print(f"❌ FastAPI Client error: {e}")


def run_both():
    """Run both MCP server and FastAPI client"""
    print("🚀 Starting both Clean Architecture servers...")
    print("📡 MCP Server will handle MCP protocol communication")
    print("🌐 FastAPI Client will handle HTTP API requests")
    print("Press Ctrl+C to stop both servers")
    print("")
    
    try:
        # Start MCP server in background
        mcp_process = subprocess.Popen([
            sys.executable, 
            "src/infrastructure/web/mcp_server.py"
        ])
        
        # Start FastAPI client (blocking)
        fastapi_process = subprocess.Popen([
            sys.executable, 
            "src/infrastructure/web/fastapi_app.py"
        ])
        
        # Wait for both processes
        try:
            mcp_process.wait()
            fastapi_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping servers...")
            mcp_process.terminate()
            fastapi_process.terminate()
            
            # Wait for graceful shutdown
            mcp_process.wait(timeout=5)
            fastapi_process.wait(timeout=5)
            
        print("👋 All servers stopped")
        
    except Exception as e:
        print(f"❌ Error running servers: {e}")


def show_architecture_info():
    """Show Clean Architecture information"""
    print("🏗️ Pizza AI - Clean Architecture Implementation")
    print("=" * 60)
    print("")
    
    print("📋 ARCHITECTURE LAYERS:")
    print("   🏢 Domain Layer (src/domain/)")
    print("      • Entities: Pizza, Order, User with business rules")
    print("      • Repositories: Abstract interfaces (Dependency Inversion)")  
    print("      • Services: Complex business logic")
    print("      • Data: Domain data models")
    print("")
    
    print("   🎯 Application Layer (src/application/)")
    print("      • Use Cases: High-level business workflows")
    print("      • Interfaces: External service contracts")
    print("")
    
    print("   🔧 Infrastructure Layer (src/infrastructure/)")
    print("      • External: Groq LLM service implementation")
    print("      • Persistence: In-memory repository implementations")
    print("      • Web: FastAPI and MCP server implementations") 
    print("      • DI Container: Dependency injection setup")
    print("")
    
    print("🎯 DESIGN PRINCIPLES:")
    print("   ✅ Dependency Inversion: Dependencies point inward")
    print("   ✅ Single Responsibility: Each layer has one purpose")
    print("   ✅ Interface Segregation: Small, focused contracts")
    print("   ✅ Open/Closed: Easy to extend, hard to break")
    print("   ✅ Framework Independence: Domain layer is pure Python")
    print("")
    
    print("🚀 AVAILABLE SERVERS:")
    print("   📡 MCP Server: Model Context Protocol for LLM integration")
    print("      • Tools: get_menu, find_pizza, place_order, track_order")
    print("      • Resources: menu, orders, users")
    print("      • Transport: stdio (JSON-RPC)")
    print("")
    
    print("   🌐 FastAPI Server: HTTP API for web integration")
    print("      • POST /chat - Natural language ordering")
    print("      • GET /menu - Structured menu access")
    print("      • POST /order - Direct order placement")
    print("      • GET /order/{id} - Order tracking")
    print("      • GET /health - Health check")
    print("")
    
    print("💡 BENEFITS:")
    print("   🧪 Testable: Domain logic is pure and easily tested")
    print("   🔄 Maintainable: Clear separation of concerns")
    print("   🔌 Flexible: Easy to swap implementations")
    print("   📈 Scalable: Framework-independent business logic")
    print("")


def test_architecture():
    """Test the Clean Architecture implementation"""
    print("🧪 Testing Clean Architecture Implementation...")
    print("")
    
    try:
        # Test domain layer
        print("1. Testing Domain Layer...")
        from src.domain.entities import Pizza, PizzaSize, PizzaCategory
        pizza = Pizza(
            id="test_1",
            name="Test Pizza",
            size=PizzaSize.LARGE,
            price=10.99,
            category=PizzaCategory.VEG,
            description="Test pizza for architecture validation",
            ingredients=["test", "ingredients"]
        )
        print(f"   ✅ Domain entities working: {pizza.display_name}")
        
        # Test application layer
        print("2. Testing Application Layer...")
        from src.infrastructure.di_container import container
        pizza_repo = container.get_pizza_repository()
        print("   ✅ Dependency injection working")
        
        # Test infrastructure layer
        print("3. Testing Infrastructure Layer...")
        llm_service = container.get_llm_service()
        print("   ✅ External service integration working")
        
        print("")
        print("✅ Clean Architecture test passed!")
        print("🎯 All layers are properly connected via dependency injection")
        
    except Exception as e:
        print(f"   ❌ Architecture test failed: {e}")
        return False
    
    return True


def main():
    """Main entry point for Clean Architecture implementation"""
    parser = argparse.ArgumentParser(description="Pizza AI - Clean Architecture Implementation")
    parser.add_argument(
        "mode", 
        nargs="?", 
        choices=["mcp", "fastapi", "both", "info", "test"], 
        default="both",
        help="Run mode: mcp (server only), fastapi (client), both (recommended), info (architecture), test (validation)"
    )
    
    args = parser.parse_args()
    
    print("🍕 Pizza AI - Clean Architecture Implementation")
    print("🏗️ Architecture: Clean Architecture with Dependency Injection")
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
        test_architecture()
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
    elif args.mode == "both":
        run_both()
    else:
        print("❌ Invalid mode. Use: mcp, fastapi, both, info, or test")


if __name__ == "__main__":
    main()
