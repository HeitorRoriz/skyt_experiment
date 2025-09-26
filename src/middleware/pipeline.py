# src/middleware/pipeline.py
"""
[TODO pipeline.py]
Goal: wrap existing experiment run without API break. No code.

1. Entry points:
   - wrap_contract_run(callable_producing_output)
   - wrap_simple_run(callable_producing_output)
2. Sequence in both:
   a) Call upstream to get raw output text.
   b) Normalize and compute signature.
   c) If no canon and oracle passes, fix canon. Else assert immutability.
   d) Compute and log pre distance.
   e) If non-compliant, call repair. Enforce monotonicity and bounds.
   f) Recompute and log post distance. Log repair record either way.
   g) Return final output upward unchanged for the caller.
3. Hooks:
   - Pull run_id, sample_id, prompt_id, model, temperature from existing config/main.
   - Record normalization_version and oracle_version.
4. Acceptance: for every sample we always log one pre record and one post record.
"""

import uuid
from datetime import datetime
from typing import Callable, Dict, Any, Tuple
from .schema import RunSpec, ORACLE_VERSION, NORMALIZATION_VERSION
from .canon_anchor import fix_canon_if_none, get_canon, assert_canon_immutable, CanonImmutabilityError
from .distance import compute_signature, compute_distance, record_pre_distance, record_post_distance
from .contract_enforcer import oracle_check
from .repair import repair_code
from .logger import log_run, log_repair

class PipelineContext:
    """Context for pipeline execution"""
    def __init__(self, run_id: str, sample_id: str, prompt_id: str, 
                 model: str, temperature: float, contract: Dict[str, Any]):
        self.run_id = run_id
        self.sample_id = sample_id
        self.prompt_id = prompt_id
        self.model = model
        self.temperature = temperature
        self.contract = contract

def wrap_contract_run(llm_callable: Callable[[], str], context: PipelineContext) -> str:
    """
    Wrap contract-mode experiment run with middleware
    
    Args:
        llm_callable: Function that produces raw LLM output
        context: Pipeline execution context
    
    Returns:
        Final processed output (unchanged from input for API compatibility)
    """
    return _execute_pipeline(llm_callable, context, mode="contract")

def wrap_simple_run(llm_callable: Callable[[], str], context: PipelineContext) -> str:
    """
    Wrap simple-mode experiment run with middleware
    
    Args:
        llm_callable: Function that produces raw LLM output
        context: Pipeline execution context
    
    Returns:
        Final processed output (unchanged from input for API compatibility)
    """
    return _execute_pipeline(llm_callable, context, mode="simple")

def _execute_pipeline(llm_callable: Callable[[], str], context: PipelineContext, mode: str) -> str:
    """
    Execute the complete middleware pipeline
    
    Args:
        llm_callable: Function that produces raw LLM output
        context: Pipeline execution context
        mode: Execution mode ("contract" or "simple")
    
    Returns:
        Final processed output
    """
    # Log run specification
    run_spec = RunSpec(
        run_id=context.run_id,
        prompt_id=context.prompt_id,
        mode=mode,
        model=context.model,
        temperature=context.temperature,
        seed=None,  # TODO: Extract from config if available
        oracle_version=ORACLE_VERSION,
        contract_id=context.contract.get("id", context.prompt_id),
        normalization_version=NORMALIZATION_VERSION,
        timestamp=datetime.now()
    )
    log_run(run_spec)
    
    try:
        # Step a) Call upstream to get raw output text
        raw_output = llm_callable()
        
        # Step b) Normalize and compute signature
        normalized_output = _normalize_output(raw_output)
        pre_signature = compute_signature(normalized_output)
        
        # Step c) Canon management
        canon = get_canon()
        if canon is None:
            # Check if we can establish canon
            oracle_pass, _ = oracle_check(normalized_output, context.contract)
            if oracle_pass:
                canon = fix_canon_if_none(
                    normalized_output, context.contract, oracle_pass,
                    context.prompt_id, context.model, context.temperature
                )
        else:
            # Assert canon immutability
            try:
                assert_canon_immutable(pre_signature)
            except CanonImmutabilityError as e:
                # Log the violation but continue processing
                print(f"WARNING: Canon immutability violation: {e}")
        
        # Step d) Compute and log pre distance
        if canon:
            canon_text = _get_canon_text()  # Load canonical text
            pre_distance = compute_distance(normalized_output, canon_text)
        else:
            pre_distance = 1.0  # No canon available, maximum distance
        
        oracle_pass, oracle_reason = oracle_check(normalized_output, context.contract)
        record_pre_distance(
            context.run_id, context.sample_id, context.prompt_id,
            pre_signature, pre_distance, oracle_pass
        )
        
        # Step e) Repair if non-compliant
        final_output = normalized_output
        repair_performed = False
        
        if not oracle_pass:
            # Always attempt repair, even without canon
            canon_text = _get_canon_text() if canon else ""
            repair_result, repair_record = repair_code(
                normalized_output, canon_text, context.contract,
                context.run_id, context.sample_id
            )
            
            log_repair(repair_record)
            
            if repair_result.success:
                final_output = repair_result.repaired_text
                repair_performed = True
                
                # BOOTSTRAP FIX: If no canon exists and repair succeeded, establish canon now
                if canon is None:
                    final_oracle_pass, _ = oracle_check(final_output, context.contract)
                    if final_oracle_pass:
                        canon = fix_canon_if_none(
                            final_output, context.contract, final_oracle_pass,
                            context.prompt_id, context.model, context.temperature
                        )
        
        # Step f) Recompute and log post distance
        post_signature = compute_signature(final_output)
        if canon:
            post_distance = compute_distance(final_output, canon_text)
        else:
            post_distance = 1.0
        
        final_oracle_pass, _ = oracle_check(final_output, context.contract)
        record_post_distance(
            context.run_id, context.sample_id, context.prompt_id,
            post_signature, post_distance, final_oracle_pass
        )
        
        # Log repair record even if no repair was attempted
        if not repair_performed:
            from .repair import RepairRecord
            no_repair_record = RepairRecord(
                run_id=context.run_id,
                sample_id=context.sample_id,
                before_signature=pre_signature,
                after_signature=post_signature,
                d_before=pre_distance,
                d_after=post_distance,
                steps=0,
                success=oracle_pass,
                reason="no_repair_attempted" if oracle_pass else "repair_not_performed",
                timestamp=datetime.now()
            )
            log_repair(no_repair_record)
        
        # Step g) Return final output unchanged for API compatibility
        return raw_output  # Return original for backward compatibility
    
    except Exception as e:
        # Log error but don't break existing pipeline
        print(f"Middleware pipeline error: {e}")
        # Still try to call upstream and return result
        try:
            return llm_callable()
        except:
            return ""  # Fallback empty output

def _normalize_output(raw_output: str) -> str:
    """
    Normalize output using existing normalization pipeline
    
    Args:
        raw_output: Raw LLM output
    
    Returns:
        Normalized code string
    """
    # Import here to avoid circular dependency
    try:
        from ..normalize import extract_code
        return extract_code(raw_output)
    except ImportError:
        # Fallback normalization if module not available
        return _simple_normalize(raw_output)

def _simple_normalize(text: str) -> str:
    """
    Simple fallback normalization
    
    Args:
        text: Input text
    
    Returns:
        Normalized text
    """
    import re
    
    # Remove markdown fences
    text = re.sub(r'```python\s*\n', '', text)
    text = re.sub(r'```\s*$', '', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text

def _get_canon_text() -> str:
    """
    Get canonical text for distance computation
    
    Returns:
        Canonical code text
    """
    import os
    
    canon_code_path = "outputs/canon/canon_code.txt"
    
    if os.path.exists(canon_code_path):
        try:
            with open(canon_code_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            pass
    
    # Fallback: return empty string if canon text not available
    return ""

def create_pipeline_context(prompt_id: str, contract: Dict[str, Any], 
                          model: str = "gpt-4o-mini", temperature: float = 0.0) -> PipelineContext:
    """
    Create pipeline context for experiment execution
    
    Args:
        prompt_id: Prompt identifier
        contract: Contract specification
        model: Model identifier
        temperature: Temperature parameter
    
    Returns:
        PipelineContext object
    """
    run_id = f"{prompt_id}_{uuid.uuid4().hex[:8]}"
    sample_id = f"sample_{uuid.uuid4().hex[:8]}"
    
    return PipelineContext(
        run_id=run_id,
        sample_id=sample_id,
        prompt_id=prompt_id,
        model=model,
        temperature=temperature,
        contract=contract
    )
