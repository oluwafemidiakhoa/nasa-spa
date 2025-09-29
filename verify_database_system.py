#!/usr/bin/env python3
"""
Complete verification of the database system
"""

import os
import sqlite3
import json
import requests
from datetime import datetime

def verify_database_file():
    """Verify database file exists and has correct structure"""
    print("="*60)
    print("DATABASE FILE VERIFICATION")
    print("="*60)
    
    db_path = os.path.join(os.path.dirname(__file__), "space_weather.db")
    
    if not os.path.exists(db_path):
        print("ERROR: Database file not found")
        print("Run: python simple_database_setup.py")
        return False
    
    print(f"SUCCESS: Database file found")
    print(f"Location: {db_path}")
    print(f"Size: {os.path.getsize(db_path) / 1024:.1f} KB")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check required tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['forecasts', 'alerts', 'system_logs', 'alert_subscriptions']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            print(f"ERROR: Missing tables: {missing_tables}")
            conn.close()
            return False
        
        print(f"SUCCESS: All required tables present ({len(tables)} total)")
        
        # Check data
        cursor.execute("SELECT COUNT(*) FROM forecasts")
        forecast_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM alerts WHERE is_active = 1")
        alert_count = cursor.fetchone()[0]
        
        print(f"Data: {forecast_count} forecasts, {alert_count} active alerts")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR: Database verification failed: {e}")
        return False

def verify_api_server():
    """Verify API server is running and has database endpoints"""
    print("\n" + "="*60)
    print("API SERVER VERIFICATION")
    print("="*60)
    
    base_url = "http://localhost:9001"
    
    # Test basic connectivity
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("SUCCESS: API server is running")
        else:
            print(f"WARNING: API server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("ERROR: API server not running")
        print("Start with: python simple_api_server.py")
        return False
    except Exception as e:
        print(f"ERROR: API server test failed: {e}")
        return False
    
    # Test database endpoints
    database_endpoints = [
        "/api/v1/database/status",
        "/api/v1/database/history", 
        "/api/v1/database/alerts",
        "/api/v1/database/stats"
    ]
    
    working_endpoints = 0
    
    for endpoint in database_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"SUCCESS: {endpoint}")
                    working_endpoints += 1
                else:
                    print(f"API ERROR: {endpoint} - {data.get('error', 'Unknown')}")
            else:
                print(f"HTTP ERROR: {endpoint} - Status {response.status_code}")
        except Exception as e:
            print(f"ERROR: {endpoint} - {e}")
    
    if working_endpoints == len(database_endpoints):
        print(f"\nSUCCESS: All {working_endpoints} database endpoints working")
        return True
    else:
        print(f"\nPARTIAL: {working_endpoints}/{len(database_endpoints)} endpoints working")
        if working_endpoints == 0:
            print("API server may need restart to load new database endpoints")
        return working_endpoints > 0

def test_database_functionality():
    """Test actual database operations through API"""
    print("\n" + "="*60)
    print("DATABASE FUNCTIONALITY TEST")
    print("="*60)
    
    base_url = "http://localhost:9001"
    
    tests = [
        {
            "name": "Database Status",
            "url": f"{base_url}/api/v1/database/status",
            "check": lambda data: data.get('data', {}).get('database_available', False)
        },
        {
            "name": "Forecast History",
            "url": f"{base_url}/api/v1/database/history",
            "check": lambda data: len(data.get('data', {}).get('forecasts', [])) > 0
        },
        {
            "name": "Active Alerts",
            "url": f"{base_url}/api/v1/database/alerts", 
            "check": lambda data: 'alerts' in data.get('data', {})
        },
        {
            "name": "Accuracy Stats",
            "url": f"{base_url}/api/v1/database/stats",
            "check": lambda data: 'total_forecasts' in data.get('data', {})
        }
    ]
    
    passed_tests = 0
    
    for test in tests:
        try:
            response = requests.get(test['url'], timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and test['check'](data):
                    print(f"SUCCESS: {test['name']}")
                    passed_tests += 1
                else:
                    print(f"FAIL: {test['name']} - Data validation failed")
            else:
                print(f"FAIL: {test['name']} - HTTP {response.status_code}")
        except Exception as e:
            print(f"ERROR: {test['name']} - {e}")
    
    return passed_tests == len(tests)

def generate_system_report():
    """Generate a comprehensive system status report"""
    print("\n" + "="*60)
    print("SYSTEM STATUS REPORT")
    print("="*60)
    
    # Database info
    db_path = os.path.join(os.path.dirname(__file__), "space_weather.db")
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get forecast stats
            cursor.execute("SELECT COUNT(*), MAX(created_at) FROM forecasts")
            forecast_stats = cursor.fetchone()
            
            # Get alert stats
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE is_active = 1")
            active_alerts = cursor.fetchone()[0]
            
            # Get log stats
            cursor.execute("SELECT COUNT(*) FROM system_logs")
            log_entries = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"\nDatabase Statistics:")
            print(f"  Total forecasts: {forecast_stats[0]}")
            print(f"  Latest forecast: {forecast_stats[1] or 'None'}")
            print(f"  Active alerts: {active_alerts}")
            print(f"  Log entries: {log_entries}")
            print(f"  Database size: {os.path.getsize(db_path) / 1024:.1f} KB")
            
        except Exception as e:
            print(f"  Database query error: {e}")
    
    # API status
    try:
        response = requests.get("http://localhost:9001/", timeout=3)
        if response.status_code == 200:
            print(f"\nAPI Server: RUNNING")
            print(f"  URL: http://localhost:9001")
            print(f"  Status: Operational")
        else:
            print(f"\nAPI Server: ISSUES (Status {response.status_code})")
    except:
        print(f"\nAPI Server: NOT RUNNING")
    
    print(f"\nSystem Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Main verification function"""
    print("NASA Space Weather Forecaster - Database System Verification")
    print("This checks all database components are working correctly")
    print()
    
    # Step 1: Verify database file
    db_ok = verify_database_file()
    
    # Step 2: Verify API server
    api_ok = verify_api_server()
    
    # Step 3: Test functionality
    if db_ok and api_ok:
        func_ok = test_database_functionality()
    else:
        func_ok = False
    
    # Step 4: Generate report
    generate_system_report()
    
    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    if db_ok and api_ok and func_ok:
        print("STATUS: ALL SYSTEMS OPERATIONAL")
        print("\nThe database system is fully functional!")
        print("\nWhat you can do now:")
        print("  - View forecast history in dashboards")
        print("  - Monitor space weather alerts")
        print("  - Track prediction accuracy over time")
        print("  - Export historical data for analysis")
    elif db_ok and api_ok:
        print("STATUS: PARTIAL - Database and API working, some functions need attention")
    elif db_ok:
        print("STATUS: DATABASE OK - API server needs restart or configuration")
        print("\nNext steps:")
        print("  1. Restart API server: python simple_api_server.py")
        print("  2. Re-run this verification")
    else:
        print("STATUS: DATABASE NEEDS SETUP")
        print("\nNext steps:")
        print("  1. Run: python simple_database_setup.py")
        print("  2. Run: python simple_api_server.py") 
        print("  3. Re-run this verification")

if __name__ == "__main__":
    main()