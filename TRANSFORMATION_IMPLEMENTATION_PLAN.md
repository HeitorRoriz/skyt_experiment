# Transformation Implementation Plan

## Overview
Implementation plan for 7 missing transformations identified in the incomplete transformations analysis. Organized by priority and complexity, targeting rescue rate improvements from 0-33% to 30-100%.

---

## Phase 1: Fix ParameterRenamer (Binary Search - Easy Win) 🟢

**Target**: Binary Search rescue rate 16.7% → 50%+
**Complexity**: Low (1-2 hours)
**Impact**: High

### Problem
`VariableRenamer` only succeeded in 1 out of 6 cases where parameter renaming was needed (`arr` → `sorted_list`).

### Root Cause Analysis
Need to investigate why the transformer:
- ✅ Worked for Run 8
- ❌ Failed for Runs 2, 3, 5, 7, 10

### Implementation Steps

1. **Investigate existing VariableRenamer**
   - Location: `src/transformations/variable_renamer.py`
   - Check: Does it handle function parameters?
   - Check: Does it handle all occurrences in function body?
   - Check: Is there a condition that prevented it from running?

2. **Debug the failure cases**
   - Read Run 2 and Run 8 outputs from JSON
   - Compare what made Run 8 succeed
   - Identify the blocking condition

3. **Fix the transformer**
   - Ensure it handles function parameters (not just local variables)
   - Ensure it renames ALL occurrences (parameters + body references)
   - Remove any overly restrictive conditions

4. **Add test cases**
   ```python
   # Test: Parameter renaming
   def test_parameter_renaming():
       code = "def binary_search(arr, target):\n    return arr[0]"
       expected = "def binary_search(sorted_list, target):\n    return sorted_list[0]"
       result = VariableRenamer().transform(code, canon_code)
       assert result == expected
   ```

5. **Validate fix**
   - Re-run binary_search experiment
   - Expect rescue rate to increase significantly

### Success Criteria
- ✅ VariableRenamer handles all parameter renamings
- ✅ Binary Search rescue rate > 50%
- ✅ All 6 parameter renaming cases succeed

---

## Phase 2: Implement ArithmeticExpressionNormalizer (Binary Search - Medium) 🟢

**Target**: Binary Search rescue rate 50% → 100%
**Complexity**: Medium (3-4 hours)
**Impact**: High

### Problem
Canon uses `mid = left + (right - left) // 2` but variants use `mid = (left + right) // 2`.
These are algebraically equivalent but have different AST structures.

### Implementation Steps

1. **Create new transformer file**
   - Location: `src/transformations/arithmetic_expression_normalizer.py`
   - Inherit from `TransformationBase`

2. **Implement pattern matching**
   ```python
   class ArithmeticExpressionNormalizer(TransformationBase):
       """Normalizes algebraically equivalent arithmetic expressions"""
       
       def __init__(self):
           super().__init__()
           self.patterns = [
               # Pattern: (a + b) // 2 → a + (b - a) // 2
               {
                   'match': self._match_simple_midpoint,
                   'transform': self._transform_to_overflow_safe_midpoint
               }
           ]
       
       def _match_simple_midpoint(self, node):
           """
           Match: (left + right) // 2
           AST: BinOp(BinOp(left, Add, right), FloorDiv, 2)
           """
           if not isinstance(node, ast.BinOp):
               return None
           if not isinstance(node.op, ast.FloorDiv):
               return None
           if not (isinstance(node.right, ast.Constant) and node.right.value == 2):
               return None
           if not isinstance(node.left, ast.BinOp):
               return None
           if not isinstance(node.left.op, ast.Add):
               return None
           
           # Extract variable names
           left_var = self._get_name(node.left.left)
           right_var = self._get_name(node.left.right)
           
           if left_var and right_var:
               return {'left': left_var, 'right': right_var}
           return None
       
       def _transform_to_overflow_safe_midpoint(self, node, match_info):
           """
           Transform: (left + right) // 2 → left + (right - left) // 2
           """
           left_name = match_info['left']
           right_name = match_info['right']
           
           # Build: left + (right - left) // 2
           new_node = ast.BinOp(
               left=ast.Name(id=left_name, ctx=ast.Load()),
               op=ast.Add(),
               right=ast.BinOp(
                   left=ast.BinOp(
                       left=ast.Name(id=right_name, ctx=ast.Load()),
                       op=ast.Sub(),
                       right=ast.Name(id=left_name, ctx=ast.Load())
                   ),
                   op=ast.FloorDiv(),
                   right=ast.Constant(value=2)
               )
           )
           return new_node
       
       def transform(self, code: str, canon_code: str) -> str:
           """Apply arithmetic expression normalization"""
           tree = ast.parse(code)
           
           # Walk the tree and apply transformations
           class ExpressionNormalizer(ast.NodeTransformer):
               def __init__(self, normalizer):
                   self.normalizer = normalizer
               
               def visit_BinOp(self, node):
                   self.generic_visit(node)
                   
                   for pattern in self.normalizer.patterns:
                       match = pattern['match'](node)
                       if match:
                           return pattern['transform'](node, match)
                   
                   return node
           
           transformer = ExpressionNormalizer(self)
           new_tree = transformer.visit(tree)
           
           return ast.unparse(new_tree)
   ```

3. **Add to transformation pipeline**
   - Location: `src/transformations/transformation_pipeline.py`
   - Add after `VariableRenamer`, before `SnapToCanonFinalizer`
   ```python
   from .arithmetic_expression_normalizer import ArithmeticExpressionNormalizer
   
   # In TransformationPipeline.__init__:
   self.transformations = [
       VariableRenamer(),
       ArithmeticExpressionNormalizer(),  # NEW
       WhitespaceNormalizer(),
       # ...
   ]
   ```

4. **Add test cases**
   ```python
   def test_midpoint_normalization():
       code = "mid = (left + right) // 2"
       canon = "mid = left + (right - left) // 2"
       result = ArithmeticExpressionNormalizer().transform(code, canon)
       assert result == canon
   ```

5. **Validate**
   - Re-run binary_search experiment
   - Expect rescue rate → 100%

### Success Criteria
- ✅ Recognizes `(a + b) // 2` pattern
- ✅ Transforms to `a + (b - a) // 2`
- ✅ Binary Search rescue rate = 100%

---

## Phase 3: Implement ClassMethodReorderer (LRU Cache - Easy) 🟢

**Target**: LRU Cache rescue rate 0% → 10%+
**Complexity**: Low (1-2 hours)
**Impact**: Low-Medium

### Problem
Methods defined in different orders create AST differences even though behavior is identical.

### Implementation Steps

1. **Create new transformer file**
   - Location: `src/transformations/class_method_reorderer.py`

2. **Implement method reordering**
   ```python
   class ClassMethodReorderer(TransformationBase):
       """Reorders class methods to canonical order"""
       
       CANONICAL_METHOD_ORDER = [
           '__init__',
           '__new__',
           '__del__',
           '__str__',
           '__repr__',
           # Then alphabetically by name
       ]
       
       def _get_method_priority(self, method_name: str) -> tuple:
           """Return sort key for method"""
           if method_name in self.CANONICAL_METHOD_ORDER:
               return (0, self.CANONICAL_METHOD_ORDER.index(method_name))
           else:
               return (1, method_name)  # Alphabetical for non-special methods
       
       def transform(self, code: str, canon_code: str) -> str:
           """Reorder class methods to match canonical order"""
           tree = ast.parse(code)
           
           class MethodReorderer(ast.NodeTransformer):
               def __init__(self, reorderer):
                   self.reorderer = reorderer
               
               def visit_ClassDef(self, node):
                   self.generic_visit(node)
                   
                   # Separate methods from other class members
                   methods = []
                   other_members = []
                   
                   for item in node.body:
                       if isinstance(item, ast.FunctionDef):
                           methods.append(item)
                       else:
                           other_members.append(item)
                   
                   # Sort methods by canonical order
                   methods.sort(key=lambda m: self.reorderer._get_method_priority(m.name))
                   
                   # Reconstruct body: other members first, then sorted methods
                   node.body = other_members + methods
                   
                   return node
           
           transformer = MethodReorderer(self)
           new_tree = transformer.visit(tree)
           
           return ast.unparse(new_tree)
   ```

3. **Add to pipeline**
   ```python
   from .class_method_reorderer import ClassMethodReorderer
   
   self.transformations = [
       # ...
       ClassMethodReorderer(),  # NEW
       SnapToCanonFinalizer()
   ]
   ```

4. **Test**
   ```python
   def test_method_reordering():
       code = """
       class LRUCache:
           def put(self, k, v): pass
           def __init__(self, cap): pass
           def get(self, k): pass
       """
       expected = """
       class LRUCache:
           def __init__(self, cap): pass
           def get(self, k): pass
           def put(self, k, v): pass
       """
       result = ClassMethodReorderer().transform(code, expected)
       # Assert methods are in correct order
   ```

### Success Criteria
- ✅ Reorders methods to canonical sequence
- ✅ Preserves method implementations
- ✅ LRU Cache rescue rate increases slightly

---

## Phase 4: Implement ImportNormalizer (LRU Cache - Easy) 🟢

**Target**: LRU Cache rescue rate 10% → 30%
**Complexity**: Low (1-2 hours)
**Impact**: Medium

### Problem
Missing or differently ordered import statements create AST differences.

### Implementation Steps

1. **Create new transformer file**
   - Location: `src/transformations/import_normalizer.py`

2. **Implement import normalization**
   ```python
   class ImportNormalizer(TransformationBase):
       """Normalizes import statements to match canon"""
       
       def transform(self, code: str, canon_code: str) -> str:
           """Add missing imports and sort them"""
           code_tree = ast.parse(code)
           canon_tree = ast.parse(canon_code)
           
           # Extract imports from canon
           canon_imports = self._extract_imports(canon_tree)
           code_imports = self._extract_imports(code_tree)
           
           # Find missing imports
           missing_imports = canon_imports - code_imports
           
           if not missing_imports:
               return code
           
           # Add missing imports at the top
           new_body = list(missing_imports) + code_tree.body
           code_tree.body = new_body
           
           return ast.unparse(code_tree)
       
       def _extract_imports(self, tree):
           """Extract set of import statements"""
           imports = set()
           for node in ast.walk(tree):
               if isinstance(node, ast.Import):
                   for alias in node.names:
                       imports.add(('import', alias.name, alias.asname))
               elif isinstance(node, ast.ImportFrom):
                   for alias in node.names:
                       imports.add(('from', node.module, alias.name, alias.asname))
           return imports
   ```

3. **Add to pipeline**
   ```python
   from .import_normalizer import ImportNormalizer
   
   self.transformations = [
       ImportNormalizer(),  # NEW - should be first
       VariableRenamer(),
       # ...
   ]
   ```

4. **Test**
   ```python
   def test_add_missing_import():
       code = """
       class LRUCache:
           def __init__(self):
               self.cache = OrderedDict()
       """
       canon = """
       from collections import OrderedDict
       
       class LRUCache:
           def __init__(self):
               self.cache = OrderedDict()
       """
       result = ImportNormalizer().transform(code, canon)
       assert 'from collections import OrderedDict' in result
   ```

### Success Criteria
- ✅ Adds missing imports from canon
- ✅ Sorts imports consistently
- ✅ LRU Cache rescue rate reaches ~30%

---

## Phase 5: Test Improvements on Binary Search and LRU Cache 🧪

**Target**: Validate all Phase 1-4 improvements
**Complexity**: Low (1 hour)
**Impact**: Validation

### Testing Steps

1. **Re-run Binary Search experiment**
   ```bash
   python main.py --contract binary_search --runs 10 --temperature 0.7
   ```
   - Expected: R_anchor (post) = 1.000 (up from 0.500)
   - Expected: Δ_rescue = 0.600 (up from 0.100)
   - Expected: Rescue rate = 1.000 (up from 0.167)

2. **Re-run LRU Cache experiment**
   ```bash
   python main.py --contract lru_cache --runs 10 --temperature 0.7
   ```
   - Expected: R_anchor (post) = 0.400 (up from 0.100)
   - Expected: Δ_rescue = 0.300 (up from 0.000)
   - Expected: Rescue rate = 0.333 (up from 0.000)

3. **Document results**
   - Update metrics_summary.csv
   - Compare before/after rescue rates
   - Create visualization of improvements

4. **Create comparison report**
   ```markdown
   # Transformation Improvements Report
   
   ## Binary Search
   - Before: 16.7% rescue rate
   - After: 100% rescue rate
   - Improvement: +83.3 percentage points
   
   ## LRU Cache
   - Before: 0% rescue rate
   - After: 30% rescue rate
   - Improvement: +30 percentage points
   ```

### Success Criteria
- ✅ Binary Search rescue rate ≥ 90%
- ✅ LRU Cache rescue rate ≥ 25%
- ✅ All transformations working correctly

---

## Phase 6: Implement MergeStrategyNormalizer (Merge Sort - Complex) 🟡

**Target**: Merge Sort rescue rate 33% → 60%
**Complexity**: High (6-8 hours)
**Impact**: Medium

### Problem
Different merge strategies (pop-based vs index-based) create fundamentally different AST structures.

### Implementation Steps

1. **Create new transformer file**
   - Location: `src/transformations/merge_strategy_normalizer.py`

2. **Implement pattern detection**
   ```python
   class MergeStrategyNormalizer(TransformationBase):
       """Converts pop-based merge to index-based merge"""
       
       def _detect_merge_pattern(self, func_node):
           """Detect if this is a pop-based merge function"""
           # Look for: while left and right: ... left.pop(0)
           for node in ast.walk(func_node):
               if isinstance(node, ast.While):
                   # Check condition: left and right
                   if self._is_list_and_condition(node.test):
                       # Check body for pop(0) calls
                       if self._has_pop_calls(node.body):
                           return 'pop_based'
           
           # Look for: while i < len(left) and j < len(right)
           for node in ast.walk(func_node):
               if isinstance(node, ast.While):
                   if self._is_index_condition(node.test):
                       return 'index_based'
           
           return None
       
       def _transform_pop_to_index(self, func_node):
           """Transform pop-based merge to index-based"""
           # This is complex - need to:
           # 1. Add index variables (i, j = 0, 0)
           # 2. Change while condition: left and right → i < len(left) and j < len(right)
           # 3. Replace left.pop(0) with left[i]; i += 1
           # 4. Replace right.pop(0) with right[j]; j += 1
           # 5. Change remainder: left if left else right → left[i:] + right[j:]
           
           # ... implementation details ...
   ```

3. **Handle edge cases**
   - Different variable names (left/right vs l/r vs arr1/arr2)
   - Different remainder handling patterns
   - Nested merge functions

4. **Add to pipeline**
   ```python
   from .merge_strategy_normalizer import MergeStrategyNormalizer
   
   self.transformations = [
       # ...
       MergeStrategyNormalizer(),  # NEW
       # ...
   ]
   ```

5. **Test extensively**
   ```python
   def test_pop_to_index_merge():
       code = """
       def merge(left, right):
           merged = []
           while left and right:
               if left[0] <= right[0]:
                   merged.append(left.pop(0))
               else:
                   merged.append(right.pop(0))
           merged.extend(left if left else right)
           return merged
       """
       
       expected = """
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
       """
       
       result = MergeStrategyNormalizer().transform(code, expected)
       # Assert transformation is correct
   ```

### Success Criteria
- ✅ Detects pop-based merge pattern
- ✅ Transforms to index-based merge
- ✅ Merge Sort rescue rate ≥ 60%

### Note
This is the most complex transformation. Consider:
- Breaking into smaller sub-transformations
- Implementing incrementally
- May need multiple iterations to get right

---

## Phase 7: Test All Contracts and Measure Improvements 🧪

**Target**: Final validation and publication-ready metrics
**Complexity**: Low (2 hours)
**Impact**: High (deliverable)

### Testing Steps

1. **Run full experiment suite**
   ```bash
   # Test all 7 contracts at temp 0.7
   for contract in gcd binary_search merge_sort lru_cache fibonacci_basic slugify balanced_brackets; do
       python main.py --contract $contract --runs 10 --temperature 0.7
   done
   ```

2. **Generate comparison report**
   ```python
   # Create before/after comparison
   import pandas as pd
   
   before = pd.read_csv('outputs/metrics_summary_before.csv')
   after = pd.read_csv('outputs/metrics_summary.csv')
   
   comparison = pd.merge(before, after, on='contract_id', suffixes=('_before', '_after'))
   comparison['rescue_improvement'] = comparison['Delta_rescue_after'] - comparison['Delta_rescue_before']
   
   print(comparison[['contract_id', 'Delta_rescue_before', 'Delta_rescue_after', 'rescue_improvement']])
   ```

3. **Create visualization**
   - Bar chart: Rescue rates before/after
   - Table: Property coverage by contract
   - Heatmap: Transformation success by contract

4. **Document findings**
   ```markdown
   # Transformation Implementation Results
   
   ## Overall Improvements
   - Average rescue rate: 16.7% → 63.3% (+46.6pp)
   - Contracts with 100% rescue: 3 → 5
   - Property coverage: 85% → 95%
   
   ## By Contract
   | Contract | Before | After | Improvement |
   |----------|--------|-------|-------------|
   | GCD | 0% | 0% | - (already perfect) |
   | Binary Search | 16.7% | 100% | +83.3pp |
   | Merge Sort | 33.3% | 60% | +26.7pp |
   | LRU Cache | 0% | 30% | +30pp |
   | Fibonacci | 0% | 0% | - (already perfect) |
   | Slugify | 80% | 80% | - (no change) |
   | Balanced Brackets | 85.7% | 85.7% | - (no change) |
   
   ## Transformations Implemented
   1. ✅ ParameterRenamer (fixed)
   2. ✅ ArithmeticExpressionNormalizer
   3. ✅ ClassMethodReorderer
   4. ✅ ImportNormalizer
   5. ✅ MergeStrategyNormalizer
   
   ## Remaining Gaps
   - RecursionPatternNormalizer (too complex)
   - DataStructureNormalizer (too complex)
   ```

### Success Criteria
- ✅ All contracts tested
- ✅ Improvements documented
- ✅ Publication-ready metrics generated

---

## Implementation Timeline

### Week 1: Easy Wins (Phases 1-4)
- **Day 1**: Phase 1 - Fix ParameterRenamer
- **Day 2**: Phase 2 - Implement ArithmeticExpressionNormalizer
- **Day 3**: Phase 3 - Implement ClassMethodReorderer
- **Day 4**: Phase 4 - Implement ImportNormalizer
- **Day 5**: Phase 5 - Test and validate

### Week 2: Complex Transformation (Phase 6)
- **Day 1-2**: Design MergeStrategyNormalizer
- **Day 3-4**: Implement and debug
- **Day 5**: Test and refine

### Week 3: Final Validation (Phase 7)
- **Day 1**: Run full experiment suite
- **Day 2**: Generate reports and visualizations
- **Day 3**: Document findings

---

## Risk Mitigation

### High Risk: MergeStrategyNormalizer
- **Risk**: Too complex, may not work
- **Mitigation**: Implement incrementally, test each sub-transformation
- **Fallback**: Document as "future work" if infeasible

### Medium Risk: ArithmeticExpressionNormalizer
- **Risk**: May not catch all algebraic equivalences
- **Mitigation**: Start with common patterns, expand as needed
- **Fallback**: Implement only midpoint calculation pattern

### Low Risk: Other transformations
- **Risk**: Minimal - straightforward AST manipulations
- **Mitigation**: Standard testing and validation

---

## Success Metrics

### Quantitative
- ✅ Binary Search rescue rate ≥ 90%
- ✅ LRU Cache rescue rate ≥ 25%
- ✅ Merge Sort rescue rate ≥ 55%
- ✅ Average rescue rate improvement ≥ 40pp

### Qualitative
- ✅ Property coverage gaps identified and addressed
- ✅ Transformation limits documented
- ✅ Publication-ready results generated

---

## Next Steps After Implementation

1. **Write paper section** on transformation design and limits
2. **Create property coverage matrix** showing which transformers handle which properties
3. **Document transformation complexity hierarchy** (easy → hard → infeasible)
4. **Propose future research directions** for complex transformations (RecursionPatternNormalizer, DataStructureNormalizer)
