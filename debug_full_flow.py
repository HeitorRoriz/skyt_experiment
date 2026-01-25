#!/usr/bin/env python3
"""Debug the full experiment flow for binary_search_strict"""
import json
import sys

print("1. Load contract")
sys.stdout.flush()
with open('contracts/templates.json') as f:
    contract = json.load(f)['binary_search_strict']

print("2. Generate code (simulated)")
sys.stdout.flush()
code = '''def binary_search(arr, target):
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

print("3. Check compliance")
sys.stdout.flush()
from src.contract_compliance import check_contract_compliance, make_compliant
is_compliant, violations = check_contract_compliance(code, contract)
print(f"   Compliant: {is_compliant}")

print("4. Make compliant")
sys.stdout.flush()
compliant_code = make_compliant(code, contract)
print("   Done")

print("5. Oracle test")
sys.stdout.flush()
from src.oracle_system import OracleSystem
oracle = OracleSystem()
result = oracle.run_oracle_tests(compliant_code, contract)
print(f"   Passed: {result['passed']}")

print("6. Create canon")
sys.stdout.flush()
from src.contract import Contract
from src.canon_system import CanonSystem
c = Contract(contract)
canon_system = CanonSystem()

import os
if os.path.exists("outputs/canon/binary_search_strict_canon.json"):
    os.remove("outputs/canon/binary_search_strict_canon.json")

canon_data = canon_system.create_canon(c, compliant_code, oracle_result=result, require_oracle_pass=True)
print("   Done")

print("\nSUCCESS!")
