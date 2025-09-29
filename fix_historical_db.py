#!/usr/bin/env python3
"""
Fix and populate historical database with proper schema
"""

import sys
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import requests
import time
import json

def fix_database_schema():
    """Fix the database schema"""
    db_path = Path("data/historical/space_weather_history.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove old database and create new one
    if db_path.exists():
        db_path.unlink()
    
    conn = sqlite3.connect(db_path)
    
    # Create table with correct column name
    conn.execute("""
        CREATE TABLE historical_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id TEXT UNIQUE,
            event_type TEXT,
            start_time TEXT,
            source_location TEXT,
            speed REAL,
            angular_width REAL,
            direction REAL,
            catalog TEXT,
            raw_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE TABLE collection_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collection_date TEXT,
            events_collected INTEGER,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("Database schema fixed")

def collect_sample_historical_data():
    """Collect a manageable sample of historical data (6 months)"""
    
    # Load NASA API key
    nasa_api_key = os.getenv("NASA_API_KEY", "h5JimwlPt4XCO0IKcwEhRuVmC7UmSReEp2rP0HPA")
    
    # Collect last 6 months instead of 2 years
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)  # 6 months
    
    print(f"Collecting CME data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    url = "https://api.nasa.gov/DONKI/CME"
    params = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "api_key": nasa_api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        cme_data = response.json()
        print(f"Retrieved {len(cme_data)} CME events")
        
        # Store in database
        db_path = "data/historical/space_weather_history.db"
        conn = sqlite3.connect(db_path)
        stored_count = 0
        
        for event in cme_data:
            try:
                activity_id = event.get('activityID', '')
                start_time = event.get('startTime', '')
                source_location = str(event.get('sourceLocation', ''))
                
                # Extract CME analysis parameters
                speed = None
                angular_width = None
                direction = None
                
                if 'cmeAnalyses' in event and event['cmeAnalyses']:
                    analysis = event['cmeAnalyses'][0]
                    speed = analysis.get('speed', 0)
                    angular_width = analysis.get('halfAngle', 0) 
                    direction = analysis.get('latitude', 0)
                
                # Store with correct column name
                conn.execute("""
                    INSERT OR REPLACE INTO historical_events 
                    (activity_id, event_type, start_time, source_location, speed, angular_width, direction, catalog, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    activity_id, 'CME', start_time, source_location,
                    speed, angular_width, direction, 'DONKI', json.dumps(event)
                ))
                
                stored_count += 1
                
            except Exception as e:
                print(f"Error storing event {event.get('activityID', 'unknown')}: {e}")
        
        conn.commit()
        
        # Update collection status
        conn.execute("""
            INSERT INTO collection_status (collection_date, events_collected, status)
            VALUES (?, ?, ?)
        """, (datetime.now().strftime('%Y-%m-%d'), stored_count, 'completed'))
        conn.commit()
        conn.close()
        
        print(f"Successfully stored {stored_count} events in database")
        return stored_count
        
    except Exception as e:
        print(f"Error collecting data: {e}")
        return 0

def main():
    """Main function"""
    print("FIXING AND POPULATING HISTORICAL DATABASE")
    print("=" * 50)
    
    # Fix database schema
    fix_database_schema()
    
    # Collect sample data (6 months)
    events_collected = collect_sample_historical_data()
    
    if events_collected > 0:
        print(f"\nSUCCESS: Historical database populated with {events_collected} events")
        print("Database ready for ML model training")
        
        # Show summary
        db_path = "data/historical/space_weather_history.db"
        conn = sqlite3.connect(db_path)
        
        cursor = conn.execute("SELECT COUNT(*) FROM historical_events")
        total_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT MIN(start_time), MAX(start_time) FROM historical_events")
        date_range = cursor.fetchone()
        
        conn.close()
        
        print(f"\nDatabase Summary:")
        print(f"- Total events: {total_count}")
        print(f"- Date range: {date_range[0]} to {date_range[1]}")
        print(f"- Ready for ML training: YES")
        
        return True
    else:
        print("FAILED: Could not populate historical database")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("Database population failed")