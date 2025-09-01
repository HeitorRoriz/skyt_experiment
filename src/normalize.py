# src/normalize.py
"""
Code parsing and extraction utilities for SKYT pipeline
Handles extraction of code and reflection from raw LLM outputs
"""

import re
from typing import Optional, Tuple


def extract_code(raw_output: str) -> str:
    """
    Extract Python code from raw LLM output
    Handles various formats: fenced, unfenced, mixed responses
    
    Args:
        raw_output: Raw LLM response string
    
    Returns:
        Extracted Python code string
    """
    if not raw_output or not raw_output.strip():
        return ""
    
    # Strategy 1: Look for fenced code blocks
    fenced_code = _extract_fenced_code(raw_output)
    if fenced_code:
        return fenced_code
    
    # Strategy 2: Look for python/py language specifiers
    lang_code = _extract_language_specified_code(raw_output)
    if lang_code:
        return lang_code
    
    # Strategy 3: Fallback - find longest code-like block
    return _extract_longest_code_block(raw_output)


def extract_reflection(raw_output: str) -> Optional[str]:
    """
    Extract reflection/explanation from LLM output if present
    
    Args:
        raw_output: Raw LLM response string
    
    Returns:
        Reflection text or None if not found
    """
    # Look for JSON-like reflection at end
    json_match = re.search(r'\{[^}]*"reflection"[^}]*\}', raw_output, re.IGNORECASE | re.DOTALL)
    if json_match:
        return json_match.group(0)
    
    # Look for explanation after code
    lines = raw_output.split('\n')
    code_ended = False
    reflection_lines = []
    
    for line in lines:
        if code_ended and line.strip():
            reflection_lines.append(line)
        elif line.strip() == '```' and not code_ended:
            code_ended = True
    
    if reflection_lines:
        return '\n'.join(reflection_lines).strip()
    
    return None


def _extract_fenced_code(text: str) -> Optional[str]:
    """Extract code from fenced code blocks (```...```)"""
    # Match fenced blocks with optional language specifier
    pattern = r'```(?:python|py)?\s*\n(.*?)\n```'
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    
    if matches:
        # Return the first (usually only) code block
        return matches[0].strip()
    
    return None


def _extract_language_specified_code(text: str) -> Optional[str]:
    """Extract code with python/py language specifiers"""
    # Look for python: or py: prefixed blocks
    patterns = [
        r'python:\s*\n(.*?)(?=\n\n|\Z)',
        r'py:\s*\n(.*?)(?=\n\n|\Z)',
        r'```python\s*\n(.*?)\n```',
        r'```py\s*\n(.*?)\n```'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            return matches[0].strip()
    
    return None


def _extract_longest_code_block(text: str) -> str:
    """Fallback: extract the longest code-like block"""
    lines = text.split('\n')
    code_blocks = []
    current_block = []
    
    for line in lines:
        # Heuristic: line looks like code if it has indentation or Python keywords
        if _looks_like_code(line):
            current_block.append(line)
        else:
            if current_block:
                code_blocks.append('\n'.join(current_block))
                current_block = []
    
    # Add final block if exists
    if current_block:
        code_blocks.append('\n'.join(current_block))
    
    # Return longest block, or entire text if no blocks found
    if code_blocks:
        return max(code_blocks, key=len).strip()
    else:
        return text.strip()


def _looks_like_code(line: str) -> bool:
    """Heuristic to determine if a line looks like Python code"""
    stripped = line.strip()
    
    if not stripped:
        return False
    
    # Check for Python keywords
    python_keywords = ['def ', 'class ', 'if ', 'else:', 'elif ', 'for ', 'while ', 
                      'return ', 'import ', 'from ', 'try:', 'except:', 'with ']
    
    for keyword in python_keywords:
        if stripped.startswith(keyword):
            return True
    
    # Check for indentation (likely code)
    if line.startswith('    ') or line.startswith('\t'):
        return True
    
    # Check for assignment or function calls
    if '=' in stripped or '(' in stripped:
        return True
    
    return False
