#!/usr/bin/env python3
"""
Simplified NASA Space Weather Dashboard API with Ensemble Forecasting
Bypasses websockets issues to focus on ensemble functionality
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

# Add backend to path
sys.path.append('.')
sys.path.append('backend')

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

# FastAPI imports with minimal websocket support
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import ensemble forecasting components
try:
    from backend.expert_forecaster import ExpertSpaceWeatherForecaster
    EXPERT_AVAILABLE = True
except ImportError as e:
    print(f"Expert forecaster import failed: {e}")
    EXPERT_AVAILABLE = False

try:
    from backend.ensemble_forecaster import EnsembleSpaceWeatherForecaster
    ENSEMBLE_AVAILABLE = True
except ImportError as e:
    print(f"Ensemble forecaster import failed: {e}")
    ENSEMBLE_AVAILABLE = False

# Fallback to basic forecaster
from backend.forecaster import run_forecast

# Create FastAPI app
app = FastAPI(title="NASA Space Weather Ensemble API", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def convert_to_dashboard_format(forecast_result):
    """Convert forecast to dashboard format with ensemble information"""
    
    if hasattr(forecast_result, 'error'):
        return {
            "success": False,
            "error": forecast_result.error,
            "data": None
        }
    
    if not hasattr(forecast_result, 'forecasts'):
        return {
            "success": False,
            "error": "Invalid forecast format",
            "data": None
        }
    
    forecasts = forecast_result.forecasts
    
    # Determine if using ensemble
    ai_model = "Ensemble AI (Physics + ML + Neural)" if ENSEMBLE_AVAILABLE else "Physics + AI"
    methodology = "Ensemble forecasting: Physics models + Machine Learning + Neural Networks" if ENSEMBLE_AVAILABLE else "Physics-based forecasting with AI analysis"
    
    # Determine overall risk level
    if not forecasts:
        risk_level = "MINIMAL"
        confidence_score = 1.0
        executive_summary = "No significant space weather events detected. Current conditions are quiet with minimal Earth impact expected."
    else:
        # Use the highest confidence forecast for main summary
        main_forecast = max(forecasts, key=lambda f: f.confidence)
        
        # Map our risk levels to dashboard format
        risk_mapping = {
            "aurora_midlat": "MODERATE",
            "aurora_highlat": "LOW", 
            "HF_comms": "MODERATE",
            "GNSS_jitter": "MODERATE",
            "satellite_drag": "HIGH"
        }
        
        # Determine overall risk level
        max_risk = "LOW"
        for forecast in forecasts:
            for impact in forecast.impacts:
                if risk_mapping.get(impact, "LOW") in ["EXTREME", "HIGH"]:
                    max_risk = "HIGH"
                elif risk_mapping.get(impact, "LOW") == "MODERATE" and max_risk == "LOW":
                    max_risk = "MODERATE"
        
        risk_level = max_risk
        confidence_score = main_forecast.confidence
        executive_summary = main_forecast.risk_summary
    
    # Build evidence chain
    evidence_chain = []
    for i, forecast in enumerate(forecasts):
        evidence_chain.append({
            "evidence_type": f"{forecast.event}_EVENT",
            "description": f"Solar {forecast.event.lower()} event detected at {forecast.solar_timestamp}",
            "source": f"NASA DONKI + {ai_model}",
            "confidence": forecast.confidence
        })
        
        # Add DONKI evidence
        for donki_id in forecast.evidence.donki_ids:
            evidence_chain.append({
                "evidence_type": "OBSERVATIONAL_DATA",
                "description": f"DONKI event reference: {donki_id}",
                "source": "NASA DONKI Database",
                "confidence": 1.0
            })
    
    # Build predicted impacts
    predicted_impacts = []
    risk_mapping = {
        "aurora_midlat": "MODERATE",
        "aurora_highlat": "LOW",
        "HF_comms": "MODERATE", 
        "GNSS_jitter": "MODERATE",
        "satellite_drag": "HIGH"
    }
    
    for forecast in forecasts:
        for impact in forecast.impacts:
            severity = risk_mapping.get(impact, "LOW")
            predicted_impacts.append({
                "category": impact.replace("_", " ").title(),
                "severity": severity,
                "description": f"Potential {impact.replace('_', ' ')} effects from {forecast.event}"
            })
    
    # Build recommendations
    recommendations = []
    if risk_level == "HIGH":
        recommendations.extend([
            "Monitor satellite operations for potential anomalies",
            "Prepare backup communication systems",
            "Alert aviation authorities of potential navigation disruptions"
        ])
    elif risk_level == "MODERATE":
        recommendations.extend([
            "Monitor space weather conditions",
            "Check satellite system status",
            "Be aware of potential minor disruptions"
        ])
    else:
        recommendations.append("Continue normal operations")
    
    # Calculate space weather score
    if forecasts:
        max_confidence = max(f.confidence for f in forecasts)
        impact_count = sum(len(f.impacts) for f in forecasts)
        space_weather_score = min(100, (max_confidence * 50) + (impact_count * 10))
    else:
        space_weather_score = 0
    
    activity_levels = {
        0: "MINIMAL",
        20: "LOW", 
        40: "MODERATE",
        60: "HIGH",
        80: "EXTREME"
    }
    
    activity_level = "MINIMAL"
    for threshold, level in sorted(activity_levels.items()):
        if space_weather_score >= threshold:
            activity_level = level
    
    return {
        "success": True,
        "data": {
            "forecast": {
                "title": f"Space Weather Forecast - {len(forecasts)} Event(s) Analyzed",
                "executive_summary": executive_summary,
                "confidence_score": confidence_score,
                "risk_level": risk_level,
                "ai_model": ai_model,
                "methodology": methodology,
                "valid_until": (datetime.utcnow() + timedelta(hours=24)).isoformat() + "Z",
                "detailed_analysis": f"Analyzed {len(forecasts)} space weather events using NASA DONKI data. {executive_summary} Forecast generated using {'ensemble AI combining physics models, machine learning, and neural networks' if ENSEMBLE_AVAILABLE else 'physics-based models with AI analysis'}.",
                "evidence_chain": evidence_chain,
                "predicted_impacts": predicted_impacts,
                "recommendations": recommendations
            },
            "raw_data_summary": {
                "space_weather_index": {
                    "score": int(space_weather_score),
                    "level": activity_level
                },
                "data_sources": ["NASA_DONKI", "NASA_EPIC", "NASA_GIBS"],
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "forecast_count": len(forecasts),
                "ensemble_active": ENSEMBLE_AVAILABLE,
                "models_used": ["Physics", "ML", "Neural"] if ENSEMBLE_AVAILABLE else ["Physics", "AI"]
            }
        }
    }

@app.get("/")
async def root():
    """Root endpoint with system status"""
    return {
        "service": "NASA Space Weather Ensemble API",
        "version": "2.0.0",
        "status": "operational",
        "ensemble_forecasting": ENSEMBLE_AVAILABLE,
        "expert_forecasting": EXPERT_AVAILABLE,
        "endpoints": [
            "/api/v1/forecasts/simple",
            "/api/v1/forecasts/advanced", 
            "/api/v1/system/status"
        ]
    }

@app.get("/api/v1/system/status")
async def system_status():
    """Get system status and capabilities"""
    return {
        "success": True,
        "data": {
            "ensemble_forecasting": ENSEMBLE_AVAILABLE,
            "expert_forecasting": EXPERT_AVAILABLE,
            "neural_networks": ENSEMBLE_AVAILABLE,
            "ml_models": ENSEMBLE_AVAILABLE,
            "physics_models": True,
            "historical_database": Path("data/historical/space_weather_history.db").exists(),
            "capabilities": [
                "Physics-based CME arrival predictions",
                "Machine learning ensemble models" if ENSEMBLE_AVAILABLE else "Basic AI analysis", 
                "Neural network pattern recognition" if ENSEMBLE_AVAILABLE else "Pattern analysis",
                "Real-time NASA data integration",
                "Multi-model uncertainty quantification" if ENSEMBLE_AVAILABLE else "Basic uncertainty estimates"
            ]
        }
    }

@app.get("/api/v1/forecasts/simple")
async def get_simple_forecast():
    """Get simple forecast with ensemble predictions if available"""
    try:
        if EXPERT_AVAILABLE:
            print("Using expert ensemble forecaster...")
            expert_forecaster = ExpertSpaceWeatherForecaster()
            result = expert_forecaster.generate_expert_forecast(days_back=3)
        else:
            print("Using basic forecaster...")
            result = run_forecast(days_back=3)
        
        if hasattr(result, 'error'):
            raise HTTPException(status_code=500, detail=result.error)
        
        # Convert to simple format
        simple_data = {
            "success": True,
            "data": {
                "forecasts": [
                    {
                        "event": f.event,
                        "solar_timestamp": f.solar_timestamp,
                        "predicted_arrival_window_utc": f.predicted_arrival_window_utc,
                        "risk_summary": f.risk_summary,
                        "impacts": f.impacts,
                        "confidence": f.confidence,
                        "evidence": {
                            "donki_ids": f.evidence.donki_ids,
                            "epic_frames": f.evidence.epic_frames,
                            "gibs_layers": f.evidence.gibs_layers
                        }
                    } for f in result.forecasts
                ],
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "data_sources": ["NASA_DONKI", "NASA_EPIC", "NASA_GIBS"],
                "model_type": "Ensemble AI" if ENSEMBLE_AVAILABLE else "Physics + AI"
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return JSONResponse(content=simple_data)
        
    except Exception as e:
        print(f"Simple forecast error: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": f"Forecast generation failed: {str(e)}",
                "data": None
            },
            status_code=500
        )

@app.get("/api/v1/forecasts/advanced")
async def get_advanced_forecast():
    """Get advanced forecast with full ensemble analysis"""
    try:
        if EXPERT_AVAILABLE:
            print("Generating expert ensemble forecast...")
            expert_forecaster = ExpertSpaceWeatherForecaster()
            result = expert_forecaster.generate_expert_forecast(days_back=3)
        else:
            print("Generating basic forecast...")
            result = run_forecast(days_back=3)
        
        dashboard_data = convert_to_dashboard_format(result)
        return JSONResponse(content=dashboard_data)
        
    except Exception as e:
        print(f"Advanced forecast error: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": f"Advanced forecast failed: {str(e)}",
                "data": None
            },
            status_code=500
        )

if __name__ == "__main__":
    print("Starting NASA Space Weather Ensemble Dashboard API...")
    print(f"Ensemble forecasting: {'ENABLED' if ENSEMBLE_AVAILABLE else 'DISABLED'}")
    print(f"Expert forecasting: {'ENABLED' if EXPERT_AVAILABLE else 'DISABLED'}")
    print("API will be available at: http://localhost:8001")
    
    # Start server without websockets
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8001, 
        log_level="warning",
        ws_ping_interval=None,
        ws_ping_timeout=None
    )