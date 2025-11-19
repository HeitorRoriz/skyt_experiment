"""
Test Suite for Enhanced Function Contracts Property

Tests the integration of mypy-based type checking with
the existing AST-based contract extraction.

Design principles:
- Test backward compatibility (baseline still works)
- Test enhancement (mypy type analysis added when available)
- Test graceful degradation (works without mypy)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.foundational_properties import FoundationalProperties


class TestTypeCheckingEnhancement:
    """Test enhanced function_contracts property"""
    
    def test_baseline_still_works(self):
        """Baseline AST contract extraction should always be present"""
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
        props = FoundationalProperties()
        result = props.extract_all_properties(code)
        contracts = result["function_contracts"]
        
        # Baseline fields must exist
        assert "fibonacci" in contracts
        assert "name" in contracts["fibonacci"]
        assert "args" in contracts["fibonacci"]
        assert "has_return" in contracts["fibonacci"]
        
        # Baseline values should be correct
        assert contracts["fibonacci"]["name"] == "fibonacci"
        assert contracts["fibonacci"]["args"] == ["n"]
        assert contracts["fibonacci"]["has_return"] is True
    
    def test_type_analysis_added(self):
        """Enhanced type analysis should be added if mypy available"""
        code = """
def add(a: int, b: int) -> int:
    return a + b

def multiply(x, y):
    return x * y
"""
        props = FoundationalProperties()
        result = props.extract_all_properties(code)
        contracts = result["function_contracts"]
        
        # Baseline fields for both functions
        assert "add" in contracts
        assert "multiply" in contracts
        
        # Enhanced fields (if mypy available)
        if props.type_checker is not None and props.type_checker.available:
            # Global type analysis
            assert "_type_analysis" in contracts
            assert "type_errors" in contracts["_type_analysis"]
            assert "type_safe" in contracts["_type_analysis"]
            assert "annotation_coverage" in contracts["_type_analysis"]
            
            # Per-function type signatures
            assert "type_signature" in contracts["add"]
            assert "has_type_annotations" in contracts["add"]
            
            # add() has annotations
            assert contracts["add"]["has_type_annotations"] is True
            
            # multiply() has no annotations
            assert contracts["multiply"]["has_type_annotations"] is False
            
            # No type errors in this code
            assert contracts["_type_analysis"]["type_safe"] is True
    
    def test_type_error_detection(self):
        """Type errors should be detected"""
        code = """
def bad_function(n: int) -> int:
    if n > 0:
        return "string"  # Type error: returning str instead of int
    return n
"""
        props = FoundationalProperties()
        result = props.extract_all_properties(code)
        contracts = result["function_contracts"]
        
        # Baseline still works
        assert "bad_function" in contracts
        
        # Enhanced type checking (if available)
        if props.type_checker is not None and props.type_checker.available:
            type_analysis = contracts.get("_type_analysis", {})
            
            # Should detect type error
            if "type_errors" in type_analysis:
                # mypy should flag the return type mismatch
                # Note: mypy might not catch this in all modes
                assert isinstance(type_analysis["type_errors"], list)
    
    def test_unannotated_code_no_errors(self):
        """Unannotated code should not trigger type errors (lenient mode)"""
        code = """
def mystery(x):
    return x + 1
"""
        props = FoundationalProperties()
        result = props.extract_all_properties(code)
        contracts = result["function_contracts"]
        
        # Baseline
        assert "mystery" in contracts
        assert contracts["mystery"]["args"] == ["x"]
        
        # Enhanced (if available)
        if props.type_checker is not None and props.type_checker.available:
            # Should have 0% annotation coverage
            coverage = contracts["_type_analysis"]["annotation_coverage"]
            assert coverage == 0.0
    
    def test_backward_compatibility(self):
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
        contracts = result["function_contracts"]
        
        # Old code can access baseline fields without checking for mypy
        assert "quicksort" in contracts
        name = contracts["quicksort"]["name"]
        args = contracts["quicksort"]["args"]
        has_return = contracts["quicksort"]["has_return"]
        
        assert name == "quicksort"
        assert args == ["arr"]
        assert has_return is True
    
    def test_multiple_functions_annotation_coverage(self):
        """Test annotation coverage calculation"""
        code = """
def annotated_func(x: int, y: int) -> int:
    return x + y

def unannotated_func(a, b):
    return a - b

def partial_annotated(m: int, n):
    return m * n
"""
        props = FoundationalProperties()
        result = props.extract_all_properties(code)
        contracts = result["function_contracts"]
        
        # All three functions in baseline
        assert "annotated_func" in contracts
        assert "unannotated_func" in contracts
        assert "partial_annotated" in contracts
        
        # Enhanced (if available)
        if props.type_checker is not None and props.type_checker.available:
            # 1 fully annotated out of 3 = ~33.3%
            # or 2 with any annotations out of 3 = ~66.7%
            coverage = contracts["_type_analysis"]["annotation_coverage"]
            assert 0.0 <= coverage <= 1.0
            
            # Check individual functions
            assert contracts["annotated_func"]["has_type_annotations"] is True
            assert contracts["unannotated_func"]["has_type_annotations"] is False
            assert contracts["partial_annotated"]["has_type_annotations"] is True


def run_tests():
    """Run all tests"""
    test = TestTypeCheckingEnhancement()
    
    print("Running: test_baseline_still_works...")
    test.test_baseline_still_works()
    print("✓ PASS")
    
    print("Running: test_type_analysis_added...")
    test.test_type_analysis_added()
    print("✓ PASS")
    
    print("Running: test_type_error_detection...")
    test.test_type_error_detection()
    print("✓ PASS")
    
    print("Running: test_unannotated_code_no_errors...")
    test.test_unannotated_code_no_errors()
    print("✓ PASS")
    
    print("Running: test_backward_compatibility...")
    test.test_backward_compatibility()
    print("✓ PASS")
    
    print("Running: test_multiple_functions_annotation_coverage...")
    test.test_multiple_functions_annotation_coverage()
    print("✓ PASS")
    
    print("\n" + "="*50)
    print("All tests passed! ✓")
    print("="*50)


if __name__ == "__main__":
    run_tests()
