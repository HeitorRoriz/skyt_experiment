# src/llm_client.py
"""
Simple LLM client interface for SKYT experiments
Focuses on clean code generation without complex middleware
"""

import openai
import re
from typing import Optional
from .config import OPENAI_API_KEY, MODEL


class LLMClient:
    """Simple OpenAI client for code generation"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = MODEL):
        self.client = openai.OpenAI(api_key=api_key or OPENAI_API_KEY)
        self.model = model
        
        if not (api_key or OPENAI_API_KEY):
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
    
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Python code generator. Generate only clean, working Python code without explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=1000
            )
            
            raw_output = response.choices[0].message.content
            
            # Extract Python code from response
            code = self._extract_python_code(raw_output)
            
            return code
            
        except Exception as e:
            raise RuntimeError(f"LLM generation failed: {e}")
    
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
