# SKYT Validation Enhancement - Implementation Steps

## Phase 1: Quick Wins (Weeks 1-2)
**Goal:** Enhance existing properties with radon, mypy, and bandit

---

## Step 1: Install Dependencies & Update Requirements

### Actions:
1. Add new dependencies to `requirements.txt`
2. Install packages
3. Verify installations

### Commands:
```bash
# Add to requirements.txt
echo "radon>=6.0.1" >> requirements.txt
echo "mypy>=1.7.0" >> requirements.txt
echo "bandit>=1.7.5" >> requirements.txt

# Install
pip install radon mypy bandit

# Verify
radon --version
mypy --version
bandit --version
```

### Expected Output:
```
radon 6.0.1
mypy 1.7.1
bandit 1.7.5
```

### Files Modified:
- `requirements.txt`

---

## Step 2: Create Validation Configuration Module

### Actions:
1. Create `src/validation/` directory
2. Create `config.py` with validation modes
3. Define opt-in validation layers

### Implementation:

**File: `src/validation/__init__.py`**
```python
"""
SKYT Validation Framework
Multi-layer code validation beyond AST
"""

from .config import ValidationConfig, ValidationMode

__all__ = ["ValidationConfig", "ValidationMode"]
```

**File: `src/validation/config.py`**
```python
"""
Validation configuration and modes
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ValidationMode(Enum):
    """Predefined validation modes"""
    FAST = "fast"           # AST only (current baseline)
    STANDARD = "standard"   # AST + static analysis (recommended)
    THOROUGH = "thorough"   # AST + CFG + static + types
    RESEARCH = "research"   # All layers including symbolic


@dataclass
class ValidationConfig:
    """Configuration for validation layers"""
    
    # Core layers (always enabled)
    enable_ast: bool = True
    
    # Quick wins (Phase 1)
    enable_static_analysis: bool = False  # radon, bandit
    enable_type_checking: bool = False    # mypy
    
    # Advanced (Phase 2+)
    enable_cfg_analysis: bool = False     # Control flow graphs
    enable_dataflow_analysis: bool = False  # Def-use chains
    enable_symbolic_execution: bool = False  # Z3
    enable_property_testing: bool = False   # hypothesis
    
    # Timeouts (seconds)
    ast_timeout: float = 1.0
    static_analysis_timeout: float = 5.0
    type_checking_timeout: float = 5.0
    cfg_timeout: float = 10.0
    symbolic_timeout: float = 60.0
    
    @classmethod
    def from_mode(cls, mode: ValidationMode) -> "ValidationConfig":
        """Create config from predefined mode"""
        configs = {
            ValidationMode.FAST: cls(
                enable_ast=True,
            ),
            ValidationMode.STANDARD: cls(
                enable_ast=True,
                enable_static_analysis=True,
            ),
            ValidationMode.THOROUGH: cls(
                enable_ast=True,
                enable_static_analysis=True,
                enable_type_checking=True,
                enable_cfg_analysis=True,
            ),
            ValidationMode.RESEARCH: cls(
                enable_ast=True,
                enable_static_analysis=True,
                enable_type_checking=True,
                enable_cfg_analysis=True,
                enable_dataflow_analysis=True,
                enable_symbolic_execution=True,
                enable_property_testing=True,
            ),
        }
        return configs[mode]
```

### Files Created:
- `src/validation/__init__.py`
- `src/validation/config.py`

---

## Step 3: Create Static Analysis Wrapper (radon + bandit)

### Actions:
1. Create `static_analyzer.py` with radon and bandit integration
2. Implement complexity metrics extraction
3. Implement security scanning

### Implementation:

**File: `src/validation/static_analyzer.py`**
```python
"""
Static analysis using radon and bandit
Enhances complexity_class and side_effect_profile properties
"""
import tempfile
import json
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path

from radon.complexity import cc_visit, average_complexity
from radon.metrics import mi_visit, h_visit


class StaticAnalyzer:
    """
    Wrapper for static analysis tools
    - radon: complexity metrics
    - bandit: security scanning
    """
    
    def analyze_complexity(self, code: str) -> Dict[str, Any]:
        """
        Use radon to compute complexity metrics
        
        Enhances: complexity_class property
        """
        try:
            # Cyclomatic complexity
            cc_results = cc_visit(code)
            
            # Maintainability index
            mi_results = mi_visit(code, multi=True)
            
            # Halstead metrics
            h_results = h_visit(code)
            
            return {
                "cyclomatic_complexity": cc_results[0].complexity if cc_results else 0,
                "complexity_rank": cc_results[0].rank if cc_results else "A",
                "average_complexity": average_complexity(cc_results) if cc_results else 0,
                "maintainability_index": mi_results if mi_results else 100.0,
                "halstead_metrics": {
                    "difficulty": h_results.total.difficulty if h_results else 0,
                    "effort": h_results.total.effort if h_results else 0,
                    "volume": h_results.total.volume if h_results else 0,
                    "bugs": h_results.total.bugs if h_results else 0,
                } if h_results else {},
            }
        except Exception as e:
            return {
                "error": str(e),
                "cyclomatic_complexity": None,
            }
    
    def analyze_security(self, code: str) -> Dict[str, Any]:
        """
        Use bandit to scan for security issues
        
        Enhances: side_effect_profile property
        """
        try:
            # Write code to temp file (bandit requires file)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            try:
                # Run bandit with JSON output
                result = subprocess.run(
                    ['bandit', '-f', 'json', temp_path],
                    capture_output=True,
                    text=True,
                    timeout=5.0
                )
                
                # Parse JSON output
                if result.stdout:
                    report = json.loads(result.stdout)
                    
                    return {
                        "security_issues": [
                            {
                                "severity": issue.get("issue_severity"),
                                "confidence": issue.get("issue_confidence"),
                                "type": issue.get("test_id"),
                                "message": issue.get("issue_text"),
                                "line": issue.get("line_number"),
                            }
                            for issue in report.get("results", [])
                        ],
                        "total_issues": len(report.get("results", [])),
                        "high_severity_count": sum(
                            1 for issue in report.get("results", [])
                            if issue.get("issue_severity") == "HIGH"
                        ),
                    }
                else:
                    return {"security_issues": [], "total_issues": 0}
                    
            finally:
                # Clean up temp file
                Path(temp_path).unlink(missing_ok=True)
                
        except subprocess.TimeoutExpired:
            return {"error": "bandit timeout", "security_issues": []}
        except Exception as e:
            return {"error": str(e), "security_issues": []}
    
    def analyze_all(self, code: str) -> Dict[str, Any]:
        """
        Run all static analysis checks
        
        Returns combined metrics for complexity and security
        """
        return {
            "complexity": self.analyze_complexity(code),
            "security": self.analyze_security(code),
        }


# Quick test
if __name__ == "__main__":
    analyzer = StaticAnalyzer()
    
    test_code = """
def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n-1) + fibonacci(n-2)
"""
    
    result = analyzer.analyze_all(test_code)
    print("Complexity:", result["complexity"])
    print("Security:", result["security"])
```

### Files Created:
- `src/validation/static_analyzer.py`

### Test:
```bash
cd src/validation
python static_analyzer.py
```

---

## Step 4: Create Type Checker Wrapper (mypy)

### Actions:
1. Create `type_checker.py` with mypy integration
2. Implement type inference (even without annotations)
3. Implement type error detection

### Implementation:

**File: `src/validation/type_checker.py`**
```python
"""
Type checking using mypy
Enhances function_contracts property
"""
import tempfile
import json
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path
import ast


class TypeChecker:
    """
    Wrapper for mypy type checking
    Infers types even without annotations
    """
    
    def check_types(self, code: str) -> Dict[str, Any]:
        """
        Run mypy on code to detect type errors and infer types
        
        Enhances: function_contracts property
        """
        try:
            # Write code to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            try:
                # Run mypy with JSON output
                result = subprocess.run(
                    [
                        'mypy',
                        '--show-error-codes',
                        '--no-error-summary',
                        '--output=json',
                        temp_path
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5.0
                )
                
                # Parse errors
                type_errors = []
                if result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            try:
                                error = json.loads(line)
                                type_errors.append({
                                    "line": error.get("line"),
                                    "column": error.get("column"),
                                    "message": error.get("message"),
                                    "severity": error.get("severity"),
                                    "error_code": error.get("code"),
                                })
                            except json.JSONDecodeError:
                                pass
                
                return {
                    "type_errors": type_errors,
                    "total_errors": len(type_errors),
                    "has_type_errors": len(type_errors) > 0,
                }
                
            finally:
                # Clean up
                Path(temp_path).unlink(missing_ok=True)
                
        except subprocess.TimeoutExpired:
            return {"error": "mypy timeout", "type_errors": []}
        except Exception as e:
            return {"error": str(e), "type_errors": []}
    
    def infer_function_signatures(self, code: str) -> Dict[str, Any]:
        """
        Infer function signatures from code
        
        Uses AST + basic type inference
        """
        try:
            tree = ast.parse(code)
            signatures = {}
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Extract parameter info
                    params = []
                    for arg in node.args.args:
                        param_info = {
                            "name": arg.arg,
                            "annotation": ast.unparse(arg.annotation) if arg.annotation else None,
                        }
                        params.append(param_info)
                    
                    # Extract return annotation
                    return_annotation = None
                    if node.returns:
                        return_annotation = ast.unparse(node.returns)
                    
                    signatures[node.name] = {
                        "parameters": params,
                        "return_annotation": return_annotation,
                        "has_annotations": any(p["annotation"] for p in params) or return_annotation is not None,
                    }
            
            return {
                "signatures": signatures,
                "total_functions": len(signatures),
            }
            
        except Exception as e:
            return {"error": str(e), "signatures": {}}
    
    def analyze_all(self, code: str) -> Dict[str, Any]:
        """
        Run all type checking analysis
        """
        return {
            "type_errors": self.check_types(code),
            "signatures": self.infer_function_signatures(code),
        }


# Quick test
if __name__ == "__main__":
    checker = TypeChecker()
    
    test_code = """
def fibonacci(n: int) -> int:
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n-1) + fibonacci(n-2)

def bad_fibonacci(n):
    if n <= 0:
        return "zero"  # Type error!
    return fibonacci(n-1) + fibonacci(n-2)
"""
    
    result = checker.analyze_all(test_code)
    print("Type Errors:", result["type_errors"])
    print("Signatures:", result["signatures"])
```

### Files Created:
- `src/validation/type_checker.py`

### Test:
```bash
cd src/validation
python type_checker.py
```

---

## Step 5: Integrate Validators into FoundationalProperties

### Actions:
1. Update `foundational_properties.py` to accept `ValidationConfig`
2. Enhance 3 weak properties with new validators
3. Maintain backward compatibility (extend, don't replace)

### Implementation:

**File: `src/foundational_properties.py` (modifications)**

```python
# Add imports at top
from typing import Dict, Any, List, Set, Tuple, Optional
import sys
from pathlib import Path

# Add validation imports
sys.path.append(str(Path(__file__).parent))
from validation.config import ValidationConfig, ValidationMode
from validation.static_analyzer import StaticAnalyzer
from validation.type_checker import TypeChecker


class FoundationalProperties:
    """
    Extracts and compares the 13 foundational properties that define code sameness
    NOW WITH ENHANCED VALIDATION LAYERS
    """
    
    def __init__(self, contract: Optional[Dict[str, Any]] = None, 
                 validation_config: Optional[ValidationConfig] = None):
        self.contract = contract
        
        # Validation configuration (default: FAST mode = AST only)
        self.validation_config = validation_config or ValidationConfig.from_mode(ValidationMode.FAST)
        
        # Initialize validators (lazy loading)
        self._static_analyzer = None
        self._type_checker = None
        
        # Define the 13 foundational properties
        self.properties = [
            "control_flow_signature",
            "data_dependency_graph", 
            "execution_paths",
            "function_contracts",      # ← Will be enhanced
            "complexity_class",        # ← Will be enhanced
            "side_effect_profile",     # ← Will be enhanced
            "termination_properties",
            "algebraic_structure",
            "numerical_behavior",
            "logical_equivalence",
            "normalized_ast_structure",
            "operator_precedence",
            "statement_ordering",
            "recursion_schema"
        ]
    
    @property
    def static_analyzer(self) -> StaticAnalyzer:
        """Lazy load static analyzer"""
        if self._static_analyzer is None:
            self._static_analyzer = StaticAnalyzer()
        return self._static_analyzer
    
    @property
    def type_checker(self) -> TypeChecker:
        """Lazy load type checker"""
        if self._type_checker is None:
            self._type_checker = TypeChecker()
        return self._type_checker
    
    # ... existing extract_all_properties method stays the same ...
    
    def _extract_complexity_class(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """
        Extract algorithmic complexity (O-notation)
        ENHANCED with radon static analysis
        """
        # BASELINE: AST-based complexity (existing code)
        complexity = {
            "nested_loops": 0,
            "recursive_calls": 0,
            "estimated_complexity": "O(1)"
        }
        
        class ComplexityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.loop_depth = 0
                self.max_loop_depth = 0
                self.function_names = set()
                
            def visit_FunctionDef(self, node):
                self.function_names.add(node.name)
                self.generic_visit(node)
                
            def visit_For(self, node):
                self.loop_depth += 1
                self.max_loop_depth = max(self.max_loop_depth, self.loop_depth)
                self.generic_visit(node)
                self.loop_depth -= 1
                
            def visit_While(self, node):
                self.loop_depth += 1
                self.max_loop_depth = max(self.max_loop_depth, self.loop_depth)
                self.generic_visit(node)
                self.loop_depth -= 1
                
            def visit_Call(self, node):
                if isinstance(node.func, ast.Name) and node.func.id in self.function_names:
                    complexity["recursive_calls"] += 1
                self.generic_visit(node)
        
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        
        complexity["nested_loops"] = visitor.max_loop_depth
        
        # Estimate complexity (heuristic)
        if complexity["recursive_calls"] > 0:
            complexity["estimated_complexity"] = "O(2^n)"
        elif complexity["nested_loops"] >= 2:
            complexity["estimated_complexity"] = "O(n^2)"
        elif complexity["nested_loops"] == 1:
            complexity["estimated_complexity"] = "O(n)"
        
        # ENHANCEMENT: Add radon metrics if enabled
        if self.validation_config.enable_static_analysis:
            try:
                radon_metrics = self.static_analyzer.analyze_complexity(code)
                complexity.update({
                    "cyclomatic_complexity": radon_metrics.get("cyclomatic_complexity"),
                    "complexity_rank": radon_metrics.get("complexity_rank"),
                    "maintainability_index": radon_metrics.get("maintainability_index"),
                    "halstead_metrics": radon_metrics.get("halstead_metrics"),
                })
            except Exception as e:
                complexity["static_analysis_error"] = str(e)
        
        return complexity
    
    def _extract_function_contracts(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """
        Extract input/output type relationships
        ENHANCED with mypy type checking
        """
        # BASELINE: AST-based contracts (existing code)
        contracts = {}
        
        class ContractVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                contract = {
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "returns": None,
                    "has_return": False
                }
                
                # Check for return statements
                for child in ast.walk(node):
                    if isinstance(child, ast.Return):
                        contract["has_return"] = True
                        break
                
                contracts[node.name] = contract
                self.generic_visit(node)
        
        visitor = ContractVisitor()
        visitor.visit(tree)
        
        # ENHANCEMENT: Add type checking if enabled
        if self.validation_config.enable_type_checking:
            try:
                type_analysis = self.type_checker.analyze_all(code)
                
                # Merge type info into contracts
                for func_name, contract in contracts.items():
                    if func_name in type_analysis["signatures"]["signatures"]:
                        sig = type_analysis["signatures"]["signatures"][func_name]
                        contract["parameters"] = sig["parameters"]
                        contract["return_annotation"] = sig["return_annotation"]
                        contract["has_annotations"] = sig["has_annotations"]
                
                # Add type errors to contracts
                contracts["_type_analysis"] = {
                    "type_errors": type_analysis["type_errors"]["type_errors"],
                    "has_type_errors": type_analysis["type_errors"]["has_type_errors"],
                }
            except Exception as e:
                contracts["_type_analysis"] = {"error": str(e)}
        
        return contracts
    
    def _extract_side_effect_profile(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """
        Extract pure vs stateful operations
        ENHANCED with bandit security analysis
        """
        # BASELINE: AST-based side effects (existing code)
        profile = {
            "has_print": False,
            "has_global_access": False,
            "has_file_io": False,
            "modifies_arguments": False,
            "is_pure": True
        }
        
        class SideEffectVisitor(ast.NodeVisitor):
            def visit_Call(self, node):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ["print", "input"]:
                        profile["has_print"] = True
                        profile["is_pure"] = False
                    elif node.func.id in ["open", "read", "write"]:
                        profile["has_file_io"] = True
                        profile["is_pure"] = False
                self.generic_visit(node)
                
            def visit_Global(self, node):
                profile["has_global_access"] = True
                profile["is_pure"] = False
                self.generic_visit(node)
        
        visitor = SideEffectVisitor()
        visitor.visit(tree)
        
        # ENHANCEMENT: Add security analysis if enabled
        if self.validation_config.enable_static_analysis:
            try:
                security = self.static_analyzer.analyze_security(code)
                profile.update({
                    "security_issues": security.get("security_issues", []),
                    "total_security_issues": security.get("total_issues", 0),
                    "high_severity_issues": security.get("high_severity_count", 0),
                })
                
                # Update purity based on security findings
                if profile["total_security_issues"] > 0:
                    profile["is_pure"] = False
            except Exception as e:
                profile["security_analysis_error"] = str(e)
        
        return profile
```

### Files Modified:
- `src/foundational_properties.py`

### Test:
```python
# test_enhanced_properties.py
from src.foundational_properties import FoundationalProperties
from src.validation.config import ValidationConfig, ValidationMode

code = """
def fibonacci(n: int) -> int:
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n-1) + fibonacci(n-2)
"""

# Test with FAST mode (AST only)
props_fast = FoundationalProperties(validation_config=ValidationConfig.from_mode(ValidationMode.FAST))
result_fast = props_fast.extract_all_properties(code)
print("FAST mode complexity:", result_fast["complexity_class"])

# Test with STANDARD mode (AST + static analysis)
props_standard = FoundationalProperties(validation_config=ValidationConfig.from_mode(ValidationMode.STANDARD))
result_standard = props_standard.extract_all_properties(code)
print("STANDARD mode complexity:", result_standard["complexity_class"])
print("STANDARD mode contracts:", result_standard["function_contracts"])
```

---

## Summary of First 5 Steps

| Step | What | Files | Time Estimate |
|------|------|-------|---------------|
| 1 | Install dependencies | `requirements.txt` | 10 min |
| 2 | Create validation config | `src/validation/config.py` | 30 min |
| 3 | Create static analyzer | `src/validation/static_analyzer.py` | 1 hour |
| 4 | Create type checker | `src/validation/type_checker.py` | 1 hour |
| 5 | Integrate into properties | `src/foundational_properties.py` | 2 hours |

**Total Time:** ~5 hours

---

## Verification Checklist

After completing these steps, verify:

- [ ] All dependencies installed (`radon`, `mypy`, `bandit`)
- [ ] `src/validation/` directory created with 3 modules
- [ ] `static_analyzer.py` runs standalone test
- [ ] `type_checker.py` runs standalone test
- [ ] `foundational_properties.py` accepts `ValidationConfig`
- [ ] FAST mode returns baseline (AST-only) properties
- [ ] STANDARD mode returns enhanced properties with radon/mypy/bandit data

---

## Next Steps (Step 6+)

After completing Steps 1-5:
- Step 6: Update contract schema to support validation config
- Step 7: Update pipeline to pass validation config
- Step 8: Add validation reports to experiment results
- Step 9: Create tests for enhanced properties
- Step 10: Update documentation and CLI

Ready to start with Step 1?
