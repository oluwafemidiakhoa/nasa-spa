"""
Vercel deployment entrypoint for NASA Space Weather Forecaster
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Environment setup for Vercel
os.environ.setdefault('ENVIRONMENT', 'production')

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any

# Simplified imports for Vercel deployment
try:
    from backend.forecaster import run_forecast
    from backend.schema import ForecastBundle
except ImportError:
    # Fallback for missing dependencies
    run_forecast = None
    ForecastBundle = None

class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str = datetime.utcnow().isoformat() + "Z"

# Create FastAPI app for Vercel
app = FastAPI(
    title="NASA Space Weather Forecaster",
    description="Real-time space weather forecasting using NASA data and AI analysis",
    version="2.0.0"
)

# Enable CORS for all origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint with basic info"""
    return {
        "name": "NASA Space Weather Forecaster",
        "version": "2.0.0",
        "status": "online",
        "description": "Real-time space weather forecasting using NASA data and AI analysis",
        "endpoints": {
            "health": "/health",
            "forecast": "/api/forecast",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return APIResponse(
        success=True, 
        data={
            "status": "healthy", 
            "service": "nasa-space-weather-api",
            "environment": os.getenv("ENVIRONMENT", "production")
        }
    )

@app.get("/api/forecast")
async def get_forecast():
    """Get space weather forecast - simplified for Vercel"""
    try:
        # Check if we have the full forecasting system available
        if run_forecast is None:
            # Return a demo forecast structure if full system not available
            return APIResponse(
                success=True,
                data={
                    "forecast": {
                        "forecasts": [
                            {
                                "event": "CME",
                                "solar_timestamp": datetime.utcnow().isoformat() + "Z",
                                "predicted_arrival_window_utc": [
                                    (datetime.utcnow()).isoformat() + "Z",
                                    (datetime.utcnow()).isoformat() + "Z"
                                ],
                                "risk_summary": "Demo mode - full forecasting system not available in this deployment",
                                "impacts": ["system_demo"],
                                "confidence": 0.5,
                                "evidence": {
                                    "donki_ids": ["demo"],
                                    "epic_frames": ["demo"],
                                    "gibs_layers": ["demo"]
                                }
                            }
                        ]
                    },
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "source": "demo_mode",
                    "note": "This is a demo deployment. Full functionality requires environment setup."
                }
            )
        
        # Try to run actual forecast if system is available
        result = run_forecast(days_back=3)
        
        if isinstance(result, ForecastBundle):
            return APIResponse(
                success=True,
                data={
                    "forecast": result.model_dump(),
                    "generated_at": result.generated_at,
                    "source": "live_generation"
                }
            )
        else:
            return APIResponse(
                success=False,
                error=f"Forecast generation failed: {getattr(result, 'error', 'Unknown error')}"
            )
    
    except Exception as e:
        return APIResponse(
            success=False, 
            error=f"Service error: {str(e)}",
            data={"note": "This may be due to missing environment variables or dependencies"}
        )

@app.get("/api/status")
async def get_system_status():
    """Get system component status"""
    status = {
        "api": "online",
        "forecasting_system": "checking...",
        "database": "not_configured",
        "nasa_api": "checking...",
        "ai_services": "checking..."
    }
    
    # Check forecasting system
    try:
        if run_forecast is not None:
            status["forecasting_system"] = "available"
        else:
            status["forecasting_system"] = "not_available"
    except:
        status["forecasting_system"] = "error"
    
    # Check NASA API key
    nasa_key = os.getenv("NASA_API_KEY")
    if nasa_key:
        status["nasa_api"] = "configured"
    else:
        status["nasa_api"] = "not_configured"
    
    # Check AI service keys
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        status["ai_services"] = "configured"
    else:
        status["ai_services"] = "not_configured"
    
    return APIResponse(success=True, data=status)

# This is required for Vercel deployment
# Vercel looks for either 'app' or 'handler'
handler = app