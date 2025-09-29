#!/usr/bin/env python3
"""
Simple NASA Space Weather API Server
Minimal working version
"""

import os
import json
import requests
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI
app = FastAPI(title="NASA Space Weather API", version="1.0.0")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get API key
NASA_API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")

@app.get("/api/v1/health")
async def health():
    return {
        "success": True,
        "data": {"status": "healthy", "service": "space-weather-api"},
        "error": None,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/api/v1/forecasts/current")
async def current_forecast():
    try:
        # Try to get NASA data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)
        
        try:
            cme_url = "https://api.nasa.gov/DONKI/CME"
            params = {
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "api_key": NASA_API_KEY
            }
            response = requests.get(cme_url, params=params, timeout=10)
            cme_count = len(response.json()) if response.status_code == 200 else 0
        except:
            cme_count = 0
        
        # Generate simple forecast
        if cme_count >= 3:
            title = "High Space Weather Activity"
            description = f"Detected {cme_count} CMEs. Increased aurora activity expected."
            confidence = 0.8
        elif cme_count >= 1:
            title = "Moderate Space Weather Activity" 
            description = f"Detected {cme_count} CME(s). Possible aurora at high latitudes."
            confidence = 0.6
        else:
            title = "Quiet Space Weather"
            description = "No significant events detected. Normal conditions."
            confidence = 0.9
        
        forecast = {
            "id": f"forecast_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": title,
            "description": description,
            "confidence": confidence,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "source": "nasa_donki"
        }
        
        return {
            "success": True,
            "data": {
                "forecast": forecast,
                "generated_at": forecast["generated_at"],
                "source": forecast["source"]
            },
            "error": None,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/forecasts/generate")
async def generate_forecast():
    return await current_forecast()

@app.get("/")
async def root():
    return {"message": "NASA Space Weather API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)