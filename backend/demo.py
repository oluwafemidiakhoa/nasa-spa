#!/usr/bin/env python3
"""
Demo script for NASA Space Weather Forecaster
Demonstrates the complete forecasting pipeline
"""

import os
import sys
import json
from pathlib import Path
from typing import Union

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Load environment variables manually
def load_env_file(env_path):
    """Simple env file loader"""
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env_file(backend_dir.parent / ".env")

# Import our modules
from backend.forecaster import run_forecast, ForecastConfig, run_forecast_advanced
from backend.schema import ForecastBundle, ForecastError

def print_separator(title: str = ""):
    """Print a decorative separator"""
    if title:
        print(f"\n{'='*20} {title} {'='*20}")
    else:
        print("="*60)

def print_forecast_summary(forecast_bundle: ForecastBundle):
    """Print a human-readable summary of forecasts"""
    if not forecast_bundle.forecasts:
        print("[QUIET] No significant space weather events forecasted.")
        print("Current conditions appear quiet with minimal Earth-impact expected.")
        return
    
    print(f"[FORECAST] Generated {len(forecast_bundle.forecasts)} forecast(s)")
    print(f"[TIME] Analysis time: {forecast_bundle.generated_at}")
    print(f"[DATA] Data sources: {', '.join(forecast_bundle.data_sources)}")
    
    for i, forecast in enumerate(forecast_bundle.forecasts, 1):
        print(f"\n[FORECAST #{i}]")
        print(f"   Event Type: {forecast.event}")
        print(f"   Solar Event: {forecast.solar_timestamp}")
        print(f"   Earth Impact Window: {forecast.predicted_arrival_window_utc[0]} to {forecast.predicted_arrival_window_utc[1]}")
        print(f"   Confidence: {forecast.confidence:.1%}")
        print(f"   Risk Summary: {forecast.risk_summary}")
        print(f"   Impacts: {', '.join(forecast.impacts)}")
        print(f"   Evidence:")
        print(f"     - DONKI IDs: {', '.join(forecast.evidence.donki_ids)}")
        print(f"     - EPIC Frames: {', '.join(forecast.evidence.epic_frames)}")
        print(f"     - GIBS Layers: {', '.join(forecast.evidence.gibs_layers)}")

def print_error_details(error: ForecastError):
    """Print error information"""
    print(f"[ERROR] Forecast generation failed!")
    print(f"   Error: {error.error}")
    print(f"   Code: {error.error_code}")
    print(f"   Time: {error.timestamp}")

def check_api_keys():
    """Check if required API keys are available"""
    nasa_key = os.getenv("NASA_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    missing_keys = []
    if not nasa_key or nasa_key == "your_nasa_api_key_here":
        missing_keys.append("NASA_API_KEY")
    if not anthropic_key or anthropic_key == "your_anthropic_api_key_here":
        missing_keys.append("ANTHROPIC_API_KEY")
    
    if missing_keys:
        print("[WARNING] Missing API keys:")
        for key in missing_keys:
            print(f"   - {key}")
        print("\nPlease:")
        print("1. Copy .env.template to .env")
        print("2. Get NASA API key from: https://api.nasa.gov/")
        print("3. Get Anthropic API key from: https://console.anthropic.com/")
        print("4. Fill in your keys in the .env file")
        return False
    
    print("[SUCCESS] API keys found")
    return True

def demo_basic_forecast():
    """Run a basic forecast demo"""
    print_separator("BASIC FORECAST DEMO")
    
    if not check_api_keys():
        return
    
    print("[RUNNING] Basic space weather forecast...")
    print("   - Looking back 3 days for space weather events")
    print("   - Using today's EPIC Earth imagery")
    print("   - Standard analysis parameters")
    
    try:
        result = run_forecast(days_back=3)
        
        if isinstance(result, ForecastBundle):
            print_forecast_summary(result)
        else:
            print_error_details(result)
            
    except Exception as e:
        print(f"[ERROR] Demo failed with exception: {e}")

def demo_advanced_forecast():
    """Run an advanced forecast demo with custom configuration"""
    print_separator("ADVANCED FORECAST DEMO")
    
    if not check_api_keys():
        return
    
    print("[RUNNING] Advanced space weather forecast...")
    print("   - Looking back 5 days for space weather events")
    print("   - Including EPIC image analysis")
    print("   - Extended token limit for detailed analysis")
    
    config = ForecastConfig(
        days_back=5,
        max_events_per_source=8,
        max_epic_frames=5,
        include_images=True,
        max_tokens=2000
    )
    
    try:
        result = run_forecast_advanced(config)
        
        if isinstance(result, ForecastBundle):
            print_forecast_summary(result)
        else:
            print_error_details(result)
            
    except Exception as e:
        print(f"[ERROR] Advanced demo failed with exception: {e}")

def demo_json_output():
    """Demonstrate JSON output for automation"""
    print_separator("JSON OUTPUT DEMO")
    
    if not check_api_keys():
        return
        
    print("[GENERATING] JSON output for automation/API use...")
    
    try:
        result = run_forecast(days_back=2)
        
        if isinstance(result, ForecastBundle):
            json_output = result.model_dump_json(indent=2)
            print("Raw JSON output:")
            print(json_output)
            
            # Save to file
            output_file = backend_dir.parent / "forecast_output.json"
            with open(output_file, 'w') as f:
                f.write(json_output)
            print(f"\n[SAVED] JSON saved to: {output_file}")
            
        else:
            error_json = result.__dict__
            print("Error JSON:")
            print(json.dumps(error_json, indent=2))
            
    except Exception as e:
        print(f"[ERROR] JSON demo failed with exception: {e}")

def main():
    """Main demo function"""
    print_separator("NASA SPACE WEATHER FORECASTER")
    print("Space Weather Helio->Earth Emergence Forecaster Demo")
    print("Using NASA DONKI + EPIC + GIBS data with Claude AI analysis")
    
    # Run all demos
    demo_basic_forecast()
    demo_advanced_forecast()
    demo_json_output()
    
    print_separator("DEMO COMPLETE")
    print("[SUCCESS] Demo completed!")
    print("\nNext steps:")
    print("- Review forecast_output.json for automation integration")
    print("- Customize ForecastConfig for your specific needs")
    print("- Build web interface using forecast JSON output")
    print("- Set up automated forecasting with cron/scheduler")

if __name__ == "__main__":
    main()