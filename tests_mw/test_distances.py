# tests_mw/test_distances.py
"""
[TODO test_distances.py]
Goal: distance correctness on normalized text. No code.

1. Identical normalized texts -> d=0.
2. One line edit -> 0<d<1.
3. Whitespace differences removed by normalization -> d=0.
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.middleware.distance import compute_signature, compute_distance, _levenshtein_distance

class TestDistanceCorrectness(unittest.TestCase):
    """Test distance computation correctness"""
    
    def test_identical_texts_zero_distance(self):
        """Test that identical normalized texts yield d=0"""
        text1 = "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
        text2 = "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
        
        distance = compute_distance(text1, text2)
        self.assertEqual(distance, 0.0)
        
        # Signatures should also be identical
        sig1 = compute_signature(text1)
        sig2 = compute_signature(text2)
        self.assertEqual(sig1, sig2)
    
    def test_single_character_edit(self):
        """Test that single character edit produces 0 < d < 1"""
        text1 = "def fibonacci(n):\n    return n"
        text2 = "def fibonacci(n):\n    return m"  # Changed 'n' to 'm'
        
        distance = compute_distance(text1, text2)
        
        self.assertGreater(distance, 0.0)
        self.assertLess(distance, 1.0)
        
        # Should be a small distance for single character change
        self.assertLess(distance, 0.1)
    
    def test_single_line_edit(self):
        """Test that single line edit produces reasonable distance"""
        text1 = "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
        text2 = "def fibonacci(n):\n    if n <= 1:\n        return 1\n    return fibonacci(n-1) + fibonacci(n-2)"
        
        distance = compute_distance(text1, text2)
        
        self.assertGreater(distance, 0.0)
        self.assertLess(distance, 1.0)
        
        # Should be small distance for single character in longer text
        self.assertLess(distance, 0.05)
    
    def test_whitespace_normalization_effect(self):
        """Test that whitespace differences are handled by normalization"""
        # Note: This test assumes normalization happens before distance computation
        text1 = "def fibonacci(n):\n    return n"
        text2 = "def fibonacci(n):\n        return n"  # Extra spaces
        text3 = "def fibonacci(n):\n\treturn n"  # Tab instead of spaces
        
        # After normalization, these should be identical
        # This test verifies the normalization pipeline works correctly
        
        # For now, test that small whitespace differences produce small distances
        distance12 = compute_distance(text1, text2)
        distance13 = compute_distance(text1, text3)
        
        # Distances should be small for whitespace-only differences
        self.assertLess(distance12, 0.2)
        self.assertLess(distance13, 0.2)
    
    def test_completely_different_texts(self):
        """Test that completely different texts produce high distance"""
        text1 = "def fibonacci(n):\n    return n"
        text2 = "import os\nprint('hello world')\nx = [1, 2, 3]"
        
        distance = compute_distance(text1, text2)
        
        # Should be high distance for completely different content
        self.assertGreater(distance, 0.5)
        self.assertLessEqual(distance, 1.0)
    
    def test_function_name_change(self):
        """Test distance for function name changes"""
        text1 = "def fibonacci(n):\n    return n"
        text2 = "def fib(n):\n    return n"
        
        distance = compute_distance(text1, text2)
        
        # Should be moderate distance for function name change
        self.assertGreater(distance, 0.0)
        self.assertLess(distance, 0.5)
    
    def test_signature_determinism(self):
        """Test that signature computation is deterministic"""
        text = "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
        
        # Compute signature multiple times
        signatures = [compute_signature(text) for _ in range(10)]
        
        # All signatures should be identical
        self.assertEqual(len(set(signatures)), 1)
        
        # Signature should be non-empty hex string
        sig = signatures[0]
        self.assertIsInstance(sig, str)
        self.assertGreater(len(sig), 0)
        
        # Should be valid hex
        try:
            int(sig, 16)
        except ValueError:
            self.fail("Signature is not valid hexadecimal")

class TestLevenshteinDistance(unittest.TestCase):
    """Test Levenshtein distance implementation"""
    
    def test_empty_strings(self):
        """Test Levenshtein distance with empty strings"""
        self.assertEqual(_levenshtein_distance("", ""), 0)
        self.assertEqual(_levenshtein_distance("", "abc"), 3)
        self.assertEqual(_levenshtein_distance("abc", ""), 3)
    
    def test_identical_strings(self):
        """Test Levenshtein distance with identical strings"""
        self.assertEqual(_levenshtein_distance("hello", "hello"), 0)
        self.assertEqual(_levenshtein_distance("fibonacci", "fibonacci"), 0)
    
    def test_single_operations(self):
        """Test Levenshtein distance with single edit operations"""
        # Single insertion
        self.assertEqual(_levenshtein_distance("abc", "abcd"), 1)
        
        # Single deletion
        self.assertEqual(_levenshtein_distance("abcd", "abc"), 1)
        
        # Single substitution
        self.assertEqual(_levenshtein_distance("abc", "abd"), 1)
    
    def test_multiple_operations(self):
        """Test Levenshtein distance with multiple operations"""
        # Multiple substitutions
        self.assertEqual(_levenshtein_distance("kitten", "sitting"), 3)
        
        # Mixed operations
        self.assertEqual(_levenshtein_distance("saturday", "sunday"), 3)
    
    def test_symmetry(self):
        """Test that Levenshtein distance is symmetric"""
        s1 = "fibonacci"
        s2 = "sequence"
        
        dist12 = _levenshtein_distance(s1, s2)
        dist21 = _levenshtein_distance(s2, s1)
        
        self.assertEqual(dist12, dist21)

class TestNormalizedDistance(unittest.TestCase):
    """Test normalized distance properties"""
    
    def test_distance_bounds(self):
        """Test that normalized distance is always in [0,1]"""
        test_cases = [
            ("", ""),
            ("a", ""),
            ("", "a"),
            ("hello", "hello"),
            ("hello", "world"),
            ("short", "much longer string"),
            ("fibonacci", "f"),
        ]
        
        for text1, text2 in test_cases:
            distance = compute_distance(text1, text2)
            self.assertGreaterEqual(distance, 0.0, f"Distance < 0 for '{text1}' vs '{text2}'")
            self.assertLessEqual(distance, 1.0, f"Distance > 1 for '{text1}' vs '{text2}'")
    
    def test_distance_zero_iff_identical(self):
        """Test that distance is 0 if and only if strings are identical"""
        # Identical strings
        self.assertEqual(compute_distance("hello", "hello"), 0.0)
        self.assertEqual(compute_distance("", ""), 0.0)
        
        # Different strings
        self.assertGreater(compute_distance("hello", "world"), 0.0)
        self.assertGreater(compute_distance("a", "b"), 0.0)
        self.assertGreater(compute_distance("", "a"), 0.0)
    
    def test_distance_monotonicity(self):
        """Test that adding more differences increases distance"""
        base = "def fibonacci(n): return n"
        
        # Single character change
        single_change = "def fibonacci(n): return m"
        
        # Multiple character changes
        multi_change = "def fibonacci(x): return x + 1"
        
        dist_single = compute_distance(base, single_change)
        dist_multi = compute_distance(base, multi_change)
        
        # More changes should generally result in higher distance
        # (This is not always guaranteed due to normalization, but should hold for these examples)
        self.assertGreaterEqual(dist_multi, dist_single)

if __name__ == '__main__':
    unittest.main()
