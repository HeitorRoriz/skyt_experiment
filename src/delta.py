# src/delta.py
"""
Delta comparison module for SKYT pipeline
Compares raw code vs canonical code for similarity analysis
"""

import difflib
from typing import Dict, Any, List, Tuple


def compute_similarity_score(raw_code: str, canon_code: str) -> float:
    """
    Compute similarity score between raw and canonical code
    
    Args:
        raw_code: Original code string
        canon_code: Canonicalized code string
    
    Returns:
        Similarity score between 0.0 and 1.0
    """
    if not raw_code and not canon_code:
        return 1.0
    
    if not raw_code or not canon_code:
        return 0.0
    
    # Use sequence matcher for similarity
    matcher = difflib.SequenceMatcher(None, raw_code, canon_code)
    return matcher.ratio()


def compute_line_deltas(raw_code: str, canon_code: str) -> Dict[str, Any]:
    """
    Compute line-by-line differences between raw and canonical code
    
    Args:
        raw_code: Original code string
        canon_code: Canonicalized code string
    
    Returns:
        Dict with delta statistics and diff lines
    """
    raw_lines = raw_code.splitlines()
    canon_lines = canon_code.splitlines()
    
    # Generate unified diff
    diff_lines = list(difflib.unified_diff(
        raw_lines, canon_lines,
        fromfile='raw_code',
        tofile='canon_code',
        lineterm=''
    ))
    
    # Count changes
    additions = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
    deletions = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))
    
    return {
        "raw_lines": len(raw_lines),
        "canon_lines": len(canon_lines),
        "additions": additions,
        "deletions": deletions,
        "total_changes": additions + deletions,
        "diff_lines": diff_lines[:50]  # Limit to first 50 lines for storage
    }


def analyze_code_delta(raw_code: str, canon_code: str) -> Dict[str, Any]:
    """
    Complete delta analysis between raw and canonical code
    
    Args:
        raw_code: Original code string
        canon_code: Canonicalized code string
    
    Returns:
        Complete delta analysis dict
    """
    similarity = compute_similarity_score(raw_code, canon_code)
    line_deltas = compute_line_deltas(raw_code, canon_code)
    
    # Character-level statistics
    raw_chars = len(raw_code)
    canon_chars = len(canon_code)
    char_reduction = (raw_chars - canon_chars) / raw_chars if raw_chars > 0 else 0.0
    
    return {
        "similarity_score": similarity,
        "char_reduction": char_reduction,
        "raw_char_count": raw_chars,
        "canon_char_count": canon_chars,
        **line_deltas
    }
