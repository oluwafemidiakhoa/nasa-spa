#!/usr/bin/env python3
"""
Test the ensemble API to verify it's working
"""

import requests
import json
import time

def test_api():
    """Test the robust ensemble API"""
    
    print("Testing NASA Space Weather Ensemble API")
    print("=" * 50)
    
    base_url = "http://localhost:8002"
    
    # Test 1: Root endpoint
    print("1. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Service: {data.get('service', 'Unknown')}")
            print(f"   ✓ Status: {data.get('status', 'Unknown')}")
            print(f"   ✓ Ensemble: {data.get('ai_providers', {}).get('ensemble_forecasting', False)}")
        else:
            print(f"   ✗ HTTP {response.status_code}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    # Test 2: System status
    print("\n2. Testing system status...")
    try:
        response = requests.get(f"{base_url}/api/v1/system/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                components = data['data']['forecasting_components']
                print(f"   ✓ Ensemble: {components.get('ensemble_forecasting', False)}")
                print(f"   ✓ Physics: {components.get('physics_models', False)}")
                print(f"   ✓ Neural Networks: {components.get('neural_networks', False)}")
                print(f"   ✓ Historical DB: {components.get('historical_database', False)}")
            else:
                print(f"   ✗ API Error: {data.get('error', 'Unknown')}")
        else:
            print(f"   ✗ HTTP {response.status_code}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    # Test 3: Simple forecast
    print("\n3. Testing simple forecast...")
    try:
        response = requests.get(f"{base_url}/api/v1/forecasts/simple", timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                forecast_data = data['data']
                forecasts = forecast_data.get('forecasts', [])
                print(f"   ✓ Forecasts: {len(forecasts)} events")
                print(f"   ✓ Model: {forecast_data.get('model_type', 'Unknown')}")
                print(f"   ✓ Generated: {forecast_data.get('generated_at', 'Unknown')}")
            else:
                print(f"   ✗ API Error: {data.get('error', 'Unknown')}")
        else:
            print(f"   ✗ HTTP {response.status_code}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    # Test 4: Advanced forecast (dashboard format)
    print("\n4. Testing advanced forecast...")
    try:
        response = requests.get(f"{base_url}/api/v1/forecasts/advanced", timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                forecast = data['data']['forecast']
                print(f"   ✓ Title: {forecast.get('title', 'Unknown')}")
                print(f"   ✓ AI Model: {forecast.get('ai_model', 'Unknown')}")
                print(f"   ✓ Methodology: {forecast.get('methodology', 'Unknown')}")
                print(f"   ✓ Risk Level: {forecast.get('risk_level', 'Unknown')}")
                print(f"   ✓ Confidence: {forecast.get('confidence_score', 0):.1%}")
            else:
                print(f"   ✗ API Error: {data.get('error', 'Unknown')}")
        else:
            print(f"   ✗ HTTP {response.status_code}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    print("\n" + "=" * 50)
    print("API Test Complete")
    print("Ready for dashboard integration!")

if __name__ == "__main__":
    test_api()