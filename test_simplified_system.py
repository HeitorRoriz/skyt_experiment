# test_simplified_system.py
"""
Test script for the simplified SKYT experiment system
"""

from src.canonicalizer import canonicalize_code, generate_signature
from src.determinism_lint import lint_code, is_deterministic, format_violations
from src.contract_checker import check_fibonacci_contract
from src.metrics import calculate_metrics
from src.log import ExperimentLogger
from src.experiment import LLMClient
from src.run_experiment import ExperimentRunner, ExperimentConfig
from src.analyze import analyze_experiment_results
from src.summarize import print_summary_table

def test_canonicalizer():
    """Test the canonicalizer module"""
    print("Testing Canonicalizer...")
    
    test_code = '''
def fib():
    """Generate fibonacci numbers"""
    # This is a comment
    a, b = 0, 1
    result = []
    for i in range(20):
        result.append(a)
        a, b = b, a + b
    return result
'''
    
    canonical_code = canonicalize_code(test_code, "fibonacci")
    if canonical_code:
        print("[OK] Canonicalization successful")
        signature = generate_signature(canonical_code)
        print(f"[OK] Signature generated: {signature[:16]}...")
    else:
        print("[FAIL] Canonicalization failed")

def test_determinism_lint():
    """Test the determinism linter"""
    print("\nTesting Determinism Linter...")
    
    good_code = '''
def fibonacci():
    a, b = 0, 1
    result = []
    for i in range(20):
        result.append(a)
        a, b = b, a + b
    return result
'''
    
    bad_code = '''
import random
def fibonacci():
    return [random.randint(0, 100) for _ in range(20)]
'''
    
    if is_deterministic(good_code):
        print("[OK] Good code passed determinism check")
    else:
        print("[FAIL] Good code failed determinism check")
    
    if not is_deterministic(bad_code):
        print("[OK] Bad code correctly flagged as non-deterministic")
        violations = lint_code(bad_code)
        print(f"  Found {len(violations)} violations")
    else:
        print("[FAIL] Bad code incorrectly passed determinism check")

def test_contract_checker():
    """Test the contract checker"""
    print("\nTesting Contract Checker...")
    
    test_code = '''
def fibonacci():
    result = []
    a, b = 0, 1
    for i in range(20):
        result.append(a)
        a, b = b, a + b
    return result
'''
    
    result = check_fibonacci_contract(test_code)
    if result.passed:
        print("[OK] Contract check passed")
        print(f"  Oracle result: {result.oracle_result}")
        print(f"  Canonical signature: {result.canonical_signature[:16] if result.canonical_signature else 'None'}...")
    else:
        print("[FAIL] Contract check failed")
        print(f"  Error: {result.error_message}")

def test_metrics():
    """Test the metrics calculation"""
    print("\nTesting Metrics...")
    
    raw_outputs = [
        "def fib(): return [0,1,1,2,3,5,8,13,21,34,55,89,144,233,377,610,987,1597,2584,4181]",
        "def fib(): return [0,1,1,2,3,5,8,13,21,34,55,89,144,233,377,610,987,1597,2584,4181]",
        "def fibonacci(): return [0,1,1,2,3,5,8,13,21,34,55,89,144,233,377,610,987,1597,2584,4181]",
        "def fib(): return list(range(20))",  # Different output
        "def fib(): return [0,1,1,2,3,5,8,13,21,34,55,89,144,233,377,610,987,1597,2584,4181]"
    ]
    
    canonical_outputs = [
        "def fibonacci(n):\n    return 1 if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
        "def fibonacci(n):\n    return 1 if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
        "def fibonacci(n):\n    return 1 if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
        None,  # Failed canonicalization
        "def fibonacci(n):\n    return 1 if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"
    ]
    
    contract_passes = [True, True, True, False, True]  # 4 out of 5 pass
    
    metrics = calculate_metrics(raw_outputs, canonical_outputs, contract_passes)
    print(f"[OK] Metrics calculated:")
    print(f"  R_raw: {metrics.r_raw:.3f}")
    print(f"  R_canon: {metrics.r_canon:.3f}")
    print(f"  Coverage: {metrics.canon_coverage:.3f}")
    print(f"  Delta: {metrics.rescue_delta:.3f}")

def main():
    """Run all tests"""
    print("=" * 60)
    print("SIMPLIFIED SKYT SYSTEM TESTS")
    print("=" * 60)
    
    test_canonicalizer()
    test_determinism_lint()
    test_contract_checker()
    test_metrics()
    
    print("\n" + "=" * 60)
    print("SYSTEM READY FOR EXPERIMENTS")
    print("=" * 60)
    print("To run experiments:")
    print("1. Set OPENAI_API_KEY environment variable")
    print("2. Run: python src/run_experiment.py")
    print("3. Analyze: python src/analyze.py")
    print("4. Summarize: python src/summarize.py")

if __name__ == "__main__":
    main()
