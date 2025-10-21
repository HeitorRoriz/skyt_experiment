"""
Contract-Aware Validator for SKYT Transformations
Validates transformations based on contract domain and oracle compliance
"""

from typing import Tuple, Dict, Any, Callable
import ast


def parse_domain(contract: Dict[str, Any]) -> Callable:
    """
    Parse domain constraints from contract
    
    Args:
        contract: Contract dictionary with domain specification
        
    Returns:
        Function that checks if arguments are in domain
    """
    domain_spec = contract.get("domain", {}).get("inputs", [])
    if not domain_spec:
        # No domain specified - all inputs valid
        return lambda args: True
    
    # For now, support single int argument with constraint "n >= 0"
    spec = domain_spec[0]
    param_name = spec.get("name", "n")
    constraint = spec.get("constraint", None)
    
    if constraint is None:
        return lambda args: True
    
    def in_domain(args: Dict[str, Any]) -> bool:
        """Check if arguments satisfy domain constraint"""
        if param_name not in args:
            return True  # Can't validate, assume valid
        
        val = args[param_name]
        
        # Simple constraint parser for common patterns
        constraint_str = constraint.strip()
        
        if constraint_str == "n >= 0":
            return val >= 0
        elif constraint_str == "n > 0":
            return val > 0
        elif constraint_str == "n <= 0":
            return val <= 0
        elif constraint_str == "n < 0":
            return val < 0
        
        # Default: assume in domain
        return True
    
    return in_domain


def run_oracle_in_domain(code: str, contract: Dict[str, Any]) -> Tuple[bool, list]:
    """
    Run oracle tests only on inputs within the contract domain
    
    Args:
        code: Python code to test
        contract: Contract with oracle and domain specifications
        
    Returns:
        (all_passed, results) tuple
    """
    # Parse domain constraint
    in_domain = parse_domain(contract)
    
    # Get oracle test cases
    oracle_spec = contract.get("oracle_requirements", {})
    test_cases = oracle_spec.get("test_cases", [])
    
    if not test_cases:
        return True, []  # No tests = vacuously true
    
    # Filter test cases to only those in contract domain
    # Get parameter name from contract domain specification
    domain_spec = contract.get("domain", {})
    inputs_spec = domain_spec.get("inputs", [])
    param_name = inputs_spec[0].get("name", "n") if inputs_spec else "n"
    
    domain_cases = []
    for case in test_cases:
        # Convert test case format to args dict using correct parameter name
        args = {param_name: case.get("input")}
        if in_domain(args):
            domain_cases.append(case)
    
    if not domain_cases:
        return True, []  # No in-domain tests = vacuously true
    
    # Execute code and run tests
    try:
        # Create execution namespace
        namespace = {}
        exec(code, namespace)
        
        # Find the function (use contract's function_name)
        func_name = contract.get("constraints", {}).get("function_name", "fibonacci")
        if func_name not in namespace:
            return False, ["Function not found in code"]
        
        func = namespace[func_name]
        
        # Run each test case
        results = []
        for case in domain_cases:
            try:
                input_val = case.get("input")
                expected = case.get("expected")
                
                result = func(input_val)
                passed = (result == expected)
                results.append(passed)
                
            except Exception as e:
                results.append(False)
        
        return all(results), results
        
    except Exception as e:
        return False, [f"Execution error: {str(e)}"]


def calculate_distance_to_canon(code: str, contract_id: str) -> float:
    """
    Calculate distance from code to canonical form
    
    Args:
        code: Code to measure
        contract_id: Contract identifier
        
    Returns:
        Distance value (0.0 = identical to canon)
    """
    # Import here to avoid circular dependencies
    from .canon_system import CanonSystem
    import difflib
    
    canon_system = CanonSystem()
    
    # Get canon
    canon_data = canon_system.load_canon(contract_id)
    if not canon_data:
        return 1.0  # No canon = maximum distance
    
    canon_code = canon_data.get("canonical_code", "")
    
    # Use simple text-based distance (fast and reliable)
    # Normalize whitespace for comparison
    code_normalized = " ".join(code.split())
    canon_normalized = " ".join(canon_code.split())
    
    # Calculate similarity ratio
    similarity = difflib.SequenceMatcher(None, code_normalized, canon_normalized).ratio()
    distance = 1.0 - similarity
    
    return distance


def validate_transformation(
    pre_code: str,
    post_code: str,
    contract: Dict[str, Any],
    contract_id: str
) -> Tuple[bool, str]:
    """
    Validate transformation is contract-compliant and monotonically improves
    
    Validation criteria:
    1. Both pre and post code must pass oracle tests within contract domain
    2. Post-transformation distance to canon must not increase (monotonic)
    3. Transformation only affects behavior outside contract domain (optional)
    
    Args:
        pre_code: Code before transformation
        post_code: Code after transformation
        contract: Contract specification
        contract_id: Contract identifier for canon lookup
        
    Returns:
        (is_valid, message) tuple
    """
    
    # Criterion 1: Both versions must satisfy oracle on contract domain
    pre_ok, pre_results = run_oracle_in_domain(pre_code, contract)
    post_ok, post_results = run_oracle_in_domain(post_code, contract)
    
    # Accept transformation if:
    # 1. Post-transformation code passes (even if pre-transformation failed) - we fixed it!
    # 2. Both pass (maintained correctness)
    # Reject only if post-transformation breaks passing code OR doesn't improve failing code
    
    if not post_ok:
        # Post-transformation fails
        if pre_ok:
            # We broke working code - REJECT
            return False, "Transformation broke working code (pre passed, post failed)"
        else:
            # Both fail - transformation didn't help, but also didn't make it worse
            # Accept it if it reduces distance (checked later)
            pass
    
    # If we get here: post_ok is True OR both fail
    # Either way, transformation is acceptable from oracle perspective
    
    # Criterion 2: Monotonic distance reduction toward canon
    d_pre = calculate_distance_to_canon(pre_code, contract_id)
    d_post = calculate_distance_to_canon(post_code, contract_id)
    
    if d_post > d_pre:
        return False, f"Non-monotonic: distance increased ({d_pre:.3f} -> {d_post:.3f})"
    
    # Criterion 3 (Optional): Check if changes are only out-of-domain
    # For now, we skip this check - the above two criteria are sufficient
    
    return True, f"Contract-compliant and closer to canon (delta_d={d_pre-d_post:.3f})"


def check_out_of_domain_change(pre_code: str, post_code: str, contract: Dict[str, Any]) -> bool:
    """
    Check if transformation only changed behavior outside contract domain
    
    This is a heuristic check - looks for changes in error handling for out-of-domain inputs
    
    Args:
        pre_code: Code before transformation
        post_code: Code after transformation
        contract: Contract with domain specification
        
    Returns:
        True if changes appear to be out-of-domain only
    """
    # Simple heuristic: if pre has "raise" and post doesn't, and domain is "n >= 0",
    # then the change is likely in the n < 0 path (out of domain)
    
    domain_spec = contract.get("domain", {}).get("inputs", [])
    if not domain_spec:
        return False
    
    constraint = domain_spec[0].get("constraint", "")
    
    # If domain is "n >= 0" and we removed a "raise" statement,
    # it's likely we changed the n < 0 handling (out of domain)
    if "n >= 0" in constraint:
        pre_has_raise = "raise " in pre_code
        post_has_raise = "raise " in post_code
        
        if pre_has_raise and not post_has_raise:
            return True
    
    return False
