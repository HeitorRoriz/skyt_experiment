# Transformation Validation Checklist

**Critical System: Prevents Code Corruption During Transformations**

## Overview

The SKYT transformation pipeline now includes a 4-layer validation system that prevents transformers from corrupting code. Every transformation must pass ALL checks before being accepted.

---

## The Validation Pipeline

```
Transformation Applied
    ↓
┌─────────────────────────────────────┐
│  _validate_transformation()         │
├─────────────────────────────────────┤
│  ✓ Check 1: Syntax Validation       │
│  ✓ Check 2: Undefined Variables     │
│  ✓ Check 3: Function Preservation   │
│  ✓ Check 4: Semantic Equivalence    │
└─────────────────────────────────────┘
    ↓
ALL PASS? → Accept transformation
ANY FAIL? → Rollback (reject transformation)
```

---

## Check 1: Syntax Validation

**Purpose:** Ensure transformed code is valid Python

**Method:**
```python
try:
    tree = ast.parse(transformed_code)
except SyntaxError:
    return False  # REJECT
```

**Catches:**
- Missing colons
- Unmatched parentheses
- Invalid Python syntax

**Example Rejection:**
```python
# REJECTED: Missing colon
def broken_function(
    return 42
```

---

## Check 2: Undefined Variable Detection

**Purpose:** Prevent transformers from introducing undefined variables

**Method:**
- Extract all defined variables (parameters, assignments)
- Extract all used variables (Name nodes with Load context)
- Check for uses without definitions

**Catches:**
- Variable name mismatches (e.g., uses `arr` when param is `sorted_list`)
- Typos in variable references
- Incomplete renaming

**Example Rejection:**
```python
# REJECTED: 'arr' is undefined
def binary_search(sorted_list, target):
    if arr[mid] == target:  # arr doesn't exist!
        return mid
```

**Critical Case This Fixed:**
- BoundaryConditionAligner was copying canonical conditions with canonical variable names
- Created mixed naming: `def func(sorted_list): ... if arr[mid] ...`
- Now caught and rolled back

---

## Check 3: Function Preservation

**Purpose:** Ensure transformation didn't accidentally delete all functions

**Method:**
```python
has_function = any(isinstance(node, ast.FunctionDef) 
                   for node in ast.walk(tree))
if not has_function:
    return False  # REJECT
```

**Catches:**
- Transformers that completely mangle the code
- Edge cases where function definition is removed

---

## Check 4: Semantic Equivalence

**Purpose:** Ensure transformed code BEHAVES the same as original

**Method:** Execution-based testing
1. Extract function from original code
2. Extract function from transformed code
3. Test both on standard inputs: `[0, 1, 2, 5, 10, -1, 100]`
4. Verify:
   - Same outputs for same inputs
   - Same exception types for failing inputs

**Implementation:** `SemanticValidator` class

**Example:**
```python
# Original
def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

# Transformed (valid - different vars, same behavior)
def fib(n):
    x, y = 0, 1
    for _ in range(n):
        x, y = y, x + y
    return x
# ✓ ACCEPTED: Semantically equivalent

# Transformed (invalid - different behavior)
def fib(n):
    return n * 2  # Wrong algorithm!
# ✗ REJECTED: Not semantically equivalent
```

**Behavioral Distance:**
- 0.0 = Identical behavior
- 0.5 = Partially different
- 1.0 = Completely different

---

## Rollback Mechanism

**Location:** `transformation_pipeline.py` lines 111-132

**Logic:**
```python
if result.success:
    is_valid = self._validate_transformation(
        original_code=current_code,
        transformed_code=result.transformed_code,
        transformer_name=transformer.name
    )
    
    if is_valid:
        # Accept transformation
        current_code = result.transformed_code
        successful_transformations.append(transformer.name)
    else:
        # ROLLBACK: Keep original code, try next transformer
        continue
```

**Key Principle:** **DO NO HARM**
- Better to make NO transformation than to break the code
- Correctness > Distance reduction

---

## Configuration

### VariableRenamer Threshold
- **Location:** `variable_renamer.py` line 73
- **Current Value:** 50% overlap threshold
- **Previous Value:** 70% (too lenient)
- **Reasoning:** Even 1-2 variable differences in small functions need to trigger

### Debug Mode
Enable validation logging:
```python
pipeline = TransformationPipeline(debug_mode=True)
```

Output shows:
```
Trying VariableRenamer...
  REJECT: BoundaryConditionAligner introduced undefined variables: {'arr'}
⚠️ BoundaryConditionAligner broke code - rolling back
```

---

## Test Suite

**Location:** `tests/test_transformation_validation.py`

**Tests:**
1. `test_no_undefined_variables()` - Validates Check 2
2. `test_semantic_equivalence()` - Validates Check 4
3. `test_rollback_on_corruption()` - Validates rollback mechanism
4. `test_variable_renamer_threshold()` - Validates threshold config
5. `test_syntax_error_detection()` - Validates Check 1

**Run:** `python tests/test_transformation_validation.py`

**All tests must pass** before releasing transformer changes.

---

## Historical Context: Why This Was Needed

### The Corruption Bug (Discovered 2025-09-29)

**Problem:**
- BoundaryConditionAligner copied canonical conditions verbatim
- Included canonical variable names (`arr`) into code using different names (`sorted_list`)
- Distance appeared to improve (0.216 → 0.222) ✨
- But code was BROKEN (undefined variable) 🐛

**Example:**
```python
# Original (working)
def binary_search(sorted_list, target):
    if sorted_list[mid] == target:
        return mid

# After "improvement" (broken, distance 0.222)
def binary_search(sorted_list, target):  # param still sorted_list
    if arr[mid] == target:  # arr is undefined!
        return mid
```

**Lesson:** Lower distance ≠ better code without validation

### The Fix

1. **Disabled BoundaryConditionAligner** (preventing corruption)
2. **Added 4-layer validation** (detecting corruption)
3. **Implemented rollback** (rejecting corruption)
4. **Result:** Distance got "worse" (0.233) but code is VALID ✅

**Philosophy:** Better honest measurement (0.233 with valid code) than dishonest improvement (0.222 with broken code)

---

## Metrics Impact

### Before Validation System
- Average distance: 0.222 ✨
- BoundaryConditionAligner: Fired 8x
- Transformations applied: ['BoundaryConditionAligner']
- Code quality: **BROKEN** (undefined variables)
- Success metric: **FAKE** (lower distance via corruption)

### After Validation System
- Average distance: 0.233 😟
- BoundaryConditionAligner: Fired 0x (disabled)
- Transformations applied: []
- Code quality: **VALID** ✅
- Success metric: **HONEST** (true baseline)

**Key Insight:** The "worse" result is actually progress - we now see reality!

---

## Future Improvements

### Short-term
- [ ] Lower VariableRenamer threshold further (50% → 30%?)
- [ ] Add more sophisticated semantic tests
- [ ] Profile validation performance (currently adds overhead)

### Long-term
- [ ] Oracle-based validation (run acceptance tests after transformation)
- [ ] Fuzzing to find edge cases
- [ ] Transformation verification proofs
- [ ] ML-based behavioral equivalence checking

---

## Integration Points

### Used By
- `TransformationPipeline.transform_code()` - Main pipeline
- All transformers inherit validation via pipeline

### Dependencies
- `ast` module - Syntax and AST analysis
- `SemanticValidator` - Behavioral equivalence
- Python execution environment - For semantic testing

### Called For
- Every transformation attempt
- Before accepting any code change
- During transformation pipeline execution

---

## Best Practices

### For Transformer Authors

1. **Never rename variables directly** - Use VariableRenamer
2. **Test transformations** against validation suite
3. **Handle edge cases** gracefully (return original code on error)
4. **Document assumptions** about code structure

### For Pipeline Users

1. **Enable debug mode** during development
2. **Monitor rollback rate** (high rate = transformers need fixing)
3. **Validate final output** with oracle tests
4. **Trust the validation** - rejected transformations are protecting you

---

## Emergency Bypass (NOT RECOMMENDED)

If you absolutely must disable validation (e.g., debugging):

```python
# DON'T DO THIS IN PRODUCTION
def _validate_transformation(self, original_code, transformed_code, transformer_name):
    return True  # Accept everything (DANGEROUS!)
```

**Warning:** This will allow corrupt code through. Only use for diagnosis.

---

## Summary

**The validation checklist ensures:**
✅ Syntactically valid Python  
✅ No undefined variables  
✅ Functions preserved  
✅ Behavior unchanged  

**Result:** System is now **HONEST** and **SAFE** - the foundation for actual improvement.

---

**Document Version:** 1.0  
**Last Updated:** 2025-09-29  
**Status:** Production Active  
**Criticality:** HIGH - Do not disable without understanding consequences
