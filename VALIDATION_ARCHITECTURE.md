# SKYT Validation Architecture: Beyond AST

## Problem Statement

**Current limitation:** SKYT relies solely on AST (Abstract Syntax Tree) analysis, which only captures **syntactic structure**, not semantic meaning or behavioral properties.

**AST cannot detect:**
- Type errors (calling `len()` on an integer)
- Control flow issues (unreachable code, infinite loops)
- Data flow problems (using uninitialized variables)
- Security vulnerabilities (SQL injection patterns)
- Runtime behavior (exception handling correctness)
- Semantic equivalence (different algorithms solving same problem)

**Goal:** Build a multi-layered validation system that provides **syntactic, semantic, behavioral, and quality-based** analysis.

---

## Proposed Architecture: 5-Layer Validation Stack

```
┌─────────────────────────────────────────────────┐
│  Layer 5: Behavioral Validation                 │
│  (Runtime contracts, property-based testing)    │
└─────────────────────────────────────────────────┘
                     ▲
┌─────────────────────────────────────────────────┐
│  Layer 4: Semantic Analysis                     │
│  (Type checking, control/data flow analysis)    │
└─────────────────────────────────────────────────┘
                     ▲
┌─────────────────────────────────────────────────┐
│  Layer 3: Static Analysis                       │
│  (Code quality, complexity, security)           │
└─────────────────────────────────────────────────┘
                     ▲
┌─────────────────────────────────────────────────┐
│  Layer 2: Enhanced AST Analysis                 │
│  (Control Flow Graphs, Program Slicing)         │
└─────────────────────────────────────────────────┘
                     ▲
┌─────────────────────────────────────────────────┐
│  Layer 1: Syntactic (Current)                   │
│  (AST parsing, structural comparison)           │
└─────────────────────────────────────────────────┘
```

---

## Layer 1: Enhanced AST Analysis (Build on Current)

### What to Add:

**Control Flow Graphs (CFG)**
```python
# src/validation/cfg_analyzer.py
import ast
from typing import Dict, Set, List

class ControlFlowGraph:
    """Build CFG from AST for control flow analysis"""
    
    def __init__(self, tree: ast.AST):
        self.nodes: Dict[int, "CFGNode"] = {}
        self.entry_node: "CFGNode" = None
        self.exit_nodes: Set["CFGNode"] = set()
        
    def detect_unreachable_code(self) -> List[ast.AST]:
        """Find code blocks never executed"""
        
    def find_infinite_loops(self) -> List[ast.While | ast.For]:
        """Detect loops without termination conditions"""
        
    def compute_cyclomatic_complexity(self) -> int:
        """McCabe complexity metric"""
```

**Program Slicing**
```python
# src/validation/program_slicer.py
class ProgramSlicer:
    """Extract code affecting specific variables/statements"""
    
    def backward_slice(self, var_name: str, line: int) -> Set[ast.AST]:
        """Find all code affecting var_name at line"""
        
    def forward_slice(self, var_name: str, line: int) -> Set[ast.AST]:
        """Find all code affected by var_name at line"""
```

**Tools:** Python's `ast` module + custom graph algorithms

---

## Layer 2: Static Analysis & Code Quality

### Tools to Integrate:

**1. pylint** - Comprehensive code quality
```python
# src/validation/static_analyzer.py
from pylint.lint import Run
from pylint.reporters.json_reporter import JSONReporter

class StaticAnalyzer:
    def analyze_code(self, code: str) -> "StaticAnalysisReport":
        """Run pylint, return structured violations"""
        results = Run([code], reporter=JSONReporter(), exit=False)
        return self._parse_violations(results)
```

**2. bandit** - Security analysis
```python
class SecurityAnalyzer:
    def scan_for_vulnerabilities(self, code: str) -> List["SecurityIssue"]:
        """Detect SQL injection, hardcoded secrets, etc."""
```

**3. radon** - Complexity metrics
```python
class ComplexityAnalyzer:
    def compute_metrics(self, code: str) -> "ComplexityReport":
        """
        Returns:
        - Cyclomatic complexity (CC)
        - Cognitive complexity
        - Halstead metrics
        - Maintainability index
        """
```

**Integration:**
```python
# src/core/interfaces.py
class StaticAnalyzer(Protocol):
    def analyze(self, code: str) -> "AnalysisReport": ...

# Configuration in contract
{
  "validation_rules": {
    "max_cyclomatic_complexity": 10,
    "max_cognitive_complexity": 15,
    "security_level": "strict",
    "allowed_violations": []
  }
}
```

---

## Layer 3: Semantic Analysis (Type Checking & Data Flow)

### 1. Static Type Checking

**Use mypy or pyright for type inference:**
```python
# src/validation/type_checker.py
import subprocess
import json
from typing import List

class TypeChecker:
    def check_types(self, code: str) -> "TypeCheckReport":
        """
        Run mypy on code, return type errors
        Even without annotations, mypy infers types
        """
        # Write code to temp file with .py extension
        # Run: mypy --show-error-codes --json <file>
        # Parse JSON output
        
    def infer_function_signature(self, func: ast.FunctionDef) -> "Signature":
        """Infer parameter and return types"""
```

**Example Detection:**
```python
# Code 1
def fibonacci(n):
    if n <= 0:
        return 0
    return fibonacci(n-1) + fibonacci(n-2)

# Code 2
def fibonacci(n):
    if n <= 0:
        return "zero"  # ← Type error! Returns str sometimes
    return fibonacci(n-1) + fibonacci(n-2)
```

**AST can't detect this, but mypy can!**

### 2. Control Flow Analysis

```python
# src/validation/control_flow_analyzer.py
class ControlFlowAnalyzer:
    def __init__(self, cfg: ControlFlowGraph):
        self.cfg = cfg
        
    def find_unreachable_code(self) -> List[ast.AST]:
        """DFS from entry, mark unreachable nodes"""
        
    def detect_missing_return_paths(self) -> List[ast.FunctionDef]:
        """Functions with branches that don't return"""
        
    def validate_exception_handling(self) -> List["ExceptionIssue"]:
        """
        - Bare except clauses
        - Catching too broad exceptions
        - Swallowing exceptions
        """
```

### 3. Data Flow Analysis

```python
# src/validation/data_flow_analyzer.py
class DataFlowAnalyzer:
    def compute_def_use_chains(self, cfg: ControlFlowGraph) -> Dict[str, List]:
        """For each variable, track definitions and uses"""
        
    def find_uninitialized_variables(self) -> List[str]:
        """Variables used before definition"""
        
    def detect_dead_stores(self) -> List[ast.Assign]:
        """Variables assigned but never used"""
        
    def analyze_variable_scope(self) -> "ScopeReport":
        """Variable shadowing, scope violations"""
```

**Example:**
```python
def buggy_code(n):
    if n > 0:
        result = n * 2
    # result might not be defined here! ← Data flow analysis catches this
    return result
```

---

## Layer 4: Symbolic Execution & Formal Methods

### 1. Symbolic Execution (Path Exploration)

```python
# src/validation/symbolic_executor.py
from z3 import *

class SymbolicExecutor:
    """Execute code symbolically to explore all paths"""
    
    def explore_paths(self, func: ast.FunctionDef, max_depth: int = 5) -> List["Path"]:
        """
        Generate symbolic inputs to explore all execution paths
        Useful for detecting:
        - Division by zero
        - Array out of bounds
        - Assertion failures
        """
        
    def generate_test_inputs(self, func: ast.FunctionDef) -> List[Dict]:
        """Generate inputs that cover all branches"""
```

**Use Case: Equivalence Checking**
```python
# Prove two implementations are equivalent
def are_equivalent(code1: str, code2: str, func_name: str) -> bool:
    """
    Use Z3 to prove:
    ∀ inputs: func1(inputs) == func2(inputs)
    """
```

### 2. SMT Solvers (Z3 Integration)

```python
# src/validation/smt_verifier.py
class SMTVerifier:
    def verify_contract(self, code: str, contract: "Contract") -> bool:
        """
        Verify contract properties using SMT solver:
        - Preconditions → Postconditions
        - Loop invariants
        - Function contracts
        """
        
    def prove_equivalence(self, impl1: str, impl2: str) -> "EquivalenceProof":
        """Formal proof of semantic equivalence"""
```

**Example:**
```python
# Contract: fibonacci(n) where n >= 0 returns non-negative int
# SMT can prove: ∀n ≥ 0 → fibonacci(n) ≥ 0
```

---

## Layer 5: Behavioral Validation (Runtime)

### 1. Property-Based Testing

```python
# src/validation/property_tester.py
from hypothesis import given, strategies as st

class PropertyTester:
    """Use Hypothesis for property-based testing"""
    
    def test_contract_properties(self, func, contract: "Contract"):
        """
        Generate random inputs, verify:
        - Preconditions respected
        - Postconditions satisfied
        - Invariants maintained
        """
        
    @given(st.integers(min_value=0, max_value=100))
    def test_fibonacci_properties(self, n):
        """Example: Test fibonacci invariants"""
        result = fibonacci(n)
        assert result >= 0
        if n > 1:
            assert result == fibonacci(n-1) + fibonacci(n-2)
```

### 2. Dynamic Taint Analysis

```python
# src/validation/taint_analyzer.py
class TaintAnalyzer:
    """Track data flow at runtime for security"""
    
    def trace_tainted_data(self, code: str, taint_sources: List[str]):
        """
        Mark inputs as 'tainted'
        Track if tainted data reaches sensitive sinks
        Example: User input → SQL query (injection risk)
        """
```

### 3. Mutation Testing

```python
# src/validation/mutation_tester.py
class MutationTester:
    """Verify oracle quality by mutating code"""
    
    def generate_mutants(self, code: str) -> List[str]:
        """
        Create mutations:
        - Change operators (+ → -)
        - Modify constants (0 → 1)
        - Remove statements
        """
        
    def test_oracle_quality(self, oracle: "Oracle", mutants: List[str]) -> float:
        """
        Mutation score = % of mutants detected by oracle
        High score = good oracle
        """
```

---

## Integration Architecture

### Validation Pipeline

```python
# src/validation/validation_pipeline.py
from typing import Protocol

class Validator(Protocol):
    def validate(self, code: str, contract: "Contract") -> "ValidationReport": ...

class ValidationPipeline:
    def __init__(self, validators: List[Validator]):
        self.validators = validators
        
    def validate_code(self, code: str, contract: "Contract") -> "AggregateReport":
        """
        Run all validators in sequence:
        1. AST parse
        2. Static analysis (pylint, bandit, radon)
        3. Type checking (mypy)
        4. CFG + data flow analysis
        5. Symbolic execution (optional, expensive)
        6. Property-based tests
        
        Return aggregate report with all findings
        """
        reports = []
        for validator in self.validators:
            report = validator.validate(code, contract)
            reports.append(report)
            if report.is_fatal:
                break  # Stop on fatal errors
        return AggregateReport(reports)
```

### Contract Extensions

```json
{
  "contract_id": "fibonacci_basic",
  "validation": {
    "layers": ["ast", "static", "type", "dataflow", "symbolic"],
    "static_analysis": {
      "max_complexity": 10,
      "security_level": "strict",
      "ignore_warnings": ["missing-docstring"]
    },
    "type_checking": {
      "strict": true,
      "infer_types": true
    },
    "symbolic_execution": {
      "max_paths": 100,
      "timeout_seconds": 10
    },
    "properties": [
      {
        "name": "non_negative_output",
        "expression": "∀n ≥ 0 → fibonacci(n) ≥ 0"
      },
      {
        "name": "recurrence_relation",
        "expression": "∀n > 1 → fib(n) = fib(n-1) + fib(n-2)"
      }
    ]
  }
}
```

---

## Recommended Tools & Libraries

| Layer | Tool | Purpose | Integration Effort |
|-------|------|---------|-------------------|
| **Static Analysis** | pylint | Code quality | Low |
| | bandit | Security scanning | Low |
| | radon | Complexity metrics | Low |
| **Type Checking** | mypy | Type inference & checking | Medium |
| | pyright | Fast type checker (optional) | Medium |
| **Data Flow** | Custom (networkx) | Build CFG, def-use chains | Medium |
| **Symbolic Exec** | Z3 | SMT solver, path exploration | High |
| | angr | Binary analysis (advanced) | High |
| **Property Testing** | hypothesis | Property-based testing | Low |
| **Mutation Testing** | mutmut | Mutation testing | Medium |
| **Formal Verification** | Z3 | Contract verification | High |

---

## Implementation Priority

### Phase 1 (Weeks 1-2): Quick Wins
- ✅ **pylint integration** (code quality)
- ✅ **bandit integration** (security)
- ✅ **radon integration** (complexity)
- ✅ **mypy integration** (type checking)

**Impact:** Catches 70% of common issues with low effort

### Phase 2 (Weeks 3-4): Control & Data Flow
- ✅ **CFG builder** (control flow graphs)
- ✅ **Data flow analyzer** (def-use chains)
- ✅ **Unreachable code detection**
- ✅ **Dead store detection**

**Impact:** Semantic understanding, better canonicalization

### Phase 3 (Weeks 5-6): Property Testing
- ✅ **hypothesis integration** (property-based tests)
- ✅ **Mutation testing** (oracle quality)
- ✅ **Contract property verification**

**Impact:** Stronger behavioral validation

### Phase 4 (Weeks 7-8): Advanced (Optional)
- ⚠️ **Z3 symbolic execution** (expensive, research-grade)
- ⚠️ **Formal equivalence proofs** (complex)
- ⚠️ **Taint analysis** (security-critical domains)

**Impact:** Research-grade validation, good for papers

---

## Example: Enhanced Validation Report

```python
{
  "code_id": "run_5",
  "validation_summary": {
    "passed": false,
    "layers_passed": ["ast", "static", "type"],
    "layers_failed": ["dataflow"]
  },
  "findings": [
    {
      "layer": "static",
      "tool": "pylint",
      "severity": "warning",
      "message": "Variable name 'x' doesn't conform to snake_case",
      "line": 12
    },
    {
      "layer": "type",
      "tool": "mypy",
      "severity": "error",
      "message": "Incompatible return type (expected int, got str)",
      "line": 15
    },
    {
      "layer": "dataflow",
      "tool": "custom",
      "severity": "error",
      "message": "Variable 'result' used before assignment on line 18",
      "line": 18
    }
  ],
  "metrics": {
    "cyclomatic_complexity": 8,
    "cognitive_complexity": 12,
    "maintainability_index": 65.3,
    "type_coverage": 0.75
  }
}
```

---

## Benefits to SKYT

1. **Stronger Canonicalization**  
   - Type-aware transformations (don't rename variables with different types)
   - Control-flow-aware equivalence (recognize loop transformations)

2. **Better Rescue System**  
   - Data flow analysis guides variable renaming
   - Type checking prevents breaking transformations

3. **Semantic Equivalence Detection**  
   - Symbolic execution proves two implementations equivalent
   - Not just syntactic similarity

4. **Security & Compliance**  
   - bandit catches security issues
   - Restriction sets enforced via static analysis

5. **Research Credibility**  
   - Multi-layer validation → publishable novelty
   - Formal methods → strong claims about correctness

---

## Open Questions

1. **Performance:** How expensive is symbolic execution at scale?
2. **False Positives:** How to tune static analyzers to avoid noise?
3. **User Experience:** Should all layers run by default, or opt-in?
4. **Integration:** How does this fit into the existing `code_transformer.py`?
5. **Caching:** Can we cache validation results per (code_hash, contract_version)?

---

## Next Steps

1. **Review this architecture** with the team
2. **Prototype Phase 1** (pylint + mypy integration)
3. **Benchmark performance** (validation time vs accuracy trade-off)
4. **Update contract schema** to support validation layers
5. **Document validation reports** for users

---

**Document Version:** 1.0  
**Date:** 2025-11-19  
**Author:** SKYT Validation Team  
**Status:** Draft for Review
