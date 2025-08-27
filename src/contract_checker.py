# src/contract_checker.py
"""
Contract checker that combines:
- Structural lint (determinism checking)
- Canonicalization
- Oracle execution (plug-in model)
- Includes anchor oracle for fibonacci20
- Defaults to pass-through when oracle is null
"""

import ast
import sys
from io import StringIO
from typing import Optional, List, Any, Callable
from dataclasses import dataclass

from .determinism_lint import lint_code, DeterminismViolation
from .canonicalizer import canonicalize_with_signature
from .config import FIBONACCI_20_EXPECTED


@dataclass
class ContractResult:
    """Result of contract checking"""
    passed: bool
    canonical_code: Optional[str]
    canonical_signature: Optional[str]
    determinism_violations: List[DeterminismViolation]
    structural_ok: bool
    canonicalization_ok: bool
    oracle_result: Optional[bool]
    oracle_output: Optional[Any]
    contract_pass: bool
    error_message: Optional[str]


def fibonacci_oracle(code: str) -> tuple[bool, Optional[Any]]:
    """
    Anchor oracle for fibonacci20 - executes code and checks if it produces
    the expected first 20 Fibonacci numbers
    
    Returns:
        (success, output) where success indicates if output matches expected
    """
    try:
        # Create a safe execution environment with restricted builtins
        safe_builtins = {
            '__builtins__': {
                'len': len, 'range': range, 'list': list, 'int': int,
                'float': float, 'str': str, 'bool': bool, 'tuple': tuple,
                'dict': dict, 'set': set, 'abs': abs, 'max': max, 'min': min,
                'sum': sum, 'enumerate': enumerate, 'zip': zip
            }
        }
        namespace = safe_builtins.copy()
        
        # Execute the code
        exec(code, namespace)
        
        # Try to find and call the fibonacci function
        if 'fibonacci' not in namespace:
            return False, "No fibonacci function found"
        
        fibonacci_func = namespace['fibonacci']
        
        # Call the function (assume it takes no parameters for fibonacci20)
        try:
            result = fibonacci_func()
        except TypeError:
            # Maybe it takes a parameter (number of terms)
            try:
                result = fibonacci_func(20)
            except:
                return False, "Function call failed"
        except:
            return False, "Function execution failed"
        
        # Check if result matches expected fibonacci sequence
        if isinstance(result, list) and result == FIBONACCI_20_EXPECTED:
            return True, result
        else:
            return False, result
            
    except Exception as e:
        return False, f"Execution error: {str(e)}"


class ContractChecker:
    """Main contract checker class"""
    
    def __init__(self, oracle: Optional[Callable[[str], tuple[bool, Optional[Any]]]] = None):
        """
        Initialize contract checker
        
        Args:
            oracle: Optional oracle function for semantic checking
                   If None, defaults to pass-through (always passes)
        """
        self.oracle = oracle
    
    def check_contract(self, code: str, target_function_name: str = "fibonacci") -> ContractResult:
        """
        Check code against contract requirements
        
        Args:
            code: Python source code to check
            target_function_name: Expected function name
            
        Returns:
            ContractResult with all check results
        """
        # Step 1: Check determinism on raw code
        violations = lint_code(code)
        structural_ok = len(violations) == 0
        
        # Step 2: Attempt canonicalization (always try, even with violations)
        canonical_code, canonical_signature = canonicalize_with_signature(code, target_function_name)
        canonicalization_ok = canonical_code is not None
        
        # Step 3: Run oracle only if both structural and canonicalization passed
        oracle_result = None
        oracle_output = None
        
        if structural_ok and canonicalization_ok:
            if self.oracle is not None:
                oracle_result, oracle_output = self.oracle(canonical_code)
            else:
                # Pass-through when oracle is null
                oracle_result = True
                oracle_output = "Pass-through (no oracle)"
        
        # Final contract decision: structural_ok AND canonicalization_ok AND (oracle_pass OR oracle_none)
        contract_pass = (
            structural_ok and 
            canonicalization_ok and 
            (oracle_result is True or (oracle_result is None and self.oracle is None))
        )
        
        # Generate error message if failed
        error_message = None
        if not contract_pass:
            error_parts = []
            if not structural_ok:
                error_parts.append(f"{len(violations)} determinism violations")
            if not canonicalization_ok:
                error_parts.append("canonicalization failed")
            if oracle_result is False:
                error_parts.append(f"oracle failed: {oracle_output}")
            error_message = "; ".join(error_parts)
        
        return ContractResult(
            passed=contract_pass,
            canonical_code=canonical_code,
            canonical_signature=canonical_signature,
            determinism_violations=violations,
            structural_ok=structural_ok,
            canonicalization_ok=canonicalization_ok,
            oracle_result=oracle_result,
            oracle_output=oracle_output,
            contract_pass=contract_pass,
            error_message=error_message
        )


def create_fibonacci_checker() -> ContractChecker:
    """Create a contract checker with fibonacci oracle"""
    return ContractChecker(oracle=fibonacci_oracle)


def create_passthrough_checker() -> ContractChecker:
    """Create a contract checker with no oracle (pass-through)"""
    return ContractChecker(oracle=None)


def check_fibonacci_contract(code: str) -> ContractResult:
    """
    Convenience function to check code against fibonacci contract
    
    Args:
        code: Python source code to check
        
    Returns:
        ContractResult with all check results
    """
    checker = create_fibonacci_checker()
    return checker.check_contract(code, "fibonacci")
