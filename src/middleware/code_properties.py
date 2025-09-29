# src/middleware/code_properties.py
"""
Foundational Code Properties for Canonical Sameness

Defines the fundamental properties that determine if two pieces of code
are semantically equivalent at the deepest level. Code is considered
"the same" if and only if these foundational properties match.
"""

import ast
import hashlib
from typing import Dict, Any, List, Tuple, Set, Optional
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class CodeProperties:
    """Foundational properties that define code sameness"""
    
    # 1. Computational Graph Structure
    control_flow_signature: str      # Topology of branches, loops, calls
    data_dependency_graph: str       # Variable dependency relationships
    execution_paths: str             # Canonical execution path representation
    
    # 2. Semantic Invariants  
    function_contracts: str          # Input/output type relationships
    complexity_class: str            # Algorithmic complexity (O-notation)
    side_effect_profile: str         # Pure vs stateful operations
    termination_properties: str      # Base cases, loop bounds
    
    # 3. Mathematical Properties
    algebraic_structure: str         # Commutativity, associativity
    numerical_behavior: str          # Precision, overflow handling
    logical_equivalence: str         # Boolean expression normalization
    
    # 4. Abstract Syntax Properties
    normalized_ast_structure: str    # Canonical AST representation
    operator_precedence: str         # Explicit precedence normalization
    statement_ordering: str          # Canonical statement sequence

def extract_code_properties(code: str, function_name: Optional[str] = None) -> CodeProperties:
    """
    Extract foundational properties from code
    
    Args:
        code: Python code string
        function_name: Target function name to analyze
    
    Returns:
        CodeProperties object with all foundational properties
    """
    try:
        tree = ast.parse(code)
        target_func = _find_target_function(tree, function_name)
        
        return CodeProperties(
            control_flow_signature=_extract_control_flow(target_func),
            data_dependency_graph=_extract_data_dependencies(target_func),
            execution_paths=_extract_execution_paths(target_func),
            function_contracts=_extract_function_contracts(target_func),
            complexity_class=_analyze_complexity_class(target_func),
            side_effect_profile=_analyze_side_effects(target_func),
            termination_properties=_analyze_termination(target_func),
            algebraic_structure=_extract_algebraic_structure(target_func),
            numerical_behavior=_analyze_numerical_behavior(target_func),
            logical_equivalence=_normalize_logical_expressions(target_func),
            normalized_ast_structure=_normalize_ast_structure(target_func),
            operator_precedence=_normalize_operator_precedence(target_func),
            statement_ordering=_canonicalize_statement_order(target_func)
        )
    
    except SyntaxError:
        # Return empty properties for invalid code
        return _empty_properties()

def properties_match(props1: CodeProperties, props2: CodeProperties, 
                    tolerance: float = 0.0) -> Tuple[bool, List[str]]:
    """
    Check if two code property sets represent the same foundational code
    
    Args:
        props1: First property set
        props2: Second property set
        tolerance: Tolerance for numerical differences
    
    Returns:
        Tuple of (match: bool, differences: List[str])
    """
    differences = []
    
    # Check each foundational property
    property_checks = [
        ("control_flow", props1.control_flow_signature, props2.control_flow_signature),
        ("data_dependencies", props1.data_dependency_graph, props2.data_dependency_graph),
        ("execution_paths", props1.execution_paths, props2.execution_paths),
        ("function_contracts", props1.function_contracts, props2.function_contracts),
        ("complexity_class", props1.complexity_class, props2.complexity_class),
        ("side_effects", props1.side_effect_profile, props2.side_effect_profile),
        ("termination", props1.termination_properties, props2.termination_properties),
        ("algebraic_structure", props1.algebraic_structure, props2.algebraic_structure),
        ("numerical_behavior", props1.numerical_behavior, props2.numerical_behavior),
        ("logical_equivalence", props1.logical_equivalence, props2.logical_equivalence),
        ("ast_structure", props1.normalized_ast_structure, props2.normalized_ast_structure),
        ("operator_precedence", props1.operator_precedence, props2.operator_precedence),
        ("statement_ordering", props1.statement_ordering, props2.statement_ordering),
    ]
    
    for prop_name, val1, val2 in property_checks:
        if val1 != val2:
            differences.append(f"{prop_name}_mismatch")
    
    return len(differences) == 0, differences

def compute_property_signature(properties: CodeProperties) -> str:
    """
    Compute deterministic signature from foundational properties
    
    Args:
        properties: CodeProperties object
    
    Returns:
        SHA-256 hex digest of all properties combined
    """
    # Combine all properties in deterministic order
    combined = (
        properties.control_flow_signature +
        properties.data_dependency_graph +
        properties.execution_paths +
        properties.function_contracts +
        properties.complexity_class +
        properties.side_effect_profile +
        properties.termination_properties +
        properties.algebraic_structure +
        properties.numerical_behavior +
        properties.logical_equivalence +
        properties.normalized_ast_structure +
        properties.operator_precedence +
        properties.statement_ordering
    )
    
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()

# ========== PROPERTY EXTRACTION FUNCTIONS ==========

def _find_target_function(tree: ast.AST, function_name: Optional[str]) -> Optional[ast.FunctionDef]:
    """Find target function in AST"""
    if not function_name:
        # Return first function found
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                return node
        return None
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return node
    return None

def _extract_control_flow(func: Optional[ast.FunctionDef]) -> str:
    """Extract control flow topology signature"""
    if not func:
        return "no_function"
    
    flow_elements = []
    
    for node in ast.walk(func):
        if isinstance(node, ast.If):
            flow_elements.append("branch")
        elif isinstance(node, ast.For):
            flow_elements.append("for_loop")
        elif isinstance(node, ast.While):
            flow_elements.append("while_loop")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                flow_elements.append(f"call_{node.func.id}")
        elif isinstance(node, ast.Return):
            flow_elements.append("return")
    
    return "|".join(sorted(flow_elements))

def _extract_data_dependencies(func: Optional[ast.FunctionDef]) -> str:
    """Extract data dependency graph"""
    if not func:
        return "no_dependencies"
    
    dependencies = defaultdict(set)
    
    # Track variable assignments and uses
    for node in ast.walk(func):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id
                    # Find variables used in the assignment
                    for dep_node in ast.walk(node.value):
                        if isinstance(dep_node, ast.Name):
                            dependencies[var_name].add(dep_node.id)
    
    # Create canonical dependency representation
    dep_strings = []
    for var, deps in sorted(dependencies.items()):
        dep_strings.append(f"{var}:{','.join(sorted(deps))}")
    
    return "|".join(dep_strings)

def _extract_execution_paths(func: Optional[ast.FunctionDef]) -> str:
    """Extract canonical execution path representation"""
    if not func:
        return "no_paths"
    
    # Simplified path extraction - can be enhanced
    path_elements = []
    
    def visit_node(node, path_prefix=""):
        if isinstance(node, ast.If):
            path_elements.append(f"{path_prefix}if_branch")
            for child in node.body:
                visit_node(child, path_prefix + "then_")
            for child in node.orelse:
                visit_node(child, path_prefix + "else_")
        elif isinstance(node, (ast.For, ast.While)):
            path_elements.append(f"{path_prefix}loop")
            for child in node.body:
                visit_node(child, path_prefix + "loop_")
        elif isinstance(node, ast.Return):
            path_elements.append(f"{path_prefix}return")
    
    for stmt in func.body:
        visit_node(stmt)
    
    return "|".join(path_elements)

def _extract_function_contracts(func: Optional[ast.FunctionDef]) -> str:
    """Extract function signature contracts"""
    if not func:
        return "no_contract"
    
    # Extract argument types and return behavior
    args = [arg.arg for arg in func.args.args]
    
    # Analyze return statements
    returns = []
    for node in ast.walk(func):
        if isinstance(node, ast.Return):
            if isinstance(node.value, ast.Name):
                returns.append(f"var_{node.value.id}")
            elif isinstance(node.value, ast.Constant):
                returns.append(f"const_{type(node.value.value).__name__}")
            elif isinstance(node.value, ast.List):
                returns.append("list")
            else:
                returns.append("expression")
    
    contract = f"args:{','.join(args)}|returns:{','.join(set(returns))}"
    return contract

def _analyze_complexity_class(func: Optional[ast.FunctionDef]) -> str:
    """Analyze algorithmic complexity class"""
    if not func:
        return "O(1)"
    
    # Simple heuristic-based complexity analysis
    nested_loops = 0
    recursive_calls = 0
    
    def count_nesting(node, current_depth=0):
        nonlocal nested_loops, recursive_calls
        
        if isinstance(node, (ast.For, ast.While)):
            nested_loops = max(nested_loops, current_depth + 1)
            for child in ast.iter_child_nodes(node):
                count_nesting(child, current_depth + 1)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == func.name:
                recursive_calls += 1
        else:
            for child in ast.iter_child_nodes(node):
                count_nesting(child, current_depth)
    
    count_nesting(func)
    
    if recursive_calls > 0:
        return "O(exp)"  # Exponential for recursive
    elif nested_loops >= 2:
        return "O(n^2)"
    elif nested_loops == 1:
        return "O(n)"
    else:
        return "O(1)"

def _analyze_side_effects(func: Optional[ast.FunctionDef]) -> str:
    """Analyze side effect profile"""
    if not func:
        return "pure"
    
    side_effects = []
    
    for node in ast.walk(func):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in ['print', 'input', 'open']:
                    side_effects.append("io")
        elif isinstance(node, ast.Global):
            side_effects.append("global_access")
        elif isinstance(node, ast.Nonlocal):
            side_effects.append("nonlocal_access")
    
    return "|".join(sorted(set(side_effects))) if side_effects else "pure"

def _analyze_termination(func: Optional[ast.FunctionDef]) -> str:
    """Analyze termination properties"""
    if not func:
        return "terminates"
    
    # Check for base cases in recursive functions
    has_base_case = False
    has_recursive_call = False
    
    for node in ast.walk(func):
        if isinstance(node, ast.If):
            # Check if this could be a base case
            for child in ast.walk(node):
                if isinstance(child, ast.Return):
                    has_base_case = True
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == func.name:
                has_recursive_call = True
    
    if has_recursive_call and has_base_case:
        return "recursive_with_base"
    elif has_recursive_call:
        return "recursive_no_base"
    else:
        return "iterative"

def _extract_algebraic_structure(func: Optional[ast.FunctionDef]) -> str:
    """Extract algebraic structure properties"""
    if not func:
        return "no_algebra"
    
    operations = []
    
    for node in ast.walk(func):
        if isinstance(node, ast.BinOp):
            if isinstance(node.op, ast.Add):
                operations.append("add")
            elif isinstance(node.op, ast.Mult):
                operations.append("mult")
            elif isinstance(node.op, ast.Sub):
                operations.append("sub")
            elif isinstance(node.op, ast.Div):
                operations.append("div")
    
    return "|".join(sorted(set(operations)))

def _analyze_numerical_behavior(func: Optional[ast.FunctionDef]) -> str:
    """Analyze numerical behavior"""
    if not func:
        return "no_numbers"
    
    number_types = []
    
    for node in ast.walk(func):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, int):
                number_types.append("int")
            elif isinstance(node.value, float):
                number_types.append("float")
    
    return "|".join(sorted(set(number_types)))

def _normalize_logical_expressions(func: Optional[ast.FunctionDef]) -> str:
    """Normalize logical expressions"""
    if not func:
        return "no_logic"
    
    logical_ops = []
    
    for node in ast.walk(func):
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                logical_ops.append("and")
            elif isinstance(node.op, ast.Or):
                logical_ops.append("or")
        elif isinstance(node, ast.Compare):
            for op in node.ops:
                if isinstance(op, ast.Eq):
                    logical_ops.append("eq")
                elif isinstance(op, ast.Lt):
                    logical_ops.append("lt")
                elif isinstance(op, ast.Gt):
                    logical_ops.append("gt")
    
    return "|".join(sorted(set(logical_ops)))

def _normalize_ast_structure(func: Optional[ast.FunctionDef]) -> str:
    """Normalize AST structure"""
    if not func:
        return "no_ast"
    
    # Create canonical AST representation
    node_types = []
    
    for node in ast.walk(func):
        node_types.append(type(node).__name__)
    
    # Count occurrences for canonical representation
    from collections import Counter
    counts = Counter(node_types)
    
    structure_parts = []
    for node_type, count in sorted(counts.items()):
        structure_parts.append(f"{node_type}:{count}")
    
    return "|".join(structure_parts)

def _normalize_operator_precedence(func: Optional[ast.FunctionDef]) -> str:
    """Normalize operator precedence"""
    if not func:
        return "no_operators"
    
    # Extract operator usage patterns
    operators = []
    
    for node in ast.walk(func):
        if isinstance(node, ast.BinOp):
            operators.append(type(node.op).__name__)
        elif isinstance(node, ast.UnaryOp):
            operators.append(type(node.op).__name__)
        elif isinstance(node, ast.Compare):
            for op in node.ops:
                operators.append(type(op).__name__)
    
    return "|".join(sorted(operators))

def _canonicalize_statement_order(func: Optional[ast.FunctionDef]) -> str:
    """Canonicalize statement ordering"""
    if not func:
        return "no_statements"
    
    # Extract statement types in order
    statements = []
    
    for stmt in func.body:
        statements.append(type(stmt).__name__)
    
    return "|".join(statements)

def _empty_properties() -> CodeProperties:
    """Return empty properties for invalid code"""
    return CodeProperties(
        control_flow_signature="invalid",
        data_dependency_graph="invalid",
        execution_paths="invalid",
        function_contracts="invalid",
        complexity_class="invalid",
        side_effect_profile="invalid",
        termination_properties="invalid",
        algebraic_structure="invalid",
        numerical_behavior="invalid",
        logical_equivalence="invalid",
        normalized_ast_structure="invalid",
        operator_precedence="invalid",
        statement_ordering="invalid"
    )
