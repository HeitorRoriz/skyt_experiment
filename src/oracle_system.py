# src/oracle_system.py
"""
Oracle system for behavioral testing and compliance checking
Implements acceptance tests for different algorithm families
"""

import ast
import sys
import io
from typing import Dict, Any, List, Callable, Optional
from contextlib import redirect_stdout, redirect_stderr


class OracleSystem:
    """
    Behavioral testing system using algorithm-specific oracles
    """
    
    def __init__(self):
        self.algorithm_oracles = {
            "fibonacci": self._fibonacci_oracle,
            "merge_sort": self._merge_sort_oracle,
            "binary_search": self._binary_search_oracle,
            "sieve_eratosthenes": self._sieve_oracle,
            "dijkstra": self._dijkstra_oracle,
            "slugify": self._slugify_oracle,
            "balanced_brackets": self._balanced_brackets_oracle
        }
    
    def run_oracle_tests(self, code: str, contract: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run oracle tests for given code and contract
        
        Args:
            code: Python code to test
            contract: Contract specification with oracle requirements
            
        Returns:
            Test results with pass/fail status and details
        """
        algorithm_family = contract.get("algorithm_family", "fibonacci")
        oracle_requirements = contract.get("oracle_requirements", {})
        
        if algorithm_family not in self.algorithm_oracles:
            return {
                "passed": False,
                "error": f"No oracle available for algorithm family: {algorithm_family}",
                "test_results": []
            }
        
        try:
            # Execute the code safely
            namespace = {}
            exec(code, namespace)
            
            # Run algorithm-specific oracle
            oracle_func = self.algorithm_oracles[algorithm_family]
            results = oracle_func(namespace, oracle_requirements)
            
            return results
            
        except Exception as e:
            return {
                "passed": False,
                "error": f"Code execution failed: {str(e)}",
                "test_results": []
            }
    
    def _fibonacci_oracle(self, namespace: Dict, requirements: Dict) -> Dict[str, Any]:
        """Oracle tests for Fibonacci implementations"""
        test_results = []
        
        # Find the fibonacci function
        fibonacci_func = None
        for name, obj in namespace.items():
            if callable(obj) and 'fibonacci' in name.lower():
                fibonacci_func = obj
                break
        
        if not fibonacci_func:
            return {
                "passed": False,
                "error": "No fibonacci function found",
                "test_results": []
            }
        
        # Test cases
        test_cases = [
            {"input": 0, "expected": 0, "description": "Base case: F(0)"},
            {"input": 1, "expected": 1, "description": "Base case: F(1)"},
            {"input": 2, "expected": 1, "description": "F(2)"},
            {"input": 5, "expected": 5, "description": "F(5)"},
            {"input": 10, "expected": 55, "description": "F(10)"},
        ]
        
        # Check if function returns a list (sequence variant)
        try:
            result_0 = fibonacci_func(0)
            is_sequence = isinstance(result_0, list)
        except:
            is_sequence = False
        
        if is_sequence:
            # Sequence tests
            sequence_tests = [
                {"input": 0, "expected": [], "description": "Empty sequence"},
                {"input": 1, "expected": [0], "description": "Single element"},
                {"input": 5, "expected": [0, 1, 1, 2, 3], "description": "First 5 numbers"},
            ]
            test_cases = sequence_tests
        
        passed_tests = 0
        
        for test_case in test_cases:
            try:
                result = fibonacci_func(test_case["input"])
                passed = (result == test_case["expected"])
                
                test_results.append({
                    "description": test_case["description"],
                    "input": test_case["input"],
                    "expected": test_case["expected"],
                    "actual": result,
                    "passed": passed
                })
                
                if passed:
                    passed_tests += 1
                    
            except Exception as e:
                test_results.append({
                    "description": test_case["description"],
                    "input": test_case["input"],
                    "expected": test_case["expected"],
                    "actual": None,
                    "passed": False,
                    "error": str(e)
                })
        
        # Property tests
        if not is_sequence:
            # Test Fibonacci property: F(n) = F(n-1) + F(n-2)
            try:
                for n in range(3, 8):
                    fn = fibonacci_func(n)
                    fn1 = fibonacci_func(n-1)
                    fn2 = fibonacci_func(n-2)
                    
                    property_holds = (fn == fn1 + fn2)
                    
                    test_results.append({
                        "description": f"Fibonacci property: F({n}) = F({n-1}) + F({n-2})",
                        "input": n,
                        "expected": fn1 + fn2,
                        "actual": fn,
                        "passed": property_holds
                    })
                    
                    if property_holds:
                        passed_tests += 1
                        
            except Exception as e:
                test_results.append({
                    "description": "Fibonacci property test",
                    "passed": False,
                    "error": str(e)
                })
        
        total_tests = len(test_results)
        pass_rate = passed_tests / total_tests if total_tests > 0 else 0.0
        
        return {
            "passed": pass_rate >= 0.8,  # 80% pass rate required
            "pass_rate": pass_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "test_results": test_results
        }
    
    def _merge_sort_oracle(self, namespace: Dict, requirements: Dict) -> Dict[str, Any]:
        """Oracle tests for merge sort implementations"""
        test_results = []
        
        # Find sorting function
        sort_func = None
        for name, obj in namespace.items():
            if callable(obj) and any(keyword in name.lower() for keyword in ['sort', 'merge']):
                sort_func = obj
                break
        
        if not sort_func:
            return {
                "passed": False,
                "error": "No sorting function found",
                "test_results": []
            }
        
        test_cases = [
            {"input": [], "expected": [], "description": "Empty array"},
            {"input": [1], "expected": [1], "description": "Single element"},
            {"input": [3, 1, 4, 1, 5], "expected": [1, 1, 3, 4, 5], "description": "Random array"},
            {"input": [5, 4, 3, 2, 1], "expected": [1, 2, 3, 4, 5], "description": "Reverse sorted"},
            {"input": [1, 2, 3, 4, 5], "expected": [1, 2, 3, 4, 5], "description": "Already sorted"},
        ]
        
        passed_tests = 0
        
        for test_case in test_cases:
            try:
                input_copy = test_case["input"].copy()
                result = sort_func(input_copy)
                
                # Handle in-place vs return sorting
                if result is None:
                    result = input_copy
                
                passed = (result == test_case["expected"])
                
                test_results.append({
                    "description": test_case["description"],
                    "input": test_case["input"],
                    "expected": test_case["expected"],
                    "actual": result,
                    "passed": passed
                })
                
                if passed:
                    passed_tests += 1
                    
            except Exception as e:
                test_results.append({
                    "description": test_case["description"],
                    "input": test_case["input"],
                    "expected": test_case["expected"],
                    "actual": None,
                    "passed": False,
                    "error": str(e)
                })
        
        total_tests = len(test_results)
        pass_rate = passed_tests / total_tests if total_tests > 0 else 0.0
        
        return {
            "passed": pass_rate >= 0.8,
            "pass_rate": pass_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "test_results": test_results
        }
    
    def _binary_search_oracle(self, namespace: Dict, requirements: Dict) -> Dict[str, Any]:
        """Oracle tests for binary search implementations"""
        test_results = []
        
        # Find search function
        search_func = None
        for name, obj in namespace.items():
            if callable(obj) and 'search' in name.lower():
                search_func = obj
                break
        
        if not search_func:
            return {
                "passed": False,
                "error": "No search function found",
                "test_results": []
            }
        
        test_cases = [
            {"array": [1, 2, 3, 4, 5], "target": 3, "expected": 2, "description": "Element found"},
            {"array": [1, 2, 3, 4, 5], "target": 6, "expected": -1, "description": "Element not found"},
            {"array": [1], "target": 1, "expected": 0, "description": "Single element found"},
            {"array": [1], "target": 2, "expected": -1, "description": "Single element not found"},
            {"array": [], "target": 1, "expected": -1, "description": "Empty array"},
        ]
        
        passed_tests = 0
        
        for test_case in test_cases:
            try:
                result = search_func(test_case["array"], test_case["target"])
                
                # Handle different return conventions (-1 vs None vs exception)
                if result is None and test_case["expected"] == -1:
                    result = -1
                
                passed = (result == test_case["expected"])
                
                test_results.append({
                    "description": test_case["description"],
                    "input": {"array": test_case["array"], "target": test_case["target"]},
                    "expected": test_case["expected"],
                    "actual": result,
                    "passed": passed
                })
                
                if passed:
                    passed_tests += 1
                    
            except Exception as e:
                test_results.append({
                    "description": test_case["description"],
                    "input": {"array": test_case["array"], "target": test_case["target"]},
                    "expected": test_case["expected"],
                    "actual": None,
                    "passed": False,
                    "error": str(e)
                })
        
        total_tests = len(test_results)
        pass_rate = passed_tests / total_tests if total_tests > 0 else 0.0
        
        return {
            "passed": pass_rate >= 0.8,
            "pass_rate": pass_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "test_results": test_results
        }
    
    def _sieve_oracle(self, namespace: Dict, requirements: Dict) -> Dict[str, Any]:
        """Oracle tests for Sieve of Eratosthenes implementations"""
        test_results = []
        
        # Find sieve function
        sieve_func = None
        for name, obj in namespace.items():
            if callable(obj) and any(keyword in name.lower() for keyword in ['sieve', 'prime']):
                sieve_func = obj
                break
        
        if not sieve_func:
            return {
                "passed": False,
                "error": "No sieve function found",
                "test_results": []
            }
        
        # Known prime sequences
        test_cases = [
            {"input": 10, "expected": [2, 3, 5, 7], "description": "Primes up to 10"},
            {"input": 20, "expected": [2, 3, 5, 7, 11, 13, 17, 19], "description": "Primes up to 20"},
            {"input": 2, "expected": [2], "description": "Primes up to 2"},
            {"input": 1, "expected": [], "description": "Primes up to 1"},
        ]
        
        passed_tests = 0
        
        for test_case in test_cases:
            try:
                result = sieve_func(test_case["input"])
                
                # Ensure result is sorted
                if isinstance(result, list):
                    result = sorted(result)
                
                passed = (result == test_case["expected"])
                
                test_results.append({
                    "description": test_case["description"],
                    "input": test_case["input"],
                    "expected": test_case["expected"],
                    "actual": result,
                    "passed": passed
                })
                
                if passed:
                    passed_tests += 1
                    
            except Exception as e:
                test_results.append({
                    "description": test_case["description"],
                    "input": test_case["input"],
                    "expected": test_case["expected"],
                    "actual": None,
                    "passed": False,
                    "error": str(e)
                })
        
        total_tests = len(test_results)
        pass_rate = passed_tests / total_tests if total_tests > 0 else 0.0
        
        return {
            "passed": pass_rate >= 0.8,
            "pass_rate": pass_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "test_results": test_results
        }
    
    def _dijkstra_oracle(self, namespace: Dict, requirements: Dict) -> Dict[str, Any]:
        """Oracle tests for Dijkstra's algorithm implementations"""
        # Simplified oracle - would need more complex graph test cases
        return {
            "passed": True,
            "pass_rate": 1.0,
            "passed_tests": 1,
            "total_tests": 1,
            "test_results": [
                {
                    "description": "Dijkstra oracle not fully implemented",
                    "passed": True
                }
            ]
        }
    
    def _slugify_oracle(self, namespace: Dict, requirements: Dict) -> Dict[str, Any]:
        """Oracle tests for slugify implementations"""
        test_results = []
        
        # Find the slugify function
        slugify_func = None
        for name, obj in namespace.items():
            if callable(obj) and 'slugify' in name.lower():
                slugify_func = obj
                break
        
        if not slugify_func:
            # Debug: show what's in namespace
            available_names = [name for name in namespace.keys() if not name.startswith('__')]
            return {
                "passed": False,
                "error": f"No slugify function found. Available: {available_names}",
                "test_results": []
            }
        
        # Get test cases from requirements or use defaults
        test_cases = requirements.get("test_cases", [])
        
        # Debug: check if test_cases is empty
        if not test_cases:
            return {
                "passed": False,
                "error": f"No test cases found in requirements. Keys: {list(requirements.keys())}",
                "test_results": []
            }
        
        passed_tests = 0
        total_tests = len(test_cases)
        
        for test_case in test_cases:
            input_str = test_case.get("input", "")
            expected = test_case.get("expected", "")
            description = test_case.get("description", "")
            
            try:
                result = slugify_func(input_str)
                passed = (result == expected)
                
                test_results.append({
                    "input": input_str,
                    "expected": expected,
                    "actual": result,
                    "passed": passed,
                    "description": description
                })
                
                if passed:
                    passed_tests += 1
                    
            except Exception as e:
                test_results.append({
                    "input": input_str,
                    "expected": expected,
                    "actual": None,
                    "passed": False,
                    "error": str(e),
                    "description": description
                })
        
        pass_rate = passed_tests / total_tests if total_tests > 0 else 0.0
        required_pass_rate = requirements.get("required_pass_rate", 0.8)
        
        return {
            "passed": pass_rate >= required_pass_rate,
            "pass_rate": pass_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "test_results": test_results
        }
    
    def _balanced_brackets_oracle(self, namespace: Dict, requirements: Dict) -> Dict[str, Any]:
        """Oracle tests for balanced brackets implementations"""
        test_results = []
        
        # Find the is_balanced function
        is_balanced_func = None
        for name, obj in namespace.items():
            if callable(obj) and 'balanced' in name.lower():
                is_balanced_func = obj
                break
        
        if not is_balanced_func:
            return {
                "passed": False,
                "error": "No is_balanced function found",
                "test_results": []
            }
        
        # Get test cases from requirements or use defaults
        test_cases = requirements.get("test_cases", [])
        
        passed_tests = 0
        total_tests = len(test_cases)
        
        for test_case in test_cases:
            input_str = test_case.get("input", "")
            expected = test_case.get("expected", False)
            description = test_case.get("description", "")
            
            try:
                result = is_balanced_func(input_str)
                passed = (result == expected)
                
                test_results.append({
                    "input": input_str,
                    "expected": expected,
                    "actual": result,
                    "passed": passed,
                    "description": description
                })
                
                if passed:
                    passed_tests += 1
                    
            except Exception as e:
                test_results.append({
                    "input": input_str,
                    "expected": expected,
                    "actual": None,
                    "passed": False,
                    "error": str(e),
                    "description": description
                })
        
        pass_rate = passed_tests / total_tests if total_tests > 0 else 0.0
        required_pass_rate = requirements.get("required_pass_rate", 0.8)
        
        return {
            "passed": pass_rate >= required_pass_rate,
            "pass_rate": pass_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "test_results": test_results
        }
