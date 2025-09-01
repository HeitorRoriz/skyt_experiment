# src/intent_capture.py
"""
Intent capture and normalization for SKYT pipeline
Handles developer and user intent extraction and conflict resolution
"""

from typing import Dict, Any, Optional, Tuple
import re


def extract_dev_intent(prompt: str) -> Optional[str]:
    """
    Extract developer implementation intent from prompt
    
    Args:
        prompt: Raw prompt string
    
    Returns:
        Developer intent string or None
    """
    # Look for implementation-specific keywords and patterns
    dev_patterns = [
        r"implement(?:ation)?\s+(?:using|with|via)\s+([^.]+)",
        r"use\s+([^.]+)\s+(?:approach|method|algorithm)",
        r"(?:recursive|iterative|dynamic|memoized)\s+(?:approach|implementation|solution)",
        r"(?:bottom-up|top-down)\s+approach"
    ]
    
    for pattern in dev_patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    
    return None


def extract_user_intent(prompt: str) -> Optional[str]:
    """
    Extract user behavioral intent from prompt
    
    Args:
        prompt: Raw prompt string
    
    Returns:
        User intent string or None
    """
    # Look for behavioral expectations and requirements
    user_patterns = [
        r"should\s+(?:return|output|produce)\s+([^.]+)",
        r"expected\s+(?:behavior|output|result):\s*([^.]+)",
        r"must\s+(?:handle|support|work with)\s+([^.]+)",
        r"(?:calculate|compute|find|generate)\s+([^.]+)"
    ]
    
    for pattern in user_patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    
    return None


def normalize_intent_dev(raw_intent: str) -> str:
    """
    Normalize developer intent to standard form
    
    Args:
        raw_intent: Raw developer intent string
    
    Returns:
        Normalized intent string
    """
    if not raw_intent:
        return ""
    
    # Convert to lowercase and normalize whitespace
    normalized = re.sub(r'\s+', ' ', raw_intent.lower().strip())
    
    # Standardize common terms
    replacements = {
        'recursive': 'recursion',
        'iterative': 'iteration', 
        'dynamic programming': 'dynamic_programming',
        'memoization': 'memoized',
        'bottom up': 'bottom_up',
        'top down': 'top_down'
    }
    
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    
    return normalized


def normalize_intent_user(raw_intent: str) -> str:
    """
    Normalize user intent to standard form
    
    Args:
        raw_intent: Raw user intent string
    
    Returns:
        Normalized intent string
    """
    if not raw_intent:
        return ""
    
    # Convert to lowercase and normalize whitespace
    normalized = re.sub(r'\s+', ' ', raw_intent.lower().strip())
    
    # Standardize behavioral terms
    replacements = {
        'should return': 'returns',
        'must handle': 'handles',
        'expected to': 'should',
        'calculate': 'computes',
        'generate': 'produces'
    }
    
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    
    return normalized


def resolve_conflicts(dev_intent: Optional[str], user_intent: Optional[str]) -> Dict[str, Any]:
    """
    Resolve conflicts between developer and user intents
    
    Args:
        dev_intent: Developer implementation intent
        user_intent: User behavioral intent
    
    Returns:
        Dict with resolved intents and conflict notes
    """
    conflicts = []
    resolved_dev = dev_intent
    resolved_user = user_intent
    
    # Check for obvious conflicts
    if dev_intent and user_intent:
        # Example: recursive implementation vs iterative behavior expectation
        if 'recursive' in dev_intent.lower() and 'iterative' in user_intent.lower():
            conflicts.append("dev_wants_recursion_user_expects_iteration")
        
        # Example: memoization vs simple implementation
        if 'memoized' in dev_intent.lower() and 'simple' in user_intent.lower():
            conflicts.append("dev_wants_optimization_user_expects_simple")
    
    return {
        "dev_intent": resolved_dev,
        "user_intent": resolved_user,
        "conflicts": conflicts,
        "resolution_strategy": "prefer_dev_intent" if conflicts else "no_conflicts"
    }


def extract_and_normalize_intents(prompt: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract and normalize both dev and user intents from prompt
    
    Args:
        prompt: Raw prompt string
    
    Returns:
        Tuple of (normalized_dev_intent, normalized_user_intent)
    """
    raw_dev = extract_dev_intent(prompt)
    raw_user = extract_user_intent(prompt)
    
    normalized_dev = normalize_intent_dev(raw_dev) if raw_dev else None
    normalized_user = normalize_intent_user(raw_user) if raw_user else None
    
    return normalized_dev, normalized_user
