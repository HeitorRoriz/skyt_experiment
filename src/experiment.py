# src/experiment.py
"""
Experiment orchestrator for SKYT pipeline
Implements the new pipeline order: ICE → Contract → Transform → LLM → Parse → Canon → Compliance → Retry → Log
"""

import hashlib
from typing import Dict, Any, Optional
from .config import CANON_POLICY
from .intent_capture import extract_and_normalize_intents
from .contract import create_prompt_contract, load_contract_from_template
from .transform import build_llm_prompt_for_code, try_repair
from .llm import query_llm
from .normalize import extract_code, extract_reflection
from .canon import apply_canon
from .compliance import check_contract_compliance
from .log import write_execution_record

MAX_ATTEMPTS = 3


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
    
    # Step 6: Canon - Apply canonicalization
    canon_result = apply_canon(code, CANON_POLICY)
    
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
    
    # Step 9: Compute hashes
    raw_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()[:16]
    canon_signature = canon_result["signature"]
    
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
        "contract_id": contract["id"]
    }
    
    write_execution_record(execution_record)
    
    return execution_record
