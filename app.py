"""
Simple Python entry point for Vercel deployment
NASA Space Weather Forecaster
"""

import json
import os
from datetime import datetime
from urllib.parse import parse_qs

def handler(event, context):
    """
    Vercel serverless function handler
    """
    
    # Get request information
    path = event.get('path', '/')
    method = event.get('httpMethod', 'GET')
    query = event.get('queryStringParameters') or {}
    
    # CORS headers
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
    }
    
    # Handle OPTIONS requests for CORS
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        # Route handling
        if path == '/' or path == '':
            response_data = {
                "name": "NASA Space Weather Forecaster",
                "version": "2.0.0", 
                "status": "online",
                "description": "Real-time space weather forecasting using NASA data and AI analysis",
                "endpoints": {
                    "health": "/api/health",
                    "forecast": "/api/forecast",
                    "status": "/api/status"
                }
            }
        
        elif path == '/api/health':
            response_data = {
                "success": True,
                "data": {
                    "status": "healthy",
                    "service": "nasa-space-weather-api",
                    "environment": "vercel-serverless",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }
        
        elif path == '/api/forecast':
            # Return demo forecast data
            response_data = {
                "success": True,
                "data": {
                    "forecast": {
                        "forecasts": [
                            {
                                "event": "CME",
                                "solar_timestamp": datetime.utcnow().isoformat() + "Z",
                                "predicted_arrival_window_utc": [
                                    datetime.utcnow().isoformat() + "Z",
                                    datetime.utcnow().isoformat() + "Z"
                                ],
                                "risk_summary": "Demo mode - serverless deployment active",
                                "impacts": ["aurora_visibility", "gps_accuracy"],
                                "confidence": 0.7,
                                "evidence": {
                                    "donki_ids": ["demo_cme_001"],
                                    "epic_frames": [datetime.utcnow().isoformat() + "Z"],
                                    "gibs_layers": ["VIIRS_TrueColor"]
                                }
                            }
                        ]
                    },
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "source": "demo_serverless",
                    "note": "This is a demo response from the serverless deployment"
                }
            }
        
        elif path == '/api/status':
            # Check environment variables
            nasa_key = bool(os.getenv("NASA_API_KEY"))
            anthropic_key = bool(os.getenv("ANTHROPIC_API_KEY"))
            
            response_data = {
                "success": True,
                "data": {
                    "api": "online",
                    "deployment": "vercel-serverless", 
                    "nasa_api": "configured" if nasa_key else "not_configured",
                    "ai_services": "configured" if anthropic_key else "not_configured",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }
        
        else:
            # 404 for unknown paths
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({
                    "success": False,
                    "error": "Endpoint not found",
                    "path": path
                })
            }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response_data, indent=2)
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        }