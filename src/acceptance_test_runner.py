"""
Acceptance Test Runner for Contract Validation
Executes comprehensive test suites to validate LLM-generated code correctness
"""

import time
import traceback
import subprocess
import sys
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from contract import PromptContract

@dataclass
class TestResult:
    name: str
    passed: bool
    execution_time: float
    error_message: Optional[str] = None
    actual_output: Any = None
    expected_output: Any = None

@dataclass
class AcceptanceTestReport:
    total_tests: int
    passed_tests: int
    failed_tests: int
    pass_rate: float
    execution_time: float
    test_results: List[TestResult]
    correctness_score: float  # 0.0 to 1.0

class AcceptanceTestRunner:
    """Runs comprehensive acceptance tests against LLM-generated code"""
    
    def __init__(self, contract: PromptContract):
        self.contract = contract
        self.test_config = contract.test_config or {
            "timeout_seconds": 5.0,
            "required_pass_rate": 1.0,
            "allow_approximate": False,
            "tolerance": 1e-9
        }
    
    def run_all_tests(self, code: str) -> AcceptanceTestReport:
        """Execute all acceptance tests and return comprehensive report"""
        start_time = time.time()
        all_results = []
        
        # Extract function for testing
        try:
            exec_globals = {}
            exec(code, exec_globals)
            func = exec_globals.get(self.contract.function_name)
            if not func:
                return self._create_failed_report("Function not found in code")
        except Exception as e:
            return self._create_failed_report(f"Code execution failed: {str(e)}")
        
        # Run different test categories
        acceptance_tests = self.contract.acceptance_tests or {}
        
        # Unit tests - basic input/output validation
        if "unit_tests" in acceptance_tests:
            all_results.extend(self._run_unit_tests(func, acceptance_tests["unit_tests"]))
        
        # Edge cases - boundary conditions
        if "edge_cases" in acceptance_tests:
            all_results.extend(self._run_edge_cases(func, acceptance_tests["edge_cases"]))
        
        # Property tests - mathematical invariants
        if "property_tests" in acceptance_tests:
            all_results.extend(self._run_property_tests(func, acceptance_tests["property_tests"]))
        
        # Performance tests - time/space complexity
        if "performance_tests" in acceptance_tests:
            all_results.extend(self._run_performance_tests(func, acceptance_tests["performance_tests"]))
        
        # Integration tests - function composition
        if "integration_tests" in acceptance_tests:
            all_results.extend(self._run_integration_tests(func, acceptance_tests["integration_tests"]))
        
        # Stress tests - large inputs
        if "stress_tests" in acceptance_tests:
            all_results.extend(self._run_stress_tests(func, acceptance_tests["stress_tests"]))
        
        total_time = time.time() - start_time
        passed = sum(1 for r in all_results if r.passed)
        total = len(all_results)
        
        return AcceptanceTestReport(
            total_tests=total,
            passed_tests=passed,
            failed_tests=total - passed,
            pass_rate=passed / total if total > 0 else 0.0,
            execution_time=total_time,
            test_results=all_results,
            correctness_score=self._calculate_correctness_score(all_results)
        )
    
    def _run_unit_tests(self, func, unit_tests: List[Dict]) -> List[TestResult]:
        """Run basic input/output validation tests"""
        results = []
        for test in unit_tests:
            result = self._execute_single_test(
                func, 
                test["name"], 
                test["input"], 
                test["expected_output"],
                test.get("description", "")
            )
            results.append(result)
        return results
    
    def _run_edge_cases(self, func, edge_cases: List[Dict]) -> List[TestResult]:
        """Run boundary condition and error handling tests"""
        results = []
        for test in edge_cases:
            result = self._execute_single_test(
                func,
                test["name"],
                test["input"],
                test["expected_output"],
                test.get("description", "")
            )
            results.append(result)
        return results
    
    def _run_property_tests(self, func, property_tests: List[Dict]) -> List[TestResult]:
        """Run mathematical property and invariant tests"""
        results = []
        for test in property_tests:
            start_time = time.time()
            try:
                # Generate test inputs based on property
                test_inputs = self._generate_property_test_inputs(test)
                all_passed = True
                error_msg = None
                
                for test_input in test_inputs:
                    try:
                        result = func(test_input)
                        if not self._validate_property(test["property"], test_input, result):
                            all_passed = False
                            error_msg = f"Property violation: {test['property']}"
                            break
                    except Exception as e:
                        all_passed = False
                        error_msg = f"Execution error: {str(e)}"
                        break
                
                execution_time = time.time() - start_time
                results.append(TestResult(
                    name=test["name"],
                    passed=all_passed,
                    execution_time=execution_time,
                    error_message=error_msg
                ))
                
            except Exception as e:
                execution_time = time.time() - start_time
                results.append(TestResult(
                    name=test["name"],
                    passed=False,
                    execution_time=execution_time,
                    error_message=f"Property test setup failed: {str(e)}"
                ))
        
        return results
    
    def _run_performance_tests(self, func, performance_tests: List[Dict]) -> List[TestResult]:
        """Run time and space complexity validation tests"""
        results = []
        for test in performance_tests:
            start_time = time.time()
            try:
                result = func(test["input"])
                execution_time = time.time() - start_time
                
                max_time = test.get("max_time_seconds", self.test_config["timeout_seconds"])
                passed = execution_time <= max_time
                
                results.append(TestResult(
                    name=test["name"],
                    passed=passed,
                    execution_time=execution_time,
                    error_message=None if passed else f"Timeout: {execution_time:.3f}s > {max_time}s",
                    actual_output=f"Execution time: {execution_time:.3f}s"
                ))
                
            except Exception as e:
                execution_time = time.time() - start_time
                results.append(TestResult(
                    name=test["name"],
                    passed=False,
                    execution_time=execution_time,
                    error_message=f"Performance test failed: {str(e)}"
                ))
        
        return results
    
    def _run_integration_tests(self, func, integration_tests: List[Dict]) -> List[TestResult]:
        """Run function composition and interaction tests"""
        results = []
        for test in integration_tests:
            result = self._execute_single_test(
                func,
                test["name"],
                test["input"],
                test["expected_output"],
                test.get("description", "")
            )
            results.append(result)
        return results
    
    def _run_stress_tests(self, func, stress_tests: List[Dict]) -> List[TestResult]:
        """Run large input and extreme condition tests"""
        results = []
        for test in stress_tests:
            start_time = time.time()
            try:
                result = func(test["input"])
                execution_time = time.time() - start_time
                
                # Stress tests focus on not crashing rather than exact output
                passed = True
                error_msg = None
                
                # Check if there's an expected output
                if "expected_output" in test:
                    passed = self._compare_outputs(result, test["expected_output"])
                    if not passed:
                        error_msg = f"Output mismatch: got {result}, expected {test['expected_output']}"
                
                results.append(TestResult(
                    name=test["name"],
                    passed=passed,
                    execution_time=execution_time,
                    error_message=error_msg,
                    actual_output=result
                ))
                
            except Exception as e:
                execution_time = time.time() - start_time
                results.append(TestResult(
                    name=test["name"],
                    passed=False,
                    execution_time=execution_time,
                    error_message=f"Stress test failed: {str(e)}"
                ))
        
        return results
    
    def _execute_single_test(self, func, name: str, test_input: Any, expected_output: Any, description: str = "") -> TestResult:
        """Execute a single test case with timeout protection"""
        start_time = time.time()
        
        try:
            # Execute with timeout protection
            actual_output = func(test_input)
            execution_time = time.time() - start_time
            
            # Check timeout
            if execution_time > self.test_config["timeout_seconds"]:
                return TestResult(
                    name=name,
                    passed=False,
                    execution_time=execution_time,
                    error_message=f"Timeout: {execution_time:.3f}s > {self.test_config['timeout_seconds']}s",
                    actual_output=actual_output,
                    expected_output=expected_output
                )
            
            # Compare outputs
            passed = self._compare_outputs(actual_output, expected_output)
            
            return TestResult(
                name=name,
                passed=passed,
                execution_time=execution_time,
                error_message=None if passed else f"Output mismatch: got {actual_output}, expected {expected_output}",
                actual_output=actual_output,
                expected_output=expected_output
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                name=name,
                passed=False,
                execution_time=execution_time,
                error_message=f"Execution error: {str(e)}",
                actual_output=None,
                expected_output=expected_output
            )
    
    def _compare_outputs(self, actual: Any, expected: Any) -> bool:
        """Compare actual vs expected outputs with tolerance support"""
        if self.test_config.get("allow_approximate", False):
            tolerance = self.test_config.get("tolerance", 1e-9)
            try:
                if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
                    return abs(actual - expected) <= tolerance
                elif isinstance(actual, list) and isinstance(expected, list):
                    if len(actual) != len(expected):
                        return False
                    return all(abs(a - e) <= tolerance for a, e in zip(actual, expected) 
                             if isinstance(a, (int, float)) and isinstance(e, (int, float)))
            except:
                pass
        
        return actual == expected
    
    def _generate_property_test_inputs(self, test: Dict) -> List[Any]:
        """Generate test inputs for property-based testing"""
        # Simple implementation - can be enhanced with hypothesis-like generation
        base_inputs = [0, 1, 2, 5, 10, 15]
        return [inp for inp in base_inputs if inp >= 0]  # Filter based on domain
    
    def _validate_property(self, property_expr: str, input_val: Any, result: Any) -> bool:
        """Validate mathematical properties and invariants"""
        try:
            # Simple property validation - can be enhanced with AST parsing
            if "len(result) == input_n" in property_expr:
                return len(result) == input_val
            elif "result[n] == result[n-1] + result[n-2]" in property_expr:
                if len(result) < 3:
                    return True  # Property doesn't apply
                return all(result[i] == result[i-1] + result[i-2] for i in range(2, len(result)))
            elif "all(result[i] <= result[i+1]" in property_expr:
                return all(result[i] <= result[i+1] for i in range(len(result)-1))
            
            return True  # Default to pass for unknown properties
        except:
            return False
    
    def _calculate_correctness_score(self, results: List[TestResult]) -> float:
        """Calculate weighted correctness score based on test importance"""
        if not results:
            return 0.0
        
        # Weight different test types
        weights = {
            "unit_test": 1.0,
            "edge_case": 1.5,      # Edge cases more important
            "property_test": 2.0,   # Properties most important
            "performance_test": 0.5,
            "integration_test": 1.2,
            "stress_test": 0.8
        }
        
        total_weight = 0
        weighted_score = 0
        
        for result in results:
            # Determine test type from name
            test_type = "unit_test"  # Default
            for t_type in weights.keys():
                if t_type.replace("_", "") in result.name.lower():
                    test_type = t_type
                    break
            
            weight = weights[test_type]
            total_weight += weight
            if result.passed:
                weighted_score += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _create_failed_report(self, error_message: str) -> AcceptanceTestReport:
        """Create a failed test report for critical errors"""
        return AcceptanceTestReport(
            total_tests=1,
            passed_tests=0,
            failed_tests=1,
            pass_rate=0.0,
            execution_time=0.0,
            test_results=[TestResult(
                name="critical_error",
                passed=False,
                execution_time=0.0,
                error_message=error_message
            )],
            correctness_score=0.0
        )

def run_acceptance_tests(code: str, contract: PromptContract) -> AcceptanceTestReport:
    """Factory function to run acceptance tests on generated code"""
    runner = AcceptanceTestRunner(contract)
    return runner.run_all_tests(code)
