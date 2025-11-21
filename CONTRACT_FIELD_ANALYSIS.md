# Contract Field Analysis & Standardization

## Current Contract Structure Analysis

### Fields Present Across All Contracts

| Field | fibonacci_basic | fibonacci_recursive | slugify | balanced_brackets | gcd | binary_search | lru_cache | Status |
|-------|----------------|-------------------|---------|------------------|-----|---------------|-----------|---------|
| **id** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Universal |
| **task_intent** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Universal |
| **prompt** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Universal |
| **description** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Universal |
| **algorithm_family** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Universal |
| **constraints** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Universal |
| **domain** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Universal |
| **oracle_requirements** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Universal |
| **normalization_rules** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Universal |
| **out_of_domain** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | **Inconsistent** |
| **rescue_bounds** | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | **Inconsistent** |

### Constraint Fields (Nested)

| Constraint Field | Present In | Missing From |
|-----------------|-----------|--------------|
| **function_name** | fibonacci_basic, fibonacci_recursive, slugify, balanced_brackets, gcd, binary_search | lru_cache |
| **class_name** | lru_cache | All others |
| **methods** | lru_cache | All others |
| **requires_recursion** | fibonacci_basic (false), fibonacci_recursive (true), merge_sort (true) | Others |
| **implementation_style** | fibonacci_basic, fibonacci_recursive, gcd | Others |
| **output_type** | slugify, balanced_brackets, gcd, binary_search, merge_sort | Others |
| **variable_naming** | ALL | None (Universal) |

---

## 🚨 **Problems Identified**

### 1. **Missing Fields**
- `out_of_domain` missing from 5 contracts
- `rescue_bounds` missing from fibonacci_recursive
- Algorithm specification missing from ALL contracts

### 2. **Inconsistent Constraints**
- `output_type` specified for some, missing for others
- `implementation_style` only in 3 contracts
- No `required_structure` field for lru_cache (critical!)

### 3. **Underspecified Contracts**
- **lru_cache**: Doesn't specify algorithm or data structure
- **binary_search**: Doesn't specify must use binary search algorithm
- **gcd**: Doesn't specify must use Euclidean algorithm

---

## ✅ **Proposed Standard Contract Schema**

### Required Top-Level Fields (All Contracts)
```json
{
  "id": "string",                    // Unique identifier
  "task_intent": "string",           // Human-readable intent
  "prompt": "string",                // LLM prompt
  "description": "string",           // Technical description
  "algorithm_family": "string",      // Algorithm category
  "constraints": {},                 // Implementation requirements (see below)
  "domain": {},                      // Input domain specification
  "out_of_domain": {},              // Out-of-domain behavior
  "oracle_requirements": {},         // Behavioral correctness tests
  "normalization_rules": {},         // Code normalization settings
  "rescue_bounds": {}                // Transformation bounds
}
```

### Required Constraint Fields (Nested in constraints)
```json
"constraints": {
  // === For Functions ===
  "function_name": "string",         // Required function name (if function)
  
  // === For Classes ===
  "class_name": "string",            // Required class name (if class)
  "methods": ["string"],             // Required methods (if class)
  "required_classes": ["string"],    // Additional required classes (NEW)
  "required_attributes": {},         // Required attributes per class (NEW)
  
  // === Implementation Style ===
  "implementation_style": "iterative" | "recursive",
  "requires_recursion": boolean,
  
  // === Algorithm Specification (NEW - CRITICAL) ===
  "algorithm": "string",             // Specific algorithm required
  "algorithm_variant": "string",     // Variant if applicable
  
  // === Type Constraints ===
  "output_type": "string",           // Expected output type
  
  // === Variable Naming ===
  "variable_naming": {
    "fixed_variables": ["string"],
    "flexible_variables": ["string"],
    "naming_policy": "strict" | "flexible"
  }
}
```

---

## 🔧 **Proposed Contract Enhancements**

### Contract 1: **lru_cache** (CRITICAL - Underspecified)

**Current:**
```json
"constraints": {
  "class_name": "LRUCache",
  "methods": ["__init__", "get", "put"]
}
```

**Enhanced:**
```json
"constraints": {
  "class_name": "LRUCache",
  "methods": ["__init__", "get", "put"],
  "required_classes": ["Node", "LRUCache"],          // NEW
  "required_attributes": {                            // NEW
    "Node": ["key", "value", "prev", "next"],
    "LRUCache": ["capacity", "cache", "head", "tail"]
  },
  "algorithm": "doubly-linked list with hash map",   // NEW
  "implementation_style": "iterative",
  "output_type": "integer",
  "variable_naming": {
    "fixed_variables": ["capacity", "key", "value"],
    "flexible_variables": ["cache", "node", "head", "tail"],
    "naming_policy": "strict"
  }
}
```

**Add out_of_domain:**
```json
"out_of_domain": {
  "policy": "must_return",
  "return_value": -1,
  "examples": [
    {"capacity": 0},
    {"capacity": -1}
  ],
  "max_checks": 2
}
```

**Add rescue_bounds:**
```json
"rescue_bounds": {
  "allow_function_rename": false,
  "allow_class_rename": false,
  "allow_print_removal": true,
  "max_transformations": 5
}
```

---

### Contract 2: **binary_search** (Missing Algorithm Spec)

**Current:**
```json
"constraints": {
  "function_name": "binary_search",
  "output_type": "integer"
}
```

**Enhanced:**
```json
"constraints": {
  "function_name": "binary_search",
  "algorithm": "binary search",                      // NEW
  "implementation_style": "iterative",               // NEW
  "output_type": "integer",
  "variable_naming": {
    "fixed_variables": ["arr", "target"],
    "flexible_variables": ["left", "right", "mid", "l", "r", "m", "low", "high"],
    "naming_policy": "strict"
  }
}
```

**Add out_of_domain:**
```json
"out_of_domain": {
  "policy": "must_return",
  "return_value": -1,
  "examples": [
    {"arr": null, "target": 1},
    {"arr": [2, 1], "target": 1}  // Unsorted array
  ],
  "max_checks": 2
}
```

**Add rescue_bounds:**
```json
"rescue_bounds": {
  "allow_function_rename": true,
  "allow_print_removal": true,
  "max_transformations": 5
}
```

---

### Contract 3: **gcd** (Missing Algorithm Spec)

**Current:**
```json
"constraints": {
  "function_name": "gcd",
  "output_type": "integer",
  "implementation_style": "iterative"
}
```

**Enhanced:**
```json
"constraints": {
  "function_name": "gcd",
  "algorithm": "euclidean algorithm",                // NEW
  "algorithm_variant": "iterative",                  // NEW (or recursive)
  "implementation_style": "iterative",
  "output_type": "integer",
  "variable_naming": {
    "fixed_variables": ["a", "b"],
    "flexible_variables": ["temp", "remainder", "r"],
    "naming_policy": "strict"
  }
}
```

**Add out_of_domain:**
```json
"out_of_domain": {
  "policy": "must_return",
  "return_value": 0,
  "examples": [
    {"a": 0, "b": 5},
    {"a": -10, "b": 5}
  ],
  "max_checks": 3
}
```

---

### Contract 4: **slugify** (Add Missing Fields)

**Add out_of_domain:**
```json
"out_of_domain": {
  "policy": "must_return",
  "return_value": "",
  "examples": [
    {"text": null}
  ],
  "max_checks": 1
}
```

**Add algorithm:**
```json
"constraints": {
  "function_name": "slugify",
  "algorithm": "string transformation",              // NEW
  "implementation_style": "iterative",               // NEW
  "output_type": "string",
  "variable_naming": { /* existing */ }
}
```

---

### Contract 5: **balanced_brackets** (Add Missing Fields)

**Add out_of_domain:**
```json
"out_of_domain": {
  "policy": "must_return",
  "return_value": false,
  "examples": [
    {"s": null}
  ],
  "max_checks": 1
}
```

**Add algorithm:**
```json
"constraints": {
  "function_name": "is_balanced",
  "algorithm": "stack-based matching",               // NEW
  "implementation_style": "iterative",               // NEW
  "output_type": "boolean",
  "variable_naming": { /* existing */ }
}
```

---

### Contract 6: **fibonacci_recursive** (Add Missing Fields)

**Add rescue_bounds:**
```json
"rescue_bounds": {
  "allow_function_rename": true,
  "allow_print_removal": true,
  "max_transformations": 5
}
```

**Add algorithm:**
```json
"constraints": {
  "function_name": "fibonacci",
  "algorithm": "fibonacci sequence",                 // NEW
  "algorithm_variant": "recursive",                  // NEW
  "requires_recursion": true,
  "implementation_style": "recursive",
  "variable_naming": { /* existing */ }
}
```

---

## 📝 **Summary of Required Changes**

| Contract | Add out_of_domain | Add rescue_bounds | Add algorithm | Add required_classes | Add required_attributes |
|----------|------------------|------------------|---------------|---------------------|------------------------|
| fibonacci_basic | ✅ Has | ✅ Has | ⚠️ ADD | N/A | N/A |
| fibonacci_recursive | ✅ Has | ⚠️ **ADD** | ⚠️ ADD | N/A | N/A |
| slugify | ⚠️ **ADD** | ✅ Has | ⚠️ ADD | N/A | N/A |
| balanced_brackets | ⚠️ **ADD** | ✅ Has | ⚠️ ADD | N/A | N/A |
| gcd | ⚠️ **ADD** | ✅ Has | ⚠️ ADD | N/A | N/A |
| binary_search | ⚠️ **ADD** | ⚠️ **ADD** | ⚠️ ADD | N/A | N/A |
| lru_cache | ⚠️ **ADD** | ✅ Has | ⚠️ **ADD** | ⚠️ **ADD** | ⚠️ **ADD** |

---

## ✅ **Validation Benefits**

With complete contracts, the compliance checker can:

1. **lru_cache**: Distinguish doubly-linked list from simple list
2. **binary_search**: Verify binary search algorithm (not linear search)
3. **gcd**: Verify Euclidean algorithm (not brute force)
4. **All**: Consistent out_of_domain and rescue_bounds behavior

---

## 🚀 **Next Steps**

1. ✅ Review this standardization proposal
2. ⏳ Update all 7 contracts with missing fields
3. ⏳ Implement compliance checker to validate new fields
4. ⏳ Test canon selection with enhanced contracts

**Ready to proceed with contract updates?**
