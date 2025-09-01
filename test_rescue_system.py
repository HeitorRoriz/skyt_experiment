#!/usr/bin/env python3
"""
Test script for the rescue system with failing cases
Tests deterministic micro-repair functionality and environment enforcement
"""

import sys
import os
sys.path.append('src')

from src.experiment import run_experiment
from src.contract import create_prompt_contract
from src.transform import try_repair
from src.compliance import check_contract_compliance
from src.canon import apply_canon
from src.config import CANON_POLICY

def test_rescue_function_rename():
    """Test rescue system fixing function name mismatch"""
    print("=== Test 1: Function Name Rescue ===")
    
    # Create contract expecting 'fibonacci' function
    contract = create_prompt_contract(
        prompt_id="test_rename",
        prompt="Write a function to compute fibonacci numbers",
        function_name="fibonacci",
        oracle='[{"input": [0], "output": 0}, {"input": [1], "output": 1}, {"input": [5], "output": 5}]'
    )
    
    # Code with wrong function name
    failing_code = """
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)
"""
    
    print(f"Original code has function 'fib', contract expects 'fibonacci'")
    
    # Test compliance before repair
    canon_result = apply_canon(failing_code, CANON_POLICY)
    compliance_before = check_contract_compliance(failing_code, contract, canon_result)
    print(f"Compliance before repair: {compliance_before['contract_pass']}")
    
    # Attempt repair
    repaired_code = try_repair(failing_code, contract)
    if repaired_code:
        print("[+] Repair successful")
        print(f"Repaired code:\n{repaired_code}")
        
        # Test compliance after repair
        canon_result_after = apply_canon(repaired_code, CANON_POLICY)
        compliance_after = check_contract_compliance(repaired_code, contract, canon_result_after)
        print(f"Compliance after repair: {compliance_after['contract_pass']}")
        print(f"Oracle pass: {compliance_after['oracle_pass']}")
    else:
        print("[-] Repair failed")
    
    print()

def test_rescue_signature_fix():
    """Test rescue system fixing function signature"""
    print("=== Test 2: Function Signature Rescue ===")
    
    contract = create_prompt_contract(
        prompt_id="test_signature",
        prompt="Write a function to add two numbers",
        function_name="add_numbers",
        signature="def add_numbers(a, b):",
        oracle='[{"input": [2, 3], "output": 5}, {"input": [0, 0], "output": 0}]'
    )
    
    # Code with wrong signature
    failing_code = """
def add_numbers(x):
    return x + x
"""
    
    print(f"Original code has signature 'add_numbers(x)', contract expects 'add_numbers(a, b)'")
    
    # Test repair
    repaired_code = try_repair(failing_code, contract)
    if repaired_code:
        print("[+] Repair successful")
        print(f"Repaired code:\n{repaired_code}")
        
        # Test compliance after repair
        canon_result = apply_canon(repaired_code, CANON_POLICY)
        compliance_after = check_contract_compliance(repaired_code, contract, canon_result)
        print(f"Compliance after repair: {compliance_after['contract_pass']}")
    else:
        print("[-] Repair failed")
    
    print()

def test_rescue_print_removal():
    """Test rescue system removing top-level prints for pure functions"""
    print("=== Test 3: Print Removal Rescue ===")
    
    contract = create_prompt_contract(
        prompt_id="test_prints",
        prompt="Write a pure function to compute factorial",
        function_name="factorial",
        oracle='[{"input": [0], "output": 1}, {"input": [5], "output": 120}]'
    )
    
    # Code with top-level prints
    failing_code = """
print("Computing factorial...")

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)

print("Factorial function defined")
"""
    
    print(f"Original code has top-level prints")
    
    # Test repair
    repaired_code = try_repair(failing_code, contract)
    if repaired_code:
        print("[+] Repair successful")
        print(f"Repaired code:\n{repaired_code}")
        
        # Test compliance after repair
        canon_result = apply_canon(repaired_code, CANON_POLICY)
        compliance_after = check_contract_compliance(repaired_code, contract, canon_result)
        print(f"Compliance after repair: {compliance_after['contract_pass']}")
        print(f"Oracle pass: {compliance_after['oracle_pass']}")
    else:
        print("[-] Repair failed")
    
    print()

def test_environment_enforcement():
    """Test environment enforcement modes"""
    print("=== Test 4: Environment Enforcement ===")
    
    # Contract with environment specification
    contract = create_prompt_contract(
        prompt_id="test_env",
        prompt="Write a simple function",
        function_name="simple_func",
        environment={"python_version": "3.12", "platform": "Linux"},  # Likely mismatch
        env_enforcement="if_specified"
    )
    
    print(f"Contract specifies environment: {contract.get('environment')}")
    print(f"Environment enforcement: {contract.get('env_enforcement')}")
    
    # Test environment checking directly
    from src.experiment import _check_environment_compliance
    from src.canon import compute_minimal_env_signature
    from src.contract import get_contract_environment
    
    current_env_sig = compute_minimal_env_signature(get_contract_environment(contract))
    contract_env = get_contract_environment(contract)
    env_check_result = _check_environment_compliance(current_env_sig, contract_env)
    
    print(f"Environment OK: {env_check_result['ok']}")
    print(f"Environment mismatches: {env_check_result['mismatches']}")
    
    print()

def main():
    """Run all rescue system tests"""
    print("Testing SKYT Rescue System")
    print("=" * 50)
    
    test_rescue_function_rename()
    test_rescue_signature_fix()
    test_rescue_print_removal()
    test_environment_enforcement()
    
    print("Rescue system testing completed!")

if __name__ == "__main__":
    main()
