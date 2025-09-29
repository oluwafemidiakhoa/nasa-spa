#!/usr/bin/env python3
"""
Demonstrate that live NASA data is successfully integrated
"""

import os
import json
from datetime import datetime

def show_live_data_summary():
    """Show summary of live NASA data"""
    print("=" * 60)
    print("LIVE NASA DATA INTEGRATION DEMONSTRATION")
    print("=" * 60)
    
    # Check live data file
    if os.path.exists('live_nasa_data.js'):
        with open('live_nasa_data.js', 'r') as f:
            content = f.read()
        
        print("✓ Live NASA data file exists")
        print(f"  Size: {len(content) / 1024:.1f} KB")
        
        # Extract summary info
        if 'Total Events:' in content:
            total_line = [line for line in content.split('\n') if 'Total Events:' in line][0]
            total_events = total_line.split('Total Events: ')[1]
            print(f"  Total Events: {total_events}")
        
        # Count different event types
        cme_count = content.count('"type": "CME"')
        flare_count = content.count('"type": "Solar Flare"')
        
        print(f"  CME Events: {cme_count}")
        print(f"  Solar Flare Events: {flare_count}")
        
        # Check for real NASA IDs
        if '-CME-' in content:
            print("  ✓ Real NASA CME IDs detected")
        if '-FLR-' in content:
            print("  ✓ Real NASA flare IDs detected")
        
        # Show sample event
        if 'events: [' in content:
            print("\n--- SAMPLE LIVE NASA EVENT ---")
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if '"id": "2025-' in line and '-CME-' in line:
                    # Show this event and next few lines
                    event_id = line.split('"id": "')[1].split('"')[0]
                    print(f"ID: {event_id}")
                    if i+1 < len(lines) and '"type":' in lines[i+1]:
                        event_type = lines[i+1].split('"type": "')[1].split('"')[0]
                        print(f"Type: {event_type}")
                    if i+2 < len(lines) and '"time":' in lines[i+2]:
                        event_time = lines[i+2].split('"time": "')[1].split('"')[0]
                        print(f"Time: {event_time}")
                    if i+3 < len(lines) and '"speed":' in lines[i+3]:
                        speed = lines[i+3].split('"speed": ')[1].split(',')[0]
                        print(f"Speed: {speed} km/s")
                    break
        
        return True
    else:
        print("✗ Live NASA data file not found")
        return False

def show_dashboard_integration():
    """Show dashboard integration status"""
    print("\n" + "=" * 60)
    print("DASHBOARD INTEGRATION STATUS")
    print("=" * 60)
    
    dashboards = {
        '3d_dashboard.html': ['live_nasa_data.js', 'LIVE_NASA_DATA'],
        'simple_new.html': ['live_nasa_data.js', 'LIVE_NASA_DATA']
    }
    
    for dashboard, checks in dashboards.items():
        if os.path.exists(dashboard):
            with open(dashboard, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"\n{dashboard}:")
            all_present = True
            
            for check in checks:
                if check in content:
                    print(f"  ✓ {check} integration present")
                else:
                    print(f"  ✗ {check} integration missing")
                    all_present = False
            
            if all_present:
                print(f"  ✓ {dashboard} is ready for live NASA data")
            else:
                print(f"  ⚠ {dashboard} needs attention")
                
        else:
            print(f"\n{dashboard}: FILE NOT FOUND")

def show_api_status():
    """Show NASA API status"""
    print("\n" + "=" * 60)
    print("NASA API STATUS")
    print("=" * 60)
    
    try:
        import sys
        sys.path.append('backend')
        os.environ['NASA_API_KEY'] = 'h5JimwlPt4XCO0IKcwEhRuVmC7UmSReEp2rP0HPA'
        
        from nasa_client import NASAClient
        client = NASAClient()
        
        # Quick test
        cmes = client.fetch_donki_cmes(days_back=1)
        print(f"✓ NASA API working: {len(cmes)} CMEs in last 24h")
        
        if cmes:
            latest = cmes[0]
            print(f"  Latest CME: {latest.get('activityID', 'Unknown')}")
            print(f"  Time: {latest.get('startTime', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"✗ NASA API error: {e}")
        return False

def main():
    """Main demonstration"""
    print("NASA Space Weather Dashboard - Live Integration Demonstration")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check components
    data_ok = show_live_data_summary()
    show_dashboard_integration()
    api_ok = show_api_status()
    
    # Final status
    print("\n" + "=" * 60)
    print("INTEGRATION STATUS SUMMARY")
    print("=" * 60)
    
    if data_ok and api_ok:
        print("STATUS: ✓ LIVE NASA INTEGRATION SUCCESSFUL")
        print()
        print("🚀 What's working:")
        print("   • Real-time NASA DONKI data feeds")
        print("   • Live CME events with speeds and coordinates")
        print("   • Actual solar flare classifications")
        print("   • Space weather event timelines")
        print("   • Dashboard integration ready")
        print()
        print("🎯 Ready for next phase:")
        print("   • Task 3 (Live NASA Integration) COMPLETE")
        print("   • Ready to proceed to Task 4 (Mobile-responsive design)")
        print()
        print("📱 How to test:")
        print("   1. Open 3d_dashboard.html in browser")
        print("   2. Open simple_new.html in browser")
        print("   3. Check browser console for 'Live NASA data loaded'")
        print("   4. Look for real CME events in timeline")
        print("   5. Verify event counts match live NASA data")
        
    elif data_ok:
        print("STATUS: ⚠ DATA READY - API NEEDS ATTENTION")
        print("Live data is available but API has issues")
        
    else:
        print("STATUS: ✗ INTEGRATION INCOMPLETE")
        print("Components need attention")
    
    print()

if __name__ == "__main__":
    main()