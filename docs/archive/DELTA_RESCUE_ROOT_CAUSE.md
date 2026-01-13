# Δ_rescue = 0 Root Cause Analysis

## 🔍 Root Cause Found

**File**: `src/foundational_properties.py`  
**Method**: `_extract_behavioral_signature` (line 525-588)  
**Issue**: Executes arbitrary code with hardcoded test inputs during property extraction

### The Problem

```python
def _extract_behavioral_signature(self, tree: ast.AST, code: str) -> Dict[str, Any]:
    # ...
    # Run on canonical seed inputs (algorithm-agnostic)
    test_inputs = [0, 1, 2, 5, 10]  # ← HARDCODED for fibonacci!
    
    for inp in test_inputs:
        result = main_func(inp)  # ← EXECUTES CODE!
```

### Why It Hangs

1. **Type Mismatch**: For `is_balanced(s)`, it expects a string but gets integers
2. **Execution Risk**: Arbitrary code execution can hang, loop infinitely, or crash
3. **Algorithm-Specific**: Test inputs are hardcoded for fibonacci-style functions

### Impact on Δ_rescue

The transformation pipeline calls `extract_all_properties` which:
1. Tries to extract behavioral signature
2. Hangs on execution
3. Never completes transformation
4. Results in `transformations_applied = []`
5. Therefore `Δ_rescue = 0`

## ✅ What We Fixed (Correctly)

### 1. Contract Validator Parameter Name Bug
**File**: `src/contract_validator.py` (line 83)  
**Before**: `args = {"n": case.get("input")}` (hardcoded for fibonacci)  
**After**: Gets parameter name from contract domain specification  
**Status**: ✅ Fixed properly

### 2. Contract Validator Distance Calculation
**File**: `src/contract_validator.py` (line 128-161)  
**Before**: Used slow property-based distance (called `extract_all_properties`)  
**After**: Uses fast text-based distance with `difflib`  
**Status**: ✅ Fixed properly - avoids the hanging property extraction

### 3. Pipeline Contract Attribute Name
**File**: `src/transformations/transformation_pipeline.py`  
**Before**: Inconsistent `self.contract` vs `self.contract_data`  
**After**: Consistent use of `self.contract_data`  
**Status**: ✅ Fixed properly

## ❌ What We Tried (Incorrectly)

### 1. Hardcoded Empty Property Diffs
**Attempted**: Skipped property extraction entirely  
**Why Wrong**: Band-aid solution, doesn't fix root cause  
**Status**: ❌ Reverted

### 2. Adding Caching Everywhere
**Attempted**: Added caching to property extraction and distance calculation  
**Why Wrong**: Doesn't solve the hang, just masks it on repeated calls  
**Status**: ❌ Reverted

## 🎯 Proper Solution

### Option 1: Make Behavioral Signature Optional
```python
def extract_all_properties(self, code: str, include_behavioral: bool = False) -> Dict[str, Any]:
    # ...
    for prop_name in self.properties:
        if prop_name == "behavioral_signature" and not include_behavioral:
            properties[prop_name] = None
            continue
        # ... rest of extraction
```

### Option 2: Use Contract-Specific Test Inputs
```python
def _extract_behavioral_signature(self, tree: ast.AST, code: str, contract: dict = None) -> Dict[str, Any]:
    # Get test inputs from contract oracle
    if contract:
        test_cases = contract.get("oracle_requirements", {}).get("test_cases", [])
        test_inputs = [case["input"] for case in test_cases[:5]]
    else:
        # Skip behavioral signature if no contract
        return {"can_execute": False}
```

### Option 3: Remove Behavioral Signature from Default Properties
```python
# In __init__
self.properties = [
    "control_flow_signature",
    # ... other properties ...
    # "behavioral_signature",  # ← Comment out - too risky
]
```

## 📊 Current Status

### What Works
- ✅ SnapToCanonFinalizer transforms code correctly in isolation
- ✅ Contract-aware validation accepts valid transformations
- ✅ Variable naming constraints implemented
- ✅ All individual property extractors are fast (<4ms each)

### What Doesn't Work
- ❌ Pipeline hangs when extracting behavioral signature
- ❌ Transformations never applied in full pipeline
- ❌ Δ_rescue remains 0

### Next Steps
1. **Immediate**: Disable behavioral signature extraction (Option 3)
2. **Short-term**: Make it contract-aware (Option 2)
3. **Long-term**: Redesign to be safe and algorithm-agnostic

## 💡 Key Lesson

**Never execute arbitrary code during static analysis.**

Property extraction should be:
- ✅ Fast (AST traversal only)
- ✅ Safe (no code execution)
- ✅ Deterministic (same code → same properties)
- ❌ NOT executing user code with arbitrary inputs

---
**Date**: October 21, 2025  
**Status**: Root cause identified, solution ready to implement
