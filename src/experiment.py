# src/experiment.py
"""
Thin wrapper around OpenAI API (chat.completions)
"""

import openai
from typing import Optional
from .config import OPENAI_API_KEY, DEFAULT_MODEL, DEFAULT_TEMPERATURE


class LLMClient:
    """Simple OpenAI client wrapper"""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model: str = DEFAULT_MODEL,
                 temperature: float = DEFAULT_TEMPERATURE):
        """
        Initialize LLM client
        
        Args:
            api_key: OpenAI API key (uses config default if None)
            model: Model name (uses config default if not specified)
            temperature: Temperature setting (uses config default if not specified)
        """
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model
        self.temperature = temperature
        
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")
        
        # Initialize OpenAI client
        openai.api_key = self.api_key
    
    def generate_code(self, prompt: str) -> str:
        """
        Generate code using OpenAI chat completions
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            Generated code as string
            
        Raises:
            Exception: If API call fails
        """
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a Python programming assistant. Generate clean, working Python code based on the user's request. Only return the code, no explanations or markdown formatting."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=1000,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"OpenAI API call failed: {str(e)}")
    
    def set_temperature(self, temperature: float):
        """Update temperature setting"""
        self.temperature = temperature
    
    def set_model(self, model: str):
        """Update model setting"""
        self.model = model
