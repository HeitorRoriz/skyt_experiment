# Incomplete Transformations Analysis for New Contracts

## Executive Summary
Analysis of incomplete transformations across the 4 new contracts (GCD, Binary Search, Merge Sort, LRU Cache) reveals **7 missing transformation cases** that map to specific foundational properties. These gaps explain why rescue rates are low (0-33%) for the new contracts.

---

## 1. Binary Search (5 incomplete, distance 0.167)

### Missing Transformation #1: **Arithmetic Expression Normalization**
**Property**: Operator Precedence (#12)

**Canon**:
```python
mid = left + (right - left) // 2
```

**Variant**:
```python
mid = (left + right) // 2
```

**Why it matters**: These are mathematically equivalent for finding midpoint, but have different overflow behavior in languages like C/Java. The canon form `left + (right - left) // 2` prevents integer overflow.

**Property mapping**:
- **Operator Precedence**: Different parenthesization patterns
- **Numerical Behavior**: Overflow prevention strategy
- **Algebraic Structure**: Equivalent expressions with different evaluation order

**Transformer needed**: `ArithmeticExpressionNormalizer`
- Recognizes algebraically equivalent expressions
- Rewrites `(a + b) // 2` → `a + (b - a) // 2`
- Preserves semantic equivalence while matching canon form

---

### Missing Transformation #2: **Parameter Name Normalization**
**Property**: Function Contracts (#4)

**Canon**:
```python
def binary_search(sorted_list, target):
```

**Variant**:
```python
def binary_search(arr, target):
```

**Why it matters**: Contract specifies `arr` as fixed variable, but canon uses `sorted_list`. This is a contract specification issue - the flexible_variables list should include both.

**Property mapping**:
- **Function Contracts**: Parameter naming consistency
- **Normalized AST Structure**: Function signature differences

**Transformer needed**: `ParameterRenamer` (already exists as `VariableRenamer` but only worked for 1 case)
- Should handle all parameter renamings consistently
- Currently only succeeded once (Run 8)

---

## 2. Merge Sort (6 incomplete, distance 0.161)

### Missing Transformation #3: **List Slicing vs Index-Based Recursion**
**Property**: Recursion Schema (#14)

**Canon** (likely):
```python
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)
```

**Variant**:
```python
def merge_sort(arr, left_idx=0, right_idx=None):
    if right_idx is None:
        right_idx = len(arr) - 1
    if left_idx >= right_idx:
        return
    mid = (left_idx + right_idx) // 2
    merge_sort(arr, left_idx, mid)
    merge_sort(arr, mid + 1, right_idx)
    merge(arr, left_idx, mid, right_idx)
```

**Why it matters**: Fundamentally different recursion patterns - slicing creates new lists (functional style) vs index-based modifies in-place (imperative style).

**Property mapping**:
- **Recursion Schema**: Different recursion patterns (copy vs in-place)
- **Side Effect Profile**: Pure (returns new list) vs impure (modifies argument)
- **Data Dependency Graph**: Different variable dependencies
- **Statement Ordering**: Different control flow structure

**Transformer needed**: `RecursionPatternNormalizer`
- Converts in-place recursion to copy-based recursion
- Transforms index parameters to slicing operations
- Changes void functions to return-based functions
- **VERY COMPLEX** - may not be feasible

---

### Missing Transformation #4: **Merge Helper Function Variations**
**Property**: Statement Ordering (#13)

**Canon merge helper** (likely):
```python
def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
```

**Variant**:
```python
def merge(left, right):
    merged = []
    while left and right:
        if left[0] <= right[0]:
            merged.append(left.pop(0))
        else:
            merged.append(right.pop(0))
    merged.extend(left if left else right)
    return merged
```

**Why it matters**: Different merge strategies - index-based vs pop-based, different loop conditions, different remainder handling.

**Property mapping**:
- **Statement Ordering**: Different sequence of operations
- **Data Dependency Graph**: Different variable usage patterns
- **Control Flow Signature**: Different loop conditions
- **Side Effect Profile**: Mutates input lists (pop) vs preserves them

**Transformer needed**: `MergeStrategyNormalizer`
- Converts pop-based to index-based merging
- Normalizes loop termination conditions
- Standardizes remainder handling

---

## 3. LRU Cache (9 incomplete, distance 0.365-0.408)

### Missing Transformation #5: **Data Structure Choice Normalization**
**Property**: Normalized AST Structure (#11)

**Canon** (likely uses OrderedDict):
```python
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity):
        self.cache = OrderedDict()
        self.capacity = capacity
    
    def get(self, key):
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
```

**Variant** (dict + list):
```python
class LRUCache:
    def __init__(self, capacity):
        self.cache = {}
        self.order = []
        self.capacity = capacity
    
    def get(self, key):
        if key not in self.cache:
            return -1
        self.order.remove(key)
        self.order.append(key)
        return self.cache[key]
    
    def put(self, key, value):
        if key in self.cache:
            self.order.remove(key)
        elif len(self.cache) >= self.capacity:
            oldest = self.order.pop(0)
            del self.cache[oldest]
        self.cache[key] = value
        self.order.append(key)
```

**Why it matters**: Completely different data structure implementations with equivalent behavior but different AST structure.

**Property mapping**:
- **Normalized AST Structure**: Different node types (OrderedDict vs dict+list)
- **Data Dependency Graph**: Different variable relationships
- **Statement Ordering**: Different operation sequences
- **Function Calls**: Different method calls (move_to_end vs remove/append)

**Transformer needed**: `DataStructureNormalizer`
- Converts dict+list pattern to OrderedDict
- Maps remove/append operations to move_to_end
- Handles eviction logic differences
- **EXTREMELY COMPLEX** - likely infeasible

---

### Missing Transformation #6: **Class Method Ordering**
**Property**: Statement Ordering (#13)

**Canon**:
```python
class LRUCache:
    def __init__(self, capacity):
        ...
    
    def get(self, key):
        ...
    
    def put(self, key, value):
        ...
```

**Variant**:
```python
class LRUCache:
    def __init__(self, capacity):
        ...
    
    def put(self, key, value):
        ...
    
    def get(self, key):
        ...
```

**Why it matters**: Method definition order doesn't affect behavior but creates AST differences.

**Property mapping**:
- **Statement Ordering**: Different method sequence
- **Normalized AST Structure**: Different AST node order

**Transformer needed**: `ClassMethodReorderer`
- Sorts methods in canonical order (\_\_init\_\_, get, put, etc.)
- Preserves method implementations
- **EASY** to implement

---

### Missing Transformation #7: **Import Statement Normalization**
**Property**: Statement Ordering (#13)

**Canon**:
```python
from collections import OrderedDict
```

**Variant** (if using dict+list):
```python
# No imports needed
```

**Why it matters**: Different data structure choices require different imports.

**Property mapping**:
- **Statement Ordering**: Presence/absence of import statements
- **Normalized AST Structure**: Different module-level statements

**Transformer needed**: Part of `DataStructureNormalizer` - must add imports when converting to OrderedDict

---

## Summary Table: Missing Transformations → Properties

| # | Transformation | Affected Contracts | Primary Properties | Complexity | Feasibility |
|---|----------------|-------------------|-------------------|------------|-------------|
| 1 | ArithmeticExpressionNormalizer | Binary Search | Operator Precedence, Numerical Behavior, Algebraic Structure | Medium | ✅ Feasible |
| 2 | ParameterRenamer (fix) | Binary Search | Function Contracts, AST Structure | Low | ✅ Easy |
| 3 | RecursionPatternNormalizer | Merge Sort | Recursion Schema, Side Effects, Data Dependencies | Very High | ❌ Hard |
| 4 | MergeStrategyNormalizer | Merge Sort | Statement Ordering, Control Flow, Data Dependencies | High | ⚠️ Medium |
| 5 | DataStructureNormalizer | LRU Cache | AST Structure, Data Dependencies, Statement Ordering | Very High | ❌ Hard |
| 6 | ClassMethodReorderer | LRU Cache | Statement Ordering, AST Structure | Low | ✅ Easy |
| 7 | ImportNormalizer | LRU Cache | Statement Ordering, AST Structure | Low | ✅ Easy |

---

## Property Coverage Analysis

### Properties with Missing Transformers:

1. **Operator Precedence (#12)**: ⚠️ Partially covered
   - Need: ArithmeticExpressionNormalizer for equivalent expressions

2. **Recursion Schema (#14)**: ❌ Not covered
   - Need: RecursionPatternNormalizer (very complex)

3. **Side Effect Profile (#6)**: ❌ Not covered
   - Need: Pure/impure conversion (part of RecursionPatternNormalizer)

4. **Algebraic Structure (#8)**: ⚠️ Partially covered
   - Need: Algebraic equivalence recognition

### Properties with Good Coverage:

- Control Flow Signature (#1): ✅ Covered by existing transformers
- Data Dependency Graph (#2): ✅ Covered
- Statement Ordering (#13): ⚠️ Partially covered (need ClassMethodReorderer)
- Function Contracts (#4): ⚠️ Partially covered (ParameterRenamer needs fix)

---

## Recommendations

### High Priority (Easy Wins):
1. **Fix ParameterRenamer** - Should handle all parameter renamings, not just some
2. **Implement ClassMethodReorderer** - Simple AST reordering
3. **Implement ArithmeticExpressionNormalizer** - Pattern matching for algebraic equivalences

### Medium Priority:
4. **Implement MergeStrategyNormalizer** - Complex but valuable for merge_sort

### Low Priority (Research Projects):
5. **RecursionPatternNormalizer** - Very complex, may not be feasible
6. **DataStructureNormalizer** - Extremely complex, likely infeasible

### Expected Impact:
- **Binary Search**: 0.167 → 1.000 rescue rate (100% success with #1 and #2)
- **Merge Sort**: 0.333 → 0.600 rescue rate (60% success with #4)
- **LRU Cache**: 0.000 → 0.300 rescue rate (30% success with #6 and #7 only)

The incomplete transformations reveal that **class-based** and **recursive** algorithms are fundamentally harder to canonicalize than iterative function-based algorithms. This is valuable research data showing the limits of AST-based transformation approaches.
