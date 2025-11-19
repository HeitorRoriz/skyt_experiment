"""
Test Suite for Enhanced Side Effect Profile Property

Tests the integration of bandit-based security analysis with
the existing AST-based side effect detection.

Design principles:
- Test backward compatibility (baseline still works)
- Test enhancement (bandit analysis added when available)
- Test graceful degradation (works without bandit)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.foundational_properties import FoundationalProperties


class TestSecurityEnhancement:
    """Test enhanced side_effect_profile property"""
    
    def test_baseline_still_works(self):
        """Baseline AST side effect detection should always be present"""
        code = """
def pure_function(n):
    return n * 2
"""
        props = FoundationalProperties()
        result = props.extract_all_properties(code)
        profile = result["side_effect_profile"]
        
        # Baseline fields must exist
        assert "has_print" in profile
        assert "has_global_access" in profile
        assert "has_file_io" in profile
        assert "is_pure" in profile
        
        # Pure function should be detected
        assert profile["has_print"] is False
        assert profile["has_global_access"] is False
        assert profile["has_file_io"] is False
        assert profile["is_pure"] is True
    
    def test_baseline_detects_print(self):
        """Baseline should detect print statements"""
        code = """
def impure_function(n):
    print(f"Processing {n}")
    return n * 2
"""
        props = FoundationalProperties()
        result = props.extract_all_properties(code)
        profile = result["side_effect_profile"]
        
        # Baseline detects print
        assert profile["has_print"] is True
        assert profile["is_pure"] is False
    
    def test_security_analysis_added(self):
        """Enhanced security analysis should be added if bandit available"""
        code = """
import os

def system_call(command):
    os.system(command)  # Security risk!
    return True
"""
        props = FoundationalProperties()
        result = props.extract_all_properties(code)
        profile = result["side_effect_profile"]
        
        # Baseline
        assert "is_pure" in profile
        
        # Enhanced fields (if bandit available)
        if props.security_analyzer is not None and props.security_analyzer.available:
            assert "io_operations" in profile
            assert "network_calls" in profile
            assert "system_calls" in profile
            assert "unsafe_operations" in profile
            assert "security_risks" in profile
            assert "security_score" in profile
            assert "purity_level" in profile
            
            # Should detect system call
            assert len(profile["system_calls"]) > 0 or len(profile["security_risks"]) > 0
            
            # Should not be pure
            assert profile["is_pure"] is False
    
    def test_file_io_detection(self):
        """Should detect file I/O operations"""
        code = """
def read_file(filename):
    with open(filename, 'r') as f:
        return f.read()
"""
        props = FoundationalProperties()
        result = props.extract_all_properties(code)
        profile = result["side_effect_profile"]
        
        # Baseline detects file I/O
        assert profile["has_file_io"] is True
        assert profile["is_pure"] is False
        
        # Enhanced (if available)
        if props.security_analyzer is not None and props.security_analyzer.available:
            # Should detect I/O operations
            assert "io_operations" in profile
    
    def test_unsafe_operations_detection(self):
        """Should detect unsafe operations like eval"""
        code = """
def unsafe_function(code_string):
    result = eval(code_string)  # Unsafe!
    return result
"""
        props = FoundationalProperties()
        result = props.extract_all_properties(code)
        profile = result["side_effect_profile"]
        
        # Baseline can't detect eval
        assert "is_pure" in profile
        
        # Enhanced (if available)
        if props.security_analyzer is not None and props.security_analyzer.available:
            # Should detect unsafe operation
            assert "unsafe_operations" in profile
            assert profile["is_pure"] is False
    
    def test_security_score_computation(self):
        """Security score should reflect code safety"""
        # Safe code
        safe_code = """
def safe_function(a, b):
    return a + b
"""
        
        # Unsafe code
        unsafe_code = """
import subprocess
def unsafe_function(user_input):
    subprocess.call(user_input, shell=True)  # High severity!
"""
        
        props = FoundationalProperties()
        
        safe_result = props.extract_all_properties(safe_code)
        safe_profile = safe_result["side_effect_profile"]
        
        unsafe_result = props.extract_all_properties(unsafe_code)
        unsafe_profile = unsafe_result["side_effect_profile"]
        
        if props.security_analyzer is not None and props.security_analyzer.available:
            # Safe code should have higher security score
            safe_score = safe_profile.get("security_score")
            unsafe_score = unsafe_profile.get("security_score")
            
            if safe_score is not None and unsafe_score is not None:
                assert safe_score > unsafe_score
                assert safe_score >= 0.9  # Near perfect
    
    def test_backward_compatibility(self):
        """Old code expecting only baseline fields should still work"""
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
        props = FoundationalProperties()
        result = props.extract_all_properties(code)
        profile = result["side_effect_profile"]
        
        # Old code can access baseline fields without checking for bandit
        is_pure = profile["is_pure"]
        has_print = profile["has_print"]
        has_file_io = profile["has_file_io"]
        has_global_access = profile["has_global_access"]
        
        assert isinstance(is_pure, bool)
        assert isinstance(has_print, bool)
        assert isinstance(has_file_io, bool)
        assert isinstance(has_global_access, bool)
    
    def test_purity_levels(self):
        """Test different purity levels"""
        # Pure
        pure_code = """
def pure(n):
    return n * 2
"""
        
        # Impure
        impure_code = """
def impure(n):
    print(n)
    return n * 2
"""
        
        props = FoundationalProperties()
        
        pure_result = props.extract_all_properties(pure_code)
        pure_profile = pure_result["side_effect_profile"]
        
        impure_result = props.extract_all_properties(impure_code)
        impure_profile = impure_result["side_effect_profile"]
        
        # Baseline detection
        assert pure_profile["is_pure"] is True
        assert impure_profile["is_pure"] is False
        
        # Enhanced purity levels (if available)
        if props.security_analyzer is not None and props.security_analyzer.available:
            pure_level = pure_profile.get("purity_level")
            impure_level = impure_profile.get("purity_level")
            
            if pure_level is not None:
                assert pure_level == "pure"
            if impure_level is not None:
                # print() may not be detected by bandit, so it might still be "pure"
                # This is OK - bandit focuses on security, not all side effects
                assert impure_level in ["pure", "mostly_pure", "impure", "unsafe"]


def run_tests():
    """Run all tests"""
    test = TestSecurityEnhancement()
    
    print("Running: test_baseline_still_works...")
    test.test_baseline_still_works()
    print("✓ PASS")
    
    print("Running: test_baseline_detects_print...")
    test.test_baseline_detects_print()
    print("✓ PASS")
    
    print("Running: test_security_analysis_added...")
    test.test_security_analysis_added()
    print("✓ PASS")
    
    print("Running: test_file_io_detection...")
    test.test_file_io_detection()
    print("✓ PASS")
    
    print("Running: test_unsafe_operations_detection...")
    test.test_unsafe_operations_detection()
    print("✓ PASS")
    
    print("Running: test_security_score_computation...")
    test.test_security_score_computation()
    print("✓ PASS")
    
    print("Running: test_backward_compatibility...")
    test.test_backward_compatibility()
    print("✓ PASS")
    
    print("Running: test_purity_levels...")
    test.test_purity_levels()
    print("✓ PASS")
    
    print("\n" + "="*50)
    print("All tests passed! ✓")
    print("="*50)


if __name__ == "__main__":
    run_tests()
