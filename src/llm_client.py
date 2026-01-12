# src/llm_client.py
"""
Simple LLM client interface for SKYT experiments
Focuses on clean code generation without complex middleware
"""

import openai
import re
from typing import Optional
from .config import OPENAI_API_KEY, MODEL
import os


class LLMClient:
    """Multi-provider LLM client for code generation (OpenAI and Anthropic)"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = MODEL):
        self.model = model
        self.provider = self._detect_provider(model)
        
        if self.provider == "openai":
            self.client = openai.OpenAI(api_key=api_key or OPENAI_API_KEY)
            if not (api_key or OPENAI_API_KEY):
                raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
        elif self.provider == "anthropic":
            try:
                import anthropic
                anthropic_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
                if not anthropic_key:
                    raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY environment variable.")
                self.client = anthropic.Anthropic(api_key=anthropic_key)
            except ImportError:
                raise ImportError("anthropic package required for Claude models. Install with: pip install anthropic")
        else:
            raise ValueError(f"Unsupported model: {model}")
    
    def _detect_provider(self, model: str) -> str:
        """Detect LLM provider from model name"""
        if model.startswith("gpt-") or model.startswith("o1-"):
            return "openai"
        elif model.startswith("claude-"):
            return "anthropic"
        else:
            # Default to OpenAI for backward compatibility
            return "openai"
    
    def generate_code(self, prompt: str, temperature: float = 0.0) -> str:
        """
        Generate code from prompt
        
        Args:
            prompt: The code generation prompt
            temperature: Sampling temperature (0.0 = deterministic)
            
        Returns:
            Generated code as string
        """
        try:
            if self.provider == "openai":
                raw_output = self._generate_openai(prompt, temperature)
            elif self.provider == "anthropic":
                raw_output = self._generate_anthropic(prompt, temperature)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            # Extract Python code from response
            code = self._extract_python_code(raw_output)
            
            return code
            
        except Exception as e:
            raise RuntimeError(f"LLM generation failed: {e}")
    
    def _generate_openai(self, prompt: str, temperature: float) -> str:
        """Generate code using OpenAI API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a Python code generator. Generate only clean, working Python code without explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=1000
        )
        return response.choices[0].message.content
    
    def _generate_anthropic(self, prompt: str, temperature: float) -> str:
        """Generate code using Anthropic API"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            temperature=temperature,
            system="You are a Python code generator. Generate only clean, working Python code without explanations.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    
    def _extract_python_code(self, text: str) -> str:
        """Extract Python code from LLM response"""
        # Look for code blocks
        code_block_pattern = r'```python\n(.*?)\n```'
        match = re.search(code_block_pattern, text, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        # Look for code without markdown
        code_block_pattern = r'```\n(.*?)\n```'
        match = re.search(code_block_pattern, text, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        # Return raw text if no code blocks found
        return text.strip()
