#!/usr/bin/env python3
"""
Smoke test for refactored SKYT pipeline
Tests core functionality without requiring API calls
"""

import sys
import os
sys.path.insert(0, 'src')

def test_canon_module():
    """Test canonicalization module"""
    print("Testing canon.py...")
    from src.canon import apply_canon, CanonPolicy
    
    test_code = '''
def fibonacci(n):
    """Calculate fibonacci number"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)  # Recursive approach
    '''
    
    policy = CanonPolicy()
    result = apply_canon(test_code, policy)
    
    assert result["structural_ok"] == True
    assert len(result["canon_code"]) > 0
    assert len(result["signature"]) == 16
    print("OK Canon module working")

def test_compliance_module():
    """Test compliance module"""
    print("Testing compliance.py...")
    from src.compliance import check_contract_compliance
    from src.canon import apply_canon, CanonPolicy
    
    code = "def fibonacci(n):\n    return n"
    contract = {"function_name": "fibonacci", "language": "python"}
    canon_result = apply_canon(code, CanonPolicy())
    
    result = check_contract_compliance(code, contract, canon_result)
    
    assert "canonicalization_ok" in result
    assert "structural_ok" in result
    assert "contract_pass" in result
    print("OK Compliance module working")

def test_transform_module():
    """Test transform module"""
    print("Testing transform.py...")
    from src.transform import build_llm_prompt_for_code, compose_system_message
    
    contract = {"prompt": "Generate fibonacci", "function_name": "fibonacci"}
    messages = build_llm_prompt_for_code(contract)
    
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    print("OK Transform module working")

def test_intent_capture_module():
    """Test intent capture module"""
    print("Testing intent_capture.py...")
    from src.intent_capture import extract_and_normalize_intents, resolve_conflicts
    
    prompt = "Implement fibonacci using recursive approach that should return correct values"
    dev_intent, user_intent = extract_and_normalize_intents(prompt)
    
    resolution = resolve_conflicts(dev_intent, user_intent)
    assert "conflicts" in resolution
    print("OK Intent capture module working")

def test_contract_module():
    """Test contract module"""
    print("Testing contract.py...")
    from src.contract import create_prompt_contract, validate_contract
    
    contract = create_prompt_contract("test", "Generate fibonacci", "fibonacci")
    
    assert contract["id"] == "test"
    assert contract["function_name"] == "fibonacci"
    assert validate_contract(contract) == True
    print("OK Contract module working")

def test_normalize_module():
    """Test normalize module"""
    print("Testing normalize.py...")
    from src.normalize import extract_code
    
    raw_output = '''
Here's the fibonacci function:

```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

This implements the recursive approach.
    '''
    
    code = extract_code(raw_output)
    assert "def fibonacci" in code
    assert "```" not in code
    print("OK Normalize module working")

def test_log_module():
    """Test log module"""
    print("Testing log.py...")
    from src.log import write_execution_record, read_execution_records
    
    test_record = {
        "prompt_id": "test",
        "model": "test-model",
        "temperature": 0.0,
        "code": "def test(): pass",
        "contract_pass": True
    }
    
    test_path = "test_results.csv"
    write_execution_record(test_record, test_path)
    
    records = read_execution_records(test_path)
    assert len(records) >= 1
    
    # Cleanup
    if os.path.exists(test_path):
        os.remove(test_path)
    
    print("OK Log module working")

def test_extract_code_robustness():
    """Test code extraction with various formats"""
    print("Testing extract_code robustness...")
    from src.normalize import extract_code
    
    test_cases = [
        # Fenced code
        "```python\ndef fib(n): return n\n```",
        # Unfenced code
        "def fib(n): return n",
        # Mixed content
        "Here is the code:\n```\ndef fib(n): return n\n```\nThat's it!",
        # No fences but code-like
        "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
    ]
    
    for i, test_case in enumerate(test_cases):
        code = extract_code(test_case)
        assert "def fib" in code, f"Test case {i+1} failed: {code}"
    
    print("OK Extract code robustness verified")

def test_canon_signature_stability():
    """Test that canon signature is stable across re-runs"""
    print("Testing canon signature stability...")
    from src.canon import apply_canon, CanonPolicy
    
    test_code = "def fibonacci(n):\n    return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"
    policy = CanonPolicy()
    
    # Run canonicalization multiple times
    signatures = []
    for _ in range(3):
        result = apply_canon(test_code, policy)
        signatures.append(result["signature"])
    
    # All signatures should be identical
    assert len(set(signatures)) == 1, f"Signatures not stable: {signatures}"
    print("OK Canon signature stability verified")

def main():
    """Run all smoke tests"""
    print("SKYT Pipeline Smoke Tests")
    print("=" * 40)
    
    try:
        test_canon_module()
        test_compliance_module()
        test_transform_module()
        test_intent_capture_module()
        test_contract_module()
        test_normalize_module()
        test_log_module()
        test_extract_code_robustness()
        test_canon_signature_stability()
        
        print("\n" + "=" * 40)
        print("SUCCESS: ALL SMOKE TESTS PASSED")
        print("Pipeline refactor successful!")
        
    except Exception as e:
        print(f"\nFAILED: SMOKE TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
