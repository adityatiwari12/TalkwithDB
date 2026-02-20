"""
Talk with DB - Version 3
Main entry point for the advanced chatbot system.

Usage:
    python chat_v3.py              # Start both API and UI
    python chat_v3.py --api-only   # Start only FastAPI backend
    python chat_v3.py --ui-only    # Start only Streamlit UI
"""

import argparse
import subprocess
import sys
import os
import time
import webbrowser
from threading import Thread

def start_api():
    """Start FastAPI backend."""
    print("🚀 Starting FastAPI Backend...")
    
    # Change to src/chat_sql directory
    api_path = os.path.join(os.path.dirname(__file__), "src", "chat_sql", "api", "v3_api.py")
    
    # Start API using uvicorn
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "src.chat_sql.api.v3_api:app",
        "--host", "0.0.0.0",
        "--port", "8001",
        "--reload"
    ], cwd=os.path.dirname(__file__))
    
    return process

def start_ui():
    """Start Streamlit UI."""
    print("🎨 Starting Streamlit UI...")
    
    ui_path = os.path.join(os.path.dirname(__file__), "chat_ui.py")
    
    # Start Streamlit
    process = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run",
        ui_path,
        "--server.port", "8502",
        "--server.headless", "false"
    ], cwd=os.path.dirname(__file__))
    
    return process

def main():
    parser = argparse.ArgumentParser(description="Talk with DB - Version 3")
    parser.add_argument("--api-only", action="store_true", help="Start only API")
    parser.add_argument("--ui-only", action="store_true", help="Start only UI")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    
    args = parser.parse_args()
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║           🤖 Talk with DB - Version 3                     ║
    ║                                                           ║
    ║     Advanced Chat with SQL - Enterprise Ready             ║
    ║                                                           ║
    ║   Features:                                               ║
    ║   ✅ Query Rewriting & Expansion                         ║
    ║   ✅ Hybrid Search (BM25 + Vector)                       ║
    ║   ✅ LLM Re-ranking                                      ║
    ║   ✅ Conversation Memory                                 ║
    ║   ✅ Real-time WebSocket Chat                            ║
    ║   ✅ Schema Exploration                                  ║
    ║   ✅ Query Analytics                                     ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    api_process = None
    ui_process = None
    
    try:
        if args.api_only:
            api_process = start_api()
            print("\n📡 API running at: http://localhost:8000")
            print("📚 API Docs: http://localhost:8000/docs")
            api_process.wait()
            
        elif args.ui_only:
            ui_process = start_ui()
            print("\n🌐 UI running at: http://localhost:8502")
            if not args.no_browser:
                time.sleep(3)
                webbrowser.open("http://localhost:8502")
            ui_process.wait()
            
        else:
            # Start both
            api_process = start_api()
            print("\n📡 API starting at: http://localhost:8000")
            
            # Wait for API to start
            time.sleep(3)
            
            ui_process = start_ui()
            print("🌐 UI starting at: http://localhost:8502")
            
            if not args.no_browser:
                time.sleep(3)
                webbrowser.open("http://localhost:8502")
            
            print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║  🎉 Version 3 is now running!                           ║
    ║                                                           ║
    ║  📡 API: http://localhost:8001                         ║
    ║  📚 Docs: http://localhost:8001/docs                     ║
    ║  🌐 UI:  http://localhost:8502                           ║
    ║                                                           ║
    ║  Press Ctrl+C to stop                                     ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
            """)
            
            # Wait for both processes
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        
        if api_process:
            api_process.terminate()
            print("✅ API stopped")
            
        if ui_process:
            ui_process.terminate()
            print("✅ UI stopped")
            
        print("👋 Goodbye!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
