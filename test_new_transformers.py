#!/usr/bin/env python3
"""Test the new MISRA/P10 transformers"""

from src.transformations.structural.single_exit_transformer import SingleExitTransformer
from src.transformations.structural.break_remover import BreakRemover

# Test code with violations
code_with_early_return = '''
def is_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
'''

code_with_break = '''
def is_prime(n):
    result = True
    if n <= 1:
        result = False
    else:
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                result = False
                break
    return result
'''

print("=" * 60)
print("Testing SingleExitTransformer (MISRA 15.5)")
print("=" * 60)
print("\nINPUT (has early returns):")
print(code_with_early_return)

t1 = SingleExitTransformer()
can_transform = t1.can_transform(code_with_early_return, "")
print(f"Can transform: {can_transform}")

if can_transform:
    result1 = t1.transform(code_with_early_return, "")
    print(f"Success: {result1.success}")
    if result1.success:
        print("\nOUTPUT (single exit point):")
        print(result1.transformed_code)
    else:
        print(f"Error: {result1.error_message}")

print("\n" + "=" * 60)
print("Testing BreakRemover (MISRA 15.4)")
print("=" * 60)
print("\nINPUT (has break):")
print(code_with_break)

t2 = BreakRemover()
can_transform = t2.can_transform(code_with_break, "")
print(f"Can transform: {can_transform}")

if can_transform:
    result2 = t2.transform(code_with_break, "")
    print(f"Success: {result2.success}")
    if result2.success:
        print("\nOUTPUT (no break):")
        print(result2.transformed_code)
    else:
        print(f"Error: {result2.error_message}")

print("\n" + "=" * 60)
print("Combined transformation test")
print("=" * 60)

# Test combined: early return + break
combined_violations = '''
def is_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
'''

print("\nINPUT:")
print(combined_violations)

# First apply SingleExit
result = t1.transform(combined_violations, "")
if result.success:
    code = result.transformed_code
    print("\nAfter SingleExitTransformer:")
    print(code)
    
    # Then apply BreakRemover if needed
    if t2.can_transform(code, ""):
        result2 = t2.transform(code, "")
        if result2.success:
            print("\nAfter BreakRemover:")
            print(result2.transformed_code)
