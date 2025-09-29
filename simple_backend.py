#!/usr/bin/env python3
"""
Simple NASA Space Weather API Server
A minimal working version for demonstration
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Initialize FastAPI
app = FastAPI(
    title="NASA Space Weather API",
    description="Simple space weather forecasting API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get API keys from environment
NASA_API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Simple models
class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str

class SimpleForecast(BaseModel):
    id: str
    title: str
    description: str
    confidence: float
    generated_at: str
    source: str

class ForecastResponse(BaseModel):
    forecast: SimpleForecast
    generated_at: str
    source: str

# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "service": "space-weather-api"
        },
        "error": None,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

# Simple NASA data fetcher
def fetch_nasa_data() -> Dict[str, Any]:
    """Fetch basic space weather data from NASA DONKI"""
    try:
        # Get CME data (last 3 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)
        
        cme_url = "https://api.nasa.gov/DONKI/CME"
        params = {
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d"),
            "api_key": NASA_API_KEY
        }
        
        response = requests.get(cme_url, params=params, timeout=10)
        if response.status_code == 200:
            cmes = response.json()
            return {
                "cmes": len(cmes),
                "data": cmes[:3],  # Just first 3 for demo
                "status": "success"
            }
        else:
            return {
                "cmes": 0,
                "data": [],
                "status": "api_error",
                "error": f"NASA API returned {response.status_code}"
            }
    
    except Exception as e:
        return {
            "cmes": 0,
            "data": [],
            "status": "error",
            "error": str(e)
        }

# Generate simple forecast
def generate_simple_forecast(nasa_data: Dict[str, Any]) -> SimpleForecast:
    """Generate a simple forecast based on NASA data"""
    
    # Simple logic based on CME count
    cme_count = nasa_data.get("cmes", 0)
    
    if cme_count >= 3:
        title = "High Space Weather Activity"
        description = f"Detected {cme_count} Coronal Mass Ejections in the last 3 days. Increased aurora activity and potential minor GPS/communication impacts expected."
        confidence = 0.8
    elif cme_count >= 1:
        title = "Moderate Space Weather Activity"
        description = f"Detected {cme_count} Coronal Mass Ejection(s) in recent days. Possible aurora visibility at higher latitudes."
        confidence = 0.6
    else:
        title = "Quiet Space Weather"
        description = "No significant space weather events detected. Normal conditions expected."
        confidence = 0.9
    
    return SimpleForecast(
        id=f"forecast_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        title=title,
        description=description,
        confidence=confidence,
        generated_at=datetime.utcnow().isoformat() + "Z",
        source="nasa_donki"
    )

# Current forecast endpoint
@app.get("/api/v1/forecasts/current")
async def get_current_forecast():
    """Get current space weather forecast"""
    try:
        # Fetch NASA data
        nasa_data = fetch_nasa_data()
        
        # Generate forecast
        forecast = generate_simple_forecast(nasa_data)
        
        return {
            "success": True,
            "data": ForecastResponse(
                forecast=forecast,
                generated_at=forecast.generated_at,
                source=forecast.source
            ),
            "error": None,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating forecast: {str(e)}")

# Generate new forecast endpoint
@app.post("/api/v1/forecasts/generate")
async def generate_forecast():
    """Generate a new space weather forecast"""
    return await get_current_forecast()

# NASA data endpoint
@app.get("/api/v1/nasa/status")
async def nasa_status():
    """Get NASA API status and recent data"""
    nasa_data = fetch_nasa_data()
    
    return {
        "success": True,
        "data": {
            "api_status": nasa_data.get("status", "unknown"),
            "cme_count": nasa_data.get("cmes", 0),
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "error": nasa_data.get("error")
        },
        "error": None,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")