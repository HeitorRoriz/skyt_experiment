#!/usr/bin/env python3
"""Test oracle execution on binary_search"""
import json
import sys
import threading

print("1. Load contract")
with open('contracts/templates.json') as f:
    contract = json.load(f)['binary_search_strict']

print("2. Test code")
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

print("3. Run oracle with timeout")
from src.oracle_system import OracleSystem
oracle = OracleSystem()

result = [None]
error = [None]

def run_test():
    try:
        print("   Oracle starting...")
        sys.stdout.flush()
        result[0] = oracle.run_oracle_tests(code, contract)
        print("   Oracle finished")
    except Exception as e:
        error[0] = e
        print(f"   Oracle error: {e}")

thread = threading.Thread(target=run_test, daemon=True)
thread.start()
thread.join(timeout=5)

if thread.is_alive():
    print("\n❌ TIMEOUT! Oracle is hanging")
    print("   The oracle test is stuck in infinite loop")
    sys.exit(1)
elif error[0]:
    print(f"\n❌ ERROR: {error[0]}")
    sys.exit(1)
else:
    print(f"\n✅ SUCCESS: passed={result[0]['passed']}")
