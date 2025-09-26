# src/prompt_builder.py
"""
Simple prompt builder for LLM queries
Replaces the functionality from the deleted transform.py module
"""

from typing import Dict, Any, List

def build_llm_prompt_for_code(contract: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Build LLM prompt messages from contract
    
    Args:
        contract: Contract specification dict
    
    Returns:
        List of message dicts for LLM API
    """
    prompt = contract.get("prompt", "Generate Python code.")
    
    # Build system message
    system_msg = "You are a Python code generator. Generate only clean, working Python code without explanations, comments, or markdown formatting."
    
    # Add function name requirement if specified
    function_name = contract.get("enforce_function_name")
    if function_name:
        system_msg += f" The function must be named '{function_name}'."
    
    # Add recursion requirement if specified
    if contract.get("requires_recursion", False):
        system_msg += " Use recursion in your implementation."
    
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": prompt}
    ]
    
    return messages
