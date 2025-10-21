"""
AST Pattern Library
Reusable AST pattern matchers and replacers for code transformations
"""

import ast
from typing import Optional, Dict, Any, List, Callable


# ============================================================================
# PATTERN MATCHERS
# ============================================================================

def match_len_zero_check(node: ast.AST) -> Optional[Dict[str, Any]]:
    """
    Match: len(x) == 0 or len(x) != 0
    Returns: {'target': variable_name, 'operator': 'Eq' or 'NotEq'}
    """
    if not isinstance(node, ast.Compare):
        return None
    
    # Check if left side is len(x)
    if not (isinstance(node.left, ast.Call) and
            isinstance(node.left.func, ast.Name) and
            node.left.func.id == 'len' and
            len(node.left.args) == 1):
        return None
    
    # Check if comparing to 0
    if not (len(node.ops) == 1 and
            len(node.comparators) == 1 and
            isinstance(node.comparators[0], ast.Constant) and
            node.comparators[0].value == 0):
        return None
    
    # Extract target variable
    target_arg = node.left.args[0]
    target_name = extract_variable_name(target_arg)
    
    if not target_name:
        return None
    
    # Determine operator
    op_type = type(node.ops[0]).__name__
    
    return {
        'target': target_name,
        'operator': op_type,
        'original_node': node
    }


def match_boolean_redundancy(node: ast.AST) -> Optional[Dict[str, Any]]:
    """
    Match: x == True, x == False, x != True, x != False
    Returns: {'target': variable_name, 'operator': op, 'value': bool}
    """
    if not isinstance(node, ast.Compare):
        return None
    
    # Check if comparing to boolean constant
    if not (len(node.ops) == 1 and
            len(node.comparators) == 1 and
            isinstance(node.comparators[0], ast.Constant) and
            isinstance(node.comparators[0].value, bool)):
        return None
    
    target_name = extract_variable_name(node.left)
    if not target_name:
        return None
    
    return {
        'target': target_name,
        'operator': type(node.ops[0]).__name__,
        'value': node.comparators[0].value,
        'original_node': node
    }


def match_append_in_loop(tree: ast.AST) -> Optional[Dict[str, Any]]:
    """
    Match: for x in iterable: list.append(x) [with optional if]
    Returns: {'list_var': name, 'loop_var': name, 'iterable': name, 'condition': ast or None}
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.For):
            continue
        
        # Check if loop has append call
        for stmt in node.body:
            # Direct append
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                if _is_append_call(stmt.value):
                    return {
                        'list_var': extract_variable_name(stmt.value.func.value),
                        'loop_var': extract_variable_name(node.target),
                        'iterable': extract_variable_name(node.iter),
                        'condition': None,
                        'original_node': node
                    }
            
            # Conditional append: if condition: list.append(x)
            if isinstance(stmt, ast.If):
                for if_stmt in stmt.body:
                    if isinstance(if_stmt, ast.Expr) and isinstance(if_stmt.value, ast.Call):
                        if _is_append_call(if_stmt.value):
                            return {
                                'list_var': extract_variable_name(if_stmt.value.func.value),
                                'loop_var': extract_variable_name(node.target),
                                'iterable': extract_variable_name(node.iter),
                                'condition': stmt.test,
                                'original_node': node
                            }
    
    return None


def match_string_concat_in_loop(tree: ast.AST) -> Optional[Dict[str, Any]]:
    """
    Match: for x in iterable: result += x
    Returns: {'result_var': name, 'loop_var': name, 'iterable': name}
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.For):
            continue
        
        # Check for augmented assignment (+=)
        for stmt in node.body:
            if isinstance(stmt, ast.AugAssign) and isinstance(stmt.op, ast.Add):
                target_name = extract_variable_name(stmt.target)
                value_name = extract_variable_name(stmt.value)
                loop_var = extract_variable_name(node.target)
                
                # Check if value is loop variable or related
                if value_name == loop_var or target_name:
                    return {
                        'result_var': target_name,
                        'loop_var': loop_var,
                        'iterable': extract_variable_name(node.iter),
                        'original_node': node
                    }
    
    return None


def match_ternary_opportunity(node: ast.AST) -> Optional[Dict[str, Any]]:
    """
    Match: if condition: return x else: return y
    Returns: {'condition': ast, 'true_value': ast, 'false_value': ast}
    """
    if not isinstance(node, ast.If):
        return None
    
    # Check if both branches are single return statements
    if (len(node.body) == 1 and isinstance(node.body[0], ast.Return) and
        len(node.orelse) == 1 and isinstance(node.orelse[0], ast.Return)):
        
        return {
            'condition': node.test,
            'true_value': node.body[0].value,
            'false_value': node.orelse[0].value,
            'original_node': node
        }
    
    return None


def match_separate_assign_return(tree: ast.AST) -> Optional[Dict[str, Any]]:
    """
    Match: var = var.method(args); return var
    Returns: {'var_name': name, 'method': name, 'args': list, 'assign_node': ast, 'return_node': ast}
    """
    # Find function def
    func_def = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_def = node
            break
    
    if not func_def or len(func_def.body) < 2:
        return None
    
    # Check last two statements
    if len(func_def.body) >= 2:
        second_last = func_def.body[-2]
        last = func_def.body[-1]
        
        # Check if second_last is: var = var.method(args)
        if isinstance(second_last, ast.Assign) and isinstance(last, ast.Return):
            if len(second_last.targets) == 1 and isinstance(second_last.targets[0], ast.Name):
                target_name = second_last.targets[0].id
                
                # Check if value is var.method(...)
                if isinstance(second_last.value, ast.Call):
                    if isinstance(second_last.value.func, ast.Attribute):
                        obj = second_last.value.func.value
                        if isinstance(obj, ast.Name) and obj.id == target_name:
                            # Check if return statement returns same var
                            if isinstance(last.value, ast.Name) and last.value.id == target_name:
                                return {
                                    'var_name': target_name,
                                    'method': second_last.value.func.attr,
                                    'call_node': second_last.value,
                                    'assign_node': second_last,
                                    'return_node': last,
                                    'original_nodes': (second_last, last)
                                }
    
    return None


# ============================================================================
# PATTERN REPLACERS
# ============================================================================

def replace_len_check_with_bool(match: Dict[str, Any]) -> str:
    """
    Replace len(x) == 0 with 'not x'
    Replace len(x) != 0 with 'x'
    """
    target = match['target']
    operator = match['operator']
    
    if operator == 'Eq':
        return f"not {target}"
    elif operator == 'NotEq':
        return target
    else:
        return None


def replace_boolean_redundancy(match: Dict[str, Any]) -> str:
    """
    Replace x == True with 'x'
    Replace x == False with 'not x'
    Replace x != True with 'not x'
    Replace x != False with 'x'
    """
    target = match['target']
    operator = match['operator']
    value = match['value']
    
    if operator == 'Eq':
        return target if value else f"not {target}"
    elif operator == 'NotEq':
        return f"not {target}" if value else target
    else:
        return None


def replace_append_loop_with_comprehension(match: Dict[str, Any]) -> str:
    """
    Replace: for x in iterable: list.append(x)
    With: list = [x for x in iterable]
    
    Replace: for x in iterable: if cond: list.append(x)
    With: list = [x for x in iterable if cond]
    """
    list_var = match['list_var']
    loop_var = match['loop_var']
    iterable = match['iterable']
    condition = match['condition']
    
    if condition:
        # Convert condition AST to string
        cond_str = ast.unparse(condition)
        return f"{list_var} = [{loop_var} for {loop_var} in {iterable} if {cond_str}]"
    else:
        return f"{list_var} = [{loop_var} for {loop_var} in {iterable}]"


def replace_string_concat_with_join(match: Dict[str, Any]) -> str:
    """
    Replace: for x in iterable: result += x
    With: result = ''.join(iterable)
    """
    result_var = match['result_var']
    iterable = match['iterable']
    
    return f"{result_var} = ''.join({iterable})"


def replace_if_else_with_ternary(match: Dict[str, Any]) -> str:
    """
    Replace: if cond: return x else: return y
    With: return x if cond else y
    """
    condition = ast.unparse(match['condition'])
    true_value = ast.unparse(match['true_value'])
    false_value = ast.unparse(match['false_value'])
    
    return f"return {true_value} if {condition} else {false_value}"


def replace_separate_with_inline_return(match: Dict[str, Any]) -> str:
    """
    Replace: var = var.method(args); return var
    With: return var.method(args)
    """
    var_name = match['var_name']
    call_node = match['call_node']
    
    # Unparse the call expression
    call_expr = ast.unparse(call_node)
    
    return f"return {call_expr}"


# ============================================================================
# UTILITIES
# ============================================================================

def extract_variable_name(node: ast.AST) -> Optional[str]:
    """Extract variable name from AST node"""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        # For things like self.x, return 'x'
        return node.attr
    elif isinstance(node, ast.Subscript):
        # For things like list[0], return the base name
        return extract_variable_name(node.value)
    return None


def find_pattern_in_tree(tree: ast.AST, pattern_func: Callable) -> List[Dict[str, Any]]:
    """
    Find all occurrences of a pattern in AST tree
    
    Args:
        tree: AST to search
        pattern_func: Pattern matcher function
        
    Returns:
        List of match dictionaries
    """
    matches = []
    
    for node in ast.walk(tree):
        match = pattern_func(node)
        if match:
            matches.append(match)
    
    return matches


def find_return_statements(tree: ast.AST) -> List[ast.Return]:
    """Find all return statements in tree"""
    returns = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Return):
            returns.append(node)
    return returns


def find_function_def(tree: ast.AST, func_name: Optional[str] = None) -> Optional[ast.FunctionDef]:
    """
    Find function definition in tree
    If func_name is None, returns first function found
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if func_name is None or node.name == func_name:
                return node
    return None


def replace_node_in_tree(tree: ast.AST, old_node: ast.AST, new_node: ast.AST) -> ast.AST:
    """
    Replace a node in the AST tree
    Returns modified tree
    """
    class NodeReplacer(ast.NodeTransformer):
        def visit(self, node):
            if node is old_node:
                return new_node
            return self.generic_visit(node)
    
    replacer = NodeReplacer()
    return replacer.visit(tree)


def apply_pattern_replacement(code: str, match: Dict[str, Any], 
                              replacer_func: Callable) -> Optional[str]:
    """
    Apply a pattern replacement to code
    
    Args:
        code: Original code string
        match: Match dictionary from pattern matcher
        replacer_func: Function that generates replacement code
        
    Returns:
        Modified code string or None if replacement failed
    """
    try:
        tree = ast.parse(code)
        original_node = match.get('original_node')
        
        if not original_node:
            return None
        
        # Generate replacement code
        replacement_str = replacer_func(match)
        if not replacement_str:
            return None
        
        # Parse replacement
        replacement_node = ast.parse(replacement_str).body[0]
        
        # If it's a statement, use it directly
        # If it's an expression, extract the value
        if isinstance(replacement_node, ast.Expr):
            replacement_node = replacement_node.value
        
        # Replace in tree
        new_tree = replace_node_in_tree(tree, original_node, replacement_node)
        
        # Convert back to code
        return ast.unparse(new_tree)
        
    except Exception:
        return None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _is_append_call(node: ast.Call) -> bool:
    """Check if node is a .append() call"""
    return (isinstance(node.func, ast.Attribute) and
            node.func.attr == 'append' and
            len(node.args) == 1)


def _is_string_type(node: ast.AST) -> bool:
    """Check if node represents a string"""
    if isinstance(node, ast.Constant):
        return isinstance(node.value, str)
    return False


def get_node_line_range(node: ast.AST) -> tuple:
    """Get line range of a node (start, end)"""
    if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
        return (node.lineno, node.end_lineno)
    return (0, 0)
