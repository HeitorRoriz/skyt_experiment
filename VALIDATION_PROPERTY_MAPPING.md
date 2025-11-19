# SKYT Validation Architecture: Property Mapping & Integration Plan

## Executive Summary

This document maps SKYT's **current 13 foundational properties** (AST-based) to the **proposed 5-layer validation architecture**, showing how each validation layer enhances existing properties and what new capabilities emerge.

**Key Insight:** Current properties provide syntactic structure; new layers add semantic depth, behavioral validation, and formal correctness guarantees.

---

## Current State: 13 Foundational Properties (AST-Only)

```python
# src/foundational_properties.py
self.properties = [
    "control_flow_signature",        # ✓ Branches, loops, calls
    "data_dependency_graph",         # ✓ Variable dependencies
    "execution_paths",               # ✓ Path topology
    "function_contracts",            # ⚠️  Args only, no type info
    "complexity_class",              # ⚠️  Rough estimate (nested loops)
    "side_effect_profile",           # ⚠️  Shallow (print detection only)
    "termination_properties",        # ⚠️  Pattern-based, not proven
    "algebraic_structure",           # ✓ Commutative/associative ops
    "numerical_behavior",            # ⚠️  Constants only, no overflow
    "logical_equivalence",           # ⚠️  Patterns, not SAT-level
    "normalized_ast_structure",      # ✓ α-renaming
    "operator_precedence",           # ✓ Precedence levels
    "statement_ordering",            # ✓ Statement sequence
    "recursion_schema"              # ✓ Base cases, recursive calls
]
```

**Legend:**
- ✓ = Strong (syntactically complete)
- ⚠️  = Weak (limited to patterns, missing semantic depth)

---

## Mapping: Current Properties → Enhanced Validation Layers

### Property 1: `control_flow_signature`

**Current (AST-Only):**
```python
{
  "if_statements": 2,
  "for_loops": 1,
  "while_loops": 0,
  "function_calls": ["fibonacci"],
  "nested_depth": 2
}
```

**Limitations:**
- ❌ Doesn't detect unreachable code
- ❌ Doesn't detect infinite loops
- ❌ Doesn't compute cyclomatic complexity accurately

**Enhanced with Layer 2 (CFG + Data Flow):**
```python
# Add CFG-based analysis
class EnhancedControlFlow:
    def build_cfg(self, tree: ast.AST) -> ControlFlowGraph:
        """Build explicit control flow graph"""
        
    def detect_unreachable_code(self, cfg: CFG) -> List[ast.AST]:
        """DFS from entry, mark unreachable blocks"""
        
    def compute_cyclomatic_complexity(self, cfg: CFG) -> int:
        """McCabe: M = E - N + 2P"""
        
    def find_infinite_loops(self, cfg: CFG) -> List[ast.While]:
        """Loops without exit conditions or decreasing measures"""
```

**Enhanced with Layer 3 (Static Analysis):**
```python
# Add radon complexity metrics
from radon.complexity import cc_visit

complexity_report = cc_visit(code)
# Returns: rank, complexity, methods, etc.
```

**Result:**
```python
{
  # Original
  "if_statements": 2,
  "nested_depth": 2,
  
  # NEW: CFG analysis
  "unreachable_blocks": [],
  "infinite_loops": [],
  "cyclomatic_complexity": 5,
  "essential_complexity": 3,
  
  # NEW: Static analysis
  "cognitive_complexity": 7,
  "maintainability_index": 72.5,
  "halstead_metrics": {...}
}
```

---

### Property 2: `data_dependency_graph`

**Current (AST-Only):**
```python
{
  "dependencies": {
    "result": ["n", "fibonacci"],
    "a": ["b"]
  },
  "assignments": {...}
}
```

**Limitations:**
- ❌ Doesn't detect use-before-definition
- ❌ Doesn't track dead stores
- ❌ No def-use chains

**Enhanced with Layer 2 (Data Flow Analysis):**
```python
class DataFlowAnalyzer:
    def compute_def_use_chains(self, cfg: CFG) -> Dict:
        """For each variable, track all definitions and uses"""
        
    def find_uninitialized_variables(self) -> List[str]:
        """Variables used before any definition"""
        
    def detect_dead_stores(self) -> List[ast.Assign]:
        """Assignments to variables never read"""
        
    def analyze_liveness(self, cfg: CFG) -> Dict:
        """Live variables at each program point"""
```

**Result:**
```python
{
  # Original
  "dependencies": {...},
  
  # NEW: Data flow
  "def_use_chains": {
    "n": {
      "definitions": [("line_2", "parameter")],
      "uses": [("line_3", "condition"), ("line_5", "call")]
    }
  },
  "uninitialized_vars": [],
  "dead_stores": ["temp at line 10"],
  "live_ranges": {...}
}
```

---

### Property 3: `function_contracts`

**Current (AST-Only):**
```python
{
  "fibonacci": {
    "name": "fibonacci",
    "args": ["n"],
    "returns": None,  # ← No type info!
    "has_return": True
  }
}
```

**Limitations:**
- ❌ No type information
- ❌ Can't detect type errors
- ❌ No precondition/postcondition verification

**Enhanced with Layer 3 (Type Checking):**
```python
# Use mypy for type inference
import subprocess
import json

class TypeChecker:
    def infer_function_signature(self, func_def: ast.FunctionDef) -> Signature:
        """
        Run mypy to infer types even without annotations
        """
        # mypy can infer: fibonacci(int) -> int
        
    def check_type_consistency(self, code: str) -> List[TypeError]:
        """
        Detect:
        - Return type mismatches
        - Argument type mismatches
        - Operation on incompatible types
        """
```

**Enhanced with Layer 4 (Symbolic Execution):**
```python
# Use Z3 for contract verification
class ContractVerifier:
    def verify_preconditions(self, func, contract: Contract) -> bool:
        """
        Prove: ∀ inputs satisfying precondition → function doesn't crash
        """
        
    def verify_postconditions(self, func, contract: Contract) -> bool:
        """
        Prove: ∀ valid inputs → output satisfies postcondition
        """
```

**Result:**
```python
{
  # Original
  "name": "fibonacci",
  "args": ["n"],
  
  # NEW: Type checking
  "inferred_signature": "fibonacci(n: int) -> int",
  "type_errors": [],
  
  # NEW: Contract verification
  "precondition_verified": True,  # n >= 0
  "postcondition_verified": True, # result >= 0
  "contract_holds": True
}
```

---

### Property 4: `complexity_class`

**Current (AST-Only):**
```python
{
  "nested_loops": 0,
  "recursive_calls": 5,
  "estimated_complexity": "O(2^n)"  # ← Heuristic!
}
```

**Limitations:**
- ❌ Rough heuristic (nested loops → O(n²))
- ❌ Doesn't analyze recurrence relations
- ❌ Can't prove tight bounds

**Enhanced with Layer 4 (Symbolic Execution):**
```python
class ComplexityAnalyzer:
    def analyze_recurrence(self, func: ast.FunctionDef) -> str:
        """
        Symbolic analysis of recursive structure:
        - T(n) = T(n-1) + T(n-2) + O(1) → T(n) = Θ(φ^n)
        - T(n) = 2T(n/2) + O(n) → T(n) = Θ(n log n)
        """
        
    def prove_complexity_bound(self, func, bound: str) -> Proof:
        """
        Use Z3 to prove complexity claim
        Example: Prove fibonacci is O(2^n), not O(n)
        """
```

**Result:**
```python
{
  # Original
  "nested_loops": 0,
  "recursive_calls": 5,
  
  # NEW: Precise analysis
  "recurrence_relation": "T(n) = T(n-1) + T(n-2) + O(1)",
  "exact_complexity": "Θ(φ^n) where φ ≈ 1.618",
  "complexity_proof": "verified",
  "space_complexity": "O(n)"  # Call stack depth
}
```

---

### Property 5: `side_effect_profile`

**Current (AST-Only):**
```python
{
  "has_print": False,
  "has_global_access": False,
  "has_file_io": False,
  "is_pure": True
}
```

**Limitations:**
- ❌ Only checks for obvious patterns (print, open)
- ❌ Doesn't track mutation of arguments
- ❌ Doesn't detect network calls, system calls

**Enhanced with Layer 3 (Static Analysis):**
```python
# Use bandit for security/side-effect analysis
from bandit.core import manager

class SideEffectAnalyzer:
    def detect_all_side_effects(self, code: str) -> SideEffectReport:
        """
        Detect:
        - File I/O (open, read, write)
        - Network calls (requests, urllib)
        - System calls (os.system, subprocess)
        - Environment access (os.environ)
        - Argument mutation
        """
```

**Enhanced with Layer 5 (Dynamic Taint Analysis):**
```python
class TaintAnalyzer:
    def trace_data_flow(self, code: str) -> TaintReport:
        """
        Run code with instrumentation, track:
        - Where inputs flow
        - What gets modified
        - What gets written/sent
        """
```

**Result:**
```python
{
  # Original
  "has_print": False,
  "is_pure": True,
  
  # NEW: Comprehensive analysis
  "side_effects": [],
  "mutates_arguments": False,
  "accesses_globals": [],
  "io_operations": [],
  "network_calls": [],
  "purity_level": "referentially_transparent"
}
```

---

### Property 6: `termination_properties`

**Current (AST-Only):**
```python
{
  "has_base_case": True,
  "has_bounded_loops": False,
  "recursive_depth": 0
}
```

**Limitations:**
- ❌ Pattern matching only (looks for `if + return`)
- ❌ Doesn't prove termination
- ❌ Can't verify loop bounds

**Enhanced with Layer 4 (Symbolic Execution):**
```python
class TerminationVerifier:
    def find_ranking_function(self, loop: ast.While) -> Optional[str]:
        """
        Find a measure that decreases on each iteration
        Example: n → n-1 (for countdown loops)
        """
        
    def prove_termination(self, func: ast.FunctionDef) -> TerminationProof:
        """
        Use Z3 to prove:
        - All recursive calls decrease some measure
        - All loops have bounded iterations
        """
```

**Result:**
```python
{
  # Original
  "has_base_case": True,
  
  # NEW: Formal verification
  "termination_proven": True,
  "ranking_function": "n (decreases by 1 each call)",
  "max_recursion_depth": "n",
  "loops_verified_bounded": True,
  "potential_infinite_loops": []
}
```

---

### Property 7: `logical_equivalence`

**Current (AST-Only):**
```python
{
  "boolean_ops": ["And", "Or"],
  "comparisons": ["Gt", "LtE"],
  "logical_patterns": []
}
```

**Limitations:**
- ❌ Doesn't normalize boolean expressions
- ❌ Can't detect equivalent conditions (e.g., `not (a and b)` ≡ `(not a) or (not b)`)

**Enhanced with Layer 4 (SMT Solver):**
```python
from z3 import *

class LogicalEquivalenceChecker:
    def normalize_boolean_expr(self, expr: ast.BoolOp) -> str:
        """
        Convert to CNF/DNF for canonical comparison
        """
        
    def prove_equivalence(self, expr1: ast.BoolOp, expr2: ast.BoolOp) -> bool:
        """
        Use Z3 to prove: ∀ vars → expr1 ≡ expr2
        Example: (a and b) ≡ (b and a)
        """
```

**Result:**
```python
{
  # Original
  "boolean_ops": ["And"],
  
  # NEW: Semantic equivalence
  "normalized_cnf": "((n > 0) ∧ (n <= 10))",
  "equivalent_to_canonical": True,
  "equivalence_proof": "verified"
}
```

---

### Property 8: `normalized_ast_structure`

**Current (AST-Only):**
```python
{
  "ast_hash": "abc123...",
  "alpha_renamed_hash": "def456..."  # ✓ Good!
}
```

**Strengths:**
- ✓ α-renaming already implemented
- ✓ Variable-name-agnostic comparison

**Enhancement Needed:**
- Add contract-aware α-renaming (respect `naming_policy`)

**Enhanced Version:**
```python
def _should_use_alpha_renaming(self, contract: Contract) -> bool:
    """
    Respect contract naming policy:
    - "strict": Never rename (firmware/embedded)
    - "flexible": Allow renaming
    """
    policy = contract.get("variable_naming", {}).get("naming_policy", "flexible")
    return policy == "flexible"
```

**Result:** Already strong, minor contract-aware tweaks needed.

---

## New Properties Enabled by Enhanced Validation

### NEW Property 9: `type_consistency`

```python
{
  "type_errors": [],
  "inferred_types": {
    "n": "int",
    "result": "int"
  },
  "type_coverage": 1.0,  # 100% of expressions typed
  "polymorphic_calls": []
}
```

**Enabled by:** Layer 3 (mypy/pyright)

---

### NEW Property 10: `security_profile`

```python
{
  "vulnerabilities": [],
  "security_issues": [],
  "hardcoded_secrets": [],
  "injection_risks": [],
  "unsafe_patterns": []
}
```

**Enabled by:** Layer 3 (bandit)

---

### NEW Property 11: `formal_correctness`

```python
{
  "contract_verified": True,
  "preconditions_hold": True,
  "postconditions_hold": True,
  "invariants_maintained": True,
  "termination_proven": True
}
```

**Enabled by:** Layer 4 (Z3 symbolic execution)

---

### NEW Property 12: `behavioral_equivalence`

```python
{
  "io_signature": "abc123...",
  "property_tests_passed": 100,
  "mutation_score": 0.95,  # 95% of mutants killed by oracle
  "oracle_quality": "high"
}
```

**Enabled by:** Layer 5 (hypothesis + mutation testing)

---

## Integration Architecture

### Phase 1: Extend Existing Properties (Weeks 1-2)

```python
# src/foundational_properties.py

class FoundationalProperties:
    def __init__(self, contract, validation_config):
        self.contract = contract
        self.config = validation_config
        
        # NEW: Optional validators
        self.type_checker = TypeChecker() if config.enable_type_checking else None
        self.static_analyzer = StaticAnalyzer() if config.enable_static_analysis else None
        
    def extract_all_properties(self, code: str) -> Dict[str, Any]:
        """
        Extract properties with configurable validation layers
        """
        properties = {}
        
        # Layer 1: AST (always enabled)
        properties.update(self._extract_ast_properties(code))
        
        # Layer 2: CFG + Data Flow (optional)
        if self.config.enable_cfg_analysis:
            cfg = self.build_cfg(code)
            properties.update(self._extract_cfg_properties(cfg))
            properties.update(self._extract_dataflow_properties(cfg))
        
        # Layer 3: Static Analysis (optional)
        if self.config.enable_static_analysis:
            properties.update(self._extract_static_properties(code))
        
        # Layer 4: Symbolic Execution (expensive, opt-in)
        if self.config.enable_symbolic_execution:
            properties.update(self._extract_symbolic_properties(code))
        
        # Layer 5: Behavioral Testing (expensive, opt-in)
        if self.config.enable_property_testing:
            properties.update(self._extract_behavioral_properties(code))
        
        return properties
```

### Phase 2: New Validation Modules (Weeks 3-4)

```
src/validation/
├── __init__.py
├── cfg_builder.py           # Control flow graphs
├── dataflow_analyzer.py     # Def-use chains, liveness
├── type_checker.py          # mypy integration
├── static_analyzer.py       # pylint + bandit + radon
├── symbolic_executor.py     # Z3 integration
└── property_tester.py       # hypothesis integration
```

### Phase 3: Contract Schema Extension (Week 3)

```json
{
  "contract_id": "fibonacci_basic",
  "validation": {
    "layers": {
      "ast": {"enabled": true},
      "cfg": {"enabled": true},
      "static": {
        "enabled": true,
        "max_complexity": 10,
        "security_level": "strict"
      },
      "type_checking": {
        "enabled": true,
        "strict": true
      },
      "symbolic": {
        "enabled": false,  // Expensive
        "max_paths": 100
      },
      "behavioral": {
        "enabled": true,
        "property_tests": 100
      }
    },
    "properties_required": [
      "control_flow_signature",
      "type_consistency",
      "security_profile",
      "behavioral_equivalence"
    ]
  }
}
```

---

## Implementation Priority

### Quick Wins (Weeks 1-2): 70% Impact, Low Effort

**Add to existing properties:**

1. **`control_flow_signature`** → Add radon complexity
   ```python
   from radon.complexity import cc_visit
   complexity = cc_visit(code)
   properties["cyclomatic_complexity"] = complexity[0].complexity
   ```

2. **`function_contracts`** → Add mypy type inference
   ```python
   type_info = self.type_checker.infer_signature(func_def)
   properties["inferred_signature"] = type_info
   ```

3. **`side_effect_profile`** → Add bandit security scan
   ```python
   security_report = self.static_analyzer.scan_security(code)
   properties["security_issues"] = security_report.issues
   ```

**Estimated Effort:** 1-2 weeks  
**Impact:** Catches 70% of issues AST alone misses

---

### High Value (Weeks 3-4): CFG + Data Flow

**New modules:**

4. **CFG Builder** → Enable unreachable code detection
5. **Data Flow Analyzer** → Detect use-before-def, dead stores

**Estimated Effort:** 2 weeks  
**Impact:** Semantic understanding for better canonicalization

---

### Research-Grade (Weeks 5-8): Symbolic + Behavioral

**Advanced features:**

6. **Z3 Integration** → Formal correctness proofs
7. **Property Testing** → Oracle quality measurement

**Estimated Effort:** 4 weeks  
**Impact:** Publishable novelty, formal guarantees

---

## Configuration: Tiered Validation Modes

```python
# src/validation/config.py

VALIDATION_MODES = {
    "fast": {
        "layers": ["ast"],
        "timeout": 1.0  # 1 second
    },
    "standard": {
        "layers": ["ast", "static"],
        "timeout": 5.0  # 5 seconds
    },
    "thorough": {
        "layers": ["ast", "cfg", "static", "type"],
        "timeout": 30.0  # 30 seconds
    },
    "research": {
        "layers": ["ast", "cfg", "static", "type", "symbolic", "behavioral"],
        "timeout": 300.0  # 5 minutes
    }
}
```

**User-facing:**
```bash
# CLI
skyt run --contract fibonacci --validation-mode thorough

# API
POST /api/v1/pipeline/run
{
  "contract_id": "fibonacci",
  "validation_mode": "standard"
}
```

---

## Benefits: Before vs After

| Property | Before (AST-Only) | After (Multi-Layer) |
|----------|-------------------|---------------------|
| Control Flow | Counts branches | Detects unreachable code, proves complexity |
| Data Flow | Lists dependencies | Detects use-before-def, dead stores |
| Function Contracts | Args only | Full type signatures + verification |
| Termination | Pattern-based | Formally proven |
| Side Effects | Print detection | Comprehensive (I/O, network, mutation) |
| Logical Equivalence | Pattern matching | SAT-level proofs |
| **NEW:** Type Consistency | N/A | Full type checking |
| **NEW:** Security | N/A | CVE detection, injection risks |
| **NEW:** Formal Correctness | N/A | Contract verification |
| **NEW:** Behavioral Equivalence | N/A | Property-based testing |

---

## Open Questions

1. **Performance:** How much overhead do validation layers add?
2. **Caching:** Can we cache validation results by code hash?
3. **User Choice:** Default mode = "standard", or let users choose?
4. **Research vs Production:** Symbolic execution too expensive for production?
5. **Contract Schema:** Add per-property validation configs?

---

## Next Steps

1. **Review this mapping** with team
2. **Prototype Phase 1** (radon + mypy + bandit)
3. **Benchmark** validation overhead
4. **User testing** with validation modes
5. **Iterate** based on performance data

---

**Document Version:** 1.0  
**Date:** 2025-11-19  
**Author:** SKYT Validation Team  
**Status:** Ready for Implementation
