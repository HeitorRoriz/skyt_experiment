#!/usr/bin/env python3
"""
Transformation Test Suite - Isolated Testing Branch
Tests transformation effectiveness with known diverse inputs
"""

import sys
import json
from typing import List, Dict, Any
sys.path.append('src')

from transformations.transformation_pipeline import TransformationPipeline
from transformations.structural.error_handling_aligner import ErrorHandlingAligner
from transformations.structural.redundant_clause_remover import RedundantClauseRemover
from transformations.behavioral.algorithm_optimizer import AlgorithmOptimizer
from transformations.behavioral.boundary_condition_aligner import BoundaryConditionAligner


class TransformationTestSuite:
    """Comprehensive test suite for transformation system"""
    
    def __init__(self):
        self.canonical_code = '''def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b'''
        
        # Create diverse test cases that represent real LLM variations
        self.test_cases = self._create_test_cases()
        
    def _create_test_cases(self) -> List[Dict[str, Any]]:
        """Create diverse test cases representing different LLM output patterns"""
        
        return [
            {
                "name": "Error Handling Pattern",
                "code": '''def fibonacci(n):
    if n < 0:
        raise ValueError("Input must be a non-negative integer.")
    elif n == 0:
        return 0
    elif n == 1:
        return 1
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b''',
                "expected_transformations": ["ErrorHandlingAligner"],
                "description": "Should convert error handling to boundary check"
            },
            
            {
                "name": "Redundant Else Pattern",
                "code": '''def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b''',
                "expected_transformations": ["RedundantClauseRemover"],
                "description": "Should remove unnecessary else clause"
            },
            
            {
                "name": "Variable Naming Pattern",
                "code": '''def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    fib1, fib2 = 0, 1
    for _ in range(2, n + 1):
        fib1, fib2 = fib2, fib1 + fib2
    return fib2''',
                "expected_transformations": ["AlgorithmOptimizer"],
                "description": "Should normalize variable names to a, b"
            },
            
            {
                "name": "Boundary Condition Pattern",
                "code": '''def fibonacci(n):
    if n < 1:
        return 0
    elif n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b''',
                "expected_transformations": ["BoundaryConditionAligner"],
                "description": "Should align boundary condition to n <= 0"
            },
            
            {
                "name": "Multiple Issues Pattern",
                "code": '''def fibonacci(n):
    if n < 0:
        raise ValueError("Input should be non-negative")
    elif n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        fib1, fib2 = 0, 1
        for i in range(2, n + 1):
            fib1, fib2 = fib2, fib1 + fib2
        return fib2''',
                "expected_transformations": ["ErrorHandlingAligner", "RedundantClauseRemover", "AlgorithmOptimizer"],
                "description": "Should fix error handling, remove else, and normalize variables"
            },
            
            {
                "name": "Already Canonical",
                "code": '''def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b''',
                "expected_transformations": [],
                "description": "Should require no transformations"
            },
            
            {
                "name": "Complex Variation",
                "code": '''def fibonacci(n):
    # Calculate Fibonacci number
    if n < 0:
        raise ValueError("Negative input not allowed")
    elif n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        # Initialize variables
        first, second = 0, 1
        for iteration in range(2, n + 1):
            first, second = second, first + second
        return second''',
                "expected_transformations": ["ErrorHandlingAligner", "RedundantClauseRemover", "AlgorithmOptimizer"],
                "description": "Complex case with comments, error handling, else clause, and different variables"
            }
        ]
    
    def calculate_distance(self, code1: str, code2: str) -> float:
        """Simple distance calculation for testing"""
        # Normalize both codes
        norm1 = '\n'.join(line.strip() for line in code1.split('\n') if line.strip())
        norm2 = '\n'.join(line.strip() for line in code2.split('\n') if line.strip())
        
        if norm1 == norm2:
            return 0.0
        
        # Simple character-based distance
        max_len = max(len(norm1), len(norm2))
        if max_len == 0:
            return 0.0
        
        # Count differing characters
        diff_count = 0
        for i in range(max_len):
            c1 = norm1[i] if i < len(norm1) else ''
            c2 = norm2[i] if i < len(norm2) else ''
            if c1 != c2:
                diff_count += 1
        
        return min(1.0, diff_count / max_len)
    
    def test_individual_transformations(self) -> Dict[str, Any]:
        """Test each transformation individually"""
        
        print("🧪 TESTING INDIVIDUAL TRANSFORMATIONS")
        print("=" * 50)
        
        transformers = {
            "ErrorHandlingAligner": ErrorHandlingAligner(),
            "RedundantClauseRemover": RedundantClauseRemover(),
            "AlgorithmOptimizer": AlgorithmOptimizer(),
            "BoundaryConditionAligner": BoundaryConditionAligner()
        }
        
        results = {}
        
        for transformer_name, transformer in transformers.items():
            print(f"\n--- Testing {transformer_name} ---")
            transformer.enable_debug()
            
            transformer_results = []
            
            for test_case in self.test_cases:
                if transformer_name in test_case["expected_transformations"]:
                    print(f"\n🔧 Testing: {test_case['name']}")
                    
                    result = transformer.transform(test_case["code"], self.canonical_code)
                    
                    original_distance = self.calculate_distance(test_case["code"], self.canonical_code)
                    final_distance = self.calculate_distance(result.transformed_code, self.canonical_code)
                    improvement = original_distance - final_distance
                    
                    test_result = {
                        "test_case": test_case["name"],
                        "success": result.success,
                        "original_distance": original_distance,
                        "final_distance": final_distance,
                        "improvement": improvement,
                        "error": result.error_message
                    }
                    
                    transformer_results.append(test_result)
                    
                    status = "✅ PASS" if result.success and improvement > 0 else "❌ FAIL"
                    print(f"  {status} - Distance: {original_distance:.3f} → {final_distance:.3f} (Δ{improvement:+.3f})")
                    
                    if not result.success:
                        print(f"  Error: {result.error_message}")
            
            results[transformer_name] = transformer_results
        
        return results
    
    def test_pipeline_integration(self) -> Dict[str, Any]:
        """Test the complete transformation pipeline"""
        
        print("\n🔄 TESTING PIPELINE INTEGRATION")
        print("=" * 50)
        
        pipeline = TransformationPipeline(debug_mode=True)
        pipeline_results = []
        
        for test_case in self.test_cases:
            print(f"\n🧪 Testing: {test_case['name']}")
            print(f"Description: {test_case['description']}")
            
            original_distance = self.calculate_distance(test_case["code"], self.canonical_code)
            
            result = pipeline.transform_code(test_case["code"], self.canonical_code)
            
            final_distance = self.calculate_distance(result["final_code"], self.canonical_code)
            improvement = original_distance - final_distance
            
            test_result = {
                "test_case": test_case["name"],
                "success": result["transformation_success"],
                "transformations_applied": result["successful_transformations"],
                "expected_transformations": test_case["expected_transformations"],
                "original_distance": original_distance,
                "final_distance": final_distance,
                "improvement": improvement,
                "iterations_used": result["iterations_used"]
            }
            
            pipeline_results.append(test_result)
            
            # Evaluate success
            expected_any = len(test_case["expected_transformations"]) > 0
            got_improvement = improvement > 0.01  # Significant improvement threshold
            
            if expected_any:
                status = "✅ PASS" if got_improvement else "❌ FAIL"
            else:
                status = "✅ PASS" if not result["transformation_success"] else "⚠️ UNEXPECTED"
            
            print(f"  {status} - Distance: {original_distance:.3f} → {final_distance:.3f} (Δ{improvement:+.3f})")
            print(f"  Applied: {result['successful_transformations']}")
            print(f"  Expected: {test_case['expected_transformations']}")
        
        return pipeline_results
    
    def generate_report(self, individual_results: Dict[str, Any], pipeline_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        
        print("\n📊 TRANSFORMATION TEST REPORT")
        print("=" * 50)
        
        # Individual transformer stats
        individual_stats = {}
        for transformer_name, results in individual_results.items():
            if results:
                successes = sum(1 for r in results if r["success"] and r["improvement"] > 0)
                total = len(results)
                avg_improvement = sum(r["improvement"] for r in results if r["improvement"] > 0) / max(1, successes)
                
                individual_stats[transformer_name] = {
                    "success_rate": successes / total if total > 0 else 0,
                    "total_tests": total,
                    "avg_improvement": avg_improvement
                }
                
                print(f"\n{transformer_name}:")
                print(f"  Success Rate: {successes}/{total} ({successes/total*100:.1f}%)")
                print(f"  Avg Improvement: {avg_improvement:.3f}")
        
        # Pipeline stats
        pipeline_successes = sum(1 for r in pipeline_results if r["improvement"] > 0.01)
        pipeline_total = len([r for r in pipeline_results if len(r["expected_transformations"]) > 0])
        
        pipeline_stats = {
            "success_rate": pipeline_successes / pipeline_total if pipeline_total > 0 else 0,
            "total_tests": pipeline_total,
            "avg_improvement": sum(r["improvement"] for r in pipeline_results if r["improvement"] > 0) / max(1, pipeline_successes)
        }
        
        print(f"\nPipeline Integration:")
        print(f"  Success Rate: {pipeline_successes}/{pipeline_total} ({pipeline_successes/pipeline_total*100:.1f}%)")
        print(f"  Avg Improvement: {pipeline_stats['avg_improvement']:.3f}")
        
        return {
            "individual_stats": individual_stats,
            "pipeline_stats": pipeline_stats,
            "individual_results": individual_results,
            "pipeline_results": pipeline_results
        }
    
    def run_full_test_suite(self) -> Dict[str, Any]:
        """Run the complete transformation test suite"""
        
        print("🚀 TRANSFORMATION SYSTEM TEST SUITE")
        print("Testing transformation effectiveness with controlled inputs")
        print("=" * 70)
        
        # Test individual transformations
        individual_results = self.test_individual_transformations()
        
        # Test pipeline integration
        pipeline_results = self.test_pipeline_integration()
        
        # Generate report
        report = self.generate_report(individual_results, pipeline_results)
        
        # Save results
        with open("transformation_test_results.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Results saved to: transformation_test_results.json")
        
        return report


if __name__ == "__main__":
    suite = TransformationTestSuite()
    results = suite.run_full_test_suite()
    
    # Final summary
    pipeline_success_rate = results["pipeline_stats"]["success_rate"]
    
    print(f"\n🎯 FINAL ASSESSMENT:")
    if pipeline_success_rate >= 0.8:
        print(f"✅ TRANSFORMATION SYSTEM WORKING EXCELLENTLY ({pipeline_success_rate:.1%} success rate)")
    elif pipeline_success_rate >= 0.6:
        print(f"⚠️ TRANSFORMATION SYSTEM WORKING ADEQUATELY ({pipeline_success_rate:.1%} success rate)")
    else:
        print(f"❌ TRANSFORMATION SYSTEM NEEDS IMPROVEMENT ({pipeline_success_rate:.1%} success rate)")
