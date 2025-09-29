#!/usr/bin/env python3
"""
Test the simple API server directly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.simple_api import app
import uvicorn

if __name__ == "__main__":
    print("Testing Simple NASA Space Weather API...")
    print("API will be available at: http://localhost:8001")
    print("Health check: http://localhost:8001/api/v1/health")
    print("Current forecast: http://localhost:8001/api/v1/forecasts/current")
    print("\nPress Ctrl+C to stop the server")
    
    # Start without websockets and reload to avoid dependency issues
    try:
        uvicorn.run(
            app,
            host="127.0.0.1", 
            port=8001,  # Use different port
            log_level="info",
            ws="none"  # Disable websockets
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        # Try alternative method
        print("Trying alternative startup method...")
        import asyncio
        from uvicorn import Config, Server
        
        config = Config(app, host="127.0.0.1", port=8000, log_level="info")
        server = Server(config)
        asyncio.run(server.serve())