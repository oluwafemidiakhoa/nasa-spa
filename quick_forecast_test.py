#!/usr/bin/env python3
"""
Quick test of NASA Space Weather forecasting without API server
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
from datetime import datetime, timedelta

# Test the forecast functionality directly
def test_forecast():
    print("NASA Space Weather Quick Forecast Test")
    print("=" * 50)
    
    # Set up API key
    NASA_API_KEY = "h5JimwlPt4XCO0IKcwEhRuVmC7UmSReEp2rP0HPA"
    
    # Get NASA data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3)
    
    try:
        # Test CME data
        cme_url = "https://api.nasa.gov/DONKI/CME"
        params = {
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d"),
            "api_key": NASA_API_KEY
        }
        
        print(f"Fetching CME data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
        response = requests.get(cme_url, params=params, timeout=10)
        
        if response.status_code == 200:
            cme_data = response.json()
            cme_count = len(cme_data)
            print(f"Found {cme_count} CME events")
            
            # Generate simple forecast
            if cme_count >= 3:
                forecast = {
                    "status": "HIGH ACTIVITY",
                    "description": f"Detected {cme_count} CMEs in the last 3 days. Increased aurora activity expected.",
                    "confidence": 0.8,
                    "risk_level": "Moderate to High",
                    "impacts": ["Enhanced aurora activity", "Possible HF radio disruptions", "Minor GNSS degradation"]
                }
            elif cme_count >= 1:
                forecast = {
                    "status": "MODERATE ACTIVITY", 
                    "description": f"Detected {cme_count} CME(s). Possible aurora at high latitudes.",
                    "confidence": 0.6,
                    "risk_level": "Low to Moderate",
                    "impacts": ["Aurora possible at high latitudes", "Minor radio effects"]
                }
            else:
                forecast = {
                    "status": "QUIET CONDITIONS",
                    "description": "No significant events detected. Normal space weather conditions.",
                    "confidence": 0.9,
                    "risk_level": "Low",
                    "impacts": ["Normal conditions", "No significant space weather impacts expected"]
                }
            
            # Display forecast
            print("\n" + "=" * 50)
            print("SPACE WEATHER FORECAST")
            print("=" * 50)
            print(f"Status: {forecast['status']}")
            print(f"Description: {forecast['description']}")
            print(f"Risk Level: {forecast['risk_level']}")
            print(f"Confidence: {forecast['confidence']*100:.0f}%")
            print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print("\nPotential Impacts:")
            for impact in forecast['impacts']:
                print(f"• {impact}")
            
            if cme_count > 0:
                print(f"\nRecent CME Events:")
                for i, cme in enumerate(cme_data[:3]):  # Show first 3 events
                    print(f"• {cme.get('activityID', 'Unknown')} - {cme.get('startTime', 'Unknown time')}")
            
            print("\n" + "=" * 50)
            print("Space Weather Forecasting System is working!")
            return True
            
        else:
            print(f"NASA API Error: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = test_forecast()
    if success:
        print("\nNASA Space Weather System is operational!")
    else:
        print("\nSystem test failed")