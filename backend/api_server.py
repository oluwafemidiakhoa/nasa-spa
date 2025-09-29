"""
FastAPI server for NASA Space Weather Forecaster
Provides REST API endpoints for forecast data and real-time updates
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Import our modules
from backend.schema import ForecastBundle, ForecastError, Forecast
from backend.forecaster import SpaceWeatherForecaster, ForecastConfig, run_forecast
from backend.database import DatabaseManager, ForecastRecord, AlertRecord
from backend.monitor import MonitorService
from backend.notifications import NotificationService


class ForecastRequest(BaseModel):
    """Request model for generating custom forecasts"""
    days_back: int = Field(default=3, ge=1, le=7)
    include_images: bool = Field(default=False)
    epic_date_iso: Optional[str] = Field(default=None)
    max_tokens: int = Field(default=1500, ge=500, le=3000)


class AlertSubscription(BaseModel):
    """Model for alert subscriptions"""
    email: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    alert_types: List[str] = Field(default=["CME", "FLARE"])
    min_confidence: float = Field(default=0.6, ge=0.0, le=1.0)


class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
            
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.active_connections.remove(connection)


# Global instances
db_manager = DatabaseManager()
notification_service = NotificationService()
websocket_manager = WebSocketManager()
monitor_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global monitor_service
    
    # Startup
    print("Starting NASA Space Weather API server...")
    
    # Initialize database
    await db_manager.initialize()
    
    # Start monitoring service
    monitor_service = MonitorService(
        db_manager=db_manager,
        notification_service=notification_service,
        websocket_manager=websocket_manager
    )
    await monitor_service.start()
    
    yield
    
    # Shutdown
    print("Shutting down NASA Space Weather API server...")
    if monitor_service:
        await monitor_service.stop()
    await db_manager.close()


# Create FastAPI app
app = FastAPI(
    title="NASA Space Weather Forecaster API",
    description="Real-time space weather forecasting using NASA data and AI analysis",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return APIResponse(success=True, data={"status": "healthy", "service": "space-weather-api"})


@app.get("/api/v1/forecast/current", response_model=APIResponse)
async def get_current_forecast():
    """Get the latest forecast from database or generate new one"""
    try:
        # Try to get recent forecast from database
        recent_forecast = await db_manager.get_latest_forecast(max_age_hours=1)
        
        if recent_forecast:
            return APIResponse(
                success=True,
                data={
                    "forecast": recent_forecast.forecast_data,
                    "generated_at": recent_forecast.created_at.isoformat() + "Z",
                    "source": "cached"
                }
            )
        
        # Generate new forecast if no recent one exists
        result = run_forecast(days_back=3)
        
        if isinstance(result, ForecastBundle):
            # Store in database
            await db_manager.store_forecast(result)
            
            return APIResponse(
                success=True,
                data={
                    "forecast": result.model_dump(),
                    "generated_at": result.generated_at,
                    "source": "generated"
                }
            )
        else:
            return APIResponse(
                success=False,
                error=f"Forecast generation failed: {result.error}"
            )
    
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@app.post("/api/v1/forecast/generate", response_model=APIResponse)
async def generate_custom_forecast(request: ForecastRequest, background_tasks: BackgroundTasks):
    """Generate a custom forecast with specified parameters"""
    try:
        config = ForecastConfig(
            days_back=request.days_back,
            include_images=request.include_images,
            epic_date_iso=request.epic_date_iso,
            max_tokens=request.max_tokens
        )
        
        forecaster = SpaceWeatherForecaster(config)
        result = forecaster.generate_forecast()
        
        if isinstance(result, ForecastBundle):
            # Store in database in background
            background_tasks.add_task(db_manager.store_forecast, result)
            
            # Broadcast to websocket clients
            background_tasks.add_task(
                websocket_manager.broadcast,
                {"type": "new_forecast", "data": result.model_dump()}
            )
            
            return APIResponse(
                success=True,
                data={
                    "forecast": result.model_dump(),
                    "generated_at": result.generated_at
                }
            )
        else:
            return APIResponse(
                success=False,
                error=f"Forecast generation failed: {result.error}"
            )
    
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@app.get("/api/v1/forecast/history", response_model=APIResponse)
async def get_forecast_history(
    days: int = 7,
    limit: int = 50,
    event_type: Optional[str] = None
):
    """Get historical forecasts"""
    try:
        forecasts = await db_manager.get_forecast_history(
            days_back=days,
            limit=limit,
            event_type=event_type
        )
        
        return APIResponse(
            success=True,
            data={
                "forecasts": [
                    {
                        "id": f.id,
                        "forecast": f.forecast_data,
                        "created_at": f.created_at.isoformat() + "Z",
                        "accuracy_score": f.accuracy_score
                    }
                    for f in forecasts
                ],
                "count": len(forecasts)
            }
        )
    
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@app.get("/api/v1/alerts/active", response_model=APIResponse)
async def get_active_alerts():
    """Get currently active space weather alerts"""
    try:
        alerts = await db_manager.get_active_alerts()
        
        return APIResponse(
            success=True,
            data={
                "alerts": [
                    {
                        "id": alert.id,
                        "event_type": alert.event_type,
                        "severity": alert.severity,
                        "message": alert.message,
                        "created_at": alert.created_at.isoformat() + "Z",
                        "expires_at": alert.expires_at.isoformat() + "Z" if alert.expires_at else None
                    }
                    for alert in alerts
                ]
            }
        )
    
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@app.post("/api/v1/alerts/subscribe", response_model=APIResponse)
async def subscribe_to_alerts(subscription: AlertSubscription):
    """Subscribe to space weather alerts"""
    try:
        # Validate email format if provided
        if subscription.email:
            from email_validator import validate_email, EmailNotValidError
            try:
                validate_email(subscription.email)
            except EmailNotValidError:
                return APIResponse(success=False, error="Invalid email format")
        
        # Store subscription in database
        subscription_id = await db_manager.store_alert_subscription(
            email=subscription.email,
            phone=subscription.phone,
            alert_types=subscription.alert_types,
            min_confidence=subscription.min_confidence
        )
        
        return APIResponse(
            success=True,
            data={"subscription_id": subscription_id, "message": "Successfully subscribed to alerts"}
        )
    
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@app.get("/api/v1/stats/accuracy", response_model=APIResponse)
async def get_accuracy_stats():
    """Get forecast accuracy statistics"""
    try:
        stats = await db_manager.get_accuracy_stats()
        
        return APIResponse(
            success=True,
            data=stats
        )
    
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@app.websocket("/ws/forecasts")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time forecast updates"""
    await websocket_manager.connect(websocket)
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "message": "Connected to NASA Space Weather real-time updates",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
        # Keep connection alive and handle client messages
        while True:
            data = await websocket.receive_text()
            # Echo client messages for now (could implement commands later)
            await websocket.send_json({
                "type": "echo",
                "data": data,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
    
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)


# Development server configuration
if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )