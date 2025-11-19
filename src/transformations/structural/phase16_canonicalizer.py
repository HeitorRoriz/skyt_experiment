"""
Phase 1.6 Canonicalizer - Unified transformer for all Phase 1.6 enhancements

Applies three transformations in sequence:
1. Expression Canonicalization (x+0→x, x*1→x)
2. Dead Code Elimination (unused variables)
3. Commutative Normalization (a+b vs b+a)

All transformations are semantics-preserving and safe.
"""

import sys
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from transformations.transformation_base import TransformationBase, TransformationResult
from transformations.expression_canonicalizer import canonicalize_expressions
from transformations.dead_code_eliminator import eliminate_dead_code
from transformations.commutative_normalizer import normalize_commutative


class Phase16Canonicalizer(TransformationBase):
    """
    Unified transformer for Phase 1.6 enhancements.
    
    Applies all three canonicalizations in sequence:
    - Expression canonicalization
    - Dead code elimination
    - Commutative normalization
    """
    
    def __init__(self):
        super().__init__(
            name="Phase16Canonicalizer",
            description="Expression canon + Dead code elim + Commutative norm"
        )
    
    def can_transform(self, code: str, canon_code: str = None) -> bool:
        """Always enabled - these are general-purpose transformations"""
        return True
    
    def _apply_transformation(self, code: str, canon_code: str) -> str:
        """
        Apply Phase 1.6 transformations (required by TransformationBase).
        Returns transformed code as string.
        """
        result = self.transform(code, canon_code)
        return result.transformed_code
    
    def transform(self, code: str, canon_code: str = None, **kwargs) -> TransformationResult:
        """
        Apply all Phase 1.6 canonicalizations.
        
        Order matters:
        1. Expression canonicalization first (simplifies expressions)
        2. Dead code elimination second (removes unused after simplification)
        3. Commutative normalization last (canonical ordering)
        """
        current_code = code
        total_transformations = 0
        all_logs = []
        
        # Step 1: Expression Canonicalization
        try:
            transformed, stats1 = canonicalize_expressions(current_code)
            if stats1.get('success'):
                current_code = transformed
                total_transformations += stats1.get('transformations_applied', 0)
                if stats1.get('transformation_log'):
                    all_logs.extend([f"ExprCanon: {log['pattern']} → {log['result']}" 
                                    for log in stats1['transformation_log']])
        except Exception as e:
            if self.debug:
                print(f"Expression canonicalization failed: {e}")
        
        # Step 2: Dead Code Elimination
        try:
            transformed, stats2 = eliminate_dead_code(current_code)
            if stats2.get('success'):
                current_code = transformed
                total_transformations += stats2.get('transformations_applied', 0)
                if stats2.get('transformation_log'):
                    all_logs.extend([f"DeadCode: {log}" for log in stats2['transformation_log']])
        except Exception as e:
            if self.debug:
                print(f"Dead code elimination failed: {e}")
        
        # Step 3: Commutative Normalization
        try:
            transformed, stats3 = normalize_commutative(current_code)
            if stats3.get('success'):
                current_code = transformed
                total_transformations += stats3.get('transformations_applied', 0)
                if stats3.get('transformation_log'):
                    all_logs.extend([f"Commutative: {log}" for log in stats3['transformation_log']])
        except Exception as e:
            if self.debug:
                print(f"Commutative normalization failed: {e}")
        
        # Determine success
        success = current_code != code  # Changed if any transformation applied
        
        # Store details for debugging (not part of TransformationResult)
        self.last_transformation_log = all_logs
        self.last_transformation_count = total_transformations
        
        return TransformationResult(
            transformed_code=current_code,
            success=success,
            original_code=code,
            transformation_name=self.name,
            distance_improvement=0.0,  # We don't calculate distance here
            error_message=None
        )


# Test if run directly
if __name__ == "__main__":
    test_code = """
def fibonacci(n):
    if n <= 0:
        return 0 + 0  # Can canonicalize
    elif n == 1:
        return 1 * 1  # Can canonicalize
    
    unused = 999  # Dead code
    b, a = 0, 1  # Commutative swap
    for _ in range(2, n + 1):
        b, a = a, b + a  # Commutative swap
    return a
"""
    
    print("Testing Phase 1.6 Canonicalizer:")
    print("=" * 70)
    print("\nOriginal code:")
    print(test_code)
    
    transformer = Phase16Canonicalizer()
    transformer.enable_debug()
    
    result = transformer.transform(test_code)
    
    print("\nTransformed code:")
    print(result.transformed_code)
    
    print(f"\nSuccess: {result.success}")
    print(f"Explanation: {result.explanation}")
    
    if result.details.get('transformation_log'):
        print("\nDetailed log:")
        for log in result.details['transformation_log']:
            print(f"  - {log}")
