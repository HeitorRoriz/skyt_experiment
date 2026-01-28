#!/usr/bin/env python3
"""Test transformers on binary_search code"""

from src.transformations.structural.single_exit_transformer import SingleExitTransformer
from src.transformations.structural.break_remover import BreakRemover

# Typical binary_search with multiple returns
code = '''
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

print("=== Original code ===")
print(code)

print("\n=== Testing SingleExitTransformer ===")
t1 = SingleExitTransformer()
can = t1.can_transform(code, "")
print(f"Can transform: {can}")

if can:
    print("Applying transformation...")
    result = t1.transform(code, "")
    print(f"Success: {result.success}")
    if result.success:
        print("\n=== Transformed ===")
        print(result.transformed_code)
    else:
        print(f"Error: {result.error_message}")
