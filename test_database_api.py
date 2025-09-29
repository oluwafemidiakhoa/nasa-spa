#!/usr/bin/env python3
"""
Test database API endpoints for NASA Space Weather Forecaster
"""

import requests
import json
import time
from datetime import datetime

API_BASE = "http://localhost:9001"

def test_database_endpoints():
    """Test all database-related API endpoints"""
    print("="*60)
    print("NASA SPACE WEATHER DATABASE API TEST")
    print("="*60)
    
    endpoints = [
        {
            "name": "Database Status",
            "url": f"{API_BASE}/api/v1/database/status",
            "description": "Check if database is initialized and operational"
        },
        {
            "name": "Forecast History", 
            "url": f"{API_BASE}/api/v1/database/history?days=7&limit=10",
            "description": "Get recent forecast history with query parameters"
        },
        {
            "name": "Active Alerts",
            "url": f"{API_BASE}/api/v1/database/alerts", 
            "description": "Get currently active space weather alerts"
        },
        {
            "name": "Accuracy Statistics",
            "url": f"{API_BASE}/api/v1/database/stats",
            "description": "Get forecast accuracy statistics and metrics"
        }
    ]
    
    results = []
    
    for i, endpoint in enumerate(endpoints, 1):
        print(f"\n[{i}/{len(endpoints)}] Testing {endpoint['name']}...")
        print(f"URL: {endpoint['url']}")
        print(f"Description: {endpoint['description']}")
        
        try:
            response = requests.get(endpoint['url'], timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    print("STATUS: SUCCESS")
                    
                    # Display relevant data
                    if 'database_status' in endpoint['name'].lower():
                        db_data = data['data']
                        print(f"  Database Available: {db_data.get('database_available', 'Unknown')}")
                        if db_data.get('database_available'):
                            print(f"  Database Size: {db_data.get('database_size_mb', 0):.2f} MB")
                            print(f"  Status: {db_data.get('status', 'Unknown')}")
                        else:
                            print(f"  Message: {db_data.get('message', 'No details')}")
                    
                    elif 'history' in endpoint['name'].lower():
                        history_data = data['data']
                        forecasts = history_data.get('forecasts', [])
                        print(f"  Total Forecasts: {history_data.get('total_count', 0)}")
                        print(f"  Days Back: {history_data.get('days_back', 0)}")
                        
                        if forecasts:
                            print(f"  Latest Forecasts:")
                            for forecast in forecasts[:3]:  # Show first 3
                                print(f"    - ID {forecast['id']}: {forecast['event_types']} ({forecast['max_confidence']:.1%} confidence)")
                        else:
                            print("    No forecast history found")
                    
                    elif 'alerts' in endpoint['name'].lower():
                        alerts_data = data['data']
                        alerts = alerts_data.get('alerts', [])
                        print(f"  Active Alerts: {alerts_data.get('active_count', 0)}")
                        
                        if alerts:
                            for alert in alerts:
                                print(f"    - {alert['event_type']} {alert['severity']}: {alert['message']}")
                        else:
                            print("    No active alerts")
                    
                    elif 'stats' in endpoint['name'].lower():
                        stats_data = data['data']
                        print(f"  Total Forecasts (30 days): {stats_data.get('total_forecasts', 0)}")
                        print(f"  Average Confidence: {stats_data.get('average_confidence', 0):.1%}")
                        print(f"  Evaluated Forecasts: {stats_data.get('evaluated_forecasts', 0)}")
                        print(f"  Average Accuracy: {stats_data.get('average_accuracy', 0):.1%}")
                        
                        event_dist = stats_data.get('event_distribution', {})
                        if event_dist:
                            print("  Event Distribution:")
                            for event_type, count in event_dist.items():
                                print(f"    - {event_type}: {count}")
                    
                    results.append({"endpoint": endpoint['name'], "status": "SUCCESS", "data": data})
                else:
                    print(f"STATUS: API ERROR - {data.get('error', 'Unknown error')}")
                    results.append({"endpoint": endpoint['name'], "status": "API_ERROR", "error": data.get('error')})
            else:
                print(f"STATUS: HTTP ERROR - {response.status_code}")
                results.append({"endpoint": endpoint['name'], "status": "HTTP_ERROR", "code": response.status_code})
                
        except requests.exceptions.ConnectionError:
            print("STATUS: CONNECTION ERROR - API server not running")
            results.append({"endpoint": endpoint['name'], "status": "CONNECTION_ERROR"})
        except requests.exceptions.Timeout:
            print("STATUS: TIMEOUT ERROR")
            results.append({"endpoint": endpoint['name'], "status": "TIMEOUT"})
        except Exception as e:
            print(f"STATUS: UNEXPECTED ERROR - {e}")
            results.append({"endpoint": endpoint['name'], "status": "ERROR", "error": str(e)})
        
        time.sleep(0.5)  # Small delay between requests
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    total_count = len(results)
    
    print(f"Database API Tests: {success_count}/{total_count} passed")
    
    if success_count == total_count:
        print("\nSUCCESS: All database endpoints are working!")
        print("\nWhat you can do now:")
        print("  1. View forecast history in dashboards")
        print("  2. Track space weather alerts over time")
        print("  3. Monitor forecast accuracy statistics")
        print("  4. Export historical data for analysis")
    elif success_count == 0:
        print("\nERROR: Database system not available")
        print("\nTo fix this:")
        print("  1. Initialize database: python setup_database.py")
        print("  2. Restart API server: python simple_api_server.py")
        print("  3. Re-run this test")
    else:
        print(f"\nPARTIAL: {total_count - success_count} endpoint(s) failed")
        print("\nFailed endpoints:")
        for result in results:
            if result['status'] != 'SUCCESS':
                print(f"  - {result['endpoint']}: {result['status']}")
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return success_count == total_count

def test_database_initialization():
    """Test if database is properly initialized"""
    print("\n" + "="*60)
    print("DATABASE INITIALIZATION TEST")
    print("="*60)
    
    try:
        # Test database file existence
        import os
        db_path = os.path.join(os.path.dirname(__file__), "space_weather.db")
        
        if os.path.exists(db_path):
            db_size = os.path.getsize(db_path)
            print(f"SUCCESS: Database file found")
            print(f"  Location: {db_path}")
            print(f"  Size: {db_size / 1024:.1f} KB")
            
            # Test basic SQLite connection
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print(f"  Tables: {len(tables)}")
            for table in tables:
                print(f"    - {table[0]}")
            
            # Check forecast count
            cursor.execute("SELECT COUNT(*) FROM forecasts")
            forecast_count = cursor.fetchone()[0]
            print(f"  Forecast records: {forecast_count}")
            
            # Check alert count  
            cursor.execute("SELECT COUNT(*) FROM alerts")
            alert_count = cursor.fetchone()[0]
            print(f"  Alert records: {alert_count}")
            
            conn.close()
            return True
            
        else:
            print("WARNING: Database file not found")
            print(f"  Expected location: {db_path}")
            print("  Run setup_database.py to initialize")
            return False
            
    except Exception as e:
        print(f"ERROR: Database initialization test failed: {e}")
        return False

if __name__ == "__main__":
    print("NASA Space Weather Forecaster - Database API Test Suite")
    print("This will test all database-related API endpoints")
    print()
    
    # Test 1: Database initialization
    db_ready = test_database_initialization()
    
    # Test 2: API endpoints
    if db_ready:
        api_ready = test_database_endpoints()
        
        if api_ready:
            print("\n" + "="*60)
            print("ALL TESTS PASSED - DATABASE SYSTEM OPERATIONAL")
            print("="*60)
        else:
            print("\nSome database API tests failed. Check API server status.")
    else:
        print("\nDatabase not initialized. Run setup_database.py first.")
    
    print("\nNext steps:")
    print("  • Historical data will be automatically stored")
    print("  • Use database browser to explore data")
    print("  • Monitor accuracy statistics over time")
    print("  • Set up automated data cleanup if needed")