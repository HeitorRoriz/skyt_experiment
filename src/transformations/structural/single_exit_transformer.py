"""
Single Exit Point Transformer - MISRA C Rule 15.5
Converts multiple return statements to single exit point with result variable
"""

import ast
from typing import Optional
from ..transformation_base import TransformationBase, TransformationResult


class SingleExitTransformer(TransformationBase):
    """
    Transforms code to have a single exit point (MISRA C Rule 15.5)
    
    Converts patterns like:
        if n <= 1:
            return False
        ...
        return True
    
    To:
        result = True
        if n <= 1:
            result = False
        ...
        return result
    """
    
    def __init__(self):
        super().__init__(
            name="SingleExitTransformer",
            description="Convert multiple returns to single exit point (MISRA 15.5)"
        )
    
    def can_transform(self, code: str, canon_code: str, property_diffs: list = None) -> bool:
        """Check if code has multiple exit points (returns or breaks) that need handling"""
        tree = self.safe_parse_ast(code)
        if not tree:
            return False
        
        # Count return statements and breaks in function
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                returns = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
                breaks = [n for n in ast.walk(node) if isinstance(n, ast.Break)]
                
                # Can transform if more than 1 return
                if len(returns) > 1:
                    return True
                
                # Can transform if there are breaks in while loops (need flag for termination)
                if breaks:
                    for stmt in ast.walk(node):
                        if isinstance(stmt, ast.While):
                            for child in ast.walk(stmt):
                                if isinstance(child, ast.Break):
                                    return True
                
                # Check for early returns (return inside if, not at end)
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.If):
                        for child in ast.walk(stmt):
                            if isinstance(child, ast.Return):
                                return True
        return False
    
    def _apply_transformation(self, code: str, canon_code: str) -> str:
        """Apply single exit point transformation"""
        tree = self.safe_parse_ast(code)
        if not tree:
            return code
        
        transformer = SingleExitNodeTransformer()
        new_tree = transformer.visit(tree)
        
        if transformer.modified:
            ast.fix_missing_locations(new_tree)
            try:
                return ast.unparse(new_tree)
            except:
                return code
        return code


class SingleExitNodeTransformer(ast.NodeTransformer):
    """AST transformer for single exit point conversion"""
    
    def __init__(self):
        self.modified = False
        self._needs_flag = False
    
    def _check_needs_flag(self, func_node: ast.FunctionDef) -> bool:
        """
        Check if we need a flag variable for loop termination.
        
        Flag needed when:
        - Function has a while loop
        - While loop contains early exit (return or break inside if/elif)
        - The exit is not the last statement in the loop
        
        Returns:
            True if flag variable needed, False otherwise
        """
        for stmt in ast.walk(func_node):
            if isinstance(stmt, ast.While):
                # Check if while loop contains early exit (return or break)
                has_early_exit = False
                for child in ast.walk(stmt):
                    if isinstance(child, ast.If):
                        # Check if this if statement contains a return or break
                        for if_child in ast.walk(child):
                            if isinstance(if_child, ast.Return) and if_child.value is not None:
                                has_early_exit = True
                                break
                            elif isinstance(if_child, ast.Break):
                                has_early_exit = True
                                break
                        if has_early_exit:
                            break
                
                if has_early_exit:
                    return True
        
        return False
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Transform function to have single exit point"""
        # First, process any nested functions
        self.generic_visit(node)
        
        # Collect all return statements
        returns = []
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and child.value is not None:
                returns.append(child)
        
        # Check if we need a flag variable for loop termination
        # Flag needed when: while loop contains early exit (return or break)
        self._needs_flag = self._check_needs_flag(node)
        
        # If only 1 return but no flag needed, nothing to do
        if len(returns) <= 1 and not self._needs_flag:
            return node
        
        # Collect return values - separate constants from variables
        constant_values = []
        variable_values = []
        for ret in returns:
            if isinstance(ret.value, ast.Constant):
                constant_values.append(ret.value.value)
            elif isinstance(ret.value, ast.Name):
                variable_values.append(ret.value.id)
            elif isinstance(ret.value, ast.UnaryOp) and isinstance(ret.value.op, ast.USub):
                # Handle negative numbers like -1
                if isinstance(ret.value.operand, ast.Constant):
                    constant_values.append(-ret.value.operand.value)
        
        # Determine initial result value
        # Priority: -1 (search not found) > False > other constants > variables
        if -1 in constant_values:
            initial_value = ast.Constant(value=-1)
            self._initial_value = -1
        elif True in constant_values and False in constant_values:
            initial_value = ast.Constant(value=True)
            self._initial_value = True
        elif False in constant_values:
            initial_value = ast.Constant(value=False)
            self._initial_value = False
        elif constant_values:
            initial_value = ast.Constant(value=constant_values[0])
            self._initial_value = constant_values[0]
        elif variable_values:
            # Use None as safe default when only variables are returned
            initial_value = ast.Constant(value=None)
            self._initial_value = None
        else:
            return node  # Can't determine initial value
        
        # Transform the function body
        new_body = []
        
        # Add result initialization
        result_assign = ast.Assign(
            targets=[ast.Name(id='result', ctx=ast.Store())],
            value=initial_value
        )
        new_body.append(result_assign)
        
        # Add flag variable if needed for loop termination
        if self._needs_flag:
            flag_assign = ast.Assign(
                targets=[ast.Name(id='found', ctx=ast.Store())],
                value=ast.Constant(value=False)
            )
            new_body.append(flag_assign)
        
        # Transform body statements (except the last return)
        body_len = len(node.body)
        for i, stmt in enumerate(node.body):
            is_last = (i == body_len - 1)
            # Skip the final return - we'll add our own
            if is_last and isinstance(stmt, ast.Return):
                continue
            transformed = self._transform_statement(stmt)
            if transformed is not None:
                if isinstance(transformed, list):
                    new_body.extend(transformed)
                else:
                    new_body.append(transformed)
        
        # Add final return statement
        new_body.append(ast.Return(value=ast.Name(id='result', ctx=ast.Load())))
        
        node.body = new_body
        self.modified = True
        return node
    
    def _transform_statement(self, stmt: ast.stmt):
        """Transform a statement, converting returns to result assignments"""
        if isinstance(stmt, ast.Return):
            if stmt.value is not None:
                # Convert return X to: result = X; found = True (if flag needed)
                assignments = [
                    ast.Assign(
                        targets=[ast.Name(id='result', ctx=ast.Store())],
                        value=stmt.value
                    )
                ]
                # Add flag assignment if needed for loop termination
                if self._needs_flag:
                    assignments.append(
                        ast.Assign(
                            targets=[ast.Name(id='found', ctx=ast.Store())],
                            value=ast.Constant(value=True)
                        )
                    )
                return assignments if len(assignments) > 1 else assignments[0]
            return None  # Remove bare return
        
        elif isinstance(stmt, ast.If):
            # Transform if statement body and orelse
            new_body = []
            for s in stmt.body:
                transformed = self._transform_statement(s)
                if transformed is not None:
                    if isinstance(transformed, list):
                        new_body.extend(transformed)
                    else:
                        new_body.append(transformed)
            
            new_orelse = []
            for s in stmt.orelse:
                transformed = self._transform_statement(s)
                if transformed is not None:
                    if isinstance(transformed, list):
                        new_orelse.extend(transformed)
                    else:
                        new_orelse.append(transformed)
            
            # Keep the if statement with transformed body
            if new_body:  # Only keep if there's something in the body
                stmt.body = new_body
                stmt.orelse = new_orelse
                return stmt
            return None
        
        elif isinstance(stmt, ast.For) or isinstance(stmt, ast.While):
            # Transform loop body
            new_body = []
            for s in stmt.body:
                transformed = self._transform_statement(s)
                if transformed is not None:
                    if isinstance(transformed, list):
                        new_body.extend(transformed)
                    else:
                        new_body.append(transformed)
            stmt.body = new_body if new_body else [ast.Pass()]
            
            # If we're using a flag variable, add it to the while loop condition
            if self._needs_flag and isinstance(stmt, ast.While):
                # Change: while condition
                # To: while condition and not found
                not_found = ast.UnaryOp(
                    op=ast.Not(),
                    operand=ast.Name(id='found', ctx=ast.Load())
                )
                stmt.test = ast.BoolOp(
                    op=ast.And(),
                    values=[stmt.test, not_found]
                )
            
            return stmt
        
        return stmt  # Return unchanged for other statements
