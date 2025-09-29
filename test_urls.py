#!/usr/bin/env python3
"""
Quick test to check if API server responds
"""

import requests

def test_localhost():
    try:
        response = requests.get("http://localhost:9001/", timeout=2)
        if response.status_code == 200:
            print("API Server is running and responding!")
            data = response.json()
            print(f"Service: {data.get('service', 'Unknown')}")
            print(f"Status: {data.get('status', 'Unknown')}")
            return True
    except:
        pass
    
    print("API Server is not running on localhost:9001")
    print("To start it manually, run: python simple_api_server.py")
    return False

if __name__ == "__main__":
    test_localhost()