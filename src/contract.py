# src/contract.py
"""
Contract specification module for SKYT pipeline
Handles contract creation from prompts and templates
"""

from typing import Dict, Any, Optional
import json


def create_prompt_contract(prompt_id: str, prompt: str, function_name: Optional[str] = None, 
                          oracle: Optional[str] = None, requires_recursion: bool = False,
                          language: str = "python", signature: Optional[str] = None) -> Dict[str, Any]:
    """
    Create contract specification from prompt parameters
    
    Args:
        prompt_id: Unique identifier for the prompt
        prompt: The actual prompt text
        function_name: Required function name
        oracle: Oracle test identifier
        requires_recursion: Whether recursion is required
        language: Programming language
        signature: Expected function signature
    
    Returns:
        Contract specification dict
    """
    contract = {
        "id": prompt_id,
        "prompt": prompt,
        "language": language,
        "version": "1.0"
    }
    
    if function_name:
        contract["function_name"] = function_name
    
    if oracle:
        contract["oracle"] = oracle
    
    if requires_recursion:
        contract["requires_recursion"] = True
    
    if signature:
        contract["signature"] = signature
    
    return contract


def load_contract_from_template(template_path: str, template_id: str) -> Dict[str, Any]:
    """
    Load contract from template file
    
    Args:
        template_path: Path to templates.json file
        template_id: ID of template to load
    
    Returns:
        Contract specification dict
    """
    try:
        with open(template_path, 'r') as f:
            templates = json.load(f)
        
        for template in templates:
            if template.get("id") == template_id:
                return create_prompt_contract(
                    prompt_id=template["id"],
                    prompt=template["prompt"],
                    function_name=template.get("enforce_function_name"),
                    oracle=template.get("oracle"),
                    requires_recursion=template.get("requires_recursion", False)
                )
        
        raise ValueError(f"Template {template_id} not found")
        
    except Exception as e:
        raise RuntimeError(f"Failed to load contract template: {str(e)}")


def validate_contract(contract: Dict[str, Any]) -> bool:
    """
    Validate contract specification
    
    Args:
        contract: Contract dict to validate
    
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["id", "prompt"]
    
    for field in required_fields:
        if field not in contract:
            return False
    
    return True
