from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse the URL
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)
        
        # Set CORS headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
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
                        "environment": "vercel-python",
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
                                    "risk_summary": "Demo mode - Vercel deployment active",
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
                        "source": "demo_vercel",
                        "note": "This is a demo response from the Vercel deployment"
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
                        "deployment": "vercel-python", 
                        "nasa_api": "configured" if nasa_key else "not_configured",
                        "ai_services": "configured" if anthropic_key else "not_configured",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                }
            
            else:
                # 404 for unknown paths
                self.send_response(404)
                response_data = {
                    "success": False,
                    "error": "Endpoint not found",
                    "path": path
                }
            
            # Send JSON response
            self.wfile.write(json.dumps(response_data, indent=2).encode())
        
        except Exception as e:
            self.send_response(500)
            error_response = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        # Handle CORS preflight requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()