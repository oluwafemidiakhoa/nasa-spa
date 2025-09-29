"""
Universal forecaster that can use Claude, OpenAI, or Hugging Face
Auto-detects available clients and falls back gracefully
"""

import os
import json
import logging
from typing import Union, Dict, Any, List, Optional
from pydantic import BaseModel

# Import our schemas
from .schema import ForecastBundle, ForecastError
from .nasa_client import NASAClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UniversalAIClient:
    """Universal AI client that can use multiple providers"""
    
    def __init__(self, preferred_provider: str = "auto"):
        self.preferred_provider = preferred_provider
        self.available_clients = {}
        self.active_client = None
        self.client_type = None
        
        # Try to initialize clients in order of preference
        self._detect_and_init_clients()
    
    def _detect_and_init_clients(self):
        """Detect available AI providers and initialize them"""
        
        # Try Claude first (if working)
        try:
            from .claude_client import ClaudeClient
            if os.getenv("ANTHROPIC_API_KEY"):
                claude_client = ClaudeClient()
                self.available_clients["claude"] = claude_client
                logger.info("Claude client available")
        except Exception as e:
            logger.warning(f"Claude client not available: {e}")
        
        # Try OpenAI
        try:
            from .openai_client import OpenAIClient
            if os.getenv("OPENAI_API_KEY"):
                openai_client = OpenAIClient()
                self.available_clients["openai"] = openai_client
                logger.info("OpenAI client available")
        except Exception as e:
            logger.warning(f"OpenAI client not available: {e}")
        
        # Try Hugging Face
        try:
            from .huggingface_client import HuggingFaceClient
            # HuggingFace can work without API key (local models)
            hf_client = HuggingFaceClient(use_local=True)
            self.available_clients["huggingface"] = hf_client
            logger.info("Hugging Face client available")
        except Exception as e:
            logger.warning(f"Hugging Face client not available: {e}")
        
        # Select active client based on preference and availability
        self._select_active_client()
    
    def _select_active_client(self):
        """Select the active client based on preference and availability"""
        
        if self.preferred_provider != "auto" and self.preferred_provider in self.available_clients:
            self.active_client = self.available_clients[self.preferred_provider]
            self.client_type = self.preferred_provider
            logger.info(f"Using preferred provider: {self.preferred_provider}")
            return
        
        # Auto-select based on quality/preference order
        preference_order = ["claude", "openai", "huggingface"]
        
        for provider in preference_order:
            if provider in self.available_clients:
                self.active_client = self.available_clients[provider]
                self.client_type = provider
                logger.info(f"Auto-selected provider: {provider}")
                return
        
        # No clients available
        raise RuntimeError("No AI providers available. Please check your API keys and dependencies.")
    
    def generate_forecast_with_schema(
        self, 
        system_prompt: str, 
        user_blocks: List[Dict[str, Any]], 
        schema_model: type,
        max_tokens: int = 1500
    ) -> Union[BaseModel, Dict[str, Any]]:
        """Generate forecast using the active AI client"""
        
        if not self.active_client:
            return {"error": "No AI client available", "error_code": "NO_CLIENT"}
        
        try:
            logger.info(f"Generating forecast using {self.client_type}")
            result = self.active_client.generate_forecast_with_schema(
                system_prompt=system_prompt,
                user_blocks=user_blocks,
                schema_model=schema_model,
                max_tokens=max_tokens
            )
            return result
            
        except Exception as e:
            logger.error(f"Forecast generation failed with {self.client_type}: {e}")
            # Try to fallback to next available client
            return self._try_fallback(system_prompt, user_blocks, schema_model, max_tokens)
    
    def _try_fallback(
        self, 
        system_prompt: str, 
        user_blocks: List[Dict[str, Any]], 
        schema_model: type,
        max_tokens: int
    ) -> Union[BaseModel, Dict[str, Any]]:
        """Try fallback to other available clients"""
        
        current_client = self.client_type
        remaining_clients = [k for k in self.available_clients.keys() if k != current_client]
        
        for client_name in remaining_clients:
            try:
                logger.info(f"Trying fallback to {client_name}")
                client = self.available_clients[client_name]
                result = client.generate_forecast_with_schema(
                    system_prompt=system_prompt,
                    user_blocks=user_blocks,
                    schema_model=schema_model,
                    max_tokens=max_tokens
                )
                
                # Update active client if successful
                self.active_client = client
                self.client_type = client_name
                logger.info(f"Successfully fell back to {client_name}")
                return result
                
            except Exception as e:
                logger.error(f"Fallback to {client_name} failed: {e}")
                continue
        
        # All clients failed
        return {
            "error": "All AI providers failed", 
            "error_code": "ALL_PROVIDERS_FAILED"
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all available clients"""
        return {
            "active_client": self.client_type,
            "available_clients": list(self.available_clients.keys()),
            "preferred_provider": self.preferred_provider
        }

def run_universal_forecast(
    days_back: int = 3,
    epic_date_iso: Optional[str] = None,
    ai_provider: str = "auto",
    max_tokens: int = 1500
) -> Union[ForecastBundle, ForecastError]:
    """
    Universal forecast function that works with any available AI provider
    
    Args:
        days_back: Days to look back for space weather events
        epic_date_iso: Specific date for EPIC imagery (optional)
        ai_provider: Preferred AI provider ("auto", "claude", "openai", "huggingface")
        max_tokens: Maximum tokens for AI response
    
    Returns:
        ForecastBundle with forecasts or ForecastError if failed
    """
    
    try:
        # Initialize universal AI client
        ai_client = UniversalAIClient(preferred_provider=ai_provider)
        logger.info(f"Active AI provider: {ai_client.client_type}")
        
        # Fetch NASA data
        nasa_client = NASAClient()
        cmes = nasa_client.fetch_donki_cmes(days_back=days_back)
        flares = nasa_client.fetch_donki_flares(days_back=days_back)
        sep_events = nasa_client.fetch_donki_sep_events(days_back=days_back)
        geo_storms = nasa_client.fetch_donki_geomagnetic_storms(days_back=days_back)
        
        # Get EPIC data
        import datetime as dt
        epic_date_iso = epic_date_iso or dt.date.today().isoformat()
        epic_list = nasa_client.fetch_epic_date(epic_date_iso)
        
        # Build user content blocks
        user_blocks = [
            {"type": "text", "text": f"""
Space Weather Analysis Request:

DONKI CME Events (last {days_back} days):
{json.dumps(cmes[:5], indent=2)}

DONKI Flare Events (last {days_back} days):
{json.dumps(flares[:5], indent=2)}

DONKI SEP Events (last {days_back} days):
{json.dumps(sep_events[:3], indent=2)}

DONKI Geomagnetic Storms (last {days_back} days):
{json.dumps(geo_storms[:3], indent=2)}

EPIC Earth Imagery ({epic_date_iso}):
{json.dumps(epic_list[:3], indent=2)}

GIBS Time URL: {nasa_client.gibs_tile_url(epic_date_iso)}

Tasks:
1) Review space weather events and identify Earth-directed or geo-effective events
2) Predict arrival times and impact windows for significant events
3) Assess risks to technology systems and aurora visibility
4) Provide confidence levels and cite evidence sources
5) Return 0-3 forecasts maximum based on event significance

Rules:
- Only cite actual DONKI IDs and EPIC timestamps from the data above
- If no significant impacts expected, return empty forecasts array
- Provide realistic confidence scores based on data quality
- Include specific impact types and risk summaries
"""}]
        
        # System prompt for space weather analysis
        system_prompt = """You are a space weather analyst expert. Analyze solar events and Earth observations to forecast potential geomagnetic impacts.

Use the provided NASA DONKI and EPIC data to generate evidence-based forecasts. Focus on:
- CME arrival predictions based on speed and direction
- Flare associations with CMEs for enhanced effects  
- Geomagnetic storm potential and Kp index estimates
- Aurora visibility and communication impacts
- GNSS and satellite system risks

Return structured JSON forecasts with confidence scores and evidence citations."""
        
        # Generate forecast
        result = ai_client.generate_forecast_with_schema(
            system_prompt=system_prompt,
            user_blocks=user_blocks,
            schema_model=ForecastBundle,
            max_tokens=max_tokens
        )
        
        # Handle different result types
        if isinstance(result, ForecastBundle):
            return result
        elif isinstance(result, dict) and "error" in result:
            return ForecastError(
                error=result["error"],
                error_code=result.get("error_code", "GENERATION_FAILED")
            )
        else:
            # Try to convert dict to ForecastBundle
            try:
                return ForecastBundle.model_validate(result)
            except Exception as e:
                return ForecastError(
                    error=f"Failed to validate result: {e}",
                    error_code="VALIDATION_FAILED"
                )
    
    except Exception as e:
        logger.error(f"Universal forecast failed: {e}")
        return ForecastError(
            error=f"Forecast pipeline failed: {str(e)}",
            error_code="PIPELINE_FAILED"
        )

# Export the main function
__all__ = ["run_universal_forecast", "UniversalAIClient"]