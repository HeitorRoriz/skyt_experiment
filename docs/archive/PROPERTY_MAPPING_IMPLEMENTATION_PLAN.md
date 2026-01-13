# Property-to-Transformation Mapping Implementation Plan

## 📋 Overview
Replace algorithm-specific transformers with a generic property-driven system.

---

## 🆕 New Modules (6 files)

### 1. `src/transformations/property_diff_analyzer.py`
**Purpose**: Analyze property differences between code and canon  
**Responsibilities**:
- Compare two property sets
- Identify specific, actionable mismatches
- Classify mismatch types (empty_check, boolean_redundancy, etc.)
- Calculate severity/priority

**Key Classes**:
```python
@dataclass
class PropertyMismatch:
    property_name: str
    mismatch_type: str
    severity: float
    details: Dict[str, Any]

class PropertyDiffAnalyzer:
    def analyze(code_props, canon_props, code, canon_code) -> List[PropertyMismatch]
    def _analyze_logical_equivalence(...)
    def _analyze_control_flow(...)
    def _analyze_data_dependencies(...)
    def _analyze_ast_structure(...)
```

**Dependencies**: `ast`, `typing`, `dataclasses`  
**Size**: ~300 lines

---

### 2. `src/transformations/transformation_rule.py`
**Purpose**: Define transformation rule structure and AST pattern matching  
**Responsibilities**:
- Define rule schema
- AST pattern matching
- Rule application logic
- Semantic preservation validation

**Key Classes**:
```python
@dataclass
class ASTPattern:
    pattern_type: str  # "len_zero_check", "boolean_redundancy", etc.
    match_func: Callable[[ast.AST], Optional[Dict]]
    replace_func: Callable[[ast.AST, Dict], ast.AST]

@dataclass
class TransformationRule:
    rule_id: str
    property_target: str
    mismatch_pattern: str
    ast_pattern: ASTPattern
    semantic_class: str
    priority: int
    preserves_semantics: bool
    
    def matches(self, mismatch: PropertyMismatch, code_ast: ast.AST) -> bool
    def apply(self, code: str, match_details: Dict) -> str
```

**Dependencies**: `ast`, `typing`, `dataclasses`  
**Size**: ~200 lines

---

### 3. `src/transformations/transformation_registry.py`
**Purpose**: Store and query transformation rules  
**Responsibilities**:
- Register transformation rules
- Query rules by property/mismatch type
- Priority sorting
- Rule validation

**Key Classes**:
```python
class TransformationRegistry:
    def __init__(self)
    def register_rule(self, rule: TransformationRule)
    def get_rules_for_property(self, property_name: str) -> List[TransformationRule]
    def get_rules_for_mismatch(self, mismatch: PropertyMismatch) -> List[TransformationRule]
    def get_all_rules(self) -> List[TransformationRule]
    
    # Built-in rule definitions
    def _register_logical_equivalence_rules(self)
    def _register_control_flow_rules(self)
    def _register_ast_structure_rules(self)
```

**Dependencies**: `transformation_rule`, `typing`  
**Size**: ~400 lines (includes rule definitions)

---

### 4. `src/transformations/transformation_selector.py`
**Purpose**: Select applicable transformations based on property diffs  
**Responsibilities**:
- Match mismatches to rules
- Check applicability
- Priority sorting
- Conflict detection

**Key Classes**:
```python
@dataclass
class SelectedTransformation:
    rule: TransformationRule
    mismatch: PropertyMismatch
    confidence: float
    
class TransformationSelector:
    def __init__(self, registry: TransformationRegistry)
    def select(self, mismatches: List[PropertyMismatch], code: str) -> List[SelectedTransformation]
    def _check_applicability(self, rule, mismatch, code_ast) -> Optional[float]
    def _detect_conflicts(self, selections) -> List[SelectedTransformation]
    def _sort_by_priority(self, selections) -> List[SelectedTransformation]
```

**Dependencies**: `transformation_rule`, `transformation_registry`, `ast`  
**Size**: ~250 lines

---

### 5. `src/transformations/property_driven_transformer.py`
**Purpose**: Main transformer that uses property-driven approach  
**Responsibilities**:
- Orchestrate property analysis → rule selection → transformation
- Apply transformations iteratively
- Validate each transformation
- Track transformation history

**Key Classes**:
```python
class PropertyDrivenTransformer(TransformationBase):
    def __init__(self, registry: TransformationRegistry, contract: dict = None)
    def transform(self, code: str, canon_code: str) -> TransformationResult
    def _extract_properties(self, code: str) -> Dict
    def _analyze_diffs(self, code_props, canon_props, code, canon) -> List[PropertyMismatch]
    def _select_transformations(self, mismatches, code) -> List[SelectedTransformation]
    def _apply_transformation(self, code, selection) -> str
    def _validate_transformation(self, original, transformed) -> bool
```

**Dependencies**: All above modules, `TransformationBase`, `FoundationalProperties`  
**Size**: ~300 lines

---

### 6. `src/transformations/ast_patterns.py`
**Purpose**: Library of reusable AST pattern matchers and replacers  
**Responsibilities**:
- Pattern matching functions
- AST manipulation utilities
- Pattern composition
- Common transformations

**Key Functions**:
```python
# Matchers
def match_len_zero_check(node: ast.AST) -> Optional[Dict]
def match_boolean_redundancy(node: ast.AST) -> Optional[Dict]
def match_append_loop(node: ast.AST) -> Optional[Dict]
def match_string_concat_loop(node: ast.AST) -> Optional[Dict]

# Replacers
def replace_with_not(node: ast.AST, match: Dict) -> ast.AST
def replace_with_comprehension(node: ast.AST, match: Dict) -> ast.AST
def replace_with_join(node: ast.AST, match: Dict) -> ast.AST

# Utilities
def extract_variable_name(node: ast.AST) -> str
def find_pattern_in_tree(tree: ast.AST, pattern_func) -> List[Dict]
```

**Dependencies**: `ast`, `typing`  
**Size**: ~400 lines

---

## 🔧 Modified Modules (3 files)

### 1. `src/transformations/transformation_pipeline.py`
**Changes**:
- Add PropertyDrivenTransformer to default transformations
- Remove or deprecate hardcoded algorithm-specific transformers
- Update property extraction to pass to PropertyDrivenTransformer

**Modified Lines**: ~50 lines
- Line ~40-60: `_setup_default_transformations()`
- Line ~100-110: Property extraction in `transform_code()`

**Backward Compatibility**: Keep old transformers as fallback (optional flag)

---

### 2. `src/code_transformer.py`
**Changes**:
- Pass contract to PropertyDrivenTransformer
- Update initialization to include TransformationRegistry

**Modified Lines**: ~20 lines
- Line ~30-40: Pipeline initialization

**Backward Compatibility**: Fully compatible

---

### 3. `src/foundational_properties.py`
**Changes**:
- Ensure all property extractors are working (already done)
- Add helper method for property comparison

**Modified Lines**: ~30 lines (optional enhancement)
- Add `compare_properties()` method for convenience

**Backward Compatibility**: Fully compatible (only additions)

---

## 📦 Module Dependencies

```
transformation_pipeline.py
    ↓
property_driven_transformer.py
    ↓ ↓ ↓
    ↓ ↓ transformation_selector.py
    ↓ ↓     ↓
    ↓ ↓ transformation_registry.py
    ↓ ↓     ↓
    ↓ property_diff_analyzer.py
    ↓       ↓
    ↓   transformation_rule.py
    ↓       ↓
    foundational_properties.py
            ↓
        ast_patterns.py
```

**Dependency Layers**:
1. **Foundation**: `ast_patterns.py`, `foundational_properties.py`
2. **Core**: `transformation_rule.py`, `property_diff_analyzer.py`
3. **Logic**: `transformation_registry.py`, `transformation_selector.py`
4. **Interface**: `property_driven_transformer.py`
5. **Integration**: `transformation_pipeline.py`

---

## 🎯 Clean Code Principles

### 1. Single Responsibility
- Each module has ONE clear purpose
- PropertyDiffAnalyzer: ONLY analyzes diffs
- TransformationSelector: ONLY selects rules
- PropertyDrivenTransformer: ONLY orchestrates

### 2. Open/Closed Principle
- Registry is open for new rules, closed for modification
- Add new rules without changing core logic
- Pattern library is extensible

### 3. Dependency Inversion
- High-level (transformer) depends on abstractions (rules)
- Low-level (patterns) implements abstractions
- Easy to swap implementations

### 4. Interface Segregation
- Small, focused interfaces
- PropertyMismatch: just data
- TransformationRule: just rule definition
- No god objects

### 5. DRY (Don't Repeat Yourself)
- AST patterns centralized in `ast_patterns.py`
- Rule definitions in registry, not scattered
- Reusable across all algorithms

---

## 📈 Scalability

### Adding New Transformations
**Before** (algorithm-specific):
```python
# Need to create new transformer class
class SlugifySpecificTransformer(TransformationBase):
    def transform(self, code, canon):
        # Hardcoded logic for slugify
        ...
```

**After** (property-driven):
```python
# Just add a rule to registry
registry.register_rule(TransformationRule(
    rule_id="string_filter_to_regex",
    property_target="normalized_ast_structure",
    mismatch_pattern="loop_to_regex",
    ast_pattern=ASTPattern(...),
    semantic_class="string_transformation",
    priority=2
))
```

**Lines of Code**: 200+ → 10

### Supporting New Algorithms
**Before**: Write algorithm-specific transformer (200-500 lines)  
**After**: Add 2-5 rules to registry (20-50 lines)

### Handling Edge Cases
**Before**: Modify transformer logic, risk breaking other cases  
**After**: Add new rule with specific pattern, no risk to existing rules

---

## 🛡️ Robustness

### Error Handling
1. **Pattern Matching Failures**: Return None, continue to next rule
2. **AST Parse Errors**: Catch SyntaxError, return empty mismatches
3. **Transformation Failures**: Rollback, log, continue
4. **Validation Failures**: Reject transformation, try next rule

### Testing Strategy
1. **Unit Tests**: Each module independently
   - PropertyDiffAnalyzer: Test each property analyzer
   - TransformationRule: Test pattern matching
   - TransformationSelector: Test rule selection logic

2. **Integration Tests**: Full pipeline
   - Test on fibonacci (should work)
   - Test on slugify (should improve)
   - Test on balanced_brackets (should work)

3. **Regression Tests**: Existing functionality
   - Ensure Δ_rescue ≥ current values
   - Ensure no performance degradation

### Validation
- Every transformation validated by contract-aware validator
- Semantic equivalence checked
- Monotonic distance reduction verified

---

## 📊 Implementation Phases

### Phase 1: Foundation (Day 1)
**Files**: `ast_patterns.py`, `transformation_rule.py`
- Implement basic AST pattern matching
- Define rule structure
- Test pattern matchers

**Deliverable**: Pattern library with 5-10 patterns

---

### Phase 2: Analysis (Day 1-2)
**Files**: `property_diff_analyzer.py`
- Implement property comparison
- Implement mismatch detection
- Test on fibonacci/slugify examples

**Deliverable**: Analyzer that identifies 3-5 mismatch types

---

### Phase 3: Selection (Day 2)
**Files**: `transformation_registry.py`, `transformation_selector.py`
- Implement rule registry
- Implement rule selection logic
- Register 10-15 initial rules

**Deliverable**: Registry with rules for logical_equivalence, control_flow, ast_structure

---

### Phase 4: Orchestration (Day 2-3)
**Files**: `property_driven_transformer.py`
- Implement main transformer
- Integrate all components
- Add validation

**Deliverable**: Working PropertyDrivenTransformer

---

### Phase 5: Integration (Day 3)
**Files**: `transformation_pipeline.py`, `code_transformer.py`
- Integrate into existing pipeline
- Test on all three contracts
- Compare to baseline

**Deliverable**: Full system with property-driven transformations

---

### Phase 6: Evaluation (Day 3-4)
- Run experiments (fibonacci, slugify, balanced_brackets)
- Measure Δ_rescue improvement
- Identify missing rules
- Add rules as needed

**Deliverable**: Δ_rescue > 0 for all contracts

---

## 📏 Code Metrics

### New Code
- **Total Lines**: ~1,850 lines
- **Modules**: 6 new files
- **Classes**: 8 new classes
- **Functions**: ~40 new functions

### Modified Code
- **Total Lines**: ~100 lines modified
- **Modules**: 3 files
- **Breaking Changes**: 0

### Code Ratio
- **New/Modified Ratio**: 18:1 (mostly additions)
- **Reusable Code**: ~80% (patterns, rules)
- **Algorithm-Specific Code**: 0%

---

## ✅ Success Criteria

### Functional
- ✅ Δ_rescue > 0 for fibonacci (baseline: 0.200)
- ✅ Δ_rescue > 0 for slugify (baseline: 0.000) ← **Key improvement**
- ✅ Δ_rescue > 0 for balanced_brackets (baseline: 0.200)
- ✅ No algorithm-specific code in transformers
- ✅ All transformations validated by contract

### Non-Functional
- ✅ No performance degradation (< 10% slower)
- ✅ Clean architecture (all modules < 500 lines)
- ✅ High test coverage (> 80%)
- ✅ Extensible (add rule in < 20 lines)

### Quality
- ✅ No circular dependencies
- ✅ Clear separation of concerns
- ✅ Comprehensive error handling
- ✅ Well-documented (docstrings + examples)

---

## 🚀 Next Steps

1. **Review this plan** - Confirm architecture
2. **Start Phase 1** - Implement `ast_patterns.py` and `transformation_rule.py`
3. **Iterative development** - Build, test, integrate
4. **Continuous validation** - Test on real examples throughout

---

**Estimated Total Time**: 3-4 days  
**Risk Level**: Medium (new architecture, but well-defined)  
**Reversibility**: High (can keep old transformers as fallback)
