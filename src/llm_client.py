# src/llm_client.py
"""
Unified LLM Client Interface for SKYT Experiments

This module provides a stable interface for all LLM interactions,
regardless of the underlying provider (OpenAI, Anthropic, OpenRouter, etc.).

Architecture:
    LLMClient (public interface)
        └── LLMProvider (abstract base)
                ├── OpenAIProvider
                ├── AnthropicProvider
                └── OpenRouterProvider

Usage:
    # Auto-detect provider from environment
    client = LLMClient()
    
    # Explicit provider selection
    client = LLMClient(provider="anthropic", model="claude-3-5-sonnet-20241022")
    
    # Generate code
    code = client.generate_code(prompt, temperature=0.5)
"""

import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List


# =============================================================================
# Configuration
# =============================================================================

class Provider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"


@dataclass
class LLMConfig:
    """Configuration for LLM client"""
    provider: Provider
    model: str
    api_key: str
    max_tokens: int = 2000
    system_prompt: str = "You are a Python code generator. Generate only clean, working Python code without explanations."
    
    @classmethod
    def from_environment(cls) -> 'LLMConfig':
        """Create config from environment variables"""
        # Determine provider
        provider_str = os.environ.get("SKYT_PROVIDER", "openai").lower()
        
        try:
            provider = Provider(provider_str)
        except ValueError:
            raise ValueError(f"Unknown provider: {provider_str}. Supported: {[p.value for p in Provider]}")
        
        # Get API key based on provider
        api_key = cls._get_api_key(provider)
        
        # Get model (with provider-specific defaults)
        model = os.environ.get("SKYT_MODEL") or cls._default_model(provider)
        
        return cls(
            provider=provider,
            model=model,
            api_key=api_key
        )
    
    @staticmethod
    def _get_api_key(provider: Provider) -> str:
        """Get API key for provider from environment"""
        key_map = {
            Provider.OPENAI: "OPENAI_API_KEY",
            Provider.ANTHROPIC: "ANTHROPIC_API_KEY",
            Provider.OPENROUTER: "OPENROUTER_API_KEY",
        }
        
        env_var = key_map[provider]
        api_key = os.environ.get(env_var)
        
        if not api_key:
            raise ValueError(
                f"API key required for {provider.value}. "
                f"Set {env_var} environment variable."
            )
        
        return api_key
    
    @staticmethod
    def _default_model(provider: Provider) -> str:
        """Get default model for provider"""
        defaults = {
            Provider.OPENAI: "gpt-4o-mini",
            Provider.ANTHROPIC: "claude-3-5-sonnet-20241022",
            Provider.OPENROUTER: "anthropic/claude-3.5-sonnet",
        }
        return defaults[provider]


# =============================================================================
# Abstract Provider Interface
# =============================================================================

class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All provider implementations must implement this interface.
    This ensures a stable API regardless of the underlying LLM service.
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.model = config.model
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: User prompt
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum tokens to generate (uses config default if None)
            system_prompt: Override system prompt (uses config default if None)
            
        Returns:
            Generated text
            
        Raises:
            LLMError: If generation fails
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name for logging"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Return provider info for metrics"""
        return {
            "provider": self.provider_name,
            "model": self.model,
        }


# =============================================================================
# Provider Implementations
# =============================================================================

class OpenAIProvider(LLMProvider):
    """OpenAI API provider (GPT-4, GPT-3.5, etc.)"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            import openai
            self.client = openai.OpenAI(api_key=config.api_key)
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt or self.config.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens or self.config.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise LLMError(f"OpenAI generation failed: {e}")


class AnthropicProvider(LLMProvider):
    """Anthropic API provider (Claude models)"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=config.api_key)
        except ImportError:
            raise ImportError("anthropic package required. Install with: pip install anthropic")
    
    @property
    def provider_name(self) -> str:
        return "anthropic"
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.config.max_tokens,
                system=system_prompt or self.config.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature
            )
            return response.content[0].text
        except Exception as e:
            raise LLMError(f"Anthropic generation failed: {e}")


class OpenRouterProvider(LLMProvider):
    """OpenRouter API provider (unified access to multiple models)"""
    
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=config.api_key,
                base_url=self.OPENROUTER_BASE_URL
            )
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")
    
    @property
    def provider_name(self) -> str:
        return "openrouter"
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt or self.config.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens or self.config.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise LLMError(f"OpenRouter generation failed: {e}")


# =============================================================================
# Custom Exception
# =============================================================================

class LLMError(Exception):
    """Exception raised for LLM-related errors"""
    pass


# =============================================================================
# Provider Factory
# =============================================================================

def create_provider(config: LLMConfig) -> LLMProvider:
    """
    Factory function to create the appropriate provider.
    
    Args:
        config: LLM configuration
        
    Returns:
        LLMProvider instance
    """
    providers = {
        Provider.OPENAI: OpenAIProvider,
        Provider.ANTHROPIC: AnthropicProvider,
        Provider.OPENROUTER: OpenRouterProvider,
    }
    
    provider_class = providers.get(config.provider)
    if not provider_class:
        raise ValueError(f"Unknown provider: {config.provider}")
    
    return provider_class(config)


# =============================================================================
# Main Client Interface (Public API)
# =============================================================================

class LLMClient:
    """
    Unified LLM client with stable interface.
    
    This is the ONLY class that should be used by the rest of the codebase.
    All LLM interactions go through this client.
    
    Examples:
        # Default configuration from environment
        client = LLMClient()
        
        # Explicit provider and model
        client = LLMClient(provider="anthropic", model="claude-3-5-sonnet-20241022")
        
        # Generate code
        code = client.generate_code("Write a fibonacci function", temperature=0.5)
    """
    
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize LLM client.
        
        Args:
            provider: Provider name ("openai", "anthropic", "openrouter")
                     If None, uses SKYT_PROVIDER env var or defaults to "openai"
            model: Model name. If None, uses SKYT_MODEL env var or provider default
            api_key: API key. If None, uses provider-specific env var
        """
        # Build config
        if provider or model or api_key:
            # Explicit configuration
            provider_enum = Provider(provider or os.environ.get("SKYT_PROVIDER", "openai"))
            config = LLMConfig(
                provider=provider_enum,
                model=model or os.environ.get("SKYT_MODEL") or LLMConfig._default_model(provider_enum),
                api_key=api_key or LLMConfig._get_api_key(provider_enum)
            )
        else:
            # Auto-detect from environment
            config = LLMConfig.from_environment()
        
        self._config = config
        self._provider = create_provider(config)
        
        # Public attributes for compatibility
        self.model = config.model
        self.provider_name = self._provider.provider_name
    
    def generate_code(self, prompt: str, temperature: float = 0.0) -> str:
        """
        Generate Python code from prompt.
        
        This is the PRIMARY method for code generation in SKYT experiments.
        
        Args:
            prompt: The code generation prompt
            temperature: Sampling temperature (0.0 = deterministic)
            
        Returns:
            Generated Python code as string
            
        Raises:
            LLMError: If generation fails
        """
        raw_output = self._provider.generate(prompt, temperature=temperature)
        
        # Extract Python code from response
        code = self._extract_python_code(raw_output)
        
        return code
    
    def generate_raw(self, prompt: str, temperature: float = 0.0) -> str:
        """
        Generate raw text without code extraction.
        
        Args:
            prompt: The prompt
            temperature: Sampling temperature
            
        Returns:
            Raw generated text
        """
        return self._provider.generate(prompt, temperature=temperature)
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get client info for metrics and logging.
        
        Returns:
            Dict with provider, model, and other metadata
        """
        return {
            **self._provider.get_info(),
            "temperature_support": True,
            "max_tokens": self._config.max_tokens,
        }
    
    def _extract_python_code(self, text: str) -> str:
        """Extract Python code from LLM response"""
        if not text:
            return ""
        
        # Try python-specific code block first
        code_block_pattern = r'```python\n(.*?)\n```'
        match = re.search(code_block_pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Try generic code block
        code_block_pattern = r'```\n(.*?)\n```'
        match = re.search(code_block_pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Return raw text if no code blocks found
        return text.strip()
    
    def __repr__(self) -> str:
        return f"LLMClient(provider={self.provider_name!r}, model={self.model!r})"


# =============================================================================
# Convenience Functions
# =============================================================================

def get_available_providers() -> List[str]:
    """Return list of available provider names"""
    return [p.value for p in Provider]


def get_default_model(provider: str) -> str:
    """Get default model for a provider"""
    return LLMConfig._default_model(Provider(provider))


# =============================================================================
# Backward Compatibility
# =============================================================================

# These are kept for backward compatibility with existing code
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MODEL = os.environ.get("SKYT_MODEL", "gpt-4o-mini")
