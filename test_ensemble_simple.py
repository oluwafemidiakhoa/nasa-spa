#!/usr/bin/env python3
"""
Simple test for ensemble forecasting system
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append('.')
sys.path.append('backend')

def test_ensemble_forecasting():
    """Test ensemble forecasting system"""
    print("TESTING ENSEMBLE FORECASTING SYSTEM")
    print("=" * 50)
    
    try:
        print("1. Testing ensemble forecaster import...")
        from backend.ensemble_forecaster import EnsembleSpaceWeatherForecaster
        print("   [OK] Ensemble forecaster imported")
        
        print("2. Initializing ensemble forecaster...")
        ensemble = EnsembleSpaceWeatherForecaster()
        print("   [OK] Ensemble forecaster initialized")
        
        print("3. Testing ML forecaster component...")
        if hasattr(ensemble, 'ml_forecaster'):
            print("   [OK] ML forecaster available")
        else:
            print("   [WARNING] ML forecaster not available")
        
        print("4. Testing neural forecaster component...")
        if hasattr(ensemble, 'neural_forecaster') and ensemble.neural_available:
            print("   [OK] Neural forecaster available")
        else:
            print("   [WARNING] Neural forecaster not available")
        
        print("5. Testing performance tracker...")
        if hasattr(ensemble, 'performance_tracker'):
            print("   [OK] Performance tracker available")
        else:
            print("   [WARNING] Performance tracker not available")
        
        print("\nEnsemble forecasting system status: READY")
        return True
        
    except Exception as e:
        print(f"   [ERROR] Ensemble forecasting test failed: {e}")
        return False

def test_expert_integration():
    """Test expert forecaster ensemble integration"""
    print("\nTESTING EXPERT FORECASTER INTEGRATION")
    print("=" * 50)
    
    try:
        print("1. Testing expert forecaster import...")
        from backend.expert_forecaster import ExpertSpaceWeatherForecaster
        print("   [OK] Expert forecaster imported")
        
        print("2. Initializing expert forecaster...")
        expert = ExpertSpaceWeatherForecaster()
        print("   [OK] Expert forecaster initialized")
        
        print("3. Checking ensemble integration...")
        if hasattr(expert, 'ensemble_forecaster'):
            print("   [OK] Ensemble forecaster integrated")
        else:
            print("   [ERROR] Ensemble forecaster not integrated")
            return False
        
        print("\nExpert forecaster ensemble integration: ACTIVE")
        return True
        
    except Exception as e:
        print(f"   [ERROR] Expert integration test failed: {e}")
        return False

def test_historical_database():
    """Test historical database availability"""
    print("\nTESTING HISTORICAL DATABASE")
    print("=" * 50)
    
    try:
        import sqlite3
        from pathlib import Path
        
        db_path = Path("data/historical/space_weather_history.db")
        
        if db_path.exists():
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT COUNT(*) FROM historical_events")
            count = cursor.fetchone()[0]
            conn.close()
            
            print(f"   [OK] Historical database found with {count} events")
            return True
        else:
            print("   [WARNING] Historical database not found")
            return False
            
    except Exception as e:
        print(f"   [ERROR] Database test failed: {e}")
        return False

def main():
    """Main test function"""
    print("NASA SPACE WEATHER ENSEMBLE SYSTEM TEST")
    print("=" * 60)
    
    results = []
    
    # Test ensemble forecasting
    results.append(test_ensemble_forecasting())
    
    # Test expert integration
    results.append(test_expert_integration())
    
    # Test historical database
    results.append(test_historical_database())
    
    print("\nTEST SUMMARY")
    print("=" * 30)
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("STATUS: ENSEMBLE FORECASTING SYSTEM READY")
        return True
    else:
        print("STATUS: SOME COMPONENTS NEED ATTENTION")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)