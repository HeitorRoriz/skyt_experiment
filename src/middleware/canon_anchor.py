# src/middleware/canon_anchor.py
"""
[TODO canon_anchor.py]
Goal: lifecycle for a single immutable canon. No code.

1. Spec fix_canon_if_none(output, contract, oracle):
   - If oracle passes and no canon exists, compute normalized signature and persist canon.json and canon_signature.txt.
   - Return canon object or None if not fixed.
2. Spec get_canon():
   - Read-only accessor that loads current canon.json and returns an object view.
3. Spec assert_canon_immutable(new_candidate):
   - If a canon exists and candidate differs, raise and abort run (log invariant breach).
4. Persistence:
   - Write to outputs/canon/canon.json and outputs/canon/canon_signature.txt atomically.
   - Record normalization_version and oracle_version.
5. Acceptance: once fixed, all future attempts to replace the canon must fail.
"""

import json
import os
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any
from .schema import (
    Canon, CANON_JSON_PATH, CANON_SIGNATURE_PATH, CANON_JSON_FIELDS,
    NORMALIZATION_VERSION, ORACLE_VERSION
)

class CanonImmutabilityError(Exception):
    """Raised when attempting to modify an existing canon"""
    pass

def fix_canon_if_none(output: str, contract: Dict[str, Any], oracle_pass: bool, 
                      prompt_id: str, model: str, temperature: float) -> Optional[Canon]:
    """
    Fix canon if none exists and oracle passes
    
    Args:
        output: Normalized code output
        contract: Contract specification
        oracle_pass: Whether oracle validation passed
        prompt_id: Prompt identifier
        model: Model used
        temperature: Temperature used
    
    Returns:
        Canon object if fixed, None otherwise
    
    Raises:
        CanonImmutabilityError: If canon already exists
    """
    # Check if canon already exists
    if os.path.exists(CANON_JSON_PATH):
        return None
    
    # Only fix canon if oracle passes
    if not oracle_pass:
        return None
    
    # Import here to avoid circular dependency
    from .distance import compute_signature
    
    # Compute canonical signature
    canon_signature = compute_signature(output)
    
    # Extract function signatures and constraints from contract
    function_signatures = _extract_function_signatures(output)
    constraints_snapshot = json.dumps(contract, sort_keys=True)
    
    # Create canon object
    canon = Canon(
        contract_id=contract.get("id", prompt_id),
        canon_signature=canon_signature,
        oracle_version=ORACLE_VERSION,
        normalization_version=NORMALIZATION_VERSION,
        fixed_at_timestamp=datetime.now(),
        prompt_id=prompt_id,
        model=model,
        temperature=temperature,
        function_signatures=function_signatures,
        constraints_snapshot=constraints_snapshot
    )
    
    # Persist canon atomically
    _persist_canon(canon, output)
    
    return canon

def get_canon() -> Optional[Canon]:
    """
    Read-only accessor for current canon
    
    Returns:
        Canon object if exists, None otherwise
    """
    if not os.path.exists(CANON_JSON_PATH):
        return None
    
    try:
        with open(CANON_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert timestamp string back to datetime
        data['fixed_at_timestamp'] = datetime.fromisoformat(data['fixed_at_timestamp'])
        
        return Canon(**data)
    
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise RuntimeError(f"Corrupted canon file: {e}")

def assert_canon_immutable(new_signature: str) -> None:
    """
    Assert that canon remains immutable
    
    Args:
        new_signature: New candidate signature
    
    Raises:
        CanonImmutabilityError: If canon exists and differs from candidate
    """
    canon = get_canon()
    if canon is None:
        return  # No canon exists, nothing to check
    
    if canon.canon_signature != new_signature:
        raise CanonImmutabilityError(
            f"Canon immutability violated: existing={canon.canon_signature[:16]}..., "
            f"candidate={new_signature[:16]}..."
        )

def _extract_function_signatures(code: str) -> str:
    """
    Extract function signatures from code for canon metadata
    
    Args:
        code: Python code string
    
    Returns:
        JSON string of function signatures
    """
    import ast
    
    try:
        tree = ast.parse(code)
        signatures = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Extract function name and arguments
                args = [arg.arg for arg in node.args.args]
                sig = f"{node.name}({', '.join(args)})"
                signatures.append(sig)
        
        return json.dumps(signatures, sort_keys=True)
    
    except SyntaxError:
        return "[]"  # Invalid code, no signatures

def _persist_canon(canon: Canon, normalized_code: str) -> None:
    """
    Atomically persist canon to disk
    
    Args:
        canon: Canon object to persist
        normalized_code: Normalized code content
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(CANON_JSON_PATH), exist_ok=True)
    
    # Convert canon to dict for JSON serialization
    canon_dict = {
        field: getattr(canon, field) for field in CANON_JSON_FIELDS
    }
    # Convert datetime to ISO string
    canon_dict['fixed_at_timestamp'] = canon.fixed_at_timestamp.isoformat()
    
    # Write canon.json atomically
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', 
                                     dir=os.path.dirname(CANON_JSON_PATH),
                                     delete=False) as tmp_json:
        json.dump(canon_dict, tmp_json, indent=2, sort_keys=True)
        tmp_json_path = tmp_json.name
    
    # Write canon_signature.txt atomically
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                     dir=os.path.dirname(CANON_SIGNATURE_PATH),
                                     delete=False) as tmp_sig:
        tmp_sig.write(canon.canon_signature)
        tmp_sig_path = tmp_sig.name
    
    # Write canonical code to canon_code.txt
    canon_code_path = "outputs/canon/canon_code.txt"
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                     dir=os.path.dirname(canon_code_path),
                                     delete=False) as tmp_code:
        tmp_code.write(normalized_code)
        tmp_code_path = tmp_code.name
    
    # Atomic rename operations
    os.replace(tmp_json_path, CANON_JSON_PATH)
    os.replace(tmp_sig_path, CANON_SIGNATURE_PATH)
    os.replace(tmp_code_path, canon_code_path)

def reset_canon() -> None:
    """
    Reset canon (for testing only)
    
    Removes canon files to allow fresh canon establishment
    """
    for path in [CANON_JSON_PATH, CANON_SIGNATURE_PATH]:
        if os.path.exists(path):
            os.remove(path)
