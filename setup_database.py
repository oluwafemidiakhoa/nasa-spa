#!/usr/bin/env python3
"""
Database setup and management for NASA Space Weather Forecaster
"""

import os
import sys
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def setup_database():
    """Initialize the database and create tables"""
    print("="*60)
    print("NASA SPACE WEATHER DATABASE SETUP")
    print("="*60)
    
    try:
        # Import database components
        from backend.database import DatabaseManager, ForecastRecord, AlertRecord, SystemLog
        from backend.schema import ForecastBundle, Forecast, Evidence
        
        print("\n[1/5] Importing database components...")
        print("SUCCESS: Database modules imported")
        
        # Initialize database
        print("\n[2/5] Initializing database...")
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        db_path = os.path.join(os.path.dirname(__file__), "space_weather.db")
        print(f"SUCCESS: Database created at {db_path}")
        
        # Create sample data
        print("\n[3/5] Creating sample forecast data...")
        
        # Create sample forecast for testing
        sample_evidence = Evidence(
            donki_ids=["2025-09-28T13:45:00-CME-001"],
            epic_frames=["2025-09-28T12:00:00Z"],
            gibs_layers=["VIIRS_SNPP_CorrectedReflectance_TrueColor"]
        )
        
        sample_forecast = Forecast(
            event="CME",
            solar_timestamp="2025-09-28T13:45:00Z",
            predicted_arrival_window_utc=[
                "2025-09-30T18:00:00Z",
                "2025-10-01T06:00:00Z"
            ],
            risk_summary="Earth-directed CME with moderate geomagnetic effects expected",
            impacts=["aurora_midlat", "HF_comms", "GNSS_jitter"],
            confidence=0.82,
            evidence=sample_evidence
        )
        
        sample_bundle = ForecastBundle(
            forecasts=[sample_forecast],
            generated_at=datetime.utcnow().isoformat() + "Z"
        )
        
        # Store sample forecast
        forecast_id = await db_manager.store_forecast(sample_bundle)
        print(f"SUCCESS: Sample forecast stored with ID {forecast_id}")
        
        # Create sample alert
        print("\n[4/5] Creating sample alert...")
        alert_id = await db_manager.store_alert(
            event_type="CME",
            severity="MODERATE",
            message="Earth-directed CME detected with 82% confidence",
            forecast_id=forecast_id,
            expires_hours=48
        )
        print(f"SUCCESS: Sample alert stored with ID {alert_id}")
        
        # Log system event
        print("\n[5/5] Creating system log entry...")
        await db_manager.log_system_event(
            level="INFO",
            component="database_setup",
            message="Database initialized successfully",
            details={
                "forecast_count": 1,
                "alert_count": 1,
                "setup_time": datetime.utcnow().isoformat()
            }
        )
        print("SUCCESS: System log entry created")
        
        # Test queries
        print("\n" + "="*60)
        print("DATABASE TEST QUERIES")
        print("="*60)
        
        # Test forecast retrieval
        latest_forecast = await db_manager.get_latest_forecast()
        if latest_forecast:
            print(f"\nLatest forecast:")
            print(f"  - ID: {latest_forecast.id}")
            print(f"  - Generated: {latest_forecast.generated_at}")
            print(f"  - Event types: {latest_forecast.event_types}")
            print(f"  - Confidence: {latest_forecast.max_confidence:.1%}")
            print(f"  - Forecast count: {latest_forecast.forecast_count}")
        
        # Test active alerts
        active_alerts = await db_manager.get_active_alerts()
        print(f"\nActive alerts: {len(active_alerts)}")
        for alert in active_alerts:
            print(f"  - {alert.event_type} {alert.severity}: {alert.message}")
            print(f"    Expires: {alert.expires_at}")
        
        # Test accuracy stats
        accuracy_stats = await db_manager.get_accuracy_stats()
        print(f"\nAccuracy statistics:")
        print(f"  - Total forecasts: {accuracy_stats['total_forecasts']}")
        print(f"  - Evaluated forecasts: {accuracy_stats['evaluated_forecasts']}")
        print(f"  - Average accuracy: {accuracy_stats['average_accuracy']:.1%}")
        
        await db_manager.close()
        
        print("\n" + "="*60)
        print("DATABASE SETUP COMPLETE")
        print("="*60)
        print(f"Database file: {db_path}")
        print(f"Size: {os.path.getsize(db_path) / 1024:.1f} KB")
        print("\nTables created:")
        print("  - forecasts (space weather predictions)")
        print("  - alerts (active warnings)")
        print("  - alert_subscriptions (user notifications)")
        print("  - system_logs (application monitoring)")
        
        return True
        
    except Exception as e:
        print(f"\nERROR: Database setup failed: {e}")
        return False

async def test_database_operations():
    """Test various database operations"""
    print("\n" + "="*60)
    print("DATABASE OPERATIONS TEST")
    print("="*60)
    
    try:
        from backend.database import DatabaseManager
        
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        # Test 1: Forecast history
        print("\n[TEST 1] Forecast history:")
        history = await db_manager.get_forecast_history(days_back=7, limit=5)
        print(f"Found {len(history)} forecasts in last 7 days")
        for forecast in history:
            print(f"  - {forecast.generated_at}: {forecast.event_types} (confidence: {forecast.max_confidence:.1%})")
        
        # Test 2: Alert management
        print("\n[TEST 2] Alert management:")
        await db_manager.expire_old_alerts()  # Clean up expired alerts
        active_alerts = await db_manager.get_active_alerts()
        print(f"Active alerts: {len(active_alerts)}")
        
        # Test 3: System logging
        print("\n[TEST 3] System logging:")
        await db_manager.log_system_event(
            level="INFO",
            component="test_suite",
            message="Database operations test completed",
            details={"test_time": datetime.utcnow().isoformat()}
        )
        print("System log entry added")
        
        await db_manager.close()
        print("\nSUCCESS: All database operations working correctly")
        return True
        
    except Exception as e:
        print(f"\nERROR: Database operations test failed: {e}")
        return False

def install_dependencies():
    """Install required database dependencies"""
    print("Installing database dependencies...")
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements_database.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("SUCCESS: Dependencies installed")
            return True
        else:
            print(f"ERROR: Failed to install dependencies: {result.stderr}")
            return False
    except Exception as e:
        print(f"ERROR: Could not install dependencies: {e}")
        return False

async def main():
    """Main setup function"""
    print("NASA Space Weather Forecaster - Database Setup")
    print("This will create a SQLite database for storing space weather data")
    print()
    
    # Check if dependencies are installed
    try:
        import sqlalchemy
        import aiosqlite
        print("SUCCESS: Database dependencies are available")
    except ImportError:
        print("INFO: Installing required dependencies...")
        if not install_dependencies():
            print("FAILED: Could not install dependencies")
            return
    
    # Setup database
    if await setup_database():
        print("\nWould you like to run additional database operation tests?")
        test_choice = input("Run tests? (Y/n): ").lower()
        
        if test_choice != 'n':
            await test_database_operations()
        
        print("\n" + "="*60)
        print("NEXT STEPS")
        print("="*60)
        print("1. Database is ready for use")
        print("2. Restart API server to enable database features")
        print("3. Historical data will be automatically stored")
        print("4. Use database browser to view data:")
        print("   - DB Browser for SQLite (recommended)")
        print("   - VS Code SQLite extension")
        print(f"   - Database file: space_weather.db")
    else:
        print("\nDatabase setup failed. Please check error messages above.")

if __name__ == "__main__":
    asyncio.run(main())