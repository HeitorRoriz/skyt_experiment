# Debug Checklist Status

## ✅ WORKING

### 1. Repairs logged
- ✅ `transformation_needed`, `transformation_success`, `transformations_applied` all logged
- ✅ `distance_pre` and `distance_post` available in JSON
- ⚠️ **Issue**: Most transformations failing (success=false, applied=[])

### 2. Single fixed canon
- ✅ One canon per contract in `outputs/canon/`
- ✅ Canon persists across temperatures/runs
- ✅ No canon drift

### 3. Iterative repair loop
- ✅ Implemented in `transformation_pipeline.py` lines 97-152
- ✅ Runs for `max_iterations` (default 3)
- ✅ Stops when no improvement
- ✅ Applies one transformation per iteration

### 6. Validator monotonicity
- ✅ Accepts when `d_post <= d_pre` (line 194 in contract_validator.py)
- ✅ Rejects when distance increases
- ✅ No trace equality requirement (commented out)

## ❌ MISSING / NEEDS FIXING

### 4. Snap-to-canon finalizer
**Status**: ❌ NOT IMPLEMENTED

**Problem**: Harmless differences not being normalized:
- Variable naming: `bracket_map` vs `brackets`
- Whitespace: blank lines, spacing
- Equivalent expressions: `len(stack) == 0` vs `not stack`
- Return style: `return len(stack) == 0` vs separate check

**Evidence from balanced_brackets_temp0.7**:
- 4/5 outputs needed transformation
- 0/4 transformations succeeded
- All had distances 0.14-0.17 (minor structural diffs)

**Solution Needed**:
```python
class SnapToCanonFinalizer(TransformationBase):
    """Final pass to normalize harmless differences"""
    
    def _apply_transformation(self, code, canon_code):
        # 1. Normalize variable names to match canon
        # 2. Normalize whitespace
        # 3. Normalize equivalent expressions
        # 4. Normalize import order
        # 5. Normalize quote style
        return normalized_code
```

### 5. Task-specific transformers
**Status**: ❌ MISSING for slugify and balanced_brackets

**Current transformers** (mostly fibonacci-focused):
- VariableRenamer (exists but not working well)
- ErrorHandlingAligner (fibonacci-specific)
- RedundantClauseRemover
- RecursionSchemaAligner
- InPlaceReturnConverter
- AlgorithmOptimizer
- BoundaryConditionAligner

**Needed for balanced_brackets**:
- Dictionary key normalization (`bracket_map` → `brackets`)
- Boolean expression normalization (`len(x) == 0` → `not x`)
- Stack operation normalization

**Needed for slugify**:
- Regex pattern normalization
- String method normalization (`re.sub` vs manual loops)
- Import normalization (`import re` placement)

### 7. Metrics wiring
**Status**: ⚠️ PARTIAL

**Missing**:
- Explicit `rescued_count = sum(d_pre > 0 and d_post == 0)`
- Pre vs post distance histograms
- Δμ = mean(d_pre) - mean(d_post) as separate metric

**Current**:
- ✅ `Delta_rescue` computed (R_anchor_post - R_anchor_pre)
- ✅ `mean_distance_pre` and `mean_distance_post` logged
- ✅ `Delta_mu` column exists but always 0

## 🎯 PRIORITY FIXES

### Priority 1: Implement SnapToCanonFinalizer
This will immediately improve Δ_rescue by handling the 80% of cases that are just naming/whitespace differences.

**Impact**: Could increase Δ_rescue from 0.0 to 0.4-0.6 for balanced_brackets and slugify.

### Priority 2: Fix VariableRenamer
Current VariableRenamer isn't working. Need to:
1. Extract variable names from canon
2. Map variables in code to canon equivalents
3. Rename consistently

### Priority 3: Add ExpressionNormalizer
Normalize equivalent boolean expressions:
- `len(x) == 0` → `not x`
- `x == True` → `x`
- `x == False` → `not x`

### Priority 4: Compute rescued_count metric
Add explicit tracking:
```python
rescued = sum(1 for i in range(len(outputs)) 
              if distance_pre[i] > 0 and distance_post[i] == 0)
rescued_rate = rescued / len(outputs)
```

## 📊 CURRENT RESULTS ANALYSIS

### Why Δ_rescue = 0?

**Fibonacci**: Outputs already match canon (d_pre = 0) → no rescue needed
**Slugify**: Structural differences transformers don't handle → rescue fails
**Balanced_brackets**: Variable naming differences → rescue fails

### What distances tell us:

| Algorithm | Temp | Mean Dist | Interpretation |
|-----------|------|-----------|----------------|
| slugify | 0.7 | 0.082 | Minor diffs (naming, whitespace) |
| balanced_brackets | 0.7 | 0.124 | Minor diffs (variable names, expressions) |

These are **exactly** the cases a snap-to-canon finalizer would fix!

## ✅ NEXT STEPS

1. Implement `SnapToCanonFinalizer` transformer
2. Add it as the LAST transformer in the pipeline
3. Re-run experiments
4. Expect Δ_rescue > 0 for slugify and balanced_brackets

---
**Generated**: October 21, 2025
**Status**: Ready for implementation
