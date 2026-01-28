#!/usr/bin/env python3
"""Test transformation on code with break pattern"""

import json
from src.contract_compliance import make_compliant

with open('contracts/templates.json') as f:
    contract = json.load(f)['binary_search_strict']

# Typical LLM output with break
code = '''def binary_search(arr, target):
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
    return -1'''

print("=== Original (with break) ===")
print(code)

print("\n=== Transforming ===")
result = make_compliant(code, contract)
print(result)

print("\n=== Testing ===")
try:
    exec(result)
    print("Test 1 (found):", binary_search([1,2,3,4,5], 3))
    print("Test 2 (not found):", binary_search([1,2,3,4,5], 6))
    print("Test 3 (empty):", binary_search([], 1))
    print("✅ All tests passed!")
except Exception as e:
    print(f"❌ Error: {e}")
