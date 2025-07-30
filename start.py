#!/usr/bin/env python3
"""
Pizza AI Quick Start Script
Simplified launcher for the clean architecture system
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Quick start the Pizza AI system"""
    print("🍕 Pizza AI - Quick Start")
    print("=" * 30)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Error: main.py not found. Please run from project root directory.")
        return
    
    # Check for .env file
    if not Path(".env").exists():
        print("⚠️  .env file not found!")
        print("📝 Please create a .env file with your Groq API key:")
        print("   echo 'GROQ_API_KEY=your_api_key_here' > .env")
        print("")
        choice = input("Continue anyway? (y/N): ").strip().lower()
        if choice != 'y':
            return
    
    print("🚀 Starting Pizza AI system...")
    print("📡 MCP Server will start on port 8002")
    print("🌐 FastAPI Client will start on port 8001")
    print("")
    print("Press Ctrl+C to stop")
    print("")
    
    try:
        # Run the main script with both servers
        subprocess.run([sys.executable, "main.py", "both"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Pizza AI stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Try running: python main.py info")

if __name__ == "__main__":
    main() 