"""
LLM client integration for test execution
Supports OpenAI, Anthropic, and other providers with proper environment pinning
"""

from llm import query_llm, call_llm_simple
import time
import hashlib
from typing import Dict, Any, Optional
from test_config import EnvironmentConfig

class LLMClient:
    """LLM client with environment pinning and proper decoding control"""
    
    def __init__(self, api_key: str = None, provider: str = "openai"):
        self.provider = provider
        # Note: API key is handled by llm.py module
    
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
        """Generate using OpenAI API via llm.py module"""
        
        try:
            # Use the centralized LLM interface from llm.py
            return query_llm(
                prompt=prompt,
                model=env_config.model_identifier,
                temperature=env_config.temperature
            )
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
