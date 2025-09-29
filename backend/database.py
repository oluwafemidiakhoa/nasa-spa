"""
Database management for NASA Space Weather Forecaster
SQLAlchemy models and data persistence layer
"""

import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import asyncio
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import desc, func, and_
import sqlite3

try:
    from backend.schema import ForecastBundle
except ImportError:
    from schema import ForecastBundle

Base = declarative_base()


class ForecastRecord(Base):
    """Database model for storing forecast data"""
    __tablename__ = "forecasts"
    
    id = Column(Integer, primary_key=True, index=True)
    forecast_data = Column(JSON)  # Store the complete ForecastBundle as JSON
    generated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Forecast metadata for easy querying
    forecast_count = Column(Integer, default=0)
    max_confidence = Column(Float, default=0.0)
    event_types = Column(String(500))  # Comma-separated event types
    
    # Accuracy tracking (populated after events occur)
    accuracy_score = Column(Float)  # 0.0 to 1.0 accuracy rating
    accuracy_evaluated = Column(Boolean, default=False)


class AlertRecord(Base):
    """Database model for storing active alerts"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), index=True)
    severity = Column(String(20), index=True)  # LOW, MODERATE, HIGH, SEVERE
    message = Column(Text)
    forecast_id = Column(Integer)  # Reference to associated forecast
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True, index=True)
    
    # Notification tracking
    email_sent = Column(Boolean, default=False)
    sms_sent = Column(Boolean, default=False)


class AlertSubscription(Base):
    """Database model for user alert subscriptions"""
    __tablename__ = "alert_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True)
    phone = Column(String(20))
    
    # Subscription preferences
    alert_types = Column(JSON)  # List of event types to receive alerts for
    min_confidence = Column(Float, default=0.6)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_notification = Column(DateTime(timezone=True))


class SystemLog(Base):
    """Database model for system logging and monitoring"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), index=True)  # INFO, WARNING, ERROR
    component = Column(String(50), index=True)  # api_server, monitor, scheduler, etc.
    message = Column(Text)
    details = Column(JSON)  # Additional structured data
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, database_url: Optional[str] = None):
        if database_url is None:
            # Default to SQLite for development
            db_path = os.path.join(os.path.dirname(__file__), "..", "space_weather.db")
            db_path = os.path.abspath(db_path)  # Convert to absolute path
            database_url = f"sqlite:///{db_path}"
        
        self.database_url = database_url
        self.engine = None
        self.async_engine = None
        self.session_factory = None
        self.async_session_factory = None
    
    async def initialize(self):
        """Initialize database connection and create tables"""
        try:
            # Create sync engine for database creation
            self.engine = create_engine(
                self.database_url.replace("sqlite://", "sqlite:///") if "sqlite://" in self.database_url else self.database_url,
                echo=False  # Set to True for SQL debugging
            )
            
            # Create async engine for operations
            if "sqlite://" in self.database_url:
                async_url = self.database_url.replace("sqlite://", "sqlite+aiosqlite://")
            else:
                async_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://")
            
            self.async_engine = create_async_engine(async_url, echo=False)
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            
            # Create session factories
            self.session_factory = sessionmaker(bind=self.engine)
            self.async_session_factory = async_sessionmaker(bind=self.async_engine, expire_on_commit=False)
            
            print(f"Database initialized: {self.database_url}")
            
        except Exception as e:
            print(f"Database initialization failed: {e}")
            raise
    
    async def close(self):
        """Close database connections"""
        if self.async_engine:
            await self.async_engine.dispose()
        if self.engine:
            self.engine.dispose()
    
    @asynccontextmanager
    async def get_session(self):
        """Get async database session with automatic cleanup"""
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def store_forecast(self, forecast: ForecastBundle) -> int:
        """Store a forecast in the database"""
        async with self.get_session() as session:
            # Extract metadata
            event_types = ",".join(set(f.event for f in forecast.forecasts)) if forecast.forecasts else ""
            max_confidence = max((f.confidence for f in forecast.forecasts), default=0.0)
            
            record = ForecastRecord(
                forecast_data=forecast.model_dump(),
                generated_at=datetime.fromisoformat(forecast.generated_at.replace("Z", "+00:00")),
                forecast_count=len(forecast.forecasts),
                max_confidence=max_confidence,
                event_types=event_types
            )
            
            session.add(record)
            await session.flush()  # Get the ID
            forecast_id = record.id
            
            return forecast_id
    
    async def get_latest_forecast(self, max_age_hours: int = 24) -> Optional[ForecastRecord]:
        """Get the most recent forecast within the specified age limit"""
        async with self.get_session() as session:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            result = await session.execute(
                select(ForecastRecord)
                .where(ForecastRecord.created_at >= cutoff_time)
                .order_by(desc(ForecastRecord.created_at))
                .limit(1)
            )
            
            return result.scalar_one_or_none()
    
    async def get_forecast_history(
        self,
        days_back: int = 7,
        limit: int = 50,
        event_type: Optional[str] = None
    ) -> List[ForecastRecord]:
        """Get historical forecasts with optional filtering"""
        async with self.get_session() as session:
            cutoff_time = datetime.utcnow() - timedelta(days=days_back)
            
            query = select(ForecastRecord).where(
                ForecastRecord.created_at >= cutoff_time
            ).order_by(desc(ForecastRecord.created_at)).limit(limit)
            
            if event_type:
                query = query.where(ForecastRecord.event_types.contains(event_type))
            
            result = await session.execute(query)
            return result.scalars().all()
    
    async def store_alert(
        self,
        event_type: str,
        severity: str,
        message: str,
        forecast_id: Optional[int] = None,
        expires_hours: int = 24
    ) -> int:
        """Store a new alert in the database"""
        async with self.get_session() as session:
            expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
            
            alert = AlertRecord(
                event_type=event_type,
                severity=severity,
                message=message,
                forecast_id=forecast_id,
                expires_at=expires_at
            )
            
            session.add(alert)
            await session.flush()
            return alert.id
    
    async def get_active_alerts(self) -> List[AlertRecord]:
        """Get all currently active alerts"""
        async with self.get_session() as session:
            now = datetime.utcnow()
            
            result = await session.execute(
                select(AlertRecord).where(
                    and_(
                        AlertRecord.is_active == True,
                        AlertRecord.expires_at > now
                    )
                ).order_by(desc(AlertRecord.created_at))
            )
            
            return result.scalars().all()
    
    async def expire_old_alerts(self):
        """Mark expired alerts as inactive"""
        async with self.get_session() as session:
            now = datetime.utcnow()
            
            await session.execute(
                AlertRecord.__table__.update()
                .where(AlertRecord.expires_at <= now)
                .values(is_active=False)
            )
    
    async def store_alert_subscription(
        self,
        email: Optional[str],
        phone: Optional[str],
        alert_types: List[str],
        min_confidence: float
    ) -> int:
        """Store a new alert subscription"""
        async with self.get_session() as session:
            subscription = AlertSubscription(
                email=email,
                phone=phone,
                alert_types=alert_types,
                min_confidence=min_confidence
            )
            
            session.add(subscription)
            await session.flush()
            return subscription.id
    
    async def get_alert_subscriptions(self, active_only: bool = True) -> List[AlertSubscription]:
        """Get all alert subscriptions"""
        async with self.get_session() as session:
            query = select(AlertSubscription)
            if active_only:
                query = query.where(AlertSubscription.is_active == True)
            
            result = await session.execute(query)
            return result.scalars().all()
    
    async def log_system_event(
        self,
        level: str,
        component: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log a system event"""
        async with self.get_session() as session:
            log_entry = SystemLog(
                level=level,
                component=component,
                message=message,
                details=details or {}
            )
            
            session.add(log_entry)
    
    async def get_accuracy_stats(self, days_back: int = 30) -> Dict[str, Any]:
        """Calculate forecast accuracy statistics"""
        async with self.get_session() as session:
            cutoff_time = datetime.utcnow() - timedelta(days=days_back)
            
            # Get evaluated forecasts
            result = await session.execute(
                select(
                    func.count(ForecastRecord.id).label("total_forecasts"),
                    func.avg(ForecastRecord.accuracy_score).label("avg_accuracy"),
                    func.count(ForecastRecord.accuracy_score).label("evaluated_forecasts")
                ).where(
                    and_(
                        ForecastRecord.created_at >= cutoff_time,
                        ForecastRecord.accuracy_evaluated == True
                    )
                )
            )
            
            stats = result.first()
            
            # Get accuracy by event type
            event_accuracy = await session.execute(
                select(
                    ForecastRecord.event_types,
                    func.avg(ForecastRecord.accuracy_score).label("accuracy")
                ).where(
                    and_(
                        ForecastRecord.created_at >= cutoff_time,
                        ForecastRecord.accuracy_evaluated == True
                    )
                ).group_by(ForecastRecord.event_types)
            )
            
            return {
                "period_days": days_back,
                "total_forecasts": stats.total_forecasts or 0,
                "evaluated_forecasts": stats.evaluated_forecasts or 0,
                "average_accuracy": float(stats.avg_accuracy or 0.0),
                "accuracy_by_event_type": {
                    row.event_types: float(row.accuracy)
                    for row in event_accuracy.fetchall()
                    if row.event_types
                }
            }
    
    async def cleanup_old_data(self, keep_days: int = 90):
        """Remove old data to manage database size"""
        async with self.get_session() as session:
            cutoff_time = datetime.utcnow() - timedelta(days=keep_days)
            
            # Remove old forecasts
            await session.execute(
                ForecastRecord.__table__.delete()
                .where(ForecastRecord.created_at < cutoff_time)
            )
            
            # Remove old logs
            await session.execute(
                SystemLog.__table__.delete()
                .where(SystemLog.created_at < cutoff_time)
            )
            
            # Remove old inactive alerts
            await session.execute(
                AlertRecord.__table__.delete()
                .where(
                    and_(
                        AlertRecord.created_at < cutoff_time,
                        AlertRecord.is_active == False
                    )
                )
            )