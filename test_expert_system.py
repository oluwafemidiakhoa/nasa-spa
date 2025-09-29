#!/usr/bin/env python3
"""
Test the NASA-grade expert space weather forecasting system
"""

import os
import sys
import json
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Load environment variables
def load_env_file(env_path):
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env_file(".env")

# Import modules with absolute imports
from backend.space_physics import SpaceWeatherPhysics, CMEParameters, create_solar_wind_sample
from backend.realtime_data import get_realtime_space_weather
from backend.nasa_client import NASAClient

def test_physics_engine():
    """Test the advanced physics models"""
    print("TESTING NASA-GRADE SPACE WEATHER PHYSICS ENGINE")
    print("=" * 60)
    
    physics = SpaceWeatherPhysics()
    
    # Create sample CME parameters
    from datetime import datetime, timedelta
    sample_cme = CMEParameters(
        initial_velocity=800.0,
        angular_width=60.0,
        mass=1e15,
        magnetic_field_strength=15.0,
        launch_time=datetime.utcnow() - timedelta(hours=12),
        source_location=(0, 0)
    )
    
    print(f"CME Parameters:")
    print(f"   Velocity: {sample_cme.initial_velocity} km/s")
    print(f"   Angular Width: {sample_cme.angular_width} degrees")
    print(f"   Launch Time: {sample_cme.launch_time}")
    
    # Test CME arrival prediction
    print(f"\nCME ARRIVAL PREDICTION (Drag-Based Model)")
    arrival = physics.predict_cme_arrival(sample_cme)
    print(f"   Predicted Arrival: {arrival['predicted_arrival']}")
    print(f"   Transit Time: {arrival['transit_time_hours']:.1f} hours")
    print(f"   Final Velocity: {arrival['final_velocity']:.0f} km/s")
    print(f"   Confidence: {arrival['confidence']:.0%}")
    
    # Test geoeffectiveness analysis
    print(f"\nGEOEFFECTIVENESS ANALYSIS")
    geo = physics.analyze_cme_geoeffectiveness(sample_cme)
    print(f"   Geoeffectiveness Score: {geo['geoeffectiveness_score']:.2f}")
    print(f"   Classification: {geo['classification']}")
    print(f"   Earth Impact Probability: {geo['earth_impact_probability']:.0%}")
    
    # Test geomagnetic predictions
    print(f"\nGEOMAGNETIC PREDICTIONS")
    solar_wind = create_solar_wind_sample()
    dst = physics.calculate_dst_index(solar_wind)
    kp = physics.predict_kp_index(solar_wind)
    
    print(f"   Solar Wind: {solar_wind.velocity} km/s, Bz={solar_wind.bz_gsm} nT")
    print(f"   Dst Index: {dst['dst_index']:.0f} nT ({dst['storm_level']} storm)")
    print(f"   Kp Index: {kp['kp_index']:.0f} ({kp['activity_level']})")
    
    # Test aurora predictions
    print(f"\nAURORA VISIBILITY FORECAST")
    aurora = physics.calculate_aurora_boundary(kp['kp_index'])
    print(f"   Aurora Boundary: {aurora['geographic_latitude_boundary']:.1f} degrees latitude")
    print(f"   Visible Cities: {', '.join(aurora['cities_visible'][:5])}")
    print(f"   Visibility Quality: {aurora['visibility_quality']}")
    
    return True

def test_realtime_data():
    """Test real-time data integration"""
    print(f"\nTESTING REAL-TIME SPACE WEATHER DATA")
    print("=" * 60)
    
    try:
        data = get_realtime_space_weather()
        
        print(f"Real-time Data Sources:")
        print(f"   Solar Wind: {data['solar_wind']['source']}")
        print(f"   Geomagnetic: {data['geomagnetic']['source']}")
        print(f"   X-ray Flux: {data['xray_flux']['source']}")
        
        print(f"\nCurrent Conditions:")
        print(f"   Solar Wind Speed: {data['solar_wind']['velocity']:.0f} km/s")
        print(f"   Kp Index: {data['geomagnetic']['kp_index']:.1f}")
        print(f"   Solar Flare Class: {data['xray_flux']['flare_class']}")
        print(f"   Overall Condition: {data['summary']['overall_condition']}")
        
        if data['summary']['concerns']:
            print(f"   Concerns: {', '.join(data['summary']['concerns'])}")
        
        return True
        
    except Exception as e:
        print(f"Real-time data test failed: {e}")
        return False

def test_nasa_integration():
    """Test NASA DONKI integration"""
    print(f"\nTESTING NASA DONKI INTEGRATION")
    print("=" * 60)
    
    try:
        nasa = NASAClient()
        
        # Test DONKI CME data
        cmes = nasa.fetch_donki_cmes(days_back=3)
        flares = nasa.fetch_donki_flares(days_back=3)
        
        print(f"NASA Data Retrieved:")
        print(f"   CME Events: {len(cmes)}")
        print(f"   Solar Flares: {len(flares)}")
        
        if cmes:
            latest_cme = cmes[0]
            print(f"\nLatest CME Event:")
            print(f"   Activity ID: {latest_cme.get('activityID', 'N/A')}")
            print(f"   Start Time: {latest_cme.get('startTime', 'N/A')}")
            
        if flares:
            latest_flare = flares[0]
            print(f"\nLatest Solar Flare:")
            print(f"   Activity ID: {latest_flare.get('flrID', 'N/A')}")
            print(f"   Class Type: {latest_flare.get('classType', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"NASA integration test failed: {e}")
        return False

def main():
    """Run comprehensive system test"""
    print("NASA EXPERT SPACE WEATHER FORECASTER - SYSTEM TEST")
    print("Physics Engine + Real-Time Data + AI Analysis")
    print("=" * 70)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Physics Engine
    if test_physics_engine():
        tests_passed += 1
        print("Physics Engine: PASSED")
    else:
        print("Physics Engine: FAILED")
    
    # Test 2: Real-time Data
    if test_realtime_data():
        tests_passed += 1
        print("Real-time Data: PASSED")
    else:
        print("Real-time Data: FAILED")
    
    # Test 3: NASA Integration
    if test_nasa_integration():
        tests_passed += 1
        print("NASA Integration: PASSED")
    else:
        print("NASA Integration: FAILED")
    
    print(f"\nSYSTEM TEST RESULTS")
    print("=" * 30)
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("ALL SYSTEMS OPERATIONAL - NASA-GRADE FORECASTER READY!")
        print("Ready to 'WOW NASA' with expert-level space weather analysis!")
    else:
        print("Some systems need attention")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)