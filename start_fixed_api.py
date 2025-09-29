#!/usr/bin/env python3
"""
Start the fixed API server with proper 3D dashboard endpoints
"""

import subprocess
import sys
import time

def start_api_server():
    print("Starting Fixed NASA Space Weather API Server...")
    print("This will fix the 3D dashboard Mission Time and Data Connection issues")
    
    # Kill any existing Python processes on port 8004
    try:
        subprocess.run("taskkill /F /IM python.exe", shell=True, capture_output=True)
        time.sleep(2)
    except:
        pass
    
    # Start the simple API server
    try:
        subprocess.Popen([sys.executable, "simple_api_server.py"])
        print("API Server started on http://localhost:8004")
        print("\nEndpoints available:")
        print("- /api/v1/visualization/3d")
        print("- /api/v1/visualization/solar-system")
        print("- /api/v1/forecasts/advanced")
        print("- /api/v1/system/status")
        print("\nWait 3 seconds, then refresh your 3D dashboard...")
        
        time.sleep(3)
        
        # Test endpoints
        import requests
        try:
            response = requests.get("http://localhost:8004/api/v1/visualization/3d", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"\n✓ 3D endpoint working - Mission Time: {data['data']['mission_time']}")
                print(f"✓ Connection Status: {data['data']['data_connection']}")
            else:
                print(f"\n✗ 3D endpoint failed - Status: {response.status_code}")
        except Exception as e:
            print(f"\n✗ API test failed: {e}")
            
    except Exception as e:
        print(f"Failed to start server: {e}")

if __name__ == "__main__":
    start_api_server()