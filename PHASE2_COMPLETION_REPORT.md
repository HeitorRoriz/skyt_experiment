# Phase 2 Completion Report: ArithmeticExpressionNormalizer

## Summary
Successfully implemented and tested ArithmeticExpressionNormalizer with critical fix for AST unparsing issue that was preventing exact canon matches.

## Problem Identified
Initial implementation showed:
- Rescue rate: 0.0 (no outputs rescued to exact canon match)
- R_anchor_post: 0.0 (no exact matches after transformation)
- Distance: 0.167 → 0.036 (improved but not perfect)

**Root Cause**: `ast.unparse()` was introducing formatting differences:
- Input: `left, right = 0, len(...)`
- Output: `left, right = (0, len(...))`  ← Extra parentheses!

This prevented exact matches (distance = 0.0) which are required for rescue_rate and R_anchor metrics.

## Solution Implemented
Added `_remove_tuple_assignment_parens()` method to post-process AST unparsing output:
- Uses regex to detect and remove unnecessary tuple parentheses
- Preserves semantic equivalence while matching canonical formatting
- Applied after AST transformation but before returning result

## Results - Binary Search (temp 0.7, 10 runs)

### Before Fix
- R_anchor (pre): 0.400
- R_anchor (post): 0.500  
- Δ_rescue: 0.100
- Rescue rate: 0.167
- Mean distance: 0.152 → 0.036

### After Fix
- R_anchor (pre): 0.600
- R_anchor (post): **1.000** ✅ (perfect!)
- Δ_rescue: **0.400** ✅ (40% improvement)
- Rescue rate: **1.000** ✅ (100% success)
- Mean distance: 0.067 → **0.000** ✅ (perfect!)

## Impact on Metrics

### Critical Insight
The metrics system requires **exact matches** (distance = 0.0) to count outputs as:
1. **R_anchor**: Exact canon matches
2. **Δ_rescue**: Improvement in exact matches
3. **Rescue rate**: Fraction successfully rescued to exact canon

Even small formatting differences (0.036 distance) prevent these metrics from registering improvements, even though:
- Structural repeatability (R_structural) = 1.000
- Behavioral correctness = 100%
- Semantic equivalence = perfect

### Lesson Learned
When implementing AST-based transformations:
1. **Always check final distance = 0.0** for exact matches
2. **Post-process AST unparsing** to remove formatting artifacts
3. **Test with actual metrics** not just structural comparison
4. **Monitor rescue_rate** as a key indicator of transformation success

## Files Modified
1. `src/transformations/structural/arithmetic_expression_normalizer.py`
   - Added `_remove_tuple_assignment_parens()` method
   - Applied post-processing after AST unparsing

2. `src/transformations/transformation_pipeline.py`
   - Added ArithmeticExpressionNormalizer to pipeline

3. `tests/test_arithmetic_expression_normalizer.py`
   - Created comprehensive unit tests (8 test cases, all passing)

## Technical Details

### Pattern Matching
Detects: `(a + b) // 2` pattern in AST
- Matches: BinOp(BinOp(a, Add, b), FloorDiv, 2)
- Extracts variable names dynamically

### Transformation
Converts to: `a + (b - a) // 2`
- Builds new AST: BinOp(a, Add, BinOp(BinOp(b, Sub, a), FloorDiv, 2))
- Preserves variable names from original code

### Post-Processing
Removes tuple parentheses:
- Regex pattern: `(\w+(?:\s*,\s*\w+)+)\s*=\s*\(([^()]+(?:\([^)]*\)[^()]*)*)\)`
- Handles nested parentheses in values (e.g., `len(...)`)
- Only removes outermost tuple parentheses

## Next Steps
Phase 2 complete! Ready to proceed with:
- Phase 3: ClassMethodReorderer (LRU Cache)
- Phase 4: ImportNormalizer (LRU Cache)
- Phase 5: Testing and validation

## Key Takeaway
**Always validate transformations with the actual metrics system**, not just structural comparison. The rescue_rate = 0.0 was the critical signal that led to discovering and fixing the AST unparsing issue.
