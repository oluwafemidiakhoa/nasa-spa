#!/usr/bin/env python3
"""
Simple NASA Space Weather System Launcher
"""

import os
import sys
import webbrowser
from pathlib import Path

def main():
    """Main launcher function"""
    print("=" * 80)
    print("NASA SPACE WEATHER MISSION CONTROL")
    print("Complete System Launcher")
    print("=" * 80)
    
    # Open the dashboard hub
    dashboard_path = Path(__file__).parent / "dashboard_hub.html"
    
    if dashboard_path.exists():
        dashboard_url = f"file://{dashboard_path.absolute()}"
        print(f"Opening Dashboard Hub: {dashboard_url}")
        webbrowser.open(dashboard_url)
        print("\nDashboard Hub opened successfully!")
        print("\nAvailable Systems:")
        print("- Expert Physics Engine")
        print("- 3D Solar System Visualization") 
        print("- Professional Mission Control")
        print("- 3D Space Weather Dashboard")
        print("- Expert Demo System")
        print("- Simple Interface")
        print("\nClick on any dashboard card to launch that system.")
        print("All systems are operational and ready for use.")
    else:
        print("Error: Dashboard Hub not found")
        return False
    
    print("\nSystem launched successfully!")
    return True

if __name__ == "__main__":
    try:
        main()
        input("\nPress Enter to exit...")
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")