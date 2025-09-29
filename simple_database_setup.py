#!/usr/bin/env python3
"""
Simple database setup for NASA Space Weather Forecaster
Creates SQLite database with basic tables
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta

def create_database():
    """Create SQLite database with required tables"""
    print("="*60)
    print("NASA SPACE WEATHER DATABASE SETUP")
    print("="*60)
    
    db_path = os.path.join(os.path.dirname(__file__), "space_weather.db")
    
    try:
        # Create database connection
        print(f"\n[1/4] Creating database at: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create forecasts table
        print("\n[2/4] Creating forecasts table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                forecast_data TEXT,
                generated_at TEXT,
                created_at TEXT,
                forecast_count INTEGER DEFAULT 0,
                max_confidence REAL DEFAULT 0.0,
                event_types TEXT,
                accuracy_score REAL,
                accuracy_evaluated BOOLEAN DEFAULT 0
            )
        """)
        
        # Create alerts table
        print("[3/4] Creating alerts table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                severity TEXT,
                message TEXT,
                forecast_id INTEGER,
                created_at TEXT,
                expires_at TEXT,
                is_active BOOLEAN DEFAULT 1,
                email_sent BOOLEAN DEFAULT 0,
                sms_sent BOOLEAN DEFAULT 0
            )
        """)
        
        # Create system_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT,
                component TEXT,
                message TEXT,
                details TEXT,
                created_at TEXT
            )
        """)
        
        # Create alert_subscriptions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                phone TEXT,
                alert_types TEXT,
                min_confidence REAL DEFAULT 0.6,
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT,
                last_notification TEXT
            )
        """)
        
        # Insert sample data
        print("[4/4] Inserting sample data...")
        
        # Sample forecast
        now = datetime.utcnow()
        sample_forecast = {
            "forecasts": [
                {
                    "event": "CME",
                    "solar_timestamp": "2025-09-28T13:45:00Z",
                    "predicted_arrival_window_utc": [
                        "2025-09-30T18:00:00Z",
                        "2025-10-01T06:00:00Z"
                    ],
                    "risk_summary": "Earth-directed CME with moderate geomagnetic effects expected",
                    "impacts": ["aurora_midlat", "HF_comms", "GNSS_jitter"],
                    "confidence": 0.82,
                    "evidence": {
                        "donki_ids": ["2025-09-28T13:45:00-CME-001"],
                        "epic_frames": ["2025-09-28T12:00:00Z"],
                        "gibs_layers": ["VIIRS_SNPP_CorrectedReflectance_TrueColor"]
                    }
                }
            ],
            "generated_at": now.isoformat() + "Z"
        }
        
        cursor.execute("""
            INSERT INTO forecasts 
            (forecast_data, generated_at, created_at, forecast_count, max_confidence, event_types)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            json.dumps(sample_forecast),
            now.isoformat(),
            now.isoformat(),
            1,
            0.82,
            "CME"
        ))
        
        forecast_id = cursor.lastrowid
        
        # Sample alert
        expires_at = now + timedelta(hours=48)
        cursor.execute("""
            INSERT INTO alerts 
            (event_type, severity, message, forecast_id, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "CME",
            "MODERATE", 
            "Earth-directed CME detected with 82% confidence",
            forecast_id,
            now.isoformat(),
            expires_at.isoformat()
        ))
        
        # Sample system log
        cursor.execute("""
            INSERT INTO system_logs 
            (level, component, message, details, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "INFO",
            "database_setup",
            "Database initialized successfully",
            json.dumps({
                "forecast_count": 1,
                "alert_count": 1,
                "setup_time": now.isoformat()
            }),
            now.isoformat()
        ))
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("\nSUCCESS: Database created successfully!")
        print(f"Database file: {db_path}")
        print(f"Size: {os.path.getsize(db_path) / 1024:.1f} KB")
        
        return True, db_path
        
    except Exception as e:
        print(f"\nERROR: Database creation failed: {e}")
        return False, None

def test_database(db_path):
    """Test database functionality"""
    print("\n" + "="*60)
    print("DATABASE FUNCTIONALITY TEST")
    print("="*60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test 1: Check tables
        print("\n[TEST 1] Checking tables...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Test 2: Check forecasts
        print("\n[TEST 2] Checking forecasts...")
        cursor.execute("SELECT COUNT(*) FROM forecasts")
        forecast_count = cursor.fetchone()[0]
        print(f"Forecast records: {forecast_count}")
        
        if forecast_count > 0:
            cursor.execute("SELECT id, event_types, max_confidence, created_at FROM forecasts LIMIT 3")
            forecasts = cursor.fetchall()
            for forecast in forecasts:
                print(f"  - ID {forecast[0]}: {forecast[1]} ({forecast[2]:.1%} confidence)")
        
        # Test 3: Check alerts
        print("\n[TEST 3] Checking alerts...")
        cursor.execute("SELECT COUNT(*) FROM alerts WHERE is_active = 1")
        alert_count = cursor.fetchone()[0]
        print(f"Active alerts: {alert_count}")
        
        if alert_count > 0:
            cursor.execute("SELECT event_type, severity, message FROM alerts WHERE is_active = 1 LIMIT 3")
            alerts = cursor.fetchall()
            for alert in alerts:
                print(f"  - {alert[0]} {alert[1]}: {alert[2]}")
        
        # Test 4: Check system logs
        print("\n[TEST 4] Checking system logs...")
        cursor.execute("SELECT COUNT(*) FROM system_logs")
        log_count = cursor.fetchone()[0]
        print(f"System log entries: {log_count}")
        
        conn.close()
        
        print("\nSUCCESS: All database tests passed!")
        return True
        
    except Exception as e:
        print(f"\nERROR: Database test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("NASA Space Weather Forecaster - Simple Database Setup")
    print("This creates a SQLite database for storing space weather data")
    print()
    
    # Create database
    success, db_path = create_database()
    
    if success:
        # Test database
        if test_database(db_path):
            print("\n" + "="*60)
            print("DATABASE SETUP COMPLETE")
            print("="*60)
            print("\nThe database is ready for use!")
            print("\nFeatures available:")
            print("  ✓ Forecast history storage")
            print("  ✓ Alert management")
            print("  ✓ System logging")
            print("  ✓ Statistical tracking")
            print("\nAPI endpoints available:")
            print("  • GET /api/v1/database/status")
            print("  • GET /api/v1/database/history")
            print("  • GET /api/v1/database/alerts")
            print("  • GET /api/v1/database/stats")
            print("\nNext steps:")
            print("  1. Restart API server: python simple_api_server.py")
            print("  2. Test endpoints: python test_database_api.py")
            print("  3. View data in DB browser or dashboard")
        else:
            print("\nDatabase created but tests failed. Check for issues.")
    else:
        print("\nDatabase setup failed. Please check error messages.")

if __name__ == "__main__":
    main()