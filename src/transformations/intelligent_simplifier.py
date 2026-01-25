#!/usr/bin/env python3
"""
Intelligent Code Simplifier: Pattern-agnostic redundancy removal.

Strategy:
1. Compare code to canon structurally (AST diff)
2. Identify statements present in code but not in canon
3. Test each extra statement: Can it be removed safely?
4. Remove statements that don't affect correctness

This is NOT hardcoded for specific patterns - it works for any code/canon pair.
"""

import ast
import astor
from typing import Dict, Any, List, Tuple
import copy

class StatementRemovalTester:
    """Tests if removing a statement preserves behavior"""
    
    def __init__(self, oracle_system, contract: Dict[str, Any]):
        self.oracle_system = oracle_system
        self.contract = contract
    
    def can_remove_safely(self, code: str, statement_to_remove: ast.stmt) -> bool:
        """
        Test if removing a statement preserves correctness.
        
        Strategy: Remove statement, run oracle tests, check if still passes.
        """
        try:
            # Parse code
            tree = ast.parse(code)
            
            # Remove the statement
            modified_tree = self._remove_statement_from_tree(tree, statement_to_remove)
            
            # Generate modified code
            modified_code = astor.to_source(modified_tree)
            
            # Run oracle tests on modified code
            oracle_result = self.oracle_system.run_oracle_tests(modified_code, self.contract)
            
            return oracle_result.get('passed', False)
            
        except Exception as e:
            # If anything fails, assume not safe to remove
            return False
    
    def _remove_statement_from_tree(self, tree: ast.AST, stmt_to_remove: ast.stmt) -> ast.AST:
        """Remove a specific statement from AST"""
        
        class StatementRemover(ast.NodeTransformer):
            def __init__(self, target_stmt):
                self.target_stmt = target_stmt
                self.removed = False
            
            def visit_FunctionDef(self, node):
                # Filter out the target statement from function body
                new_body = []
                for stmt in node.body:
                    if not self._statements_equal(stmt, self.target_stmt):
                        new_body.append(self.visit(stmt))
                    else:
                        self.removed = True
                
                node.body = new_body if new_body else [ast.Pass()]
                return node
            
            def _statements_equal(self, s1, s2):
                """Check if two statements are structurally equal"""
                return ast.dump(s1) == ast.dump(s2)
        
        remover = StatementRemover(stmt_to_remove)
        return remover.visit(copy.deepcopy(tree))


class ASTDiffer:
    """Finds structural differences between code and canon"""
    
    @staticmethod
    def find_extra_statements(code: str, canon_code: str, func_name: str) -> List[ast.stmt]:
        """
        Find statements in code that are NOT in canon.
        
        Returns list of statements that could potentially be removed.
        """
        code_tree = ast.parse(code)
        canon_tree = ast.parse(canon_code)
        
        # Extract function bodies
        code_func = ASTDiffer._find_function(code_tree, func_name)
        canon_func = ASTDiffer._find_function(canon_tree, func_name)
        
        if not code_func or not canon_func:
            return []
        
        # Get statement dumps for comparison
        canon_stmts = {ast.dump(stmt) for stmt in canon_func.body}
        
        # Find statements in code but not in canon
        extra_statements = []
        for stmt in code_func.body:
            stmt_dump = ast.dump(stmt)
            if stmt_dump not in canon_stmts:
                extra_statements.append(stmt)
        
        return extra_statements
    
    @staticmethod
    def _find_function(tree: ast.AST, func_name: str) -> ast.FunctionDef:
        """Find function definition by name"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                return node
        return None


def intelligent_simplify(code: str, canon_code: str, contract: Dict[str, Any], 
                        oracle_system) -> Dict[str, Any]:
    """
    Intelligently simplify code to match canon by removing redundant statements.
    
    This is pattern-agnostic - it works by:
    1. Finding statements in code but not in canon
    2. Testing if each can be removed safely (oracle tests)
    3. Removing safe-to-remove statements
    
    Args:
        code: Source code to simplify
        canon_code: Canonical form to match
        contract: Contract specification
        oracle_system: Oracle for testing correctness
        
    Returns:
        Dict with simplified code and metadata
    """
    
    func_name = contract.get('constraints', {}).get('function_name')
    if not func_name:
        return {
            'success': False,
            'transformed_code': code,
            'error': 'No function name in contract'
        }
    
    # Find extra statements
    differ = ASTDiffer()
    extra_statements = differ.find_extra_statements(code, canon_code, func_name)
    
    if not extra_statements:
        # No extra statements - code already matches canon structurally
        return {
            'success': True,
            'transformed_code': code,
            'removed_statements': [],
            'description': 'No redundant statements found'
        }
    
    # Test each statement for safe removal
    tester = StatementRemovalTester(oracle_system, contract)
    current_code = code
    removed_statements = []
    
    for stmt in extra_statements:
        if tester.can_remove_safely(current_code, stmt):
            # Safe to remove - do it
            tree = ast.parse(current_code)
            modified_tree = tester._remove_statement_from_tree(tree, stmt)
            current_code = astor.to_source(modified_tree)
            removed_statements.append(ast.dump(stmt)[:50])  # Store description
    
    return {
        'success': len(removed_statements) > 0,
        'transformed_code': current_code,
        'removed_statements': removed_statements,
        'description': f'Removed {len(removed_statements)} redundant statements'
    }


if __name__ == "__main__":
    # Test with Claude's is_prime (has extra statements)
    
    claude_code = """def is_prime(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
"""
    
    canon_code = """def is_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
"""
    
    contract = {
        'constraints': {
            'function_name': 'is_prime'
        }
    }
    
    # Mock oracle system for testing
    class MockOracle:
        def run_oracle_tests(self, code, contract):
            # Execute code and test
            try:
                exec_globals = {}
                exec(code, exec_globals)
                is_prime = exec_globals['is_prime']
                
                # Test cases
                tests = [
                    (2, True), (3, True), (4, False), (5, True),
                    (6, False), (7, True), (11, True), (15, False)
                ]
                
                for n, expected in tests:
                    if is_prime(n) != expected:
                        return {'passed': False}
                
                return {'passed': True}
            except:
                return {'passed': False}
    
    print("="*80)
    print("INTELLIGENT SIMPLIFIER TEST")
    print("="*80)
    
    print("\nOriginal (Claude with extra statements):")
    print(claude_code)
    
    print("\nCanon (simple form):")
    print(canon_code)
    
    oracle = MockOracle()
    result = intelligent_simplify(claude_code, canon_code, contract, oracle)
    
    print("\n" + "="*80)
    print("RESULT")
    print("="*80)
    
    print(f"\nSuccess: {result['success']}")
    print(f"Removed statements: {len(result.get('removed_statements', []))}")
    
    print("\nTransformed code:")
    print(result['transformed_code'])
    
    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80)
    
    # Verify transformed code matches canon behavior
    exec_globals_canon = {}
    exec(canon_code, exec_globals_canon)
    is_prime_canon = exec_globals_canon['is_prime']
    
    exec_globals_trans = {}
    exec(result['transformed_code'], exec_globals_trans)
    is_prime_trans = exec_globals_trans['is_prime']
    
    test_cases = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 17, 25, 29, 100]
    all_match = True
    
    for n in test_cases:
        canon_result = is_prime_canon(n)
        trans_result = is_prime_trans(n)
        if canon_result != trans_result:
            print(f"  n={n}: canon={canon_result}, transformed={trans_result} ❌")
            all_match = False
    
    if all_match:
        print(f"✅ All {len(test_cases)} test cases match!")
        print("   Intelligent simplification preserves correctness")
