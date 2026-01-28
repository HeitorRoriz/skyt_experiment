#!/usr/bin/env python3
"""Simulate the exact canon creation flow for binary_search_strict"""
import json
import sys

print("=== Simulating Canon Creation Flow ===\n")

print("1. Load contract")
with open('contracts/templates.json') as f:
    contract = json.load(f)['binary_search_strict']

print("2. Simulate 3 LLM outputs (all with early return)")
outputs = [
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
    return -1''',
    
    '''def binary_search(arr, target):
    low = 0
    high = len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1''',
    
    '''def binary_search(arr, target):
    left = 0
    right = len(arr) - 1
    while left <= right:
        mid = left + (right - left) // 2
        if arr[mid] == target:
            return mid
        if arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1'''
]

print("\n3. Check each output for compliance")
from src.contract_compliance import check_contract_compliance, make_compliant
from src.oracle_system import OracleSystem

oracle = OracleSystem()
first_oracle_passing = None
first_oracle_passing_idx = None

for i, code in enumerate(outputs):
    print(f"\n--- Output {i+1} ---")
    
    print(f"  Step 3.{i+1}.1: Run oracle tests...")
    sys.stdout.flush()
    oracle_result = oracle.run_oracle_tests(code, contract)
    print(f"    Oracle passed: {oracle_result['passed']}")
    
    if oracle_result["passed"]:
        if first_oracle_passing is None:
            first_oracle_passing = code
            first_oracle_passing_idx = i
        
        print(f"  Step 3.{i+1}.2: Check compliance...")
        sys.stdout.flush()
        is_compliant, violations = check_contract_compliance(code, contract)
        print(f"    Compliant: {is_compliant}")
        if not is_compliant:
            print(f"    Violations: {violations[:2]}")
        
        if is_compliant:
            print(f"  ✅ Would use output {i+1} as canon")
            break
    else:
        print(f"  ❌ Oracle failed")

print(f"\n4. No compliant outputs found")
print(f"   Transforming output {first_oracle_passing_idx + 1}...")
sys.stdout.flush()

compliant_code = make_compliant(first_oracle_passing, contract)
print("   Transformation complete")

print("\n5. Verify transformed code passes oracle...")
sys.stdout.flush()
oracle_result = oracle.run_oracle_tests(compliant_code, contract)
print(f"   Oracle passed: {oracle_result['passed']}")

print("\n✅ Canon creation flow completed successfully")
