"""
Unit tests for ArithmeticExpressionNormalizer

Tests the transformation of algebraically equivalent arithmetic expressions
to canonical form, particularly the midpoint calculation pattern.
"""

import unittest
import ast
from src.transformations.structural.arithmetic_expression_normalizer import ArithmeticExpressionNormalizer


class TestArithmeticExpressionNormalizer(unittest.TestCase):
    """Test cases for ArithmeticExpressionNormalizer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.normalizer = ArithmeticExpressionNormalizer()
        self.normalizer.enable_debug()
    
    def test_simple_midpoint_to_overflow_safe(self):
        """Test transformation of (left + right) // 2 to left + (right - left) // 2"""
        
        code = """def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
    return -1"""
        
        canon = """def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = left + (right - left) // 2
        if arr[mid] == target:
            return mid
    return -1"""
        
        # Check if transformation is needed
        self.assertTrue(self.normalizer.can_transform(code, canon))
        
        # Apply transformation
        result = self.normalizer.transform(code, canon)
        
        # Verify transformation succeeded
        self.assertTrue(result.success)
        
        # Verify the midpoint calculation was transformed
        self.assertIn("left + (right - left) // 2", result.transformed_code)
        self.assertNotIn("(left + right) // 2", result.transformed_code)
    
    def test_already_overflow_safe(self):
        """Test that already overflow-safe code is not transformed"""
        
        code = """def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = left + (right - left) // 2
        if arr[mid] == target:
            return mid
    return -1"""
        
        canon = code  # Same as code
        
        # Should not need transformation
        self.assertFalse(self.normalizer.can_transform(code, canon))
    
    def test_different_variable_names(self):
        """Test transformation with different variable names"""
        
        code = """def search(items, val):
    low, high = 0, len(items) - 1
    while low <= high:
        middle = (low + high) // 2
        if items[middle] == val:
            return middle
    return -1"""
        
        canon = """def search(items, val):
    low, high = 0, len(items) - 1
    while low <= high:
        middle = low + (high - low) // 2
        if items[middle] == val:
            return middle
    return -1"""
        
        # Check if transformation is needed
        self.assertTrue(self.normalizer.can_transform(code, canon))
        
        # Apply transformation
        result = self.normalizer.transform(code, canon)
        
        # Verify transformation succeeded
        self.assertTrue(result.success)
        
        # Verify the correct variable names are used
        self.assertIn("low + (high - low) // 2", result.transformed_code)
        self.assertNotIn("(low + high) // 2", result.transformed_code)
    
    def test_multiple_midpoint_calculations(self):
        """Test code with multiple midpoint calculations"""
        
        code = """def func():
    mid1 = (a + b) // 2
    mid2 = (x + y) // 2
    return mid1, mid2"""
        
        canon = """def func():
    mid1 = a + (b - a) // 2
    mid2 = x + (y - x) // 2
    return mid1, mid2"""
        
        # Apply transformation
        result = self.normalizer.transform(code, canon)
        
        # Verify both transformations
        self.assertIn("a + (b - a) // 2", result.transformed_code)
        self.assertIn("x + (y - x) // 2", result.transformed_code)
        self.assertNotIn("(a + b) // 2", result.transformed_code)
        self.assertNotIn("(x + y) // 2", result.transformed_code)
    
    def test_no_transformation_needed(self):
        """Test code that doesn't need transformation"""
        
        code = """def func():
    x = a + b
    y = c * d
    return x + y"""
        
        canon = code
        
        # Should not need transformation
        self.assertFalse(self.normalizer.can_transform(code, canon))
    
    def test_pattern_matching_simple_midpoint(self):
        """Test the pattern matching for simple midpoint"""
        
        code = "mid = (left + right) // 2"
        tree = ast.parse(code)
        
        # Find the BinOp node
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.FloorDiv):
                match = self.normalizer._match_simple_midpoint(node)
                self.assertIsNotNone(match)
                self.assertEqual(match['left'], 'left')
                self.assertEqual(match['right'], 'right')
                break
        else:
            self.fail("No matching BinOp node found")
    
    def test_pattern_matching_overflow_safe(self):
        """Test the pattern matching for overflow-safe midpoint"""
        
        code = "mid = left + (right - left) // 2"
        tree = ast.parse(code)
        
        # Find the BinOp node
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                match = self.normalizer._match_overflow_safe_midpoint(node)
                if match:
                    self.assertEqual(match['left'], 'left')
                    self.assertEqual(match['right'], 'right')
                    break
        else:
            self.fail("No matching overflow-safe pattern found")
    
    def test_preserves_other_code(self):
        """Test that transformation preserves other parts of the code"""
        
        code = """def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    count = 0
    while left <= right:
        count += 1
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1"""
        
        canon = """def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    count = 0
    while left <= right:
        count += 1
        mid = left + (right - left) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1"""
        
        result = self.normalizer.transform(code, canon)
        
        # Verify transformation succeeded
        self.assertTrue(result.success)
        
        # Verify other code is preserved
        self.assertIn("count = 0", result.transformed_code)
        self.assertIn("count += 1", result.transformed_code)
        self.assertIn("elif arr[mid] < target:", result.transformed_code)
        self.assertIn("left = mid + 1", result.transformed_code)
        self.assertIn("right = mid - 1", result.transformed_code)


if __name__ == '__main__':
    unittest.main()
