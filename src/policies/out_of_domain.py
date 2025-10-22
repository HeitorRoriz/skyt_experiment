"""
Out-of-Domain Policy System for SKYT

This module provides fine-grained control over how transformations may alter
code behavior outside the contract's specified domain.

Policy Types:
- allow: (default) Transformations may change OOD behavior
- must_raise: OOD inputs must raise specified exception
- must_return: OOD inputs must return specified value
- forbid_transform: OOD behavior must remain unchanged from baseline

All checks are example-based, deterministic, and capped to avoid performance issues.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Literal, Callable

PolicyName = Literal["allow", "must_raise", "must_return", "forbid_transform"]


@dataclass
class OODSpec:
    """Specification for out-of-domain behavior policy"""
    policy: PolicyName = "allow"
    exception: Optional[str] = None
    return_value: Optional[Any] = None
    examples: List[Dict[str, Any]] = field(default_factory=list)
    max_checks: int = 3


class OODPolicy:
    """
    Validates implementation behavior on out-of-domain inputs
    according to a specified policy.
    
    Usage:
        spec = OODSpec(policy="must_raise", exception="ValueError", 
                       examples=[{"n": -1}, {"n": -5}])
        policy = OODPolicy(spec)
        is_valid = policy.check_examples(impl_fn, baseline_fn)
    """
    
    def __init__(self, spec: Optional[OODSpec]):
        """
        Initialize OOD policy validator.
        
        Args:
            spec: Policy specification. If None, defaults to "allow" policy.
        """
        self.spec = spec or OODSpec()
        # Cap examples by max_checks to avoid performance issues
        self.examples = (self.spec.examples or [])[: self.spec.max_checks]

    def check_examples(
        self,
        impl_fn: Callable[..., Any],
        baseline_fn: Optional[Callable[..., Any]] = None,
    ) -> bool:
        """
        Returns True if the implementation conforms to the OOD policy
        on the provided examples. No exceptions escape; failures → False.
        
        Args:
            impl_fn: The implementation function to validate
            baseline_fn: Pre-transformation function (only used for forbid_transform)
            
        Returns:
            True if all examples pass the policy check, False otherwise
        """
        # Early return for "allow" policy or no examples
        if not self.examples or self.spec.policy == "allow":
            return True

        # Check each example
        for args in self.examples:
            ok = self._check_one(impl_fn, baseline_fn, args)
            if not ok:
                return False
        
        return True

    # --- Internal validation methods ---
    
    def _check_one(
        self,
        impl_fn: Callable[..., Any],
        baseline_fn: Optional[Callable[..., Any]],
        args: Dict[str, Any],
    ) -> bool:
        """
        Check a single example against the policy.
        
        Args:
            impl_fn: Implementation to validate
            baseline_fn: Baseline for comparison (forbid_transform only)
            args: Input arguments as dict
            
        Returns:
            True if example passes policy, False otherwise
        """
        pol = self.spec.policy
        
        if pol == "must_raise":
            return self._expect_exception(impl_fn, args, self.spec.exception)
        
        if pol == "must_return":
            return self._expect_return(impl_fn, args, self.spec.return_value)
        
        if pol == "forbid_transform":
            # Compare to pre-transform/baseline if available; otherwise allow
            if baseline_fn is None:
                return True
            return self._expect_same_behavior(baseline_fn, impl_fn, args)
        
        # "allow" policy or unknown - default to True
        return True

    def _expect_exception(
        self, 
        fn: Callable[..., Any], 
        args: Dict[str, Any], 
        exc_name: Optional[str]
    ) -> bool:
        """
        Verify function raises an exception (optionally of specific type).
        
        Args:
            fn: Function to test
            args: Input arguments
            exc_name: Expected exception class name (None = any exception)
            
        Returns:
            True if function raises expected exception
        """
        try:
            fn(**args)
        except Exception as e:
            # If no specific exception required, any exception is OK
            if exc_name is None:
                return True
            # Otherwise, check exception class name matches
            return e.__class__.__name__ == exc_name
        
        # Function didn't raise - policy violated
        return False

    def _expect_return(
        self, 
        fn: Callable[..., Any], 
        args: Dict[str, Any], 
        value: Any
    ) -> bool:
        """
        Verify function returns specific value.
        
        Args:
            fn: Function to test
            args: Input arguments
            value: Expected return value
            
        Returns:
            True if function returns expected value
        """
        try:
            result = fn(**args)
            return result == value
        except Exception:
            # Function raised exception - policy violated
            return False

    def _expect_same_behavior(
        self, 
        f0: Callable[..., Any], 
        f1: Callable[..., Any], 
        args: Dict[str, Any]
    ) -> bool:
        """
        Verify two functions have identical behavior (return value or exception).
        
        Args:
            f0: Baseline function
            f1: Implementation function
            args: Input arguments
            
        Returns:
            True if both functions behave identically
        """
        try:
            r0 = self._call_catch(f0, args)
            r1 = self._call_catch(f1, args)
            return r0 == r1
        except Exception:
            # Comparison failed - policy violated
            return False

    def _call_catch(
        self, 
        fn: Callable[..., Any], 
        args: Dict[str, Any]
    ) -> tuple:
        """
        Call function and catch both return values and exceptions.
        
        Args:
            fn: Function to call
            args: Input arguments
            
        Returns:
            ("ok", return_value) if successful
            ("exc", exception_class_name) if exception raised
        """
        try:
            result = fn(**args)
            return ("ok", result)
        except Exception as e:
            return ("exc", e.__class__.__name__)
