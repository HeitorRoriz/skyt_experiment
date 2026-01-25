# Property-to-Transformation Mapping System

## 🎯 Goal
Replace algorithm-specific hardcoded transformers with a generic property-driven transformation system.

## 🏗️ Architecture

### 1. Property Diff Analyzer
**Input**: Two sets of properties (code_props, canon_props)  
**Output**: List of property mismatches with severity and type

```python
PropertyMismatch(
    property_name="logical_equivalence",
    mismatch_type="boolean_expression",
    severity=0.15,  # Distance contribution
    details={
        "code_pattern": "len(stack) == 0",
        "canon_pattern": "not stack",
        "semantic_class": "empty_check"
    }
)
```

### 2. Transformation Rule Registry
**Maps property mismatches to transformation strategies**

```python
TransformationRule(
    property_target="logical_equivalence",
    mismatch_pattern="empty_check",
    ast_pattern=ASTPattern(
        match="Compare(Call(Name('len'), [target]), [Eq()], [Constant(0)])",
        replace="UnaryOp(Not(), target)"
    ),
    semantic_class="boolean_simplification",
    priority=1,
    preserves_semantics=True
)
```

### 3. Transformation Selector
**Selects applicable transformations based on property diffs**

```python
def select_transformations(property_diffs, code_ast):
    applicable = []
    for diff in property_diffs:
        rules = registry.get_rules_for_property(diff.property_name)
        for rule in rules:
            if rule.matches(diff, code_ast):
                applicable.append((rule, diff))
    return sorted(applicable, key=lambda x: x[0].priority)
```

### 4. Property-Driven Transformer
**Executes selected transformations**

```python
class PropertyDrivenTransformer(TransformationBase):
    def transform(self, code, canon_code):
        # 1. Extract properties
        code_props = extract_properties(code)
        canon_props = extract_properties(canon_code)
        
        # 2. Analyze differences
        diffs = analyze_property_diffs(code_props, canon_props)
        
        # 3. Select transformations
        transformations = select_transformations(diffs, code)
        
        # 4. Apply transformations
        for rule, diff in transformations:
            code = rule.apply(code, diff.details)
        
        return code
```

## 📋 Property-to-Transformation Mappings

### Logical Equivalence
| Mismatch Pattern | AST Pattern | Transformation | Semantic Class |
|-----------------|-------------|----------------|----------------|
| `len(x) == 0` | `Compare(Call(len), Eq, 0)` | `not x` | empty_check |
| `len(x) > 0` | `Compare(Call(len), Gt, 0)` | `x` | non_empty_check |
| `x == True` | `Compare(x, Eq, True)` | `x` | boolean_redundancy |
| `x == False` | `Compare(x, Eq, False)` | `not x` | boolean_redundancy |

### Control Flow Signature
| Mismatch Pattern | AST Pattern | Transformation | Semantic Class |
|-----------------|-------------|----------------|----------------|
| Extra if-else | `If(test, [Return(x)], [Return(y)])` | `Return(x if test else y)` | ternary_simplification |
| Nested loops | Multiple `For` nodes | Merge if independent | loop_fusion |
| Early return | `If(...): return` at end | Remove if redundant | dead_code_elimination |

### Data Dependency Graph
| Mismatch Pattern | AST Pattern | Transformation | Semantic Class |
|-----------------|-------------|----------------|----------------|
| Variable rename | Different var names, same deps | Rename to canon | variable_normalization |
| Temp variable | Extra assignment | Inline if single-use | temp_elimination |

### Statement Ordering
| Mismatch Pattern | AST Pattern | Transformation | Semantic Class |
|-----------------|-------------|----------------|----------------|
| Commutative ops | `a + b` vs `b + a` | Canonicalize order | commutative_normalization |
| Independent stmts | Reorderable statements | Sort by canonical order | statement_reordering |

### Normalized AST Structure
| Mismatch Pattern | AST Pattern | Transformation | Semantic Class |
|-----------------|-------------|----------------|----------------|
| List comp vs loop | `for x in y: if c: l.append(x)` | `[x for x in y if c]` | comprehension_conversion |
| String concat | `s += char` in loop | `''.join(...)` | string_building |
| Dict lookup | `if k in d: v = d[k]` | `v = d.get(k)` | dict_idiom |

## 🔄 Transformation Pipeline Integration

### Current Flow
```
Code → [Transformer1, Transformer2, ...] → Transformed Code
         ↑ Hardcoded, algorithm-specific
```

### New Flow
```
Code + Canon → Property Diff Analyzer → Property Mismatches
                                              ↓
                                    Transformation Selector
                                              ↓
                                    [Rule1, Rule2, ...]
                                              ↓
                                    Property-Driven Transformer
                                              ↓
                                    Transformed Code
```

## 🎯 Benefits

1. **No Algorithm-Specific Code**
   - Rules are pattern-based, not algorithm-based
   - Works for fibonacci, slugify, any algorithm

2. **Property-Guided**
   - Transformations directly address property mismatches
   - Measurable progress toward canon

3. **Composable**
   - Small, focused transformation rules
   - Combine to handle complex differences

4. **Extensible**
   - Add new rules without modifying core system
   - Rules can be learned or generated

5. **Validated**
   - Each rule preserves semantics
   - Contract-aware validation ensures correctness

## 🚀 Implementation Plan

### Phase 1: Core Infrastructure
1. `PropertyDiffAnalyzer` - Compare properties, identify mismatches
2. `TransformationRule` - Define rule structure
3. `TransformationRegistry` - Store and query rules

### Phase 2: Rule Library
1. Logical equivalence rules (boolean simplification)
2. Control flow rules (ternary, early return)
3. Data dependency rules (variable renaming)
4. AST structure rules (comprehensions, string building)

### Phase 3: Integration
1. Replace hardcoded transformers with PropertyDrivenTransformer
2. Integrate with existing validation pipeline
3. Test on fibonacci, slugify, balanced_brackets

### Phase 4: Evaluation
1. Measure Δ_rescue improvement
2. Compare to hardcoded approach
3. Identify missing rules from failures

## 📊 Success Metrics

- ✅ Δ_rescue > 0 for all three contracts (fibonacci, slugify, balanced_brackets)
- ✅ No algorithm-specific code in transformers
- ✅ Rules are reusable across algorithms
- ✅ System handles new algorithms without modification

---
**Status**: Design complete, ready for implementation  
**Next**: Implement PropertyDiffAnalyzer
