#!/usr/bin/env python3
"""Debug why transformed binary_search is failing oracle tests"""

import json
from src.contract_compliance import make_compliant, check_contract_compliance
from src.oracle_system import OracleSystem

with open('contracts/templates.json') as f:
    contract = json.load(f)['binary_search_strict']

# Simulate what LLM might generate
test_codes = [
    # Pattern 1: break statement
    '''def binary_search(arr, target):
    left = 0
    right = len(arr) - 1
    while left <= right:
        mid = left + (right - left) // 2
        if arr[mid] == target:
            break
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    if left <= right:
        return mid
    return -1''',
    
    # Pattern 2: early return
    '''def binary_search(arr, target):
    left = 0
    right = len(arr) - 1
    while left <= right:
        mid = left + (right - left) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1'''
]

oracle = OracleSystem()

for i, code in enumerate(test_codes, 1):
    print(f"\n{'='*60}")
    print(f"TEST CASE {i}")
    print(f"{'='*60}")
    
    print("\n1. Check original compliance:")
    is_compliant, violations = check_contract_compliance(code, contract)
    print(f"   Compliant: {is_compliant}")
    if violations:
        print(f"   Violations: {violations[:2]}")
    
    print("\n2. Test original with oracle:")
    result = oracle.run_oracle_tests(code, contract, timeout=3)
    print(f"   Passed: {result['passed']}")
    if not result['passed']:
        print(f"   Error: {result.get('error', 'Unknown')}")
    
    print("\n3. Transform to compliant:")
    transformed = make_compliant(code, contract)
    print("   Transformed code:")
    for line in transformed.split('\n')[:15]:
        print(f"   {line}")
    
    print("\n4. Check transformed compliance:")
    is_compliant, violations = check_contract_compliance(transformed, contract)
    print(f"   Compliant: {is_compliant}")
    if violations:
        print(f"   Violations: {violations[:2]}")
    
    print("\n5. Test transformed with oracle:")
    result = oracle.run_oracle_tests(transformed, contract, timeout=3)
    print(f"   Passed: {result['passed']}")
    if not result['passed']:
        print(f"   Error: {result.get('error', 'Unknown')}")
    else:
        print(f"   Pass rate: {result.get('pass_rate', '?')}")
