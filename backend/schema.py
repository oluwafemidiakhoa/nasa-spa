"""
Pydantic schemas for NASA Space Weather Forecaster
Defines structured JSON output schemas for Claude AI responses
"""

from pydantic import BaseModel, Field, HttpUrl, conlist
from typing import List, Literal, Optional
from datetime import datetime

# Type definitions
EventKind = Literal["CME", "FLARE", "SEP", "GEO_STORM"]
ImpactType = Literal[
    "aurora_midlat", "aurora_highlat", "HF_comms", "GNSS_jitter", 
    "GNSS_outage", "satellite_drag", "radiation_storm", "power_grid"
]

class Evidence(BaseModel):
    """Evidence linking for forecast transparency and traceability"""
    donki_ids: List[str] = Field(
        ..., 
        description="Relevant DONKI event IDs used by the analysis",
        examples=[["CME-2025-09-26T14:30:00-CME-001", "FLR-2025-09-26T14:30:00-001"]]
    )
    epic_frames: List[str] = Field(
        ..., 
        description="ISO timestamps (UTC) or EPIC identifiers used as visual evidence",
        examples=[["2025-09-26T14:30:00", "2025-09-26T15:30:00"]]
    )
    gibs_layers: List[str] = Field(
        ..., 
        description="Layer names used (e.g., AURORA proxy, clouds, solar wind)",
        examples=[["VIIRS_SNPP_CorrectedReflectance_TrueColor", "MODIS_Terra_CorrectedReflectance_TrueColor"]]
    )

class Forecast(BaseModel):
    """Individual space weather forecast with confidence and evidence"""
    event: EventKind = Field(
        ..., 
        description="Type of space weather event being forecasted"
    )
    solar_timestamp: str = Field(
        ..., 
        description="UTC time of the initiating solar event if applicable (ISO 8601)",
        examples=["2025-09-26T14:30:00Z"]
    )
    predicted_arrival_window_utc: conlist(str, min_length=2, max_length=2) = Field(
        ..., 
        description="Start and end times of predicted Earth impact window (ISO 8601)",
        examples=[["2025-09-28T06:00:00Z", "2025-09-29T18:00:00Z"]]
    )
    risk_summary: str = Field(
        ..., 
        description="Human-readable summary of risks and expected impacts",
        examples=["Moderate geomagnetic storm expected. Aurora possible to mid-latitudes."]
    )
    impacts: List[ImpactType] = Field(
        ..., 
        description="List of affected domains and systems",
        examples=[["aurora_midlat", "HF_comms", "GNSS_jitter"]]
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Forecast confidence score between 0.0 and 1.0",
        examples=[0.75]
    )
    evidence: Evidence = Field(
        ..., 
        description="Supporting evidence and data sources for this forecast"
    )

class ForecastBundle(BaseModel):
    """Container for multiple forecasts in one response"""
    forecasts: List[Forecast] = Field(
        ..., 
        description="List of space weather forecasts (0-3 forecasts maximum)",
        max_length=3
    )
    generated_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="UTC timestamp when this forecast bundle was generated"
    )
    data_sources: List[str] = Field(
        default=["NASA_DONKI", "NASA_EPIC", "NASA_GIBS"],
        description="Data sources used in generating these forecasts"
    )

class ForecastError(BaseModel):
    """Error response schema for failed forecast attempts"""
    error: str = Field(..., description="Error message describing what went wrong")
    error_code: str = Field(..., description="Machine-readable error code")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="UTC timestamp when this error occurred"
    )
    
# Export schemas for use in other modules
__all__ = [
    "EventKind", 
    "ImpactType", 
    "Evidence", 
    "Forecast", 
    "ForecastBundle", 
    "ForecastError"
]