#!/usr/bin/env python3
"""
Working demo of NASA Space Weather Forecaster with OpenAI
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

def main():
    print("NASA SPACE WEATHER FORECASTER - WORKING DEMO")
    print("=" * 60)
    print("Using OpenAI GPT-4 for space weather analysis")
    print()
    
    try:
        # Import the universal forecaster
        from backend.universal_forecaster import run_universal_forecast
        
        print("🔍 Fetching space weather data from NASA DONKI...")
        print("🤖 Analyzing with OpenAI GPT-4...")
        print("📊 Generating structured forecast...")
        print()
        
        # Generate forecast using OpenAI
        result = run_universal_forecast(
            days_back=3,           # Look back 3 days
            ai_provider="openai",  # Force OpenAI (since Claude has issues)
            max_tokens=1200        # Allow detailed analysis
        )
        
        # Display results
        if hasattr(result, 'forecasts'):
            print("✅ FORECAST GENERATED SUCCESSFULLY!")
            print(f"📅 Generated at: {result.generated_at}")
            print(f"📊 Data sources: {', '.join(result.data_sources)}")
            print(f"🔮 Number of forecasts: {len(result.forecasts)}")
            print()
            
            if result.forecasts:
                for i, forecast in enumerate(result.forecasts, 1):
                    print(f"🌞 FORECAST #{i}")
                    print(f"   Event Type: {forecast.event}")
                    print(f"   Solar Event Time: {forecast.solar_timestamp}")
                    print(f"   Earth Impact Window: {forecast.predicted_arrival_window_utc[0]} to {forecast.predicted_arrival_window_utc[1]}")
                    print(f"   Confidence: {forecast.confidence:.1%}")
                    print(f"   Risk Summary: {forecast.risk_summary}")
                    print(f"   Potential Impacts: {', '.join(forecast.impacts)}")
                    print(f"   Evidence Sources: {len(forecast.evidence.donki_ids)} DONKI events")
                    print()
            else:
                print("🌤️  QUIET CONDITIONS")
                print("   No significant space weather events forecasted.")
                print("   Current conditions appear quiet with minimal Earth impact expected.")
                print()
            
            # Save to file
            output_file = "forecast_output.json"
            with open(output_file, 'w') as f:
                f.write(result.model_dump_json(indent=2))
            print(f"💾 Forecast saved to: {output_file}")
            print()
            
        elif hasattr(result, 'error'):
            print(f"❌ FORECAST ERROR: {result.error}")
            print(f"🔧 Error Code: {result.error_code}")
        
        print("🎉 DEMO COMPLETE!")
        print()
        print("Next steps:")
        print("- Review the JSON output for automation integration")
        print("- Customize forecast parameters as needed") 
        print("- Build web interface using the forecast data")
        print("- Set up automated forecasting with scheduling")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print()
        print("Troubleshooting:")
        print("- Check your OpenAI API key in .env file")
        print("- Ensure internet connection for NASA and OpenAI APIs")
        print("- Verify all dependencies are installed")

if __name__ == "__main__":
    main()