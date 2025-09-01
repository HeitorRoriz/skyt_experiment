# src/transform.py
"""
Code transformation and prompt building for SKYT pipeline
Handles LLM prompt generation and code repair attempts
"""

from typing import Dict, Any, Optional, List


def build_llm_prompt_for_code(contract: Dict[str, Any], dev_intent: Optional[str] = None, user_intent: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Build LLM prompt messages from contract and intents
    
    Args:
        contract: Contract specification dict
        dev_intent: Developer implementation intent
        user_intent: User behavioral intent
    
    Returns:
        List of message dicts for LLM API
    """
    system_message = compose_system_message(contract)
    
    # Build user prompt from contract
    user_prompt = contract.get("prompt", "")
    
    # Enhance with intents if provided
    if dev_intent:
        user_prompt += f"\n\nImplementation approach: {dev_intent}"
    
    if user_intent:
        user_prompt += f"\n\nExpected behavior: {user_intent}"
    
    # Add contract constraints
    constraints = []
    if contract.get("function_name"):
        constraints.append(f"Function must be named '{contract['function_name']}'")
    
    if contract.get("requires_recursion"):
        constraints.append("Implementation must use recursion")
    
    if contract.get("language"):
        constraints.append(f"Use {contract['language']} language")
    
    if constraints:
        user_prompt += f"\n\nConstraints:\n" + "\n".join(f"- {c}" for c in constraints)
    
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_prompt}
    ]


def compose_system_message(contract: Dict[str, Any]) -> str:
    """
    Compose system message for LLM based on contract
    
    Args:
        contract: Contract specification
    
    Returns:
        System message string
    """
    base_message = "You are a helpful programming assistant. Generate clean, working Python code that meets the specified requirements."
    
    # Add contract-specific instructions
    if contract.get("requires_recursion"):
        base_message += " Use recursive implementation where specified."
    
    if contract.get("function_name"):
        base_message += f" Ensure the main function is named '{contract['function_name']}'."
    
    base_message += " Provide only the code without additional explanation unless requested."
    
    return base_message


def try_repair(code: str, contract: Dict[str, Any]) -> Optional[str]:
    """
    Attempt to repair code to meet contract requirements
    
    Args:
        code: Python code string that failed compliance
        contract: Contract specification
    
    Returns:
        Repaired code string or None if repair not possible
    """
    # TODO: Implement AST-based repair strategies
    # For now, return None to indicate no repair attempted
    return None
