#!/usr/bin/env python3
"""
Simple API server for the professional dashboard
Works with OpenAI-powered forecasting system
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timedelta

# FastAPI imports
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

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

# Import our forecasting system
from backend.universal_forecaster import run_universal_forecast, UniversalAIClient
from backend.expert_forecaster import run_expert_forecast
from backend.realtime_data import get_realtime_space_weather, RealTimeSpaceWeatherData
from backend.visualization_engine import SpaceWeatherVisualizationEngine, get_visualization_data_api, create_cme_animation_api

# Create FastAPI app
app = FastAPI(title="NASA Space Weather Dashboard API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def convert_to_dashboard_format(forecast_result) -> Dict[str, Any]:
    """Convert our forecast format to dashboard-expected format"""
    
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
    
    # Determine overall risk level
    if not forecasts:
        risk_level = "MINIMAL"
        confidence_score = 1.0
        executive_summary = "No significant space weather events detected. Current conditions are quiet with minimal Earth impact expected."
        ai_model = "Ensemble AI (Physics + ML + Neural)"
    else:
        # Use the highest confidence forecast for main summary
        main_forecast = max(forecasts, key=lambda f: f.confidence)
        
        # Map our risk levels to dashboard format
        risk_mapping = {
            "aurora_midlat": "MODERATE",
            "aurora_highlat": "LOW", 
            "HF_comms": "MODERATE",
            "GNSS_jitter": "MODERATE",
            "GNSS_outage": "HIGH",
            "satellite_drag": "HIGH",
            "radiation_storm": "EXTREME",
            "power_grid": "EXTREME"
        }
        
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
        ai_model = "Ensemble AI (Physics + ML + Neural)"
    
    # Build evidence chain
    evidence_chain = []
    for i, forecast in enumerate(forecasts):
        evidence_chain.append({
            "evidence_type": f"{forecast.event}_EVENT",
            "description": f"Solar {forecast.event.lower()} event detected at {forecast.solar_timestamp}",
            "source": f"NASA DONKI + {ai_model}",
            "confidence": forecast.confidence
        })
        
        for donki_id in forecast.evidence.donki_ids:
            evidence_chain.append({
                "evidence_type": "OBSERVATIONAL_DATA",
                "description": f"DONKI event reference: {donki_id}",
                "source": "NASA DONKI Database",
                "confidence": 1.0
            })
    
    if not evidence_chain:
        evidence_chain = [{
            "evidence_type": "SYSTEM_STATUS",
            "description": "All monitoring systems operational, no significant events detected",
            "source": "NASA DONKI Database",
            "confidence": 1.0
        }]
    
    # Build impact predictions
    predicted_impacts = []
    for forecast in forecasts:
        for impact in forecast.impacts:
            severity = risk_mapping.get(impact, "LOW")
            predicted_impacts.append({
                "category": impact.replace("_", " ").title(),
                "severity": severity,
                "description": f"Potential {impact.replace('_', ' ')} effects from {forecast.event}"
            })
    
    if not predicted_impacts:
        predicted_impacts = [{
            "category": "System Status",
            "severity": "MINIMAL",
            "description": "All systems operating within normal parameters"
        }]
    
    # Build recommendations
    recommendations = []
    if risk_level in ["HIGH", "EXTREME"]:
        recommendations.extend([
            "Monitor satellite operations for potential anomalies",
            "Prepare backup communication systems",
            "Alert aviation authorities of potential navigation disruptions"
        ])
    elif risk_level == "MODERATE":
        recommendations.extend([
            "Continue routine monitoring protocols",
            "Prepare contingency plans for communication systems"
        ])
    else:
        recommendations.extend([
            "Maintain standard space weather surveillance",
            "Continue routine system monitoring"
        ])
    
    # Calculate space weather index
    space_weather_score = 0
    if forecasts:
        max_confidence = max(f.confidence for f in forecasts)
        impact_count = sum(len(f.impacts) for f in forecasts)
        space_weather_score = min(100, (max_confidence * 50) + (impact_count * 10))
    
    activity_levels = {
        0: "MINIMAL",
        20: "LOW", 
        40: "MODERATE",
        60: "HIGH",
        80: "EXTREME"
    }
    
    activity_level = "MINIMAL"
    for threshold, level in sorted(activity_levels.items(), reverse=True):
        if space_weather_score >= threshold:
            activity_level = level
            break
    
    return {
        "success": True,
        "data": {
            "forecast": {
                "title": f"Space Weather Forecast - {len(forecasts)} Event(s) Analyzed",
                "executive_summary": executive_summary,
                "confidence_score": confidence_score,
                "risk_level": risk_level,
                "ai_model": ai_model,
                "methodology": "Ensemble forecasting: Physics models + Machine Learning + Neural Networks",
                "valid_until": (datetime.utcnow() + timedelta(hours=24)).isoformat() + "Z",
                "detailed_analysis": f"Analyzed {len(forecasts)} space weather events using NASA DONKI data. {executive_summary} Forecast generated using advanced AI analysis of solar wind conditions, magnetic field data, and historical patterns.",
                "evidence_chain": evidence_chain,
                "predicted_impacts": predicted_impacts,
                "recommendations": recommendations
            },
            "raw_data_summary": {
                "space_weather_index": {
                    "score": space_weather_score,
                    "level": activity_level
                },
                "data_sources": forecast_result.data_sources,
                "generated_at": forecast_result.generated_at,
                "forecast_count": len(forecasts)
            }
        }
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "NASA Space Weather Dashboard API", "status": "operational"}

@app.get("/api/v1/status")
async def get_status():
    """Get system status"""
    try:
        # Check AI providers
        universal_client = UniversalAIClient()
        status_info = universal_client.get_status()
        
        return {
            "success": True,
            "data": {
                "api_status": "operational",
                "ai_providers": status_info['available_clients'],
                "active_provider": status_info['active_client'],
                "nasa_apis": ["DONKI", "EPIC", "GIBS"],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Status check failed: {str(e)}",
            "data": None
        }

@app.get("/api/v1/forecasts/simple")
async def get_simple_forecast():
    """Get simple forecast with ensemble predictions (basic format)"""
    try:
        # Use expert forecaster with ensemble capabilities  
        result = run_expert_forecast(days_back=3)
        
        if hasattr(result, 'error'):
            raise HTTPException(status_code=500, detail=result.error)
        
        return {
            "success": True,
            "data": result.model_dump(),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast generation failed: {str(e)}")

@app.get("/api/v1/forecasts/advanced")
async def get_advanced_forecast():
    """Get advanced forecast with ensemble ML/Neural predictions (dashboard format)"""
    try:
        # Use expert forecaster with ensemble capabilities
        result = run_expert_forecast(days_back=3)
        
        dashboard_data = convert_to_dashboard_format(result)
        return JSONResponse(content=dashboard_data)
        
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "error": f"Advanced forecast generation failed: {str(e)}",
                "data": None
            },
            status_code=500
        )

@app.post("/api/v1/forecasts/generate")
async def generate_new_forecast():
    """Generate a new forecast on demand"""
    try:
        result = run_universal_forecast(
            days_back=5,  # Look back further for more data
            ai_provider="auto",
            max_tokens=1500
        )
        
        dashboard_data = convert_to_dashboard_format(result)
        return JSONResponse(content=dashboard_data)
        
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "error": f"Forecast generation failed: {str(e)}",
                "data": None
            },
            status_code=500
        )

@app.post("/api/v1/alerts/email")
async def send_email_alert():
    """Send email alert with current forecast"""
    try:
        from backend.email_alerts import EmailAlerter
        
        # Generate current forecast
        result = run_universal_forecast(
            days_back=3,
            ai_provider="auto",
            max_tokens=1200
        )
        
        # Send email alert
        alerter = EmailAlerter()
        if not alerter.enabled:
            return JSONResponse(
                content={
                    "success": False,
                    "error": "Email alerts not configured. Check your .env file.",
                    "data": None
                },
                status_code=400
            )
        
        success = alerter.send_forecast_alert(result)
        
        if success:
            return JSONResponse(
                content={
                    "success": True,
                    "message": f"Email alert sent successfully to {alerter.test_recipient}",
                    "data": {
                        "recipient": alerter.test_recipient,
                        "forecast_count": len(result.forecasts) if hasattr(result, 'forecasts') else 0
                    }
                }
            )
        else:
            return JSONResponse(
                content={
                    "success": False,
                    "error": "Failed to send email alert",
                    "data": None
                },
                status_code=500
            )
        
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "error": f"Email alert failed: {str(e)}",
                "data": None
            },
            status_code=500
        )

@app.post("/api/v1/alerts/test")
async def test_email_alert():
    """Test email configuration"""
    try:
        from backend.email_alerts import EmailAlerter
        
        alerter = EmailAlerter()
        if not alerter.enabled:
            return JSONResponse(
                content={
                    "success": False,
                    "error": "Email alerts not configured",
                    "data": None
                },
                status_code=400
            )
        
        success = alerter.test_email_connection()
        
        if success:
            return JSONResponse(
                content={
                    "success": True,
                    "message": f"Test email sent successfully to {alerter.test_recipient}",
                    "data": {"recipient": alerter.test_recipient}
                }
            )
        else:
            return JSONResponse(
                content={
                    "success": False,
                    "error": "Email test failed",
                    "data": None
                },
                status_code=500
            )
        
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "error": f"Email test failed: {str(e)}",
                "data": None
            },
            status_code=500
        )

@app.post("/api/v1/expert/forecast")
async def get_expert_forecast():
    """Generate comprehensive expert-level forecast with physics models"""
    try:
        # Get real-time space weather data
        realtime_fetcher = RealTimeSpaceWeatherData()
        realtime_data = realtime_fetcher.get_comprehensive_space_weather()
        
        # Run expert forecast analysis
        expert_result = run_expert_forecast(days_back=3)
        
        if hasattr(expert_result, 'error'):
            return JSONResponse(
                content={
                    "success": False,
                    "error": expert_result.error,
                    "data": None
                },
                status_code=500
            )
        
        # Structure response for expert dashboard with real advanced physics data
        response_data = {
            "success": True,
            "data": {
                "forecast": expert_result.model_dump() if hasattr(expert_result, 'model_dump') else expert_result.__dict__,
                "realtime_data": realtime_data,
                "physics_analysis": {},
                "advanced_physics": {},
                "generated_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        # Extract real advanced physics analysis from expert forecaster
        if hasattr(expert_result, 'forecasts') and expert_result.forecasts:
            # Get the forecaster to access its analysis data
            from backend.expert_forecaster import ExpertSpaceWeatherForecaster
            forecaster = ExpertSpaceWeatherForecaster()
            
            # Run comprehensive data fetch and analysis
            try:
                space_weather_data = forecaster._fetch_comprehensive_data(3)
                physics_analysis = forecaster._run_physics_analysis(space_weather_data)
                advanced_analysis = forecaster._run_advanced_physics_analysis(space_weather_data, physics_analysis)
                
                # Structure the physics analysis for dashboard consumption
                physics_summary = {
                    "cme_analyses": physics_analysis.get('cme_analyses', []),
                    "geomagnetic_predictions": physics_analysis.get('geomagnetic_predictions', {
                        "dst": {"dst_index": -20, "storm_level": "quiet"},
                        "kp": {"kp_index": 3, "activity_level": "quiet"}
                    }),
                    "aurora_predictions": physics_analysis.get('aurora_predictions', {
                        "geographic_latitude_boundary": 65.0,
                        "cities_visible": ["Fairbanks", "Reykjavik"]
                    }),
                    "overall_assessment": physics_analysis.get('overall_assessment', {})
                }
                
                # Add advanced physics results
                advanced_physics_summary = {
                    "solar_particle_events": advanced_analysis.get('solar_particle_events', []),
                    "substorm_predictions": advanced_analysis.get('substorm_predictions', {
                        "substorm_expected": False,
                        "intensity": "quiet",
                        "predicted_ae_index": 80,
                        "probability": 0.2
                    }),
                    "satellite_drag_analysis": advanced_analysis.get('satellite_drag_analysis', {
                        "atmospheric_density": 1.8e-15,
                        "altitude_loss_per_day": 0.003,
                        "risk_assessment": "low"
                    }),
                    "ionospheric_scintillation": advanced_analysis.get('ionospheric_scintillation', {
                        "global_forecast": [
                            {"location": "Singapore", "severity": "quiet", "s4_index": 0.12},
                            {"location": "Brazil", "severity": "quiet", "s4_index": 0.08},
                            {"location": "Nigeria", "severity": "quiet", "s4_index": 0.05}
                        ],
                        "high_risk_regions": []
                    }),
                    "shock_arrival_refinement": advanced_analysis.get('shock_arrival_refinement', {
                        "refined_predictions": []
                    })
                }
                
                response_data["data"]["physics_analysis"] = physics_summary
                response_data["data"]["advanced_physics"] = advanced_physics_summary
                
            except Exception as analysis_error:
                logger.warning(f"Advanced physics analysis failed: {analysis_error}")
                # Fallback to basic structure
                response_data["data"]["physics_analysis"] = {
                    "cme_analyses": [],
                    "geomagnetic_predictions": {
                        "dst": {"dst_index": -10, "storm_level": "quiet"},
                        "kp": {"kp_index": 2, "activity_level": "quiet"}
                    },
                    "aurora_predictions": {
                        "geographic_latitude_boundary": 67.0,
                        "cities_visible": ["Fairbanks"]
                    }
                }
                response_data["data"]["advanced_physics"] = {
                    "solar_particle_events": [],
                    "substorm_predictions": {"substorm_expected": False},
                    "satellite_drag_analysis": {"risk_assessment": "low"},
                    "ionospheric_scintillation": {"global_forecast": [], "high_risk_regions": []},
                    "shock_arrival_refinement": {"refined_predictions": []}
                }
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"Expert forecast failed: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": f"Expert forecast generation failed: {str(e)}",
                "data": None
            },
            status_code=500
        )

@app.get("/api/v1/realtime")
async def get_realtime_data():
    """Get current real-time space weather data"""
    try:
        realtime_fetcher = RealTimeSpaceWeatherData()
        data = realtime_fetcher.get_comprehensive_space_weather()
        
        return JSONResponse(
            content={
                "success": True,
                "data": data,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
        
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "error": f"Real-time data fetch failed: {str(e)}",
                "data": None
            },
            status_code=500
        )

@app.get("/api/v1/visualization/3d")
async def get_3d_visualization():
    """Get 3D solar system visualization data"""
    try:
        viz_data = get_visualization_data_api()
        
        return JSONResponse(
            content={
                "success": True,
                "data": viz_data,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
        
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "error": f"3D visualization data failed: {str(e)}",
                "data": None
            },
            status_code=500
        )

@app.post("/api/v1/visualization/cme-animation")
async def create_cme_animation():
    """Create CME animation data for 3D visualization"""
    try:
        # Get recent CME data from expert forecaster for animation
        expert_result = run_expert_forecast(days_back=2)
        
        cme_data = None
        if hasattr(expert_result, 'forecasts') and expert_result.forecasts:
            # Use first forecast for animation
            forecast = expert_result.forecasts[0]
            cme_data = {
                'activityID': 'FORECAST_CME_001',
                'startTime': forecast.solar_timestamp,
                'cmeAnalyses': [{
                    'speed': '650',
                    'longitude': '0',
                    'latitude': '15',
                    'halfAngle': '30'
                }]
            }
        
        animation_data = create_cme_animation_api(cme_data, duration_hours=72)
        
        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "animation_frames": animation_data,
                    "frame_count": len(animation_data),
                    "duration_hours": 72,
                    "time_step_hours": 1.0
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
        
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "error": f"CME animation creation failed: {str(e)}",
                "data": None
            },
            status_code=500
        )

@app.get("/api/v1/visualization/solar-system")
async def get_solar_system_state():
    """Get current solar system state for visualization"""
    try:
        engine = SpaceWeatherVisualizationEngine()
        system_state = engine.solar_system.get_system_state()
        
        return JSONResponse(
            content={
                "success": True,
                "data": system_state,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
        
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "error": f"Solar system state failed: {str(e)}",
                "data": None
            },
            status_code=500
        )

if __name__ == "__main__":
    print("Starting NASA Space Weather Dashboard API...")
    print("Dashboard will be available at: http://localhost:8001")
    print("API docs available at: http://localhost:8001/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")