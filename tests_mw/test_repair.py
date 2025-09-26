# tests_mw/test_repair.py
"""
[TODO test_repair.py]
Goal: contract enforcement reduces distance. No code.

1. Wrong function name -> repair renames to exact signature; d decreases or hits 0.
2. Output includes comments -> repair removes; oracle passes.
3. Non-compliant that cannot be fixed within steps -> bounded failure, reason logged.
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.middleware.repair import repair_code, _fix_function_name, _remove_comments, _remove_docstrings
from src.middleware.canon_anchor import fix_canon_if_none, reset_canon
from src.middleware.distance import compute_distance
from src.middleware.contract_enforcer import oracle_check

class TestRepairEffectiveness(unittest.TestCase):
    """Test that repair operations reduce distance to canon"""
    
    def setUp(self):
        """Set up test environment"""
        reset_canon()
        
        # Establish canon
        self.contract = {"id": "test", "enforce_function_name": "fibonacci"}
        self.canon_code = "def fibonacci(n):\n    return n"
        
        canon = fix_canon_if_none(self.canon_code, self.contract, True, "test", "gpt-4", 0.0)
        self.assertIsNotNone(canon)
    
    def tearDown(self):
        """Clean up test environment"""
        reset_canon()
    
    def test_function_name_repair(self):
        """Test that wrong function name gets repaired"""
        # Code with wrong function name
        broken_code = "def fib(n):\n    return n"
        
        # Compute initial distance
        initial_distance = compute_distance(broken_code, self.canon_code)
        self.assertGreater(initial_distance, 0.0)
        
        # Perform repair
        result, record = repair_code(broken_code, self.canon_code, self.contract, "run1", "sample1")
        
        # Distance should decrease or hit zero
        final_distance = record.d_after
        self.assertLessEqual(final_distance, initial_distance)
        
        # Should have performed at least one repair step
        self.assertGreater(record.steps, 0)
        
        # Repaired code should have correct function name
        self.assertIn("def fibonacci(", result.repaired_text)
    
    def test_comment_removal_repair(self):
        """Test that comments are removed during repair"""
        # Code with comments
        commented_code = """# This is a comment
def fibonacci(n):
    # Another comment
    return n  # Inline comment"""
        
        # Perform repair
        result, record = repair_code(commented_code, self.canon_code, self.contract, "run1", "sample1")
        
        # Comments should be removed
        self.assertNotIn("#", result.repaired_text)
        
        # Oracle should pass after repair
        oracle_pass, _ = oracle_check(result.repaired_text, self.contract)
        self.assertTrue(oracle_pass or result.success)
    
    def test_docstring_removal_repair(self):
        """Test that docstrings are removed during repair"""
        # Code with docstring
        docstring_code = '''def fibonacci(n):
    """This is a docstring
    that spans multiple lines"""
    return n'''
        
        # Perform repair
        result, record = repair_code(docstring_code, self.canon_code, self.contract, "run1", "sample1")
        
        # Docstring should be removed
        self.assertNotIn('"""', result.repaired_text)
        self.assertNotIn("'''", result.repaired_text)
    
    def test_print_removal_repair(self):
        """Test that extra print statements are removed"""
        # Code with print statements
        print_code = """def fibonacci(n):
    print("Debug message")
    return n
print("Extra output")"""
        
        # Perform repair
        result, record = repair_code(print_code, self.canon_code, self.contract, "run1", "sample1")
        
        # Print statements should be reduced or removed
        # (Implementation may vary, but should improve oracle compliance)
        oracle_pass, _ = oracle_check(result.repaired_text, self.contract)
        
        # Either oracle passes or repair made progress
        self.assertTrue(oracle_pass or record.d_after < record.d_before)

class TestRepairBounds(unittest.TestCase):
    """Test repair system bounds and failure cases"""
    
    def setUp(self):
        """Set up test environment"""
        reset_canon()
        
        # Establish canon
        self.contract = {"id": "test", "enforce_function_name": "fibonacci"}
        self.canon_code = "def fibonacci(n):\n    return n"
        
        canon = fix_canon_if_none(self.canon_code, self.contract, True, "test", "gpt-4", 0.0)
        self.assertIsNotNone(canon)
    
    def tearDown(self):
        """Clean up test environment"""
        reset_canon()
    
    def test_bounded_repair_failure(self):
        """Test that repair fails gracefully when bounded by max steps"""
        from src.middleware.schema import MAX_REPAIR_STEPS
        
        # Create code that needs extensive repair
        complex_broken_code = """
        # Many comments
        '''Docstring'''
        def wrong_name(n):
            # More comments
            print("debug 1")
            print("debug 2")
            print("debug 3")
            # Even more comments
            return n + 999  # This makes it semantically wrong too
        print("extra output 1")
        print("extra output 2")
        """
        
        # Perform repair
        result, record = repair_code(complex_broken_code, self.canon_code, self.contract, "run1", "sample1")
        
        # Should not exceed maximum steps
        self.assertLessEqual(record.steps, MAX_REPAIR_STEPS)
        
        # Should log reason for failure if not successful
        if not result.success:
            self.assertIn("repair_incomplete", record.reason)
    
    def test_unfixable_code_failure(self):
        """Test repair failure for code that cannot be fixed"""
        # Code with syntax errors or fundamental issues
        broken_code = "this is not valid python code at all!!!"
        
        # Perform repair
        result, record = repair_code(broken_code, self.canon_code, self.contract, "run1", "sample1")
        
        # Should fail gracefully
        self.assertFalse(result.success)
        
        # Should log appropriate reason
        self.assertIsNotNone(record.reason)
        self.assertNotEqual(record.reason, "")
    
    def test_repair_logging_completeness(self):
        """Test that repair operations are logged completely"""
        # Code needing repair
        broken_code = "def fib(n):\n    return n"
        
        # Perform repair
        result, record = repair_code(broken_code, self.canon_code, self.contract, "run1", "sample1")
        
        # All required fields should be populated
        self.assertIsNotNone(record.run_id)
        self.assertIsNotNone(record.sample_id)
        self.assertIsNotNone(record.before_signature)
        self.assertIsNotNone(record.after_signature)
        self.assertIsInstance(record.d_before, float)
        self.assertIsInstance(record.d_after, float)
        self.assertIsInstance(record.steps, int)
        self.assertIsInstance(record.success, bool)
        self.assertIsNotNone(record.reason)
        self.assertIsNotNone(record.timestamp)

class TestRepairSteps(unittest.TestCase):
    """Test individual repair step functions"""
    
    def test_fix_function_name_step(self):
        """Test function name fixing step"""
        contract = {"enforce_function_name": "fibonacci"}
        
        # Test function name correction
        code = "def fib(n):\n    return fib(n-1) + fib(n-2)"
        fixed = _fix_function_name(code, contract)
        
        # Should rename function and recursive calls
        self.assertIn("def fibonacci(", fixed)
        self.assertIn("fibonacci(n-1)", fixed)
        self.assertIn("fibonacci(n-2)", fixed)
    
    def test_remove_comments_step(self):
        """Test comment removal step"""
        code = """# Top comment
def fibonacci(n):  # Inline comment
    # Internal comment
    return n"""
        
        cleaned = _remove_comments(code, {})
        
        # Comments should be removed
        self.assertNotIn("#", cleaned)
        
        # Function structure should remain
        self.assertIn("def fibonacci(n):", cleaned)
        self.assertIn("return n", cleaned)
    
    def test_remove_docstrings_step(self):
        """Test docstring removal step"""
        code = '''"""Module docstring"""
def fibonacci(n):
    """Function docstring
    Multiple lines"""
    return n'''
        
        cleaned = _remove_docstrings(code, {})
        
        # Docstrings should be removed
        self.assertNotIn('"""', cleaned)
        
        # Function should remain
        self.assertIn("def fibonacci(n):", cleaned)
        self.assertIn("return n", cleaned)
    
    def test_repair_step_idempotence(self):
        """Test that repair steps are idempotent"""
        # Clean code
        clean_code = "def fibonacci(n):\n    return n"
        
        # Apply repair steps multiple times
        step1 = _fix_function_name(clean_code, {"enforce_function_name": "fibonacci"})
        step2 = _fix_function_name(step1, {"enforce_function_name": "fibonacci"})
        
        # Should be identical after first application
        self.assertEqual(step1, step2)
        
        # Same for comment removal
        no_comments1 = _remove_comments(clean_code, {})
        no_comments2 = _remove_comments(no_comments1, {})
        
        self.assertEqual(no_comments1, no_comments2)

if __name__ == '__main__':
    unittest.main()
