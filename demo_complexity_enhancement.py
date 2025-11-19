"""
Demo: Enhanced Complexity Analysis

Shows before/after comparison of complexity property extraction.
Run with: python demo_complexity_enhancement.py
"""

from src.foundational_properties import FoundationalProperties
import json


def demo_fibonacci():
    """Demo on fibonacci - recursive algorithm"""
    print("="*60)
    print("DEMO 1: Fibonacci (Recursive)")
    print("="*60)
    
    code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    
    props = FoundationalProperties()
    result = props.extract_all_properties(code)
    complexity = result["complexity_class"]
    
    print("\n📊 BASELINE (AST-only):")
    print(f"  - Nested loops: {complexity['nested_loops']}")
    print(f"  - Recursive calls: {complexity['recursive_calls']}")
    print(f"  - Estimated complexity: {complexity['estimated_complexity']}")
    
    if 'cyclomatic_complexity' in complexity:
        print("\n✨ ENHANCED (radon):")
        print(f"  - Cyclomatic complexity: {complexity['cyclomatic_complexity']}")
        print(f"  - Complexity rank: {complexity['complexity_rank']}")
        print(f"  - Maintainability index: {complexity['maintainability_index']:.1f}")
        print(f"  - Halstead difficulty: {complexity['halstead_difficulty']:.2f}")
        print(f"  - Halstead bugs (estimate): {complexity['halstead_bugs']:.3f}")
    else:
        print("\n⚠️  Radon not available (install with: pip install radon)")


def demo_nested_loops():
    """Demo on nested loops - O(n²) algorithm"""
    print("\n" + "="*60)
    print("DEMO 2: Nested Loops (O(n²))")
    print("="*60)
    
    code = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr
"""
    
    props = FoundationalProperties()
    result = props.extract_all_properties(code)
    complexity = result["complexity_class"]
    
    print("\n📊 BASELINE (AST-only):")
    print(f"  - Nested loops: {complexity['nested_loops']}")
    print(f"  - Recursive calls: {complexity['recursive_calls']}")
    print(f"  - Estimated complexity: {complexity['estimated_complexity']}")
    
    if 'cyclomatic_complexity' in complexity:
        print("\n✨ ENHANCED (radon):")
        print(f"  - Cyclomatic complexity: {complexity['cyclomatic_complexity']}")
        print(f"  - Complexity rank: {complexity['complexity_rank']}")
        print(f"  - Maintainability index: {complexity['maintainability_index']:.1f}")
        print(f"  - Halstead difficulty: {complexity['halstead_difficulty']:.2f}")
        print(f"  - Halstead effort: {complexity['halstead_effort']:.1f}")
        
        print("\n💡 Interpretation:")
        rank = complexity['complexity_rank']
        if rank == 'A':
            print("  → Code is simple and easy to maintain")
        elif rank == 'B':
            print("  → Code has moderate complexity")
        elif rank in ['C', 'D']:
            print("  → Code is complex, consider refactoring")
        else:
            print("  → Code is very complex, high risk")


def demo_complex_function():
    """Demo on highly complex function"""
    print("\n" + "="*60)
    print("DEMO 3: Complex Function (Many Branches)")
    print("="*60)
    
    code = """
def grade_calculator(score):
    if score < 0 or score > 100:
        raise ValueError("Invalid score")
    elif score >= 90:
        letter = 'A'
        gpa = 4.0
    elif score >= 80:
        letter = 'B'
        gpa = 3.0
    elif score >= 70:
        letter = 'C'
        gpa = 2.0
    elif score >= 60:
        letter = 'D'
        gpa = 1.0
    else:
        letter = 'F'
        gpa = 0.0
    
    if score >= 60:
        passing = True
    else:
        passing = False
    
    return {'letter': letter, 'gpa': gpa, 'passing': passing}
"""
    
    props = FoundationalProperties()
    result = props.extract_all_properties(code)
    complexity = result["complexity_class"]
    
    print("\n📊 BASELINE (AST-only):")
    print(f"  - Nested loops: {complexity['nested_loops']}")
    print(f"  - Estimated complexity: {complexity['estimated_complexity']}")
    
    if 'cyclomatic_complexity' in complexity:
        print("\n✨ ENHANCED (radon):")
        print(f"  - Cyclomatic complexity: {complexity['cyclomatic_complexity']}")
        print(f"  - Complexity rank: {complexity['complexity_rank']}")
        print(f"  - Maintainability index: {complexity['maintainability_index']:.1f}")
        
        print("\n🔬 Research Insight:")
        print("  Baseline heuristic misses branching complexity (no loops).")
        print(f"  Radon detects {complexity['cyclomatic_complexity']} decision points.")
        print("  This is why compiler-grade analysis matters!")


if __name__ == "__main__":
    print("\n🧪 Enhanced Complexity Property Demo")
    print("Showing integration of radon metrics with AST baseline\n")
    
    demo_fibonacci()
    demo_nested_loops()
    demo_complex_function()
    
    print("\n" + "="*60)
    print("✅ Step 2 Complete: complexity_class property enhanced!")
    print("="*60)
    print("\nKey achievements:")
    print("  ✓ Backward compatible (baseline always present)")
    print("  ✓ Graceful degradation (works without radon)")
    print("  ✓ Compiler-grade metrics (cyclomatic, Halstead)")
    print("  ✓ Research-ready (stronger claims for paper)")
    print("  ✓ SOLID design (Single Responsibility, Dependency Injection)")
