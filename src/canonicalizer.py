# src/canonicalizer.py

import ast
import hashlib
import re
import subprocess
import tempfile
import os
from typing import Dict, Any, Tuple, List
from dataclasses import dataclass
from contract import PromptContract

@dataclass
class CanonicalHashes:
    canonical_hash: str  # H: hash of canonical code structure
    behavior_hash: str   # B: hash of test execution results
    raw_code_hash: str   # Original code hash for tracking

@dataclass 
class CanonicalizationResult:
    canonical_code: str
    hashes: CanonicalHashes
    transformations: List[str]
    tool_versions: Dict[str, str]

class Canonicalizer:
    """Converts code to canonical form and generates stable hashes"""
    
    def __init__(self, contract: PromptContract):
        self.contract = contract
        
        # Default canonicalization policy
        self.default_policy = {
            "formatting_version": "black==23.1.0",
            "identifier_normalization_scope": "locals_only", 
            "literal_normalization": True,
            "hashing_recipe": "ast_normalized"
        }
        
        self.policy = contract.canonicalization_policy or self.default_policy
        self.transformations = []
    
    def canonicalize(self, code: str) -> CanonicalizationResult:
        """
        Convert code to canonical form and generate hashes
        """
        self.transformations = []
        
        # Step 1: Strip comments and docstrings
        canonical_code = self._strip_comments_docstrings(code)
        
        # Step 2: Format with black and isort (pinned versions)
        canonical_code = self._format_with_tools(canonical_code)
        
        # Step 3: Normalize literals and quotes
        if self.policy["literal_normalization"]:
            canonical_code = self._normalize_literals(canonical_code)
        
        # Step 4: Alpha-rename local identifiers only
        if self.policy["identifier_normalization_scope"] == "locals_only":
            canonical_code = self._normalize_local_identifiers(canonical_code)
        
        # Step 5: Ensure deterministic output ordering
        canonical_code = self._ensure_deterministic_ordering(canonical_code)
        
        # Step 6: Generate hashes
        hashes = self._generate_hashes(code, canonical_code)
        
        # Step 7: Get tool versions for audit
        tool_versions = self._get_tool_versions()
        
        return CanonicalizationResult(
            canonical_code=canonical_code,
            hashes=hashes,
            transformations=self.transformations,
            tool_versions=tool_versions
        )
    
    def _strip_comments_docstrings(self, code: str) -> str:
        """Remove comments and docstrings"""
        try:
            tree = ast.parse(code)
            
            # Remove docstrings (first string literal in functions/classes/modules)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                    if (node.body and isinstance(node.body[0], ast.Expr) and 
                        isinstance(node.body[0].value, ast.Constant) and 
                        isinstance(node.body[0].value.value, str)):
                        node.body.pop(0)
            
            # Convert back to code (this removes comments automatically)
            canonical = ast.unparse(tree)
            self.transformations.append("stripped_comments_docstrings")
            return canonical
            
        except SyntaxError:
            # If AST parsing fails, fall back to regex-based comment removal
            lines = []
            for line in code.split('\n'):
                # Remove inline comments but preserve strings
                if '#' in line and not self._is_in_string(line, line.find('#')):
                    line = line[:line.find('#')].rstrip()
                if line.strip():  # Keep non-empty lines
                    lines.append(line)
            
            self.transformations.append("stripped_comments_regex_fallback")
            return '\n'.join(lines)
    
    def _format_with_tools(self, code: str) -> str:
        """Format code with pinned black and isort versions"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            try:
                # Run isort first
                subprocess.run(['python', '-m', 'isort', '--profile', 'black', temp_path], 
                             check=True, capture_output=True)
                self.transformations.append("isort_applied")
                
                # Then run black
                subprocess.run(['python', '-m', 'black', '--quiet', temp_path], 
                             check=True, capture_output=True)
                self.transformations.append("black_applied")
                
                # Read formatted result
                with open(temp_path, 'r') as f:
                    formatted_code = f.read()
                
                return formatted_code
                
            finally:
                os.unlink(temp_path)
                
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback: basic formatting if tools not available
            self.transformations.append("basic_formatting_fallback")
            return self._basic_format(code)
    
    def _normalize_literals(self, code: str) -> str:
        """Normalize string quotes and other literals"""
        # Convert double quotes to single quotes (except for strings containing single quotes)
        normalized = re.sub(r'"([^"\']*)"', r"'\1'", code)
        
        # Normalize numeric literals (remove unnecessary .0 from floats that are integers)
        normalized = re.sub(r'\b(\d+)\.0\b', r'\1', normalized)
        
        if normalized != code:
            self.transformations.append("normalized_literals")
        
        return normalized
    
    def _normalize_local_identifiers(self, code: str) -> str:
        """Alpha-rename local variables only, preserve public API"""
        try:
            tree = ast.parse(code)
            
            # Find function definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Only rename if this is not the required function name
                    if node.name != self.contract.function_name:
                        continue
                    
                    # Collect local variable names (excluding parameters)
                    local_vars = set()
                    param_names = {arg.arg for arg in node.args.args}
                    
                    for child in ast.walk(node):
                        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                            if child.id not in param_names:
                                local_vars.add(child.id)
                    
                    # Create mapping for local variables only
                    var_mapping = {}
                    for i, var in enumerate(sorted(local_vars)):
                        if not var.startswith('_'):  # Don't rename private vars
                            var_mapping[var] = f"var{i}"
                    
                    # Apply renaming
                    if var_mapping:
                        for child in ast.walk(node):
                            if isinstance(child, ast.Name) and child.id in var_mapping:
                                child.id = var_mapping[child.id]
                        
                        self.transformations.append(f"renamed_locals_{len(var_mapping)}_vars")
            
            return ast.unparse(tree)
            
        except SyntaxError:
            return code  # Return unchanged if parsing fails
    
    def _ensure_deterministic_ordering(self, code: str) -> str:
        """Ensure any collections in output are deterministically ordered"""
        # This is a placeholder - would need more sophisticated analysis
        # to detect and fix nondeterministic collection ordering
        return code
    
    def _generate_hashes(self, raw_code: str, canonical_code: str) -> CanonicalHashes:
        """Generate canonical and behavior hashes"""
        
        # Raw code hash
        raw_hash = hashlib.sha256(raw_code.encode('utf-8')).hexdigest()[:16]
        
        # Canonical hash (H) - from normalized AST or text
        if self.policy["hashing_recipe"] == "ast_normalized":
            canonical_hash = self._ast_hash(canonical_code)
        else:
            canonical_hash = hashlib.sha256(canonical_code.encode('utf-8')).hexdigest()[:16]
        
        # Behavior hash (B) - from test execution results
        behavior_hash = self._behavior_hash(canonical_code)
        
        return CanonicalHashes(
            canonical_hash=canonical_hash,
            behavior_hash=behavior_hash,
            raw_code_hash=raw_hash
        )
    
    def _ast_hash(self, code: str) -> str:
        """Generate hash from normalized AST structure"""
        try:
            tree = ast.parse(code)
            # Create a stable string representation of the AST
            ast_str = ast.dump(tree, indent=None)
            return hashlib.sha256(ast_str.encode('utf-8')).hexdigest()[:16]
        except SyntaxError:
            # Fallback to text hash if AST parsing fails
            return hashlib.sha256(code.encode('utf-8')).hexdigest()[:16]
    
    def _behavior_hash(self, code: str) -> str:
        """Generate hash from test execution results"""
        try:
            # Execute code with test cases and capture output
            test_results = self._run_test_battery(code)
            result_str = str(sorted(test_results))  # Ensure deterministic ordering
            return hashlib.sha256(result_str.encode('utf-8')).hexdigest()[:16]
        except Exception:
            # Fallback: use canonical hash if execution fails
            return hashlib.sha256(code.encode('utf-8')).hexdigest()[:16]
    
    def _run_test_battery(self, code: str) -> List[Any]:
        """Run standardized test battery and return results"""
        # For Fibonacci functions, test with standard inputs
        test_inputs = [0, 1, 2, 5, 10, 20]
        results = []
        
        try:
            # Create a safe execution environment
            exec_globals = {}
            exec(code, exec_globals)
            
            # Find the function (assume it matches contract function_name)
            func = exec_globals.get(self.contract.function_name)
            if func:
                for test_input in test_inputs:
                    try:
                        result = func(test_input)
                        results.append((test_input, result))
                    except Exception as e:
                        results.append((test_input, f"ERROR: {type(e).__name__}"))
            
        except Exception:
            results = [("execution_failed", "ERROR")]
        
        return results
    
    def _get_tool_versions(self) -> Dict[str, str]:
        """Get versions of formatting tools for audit trail"""
        versions = {}
        
        try:
            # Get black version
            result = subprocess.run(['python', '-m', 'black', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                versions['black'] = result.stdout.strip()
        except:
            versions['black'] = 'unknown'
        
        try:
            # Get isort version  
            result = subprocess.run(['python', '-m', 'isort', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                versions['isort'] = result.stdout.strip()
        except:
            versions['isort'] = 'unknown'
        
        return versions
    
    def _basic_format(self, code: str) -> str:
        """Basic formatting fallback when tools unavailable"""
        lines = []
        indent_level = 0
        
        for line in code.split('\n'):
            stripped = line.strip()
            if not stripped:
                continue
                
            # Simple indentation logic
            if stripped.endswith(':'):
                lines.append('    ' * indent_level + stripped)
                indent_level += 1
            elif stripped in ['else:', 'elif', 'except:', 'finally:']:
                indent_level = max(0, indent_level - 1)
                lines.append('    ' * indent_level + stripped)
                indent_level += 1
            else:
                lines.append('    ' * indent_level + stripped)
        
        return '\n'.join(lines)
    
    def _is_in_string(self, line: str, pos: int) -> bool:
        """Check if position is inside a string literal"""
        in_single = False
        in_double = False
        i = 0
        
        while i < pos:
            if line[i] == "'" and not in_double:
                in_single = not in_single
            elif line[i] == '"' and not in_single:
                in_double = not in_double
            elif line[i] == '\\' and (in_single or in_double):
                i += 1  # Skip escaped character
            i += 1
        
        return in_single or in_double

def canonicalize_code(code: str, contract: PromptContract) -> CanonicalizationResult:
    """
    Convenience function to canonicalize code
    """
    canonicalizer = Canonicalizer(contract)
    return canonicalizer.canonicalize(code)
