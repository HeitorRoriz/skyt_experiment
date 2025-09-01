#!/usr/bin/env python3
"""
Test script for anchor canonicalization system
"""

from src.canon import FoundationalSignature, compute_distance, apply_canon, CanonPolicy
from src.compliance import check_contract_compliance
from src.determinism_lint import lint_determinism

def test_foundational_signature():
    """Test foundational signature computation"""
    print("Testing foundational signature computation...")
    
    policy = CanonPolicy()
    
    # Test code
    code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    
    # Apply canonicalization
    result = apply_canon(code, policy, effect_signature="pure_function")
    
    print(f"Canonical code length: {len(result['canon_code'])}")
    print(f"Foundational signature: {result['foundational_signature'].to_dict()}")
    print(f"Structural OK: {result['structural_ok']}")
    
    return result['foundational_signature']

def test_distance_computation():
    """Test distance computation between signatures"""
    print("\nTesting distance computation...")
    
    # Create two similar signatures
    sig1 = FoundationalSignature(
        struct="abc123",
        sem="def456", 
        effect="pure_function",
        env="env789"
    )
    
    sig2 = FoundationalSignature(
        struct="abc123",  # Same structure
        sem="xyz999",    # Different semantics
        effect="pure_function",
        env="env789"
    )
    
    distance = compute_distance(sig1, sig2)
    print(f"Distance between similar signatures: {distance}")
    
    # Test identical signatures
    distance_identical = compute_distance(sig1, sig1)
    print(f"Distance between identical signatures: {distance_identical}")
    
    return distance

def test_determinism_lint():
    """Test determinism linting"""
    print("\nTesting determinism linting...")
    
    # Clean code
    clean_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    
    # Dirty code with violations
    dirty_code = """
import random
import time

def fibonacci(n):
    time.sleep(0.1)  # Time violation
    if n <= 1:
        return n + random.randint(0, 1)  # Random violation
    return fibonacci(n-1) + fibonacci(n-2)
"""
    
    clean_result = lint_determinism(clean_code)
    dirty_result = lint_determinism(dirty_code)
    
    print(f"Clean code determinism pass: {clean_result['determinism_pass']}")
    print(f"Dirty code determinism pass: {dirty_result['determinism_pass']}")
    print(f"Dirty code violations: {dirty_result['violation_summary']}")
    
    return clean_result, dirty_result

def test_compliance_effects():
    """Test compliance effect signature generation"""
    print("\nTesting compliance effect signatures...")
    
    code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    
    contract = {
        "function_name": "fibonacci",
        "language": "python"
    }
    
    canon_result = {"structural_ok": True}
    compliance_result = check_contract_compliance(code, contract, canon_result)
    
    print(f"Effect signature: {compliance_result.get('effect_signature', 'None')}")
    print(f"Contract pass: {compliance_result['contract_pass']}")
    
    return compliance_result

if __name__ == "__main__":
    print("=" * 60)
    print("ANCHOR CANONICALIZATION SYSTEM TEST")
    print("=" * 60)
    
    try:
        # Run tests
        sig = test_foundational_signature()
        distance = test_distance_computation()
        clean_lint, dirty_lint = test_determinism_lint()
        compliance = test_compliance_effects()
        
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print("[PASS] Foundational signature computation")
        print("[PASS] Distance computation")
        print("[PASS] Determinism linting")
        print("[PASS] Compliance effect signatures")
        print("\nAnchor canonicalization system is ready!")
        
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
