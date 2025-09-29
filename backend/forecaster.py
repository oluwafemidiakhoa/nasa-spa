"""
Main orchestration module for NASA Space Weather Forecaster
Combines NASA data sources with Claude AI for structured forecasting
"""

import json
import datetime as dt
from typing import Dict, Any, List, Union, Optional
from dataclasses import dataclass

# Import our modules
from backend.schema import ForecastBundle, ForecastError
from backend.nasa_client import NASAClient
from backend.claude_client import ClaudeClient

@dataclass
class ForecastConfig:
    """Configuration for forecast generation"""
    days_back: int = 3
    max_events_per_source: int = 5
    max_epic_frames: int = 3
    epic_date_iso: Optional[str] = None
    claude_model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 1500
    include_images: bool = False

class SpaceWeatherForecaster:
    """Main forecaster class that orchestrates data collection and AI analysis"""
    
    def __init__(self, config: ForecastConfig = None):
        self.config = config or ForecastConfig()
        self.nasa_client = NASAClient()
        self.claude_client = ClaudeClient(model=self.config.claude_model)
        
    def _prepare_nasa_data(self) -> Dict[str, Any]:
        """Collect and prepare NASA data for analysis"""
        print("Fetching NASA space weather data...")
        
        # Get space weather events
        space_weather = self.nasa_client.get_all_space_weather_events(self.config.days_back)
        
        # Get EPIC Earth imagery
        epic_date = self.config.epic_date_iso or dt.date.today().isoformat()
        epic_data = self.nasa_client.fetch_epic_date(epic_date)
        
        # Limit data to prevent token overflow
        limited_data = {
            "cmes": space_weather["cmes"][:self.config.max_events_per_source],
            "flares": space_weather["flares"][:self.config.max_events_per_source],
            "sep_events": space_weather["sep_events"][:self.config.max_events_per_source],
            "geomagnetic_storms": space_weather["geomagnetic_storms"][:self.config.max_events_per_source],
            "epic_frames": epic_data[:self.config.max_epic_frames],
            "epic_date": epic_date
        }
        
        print(f"Retrieved {len(limited_data['cmes'])} CMEs, {len(limited_data['flares'])} flares, "
              f"{len(limited_data['sep_events'])} SEP events, {len(limited_data['geomagnetic_storms'])} storms, "
              f"{len(limited_data['epic_frames'])} EPIC frames")
        
        return limited_data

    def _build_system_prompt(self) -> str:
        """Create the system prompt for Claude"""
        return """You are a space weather analyst with expertise in solar-terrestrial physics. 
Your task is to analyze NASA space weather data and Earth imagery to forecast potential Earth-side impacts.

CRITICAL INSTRUCTIONS:
1. Return ONLY valid JSON following the ForecastBundle schema
2. Link ALL claims to specific DONKI event IDs and imagery timestamps
3. If uncertainty is high, widen the arrival window and reflect lower confidence
4. Be scientifically accurate and conservative in your predictions
5. Never hallucinate event IDs - only cite data provided to you
6. Provide 0-3 forecasts maximum based on significant events only

ANALYSIS APPROACH:
- Assess if CMEs are Earth-directed based on location and trajectory
- Consider flare intensity and associated CME likelihood
- Factor in current geomagnetic conditions
- Estimate arrival times using typical solar wind transit speeds (400-800 km/s)
- Evaluate potential impacts on technology and aurora visibility"""

    def _build_user_blocks(self, nasa_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build user content blocks for Claude"""
        blocks = []
        
        # Add task instructions
        blocks.append({
            "type": "text", 
            "text": """SPACE WEATHER ANALYSIS TASK:
1) Review the provided DONKI events and identify Earth-directed or geo-effective phenomena
2) Assess timing: estimate arrival windows for significant events
3) Evaluate impacts: aurora reach, communications, GNSS, satellite operations
4) Assign confidence based on data quality and event characteristics
5) Cite specific DONKI IDs and EPIC timestamps as evidence

FORECAST RULES:
- Only forecast events with significant Earth impact potential
- Use conservative confidence estimates for uncertain events
- Provide empty forecasts array if no significant events are found
- Include arrival time windows accounting for solar wind speed variability"""
        })
        
        # Add DONKI data sections
        if nasa_data["cmes"]:
            blocks.append({
                "type": "text",
                "text": f"DONKI CME DATA:\n{json.dumps(nasa_data['cmes'], indent=2, ensure_ascii=False)}"
            })
        
        if nasa_data["flares"]:
            blocks.append({
                "type": "text", 
                "text": f"DONKI FLARE DATA:\n{json.dumps(nasa_data['flares'], indent=2, ensure_ascii=False)}"
            })
            
        if nasa_data["sep_events"]:
            blocks.append({
                "type": "text",
                "text": f"DONKI SEP EVENTS:\n{json.dumps(nasa_data['sep_events'], indent=2, ensure_ascii=False)}"
            })
            
        if nasa_data["geomagnetic_storms"]:
            blocks.append({
                "type": "text",
                "text": f"DONKI GEOMAGNETIC STORMS:\n{json.dumps(nasa_data['geomagnetic_storms'], indent=2, ensure_ascii=False)}"
            })
        
        # Add EPIC data
        if nasa_data["epic_frames"]:
            blocks.append({
                "type": "text",
                "text": f"EPIC EARTH IMAGERY ({nasa_data['epic_date']}):\n{json.dumps(nasa_data['epic_frames'], indent=2, ensure_ascii=False)}"
            })
            
            # Add EPIC image URLs if requested
            if self.config.include_images and nasa_data["epic_frames"]:
                for frame in nasa_data["epic_frames"][:2]:  # Limit to 2 images
                    image_url = self.nasa_client.get_epic_image_url(frame, "png")
                    if image_url:
                        blocks.append({
                            "type": "text",
                            "text": f"EPIC Image URL: {image_url}"
                        })
        
        # Add GIBS reference
        gibs_url = self.nasa_client.gibs_tile_url(nasa_data["epic_date"])
        blocks.append({
            "type": "text",
            "text": f"GIBS EARTH TILES URL TEMPLATE:\n{gibs_url}"
        })
        
        return blocks

    def generate_forecast(self) -> Union[ForecastBundle, ForecastError]:
        """Generate a complete space weather forecast"""
        try:
            # Prepare NASA data
            nasa_data = self._prepare_nasa_data()
            
            # Check if we have any significant data
            total_events = (len(nasa_data["cmes"]) + len(nasa_data["flares"]) + 
                          len(nasa_data["sep_events"]) + len(nasa_data["geomagnetic_storms"]))
            
            if total_events == 0:
                print("No significant space weather events found in the specified time period.")
                return ForecastBundle(forecasts=[])
            
            # Build prompts
            system_prompt = self._build_system_prompt()
            user_blocks = self._build_user_blocks(nasa_data)
            
            print("Analyzing data with Claude AI...")
            
            # Generate forecast using Claude
            result = self.claude_client.generate_forecast_with_schema(
                system_prompt=system_prompt,
                user_blocks=user_blocks,
                schema_model=ForecastBundle,
                max_tokens=self.config.max_tokens
            )
            
            # Check if we got an error
            if isinstance(result, dict) and "error" in result:
                return ForecastError(
                    error=result["error"],
                    error_code="CLAUDE_GENERATION_FAILED",
                    timestamp=dt.datetime.utcnow().isoformat() + "Z"
                )
            
            print(f"Successfully generated {len(result.forecasts)} forecast(s)")
            return result
            
        except Exception as e:
            print(f"Forecast generation failed: {e}")
            return ForecastError(
                error=str(e),
                error_code="FORECAST_GENERATION_FAILED",
                timestamp=dt.datetime.utcnow().isoformat() + "Z"
            )

# Convenience function for simple usage
def run_forecast(days_back: int = 3, epic_date_iso: str = None, include_images: bool = False) -> Union[ForecastBundle, ForecastError]:
    """
    Simple function to run a space weather forecast
    
    Args:
        days_back: Number of days to look back for space weather events
        epic_date_iso: Specific date for EPIC imagery (ISO format), defaults to today
        include_images: Whether to include EPIC image URLs in analysis
        
    Returns:
        ForecastBundle with forecasts or ForecastError if failed
    """
    config = ForecastConfig(
        days_back=days_back,
        epic_date_iso=epic_date_iso,
        include_images=include_images
    )
    
    forecaster = SpaceWeatherForecaster(config)
    return forecaster.generate_forecast()

# Advanced configuration function
def run_forecast_advanced(config: ForecastConfig) -> Union[ForecastBundle, ForecastError]:
    """Run forecast with advanced configuration options"""
    forecaster = SpaceWeatherForecaster(config)
    return forecaster.generate_forecast()