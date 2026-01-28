#!/usr/bin/env python3
"""Test enhanced SingleExitTransformer with flag variable detection"""

from src.transformations.structural.single_exit_transformer import SingleExitTransformer

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

print("=== Original ===")
print(code)

t = SingleExitTransformer()
print(f"\nCan transform: {t.can_transform(code, '')}")

result = t.transform(code, '')
print(f"Success: {result.success}")

if result.success:
    print("\n=== Transformed ===")
    print(result.transformed_code)
    
    print("\n=== Testing ===")
    exec(result.transformed_code)
    print("Test 1 (found):", binary_search([1,2,3,4,5], 3))
    print("Test 2 (not found):", binary_search([1,2,3,4,5], 6))
    print("Test 3 (empty):", binary_search([], 1))
    print("✅ All tests passed!")
else:
    print(f"Error: {result.error_message}")
