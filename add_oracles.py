#!/usr/bin/env python3
"""Script to add missing oracle methods to oracle_system.py"""

new_methods = '''
    def _quick_sort_oracle(self, namespace: Dict, requirements: Dict) -> Dict[str, Any]:
        """Oracle tests for quick sort implementations"""
        test_results = []
        
        sort_func = None
        for name, obj in namespace.items():
            if callable(obj) and any(keyword in name.lower() for keyword in ['sort', 'quick']):
                sort_func = obj
                break
        
        if not sort_func:
            return {"passed": False, "error": "No quick_sort function found", "test_results": []}
        
        test_cases = requirements.get("test_cases", [])
        if not test_cases:
            return {"passed": False, "error": "No test cases found", "test_results": []}
        
        passed_tests = 0
        for test_case in test_cases:
            input_arr = test_case.get("input", [[]])[0] if isinstance(test_case.get("input"), list) else []
            expected = test_case.get("expected", [])
            description = test_case.get("description", "")
            
            try:
                input_copy = input_arr.copy() if isinstance(input_arr, list) else []
                result = sort_func(input_copy)
                if result is None:
                    result = input_copy
                passed = (result == expected)
                test_results.append({"input": input_arr, "expected": expected, "actual": result, "passed": passed, "description": description})
                if passed:
                    passed_tests += 1
            except Exception as e:
                test_results.append({"input": input_arr, "expected": expected, "passed": False, "error": str(e), "description": description})
        
        pass_rate = passed_tests / len(test_cases) if test_cases else 0.0
        return {"passed": pass_rate >= requirements.get("required_pass_rate", 0.8), "pass_rate": pass_rate, "passed_tests": passed_tests, "total_tests": len(test_cases), "test_results": test_results}
    
    def _factorial_oracle(self, namespace: Dict, requirements: Dict) -> Dict[str, Any]:
        """Oracle tests for factorial implementations"""
        test_results = []
        
        factorial_func = None
        for name, obj in namespace.items():
            if callable(obj) and 'factorial' in name.lower():
                factorial_func = obj
                break
        
        if not factorial_func:
            return {"passed": False, "error": "No factorial function found", "test_results": []}
        
        test_cases = requirements.get("test_cases", [])
        if not test_cases:
            return {"passed": False, "error": "No test cases found", "test_results": []}
        
        passed_tests = 0
        for test_case in test_cases:
            input_val = test_case.get("input", 0)
            expected = test_case.get("expected", 1)
            description = test_case.get("description", "")
            
            try:
                result = factorial_func(input_val)
                passed = (result == expected)
                test_results.append({"input": input_val, "expected": expected, "actual": result, "passed": passed, "description": description})
                if passed:
                    passed_tests += 1
            except Exception as e:
                test_results.append({"input": input_val, "expected": expected, "passed": False, "error": str(e), "description": description})
        
        pass_rate = passed_tests / len(test_cases) if test_cases else 0.0
        return {"passed": pass_rate >= requirements.get("required_pass_rate", 0.8), "pass_rate": pass_rate, "passed_tests": passed_tests, "total_tests": len(test_cases), "test_results": test_results}
    
    def _is_palindrome_oracle(self, namespace: Dict, requirements: Dict) -> Dict[str, Any]:
        """Oracle tests for palindrome checking implementations"""
        test_results = []
        
        palindrome_func = None
        for name, obj in namespace.items():
            if callable(obj) and 'palindrome' in name.lower():
                palindrome_func = obj
                break
        
        if not palindrome_func:
            return {"passed": False, "error": "No is_palindrome function found", "test_results": []}
        
        test_cases = requirements.get("test_cases", [])
        if not test_cases:
            return {"passed": False, "error": "No test cases found", "test_results": []}
        
        passed_tests = 0
        for test_case in test_cases:
            input_str = test_case.get("input", "")
            expected = test_case.get("expected", False)
            description = test_case.get("description", "")
            
            try:
                result = palindrome_func(input_str)
                passed = (result == expected)
                test_results.append({"input": input_str, "expected": expected, "actual": result, "passed": passed, "description": description})
                if passed:
                    passed_tests += 1
            except Exception as e:
                test_results.append({"input": input_str, "expected": expected, "passed": False, "error": str(e), "description": description})
        
        pass_rate = passed_tests / len(test_cases) if test_cases else 0.0
        return {"passed": pass_rate >= requirements.get("required_pass_rate", 0.8), "pass_rate": pass_rate, "passed_tests": passed_tests, "total_tests": len(test_cases), "test_results": test_results}
    
    def _is_prime_oracle(self, namespace: Dict, requirements: Dict) -> Dict[str, Any]:
        """Oracle tests for prime checking implementations"""
        test_results = []
        
        prime_func = None
        for name, obj in namespace.items():
            if callable(obj) and 'prime' in name.lower():
                prime_func = obj
                break
        
        if not prime_func:
            return {"passed": False, "error": "No is_prime function found", "test_results": []}
        
        test_cases = requirements.get("test_cases", [])
        if not test_cases:
            return {"passed": False, "error": "No test cases found", "test_results": []}
        
        passed_tests = 0
        for test_case in test_cases:
            input_val = test_case.get("input", 2)
            expected = test_case.get("expected", False)
            description = test_case.get("description", "")
            
            try:
                result = prime_func(input_val)
                passed = (result == expected)
                test_results.append({"input": input_val, "expected": expected, "actual": result, "passed": passed, "description": description})
                if passed:
                    passed_tests += 1
            except Exception as e:
                test_results.append({"input": input_val, "expected": expected, "passed": False, "error": str(e), "description": description})
        
        pass_rate = passed_tests / len(test_cases) if test_cases else 0.0
        return {"passed": pass_rate >= requirements.get("required_pass_rate", 0.8), "pass_rate": pass_rate, "passed_tests": passed_tests, "total_tests": len(test_cases), "test_results": test_results}
'''

with open('src/oracle_system.py', 'a') as f:
    f.write(new_methods)

print('Added 4 new oracle methods to oracle_system.py')
