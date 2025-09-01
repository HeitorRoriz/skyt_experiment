# src/llm.py
"""
LLM interface module for SKYT pipeline
Provides unified LLM API access with routing to adapters
"""

import os
from typing import List, Dict, Any
from openai import OpenAI


def query_llm(messages: List[Dict[str, str]], model: str, temperature: float) -> str:
    """
    Query LLM with messages
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model identifier
        temperature: Temperature parameter
    
    Returns:
        LLM response string
    """
    # Route to OpenAI adapter for now
    return _openai_complete_chat(messages, model, temperature)


def _openai_complete_chat(messages: List[Dict[str, str]], model: str, temperature: float) -> str:
    """
    Complete chat using OpenAI API
    
    Args:
        messages: Chat messages
        model: OpenAI model name
        temperature: Temperature parameter
    
    Returns:
        Response content string
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    client = OpenAI(api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content
    
    except Exception as e:
        raise RuntimeError(f"OpenAI API call failed: {str(e)}")


# Legacy compatibility function
def call_llm_simple(prompt: str, model: str = "gpt-4o-mini", temperature: float = 0.0) -> str:
    """Legacy compatibility wrapper"""
    messages = [{"role": "user", "content": prompt}]
    return query_llm(messages, model, temperature)
