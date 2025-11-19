# src/foundational_properties.py
"""
13 Foundational Properties for Code Sameness
Implements comprehensive property extraction and comparison for SKYT canonicalization
"""

import ast
import hashlib
from typing import Dict, Any, List, Set, Tuple, Optional
from collections import defaultdict
import json
import logging

# Import enhanced analyzers (lazy-loaded to avoid dependency issues)
try:
    from .analyzers.complexity_analyzer import ComplexityAnalyzer
    from .analyzers.type_checker import TypeChecker
    ANALYZERS_AVAILABLE = True
except ImportError:
    ANALYZERS_AVAILABLE = False

logger = logging.getLogger(__name__)


class FoundationalProperties:
    """
    Extracts and compares the 13 foundational properties that define code sameness
    """
    
    def __init__(self, contract: Optional[Dict[str, Any]] = None):
        # Define the 13 foundational properties
        self.contract = contract
        
        # Lazy-loaded analyzers (Dependency Injection pattern)
        self._complexity_analyzer = None
        self._type_checker = None
        
        self.properties = [
            "control_flow_signature",
            "data_dependency_graph", 
            "execution_paths",
            "function_contracts",
            "complexity_class",
            "side_effect_profile",
            "termination_properties",
            "algebraic_structure",
            "numerical_behavior",
            "logical_equivalence",
            "normalized_ast_structure",
            "operator_precedence",
            "statement_ordering",
            # "behavioral_signature",  # DISABLED: Executes arbitrary code, causes hangs
            "recursion_schema"       # NEW: Recursive structure
        ]
    
    @property
    def complexity_analyzer(self) -> Optional['ComplexityAnalyzer']:
        """Lazy-load complexity analyzer (avoids import if not needed)"""
        if not ANALYZERS_AVAILABLE:
            return None
        if self._complexity_analyzer is None:
            self._complexity_analyzer = ComplexityAnalyzer()
        return self._complexity_analyzer
    
    @property
    def type_checker(self) -> Optional['TypeChecker']:
        """Lazy-load type checker (avoids import if not needed)"""
        if not ANALYZERS_AVAILABLE:
            return None
        if self._type_checker is None:
            self._type_checker = TypeChecker()
        return self._type_checker
    
    def extract_all_properties(self, code: str) -> Dict[str, Any]:
        """
        Extract all 13 foundational properties from code
        
        Args:
            code: Python code string
            
        Returns:
            Dictionary with all foundational properties
        """
        try:
            tree = ast.parse(code)
            
            properties = {}
            for prop_name in self.properties:
                method_name = f"_extract_{prop_name}"
                if hasattr(self, method_name):
                    properties[prop_name] = getattr(self, method_name)(tree, code)
                else:
                    properties[prop_name] = None
            
            return properties
            
        except SyntaxError:
            # Return empty properties for unparseable code
            return {prop: None for prop in self.properties}
    
    def _extract_control_flow_signature(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """Extract control flow topology (branches, loops, function calls)"""
        signature = {
            "if_statements": 0,
            "for_loops": 0,
            "while_loops": 0,
            "function_calls": [],
            "nested_depth": 0,
            "branch_patterns": []
        }
        
        class ControlFlowVisitor(ast.NodeVisitor):
            def __init__(self):
                self.depth = 0
                self.max_depth = 0
                
            def visit_If(self, node):
                signature["if_statements"] += 1
                signature["branch_patterns"].append(f"if_at_depth_{self.depth}")
                self.depth += 1
                self.max_depth = max(self.max_depth, self.depth)
                self.generic_visit(node)
                self.depth -= 1
                
            def visit_For(self, node):
                signature["for_loops"] += 1
                self.depth += 1
                self.max_depth = max(self.max_depth, self.depth)
                self.generic_visit(node)
                self.depth -= 1
                
            def visit_While(self, node):
                signature["while_loops"] += 1
                self.depth += 1
                self.max_depth = max(self.max_depth, self.depth)
                self.generic_visit(node)
                self.depth -= 1
                
            def visit_Call(self, node):
                if isinstance(node.func, ast.Name):
                    signature["function_calls"].append(node.func.id)
                self.generic_visit(node)
        
        visitor = ControlFlowVisitor()
        visitor.visit(tree)
        signature["nested_depth"] = visitor.max_depth
        
        return signature
    
    def _extract_data_dependency_graph(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """Extract variable dependency relationships"""
        dependencies = defaultdict(set)
        assignments = {}
        
        class DependencyVisitor(ast.NodeVisitor):
            def visit_Assign(self, node):
                # Get assigned variables
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id
                        # Get dependencies from the value
                        deps = self._get_dependencies(node.value)
                        dependencies[var_name].update(deps)
                        assignments[var_name] = ast.dump(node.value)
                self.generic_visit(node)
            
            def _get_dependencies(self, node):
                deps = set()
                if isinstance(node, ast.Name):
                    deps.add(node.id)
                elif isinstance(node, ast.BinOp):
                    deps.update(self._get_dependencies(node.left))
                    deps.update(self._get_dependencies(node.right))
                elif isinstance(node, ast.Call):
                    for arg in node.args:
                        deps.update(self._get_dependencies(arg))
                return deps
        
        visitor = DependencyVisitor()
        visitor.visit(tree)
        
        return {
            "dependencies": {k: list(v) for k, v in dependencies.items()},
            "assignments": assignments
        }
    
    def _extract_execution_paths(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """Extract canonical execution path representation"""
        paths = []
        
        class PathVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_path = []
                
            def visit_If(self, node):
                self.current_path.append("branch")
                paths.append(self.current_path.copy())
                self.generic_visit(node)
                self.current_path.pop()
                
            def visit_For(self, node):
                self.current_path.append("loop")
                paths.append(self.current_path.copy())
                self.generic_visit(node)
                self.current_path.pop()
                
            def visit_FunctionDef(self, node):
                self.current_path.append(f"function_{node.name}")
                paths.append(self.current_path.copy())
                self.generic_visit(node)
                self.current_path.pop()
        
        visitor = PathVisitor()
        visitor.visit(tree)
        
        return {"execution_paths": paths}
    
    def _extract_function_contracts(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """
        Extract input/output type relationships.
        
        BASELINE: AST-based contract extraction (existing logic, always runs)
        ENHANCED: mypy type checking and inference if available
        
        Design: Extend, don't replace - maintains backward compatibility
        """
        # BASELINE: AST-based contract extraction (existing logic preserved)
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
        
        # ENHANCEMENT: Add type checking if analyzer available
        # This extends the baseline without replacing it
        if self.type_checker is not None:
            try:
                type_analysis = self.type_checker.analyze(code)
                
                # Merge type information into contracts
                for func_name in contracts:
                    if func_name in type_analysis.get("function_signatures", {}):
                        sig = type_analysis["function_signatures"][func_name]
                        # Add type-specific fields
                        contracts[func_name]["type_signature"] = sig
                        contracts[func_name]["has_type_annotations"] = sig.get("has_annotations", False)
                
                # Add global type analysis results
                contracts["_type_analysis"] = {
                    "type_errors": type_analysis.get("type_errors", []),
                    "total_type_errors": type_analysis.get("total_type_errors", 0),
                    "type_safe": type_analysis.get("type_safe", None),
                    "annotation_coverage": type_analysis.get("annotation_coverage", 0.0),
                }
            except Exception as e:
                # Graceful degradation: log error but keep baseline
                logger.warning(f"Type checking failed: {e}")
                contracts["_type_analysis"] = {"error": str(e)}
        
        return contracts
    
    def _extract_complexity_class(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """
        Extract algorithmic complexity (O-notation).
        
        BASELINE: AST-based heuristic (existing logic, always runs)
        ENHANCED: Radon metrics if available (compiler-grade analysis)
        
        Design: Extend, don't replace - maintains backward compatibility
        """
        # BASELINE: AST-based complexity analysis (existing logic preserved)
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
        
        # ENHANCEMENT: Add radon metrics if analyzer available
        # This extends the baseline without replacing it
        if self.complexity_analyzer is not None:
            try:
                radon_metrics = self.complexity_analyzer.analyze(code)
                # Merge radon metrics into result (keeps all baseline fields)
                complexity.update(radon_metrics)
            except Exception as e:
                # Graceful degradation: log error but keep baseline
                logger.warning(f"Radon analysis failed: {e}")
                complexity["radon_error"] = str(e)
        
        return complexity
    
    def _extract_side_effect_profile(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """Extract pure vs stateful operations"""
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
        
        return profile
    
    def _extract_termination_properties(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """Extract base cases and loop bounds"""
        properties = {
            "has_base_case": False,
            "has_bounded_loops": False,
            "recursive_depth": 0
        }
        
        class TerminationVisitor(ast.NodeVisitor):
            def visit_If(self, node):
                # Check for base case patterns (early returns)
                for child in ast.walk(node):
                    if isinstance(child, ast.Return):
                        properties["has_base_case"] = True
                        break
                self.generic_visit(node)
                
            def visit_For(self, node):
                properties["has_bounded_loops"] = True
                self.generic_visit(node)
        
        visitor = TerminationVisitor()
        visitor.visit(tree)
        
        return properties
    
    def _extract_algebraic_structure(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """Extract commutativity and associativity patterns"""
        structure = {
            "commutative_ops": [],
            "associative_ops": [],
            "binary_operations": []
        }
        
        class AlgebraVisitor(ast.NodeVisitor):
            def visit_BinOp(self, node):
                op_type = type(node.op).__name__
                structure["binary_operations"].append(op_type)
                
                if op_type in ["Add", "Mult"]:
                    structure["commutative_ops"].append(op_type)
                    structure["associative_ops"].append(op_type)
                
                self.generic_visit(node)
        
        visitor = AlgebraVisitor()
        visitor.visit(tree)
        
        return structure
    
    def _extract_numerical_behavior(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """Extract precision and overflow handling"""
        behavior = {
            "uses_integers": False,
            "uses_floats": False,
            "has_arithmetic": False,
            "numeric_constants": []
        }
        
        class NumericVisitor(ast.NodeVisitor):
            def visit_Constant(self, node):
                if isinstance(node.value, int):
                    behavior["uses_integers"] = True
                    behavior["numeric_constants"].append(node.value)
                elif isinstance(node.value, float):
                    behavior["uses_floats"] = True
                    behavior["numeric_constants"].append(node.value)
                self.generic_visit(node)
                
            def visit_BinOp(self, node):
                behavior["has_arithmetic"] = True
                self.generic_visit(node)
        
        visitor = NumericVisitor()
        visitor.visit(tree)
        
        return behavior
    
    def _extract_logical_equivalence(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """Extract boolean expression normalization"""
        equivalence = {
            "boolean_ops": [],
            "comparisons": [],
            "logical_patterns": []
        }
        
        class LogicalVisitor(ast.NodeVisitor):
            def visit_BoolOp(self, node):
                op_type = type(node.op).__name__
                equivalence["boolean_ops"].append(op_type)
                self.generic_visit(node)
                
            def visit_Compare(self, node):
                for op in node.ops:
                    equivalence["comparisons"].append(type(op).__name__)
                self.generic_visit(node)
        
        visitor = LogicalVisitor()
        visitor.visit(tree)
        
        return equivalence
    
    def _extract_normalized_ast_structure(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """Extract canonical AST representation with α-renaming"""
        structure = {
            "node_types": [],
            "ast_depth": 0,
            "ast_hash": "",
            "alpha_renamed_hash": ""
        }
        
        def get_ast_info(node, depth=0):
            structure["node_types"].append(type(node).__name__)
            structure["ast_depth"] = max(structure["ast_depth"], depth)
            
            for child in ast.iter_child_nodes(node):
                get_ast_info(child, depth + 1)
        
        get_ast_info(tree)
        
        # Create normalized AST hash (original, variable-name-sensitive)
        ast_dump = ast.dump(tree, annotate_fields=False)
        structure["ast_hash"] = hashlib.md5(ast_dump.encode()).hexdigest()
        
        # Create α-renamed AST hash (variable-name-agnostic)
        try:
            alpha_renamed_tree = self._alpha_rename_ast(tree)
            alpha_dump = ast.dump(alpha_renamed_tree, annotate_fields=False)
            structure["alpha_renamed_hash"] = hashlib.md5(alpha_dump.encode()).hexdigest()
        except Exception:
            # Fallback to original hash if α-renaming fails
            structure["alpha_renamed_hash"] = structure["ast_hash"]
        
        return structure
    
    def _alpha_rename_ast(self, tree: ast.AST) -> ast.AST:
        """
        Apply α-renaming to AST: systematically rename variables to v0, v1, v2...
        This makes structural comparison variable-name-agnostic
        """
        import copy
        tree = copy.deepcopy(tree)
        
        class AlphaRenamer(ast.NodeTransformer):
            def __init__(self):
                self.var_map = {}
                self.counter = 0
                self.param_names = set()  # Track parameter names to rename consistently
                
            def visit_FunctionDef(self, node):
                # First pass: collect parameter names
                for arg in node.args.args:
                    if arg.arg not in self.var_map:
                        # Keep param names as p0, p1, p2... for clarity
                        self.var_map[arg.arg] = f"p{len(self.param_names)}"
                        self.param_names.add(arg.arg)
                
                # Process function body
                self.generic_visit(node)
                
                # Rename parameters
                for arg in node.args.args:
                    if arg.arg in self.var_map:
                        arg.arg = self.var_map[arg.arg]
                
                # Don't rename function names (they're part of the contract)
                return node
            
            def visit_Name(self, node):
                # Rename variable references
                if node.id not in ['range', 'len', 'print', 'max', 'min', 'sum', 'abs']:  # Built-ins
                    if node.id not in self.var_map:
                        self.var_map[node.id] = f"v{self.counter}"
                        self.counter += 1
                    node.id = self.var_map[node.id]
                return node
        
        renamer = AlphaRenamer()
        return renamer.visit(tree)
    
    def _extract_operator_precedence(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """Extract explicit precedence normalization"""
        precedence = {
            "operator_sequence": [],
            "precedence_levels": {}
        }
        
        class PrecedenceVisitor(ast.NodeVisitor):
            def visit_BinOp(self, node):
                op_type = type(node.op).__name__
                precedence["operator_sequence"].append(op_type)
                
                # Assign precedence levels
                precedence_map = {
                    "Pow": 6, "UAdd": 5, "USub": 5,
                    "Mult": 4, "Div": 4, "FloorDiv": 4, "Mod": 4,
                    "Add": 3, "Sub": 3,
                    "LShift": 2, "RShift": 2,
                    "BitAnd": 1, "BitXor": 1, "BitOr": 1
                }
                
                precedence["precedence_levels"][op_type] = precedence_map.get(op_type, 0)
                self.generic_visit(node)
        
        visitor = PrecedenceVisitor()
        visitor.visit(tree)
        
        return precedence
    
    def _extract_statement_ordering(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """Extract canonical statement sequence"""
        ordering = {
            "statement_types": [],
            "statement_sequence": [],
            "control_flow_order": []
        }
        
        class OrderingVisitor(ast.NodeVisitor):
            def visit(self, node):
                if isinstance(node, ast.stmt):
                    stmt_type = type(node).__name__
                    ordering["statement_types"].append(stmt_type)
                    ordering["statement_sequence"].append(f"{stmt_type}_{len(ordering['statement_sequence'])}")
                    
                    if stmt_type in ["If", "For", "While", "FunctionDef"]:
                        ordering["control_flow_order"].append(stmt_type)
                
                self.generic_visit(node)
        
        visitor = OrderingVisitor()
        visitor.visit(tree)
        
        return ordering
    
    def _extract_behavioral_signature(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """
        Extract behavioral signature from code execution on canonical test cases
        This captures actual I/O behavior to detect semantic differences
        """
        signature = {
            "can_execute": False,
            "io_signature_hash": None,
            "side_effects_detected": [],
            "test_results": []
        }
        
        try:
            # Execute code safely in isolated namespace
            namespace = {}
            exec(code, namespace)
            
            # Find the main function
            main_func = None
            for name, obj in namespace.items():
                if callable(obj) and not name.startswith('_'):
                    main_func = obj
                    break
            
            if main_func:
                signature["can_execute"] = True
                
                # Run on canonical seed inputs (algorithm-agnostic)
                test_inputs = [0, 1, 2, 5, 10]
                io_pairs = []
                
                for inp in test_inputs:
                    try:
                        # Capture stdout for side-effect detection
                        import io as io_module
                        import sys
                        old_stdout = sys.stdout
                        sys.stdout = captured_output = io_module.StringIO()
                        
                        result = main_func(inp)
                        
                        sys.stdout = old_stdout
                        output_text = captured_output.getvalue()
                        
                        # Record I/O pair
                        io_pairs.append((inp, result, bool(output_text)))
                        
                        if output_text:
                            signature["side_effects_detected"].append("stdout")
                        
                    except Exception as e:
                        # Record exception type as part of behavior
                        io_pairs.append((inp, f"Exception:{type(e).__name__}", False))
                
                # Create hash of I/O behavior
                io_str = str(sorted(io_pairs))
                signature["io_signature_hash"] = hashlib.md5(io_str.encode()).hexdigest()
                signature["test_results"] = io_pairs[:3]  # Store first 3 for debugging
                
        except Exception:
            # Can't execute code safely
            signature["can_execute"] = False
        
        return signature
    
    def _extract_recursion_schema(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """
        Extract recursion schema: base cases, recursive structure, termination patterns
        Critical for algorithms like merge_sort, quicksort, binary_search
        """
        schema = {
            "is_recursive": False,
            "base_cases": [],
            "recursive_calls": [],
            "recursion_pattern": None,
            "termination_guards": []
        }
        
        class RecursionVisitor(ast.NodeVisitor):
            def __init__(self):
                self.function_name = None
                self.in_function = False
                
            def visit_FunctionDef(self, node):
                # Track function name for recursion detection
                old_name = self.function_name
                old_in_function = self.in_function
                
                self.function_name = node.name
                self.in_function = True
                
                # Extract base case patterns (early returns)
                for stmt in node.body:
                    if isinstance(stmt, ast.If):
                        # Check if this if has a return in its body
                        for child in stmt.body:
                            if isinstance(child, ast.Return):
                                # This is a potential base case
                                base_case = {
                                    "condition": ast.unparse(stmt.test) if hasattr(ast, 'unparse') else ast.dump(stmt.test),
                                    "return_type": "constant" if isinstance(child.value, ast.Constant) else "expression"
                                }
                                schema["base_cases"].append(base_case)
                                schema["termination_guards"].append(base_case["condition"])
                
                self.generic_visit(node)
                
                self.function_name = old_name
                self.in_function = old_in_function
                
            def visit_Call(self, node):
                # Detect recursive calls
                if self.in_function and isinstance(node.func, ast.Name):
                    if node.func.id == self.function_name:
                        schema["is_recursive"] = True
                        
                        # Record recursion pattern
                        call_info = {
                            "num_args": len(node.args),
                            "arg_patterns": [type(arg).__name__ for arg in node.args]
                        }
                        schema["recursive_calls"].append(call_info)
                
                self.generic_visit(node)
        
        visitor = RecursionVisitor()
        visitor.visit(tree)
        
        # Classify recursion pattern
        if schema["is_recursive"]:
            num_recursive_calls = len(schema["recursive_calls"])
            if num_recursive_calls == 1:
                schema["recursion_pattern"] = "linear"
            elif num_recursive_calls == 2:
                schema["recursion_pattern"] = "binary"  # Like merge_sort
            elif num_recursive_calls > 2:
                schema["recursion_pattern"] = "multi-way"
            
            # Check for divide-and-conquer pattern
            if num_recursive_calls == 2 and len(schema["base_cases"]) >= 1:
                schema["recursion_pattern"] = "divide_and_conquer"
        
        return schema
    
    def calculate_distance(self, props1: Dict[str, Any], props2: Dict[str, Any],
                          contract: Optional[Dict[str, Any]] = None) -> float:
        """
        Calculate distance between two sets of foundational properties
        
        Args:
            props1: First set of properties
            props2: Second set of properties
            contract: Optional contract with variable naming constraints
            
        Returns:
            Distance score (0.0 = identical, 1.0 = completely different)
        """
        # Use instance contract if not provided
        contract = contract or self.contract
        if not props1 or not props2:
            return 1.0
        
        total_distance = 0.0
        property_count = 0
        
        for prop_name in self.properties:
            if prop_name in props1 and prop_name in props2:
                prop_distance = self._calculate_property_distance(
                    props1[prop_name], props2[prop_name], prop_name, contract
                )
                total_distance += prop_distance
                property_count += 1
        
        return total_distance / property_count if property_count > 0 else 1.0
    
    def _calculate_property_distance(self, prop1: Any, prop2: Any, prop_name: str,
                                    contract: Optional[Dict[str, Any]] = None) -> float:
        """Calculate distance for a specific property"""
        if prop1 is None or prop2 is None:
            return 1.0 if prop1 != prop2 else 0.0
        
        if prop_name == "control_flow_signature":
            return self._distance_control_flow(prop1, prop2)
        elif prop_name == "normalized_ast_structure":
            # Check contract variable naming policy
            use_alpha_renaming = self._should_use_alpha_renaming(contract)
            
            if use_alpha_renaming:
                # Use α-renamed hash for variable-name-agnostic comparison
                alpha_hash1 = prop1.get("alpha_renamed_hash", prop1.get("ast_hash"))
                alpha_hash2 = prop2.get("alpha_renamed_hash", prop2.get("ast_hash"))
            else:
                # Use actual AST hash (variable names matter)
                alpha_hash1 = prop1.get("ast_hash")
                alpha_hash2 = prop2.get("ast_hash")
            
            return 0.0 if alpha_hash1 == alpha_hash2 else 1.0
        elif prop_name == "behavioral_signature":
            # Behavioral signatures must match exactly for semantic equivalence
            hash1 = prop1.get("io_signature_hash")
            hash2 = prop2.get("io_signature_hash")
            if hash1 is None or hash2 is None:
                return 0.5  # Partial penalty if can't execute
            return 0.0 if hash1 == hash2 else 1.0
        elif prop_name == "recursion_schema":
            return self._distance_recursion_schema(prop1, prop2)
        elif isinstance(prop1, dict) and isinstance(prop2, dict):
            return self._distance_dict(prop1, prop2)
        elif isinstance(prop1, list) and isinstance(prop2, list):
            return self._distance_list(prop1, prop2)
        else:
            return 0.0 if prop1 == prop2 else 1.0
    
    def _distance_control_flow(self, cf1: Dict, cf2: Dict) -> float:
        """Calculate distance for control flow signatures"""
        distances = []
        
        for key in ["if_statements", "for_loops", "while_loops", "nested_depth"]:
            val1 = cf1.get(key, 0)
            val2 = cf2.get(key, 0)
            max_val = max(val1, val2, 1)
            distances.append(abs(val1 - val2) / max_val)
        
        return sum(distances) / len(distances)
    
    def _distance_dict(self, d1: Dict, d2: Dict) -> float:
        """Calculate distance between dictionaries"""
        all_keys = set(d1.keys()) | set(d2.keys())
        if not all_keys:
            return 0.0
        
        differences = 0
        for key in all_keys:
            if key not in d1 or key not in d2 or d1[key] != d2[key]:
                differences += 1
        
        return differences / len(all_keys)
    
    def _distance_list(self, l1: List, l2: List) -> float:
        """Calculate distance between lists"""
        if not l1 and not l2:
            return 0.0
        
        max_len = max(len(l1), len(l2), 1)
        common = len(set(l1) & set(l2))
        
        return 1.0 - (common / max_len)
    
    def _distance_recursion_schema(self, rs1: Dict, rs2: Dict) -> float:
        """Calculate distance between recursion schemas"""
        distances = []
        
        # Recursion type match (critical)
        if rs1.get("is_recursive") != rs2.get("is_recursive"):
            return 1.0  # Completely different if one recursive, one not
        
        if not rs1.get("is_recursive"):
            return 0.0  # Both non-recursive
        
        # Recursion pattern match (critical for algorithm type)
        pattern1 = rs1.get("recursion_pattern")
        pattern2 = rs2.get("recursion_pattern")
        distances.append(0.0 if pattern1 == pattern2 else 1.0)
        
        # Number of base cases
        bc1 = len(rs1.get("base_cases", []))
        bc2 = len(rs2.get("base_cases", []))
        max_bc = max(bc1, bc2, 1)
        distances.append(abs(bc1 - bc2) / max_bc)
        
        # Number of recursive calls
        rc1 = len(rs1.get("recursive_calls", []))
        rc2 = len(rs2.get("recursive_calls", []))
        max_rc = max(rc1, rc2, 1)
        distances.append(abs(rc1 - rc2) / max_rc)
        
        return sum(distances) / len(distances) if distances else 0.0
    
    def _should_use_alpha_renaming(self, contract: Optional[Dict[str, Any]]) -> bool:
        """
        Determine if α-renaming should be used based on contract variable naming policy
        
        Args:
            contract: Contract with variable_naming constraints
            
        Returns:
            True if α-renaming should be used (variable names don't matter)
            False if variable names must be preserved
        """
        if not contract:
            # No contract: default to alpha renaming (backward compatibility)
            return True
        
        # Check if contract specifies variable_naming
        constraints = contract.get("constraints", {})
        var_naming = constraints.get("variable_naming", {})
        
        naming_policy = var_naming.get("naming_policy", "flexible")
        
        # If policy is "strict", variable names matter - don't use alpha renaming
        if naming_policy == "strict":
            return False
        
        # If policy is "flexible" but there are fixed_variables, 
        # we still need to respect those, but this is handled elsewhere
        # For now, flexible means we can use alpha renaming
        return True
