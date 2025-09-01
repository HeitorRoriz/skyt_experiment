# src/experiment.py
"""
Experiment orchestrator for SKYT pipeline
Implements the new pipeline order: ICE → Contract → Transform → LLM → Parse → Canon → Compliance → Retry → Log
"""

import hashlib
import json
import os
from typing import Dict, Any, Optional
from .config import CANON_POLICY, ANCHOR_MODE, DISTANCE_WEIGHTS
from .canon import FoundationalSignature, compute_distance
from .intent_capture import extract_and_normalize_intents
from .contract import create_prompt_contract, load_contract_from_template
from .transform import build_llm_prompt_for_code, try_repair
from .llm import query_llm
from .normalize import extract_code, extract_reflection
from .canon import apply_canon
from .compliance import check_contract_compliance
from .determinism_lint import lint_determinism
from .log import write_execution_record

MAX_ATTEMPTS = 3

# Global experiment state for anchor canonicalization
_experiment_anchors = {}  # {prompt_id: FoundationalSignature}


def run_experiment(prompt_id: str, prompt: str, model: str, temperature: float, 
                  contract_template_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run single experiment with new pipeline order
    
    Args:
        prompt_id: Unique prompt identifier
        prompt: Raw prompt text
        model: LLM model identifier
        temperature: Temperature parameter
        contract_template_path: Path to contract templates (optional)
    
    Returns:
        Experiment result dict
    """
    # Step 1: ICE - Intent Capture & Enhancement
    dev_intent, user_intent = extract_and_normalize_intents(prompt)
    
    # Step 2: Contract - Load or create contract specification
    if contract_template_path:
        try:
            contract = load_contract_from_template(contract_template_path, prompt_id)
        except:
            contract = create_prompt_contract(prompt_id, prompt)
    else:
        contract = create_prompt_contract(prompt_id, prompt)
    
    # Step 3: Transform - Build LLM prompt
    messages = build_llm_prompt_for_code(contract, dev_intent, user_intent)
    
    # Step 4: LLM - Generate code
    raw_output = query_llm(messages, model, temperature)
    
    # Step 5: Parse - Extract code from response
    code = extract_code(raw_output)
    reflection = extract_reflection(raw_output) if hasattr(extract_reflection, '__call__') else None
    
    # Step 5.5: Determinism Lint - Fast-fail on determinism violations
    determinism_result = lint_determinism(code, strict_mode=True)
    if not determinism_result["determinism_pass"]:
        # Early exit for determinism violations
        return {
            "prompt_id": prompt_id,
            "model": model,
            "temperature": temperature,
            "raw_output": raw_output,
            "code": code,
            "canon_code": "",
            "raw_hash": hashlib.sha256(code.encode('utf-8')).hexdigest()[:16],
            "canon_signature": "",
            "structural_ok": False,
            "canonicalization_ok": False,
            "contract_pass": False,
            "oracle_pass": False,
            "notes": f"determinism_violation: {determinism_result['violation_summary']}",
            "attempts": 1,
            "contract_id": contract["id"],
            "anchor_hit": False,
            "distance": 1.0,  # Max distance for failed runs
            "foundational_signature": None
        }
    
    # Step 6: Canon - Apply canonicalization with foundational signature
    # First get effect signature from compliance check (preview)
    temp_compliance = check_contract_compliance(code, contract, {"structural_ok": True})
    effect_signature = temp_compliance.get("effect_signature", "no_effects")
    
    canon_result = apply_canon(code, CANON_POLICY, 
                              oracle_outputs=None,  # TODO: Add oracle outputs
                              effect_signature=effect_signature)
    
    # Step 7: Compliance - Check contract compliance
    compliance_result = check_contract_compliance(code, contract, canon_result)
    
    # Step 8: Retry - Attempt repair if needed
    attempts = 1
    while not compliance_result["contract_pass"] and attempts < MAX_ATTEMPTS:
        repaired_code = try_repair(code, contract)
        if repaired_code:
            code = repaired_code
            canon_result = apply_canon(code, CANON_POLICY)
            compliance_result = check_contract_compliance(code, contract, canon_result)
        attempts += 1
    
    # Step 9: Compute hashes and anchor distance
    raw_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()[:16]
    canon_signature = canon_result["signature"]
    foundational_sig = canon_result["foundational_signature"]
    
    # Anchor canonicalization logic
    anchor_hit = False
    distance = 0.0
    
    if ANCHOR_MODE and compliance_result["contract_pass"]:
        if prompt_id not in _experiment_anchors:
            # First successful run - establish anchor
            _experiment_anchors[prompt_id] = foundational_sig
            _save_anchor_signature(prompt_id, foundational_sig)
            anchor_hit = True
            distance = 0.0
        else:
            # Subsequent runs - compute distance to anchor
            anchor_sig = _experiment_anchors[prompt_id]
            distance = compute_distance(foundational_sig, anchor_sig, DISTANCE_WEIGHTS)
            anchor_hit = (distance == 0.0)
    
    # Step 10: Log - Write execution record
    execution_record = {
        "prompt_id": prompt_id,
        "model": model,
        "temperature": temperature,
        "raw_output": raw_output,
        "code": code,
        "canon_code": canon_result["canon_code"],
        "raw_hash": raw_hash,
        "canon_signature": canon_signature,
        "structural_ok": canon_result["structural_ok"],
        "canonicalization_ok": compliance_result["canonicalization_ok"],
        "contract_pass": compliance_result["contract_pass"],
        "oracle_pass": compliance_result["oracle_pass"],
        "notes": canon_result["notes"],
        "attempts": attempts,
        "contract_id": contract["id"],
        "anchor_hit": anchor_hit,
        "distance": distance,
        "foundational_signature": foundational_sig.to_dict() if foundational_sig else None
    }
    
    write_execution_record(execution_record)
    
    return execution_record


def _extract_effect_signature(compliance_result: Dict[str, Any]) -> str:
    """Extract stable effect signature from compliance result"""
    # For now, use a simple signature based on compliance status
    # TODO: Enhance with actual side-effect detection
    effects = []
    if compliance_result.get("canonicalization_ok"):
        effects.append("canon_ok")
    if compliance_result.get("structural_ok"):
        effects.append("struct_ok")
    if compliance_result.get("oracle_pass"):
        effects.append("oracle_ok")
    
    return "|".join(sorted(effects)) if effects else "no_effects"


def _save_anchor_signature(prompt_id: str, signature: FoundationalSignature):
    """Save anchor signature to persistent storage"""
    anchor_dir = "outputs/anchors"
    os.makedirs(anchor_dir, exist_ok=True)
    
    anchor_file = os.path.join(anchor_dir, f"{prompt_id}_anchor.json")
    with open(anchor_file, 'w') as f:
        json.dump(signature.to_dict(), f, indent=2)


def load_anchor_signatures():
    """Load existing anchor signatures from storage"""
    global _experiment_anchors
    anchor_dir = "outputs/anchors"
    
    if not os.path.exists(anchor_dir):
        return
    
    for filename in os.listdir(anchor_dir):
        if filename.endswith("_anchor.json"):
            prompt_id = filename.replace("_anchor.json", "")
            anchor_file = os.path.join(anchor_dir, filename)
            
            try:
                with open(anchor_file, 'r') as f:
                    anchor_data = json.load(f)
                _experiment_anchors[prompt_id] = FoundationalSignature.from_dict(anchor_data)
            except (json.JSONDecodeError, KeyError):
                # Skip corrupted anchor files
                continue


def reset_anchors():
    """Reset all anchor signatures (for testing)"""
    global _experiment_anchors
    _experiment_anchors = {}
    
    anchor_dir = "outputs/anchors"
    if os.path.exists(anchor_dir):
        import shutil
        shutil.rmtree(anchor_dir)
