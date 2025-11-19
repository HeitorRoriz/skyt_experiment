"""
Test Suite for Enhanced Complexity Property

Tests the integration of radon-based complexity analysis with
the existing AST-based heuristic complexity extraction.

Design principles:
- Test backward compatibility (baseline still works)
- Test enhancement (radon metrics added when available)
- Test graceful degradation (works without radon)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.foundational_properties import FoundationalProperties


class TestComplexityEnhancement:
    """Test enhanced complexity_class property"""
    
    def test_baseline_still_works(self):
        """Baseline AST metrics should always be present"""
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
        props = FoundationalProperties()
        result = props.extract_all_properties(code)
        complexity = result["complexity_class"]
        
        # Baseline fields must exist
        assert "nested_loops" in complexity
        assert "recursive_calls" in complexity
        assert "estimated_complexity" in complexity
        
        # Baseline values should be correct
        assert complexity["nested_loops"] == 0  # No loops
        assert complexity["recursive_calls"] > 0  # Recursive
        assert complexity["estimated_complexity"] == "O(2^n)"  # Heuristic for recursion
    
    def test_radon_metrics_added(self):
        """Enhanced radon metrics should be added if available"""
        code = """
def complex_function(n):
    result = 0
    for i in range(n):
        for j in range(i):
            if i % 2 == 0:
                result += i * j
            else:
                result -= i + j
    return result
"""
        props = FoundationalProperties()
        result = props.extract_all_properties(code)
        complexity = result["complexity_class"]
        
        # Baseline fields
        assert "nested_loops" in complexity
        assert complexity["nested_loops"] == 2  # Two nested loops
        
        # Enhanced fields (if radon available)
        if props.complexity_analyzer is not None:
            assert "cyclomatic_complexity" in complexity
            assert "complexity_rank" in complexity
            assert "maintainability_index" in complexity
            assert "halstead_difficulty" in complexity
            assert "halstead_effort" in complexity
            
            # Cyclomatic complexity should be > 1 (has if statement)
            assert complexity["cyclomatic_complexity"] > 1
            
            # Complexity rank should be A-F
            assert complexity["complexity_rank"] in ["A", "B", "C", "D", "E", "F"]
    
    def test_simple_function_low_complexity(self):
        """Simple functions should have low complexity metrics"""
        code = """
def add(a, b):
    return a + b
"""
        props = FoundationalProperties()
        result = props.extract_all_properties(code)
        complexity = result["complexity_class"]
        
        # Baseline: Simple function
        assert complexity["nested_loops"] == 0
        assert complexity["recursive_calls"] == 0
        assert complexity["estimated_complexity"] == "O(1)"
        
        # Enhanced: Low cyclomatic complexity
        if props.complexity_analyzer is not None:
            assert complexity["cyclomatic_complexity"] == 1  # No branches
            assert complexity["complexity_rank"] == "A"  # Best rank
    
    def test_backward_compatibility_with_old_code(self):
        """Old code expecting only baseline fields should still work"""
        code = """
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
"""
        props = FoundationalProperties()
        result = props.extract_all_properties(code)
        complexity = result["complexity_class"]
        
        # Old code can access baseline fields without checking for radon
        loops = complexity["nested_loops"]
        recursive = complexity["recursive_calls"]
        estimate = complexity["estimated_complexity"]
        
        assert isinstance(loops, int)
        assert isinstance(recursive, int)
        assert isinstance(estimate, str)
    
    def test_comparison_baseline_vs_enhanced(self):
        """Compare baseline heuristic vs radon measurement"""
        code = """
def nested_loops(n):
    count = 0
    for i in range(n):
        for j in range(n):
            count += 1
    return count
"""
        props = FoundationalProperties()
        result = props.extract_all_properties(code)
        complexity = result["complexity_class"]
        
        # Baseline heuristic
        assert complexity["nested_loops"] == 2
        assert complexity["estimated_complexity"] == "O(n^2)"
        
        # Radon measurement (more precise)
        if props.complexity_analyzer is not None:
            # Cyclomatic complexity should be > 1 (loops add complexity)
            # Typically 3 for nested loops: entry + 2 loops
            assert complexity["cyclomatic_complexity"] >= 1
            assert complexity["cyclomatic_complexity"] <= 5  # Should be low for simple loops
            
            # Halstead metrics should detect nested loops
            assert complexity["halstead_difficulty"] > 0


def run_tests():
    """Run all tests"""
    test = TestComplexityEnhancement()
    
    print("Running: test_baseline_still_works...")
    test.test_baseline_still_works()
    print("✓ PASS")
    
    print("Running: test_radon_metrics_added...")
    test.test_radon_metrics_added()
    print("✓ PASS")
    
    print("Running: test_simple_function_low_complexity...")
    test.test_simple_function_low_complexity()
    print("✓ PASS")
    
    print("Running: test_backward_compatibility_with_old_code...")
    test.test_backward_compatibility_with_old_code()
    print("✓ PASS")
    
    print("Running: test_comparison_baseline_vs_enhanced...")
    test.test_comparison_baseline_vs_enhanced()
    print("✓ PASS")
    
    print("\n" + "="*50)
    print("All tests passed! ✓")
    print("="*50)


if __name__ == "__main__":
    run_tests()
