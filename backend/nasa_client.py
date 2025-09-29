"""
NASA API client for Space Weather Forecaster
Handles data fetching from DONKI, EPIC, and GIBS services
"""

import os
import datetime as dt
import requests
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Load environment variables
NASA_KEY = os.getenv("NASA_API_KEY")

@dataclass
class APIResponse:
    """Wrapper for API response with metadata"""
    data: Any
    status_code: int
    timestamp: str
    source: str

class NASAClient:
    """Client for NASA space weather and Earth observation APIs"""
    
    def __init__(self, api_key: Optional[str] = None, rate_limit_delay: float = 0.1):
        self.api_key = api_key or NASA_KEY
        self.rate_limit_delay = rate_limit_delay
        self.base_urls = {
            "donki": "https://api.nasa.gov/DONKI",
            "epic": "https://api.nasa.gov/EPIC/api/natural",
            "gibs": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best"
        }
        
        if not self.api_key:
            raise ValueError("NASA API key is required. Set NASA_API_KEY environment variable.")
    
    def _make_request(self, url: str, params: Dict[str, Any], source: str) -> APIResponse:
        """Make rate-limited API request with error handling"""
        try:
            time.sleep(self.rate_limit_delay)  # Simple rate limiting
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            return APIResponse(
                data=response.json(),
                status_code=response.status_code,
                timestamp=dt.datetime.utcnow().isoformat() + "Z",
                source=source
            )
        except requests.exceptions.RequestException as e:
            print(f"API request failed for {source}: {e}")
            return APIResponse(
                data=[],
                status_code=getattr(e.response, 'status_code', 0) if hasattr(e, 'response') else 0,
                timestamp=dt.datetime.utcnow().isoformat() + "Z",
                source=source
            )

    def fetch_donki_cmes(self, days_back: int = 3) -> List[Dict[str, Any]]:
        """Fetch Coronal Mass Ejection events from DONKI"""
        end = dt.date.today()
        start = end - dt.timedelta(days=days_back)
        
        url = f"{self.base_urls['donki']}/CME"
        params = {
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "api_key": self.api_key
        }
        
        response = self._make_request(url, params, "DONKI_CME")
        return response.data if isinstance(response.data, list) else []

    def fetch_donki_flares(self, days_back: int = 3) -> List[Dict[str, Any]]:
        """Fetch Solar Flare events from DONKI"""
        end = dt.date.today()
        start = end - dt.timedelta(days=days_back)
        
        url = f"{self.base_urls['donki']}/FLR"
        params = {
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "api_key": self.api_key
        }
        
        response = self._make_request(url, params, "DONKI_FLR")
        return response.data if isinstance(response.data, list) else []

    def fetch_donki_sep_events(self, days_back: int = 3) -> List[Dict[str, Any]]:
        """Fetch Solar Energetic Particle events from DONKI"""
        end = dt.date.today()
        start = end - dt.timedelta(days=days_back)
        
        url = f"{self.base_urls['donki']}/SEP"
        params = {
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "api_key": self.api_key
        }
        
        response = self._make_request(url, params, "DONKI_SEP")
        return response.data if isinstance(response.data, list) else []

    def fetch_donki_geomagnetic_storms(self, days_back: int = 3) -> List[Dict[str, Any]]:
        """Fetch Geomagnetic Storm events from DONKI"""
        end = dt.date.today()
        start = end - dt.timedelta(days=days_back)
        
        url = f"{self.base_urls['donki']}/GST"
        params = {
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "api_key": self.api_key
        }
        
        response = self._make_request(url, params, "DONKI_GST")
        return response.data if isinstance(response.data, list) else []

    def fetch_epic_date(self, date_iso: str) -> List[Dict[str, Any]]:
        """Fetch EPIC Earth imagery list for a given date (UTC)"""
        url = f"{self.base_urls['epic']}/date/{date_iso}"
        params = {"api_key": self.api_key}
        
        response = self._make_request(url, params, "EPIC")
        return response.data if isinstance(response.data, list) else []

    def fetch_epic_recent(self, days_back: int = 1) -> List[Dict[str, Any]]:
        """Fetch recent EPIC imagery within the last N days"""
        date = dt.date.today() - dt.timedelta(days=days_back)
        return self.fetch_epic_date(date.isoformat())

    def get_epic_image_url(self, epic_data: Dict[str, Any], size: str = "png") -> str:
        """Generate EPIC image URL from EPIC metadata"""
        identifier = epic_data.get("identifier", "")
        date = epic_data.get("date", "")
        
        if not identifier or not date:
            return ""
        
        # Parse date to get year/month/day
        try:
            parsed_date = dt.datetime.fromisoformat(date.replace("Z", "+00:00"))
            year = parsed_date.year
            month = str(parsed_date.month).zfill(2)
            day = str(parsed_date.day).zfill(2)
            
            return f"https://api.nasa.gov/EPIC/archive/natural/{year}/{month}/{day}/{size}/{identifier}.{size}?api_key={self.api_key}"
        except (ValueError, TypeError):
            return ""

    def gibs_tile_url(self, time_iso: str, layer: str = "VIIRS_SNPP_CorrectedReflectance_TrueColor") -> str:
        """Generate GIBS WMTS template URL with TIME filled for convenience"""
        return (
            f"{self.base_urls['gibs']}/"
            f"{layer}/default/"
            f"{time_iso}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.jpg"
        )

    def get_all_space_weather_events(self, days_back: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch all space weather events from the last N days"""
        return {
            "cmes": self.fetch_donki_cmes(days_back),
            "flares": self.fetch_donki_flares(days_back),
            "sep_events": self.fetch_donki_sep_events(days_back),
            "geomagnetic_storms": self.fetch_donki_geomagnetic_storms(days_back)
        }

# Convenience functions for backward compatibility
def fetch_donki_cmes(days_back: int = 3) -> List[Dict[str, Any]]:
    """Convenience function for fetching CMEs"""
    client = NASAClient()
    return client.fetch_donki_cmes(days_back)

def fetch_donki_flares(days_back: int = 3) -> List[Dict[str, Any]]:
    """Convenience function for fetching flares"""
    client = NASAClient()
    return client.fetch_donki_flares(days_back)

def fetch_epic_date(date_iso: str) -> List[Dict[str, Any]]:
    """Convenience function for fetching EPIC data"""
    client = NASAClient()
    return client.fetch_epic_date(date_iso)

def gibs_tile_url(time_iso: str) -> str:
    """Convenience function for GIBS URL generation"""
    client = NASAClient()
    return client.gibs_tile_url(time_iso)