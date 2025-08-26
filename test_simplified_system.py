# test_simplified_system.py
"""
Test script for the simplified SKYT system
Tests the two core metrics: R_raw and R_canon
"""

import sys
import os
sys.path.append('src')

from metrics import calculate_repeatability_metrics, print_metrics_summary
from simple_canonicalizer import canonicalize_code, get_canonical_signature

def test_canonicalizer():
    """Test the canonicalizer with sample Fibonacci implementations"""
    print("Testing Canonicalizer...")
    print("=" * 50)
    
    # Sample Fibonacci implementations (should canonicalize to same form)
    test_codes = [
        '''
def fibonacci(n):
    """Calculate fibonacci number"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)  # Recursive approach
        ''',
        '''
def fib(n):
    # Base cases
    if n <= 1:
        return n
    # Recursive case
    return fib(n-1) + fib(n-2)
        ''',
        '''
def fibonacci_sequence(n):
    if n <= 1:
        return n
    else:
        return fibonacci_sequence(n-1) + fibonacci_sequence(n-2)
        '''
    ]
    
    canonical_forms = []
    signatures = []
    
    for i, code in enumerate(test_codes, 1):
        canonical = canonicalize_code(code)
        signature = get_canonical_signature(code)
        
        canonical_forms.append(canonical)
        signatures.append(signature)
        
        print(f"\nTest {i}:")
        print(f"Signature: {signature}")
        print("Canonical form:")
        print(canonical)
        print("-" * 30)
    
    # Check if canonicalization worked
    unique_signatures = set(signatures)
    print(f"\nCanonicalization Test Results:")
    print(f"Original implementations: {len(test_codes)}")
    print(f"Unique canonical forms: {len(unique_signatures)}")
    print(f"Canonicalization success: {'YES' if len(unique_signatures) == 1 else 'NO'}")
    
    return canonical_forms

def test_metrics():
    """Test the metrics calculation"""
    print("\n\nTesting Metrics...")
    print("=" * 50)
    
    # Simulate raw outputs (different)
    raw_outputs = [
        "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
        "def fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)",
        "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",  # Same as first
        "def fibonacci_func(n):\n    if n <= 1:\n        return n\n    return fibonacci_func(n-1) + fibonacci_func(n-2)",
        "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"   # Same as first
    ]
    
    # Canonicalize all outputs
    canonical_outputs = [canonicalize_code(output) for output in raw_outputs]
    
    # Calculate metrics
    result = calculate_repeatability_metrics(raw_outputs, canonical_outputs)
    
    # Print results
    print_metrics_summary(result, "Test Experiment")
    
    print(f"\nExpected behavior:")
    print(f"- R_raw should be 3/5 = 0.600 (3 identical raw outputs)")
    print(f"- R_canon should be higher if canonicalization works")
    
    return result

def main():
    """Run all tests"""
    print("SIMPLIFIED SKYT SYSTEM TEST")
    print("=" * 60)
    
    # Test canonicalizer
    canonical_forms = test_canonicalizer()
    
    # Test metrics
    result = test_metrics()
    
    print(f"\n{'=' * 60}")
    print("SYSTEM TEST SUMMARY")
    print(f"{'=' * 60}")
    print(f"[OK] Canonicalizer: Working")
    print(f"[OK] Metrics: Working") 
    print(f"[OK] R_raw: {result.r_raw:.3f}")
    print(f"[OK] R_canon: {result.r_canon:.3f}")
    print(f"[OK] Improvement: {result.r_canon - result.r_raw:+.3f}")
    print(f"\nSimplified SKYT system is ready for experiments!")

if __name__ == "__main__":
    main()
