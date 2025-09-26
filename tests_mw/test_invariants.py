# tests_mw/test_invariants.py
"""
[TODO test_invariants.py]
Goal: enforce single canon, idempotence, monotonic repair. No code.

1. Fix canon once, attempt to fix again with a different signature -> expect invariant failure.
2. d=0 at entry -> repair does nothing, logs zero steps.
3. Simulate repair steps where a later step would increase d -> expect rollback or failure.
"""

import unittest
import tempfile
import os
import shutil
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.middleware.canon_anchor import (
    fix_canon_if_none, get_canon, assert_canon_immutable, 
    CanonImmutabilityError, reset_canon
)
from src.middleware.repair import repair_code
from src.middleware.distance import compute_signature, compute_distance

class TestCanonInvariants(unittest.TestCase):
    """Test canon immutability invariants"""
    
    def setUp(self):
        """Set up test environment"""
        # Reset canon for each test
        reset_canon()
        
        # Create temporary directory for test outputs
        self.test_dir = tempfile.mkdtemp()
        self.original_canon_path = "outputs/canon/canon.json"
        
    def tearDown(self):
        """Clean up test environment"""
        reset_canon()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_single_canon_establishment(self):
        """Test that canon can only be established once"""
        # First canon establishment should succeed
        contract = {"id": "test", "enforce_function_name": "fibonacci"}
        code1 = "def fibonacci(n):\n    return n"
        
        canon1 = fix_canon_if_none(code1, contract, True, "test", "gpt-4", 0.0)
        self.assertIsNotNone(canon1)
        self.assertEqual(canon1.prompt_id, "test")
        
        # Second attempt with different code should return None
        code2 = "def fibonacci(n):\n    return n + 1"
        canon2 = fix_canon_if_none(code2, contract, True, "test", "gpt-4", 0.0)
        self.assertIsNone(canon2)
        
        # Canon should remain the same
        current_canon = get_canon()
        self.assertEqual(current_canon.canon_signature, canon1.canon_signature)
    
    def test_canon_immutability_assertion(self):
        """Test that canon immutability is enforced"""
        # Establish canon
        contract = {"id": "test", "enforce_function_name": "fibonacci"}
        code1 = "def fibonacci(n):\n    return n"
        
        canon = fix_canon_if_none(code1, contract, True, "test", "gpt-4", 0.0)
        self.assertIsNotNone(canon)
        
        # Same signature should pass
        sig1 = compute_signature(code1)
        assert_canon_immutable(sig1)  # Should not raise
        
        # Different signature should raise
        code2 = "def fibonacci(n):\n    return n + 1"
        sig2 = compute_signature(code2)
        
        with self.assertRaises(CanonImmutabilityError):
            assert_canon_immutable(sig2)
    
    def test_oracle_requirement_for_canon(self):
        """Test that canon is only established when oracle passes"""
        contract = {"id": "test", "enforce_function_name": "fibonacci"}
        code = "def fibonacci(n):\n    return n"
        
        # Oracle fails - no canon should be established
        canon = fix_canon_if_none(code, contract, False, "test", "gpt-4", 0.0)
        self.assertIsNone(canon)
        
        # Verify no canon exists
        current_canon = get_canon()
        self.assertIsNone(current_canon)

class TestRepairInvariants(unittest.TestCase):
    """Test repair system invariants"""
    
    def setUp(self):
        """Set up test environment"""
        reset_canon()
    
    def tearDown(self):
        """Clean up test environment"""
        reset_canon()
    
    def test_idempotence_zero_distance(self):
        """Test that repair does nothing when d=0 at entry"""
        # Set up canon
        contract = {"id": "test", "enforce_function_name": "fibonacci"}
        canon_code = "def fibonacci(n):\n    return n"
        
        # Establish canon
        fix_canon_if_none(canon_code, contract, True, "test", "gpt-4", 0.0)
        
        # Repair identical code (d=0)
        result, record = repair_code(canon_code, canon_code, contract, "run1", "sample1")
        
        # Should succeed with zero steps
        self.assertTrue(result.success)
        self.assertEqual(result.steps, 0)
        self.assertEqual(record.steps, 0)
        self.assertEqual(record.reason, "no_repair_needed")
        self.assertEqual(record.d_before, 0.0)
        self.assertEqual(record.d_after, 0.0)
    
    @patch('src.middleware.repair._fix_function_name')
    def test_monotonic_repair_constraint(self, mock_fix_name):
        """Test that repair stops if distance increases"""
        # Set up canon
        contract = {"id": "test", "enforce_function_name": "fibonacci"}
        canon_code = "def fibonacci(n):\n    return n"
        
        # Establish canon
        fix_canon_if_none(canon_code, contract, True, "test", "gpt-4", 0.0)
        
        # Mock repair step that increases distance
        def bad_repair_step(code, contract):
            # Return code that's further from canon
            return "def fibonacci(n):\n    return n + 999"
        
        mock_fix_name.side_effect = bad_repair_step
        
        # Attempt repair on code with wrong function name
        broken_code = "def fib(n):\n    return n"
        result, record = repair_code(broken_code, canon_code, contract, "run1", "sample1")
        
        # Should stop after detecting distance increase
        self.assertFalse(result.success)
        # Steps should be limited due to monotonicity violation
        self.assertLessEqual(result.steps, 1)
    
    def test_bounded_repair_steps(self):
        """Test that repair is bounded by MAX_REPAIR_STEPS"""
        from src.middleware.schema import MAX_REPAIR_STEPS
        
        # Set up canon
        contract = {"id": "test", "enforce_function_name": "fibonacci"}
        canon_code = "def fibonacci(n):\n    return n"
        
        # Establish canon
        fix_canon_if_none(canon_code, contract, True, "test", "gpt-4", 0.0)
        
        # Create code that needs many repairs
        broken_code = """
        # This is a comment
        '''This is a docstring'''
        def wrong_name(n):
            print("debug")
            return n
        print("extra output")
        """
        
        result, record = repair_code(broken_code, canon_code, contract, "run1", "sample1")
        
        # Should not exceed maximum steps
        self.assertLessEqual(result.steps, MAX_REPAIR_STEPS)
        self.assertLessEqual(record.steps, MAX_REPAIR_STEPS)

class TestDistanceInvariants(unittest.TestCase):
    """Test distance computation invariants"""
    
    def test_identical_text_zero_distance(self):
        """Test that identical texts have zero distance"""
        text1 = "def fibonacci(n):\n    return n"
        text2 = "def fibonacci(n):\n    return n"
        
        distance = compute_distance(text1, text2)
        self.assertEqual(distance, 0.0)
    
    def test_signature_consistency(self):
        """Test that identical texts have identical signatures"""
        text1 = "def fibonacci(n):\n    return n"
        text2 = "def fibonacci(n):\n    return n"
        
        sig1 = compute_signature(text1)
        sig2 = compute_signature(text2)
        
        self.assertEqual(sig1, sig2)
    
    def test_distance_range(self):
        """Test that distance is always in [0,1] range"""
        text1 = "def fibonacci(n):\n    return n"
        text2 = "completely different text"
        
        distance = compute_distance(text1, text2)
        
        self.assertGreaterEqual(distance, 0.0)
        self.assertLessEqual(distance, 1.0)
    
    def test_empty_text_handling(self):
        """Test distance computation with empty texts"""
        text1 = ""
        text2 = "def fibonacci(n): return n"
        
        # Empty vs non-empty should be maximum distance
        distance = compute_distance(text1, text2)
        self.assertEqual(distance, 1.0)
        
        # Both empty should be zero distance
        distance_empty = compute_distance("", "")
        self.assertEqual(distance_empty, 0.0)

if __name__ == '__main__':
    unittest.main()
