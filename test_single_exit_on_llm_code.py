#!/usr/bin/env python3
"""Test SingleExitTransformer on the exact LLM-generated code"""

from src.transformations.structural.single_exit_transformer import SingleExitTransformer

code = '''def binary_search(arr, target):
    left = 0
    right = len(arr) - 1
    result = -1
    while left <= right:
        mid = left + (right - left) // 2
        if arr[mid] == target:
            result = mid
            break
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return result'''

print("=== Original ===")
print(code)

t = SingleExitTransformer()
print(f"\nCan transform: {t.can_transform(code, '')}")

result = t.transform(code, '')
print(f"Success: {result.success}")

if result.success:
    print("\n=== Transformed ===")
    print(result.transformed_code)
else:
    print(f"\nError: {result.error_message}")
