#!/usr/bin/env python3
"""
Test simple API parsing to verify the fixes
"""

import requests
import json

def test_simple_forecast():
    """Test the simple forecast endpoint and data structure"""
    print("Testing Simple Forecast API...")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8001/api/v1/forecasts/simple", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            
            if data.get('success') and data.get('data'):
                forecast_data = data['data']
                forecasts = forecast_data.get('forecasts', [])
                
                print(f"\nData Structure Analysis:")
                print(f"- Number of forecasts: {len(forecasts)}")
                print(f"- Generated at: {forecast_data.get('generated_at')}")
                print(f"- Data sources: {forecast_data.get('data_sources')}")
                
                if forecasts:
                    print(f"\nFirst Forecast:")
                    first = forecasts[0]
                    print(f"- Event: {first.get('event')}")
                    print(f"- Confidence: {first.get('confidence')} ({first.get('confidence') * 100:.0f}%)")
                    print(f"- Risk Summary: {first.get('risk_summary')[:100]}...")
                    print(f"- Impacts: {first.get('impacts')}")
                    
                    # Calculate average confidence
                    avg_confidence = sum(f.get('confidence', 0) for f in forecasts) / len(forecasts)
                    print(f"\nAverage Confidence: {avg_confidence:.2f} ({avg_confidence * 100:.0f}%)")
                
                print(f"\n✅ Simple dashboard should now show:")
                print(f"- Title: Space Weather Forecast - {len(forecasts)} Event(s) Analyzed")
                print(f"- Confidence: {avg_confidence * 100:.0f}%")
                print(f"- Generated: {forecast_data.get('generated_at')}")
                print(f"- Source: {', '.join(forecast_data.get('data_sources', ['NASA']))}")
                
            else:
                print("❌ No data in response")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_simple_forecast()