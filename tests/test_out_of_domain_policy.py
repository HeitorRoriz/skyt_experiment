"""
Unit tests for out-of-domain policy system.

Tests each policy type in isolation to ensure correct behavior.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.policies.out_of_domain import OODSpec, OODPolicy


# Mock functions for testing

def fibonacci_with_raise(n):
    """Fibonacci that raises ValueError for n < 0"""
    if n < 0:
        raise ValueError("Input must be non-negative")
    if n <= 1:
        return n
    return fibonacci_with_raise(n - 1) + fibonacci_with_raise(n - 2)


def fibonacci_return_zero(n):
    """Fibonacci that returns 0 for n <= 0"""
    if n <= 0:
        return 0
    if n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def fibonacci_return_minus_one(n):
    """Fibonacci that returns -1 for n < 0"""
    if n < 0:
        return -1
    if n <= 1:
        return n
    return fibonacci_return_minus_one(n - 1) + fibonacci_return_minus_one(n - 2)


def always_raises(n):
    """Always raises ValueError"""
    raise ValueError("Always fails")


def always_returns_42(n):
    """Always returns 42"""
    return 42


# Test: allow policy (default)

def test_allow_policy_accepts_anything():
    """Allow policy should accept any implementation"""
    spec = OODSpec(policy="allow", examples=[{"n": -1}, {"n": -5}])
    policy = OODPolicy(spec)
    
    # Any behavior should be accepted with "allow"
    assert policy.check_examples(fibonacci_with_raise) == True
    assert policy.check_examples(fibonacci_return_zero) == True
    assert policy.check_examples(always_raises) == True
    assert policy.check_examples(always_returns_42) == True


def test_default_policy_is_allow():
    """Default policy should be 'allow'"""
    spec = OODSpec(examples=[{"n": -1}])
    policy = OODPolicy(spec)
    
    assert policy.spec.policy == "allow"
    assert policy.check_examples(fibonacci_with_raise) == True


def test_no_examples_always_passes():
    """Policy with no examples should always pass"""
    spec = OODSpec(policy="must_raise", exception="ValueError", examples=[])
    policy = OODPolicy(spec)
    
    # Even if implementation doesn't raise, should pass (no examples to check)
    assert policy.check_examples(fibonacci_return_zero) == True


# Test: must_raise policy

def test_must_raise_accepts_correct_exception():
    """must_raise should accept if function raises specified exception"""
    spec = OODSpec(
        policy="must_raise",
        exception="ValueError",
        examples=[{"n": -1}, {"n": -5}]
    )
    policy = OODPolicy(spec)
    
    assert policy.check_examples(fibonacci_with_raise) == True


def test_must_raise_rejects_no_exception():
    """must_raise should reject if function doesn't raise"""
    spec = OODSpec(
        policy="must_raise",
        exception="ValueError",
        examples=[{"n": -1}]
    )
    policy = OODPolicy(spec)
    
    assert policy.check_examples(fibonacci_return_zero) == False


def test_must_raise_accepts_any_exception_if_not_specified():
    """must_raise with no exception name should accept any exception"""
    spec = OODSpec(
        policy="must_raise",
        exception=None,
        examples=[{"n": -1}]
    )
    policy = OODPolicy(spec)
    
    assert policy.check_examples(fibonacci_with_raise) == True
    assert policy.check_examples(always_raises) == True
    assert policy.check_examples(fibonacci_return_zero) == False


def test_must_raise_rejects_wrong_exception_type():
    """must_raise should reject if wrong exception type is raised"""
    spec = OODSpec(
        policy="must_raise",
        exception="TypeError",
        examples=[{"n": -1}]
    )
    policy = OODPolicy(spec)
    
    # Function raises ValueError, but we expect TypeError
    assert policy.check_examples(fibonacci_with_raise) == False


# Test: must_return policy

def test_must_return_accepts_correct_value():
    """must_return should accept if function returns specified value"""
    spec = OODSpec(
        policy="must_return",
        return_value=0,
        examples=[{"n": -1}, {"n": -5}]
    )
    policy = OODPolicy(spec)
    
    assert policy.check_examples(fibonacci_return_zero) == True


def test_must_return_rejects_wrong_value():
    """must_return should reject if function returns wrong value"""
    spec = OODSpec(
        policy="must_return",
        return_value=0,
        examples=[{"n": -1}]
    )
    policy = OODPolicy(spec)
    
    assert policy.check_examples(fibonacci_return_minus_one) == False


def test_must_return_rejects_exception():
    """must_return should reject if function raises exception"""
    spec = OODSpec(
        policy="must_return",
        return_value=0,
        examples=[{"n": -1}]
    )
    policy = OODPolicy(spec)
    
    assert policy.check_examples(fibonacci_with_raise) == False


def test_must_return_with_non_numeric_value():
    """must_return should work with any JSON-serializable value"""
    spec = OODSpec(
        policy="must_return",
        return_value=None,
        examples=[{"n": -1}]
    )
    policy = OODPolicy(spec)
    
    def return_none(n):
        if n < 0:
            return None
        return n
    
    assert policy.check_examples(return_none) == True


# Test: forbid_transform policy

def test_forbid_transform_accepts_identical_behavior():
    """forbid_transform should accept if behavior unchanged"""
    spec = OODSpec(
        policy="forbid_transform",
        examples=[{"n": -1}, {"n": -5}]
    )
    policy = OODPolicy(spec)
    
    # Same function as baseline - should pass
    assert policy.check_examples(
        fibonacci_with_raise, 
        baseline_fn=fibonacci_with_raise
    ) == True


def test_forbid_transform_rejects_changed_behavior():
    """forbid_transform should reject if behavior changes"""
    spec = OODSpec(
        policy="forbid_transform",
        examples=[{"n": -1}]
    )
    policy = OODPolicy(spec)
    
    # Different behavior - should fail
    assert policy.check_examples(
        fibonacci_return_zero,  # returns 0
        baseline_fn=fibonacci_with_raise  # raises ValueError
    ) == False


def test_forbid_transform_accepts_without_baseline():
    """forbid_transform without baseline should accept (no comparison possible)"""
    spec = OODSpec(
        policy="forbid_transform",
        examples=[{"n": -1}]
    )
    policy = OODPolicy(spec)
    
    # No baseline provided - should pass by default
    assert policy.check_examples(fibonacci_return_zero, baseline_fn=None) == True


def test_forbid_transform_compares_return_values():
    """forbid_transform should compare return values correctly"""
    spec = OODSpec(
        policy="forbid_transform",
        examples=[{"n": -1}]
    )
    policy = OODPolicy(spec)
    
    # Both return same value - should pass
    assert policy.check_examples(
        fibonacci_return_zero,
        baseline_fn=fibonacci_return_zero
    ) == True
    
    # Different return values - should fail
    assert policy.check_examples(
        fibonacci_return_minus_one,  # returns -1
        baseline_fn=fibonacci_return_zero  # returns 0
    ) == False


def test_forbid_transform_compares_exceptions():
    """forbid_transform should compare exception types"""
    spec = OODSpec(
        policy="forbid_transform",
        examples=[{"n": -1}]
    )
    policy = OODPolicy(spec)
    
    def raise_type_error(n):
        if n < 0:
            raise TypeError("Wrong type")
        return n
    
    # Both raise ValueError - should pass
    assert policy.check_examples(
        fibonacci_with_raise,
        baseline_fn=fibonacci_with_raise
    ) == True
    
    # Different exception types - should fail
    assert policy.check_examples(
        raise_type_error,  # raises TypeError
        baseline_fn=fibonacci_with_raise  # raises ValueError
    ) == False


# Test: max_checks cap

def test_max_checks_limits_examples():
    """Policy should only check up to max_checks examples"""
    # Provide 5 examples but set max_checks=2
    spec = OODSpec(
        policy="must_return",
        return_value=0,
        examples=[
            {"n": -1},  # Will be checked
            {"n": -2},  # Will be checked
            {"n": -3},  # Will NOT be checked
            {"n": -4},  # Will NOT be checked
            {"n": -5},  # Will NOT be checked
        ],
        max_checks=2
    )
    policy = OODPolicy(spec)
    
    # Should only check first 2 examples
    assert len(policy.examples) == 2
    assert policy.examples[0] == {"n": -1}
    assert policy.examples[1] == {"n": -2}
    
    # Function that only satisfies first 2 examples should pass
    def return_zero_for_minus_1_and_2(n):
        if n in [-1, -2]:
            return 0
        raise ValueError("Fails for other values")
    
    assert policy.check_examples(return_zero_for_minus_1_and_2) == True


def test_default_max_checks_is_3():
    """Default max_checks should be 3"""
    spec = OODSpec(examples=[{"n": i} for i in range(10)])
    policy = OODPolicy(spec)
    
    assert policy.spec.max_checks == 3
    assert len(policy.examples) == 3


# Test: None spec defaults

def test_none_spec_creates_allow_policy():
    """Passing None as spec should create allow policy"""
    policy = OODPolicy(None)
    
    assert policy.spec.policy == "allow"
    assert policy.examples == []
    assert policy.check_examples(fibonacci_with_raise) == True


# Test: Edge cases

def test_empty_examples_list():
    """Empty examples list should always pass"""
    spec = OODSpec(
        policy="must_raise",
        exception="ValueError",
        examples=[]
    )
    policy = OODPolicy(spec)
    
    assert policy.check_examples(fibonacci_return_zero) == True


def test_multiple_parameters_in_examples():
    """Examples can have multiple parameters"""
    spec = OODSpec(
        policy="must_return",
        return_value=0,
        examples=[{"x": -1, "y": 2}, {"x": -5, "y": 10}]
    )
    policy = OODPolicy(spec)
    
    def multi_param(x, y):
        if x < 0:
            return 0
        return x + y
    
    assert policy.check_examples(multi_param) == True


def test_all_examples_must_pass():
    """All examples must pass for check to succeed"""
    spec = OODSpec(
        policy="must_return",
        return_value=0,
        examples=[{"n": -1}, {"n": -2}, {"n": -3}]
    )
    policy = OODPolicy(spec)
    
    def fails_on_minus_2(n):
        if n == -2:
            raise ValueError("Fails on -2")
        return 0
    
    # Should fail because one example fails
    assert policy.check_examples(fails_on_minus_2) == False


if __name__ == "__main__":
    # Run all test functions
    test_functions = [
        test_allow_policy_accepts_anything,
        test_default_policy_is_allow,
        test_no_examples_always_passes,
        test_must_raise_accepts_correct_exception,
        test_must_raise_rejects_no_exception,
        test_must_raise_accepts_any_exception_if_not_specified,
        test_must_raise_rejects_wrong_exception_type,
        test_must_return_accepts_correct_value,
        test_must_return_rejects_wrong_value,
        test_must_return_rejects_exception,
        test_must_return_with_non_numeric_value,
        test_forbid_transform_accepts_identical_behavior,
        test_forbid_transform_rejects_changed_behavior,
        test_forbid_transform_accepts_without_baseline,
        test_forbid_transform_compares_return_values,
        test_forbid_transform_compares_exceptions,
        test_max_checks_limits_examples,
        test_default_max_checks_is_3,
        test_none_spec_creates_allow_policy,
        test_empty_examples_list,
        test_multiple_parameters_in_examples,
        test_all_examples_must_pass,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}: ERROR - {e}")
            failed += 1
    
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
