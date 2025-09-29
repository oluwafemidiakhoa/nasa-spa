"""
Hugging Face client for Space Weather Forecaster
Alternative to Claude using local or hosted Hugging Face models
"""

import os
import json
import logging
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from pydantic import BaseModel, TypeAdapter
from typing import Type, Any, Dict, List, Union, Optional
import torch

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")  # Optional for hosted inference
HF_MODEL = os.getenv("HUGGINGFACE_MODEL", "microsoft/DialoGPT-medium")

class HuggingFaceClient:
    """Client for Hugging Face models with structured JSON schema support"""
    
    def __init__(self, 
                 api_key: str = None, 
                 model_name: str = "microsoft/DialoGPT-medium",
                 use_local: bool = True,
                 device: str = "auto"):
        self.api_key = api_key or HF_API_KEY
        self.model_name = model_name
        self.use_local = use_local
        
        # Determine device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        logger.info(f"Using device: {self.device}")
        
        # Initialize model based on local vs hosted
        if use_local:
            self._init_local_model()
        else:
            self._init_hosted_model()
        
        # Recommended models for different use cases
        self.recommended_models = {
            "chat": ["microsoft/DialoGPT-medium", "microsoft/DialoGPT-large"],
            "text_generation": ["gpt2", "gpt2-medium", "distilgpt2"],
            "instruction_following": ["microsoft/DialoGPT-medium", "facebook/blenderbot-400M-distill"],
            "lightweight": ["distilgpt2", "microsoft/DialoGPT-small"]
        }

    def _init_local_model(self):
        """Initialize local Hugging Face model"""
        try:
            logger.info(f"Loading local model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Add padding token if it doesn't exist
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None
            )
            
            if self.device == "cpu":
                self.model = self.model.to(self.device)
                
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1
            )
            
            logger.info("Local model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load local model: {e}")
            logger.info("Falling back to hosted inference...")
            self.use_local = False
            self._init_hosted_model()

    def _init_hosted_model(self):
        """Initialize hosted Hugging Face inference API"""
        try:
            from huggingface_hub import InferenceClient
            self.inference_client = InferenceClient(
                model=self.model_name,
                token=self.api_key
            )
            logger.info("Hosted inference client initialized")
        except ImportError:
            logger.error("huggingface_hub not installed. Install with: pip install huggingface_hub")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize hosted model: {e}")
            raise

    def parse_with_schema(
        self, 
        system: str, 
        user_blocks: List[Dict[str, Any]], 
        schema: Dict[str, Any], 
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> str:
        """
        Generate structured JSON response using Hugging Face model
        
        Args:
            system: System message defining the AI's role and constraints
            user_blocks: List of content blocks (text content)
            schema: JSON schema for structured output
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            
        Returns:
            Raw JSON string from the model
        """
        try:
            # Convert user blocks to text
            user_content = ""
            for block in user_blocks:
                if block.get("type") == "text":
                    user_content += block.get("text", "") + "\n\n"
            
            # Create prompt with JSON schema instructions
            prompt = f"""System: {system}

You must respond with valid JSON that matches this exact schema:
{json.dumps(schema, indent=2)}

Instructions:
- Only return the JSON object, no other text
- Use the exact field names and types specified
- Ensure all required fields are included

User Input:
{user_content}

JSON Response:"""

            if self.use_local:
                return self._generate_local(prompt, max_tokens, temperature)
            else:
                return self._generate_hosted(prompt, max_tokens, temperature)
                
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return f'{{"forecasts": [], "error": "Generation failed: {str(e)}"}}'

    def _generate_local(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate response using local model"""
        try:
            # Generate response
            outputs = self.pipeline(
                prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                return_full_text=False
            )
            
            if outputs and len(outputs) > 0:
                generated_text = outputs[0]['generated_text'].strip()
                # Try to extract JSON from the response
                return self._extract_json(generated_text)
            else:
                return '{"forecasts": [], "error": "No output generated"}'
                
        except Exception as e:
            logger.error(f"Local generation failed: {e}")
            return f'{{"forecasts": [], "error": "Local generation failed: {str(e)}"}}'

    def _generate_hosted(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate response using hosted inference API"""
        try:
            response = self.inference_client.text_generation(
                prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                return_full_text=False
            )
            
            if response:
                return self._extract_json(response.strip())
            else:
                return '{"forecasts": [], "error": "No response from hosted model"}'
                
        except Exception as e:
            logger.error(f"Hosted generation failed: {e}")
            return f'{{"forecasts": [], "error": "Hosted generation failed: {str(e)}"}}'

    def _extract_json(self, text: str) -> str:
        """Extract JSON from generated text"""
        try:
            # Look for JSON object in the text
            start_idx = text.find('{')
            if start_idx == -1:
                # No JSON found, create minimal response
                return '{"forecasts": [], "error": "No JSON found in response"}'
            
            # Find the matching closing brace
            brace_count = 0
            end_idx = start_idx
            for i, char in enumerate(text[start_idx:], start_idx):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            json_str = text[start_idx:end_idx]
            
            # Validate it's proper JSON
            json.loads(json_str)
            return json_str
            
        except (json.JSONDecodeError, ValueError):
            # If extraction fails, return minimal response
            return '{"forecasts": [], "error": "Could not extract valid JSON"}'

    def validate_and_parse_json(self, raw_json: str, model_class: Type[BaseModel]) -> Union[BaseModel, Dict[str, Any]]:
        """
        Validate and parse JSON response against Pydantic model
        """
        try:
            parsed_data = json.loads(raw_json)
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
        max_tokens: int = 512
    ) -> Union[BaseModel, Dict[str, Any]]:
        """
        Complete pipeline: generate structured forecast and validate
        """
        # Generate JSON schema from Pydantic model
        schema = TypeAdapter(schema_model).json_schema()
        
        # Get raw JSON from model
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
def create_huggingface_client(
    api_key: str = None, 
    model_name: str = "microsoft/DialoGPT-medium",
    use_local: bool = True
) -> HuggingFaceClient:
    """Create a configured Hugging Face client instance"""
    return HuggingFaceClient(api_key=api_key, model_name=model_name, use_local=use_local)