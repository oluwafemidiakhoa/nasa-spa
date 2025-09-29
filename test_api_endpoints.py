#!/usr/bin/env python3
"""
Quick test of all API endpoints that dashboards are calling
"""

import requests
import json

def test_endpoint(url, description):
    """Test a single endpoint"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ {description}: OK")
            return True
        else:
            print(f"✗ {description}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ {description}: {e}")
        return False

def main():
    print("Testing API endpoints that dashboards are calling...")
    print("=" * 60)
    
    base_url = "http://localhost:9001"
    
    # Test endpoints that dashboards are calling
    endpoints = [
        (f"{base_url}/", "Root endpoint"),
        (f"{base_url}/api/v1/forecasts/simple", "Simple forecast (simple.html)"),
        (f"{base_url}/api/v1/forecasts/advanced", "Advanced forecast (professional_dashboard.html)"),
        (f"{base_url}/api/v1/visualization/3d", "3D data (3d_dashboard.html)"),
        (f"{base_url}/api/v1/visualization/solar-system", "Solar system data"),
        (f"{base_url}/api/v1/system/status", "System status"),
    ]
    
    results = []
    for url, desc in endpoints:
        results.append(test_endpoint(url, desc))
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} endpoints working")
    
    if all(results):
        print("✓ All API endpoints are working!")
        print("\nIf dashboards aren't working, the problem is:")
        print("1. Browser cache - try Ctrl+F5 hard refresh")
        print("2. JavaScript errors - check browser console")
        print("3. CORS issues - check browser network tab")
    else:
        print("✗ Some API endpoints are broken")
    
    return all(results)

if __name__ == "__main__":
    main()