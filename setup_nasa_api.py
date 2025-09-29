#!/usr/bin/env python3
"""
NASA API Key Setup for Space Weather Forecaster
Helps configure NASA API access for live data feeds
"""

import os
import sys
import requests
from datetime import datetime, timedelta

def get_nasa_api_key():
    """Get NASA API key for DONKI access"""
    print("="*60)
    print("NASA API KEY SETUP")
    print("="*60)
    print()
    print("NASA provides free API access to space weather data through DONKI.")
    print("You can use 'DEMO_KEY' for testing (limited requests) or get a free API key.")
    print()
    print("To get a free NASA API key:")
    print("  1. Visit: https://api.nasa.gov/")
    print("  2. Click 'Generate API Key'") 
    print("  3. Fill out the simple form")
    print("  4. Check your email for the API key")
    print()
    
    # Check current setup
    current_key = os.getenv("NASA_API_KEY")
    if current_key:
        print(f"Current NASA API key: {current_key[:8]}...{current_key[-4:] if len(current_key) > 12 else current_key}")
        print()
        use_current = input("Use current key? (Y/n): ").strip().lower()
        if use_current != 'n':
            return current_key
    
    print("\nChoose an option:")
    print("  1. Use DEMO_KEY (limited requests, good for testing)")
    print("  2. Enter your own NASA API key")
    print("  3. Keep current setup")
    
    choice = input("\nChoice (1-3): ").strip()
    
    if choice == "1":
        api_key = "DEMO_KEY"
        print("Using DEMO_KEY for testing...")
    elif choice == "2":
        api_key = input("Enter your NASA API key: ").strip()
        if not api_key:
            print("ERROR: No API key entered")
            return None
    elif choice == "3":
        return current_key
    else:
        print("Invalid choice, using DEMO_KEY")
        api_key = "DEMO_KEY"
    
    return api_key

def test_nasa_api(api_key):
    """Test NASA API access with the provided key"""
    print("\n" + "="*60)
    print("NASA API ACCESS TEST")
    print("="*60)
    
    # Test endpoints
    endpoints = [
        {
            "name": "DONKI CME Events",
            "url": "https://api.nasa.gov/DONKI/CME",
            "params": {
                "startDate": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                "endDate": datetime.now().strftime("%Y-%m-%d"),
                "api_key": api_key
            }
        },
        {
            "name": "DONKI Solar Flares", 
            "url": "https://api.nasa.gov/DONKI/FLR",
            "params": {
                "startDate": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                "endDate": datetime.now().strftime("%Y-%m-%d"),
                "api_key": api_key
            }
        },
        {
            "name": "EPIC Earth Imagery",
            "url": "https://api.nasa.gov/EPIC/api/natural/available",
            "params": {
                "api_key": api_key
            }
        }
    ]
    
    results = []
    
    for endpoint in endpoints:
        print(f"\nTesting {endpoint['name']}...")
        try:
            response = requests.get(endpoint['url'], params=endpoint['params'], timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    count = len(data)
                    print(f"SUCCESS: {count} records retrieved")
                    if count > 0 and endpoint['name'] == "DONKI CME Events":
                        # Show sample CME data
                        cme = data[0]
                        print(f"  Latest CME: {cme.get('activityID', 'Unknown ID')}")
                        print(f"  Start Time: {cme.get('startTime', 'Unknown')}")
                    elif count > 0 and endpoint['name'] == "DONKI Solar Flares":
                        # Show sample flare data
                        flare = data[0]
                        print(f"  Latest Flare: {flare.get('flrID', 'Unknown ID')}")
                        print(f"  Class: {flare.get('classType', 'Unknown')}")
                else:
                    print(f"SUCCESS: Data received (type: {type(data).__name__})")
                results.append(True)
            elif response.status_code == 403:
                print("ERROR: API key invalid or quota exceeded")
                results.append(False)
            elif response.status_code == 429:
                print("WARNING: Rate limit exceeded, try again later")
                results.append(False)
            else:
                print(f"ERROR: HTTP {response.status_code}")
                results.append(False)
                
        except requests.exceptions.Timeout:
            print("ERROR: Request timeout")
            results.append(False)
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Request failed - {e}")
            results.append(False)
        except Exception as e:
            print(f"ERROR: Unexpected error - {e}")
            results.append(False)
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\nAPI Test Results: {success_count}/{total_count} endpoints working")
    
    if success_count == total_count:
        print("SUCCESS: NASA API access is working perfectly!")
        return True
    elif success_count > 0:
        print("PARTIAL: Some endpoints working, API key is valid")
        return True
    else:
        print("FAILED: No endpoints working, check API key or connection")
        return False

def update_env_file(api_key):
    """Update .env file with NASA API key"""
    try:
        env_path = ".env"
        
        # Read existing .env if it exists
        env_lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                env_lines = f.readlines()
        
        # Update or add NASA_API_KEY
        updated = False
        for i, line in enumerate(env_lines):
            if line.startswith("NASA_API_KEY="):
                env_lines[i] = f"NASA_API_KEY={api_key}\n"
                updated = True
                break
        
        if not updated:
            env_lines.append(f"NASA_API_KEY={api_key}\n")
        
        # Write back to file
        with open(env_path, 'w') as f:
            f.writelines(env_lines)
        
        print(f"SUCCESS: NASA API key saved to {env_path}")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to save API key: {e}")
        return False

def main():
    """Main setup function"""
    print("NASA Space Weather Forecaster - API Key Setup")
    print("This configures access to live NASA space weather data")
    print()
    
    # Step 1: Get API key
    api_key = get_nasa_api_key()
    if not api_key:
        print("Setup cancelled.")
        return
    
    # Step 2: Test API access
    if test_nasa_api(api_key):
        # Step 3: Save to .env file
        if update_env_file(api_key):
            print("\n" + "="*60)
            print("NASA API SETUP COMPLETE")
            print("="*60)
            print("\nYour NASA API access is configured and working!")
            print("\nWhat's available now:")
            print("  • Live CME (Coronal Mass Ejection) data")
            print("  • Real-time solar flare information")
            print("  • Solar energetic particle events")
            print("  • Geomagnetic storm data")
            print("  • EPIC Earth imagery")
            print("\nNext steps:")
            print("  1. Restart API server: python simple_api_server.py")
            print("  2. Live data will be automatically integrated")
            print("  3. Dashboards will show real NASA data")
        else:
            print("\nAPI key works but couldn't save to .env file")
            print("You can manually add to .env file:")
            print(f"NASA_API_KEY={api_key}")
    else:
        print("\nAPI test failed. Please check your API key or try again later.")
        print("You can still use the system with simulated data.")

if __name__ == "__main__":
    main()