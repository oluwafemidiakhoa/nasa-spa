"""
OpenAI client for Space Weather Forecaster
Alternative to Claude for structured JSON output and analysis
"""

import os
import json
import logging
from openai import OpenAI
from pydantic import BaseModel, TypeAdapter
from typing import Type, Any, Dict, List, Union

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class OpenAIClient:
    """Client for OpenAI with structured JSON schema support"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4-0125-preview"):
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        
        # Verify model supports structured outputs
        self.supported_models = [
            "gpt-4-0125-preview",
            "gpt-4-turbo-preview", 
            "gpt-4-1106-preview",
            "gpt-3.5-turbo-0125"
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
        Generate structured JSON response using OpenAI with schema validation
        
        Args:
            system: System message defining the AI's role and constraints
            user_blocks: List of content blocks (text content)
            schema: JSON schema for structured output
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (lower = more deterministic)
            
        Returns:
            Raw JSON string from OpenAI
        """
        try:
            # Convert user blocks to text (OpenAI doesn't use the same block format as Claude)
            user_content = ""
            for block in user_blocks:
                if block.get("type") == "text":
                    user_content += block.get("text", "") + "\n\n"
                elif block.get("type") == "image":
                    # Note: For image support, you'd need to use gpt-4-vision-preview
                    user_content += f"[IMAGE: {block.get('source', {}).get('url', 'Unknown image')}]\n\n"
            
            # Enhanced system prompt with JSON schema
            enhanced_system = f"""{system}

CRITICAL: You must respond with valid JSON that exactly matches this schema:
{json.dumps(schema, indent=2)}

Do not include any text before or after the JSON. Only return the JSON object.
Use the exact field names and types specified in the schema."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": enhanced_system},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                response_format={"type": "json_object"}  # Ensures JSON output
            )
            
            # Extract content from response
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content:
                    return content.strip()
                else:
                    logger.error("Empty response from OpenAI")
                    return '{"forecasts": [], "error": "Empty response"}'
            else:
                logger.error("No choices in OpenAI response")
                return '{"forecasts": [], "error": "No response choices"}'
                
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return f'{{"forecasts": [], "error": "API call failed: {str(e)}"}}'

    def validate_and_parse_json(self, raw_json: str, model_class: Type[BaseModel]) -> Union[BaseModel, Dict[str, Any]]:
        """
        Validate and parse JSON response against Pydantic model
        
        Args:
            raw_json: Raw JSON string from OpenAI
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
            system_prompt: System message for OpenAI
            user_blocks: User content blocks
            schema_model: Pydantic model for validation
            max_tokens: Maximum response tokens
            
        Returns:
            Validated forecast model or error dict
        """
        # Generate JSON schema from Pydantic model
        schema = TypeAdapter(schema_model).json_schema()
        
        # Get raw JSON from OpenAI
        raw_json = self.parse_with_schema(
            system=system_prompt,
            user_blocks=user_blocks,
            schema=schema,
            max_tokens=max_tokens
        )
        
        # Validate and return
        return self.validate_and_parse_json(raw_json, schema_model)

    def create_text_block(self, text: str) -> Dict[str, Any]:
        """Create a text content block"""
        return {"type": "text", "text": text}

# Convenience function for quick access
def create_openai_client(api_key: str = None, model: str = "gpt-4-0125-preview") -> OpenAIClient:
    """Create a configured OpenAI client instance"""
    return OpenAIClient(api_key=api_key, model=model)