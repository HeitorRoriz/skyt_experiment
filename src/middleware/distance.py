# src/middleware/distance.py
"""
[TODO distance.py]
Goal: define signature and distance to canon. No code.

1. Normalization source: reuse existing normalize pipeline. Record normalization_version.
2. Signature: SHA-256 over normalized code bytes. Deterministic requirement documented.
3. Distance d:
   - Levenshtein over normalized text divided by max(len(a), len(b)). Range [0,1]. d=0 iff signatures equal.
   - This is a proxy; AST distance may replace it later without changing CSV schema.
4. Functions to specify:
   - compute_signature(normalized_text) -> str
   - compute_distance(output_text, canon) -> float d
   - record_pre_distance(...) and record_post_distance(...) append rows to CSV with schema from schema.py.
5. Acceptance: equal normalized text yields d=0 and identical signatures.
"""

import hashlib
from datetime import datetime
from typing import Optional
from .schema import (
    DistanceRecord, DISTANCES_PRE_CSV_PATH, DISTANCES_POST_CSV_PATH,
    NORMALIZATION_VERSION, ORACLE_VERSION
)
from .code_properties import extract_code_properties, properties_match, compute_property_signature

def compute_signature(normalized_text: str, function_name: Optional[str] = None) -> str:
    """
    Compute property-based signature over foundational code properties
    
    Args:
        normalized_text: Normalized Python code string
        function_name: Target function name for property extraction
    
    Returns:
        Hex-encoded SHA-256 hash of foundational properties (deterministic)
    
    Note:
        This function MUST be deterministic. Equal foundational properties
        always produce identical signatures.
    """
    # Extract foundational properties and compute property-based signature
    try:
        properties = extract_code_properties(normalized_text, function_name)
        return compute_property_signature(properties)
    except:
        # Fallback to text-based signature if property extraction fails
        text_bytes = normalized_text.encode('utf-8')
        hash_obj = hashlib.sha256(text_bytes)
        return hash_obj.hexdigest()

def compute_distance(output_text: str, canon_text: str, function_name: Optional[str] = None) -> float:
    """
    Compute property-based distance between code using foundational properties
    
    Args:
        output_text: Normalized output text
        canon_text: Canonical reference text
        function_name: Target function name for property extraction
    
    Returns:
        Distance d in [0,1] where d=0 iff foundational properties match
    
    Note:
        Uses property mismatch count normalized by total properties.
        This measures true semantic distance rather than text similarity.
    """
    # Handle edge cases
    if output_text == canon_text:
        return 0.0
    
    if not output_text and not canon_text:
        return 0.0
    
    if not output_text or not canon_text:
        return 1.0
    
    try:
        # Extract properties for both texts
        output_properties = extract_code_properties(output_text, function_name)
        canon_properties = extract_code_properties(canon_text, function_name)
        
        # Check property matches
        properties_equal, mismatches = properties_match(output_properties, canon_properties)
        
        if properties_equal:
            return 0.0
        
        # Compute distance based on property mismatches
        # Total of 13 foundational properties
        total_properties = 13
        mismatch_count = len(mismatches)
        
        # Normalize by total properties
        property_distance = mismatch_count / total_properties
        
        # Clamp to [0,1] range
        return min(1.0, max(0.0, property_distance))
    
    except:
        # Fallback to Levenshtein distance if property extraction fails
        edit_distance = _levenshtein_distance(output_text, canon_text)
        max_len = max(len(output_text), len(canon_text))
        normalized_distance = edit_distance / max_len
        return min(1.0, max(0.0, normalized_distance))

def record_pre_distance(run_id: str, sample_id: str, prompt_id: str, 
                       signature: str, d: float, compliant: bool) -> None:
    """
    Record pre-repair distance measurement
    
    Args:
        run_id: Unique run identifier
        sample_id: Sample identifier within run
        prompt_id: Prompt identifier
        signature: Code signature
        d: Distance to canon [0,1]
        compliant: Whether code passes oracle
    """
    record = DistanceRecord(
        run_id=run_id,
        sample_id=sample_id,
        prompt_id=prompt_id,
        stage="pre",
        signature=signature,
        d=d,
        compliant=compliant,
        oracle_version=ORACLE_VERSION,
        normalization_version=NORMALIZATION_VERSION,
        timestamp=datetime.now()
    )
    
    # Import here to avoid circular dependency
    from .logger import log_distance
    log_distance(record, DISTANCES_PRE_CSV_PATH)

def record_post_distance(run_id: str, sample_id: str, prompt_id: str,
                        signature: str, d: float, compliant: bool) -> None:
    """
    Record post-repair distance measurement
    
    Args:
        run_id: Unique run identifier
        sample_id: Sample identifier within run
        prompt_id: Prompt identifier
        signature: Code signature
        d: Distance to canon [0,1]
        compliant: Whether code passes oracle
    """
    record = DistanceRecord(
        run_id=run_id,
        sample_id=sample_id,
        prompt_id=prompt_id,
        stage="post",
        signature=signature,
        d=d,
        compliant=compliant,
        oracle_version=ORACLE_VERSION,
        normalization_version=NORMALIZATION_VERSION,
        timestamp=datetime.now()
    )
    
    # Import here to avoid circular dependency
    from .logger import log_distance
    log_distance(record, DISTANCES_POST_CSV_PATH)

def _levenshtein_distance(s1: str, s2: str) -> int:
    """
    Compute Levenshtein edit distance between two strings
    
    Args:
        s1: First string
        s2: Second string
    
    Returns:
        Minimum number of single-character edits (insertions, deletions, substitutions)
    
    Note:
        Uses dynamic programming algorithm with O(min(len(s1), len(s2))) space
    """
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = list(range(len(s2) + 1))
    
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        
        for j, c2 in enumerate(s2):
            # Cost of insertions, deletions, and substitutions
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            
            current_row.append(min(insertions, deletions, substitutions))
        
        previous_row = current_row
    
    return previous_row[-1]
