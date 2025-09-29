#!/usr/bin/env python3
"""
Populate Historical Space Weather Database
Collects 1-2 years of NASA DONKI data for ML training
"""

import sys
import os
from pathlib import Path
import sqlite3
from datetime import datetime, timedelta
import requests
import time
import json

# Add backend to path
sys.path.append('.')
sys.path.append('backend')

def setup_historical_database():
    """Initialize the historical database"""
    db_path = Path("data/historical/space_weather_history.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    
    # Create tables for historical events
    conn.execute("""
        CREATE TABLE IF NOT EXISTS historical_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE,
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
        CREATE TABLE IF NOT EXISTS collection_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date TEXT,
            end_date TEXT,
            events_collected INTEGER,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("Historical database initialized")

def collect_historical_cme_data(start_date, end_date, nasa_api_key):
    """Collect historical CME data from NASA DONKI"""
    
    url = "https://api.nasa.gov/DONKI/CME"
    params = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "api_key": nasa_api_key
    }
    
    print(f"Collecting CME data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        cme_data = response.json()
        print(f"Retrieved {len(cme_data)} CME events")
        
        return cme_data
        
    except Exception as e:
        print(f"Error collecting data: {e}")
        return []

def store_historical_events(events, db_path):
    """Store events in historical database"""
    
    conn = sqlite3.connect(db_path)
    stored_count = 0
    
    for event in events:
        try:
            # Extract key parameters
            event_id = event.get('activityID', '')
            start_time = event.get('startTime', '')
            source_location = event.get('sourceLocation', '')
            
            # Extract CME analysis data if available
            speed = None
            angular_width = None
            direction = None
            
            if 'cmeAnalyses' in event and event['cmeAnalyses']:
                analysis = event['cmeAnalyses'][0]  # Use first analysis
                speed = analysis.get('speed', 0)
                angular_width = analysis.get('halfAngle', 0)
                direction = analysis.get('latitude', 0)
            
            # Store in database
            conn.execute("""
                INSERT OR REPLACE INTO historical_events 
                (event_id, event_type, start_time, source_location, speed, angular_width, direction, catalog, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id, 'CME', start_time, str(source_location), 
                speed, angular_width, direction, 'DONKI', json.dumps(event)
            ))
            
            stored_count += 1
            
        except Exception as e:
            print(f"Error storing event {event.get('activityID', 'unknown')}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"Stored {stored_count} events in database")
    return stored_count

def collect_historical_flare_data(start_date, end_date, nasa_api_key):
    """Collect historical solar flare data"""
    
    url = "https://api.nasa.gov/DONKI/FLR"
    params = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "api_key": nasa_api_key
    }
    
    print(f"Collecting solar flare data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        flare_data = response.json()
        print(f"Retrieved {len(flare_data)} solar flare events")
        
        return flare_data
        
    except Exception as e:
        print(f"Error collecting flare data: {e}")
        return []

def populate_historical_database():
    """Main function to populate historical database"""
    
    print("POPULATING HISTORICAL SPACE WEATHER DATABASE")
    print("=" * 60)
    
    # Setup database
    setup_historical_database()
    
    # Load NASA API key
    nasa_api_key = os.getenv("NASA_API_KEY", "DEMO_KEY")
    if nasa_api_key == "DEMO_KEY":
        print("Warning: Using DEMO_KEY - limited requests available")
    
    # Define collection periods (last 2 years in chunks to avoid timeout)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # 2 years
    
    # Collect in 6-month chunks to avoid API timeouts
    chunk_days = 180  # 6 months
    current_start = start_date
    
    total_events = 0
    db_path = "data/historical/space_weather_history.db"
    
    while current_start < end_date:
        current_end = min(current_start + timedelta(days=chunk_days), end_date)
        
        print(f"\nCollecting chunk: {current_start.strftime('%Y-%m-%d')} to {current_end.strftime('%Y-%m-%d')}")
        
        # Collect CME data
        cme_events = collect_historical_cme_data(current_start, current_end, nasa_api_key)
        if cme_events:
            stored = store_historical_events(cme_events, db_path)
            total_events += stored
        
        # Small delay to be respectful to NASA servers
        time.sleep(2)
        
        # Collect solar flare data
        flare_events = collect_historical_flare_data(current_start, current_end, nasa_api_key)
        if flare_events:
            # Convert flares to common format and store
            for flare in flare_events:
                flare['event_type'] = 'FLARE'
            stored_flares = store_historical_events(flare_events, db_path)
            total_events += stored_flares
        
        # Update progress
        conn = sqlite3.connect(db_path)
        conn.execute("""
            INSERT INTO collection_progress (start_date, end_date, events_collected, status)
            VALUES (?, ?, ?, ?)
        """, (
            current_start.strftime('%Y-%m-%d'),
            current_end.strftime('%Y-%m-%d'),
            len(cme_events) + len(flare_events),
            'completed'
        ))
        conn.commit()
        conn.close()
        
        current_start = current_end + timedelta(days=1)
        time.sleep(3)  # Rate limiting
    
    print(f"\nHistorical data collection completed!")
    print(f"Total events collected: {total_events}")
    
    # Summary statistics
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT COUNT(*) FROM historical_events")
    total_count = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT event_type, COUNT(*) FROM historical_events GROUP BY event_type")
    type_counts = cursor.fetchall()
    conn.close()
    
    print(f"\nDatabase summary:")
    print(f"Total events in database: {total_count}")
    for event_type, count in type_counts:
        print(f"- {event_type}: {count} events")
    
    return total_count > 0

if __name__ == "__main__":
    success = populate_historical_database()
    if success:
        print("\nHistorical database population completed successfully!")
        print("Ready for ML model training")
    else:
        print("\nHistorical database population failed")