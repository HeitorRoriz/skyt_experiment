"""
LLM client integration for test execution
Supports OpenAI, Anthropic, and other providers with proper environment pinning
"""

import openai
import time
import hashlib
from typing import Dict, Any, Optional
from test_config import EnvironmentConfig

class LLMClient:
    """LLM client with environment pinning and proper decoding control"""
    
    def __init__(self, api_key: str, provider: str = "openai"):
        self.api_key = api_key
        self.provider = provider
        
        if provider == "openai":
            openai.api_key = api_key
    
    def generate_code(self, prompt: str, env_config: EnvironmentConfig) -> str:
        """
        Generate code using LLM with exact environment pinning
        
        Args:
            prompt: The prompt text
            env_config: Environment configuration with model, temperature, etc.
            
        Returns:
            Raw LLM output
        """
        if self.provider == "openai":
            return self._openai_generate(prompt, env_config)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _openai_generate(self, prompt: str, env_config: EnvironmentConfig) -> str:
        """Generate using OpenAI API"""
        
        # Prepare request parameters
        request_params = {
            "model": env_config.model_identifier,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": env_config.temperature,
            "max_tokens": 1000  # Adjust as needed
        }
        
        # Add optional parameters if specified
        if env_config.top_p is not None:
            request_params["top_p"] = env_config.top_p
        if env_config.seed is not None:
            request_params["seed"] = env_config.seed
        
        try:
            response = openai.chat.completions.create(**request_params)
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise RuntimeError(f"LLM API call failed: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get actual model information for environment fingerprinting"""
        # This should return the exact model identifier as returned by the provider
        # Important for cache key generation
        return {
            "provider": self.provider,
            "timestamp": time.time()
        }
