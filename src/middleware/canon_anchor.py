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
import shutil
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any
from .schema import (
    Canon, CANON_JSON_FIELDS,
    NORMALIZATION_VERSION, ORACLE_VERSION,
    get_canon_paths, CANON_BASE_DIR, CANON_JSON_PATH, CANON_SIGNATURE_PATH
)
from .code_properties import extract_code_properties, compute_property_signature, CodeProperties

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
    paths = get_canon_paths(prompt_id)

    # Legacy support: if old global canon exists and per-prompt does not, migrate
    if not os.path.exists(paths["json"]) and os.path.exists(CANON_JSON_PATH):
        _migrate_legacy_canon(prompt_id, paths)

    # Check if canon already exists for this prompt
    if os.path.exists(paths["json"]):
        return get_canon(prompt_id)
    
    # Only fix canon if oracle passes
    if not oracle_pass:
        return None
    
    # Import here to avoid circular dependency
    from .distance import compute_signature
    
    # Extract foundational properties and compute property-based signature
    function_name = contract.get("enforce_function_name")
    canon_properties = extract_code_properties(output, function_name)
    canon_signature = compute_property_signature(canon_properties)
    
    # Extract function signatures and constraints from contract
    function_signatures = _extract_function_signatures(output)
    constraints_snapshot = json.dumps(contract, sort_keys=True)
    
    # Create canon object
    contract_id = contract.get("id", prompt_id)
    canon = Canon(
        contract_id=contract_id,
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
    
    # Persist canon atomically with properties
    _persist_canon(canon, output, canon_properties)

    return canon

def get_canon(prompt_id: str) -> Optional[Canon]:
    """
    Read-only accessor for current canon
    
    Returns:
        Canon object if exists, None otherwise
    """
    paths = get_canon_paths(prompt_id)

    # Legacy fallback: migrate global canon if present
    if not os.path.exists(paths["json"]) and os.path.exists(CANON_JSON_PATH):
        _migrate_legacy_canon(prompt_id, paths)

    if not os.path.exists(paths["json"]):
        return None
    
    try:
        with open(paths["json"], 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert timestamp string back to datetime
        data['fixed_at_timestamp'] = datetime.fromisoformat(data['fixed_at_timestamp'])
        
        return Canon(**data)
    
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise RuntimeError(f"Corrupted canon file: {e}")

def assert_canon_immutable(prompt_id: str, new_signature: str) -> None:
    """
    Assert that canon remains immutable
    
    Args:
        new_signature: New candidate signature
    
    Raises:
        CanonImmutabilityError: If canon exists and differs from candidate
    """
    canon = get_canon(prompt_id)
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

def _persist_canon(canon: Canon, normalized_code: str, properties: Optional[CodeProperties] = None) -> None:
    """
    Atomically persist canon to disk
    
    Args:
        canon: Canon object to persist
        normalized_code: Normalized code content
    """
    paths = get_canon_paths(canon.prompt_id)

    # Ensure output directory exists
    os.makedirs(paths["dir"], exist_ok=True)
    
    # Convert canon to dict for JSON serialization
    canon_dict = {
        field: getattr(canon, field) for field in CANON_JSON_FIELDS
    }
    # Convert datetime to ISO string
    canon_dict['fixed_at_timestamp'] = canon.fixed_at_timestamp.isoformat()
    
    # Write canon.json atomically
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                     dir=paths["dir"],
                                     delete=False) as tmp_json:
        json.dump(canon_dict, tmp_json, indent=2, sort_keys=True)
        tmp_json_path = tmp_json.name

    # Write canon_signature.txt atomically
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                     dir=paths["dir"],
                                     delete=False) as tmp_sig:
        tmp_sig.write(canon.canon_signature)
        tmp_sig_path = tmp_sig.name

    # Write canonical code to canon_code.txt
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                     dir=paths["dir"],
                                     delete=False) as tmp_code:
        tmp_code.write(normalized_code)
        tmp_code_path = tmp_code.name

    # Write canonical properties to canon_properties.json
    tmp_props_path = None
    if properties:
        import json
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                         dir=paths["dir"],
                                         delete=False) as tmp_props:
            props_dict = {
                'control_flow_signature': properties.control_flow_signature,
                'data_dependency_graph': properties.data_dependency_graph,
                'execution_paths': properties.execution_paths,
                'function_contracts': properties.function_contracts,
                'complexity_class': properties.complexity_class,
                'side_effect_profile': properties.side_effect_profile,
                'termination_properties': properties.termination_properties,
                'algebraic_structure': properties.algebraic_structure,
                'numerical_behavior': properties.numerical_behavior,
                'logical_equivalence': properties.logical_equivalence,
                'normalized_ast_structure': properties.normalized_ast_structure,
                'operator_precedence': properties.operator_precedence,
                'statement_ordering': properties.statement_ordering
            }
            json.dump(props_dict, tmp_props, indent=2, sort_keys=True)
            tmp_props_path = tmp_props.name

    # Atomic rename operations
    os.replace(tmp_json_path, paths["json"])
    os.replace(tmp_sig_path, paths["signature"])
    os.replace(tmp_code_path, paths["code"])
    if tmp_props_path:
        props_path = os.path.join(paths["dir"], "canon_properties.json")
        os.replace(tmp_props_path, props_path)

def get_canon_properties(prompt_id: str) -> Optional[CodeProperties]:
    """
    Get canonical properties for a prompt
    
    Args:
        prompt_id: Prompt identifier
    
    Returns:
        CodeProperties object if exists, None otherwise
    """
    paths = get_canon_paths(prompt_id)
    props_path = os.path.join(paths["dir"], "canon_properties.json")
    
    if not os.path.exists(props_path):
        return None
    
    try:
        with open(props_path, 'r', encoding='utf-8') as f:
            props_dict = json.load(f)
        
        return CodeProperties(
            control_flow_signature=props_dict['control_flow_signature'],
            data_dependency_graph=props_dict['data_dependency_graph'],
            execution_paths=props_dict['execution_paths'],
            function_contracts=props_dict['function_contracts'],
            complexity_class=props_dict['complexity_class'],
            side_effect_profile=props_dict['side_effect_profile'],
            termination_properties=props_dict['termination_properties'],
            algebraic_structure=props_dict['algebraic_structure'],
            numerical_behavior=props_dict['numerical_behavior'],
            logical_equivalence=props_dict['logical_equivalence'],
            normalized_ast_structure=props_dict['normalized_ast_structure'],
            operator_precedence=props_dict['operator_precedence'],
            statement_ordering=props_dict['statement_ordering']
        )
    
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Warning: Corrupted canon properties file: {e}")
        return None

def reset_canon(prompt_id: Optional[str] = None) -> None:
    """
    Reset canon data (for testing only)
    
    Args:
        prompt_id: Specific prompt to reset. If None, clears all canons.
    """
    if prompt_id is not None:
        paths = get_canon_paths(prompt_id)
        if os.path.isdir(paths["dir"]):
            shutil.rmtree(paths["dir"])
        return

    if os.path.isdir(CANON_BASE_DIR):
        shutil.rmtree(CANON_BASE_DIR)


def _migrate_legacy_canon(prompt_id: str, paths: Dict[str, str]) -> None:
    """Move legacy single-canon files into per-prompt directory."""
    os.makedirs(paths["dir"], exist_ok=True)

    if os.path.exists(CANON_JSON_PATH):
        shutil.move(CANON_JSON_PATH, paths["json"])

    if os.path.exists(CANON_SIGNATURE_PATH):
        shutil.move(CANON_SIGNATURE_PATH, paths["signature"])

    legacy_code_path = os.path.join(CANON_BASE_DIR, "canon_code.txt")
    if os.path.exists(legacy_code_path):
        shutil.move(legacy_code_path, paths["code"])
