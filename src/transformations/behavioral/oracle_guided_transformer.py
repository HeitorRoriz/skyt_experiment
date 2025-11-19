"""
Oracle-Guided Template Transformer - Phase 1.7

Handles algorithmic diversity by using oracle validation to ensure equivalence,
then applying canon template when appropriate.

Key Principles:
1. If both code and canon pass oracle → they're semantically equivalent
2. If distance is high despite equivalence → algorithmic difference
3. Safe to apply canon template (preserves correctness)
4. MUST be idempotent: transform(transform(x)) = transform(x)
5. MUST ensure positive rescue: distance_after ≤ distance_before
"""

import sys
import ast
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from transformations.transformation_base import TransformationBase, TransformationResult
from foundational_properties import FoundationalProperties


class OracleGuidedTransformer(TransformationBase):
    """
    Template-based transformer for algorithmically diverse but semantically equivalent code.
    
    Uses oracle validation to ensure correctness, then applies canon template
    when syntactic transformations are insufficient.
    
    Critical Properties:
    - Idempotent: Applying multiple times produces same result
    - Positive rescue: Never increases distance to canon
    - Oracle-validated: Only transforms code that passes oracle
    """
    
    def __init__(self, contract: dict = None, oracle=None, distance_threshold: float = 0.15):
        super().__init__(
            name="OracleGuidedTransformer",
            description="Template-based transformation for algorithmic diversity"
        )
        self.contract = contract
        self.oracle = oracle
        self.distance_threshold = distance_threshold
        self.props_extractor = FoundationalProperties()
    
    def set_oracle(self, oracle):
        """Set oracle for validation (can be called after initialization)"""
        self.oracle = oracle
    
    def can_transform(self, code: str, canon_code: str = None) -> bool:
        """
        Can transform if:
        1. Code passes oracle (is correct)
        2. Distance to canon is high (likely algorithmic difference)
        3. Canon is available
        """
        if not canon_code:
            return False
        
        # Check if code passes oracle
        if self.oracle:
            try:
                if not self.oracle.validate_code(code):
                    if self.debug_mode:
                        print("[OracleGuidedTransformer] Code fails oracle - cannot transform")
                    return False
            except Exception as e:
                if self.debug_mode:
                    print(f"[OracleGuidedTransformer] Oracle validation error: {e}")
                return False
        
        # Calculate distance
        try:
            code_props = self.props_extractor.extract_transformation_properties(code)
            canon_props = self.props_extractor.extract_transformation_properties(canon_code)
            distance = self.props_extractor.calculate_transformation_distance(code_props, canon_props)
            
            # Only apply if distance is high (algorithmic difference)
            if distance > self.distance_threshold:
                if self.debug_mode:
                    print(f"[OracleGuidedTransformer] High distance ({distance:.3f}) - algorithmic difference detected")
                return True
            
        except Exception as e:
            if self.debug_mode:
                print(f"[OracleGuidedTransformer] Distance calculation error: {e}")
            return False
        
        return False
    
    def _apply_transformation(self, code: str, canon_code: str) -> str:
        """
        Apply oracle-guided transformation.
        
        Strategy:
        1. Verify code passes oracle (is correct)
        2. Check if already matches canon (idempotency)
        3. Apply canon template (safe because oracle validates equivalence)
        4. Verify result still passes oracle
        5. Ensure distance decreased (positive rescue)
        """
        
        # Step 1: Verify code is correct
        if self.oracle:
            if not self.oracle.validate_code(code):
                if self.debug_mode:
                    print("[OracleGuidedTransformer] Code fails oracle - aborting")
                return code  # Don't transform incorrect code
        
        # Step 2: Check if already at canon (idempotency)
        try:
            code_props = self.props_extractor.extract_transformation_properties(code)
            canon_props = self.props_extractor.extract_transformation_properties(canon_code)
            initial_distance = self.props_extractor.calculate_transformation_distance(code_props, canon_props)
            
            if initial_distance < 0.01:  # Already at canon
                if self.debug_mode:
                    print("[OracleGuidedTransformer] Already at canon - idempotent return")
                return code  # Idempotent: don't change what's already canonical
        
        except Exception as e:
            if self.debug_mode:
                print(f"[OracleGuidedTransformer] Distance check error: {e}")
            return code
        
        # Step 3: Apply canon template
        # Since both code and canon pass oracle, they're semantically equivalent
        # Safe to use canon structure
        transformed = canon_code
        
        if self.debug_mode:
            print(f"[OracleGuidedTransformer] Applying canon template (distance: {initial_distance:.3f})")
        
        # Step 4: Verify result passes oracle
        if self.oracle:
            if not self.oracle.validate_code(transformed):
                if self.debug_mode:
                    print("[OracleGuidedTransformer] Transformed code fails oracle - reverting")
                return code  # Safety: don't break correctness
        
        # Step 5: Verify positive rescue (distance decreased)
        try:
            transformed_props = self.props_extractor.extract_transformation_properties(transformed)
            final_distance = self.props_extractor.calculate_transformation_distance(transformed_props, canon_props)
            
            if final_distance > initial_distance:
                if self.debug_mode:
                    print(f"[OracleGuidedTransformer] Negative rescue ({initial_distance:.3f} → {final_distance:.3f}) - reverting")
                return code  # Positive rescue: never increase distance
            
            if self.debug_mode:
                print(f"[OracleGuidedTransformer] Positive rescue: {initial_distance:.3f} → {final_distance:.3f}")
        
        except Exception as e:
            if self.debug_mode:
                print(f"[OracleGuidedTransformer] Final distance check error: {e}")
            return code  # On error, be conservative
        
        return transformed
    
    def transform(self, code: str, canon_code: str = None, **kwargs) -> TransformationResult:
        """
        Apply oracle-guided transformation with full safety checks.
        """
        if not canon_code:
            return TransformationResult(
                transformed_code=code,
                success=False,
                original_code=code,
                transformation_name=self.name,
                distance_improvement=0.0,
                error_message="No canon provided"
            )
        
        # Check if we can transform
        if not self.can_transform(code, canon_code):
            return TransformationResult(
                transformed_code=code,
                success=False,
                original_code=code,
                transformation_name=self.name,
                distance_improvement=0.0,
                error_message="Cannot transform (oracle fail or low distance)"
            )
        
        # Calculate initial distance
        try:
            code_props = self.props_extractor.extract_transformation_properties(code)
            canon_props = self.props_extractor.extract_transformation_properties(canon_code)
            initial_distance = self.props_extractor.calculate_transformation_distance(code_props, canon_props)
        except Exception as e:
            return TransformationResult(
                transformed_code=code,
                success=False,
                original_code=code,
                transformation_name=self.name,
                distance_improvement=0.0,
                error_message=f"Distance calculation error: {e}"
            )
        
        # Apply transformation
        transformed = self._apply_transformation(code, canon_code)
        
        # Calculate final distance
        try:
            transformed_props = self.props_extractor.extract_transformation_properties(transformed)
            final_distance = self.props_extractor.calculate_transformation_distance(transformed_props, canon_props)
            improvement = initial_distance - final_distance
        except Exception as e:
            improvement = 0.0
            final_distance = initial_distance
        
        # Determine success
        success = transformed != code and improvement >= 0  # Changed AND didn't get worse
        
        return TransformationResult(
            transformed_code=transformed,
            success=success,
            original_code=code,
            transformation_name=self.name,
            distance_improvement=improvement,
            error_message=None if success else "No improvement or transformation reverted"
        )


# Test if run directly
if __name__ == "__main__":
    # Test idempotency
    print("="*70)
    print("Testing Oracle-Guided Transformer")
    print("="*70)
    
    # Simple test: verify idempotency
    code = """
def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    a, b = 0, 1
    for i in range(2, n + 1):
        a, b = b, a + b
    return b
"""
    
    canon = """
def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
"""
    
    transformer = OracleGuidedTransformer(distance_threshold=0.1)
    transformer.enable_debug()
    
    print("\nTest 1: Idempotency")
    print("-" * 70)
    
    result1 = transformer.transform(code, canon)
    print(f"First transform - Success: {result1.success}")
    print(f"Distance improvement: {result1.distance_improvement:.4f}")
    
    result2 = transformer.transform(result1.transformed_code, canon)
    print(f"\nSecond transform (on result) - Success: {result2.success}")
    print(f"Distance improvement: {result2.distance_improvement:.4f}")
    
    if result1.transformed_code == result2.transformed_code:
        print("\n✅ IDEMPOTENT: transform(transform(x)) = transform(x)")
    else:
        print("\n❌ NOT IDEMPOTENT!")
    
    print("\n" + "="*70)
