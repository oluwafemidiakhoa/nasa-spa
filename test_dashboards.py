#!/usr/bin/env python3
"""
Test script to verify all dashboard APIs work correctly
"""

import requests
import json
import time

def test_api_endpoint(url, description):
    """Test a single API endpoint"""
    try:
        print(f"Testing {description}...")
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"  [OK] {description} - SUCCESS")
            return True
        else:
            print(f"  [FAIL] {description} - HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] {description} - Error: {e}")
        return False

def main():
    print("="*60)
    print("NASA SPACE WEATHER DASHBOARD TESTING")
    print("="*60)
    
    base_url = "http://localhost:9001"
    
    # Test all endpoints
    endpoints = [
        (f"{base_url}/", "API Server Root"),
        (f"{base_url}/api/v1/system/status", "System Status"),
        (f"{base_url}/api/v1/forecasts/simple", "Simple Forecast"),
        (f"{base_url}/api/v1/forecasts/advanced", "Advanced Forecast"),
        (f"{base_url}/api/v1/visualization/3d", "3D Visualization Data"),
        (f"{base_url}/api/v1/visualization/solar-system", "Solar System Data")
    ]
    
    print("\nTesting API Endpoints:")
    print("-" * 40)
    
    success_count = 0
    total_count = len(endpoints)
    
    for url, description in endpoints:
        if test_api_endpoint(url, description):
            success_count += 1
        time.sleep(0.5)  # Small delay between requests
    
    print("-" * 40)
    print(f"API Tests: {success_count}/{total_count} passed")
    
    if success_count == total_count:
        print("\nAll APIs working correctly!")
        print("\nDashboard URLs:")
        print("  • Main Hub: dashboard_hub.html")
        print("  • Simple: simple.html")
        print("  • Ensemble: simple_new.html")
        print("  • Professional: professional_dashboard.html")
        print("  • Expert: expert_dashboard.html")
        print("  • 3D Dashboard: 3d_dashboard.html")
        print("  • 3D Solar System: 3d_solar_system.html")
        
        print("\nSetup Instructions:")
        print("  1. Start API server: python simple_api_server.py")
        print("  2. Open any dashboard HTML file in your browser")
        print("  3. All dashboards should now work correctly!")
        
    else:
        print(f"\nWARNING: {total_count - success_count} API(s) failed")
        print("Make sure the API server is running:")
        print("  python simple_api_server.py")
    
    print("="*60)

if __name__ == "__main__":
    main()