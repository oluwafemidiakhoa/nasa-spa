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
            if path == '/live_dashboard.html':
                # Serve the HTML dashboard
                try:
                    with open('live_dashboard.html', 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(html_content.encode('utf-8'))
                    return
                except FileNotFoundError:
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    error_response = {
                        "success": False,
                        "error": "Dashboard file not found",
                        "path": path
                    }
                    self.wfile.write(json.dumps(error_response).encode())
                    return
            
            elif path == '/' or path == '':
                response_data = {
                    "name": "NASA Space Weather Forecaster",
                    "version": "2.0.0", 
                    "status": "online",
                    "description": "Real-time space weather forecasting using NASA data and AI analysis",
                    "endpoints": {
                        "health": "/api/health",
                        "forecast": "/api/forecast",
                        "status": "/api/status",
                        "dashboard": "/live_dashboard.html"
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
                # Check if we have real API keys to potentially make real calls
                nasa_key = os.getenv("NASA_API_KEY")
                anthropic_key = os.getenv("ANTHROPIC_API_KEY")
                
                if nasa_key and anthropic_key:
                    # TODO: Implement real forecast generation when dependencies are available
                    source = "live_capable"
                    note = "API keys configured - real forecasting capability available"
                else:
                    source = "demo_mode"
                    note = "Demo mode - configure NASA_API_KEY and ANTHROPIC_API_KEY for live forecasting"
                
                # Return demo forecast data (enhanced based on configuration)
                response_data = {
                    "success": True,
                    "data": {
                        "forecast": {
                            "forecasts": [
                                {
                                    "event": "CME",
                                    "solar_timestamp": datetime.utcnow().isoformat() + "Z",
                                    "predicted_arrival_window_utc": [
                                        (datetime.utcnow()).isoformat() + "Z",
                                        (datetime.utcnow()).isoformat() + "Z"
                                    ],
                                    "risk_summary": "Moderate geomagnetic activity expected. Aurora possible at high latitudes.",
                                    "impacts": ["aurora_visibility", "gps_accuracy", "hf_radio_disruption"],
                                    "confidence": 0.75,
                                    "evidence": {
                                        "donki_ids": ["2024-001-CME"],
                                        "epic_frames": [datetime.utcnow().isoformat() + "Z"],
                                        "gibs_layers": ["VIIRS_SNPP_CorrectedReflectance_TrueColor"]
                                    }
                                },
                                {
                                    "event": "FLARE",
                                    "solar_timestamp": (datetime.utcnow()).isoformat() + "Z",
                                    "predicted_arrival_window_utc": [
                                        datetime.utcnow().isoformat() + "Z",
                                        datetime.utcnow().isoformat() + "Z"
                                    ],
                                    "risk_summary": "Minor X-ray flux enhancement detected. Minimal Earth impact expected.",
                                    "impacts": ["hf_radio_minor"],
                                    "confidence": 0.85,
                                    "evidence": {
                                        "donki_ids": ["2024-002-FLR"],
                                        "epic_frames": [datetime.utcnow().isoformat() + "Z"],
                                        "gibs_layers": ["MODIS_Aqua_CorrectedReflectance_TrueColor"]
                                    }
                                }
                            ]
                        },
                        "generated_at": datetime.utcnow().isoformat() + "Z",
                        "source": source,
                        "note": note,
                        "api_status": {
                            "nasa_configured": bool(nasa_key),
                            "ai_configured": bool(anthropic_key)
                        }
                    }
                }
            
            elif path == '/api/status':
                # Check all environment variables
                nasa_key = bool(os.getenv("NASA_API_KEY"))
                anthropic_key = bool(os.getenv("ANTHROPIC_API_KEY"))
                openai_key = bool(os.getenv("OPENAI_API_KEY"))
                huggingface_key = bool(os.getenv("HUGGINGFACE_API_KEY"))
                email_user = bool(os.getenv("EMAIL_USER"))
                email_password = bool(os.getenv("EMAIL_PASSWORD"))
                twilio_sid = bool(os.getenv("TWILIO_ACCOUNT_SID"))
                
                response_data = {
                    "success": True,
                    "data": {
                        "api": "online",
                        "deployment": "vercel-python",
                        "version": "2.0.0",
                        "services": {
                            "nasa_api": "configured" if nasa_key else "not_configured",
                            "anthropic_ai": "configured" if anthropic_key else "not_configured", 
                            "openai": "configured" if openai_key else "not_configured",
                            "huggingface": "configured" if huggingface_key else "not_configured",
                            "email_alerts": "configured" if (email_user and email_password) else "not_configured",
                            "sms_alerts": "configured" if twilio_sid else "not_configured"
                        },
                        "capabilities": {
                            "forecasting": nasa_key and (anthropic_key or openai_key),
                            "email_notifications": email_user and email_password,
                            "sms_notifications": twilio_sid,
                            "ml_models": huggingface_key
                        },
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