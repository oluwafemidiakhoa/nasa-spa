"""
Flexible scheduling system for NASA Space Weather Forecaster
Supports cron-style scheduling, time zones, and automated forecasting
"""

import os
import asyncio
import json
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.jobstores.memory import MemoryJobStore
    from apscheduler.executors.asyncio import AsyncIOExecutor
    APScheduler_AVAILABLE = True
except ImportError:
    APScheduler_AVAILABLE = False

import pytz
from croniter import croniter

from backend.forecaster import SpaceWeatherForecaster, ForecastConfig
from backend.database import DatabaseManager
from backend.notifications import NotificationService
from backend.monitor import MonitorService


class ScheduleType(Enum):
    """Types of scheduled jobs"""
    FORECAST = "forecast"
    MONITORING = "monitoring"
    MAINTENANCE = "maintenance"
    CUSTOM = "custom"


@dataclass
class ScheduledJob:
    """Definition of a scheduled job"""
    id: str
    name: str
    schedule_type: ScheduleType
    cron_expression: str
    timezone: str = "UTC"
    enabled: bool = True
    max_retries: int = 3
    retry_delay_seconds: int = 60
    timeout_seconds: Optional[int] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    failure_count: int = 0
    success_count: int = 0


class SchedulerService:
    """Main scheduler service for automated forecasting and maintenance"""
    
    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        notification_service: Optional[NotificationService] = None,
        timezone: str = "UTC"
    ):
        self.db_manager = db_manager
        self.notification_service = notification_service
        self.timezone = pytz.timezone(timezone)
        
        # Initialize scheduler if APScheduler is available
        if APScheduler_AVAILABLE:
            self.scheduler = AsyncIOScheduler(
                jobstores={'default': MemoryJobStore()},
                executors={'default': AsyncIOExecutor()},
                timezone=self.timezone
            )
        else:
            self.scheduler = None
            print("APScheduler not available, using simple timer-based scheduling")
        
        self.jobs: Dict[str, ScheduledJob] = {}
        self._running = False
        self._simple_tasks: List[asyncio.Task] = []
    
    async def start(self):
        """Start the scheduler service"""
        if self._running:
            return
        
        self._running = True
        
        if self.scheduler:
            self.scheduler.start()
        
        # Load default jobs
        await self._load_default_jobs()
        
        # Start simple scheduler if APScheduler not available
        if not self.scheduler:
            await self._start_simple_scheduler()
        
        if self.db_manager:
            await self.db_manager.log_system_event("INFO", "scheduler", "Scheduler service started")
        
        print("Scheduler service started")
    
    async def stop(self):
        """Stop the scheduler service"""
        if not self._running:
            return
        
        self._running = False
        
        if self.scheduler:
            self.scheduler.shutdown(wait=False)
        
        # Cancel simple scheduler tasks
        for task in self._simple_tasks:
            task.cancel()
        
        if self._simple_tasks:
            await asyncio.gather(*self._simple_tasks, return_exceptions=True)
        
        if self.db_manager:
            await self.db_manager.log_system_event("INFO", "scheduler", "Scheduler service stopped")
        
        print("Scheduler service stopped")
    
    async def _load_default_jobs(self):
        """Load default scheduled jobs"""
        default_jobs = [
            # Regular forecast generation every 30 minutes
            ScheduledJob(
                id="routine_forecast",
                name="Routine Space Weather Forecast",
                schedule_type=ScheduleType.FORECAST,
                cron_expression="*/30 * * * *",  # Every 30 minutes
                parameters={"days_back": 3, "include_images": False}
            ),
            
            # Priority forecast during high-activity periods (every 10 minutes during 06-22 UTC)
            ScheduledJob(
                id="priority_forecast",
                name="Priority Forecast (High Activity Hours)",
                schedule_type=ScheduleType.FORECAST,
                cron_expression="*/10 6-22 * * *",  # Every 10 minutes, 06-22 UTC
                parameters={"days_back": 3, "include_images": True, "max_tokens": 2000}
            ),
            
            # Comprehensive forecast twice daily
            ScheduledJob(
                id="comprehensive_forecast",
                name="Comprehensive Daily Forecast",
                schedule_type=ScheduleType.FORECAST,
                cron_expression="0 0,12 * * *",  # Midnight and noon UTC
                parameters={"days_back": 5, "include_images": True, "max_tokens": 2500}
            ),
            
            # Database maintenance daily at 2 AM UTC
            ScheduledJob(
                id="database_maintenance",
                name="Database Maintenance",
                schedule_type=ScheduleType.MAINTENANCE,
                cron_expression="0 2 * * *",  # 2 AM UTC daily
                parameters={"cleanup_days": 90}
            ),
            
            # Alert cleanup every 5 minutes
            ScheduledJob(
                id="alert_cleanup",
                name="Alert Cleanup",
                schedule_type=ScheduleType.MAINTENANCE,
                cron_expression="*/5 * * * *",  # Every 5 minutes
                parameters={}
            )
        ]
        
        for job in default_jobs:
            await self.add_job(job)
    
    async def add_job(self, job: ScheduledJob) -> bool:
        """Add a scheduled job"""
        try:
            if not self._is_valid_cron(job.cron_expression):
                raise ValueError(f"Invalid cron expression: {job.cron_expression}")
            
            self.jobs[job.id] = job
            
            if self.scheduler:
                # Add to APScheduler
                trigger = CronTrigger.from_crontab(
                    job.cron_expression,
                    timezone=pytz.timezone(job.timezone)
                )
                
                self.scheduler.add_job(
                    func=self._execute_job_wrapper,
                    trigger=trigger,
                    args=[job.id],
                    id=job.id,
                    name=job.name,
                    replace_existing=True,
                    max_instances=1
                )
            
            # Calculate next run time
            job.next_run = self._calculate_next_run(job)
            
            if self.db_manager:
                await self.db_manager.log_system_event(
                    "INFO", "scheduler", f"Job added: {job.name}",
                    {"job_id": job.id, "cron": job.cron_expression}
                )
            
            return True
            
        except Exception as e:
            if self.db_manager:
                await self.db_manager.log_system_event(
                    "ERROR", "scheduler", f"Failed to add job {job.id}: {e}"
                )
            return False
    
    async def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job"""
        try:
            if job_id not in self.jobs:
                return False
            
            if self.scheduler:
                self.scheduler.remove_job(job_id)
            
            del self.jobs[job_id]
            
            if self.db_manager:
                await self.db_manager.log_system_event(
                    "INFO", "scheduler", f"Job removed: {job_id}"
                )
            
            return True
            
        except Exception as e:
            if self.db_manager:
                await self.db_manager.log_system_event(
                    "ERROR", "scheduler", f"Failed to remove job {job_id}: {e}"
                )
            return False
    
    async def enable_job(self, job_id: str) -> bool:
        """Enable a scheduled job"""
        if job_id not in self.jobs:
            return False
        
        self.jobs[job_id].enabled = True
        
        if self.scheduler:
            self.scheduler.resume_job(job_id)
        
        return True
    
    async def disable_job(self, job_id: str) -> bool:
        """Disable a scheduled job"""
        if job_id not in self.jobs:
            return False
        
        self.jobs[job_id].enabled = False
        
        if self.scheduler:
            self.scheduler.pause_job(job_id)
        
        return True
    
    async def run_job_now(self, job_id: str) -> bool:
        """Manually trigger a job to run immediately"""
        if job_id not in self.jobs:
            return False
        
        try:
            await self._execute_job(job_id)
            return True
        except Exception as e:
            if self.db_manager:
                await self.db_manager.log_system_event(
                    "ERROR", "scheduler", f"Manual job execution failed {job_id}: {e}"
                )
            return False
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status information for a job"""
        if job_id not in self.jobs:
            return None
        
        job = self.jobs[job_id]
        
        return {
            "id": job.id,
            "name": job.name,
            "schedule_type": job.schedule_type.value,
            "cron_expression": job.cron_expression,
            "enabled": job.enabled,
            "last_run": job.last_run.isoformat() + "Z" if job.last_run else None,
            "next_run": job.next_run.isoformat() + "Z" if job.next_run else None,
            "success_count": job.success_count,
            "failure_count": job.failure_count
        }
    
    async def list_jobs(self) -> List[Dict[str, Any]]:
        """List all scheduled jobs with their status"""
        return [await self.get_job_status(job_id) for job_id in self.jobs.keys()]
    
    async def _execute_job_wrapper(self, job_id: str):
        """Wrapper for job execution with error handling"""
        try:
            await self._execute_job(job_id)
        except Exception as e:
            if self.db_manager:
                await self.db_manager.log_system_event(
                    "ERROR", "scheduler", f"Job execution failed {job_id}: {e}"
                )
    
    async def _execute_job(self, job_id: str):
        """Execute a scheduled job"""
        if job_id not in self.jobs:
            return
        
        job = self.jobs[job_id]
        
        if not job.enabled:
            return
        
        job.last_run = datetime.utcnow()
        job.next_run = self._calculate_next_run(job)
        
        try:
            if job.schedule_type == ScheduleType.FORECAST:
                await self._execute_forecast_job(job)
            elif job.schedule_type == ScheduleType.MAINTENANCE:
                await self._execute_maintenance_job(job)
            else:
                if self.db_manager:
                    await self.db_manager.log_system_event(
                        "WARNING", "scheduler", f"Unknown job type: {job.schedule_type}"
                    )
            
            job.success_count += 1
            job.failure_count = 0  # Reset failure count on success
            
        except Exception as e:
            job.failure_count += 1
            
            if self.db_manager:
                await self.db_manager.log_system_event(
                    "ERROR", "scheduler", f"Job {job_id} failed: {e}",
                    {"failure_count": job.failure_count}
                )
            
            # Implement retry logic if needed
            if job.failure_count < job.max_retries:
                await asyncio.sleep(job.retry_delay_seconds)
                await self._execute_job(job_id)
    
    async def _execute_forecast_job(self, job: ScheduledJob):
        """Execute a forecast generation job"""
        config = ForecastConfig(
            days_back=job.parameters.get("days_back", 3),
            include_images=job.parameters.get("include_images", False),
            max_tokens=job.parameters.get("max_tokens", 1500)
        )
        
        forecaster = SpaceWeatherForecaster(config)
        result = forecaster.generate_forecast()
        
        if self.db_manager:
            if hasattr(result, 'forecasts'):  # ForecastBundle
                await self.db_manager.store_forecast(result)
                await self.db_manager.log_system_event(
                    "INFO", "scheduler", f"Forecast generated: {len(result.forecasts)} forecasts"
                )
            else:  # ForecastError
                await self.db_manager.log_system_event(
                    "ERROR", "scheduler", f"Forecast generation failed: {result.error}"
                )
    
    async def _execute_maintenance_job(self, job: ScheduledJob):
        """Execute a maintenance job"""
        if job.id == "database_maintenance" and self.db_manager:
            cleanup_days = job.parameters.get("cleanup_days", 90)
            await self.db_manager.cleanup_old_data(keep_days=cleanup_days)
            await self.db_manager.log_system_event(
                "INFO", "scheduler", f"Database cleanup completed (kept {cleanup_days} days)"
            )
        
        elif job.id == "alert_cleanup" and self.db_manager:
            await self.db_manager.expire_old_alerts()
    
    async def _start_simple_scheduler(self):
        """Start simple timer-based scheduling (fallback if APScheduler unavailable)"""
        for job_id, job in self.jobs.items():
            if job.enabled:
                task = asyncio.create_task(self._simple_job_loop(job_id))
                self._simple_tasks.append(task)
    
    async def _simple_job_loop(self, job_id: str):
        """Simple job execution loop"""
        while self._running:
            try:
                job = self.jobs.get(job_id)
                if not job or not job.enabled:
                    await asyncio.sleep(60)
                    continue
                
                # Check if it's time to run
                now = datetime.utcnow()
                if job.next_run and now >= job.next_run:
                    await self._execute_job(job_id)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.db_manager:
                    await self.db_manager.log_system_event(
                        "ERROR", "scheduler", f"Simple scheduler error for {job_id}: {e}"
                    )
                await asyncio.sleep(60)
    
    def _calculate_next_run(self, job: ScheduledJob) -> Optional[datetime]:
        """Calculate the next run time for a job"""
        try:
            cron = croniter(job.cron_expression, datetime.utcnow())
            return cron.get_next(datetime)
        except:
            return None
    
    def _is_valid_cron(self, cron_expression: str) -> bool:
        """Validate a cron expression"""
        try:
            croniter(cron_expression, datetime.utcnow())
            return True
        except:
            return False
    
    def add_custom_job(
        self,
        job_id: str,
        name: str,
        cron_expression: str,
        callback: Callable,
        parameters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add a custom job with a callback function"""
        # This would require more complex implementation to store callbacks
        # For now, just log the request
        if self.db_manager:
            asyncio.create_task(
                self.db_manager.log_system_event(
                    "INFO", "scheduler", f"Custom job requested: {name}",
                    {"job_id": job_id, "cron": cron_expression}
                )
            )
        return False  # Not implemented in this version


# Standalone scheduler service
async def run_scheduler_service():
    """Run the scheduler service as a standalone application"""
    from database import DatabaseManager
    from notifications import NotificationService
    
    # Initialize components
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    notification_service = NotificationService()
    
    scheduler_service = SchedulerService(
        db_manager=db_manager,
        notification_service=notification_service
    )
    
    try:
        await scheduler_service.start()
        
        print("Scheduler service running. Press Ctrl+C to stop.")
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("Shutting down scheduler service...")
    finally:
        await scheduler_service.stop()
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(run_scheduler_service())