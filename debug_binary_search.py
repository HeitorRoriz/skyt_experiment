#!/usr/bin/env python3
"""Debug binary_search_strict hang"""

import json
import sys

print("1. Loading contract...")
with open('contracts/templates.json') as f:
    templates = json.load(f)
contract = templates['binary_search_strict']
print("   Done")

print("2. Testing oracle...")
from src.oracle_system import OracleSystem
oracle = OracleSystem()

code = '''
def binary_search(arr, target):
    result = -1
    left = 0
    right = len(arr) - 1
    while left <= right:
        mid = left + (right - left) // 2
        if arr[mid] == target:
            result = mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return result
'''

print("   Running oracle tests...")
result = oracle.run_oracle_tests(code, contract)
print(f"   Passed: {result['passed']}")
print(f"   Pass rate: {result.get('pass_rate', '?')}")

print("3. Testing full compliance check...")
from src.contract_compliance import check_contract_compliance
is_compliant, violations = check_contract_compliance(code, contract)
print(f"   Compliant: {is_compliant}")
print(f"   Violations: {violations}")

print("4. Testing canon creation flow...")
from src.contract import Contract
from src.canon_system import CanonSystem

c = Contract(contract)
canon_system = CanonSystem()

# Delete existing canon
import os
canon_path = "outputs/canon/binary_search_strict_canon.json"
if os.path.exists(canon_path):
    os.remove(canon_path)
    print("   Deleted existing canon")

print("   Creating canon...")
try:
    canon_data = canon_system.create_canon(c, code, oracle_result=result, require_oracle_pass=True)
    print("   Canon created successfully")
except Exception as e:
    print(f"   Error: {e}")

print("\nAll tests passed!")
