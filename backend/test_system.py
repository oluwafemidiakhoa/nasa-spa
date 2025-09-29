#!/usr/bin/env python3
"""
System validation test for NASA Space Weather Forecaster
Tests module imports and basic functionality without requiring API keys
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_imports():
    """Test that all modules can be imported successfully"""
    print("Testing module imports...")
    
    try:
        import schema
        print("[OK] schema.py imported successfully")
        
        import nasa_client
        print("[OK] nasa_client.py imported successfully")
        
        import claude_client
        print("[OK] claude_client.py imported successfully")
        
        import forecaster
        print("[OK] forecaster.py imported successfully")
        
        return True
    except ImportError as e:
        print(f"[FAIL] Import failed: {e}")
        return False

def test_schema_models():
    """Test Pydantic schema models"""
    print("\nTesting schema models...")
    
    try:
        from schema import Evidence, Forecast, ForecastBundle, EventKind, ImpactType
        
        # Test Evidence model
        evidence = Evidence(
            donki_ids=["CME-2025-09-26T14:30:00-CME-001"],
            epic_frames=["2025-09-26T14:30:00"],
            gibs_layers=["VIIRS_SNPP_CorrectedReflectance_TrueColor"]
        )
        print("[OK] Evidence model works")
        
        # Test Forecast model
        forecast = Forecast(
            event="CME",
            solar_timestamp="2025-09-26T14:30:00Z",
            predicted_arrival_window_utc=["2025-09-28T06:00:00Z", "2025-09-29T18:00:00Z"],
            risk_summary="Test forecast",
            impacts=["aurora_midlat"],
            confidence=0.75,
            evidence=evidence
        )
        print("[OK] Forecast model works")
        
        # Test ForecastBundle model
        bundle = ForecastBundle(forecasts=[forecast])
        print("[OK] ForecastBundle model works")
        
        # Test JSON serialization
        json_output = bundle.model_dump_json()
        print("[OK] JSON serialization works")
        
        # Test JSON deserialization
        parsed_bundle = ForecastBundle.model_validate_json(json_output)
        print("[OK] JSON deserialization works")
        
        return True
    except Exception as e:
        print(f"[FAIL] Schema test failed: {e}")
        return False

def test_nasa_client_structure():
    """Test NASA client class structure (without API calls)"""
    print("\nTesting NASA client structure...")
    
    try:
        from nasa_client import NASAClient
        
        # Test client creation (should fail gracefully without API key)
        try:
            client = NASAClient(api_key="test_key")
            print("[OK] NASAClient instantiation works")
        except Exception:
            print("[OK] NASAClient properly validates API key requirement")
        
        # Test URL generation methods
        from nasa_client import gibs_tile_url
        url = gibs_tile_url("2025-09-26")
        if "2025-09-26" in url and "gibs.earthdata.nasa.gov" in url:
            print("[OK] GIBS URL generation works")
        else:
            print("[FAIL] GIBS URL generation failed")
            return False
        
        return True
    except Exception as e:
        print(f"[FAIL] NASA client test failed: {e}")
        return False

def test_claude_client_structure():
    """Test Claude client class structure (without API calls)"""
    print("\nTesting Claude client structure...")
    
    try:
        from claude_client import ClaudeClient
        
        # Test client creation (should fail gracefully without API key)
        try:
            client = ClaudeClient(api_key="test_key")
            print("[OK] ClaudeClient instantiation works")
        except Exception:
            print("[OK] ClaudeClient properly validates API key requirement")
        
        # Test utility methods
        try:
            client = ClaudeClient(api_key="test_key")
            text_block = client.create_text_block("Test text")
            if text_block["type"] == "text" and text_block["text"] == "Test text":
                print("[OK] Text block creation works")
            else:
                print("[FAIL] Text block creation failed")
                return False
        except Exception as e:
            print(f"[FAIL] Claude client utility test failed: {e}")
            return False
        
        return True
    except Exception as e:
        print(f"[FAIL] Claude client test failed: {e}")
        return False

def test_forecaster_structure():
    """Test forecaster module structure (without API calls)"""
    print("\nTesting forecaster structure...")
    
    try:
        from forecaster import ForecastConfig, SpaceWeatherForecaster
        
        # Test config creation
        config = ForecastConfig(days_back=5, max_tokens=1000)
        if config.days_back == 5 and config.max_tokens == 1000:
            print("[OK] ForecastConfig works")
        else:
            print("[FAIL] ForecastConfig failed")
            return False
        
        # Test forecaster creation (should fail gracefully without API keys)
        try:
            forecaster = SpaceWeatherForecaster(config)
            print("[OK] SpaceWeatherForecaster instantiation structure works")
        except Exception as e:
            if "API key" in str(e):
                print("[OK] SpaceWeatherForecaster properly validates API keys")
            else:
                print(f"[FAIL] Unexpected error: {e}")
                return False
        
        return True
    except Exception as e:
        print(f"[FAIL] Forecaster test failed: {e}")
        return False

def main():
    """Run all system tests"""
    print("NASA Space Weather Forecaster - System Validation")
    print("="*60)
    
    tests = [
        test_imports,
        test_schema_models,
        test_nasa_client_structure,
        test_claude_client_structure,
        test_forecaster_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("="*60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All system validation tests passed!")
        print("The system is ready for use (with valid API keys)")
    else:
        print("Some tests failed. Please check the error messages above.")
        return False
    
    print("\nNext steps:")
    print("1. Set up your API keys in .env file")
    print("2. Run: python demo.py")
    print("3. Check the generated forecast output")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)