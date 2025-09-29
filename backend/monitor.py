"""
Automated monitoring service for NASA Space Weather Forecaster
Continuously monitors space weather and generates alerts
"""

import asyncio
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from backend.forecaster import SpaceWeatherForecaster, ForecastConfig
from backend.schema import ForecastBundle, Forecast
from backend.database import DatabaseManager
from backend.notifications import NotificationService


@dataclass
class MonitorConfig:
    """Configuration for the monitoring service"""
    # Forecast generation intervals
    routine_interval_minutes: int = 30  # Regular forecast check interval
    priority_interval_minutes: int = 10  # High-priority period check interval
    
    # Alert thresholds
    high_confidence_threshold: float = 0.8
    moderate_confidence_threshold: float = 0.6
    
    # Event significance thresholds
    cme_speed_high_threshold: int = 1000  # km/s
    cme_speed_moderate_threshold: int = 600  # km/s
    flare_class_severe: List[str] = field(default_factory=lambda: ["X"])
    flare_class_moderate: List[str] = field(default_factory=lambda: ["M"])
    
    # Aurora visibility thresholds (impact types)
    aurora_high_impact: List[str] = field(default_factory=lambda: ["aurora_midlat", "aurora_lowlat"])
    aurora_moderate_impact: List[str] = field(default_factory=lambda: ["aurora_highlat"])
    
    # System maintenance intervals
    cleanup_interval_hours: int = 24
    accuracy_evaluation_hours: int = 6


class EventAnalyzer:
    """Analyzes forecast events and determines alert levels"""
    
    def __init__(self, config: MonitorConfig):
        self.config = config
    
    def analyze_forecast(self, forecast_bundle: ForecastBundle) -> List[Dict[str, Any]]:
        """Analyze a forecast and generate alerts if needed"""
        alerts = []
        
        for forecast in forecast_bundle.forecasts:
            alert_info = self._analyze_single_forecast(forecast)
            if alert_info:
                alerts.append(alert_info)
        
        return alerts
    
    def _analyze_single_forecast(self, forecast: Forecast) -> Optional[Dict[str, Any]]:
        """Analyze a single forecast and determine if an alert is needed"""
        severity = self._determine_severity(forecast)
        
        if severity == "LOW":
            return None  # Don't create alerts for low severity events
        
        # Generate alert message
        message = self._generate_alert_message(forecast, severity)
        
        return {
            "event_type": forecast.event,
            "severity": severity,
            "message": message,
            "confidence": forecast.confidence,
            "arrival_window": forecast.predicted_arrival_window_utc,
            "impacts": forecast.impacts
        }
    
    def _determine_severity(self, forecast: Forecast) -> str:
        """Determine alert severity based on forecast characteristics"""
        confidence = forecast.confidence
        event_type = forecast.event
        impacts = forecast.impacts
        
        # High confidence events
        if confidence >= self.config.high_confidence_threshold:
            # Check for severe impacts
            if any(impact in self.config.aurora_high_impact for impact in impacts):
                return "SEVERE"
            elif event_type == "CME" and "GNSS_jitter" in impacts:
                return "HIGH"
            elif any(impact in self.config.aurora_moderate_impact for impact in impacts):
                return "HIGH"
        
        # Moderate confidence events
        elif confidence >= self.config.moderate_confidence_threshold:
            if any(impact in self.config.aurora_high_impact for impact in impacts):
                return "HIGH"
            elif any(impact in self.config.aurora_moderate_impact for impact in impacts):
                return "MODERATE"
            elif "HF_comms" in impacts:
                return "MODERATE"
        
        return "LOW"
    
    def _generate_alert_message(self, forecast: Forecast, severity: str) -> str:
        """Generate a human-readable alert message"""
        arrival_start = forecast.predicted_arrival_window_utc[0]
        arrival_end = forecast.predicted_arrival_window_utc[1]
        
        # Parse arrival times for display
        try:
            start_dt = datetime.fromisoformat(arrival_start.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(arrival_end.replace("Z", "+00:00"))
            arrival_text = f"{start_dt.strftime('%b %d, %H:%M')} - {end_dt.strftime('%H:%M UTC')}"
        except:
            arrival_text = f"{arrival_start} - {arrival_end}"
        
        # Create severity-specific message
        severity_text = {
            "SEVERE": "🔴 SEVERE SPACE WEATHER ALERT",
            "HIGH": "🟠 HIGH SPACE WEATHER ALERT", 
            "MODERATE": "🟡 MODERATE SPACE WEATHER ALERT"
        }.get(severity, "SPACE WEATHER ALERT")
        
        event_description = {
            "CME": "Coronal Mass Ejection",
            "FLARE": "Solar Flare",
            "SEP": "Solar Energetic Particle Event",
            "GEO_STORM": "Geomagnetic Storm"
        }.get(forecast.event, forecast.event)
        
        impacts_text = self._format_impacts(forecast.impacts)
        
        message = f"""{severity_text}
        
{event_description} detected with {forecast.confidence:.0%} confidence.

Expected Earth Impact: {arrival_text}

Potential Effects: {impacts_text}

Risk Summary: {forecast.risk_summary}

Monitor conditions and take appropriate precautions for affected systems."""
        
        return message.strip()
    
    def _format_impacts(self, impacts: List[str]) -> str:
        """Format impact list for human reading"""
        impact_descriptions = {
            "aurora_lowlat": "Aurora visible at low latitudes",
            "aurora_midlat": "Aurora visible at mid-latitudes", 
            "aurora_highlat": "Aurora visible at high latitudes",
            "HF_comms": "HF radio communication disruptions",
            "GNSS_jitter": "GPS/GNSS navigation accuracy degradation",
            "satellite_ops": "Satellite operations affected",
            "power_grid": "Power grid voltage fluctuations"
        }
        
        formatted_impacts = []
        for impact in impacts:
            description = impact_descriptions.get(impact, impact.replace("_", " ").title())
            formatted_impacts.append(description)
        
        return ", ".join(formatted_impacts)


class MonitorService:
    """Main monitoring service that coordinates forecasting and alerting"""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        notification_service: NotificationService,
        websocket_manager=None,
        config: Optional[MonitorConfig] = None
    ):
        self.db_manager = db_manager
        self.notification_service = notification_service
        self.websocket_manager = websocket_manager
        self.config = config or MonitorConfig()
        self.analyzer = EventAnalyzer(self.config)
        
        self._running = False
        self._tasks = []
    
    async def start(self):
        """Start the monitoring service"""
        if self._running:
            return
        
        self._running = True
        await self.db_manager.log_system_event("INFO", "monitor", "Starting monitoring service")
        
        # Start monitoring tasks
        self._tasks = [
            asyncio.create_task(self._routine_forecast_loop()),
            asyncio.create_task(self._maintenance_loop()),
            asyncio.create_task(self._alert_cleanup_loop())
        ]
        
        print("Monitoring service started")
    
    async def stop(self):
        """Stop the monitoring service"""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        await self.db_manager.log_system_event("INFO", "monitor", "Monitoring service stopped")
        print("Monitoring service stopped")
    
    async def _routine_forecast_loop(self):
        """Main forecast generation and monitoring loop"""
        while self._running:
            try:
                await self._generate_and_analyze_forecast()
                
                # Wait for next iteration
                await asyncio.sleep(self.config.routine_interval_minutes * 60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                await self.db_manager.log_system_event(
                    "ERROR", "monitor", f"Forecast loop error: {e}"
                )
                # Wait a bit before retrying
                await asyncio.sleep(60)
    
    async def _generate_and_analyze_forecast(self):
        """Generate a forecast and analyze it for alerts"""
        try:
            # Check if we need a new forecast
            recent_forecast = await self.db_manager.get_latest_forecast(max_age_hours=0.5)
            
            if recent_forecast:
                await self.db_manager.log_system_event(
                    "INFO", "monitor", "Using recent forecast for analysis"
                )
                # Use recent forecast
                forecast_bundle = ForecastBundle.model_validate(recent_forecast.forecast_data)
            else:
                # Generate new forecast
                await self.db_manager.log_system_event(
                    "INFO", "monitor", "Generating new forecast"
                )
                
                config = ForecastConfig(days_back=3, max_tokens=1500)
                forecaster = SpaceWeatherForecaster(config)
                result = forecaster.generate_forecast()
                
                if isinstance(result, ForecastBundle):
                    forecast_bundle = result
                    # Store in database
                    await self.db_manager.store_forecast(forecast_bundle)
                else:
                    await self.db_manager.log_system_event(
                        "ERROR", "monitor", f"Forecast generation failed: {result.error}"
                    )
                    return
            
            # Analyze forecast for alerts
            alerts = self.analyzer.analyze_forecast(forecast_bundle)
            
            # Process any new alerts
            for alert_info in alerts:
                await self._process_alert(alert_info, forecast_bundle)
                
        except Exception as e:
            await self.db_manager.log_system_event(
                "ERROR", "monitor", f"Forecast analysis error: {e}"
            )
    
    async def _process_alert(self, alert_info: Dict[str, Any], forecast_bundle: ForecastBundle):
        """Process and distribute a new alert"""
        try:
            # Check if similar alert already exists
            active_alerts = await self.db_manager.get_active_alerts()
            
            # Simple duplicate check based on event type and severity
            duplicate = any(
                alert.event_type == alert_info["event_type"] and 
                alert.severity == alert_info["severity"]
                for alert in active_alerts
            )
            
            if duplicate:
                await self.db_manager.log_system_event(
                    "INFO", "monitor", f"Skipping duplicate alert: {alert_info['event_type']}-{alert_info['severity']}"
                )
                return
            
            # Store alert in database
            alert_id = await self.db_manager.store_alert(
                event_type=alert_info["event_type"],
                severity=alert_info["severity"],
                message=alert_info["message"]
            )
            
            # Send notifications
            await self.notification_service.send_alert_notifications(alert_info)
            
            # Broadcast to websocket clients if available
            if self.websocket_manager:
                await self.websocket_manager.broadcast({
                    "type": "new_alert",
                    "data": {
                        "id": alert_id,
                        "event_type": alert_info["event_type"],
                        "severity": alert_info["severity"],
                        "message": alert_info["message"],
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                })
            
            await self.db_manager.log_system_event(
                "INFO", "monitor", 
                f"Alert generated: {alert_info['event_type']}-{alert_info['severity']}",
                {"alert_id": alert_id}
            )
            
        except Exception as e:
            await self.db_manager.log_system_event(
                "ERROR", "monitor", f"Alert processing error: {e}"
            )
    
    async def _maintenance_loop(self):
        """Periodic maintenance tasks"""
        while self._running:
            try:
                # Clean up old data
                await self.db_manager.cleanup_old_data(keep_days=90)
                
                # Expire old alerts
                await self.db_manager.expire_old_alerts()
                
                await self.db_manager.log_system_event(
                    "INFO", "monitor", "Maintenance tasks completed"
                )
                
                # Wait for next maintenance cycle
                await asyncio.sleep(self.config.cleanup_interval_hours * 3600)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                await self.db_manager.log_system_event(
                    "ERROR", "monitor", f"Maintenance error: {e}"
                )
                await asyncio.sleep(3600)  # Wait 1 hour before retry
    
    async def _alert_cleanup_loop(self):
        """Clean up expired alerts"""
        while self._running:
            try:
                await self.db_manager.expire_old_alerts()
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                await self.db_manager.log_system_event(
                    "ERROR", "monitor", f"Alert cleanup error: {e}"
                )
                await asyncio.sleep(300)
    
    async def force_forecast_check(self):
        """Manually trigger a forecast check (for API endpoints)"""
        await self._generate_and_analyze_forecast()


# Standalone monitoring service runner
async def run_monitor_service():
    """Run the monitoring service as a standalone application"""
    from database import DatabaseManager
    from notifications import NotificationService
    
    # Initialize components
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    notification_service = NotificationService()
    
    monitor_service = MonitorService(
        db_manager=db_manager,
        notification_service=notification_service
    )
    
    try:
        await monitor_service.start()
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("Shutting down monitor service...")
    finally:
        await monitor_service.stop()
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(run_monitor_service())