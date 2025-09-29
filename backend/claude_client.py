"""
Anthropic Claude client for Space Weather Forecaster
Handles structured JSON output and multimodal analysis
"""

import os
import json
from anthropic import Anthropic
from pydantic import BaseModel, TypeAdapter
from typing import Type, Any, Dict, List, Union
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

class ClaudeClient:
    """Client for Anthropic Claude with structured JSON schema support"""
    
    def __init__(self, api_key: str = None, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key or ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable.")
        
        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        
        # Verify model supports structured outputs
        self.supported_models = [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022", 
            "claude-3-opus-20240229"
        ]
        
        if model not in self.supported_models:
            logger.warning(f"Model {model} may not support structured JSON output. Recommended: {self.supported_models[0]}")

    def parse_with_schema(
        self, 
        system: str, 
        user_blocks: List[Dict[str, Any]], 
        schema: Dict[str, Any], 
        max_tokens: int = 1500,
        temperature: float = 0.1
    ) -> str:
        """
        Generate structured JSON response using Claude with schema validation
        
        Args:
            system: System message defining Claude's role and constraints
            user_blocks: List of content blocks (text, image, etc.)
            schema: JSON schema for structured output
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (lower = more deterministic)
            
        Returns:
            Raw JSON string from Claude
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                system=system,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": user_blocks}],
                extra_headers={"anthropic-beta": "max-tokens-3-5-sonnet-2024-07-15"}
            )
            
            # Extract text content from response
            if response.content and len(response.content) > 0:
                content = response.content[0]
                if hasattr(content, 'text'):
                    return content.text
                else:
                    logger.error(f"Unexpected content type: {type(content)}")
                    return "{\"forecasts\": [], \"error\": \"Invalid response format\"}"
            else:
                logger.error("Empty response from Claude")
                return "{\"forecasts\": [], \"error\": \"Empty response\"}"
                
        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            return f"{{\"forecasts\": [], \"error\": \"API call failed: {str(e)}\"}}"

    def validate_and_parse_json(self, raw_json: str, model_class: Type[BaseModel]) -> Union[BaseModel, Dict[str, Any]]:
        """
        Validate and parse JSON response against Pydantic model
        
        Args:
            raw_json: Raw JSON string from Claude
            model_class: Pydantic model class for validation
            
        Returns:
            Validated Pydantic model instance or error dict
        """
        try:
            # First, try to parse as JSON
            parsed_data = json.loads(raw_json)
            
            # Then validate against Pydantic model
            validated_model = model_class.model_validate(parsed_data)
            return validated_model
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return {"error": f"Invalid JSON: {str(e)}", "raw_response": raw_json}
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return {"error": f"Validation failed: {str(e)}", "raw_response": raw_json}

    def generate_forecast_with_schema(
        self, 
        system_prompt: str, 
        user_blocks: List[Dict[str, Any]], 
        schema_model: Type[BaseModel],
        max_tokens: int = 1500
    ) -> Union[BaseModel, Dict[str, Any]]:
        """
        Complete pipeline: generate structured forecast and validate
        
        Args:
            system_prompt: System message for Claude
            user_blocks: User content blocks
            schema_model: Pydantic model for validation
            max_tokens: Maximum response tokens
            
        Returns:
            Validated forecast model or error dict
        """
        # Generate JSON schema from Pydantic model
        schema = TypeAdapter(schema_model).json_schema()
        
        # Add JSON format instruction to system prompt
        enhanced_system = f"""{system_prompt}

CRITICAL: You must respond with valid JSON that exactly matches this schema:
{json.dumps(schema, indent=2)}

Do not include any text before or after the JSON. Only return the JSON object."""
        
        # Get raw JSON from Claude
        raw_json = self.parse_with_schema(
            system=enhanced_system,
            user_blocks=user_blocks,
            schema=schema,
            max_tokens=max_tokens
        )
        
        # Validate and return
        return self.validate_and_parse_json(raw_json, schema_model)

    def create_image_block(self, image_url: str, description: str = None) -> Dict[str, Any]:
        """
        Create an image content block for multimodal input
        
        Args:
            image_url: URL to the image
            description: Optional description of the image
            
        Returns:
            Image content block for Claude messages
        """
        block = {
            "type": "image",
            "source": {
                "type": "url",
                "url": image_url
            }
        }
        
        if description:
            # Add description as a separate text block
            return [
                {"type": "text", "text": f"Image description: {description}"},
                block
            ]
        
        return block

    def create_text_block(self, text: str) -> Dict[str, Any]:
        """Create a text content block"""
        return {"type": "text", "text": text}

# Convenience function for quick access
def create_claude_client(api_key: str = None, model: str = "claude-3-5-sonnet-20241022") -> ClaudeClient:
    """Create a configured Claude client instance"""
    return ClaudeClient(api_key=api_key, model=model)