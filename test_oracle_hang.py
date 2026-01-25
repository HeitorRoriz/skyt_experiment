#!/usr/bin/env python3
"""Test oracle on transformed binary_search code"""
import json
import sys

print("1. Load contract")
with open('contracts/templates.json') as f:
    templates = json.load(f)
contract = templates['binary_search_strict']

print("2. Create compliant code")
from src.contract_compliance import make_compliant

# Simulated LLM output with break
raw_code = '''
def binary_search(arr, target):
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
    return -1
'''

print("3. Transform to compliant")
compliant_code = make_compliant(raw_code, contract)
print("Compliant code:")
print(compliant_code)

print("\n4. Run oracle tests")
from src.oracle_system import OracleSystem
oracle = OracleSystem()

print("Calling run_oracle_tests...")
sys.stdout.flush()

# Add timeout
import threading
result = [None]
error = [None]

def run_oracle():
    try:
        result[0] = oracle.run_oracle_tests(compliant_code, contract)
    except Exception as e:
        error[0] = e

thread = threading.Thread(target=run_oracle)
thread.start()
thread.join(timeout=10)  # 10 second timeout

if thread.is_alive():
    print("TIMEOUT! Oracle is hanging")
    sys.exit(1)
elif error[0]:
    print(f"ERROR: {error[0]}")
    sys.exit(1)
else:
    print(f"Oracle result: passed={result[0]['passed']}")
    print("Done!")
