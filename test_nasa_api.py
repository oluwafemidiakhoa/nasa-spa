#!/usr/bin/env python3
"""
Test NASA API connectivity
"""

import os
import requests
from datetime import datetime, timedelta
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        pass

# Load environment variables
load_dotenv()

NASA_API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")

def test_nasa_donki():
    """Test NASA DONKI CME API"""
    print("Testing NASA DONKI CME API...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3)
    
    url = "https://api.nasa.gov/DONKI/CME"
    params = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "api_key": NASA_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"CME Events Found: {len(data)}")
            if data:
                print(f"Latest event: {data[0].get('activityID', 'Unknown')}")
                print(f"Event time: {data[0].get('startTime', 'Unknown')}")
            return True, len(data)
        else:
            print(f"Error: {response.text}")
            return False, 0
            
    except Exception as e:
        print(f"Error connecting to NASA API: {e}")
        return False, 0

def test_nasa_epic():
    """Test NASA EPIC API"""
    print("\nTesting NASA EPIC API...")
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    url = f"https://api.nasa.gov/EPIC/api/natural/date/{date_str}"
    params = {"api_key": NASA_API_KEY}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"EPIC Images Found: {len(data)}")
            if data:
                print(f"Latest image: {data[0].get('identifier', 'Unknown')}")
            return True, len(data)
        else:
            print(f"Error: {response.text}")
            return False, 0
            
    except Exception as e:
        print(f"Error connecting to EPIC API: {e}")
        return False, 0

if __name__ == "__main__":
    print("NASA API Connectivity Test")
    print("=" * 40)
    print(f"Using API Key: {NASA_API_KEY[:10]}...")
    print()
    
    # Test DONKI
    donki_success, cme_count = test_nasa_donki()
    
    # Test EPIC  
    epic_success, image_count = test_nasa_epic()
    
    print("\n" + "=" * 40)
    print("SUMMARY:")
    print(f"DONKI API: {'✓ Working' if donki_success else '✗ Failed'}")
    print(f"EPIC API: {'✓ Working' if epic_success else '✗ Failed'}")
    
    if donki_success or epic_success:
        print("\n✓ NASA API connectivity is working!")
        print(f"Found {cme_count} CME events and {image_count} EPIC images")
    else:
        print("\n✗ NASA API connectivity failed")
        print("Check your API key and internet connection")