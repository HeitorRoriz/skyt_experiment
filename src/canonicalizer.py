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
        
        # Step 5: Normalize control flow structures
        canonical_code = self._normalize_control_flow(canonical_code)
        
        # Step 6: Normalize algorithmic patterns
        canonical_code = self._normalize_algorithmic_patterns(canonical_code)
        
        # Step 7: Ensure deterministic output ordering
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
                print(f"        Removing comments...") 
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
        try:
            tree = ast.parse(code)
            
            # Transform nondeterministic constructs
            for node in ast.walk(tree):
                # Convert set literals to sorted lists
                if isinstance(node, ast.Set):
                    # Replace set with sorted list
                    list_node = ast.List(elts=node.elts, ctx=ast.Load())
                    sorted_call = ast.Call(
                        func=ast.Name(id='sorted', ctx=ast.Load()),
                        args=[list_node],
                        keywords=[]
                    )
                    # Replace the set node with sorted list
                    for parent in ast.walk(tree):
                        for field, value in ast.iter_fields(parent):
                            if value == node:
                                setattr(parent, field, sorted_call)
                            elif isinstance(value, list) and node in value:
                                value[value.index(node)] = sorted_call
                
                # Sort dictionary literals by keys
                elif isinstance(node, ast.Dict):
                    if node.keys and all(isinstance(k, ast.Constant) for k in node.keys):
                        # Sort by key values
                        pairs = list(zip(node.keys, node.values))
                        pairs.sort(key=lambda x: x[0].value if hasattr(x[0], 'value') else str(x[0]))
                        node.keys, node.values = zip(*pairs) if pairs else ([], [])
            
            self.transformations.append("deterministic_ordering_applied")
            return ast.unparse(tree)
            
        except:
            return code
    
    def _normalize_control_flow(self, code: str) -> str:
        """Normalize control flow patterns to canonical forms"""
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # Normalize if statements: convert `if not condition` to `if condition == False`
                if isinstance(node, ast.If):
                    if isinstance(node.test, ast.UnaryOp) and isinstance(node.test.op, ast.Not):
                        # Convert `if not x:` to `if x == False:`
                        node.test = ast.Compare(
                            left=node.test.operand,
                            ops=[ast.Eq()],
                            comparators=[ast.Constant(value=False)]
                        )
                
                # Normalize while loops similarly
                elif isinstance(node, ast.While):
                    if isinstance(node.test, ast.UnaryOp) and isinstance(node.test.op, ast.Not):
                        node.test = ast.Compare(
                            left=node.test.operand,
                            ops=[ast.Eq()],
                            comparators=[ast.Constant(value=False)]
                        )
                
                # Normalize comparison operators: convert `len(x) <= 1` to `len(x) < 2`
                elif isinstance(node, ast.Compare):
                    if len(node.ops) == 1 and isinstance(node.ops[0], ast.LtE):
                        if (isinstance(node.comparators[0], ast.Constant) and 
                            isinstance(node.comparators[0].value, int)):
                            # Convert <= to < with incremented value
                            node.ops[0] = ast.Lt()
                            node.comparators[0].value += 1
            
            self.transformations.append("control_flow_normalized")
            return ast.unparse(tree)
            
        except:
            return code
    
    def _normalize_algorithmic_patterns(self, code: str) -> str:
        """Normalize common algorithmic patterns to canonical forms"""
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # Normalize array slicing patterns
                if isinstance(node, ast.Slice):
                    # Convert `arr[mid:]` to `arr[mid:len(arr)]`
                    if node.upper is None:
                        node.upper = ast.Call(
                            func=ast.Name(id='len', ctx=ast.Load()),
                            args=[self._find_sliced_object(node, tree)],
                            keywords=[]
                        )
                    # Convert `arr[:mid]` to `arr[0:mid]`
                    if node.lower is None:
                        node.lower = ast.Constant(value=0)
                
                # Normalize range patterns: convert `range(len(x))` to explicit form
                elif isinstance(node, ast.Call):
                    if (isinstance(node.func, ast.Name) and node.func.id == 'range' and
                        len(node.args) == 1 and isinstance(node.args[0], ast.Call)):
                        if (isinstance(node.args[0].func, ast.Name) and 
                            node.args[0].func.id == 'len'):
                            # Keep as is - this is already canonical
                            pass
            
            self.transformations.append("algorithmic_patterns_normalized")
            return ast.unparse(tree)
            
        except:
            return code
    
    def _find_sliced_object(self, slice_node: ast.Slice, tree: ast.AST) -> ast.AST:
        """Find the object being sliced for a given slice node"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript) and node.slice == slice_node:
                return node.value
        # Fallback: return a generic name
        return ast.Name(id='arr', ctx=ast.Load())
    
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
        """Generate behavioral hash based on execution results and semantic properties"""
        try:
            # Level 1: I/O Behavior
            test_results = self._run_test_battery(code)
            io_behavior = str(sorted(test_results))
            
            # Level 2: Algorithmic Properties (for enhanced canonicalization)
            semantic_properties = self._extract_semantic_properties(code)
            
            # Level 3: Complexity Analysis
            complexity_signature = self._analyze_complexity_signature(code)
            
            # Combine all behavioral aspects
            combined_behavior = {
                'io_results': io_behavior,
                'semantic_props': semantic_properties,
                'complexity': complexity_signature
            }
            
            behavior_str = str(sorted(combined_behavior.items()))
            return hashlib.sha256(behavior_str.encode('utf-8')).hexdigest()[:16]
            
        except Exception as e:
            # Fallback: use canonical hash if execution fails
            return hashlib.sha256(code.encode('utf-8')).hexdigest()[:16]
    
    def _run_test_battery(self, code: str) -> List[Any]:
        """Run standardized test battery using contract test cases"""
        results = []
        
        try:
            # Create a safe execution environment
            exec_globals = {}
            exec(code, exec_globals)
            print(f"        Standardizing function name to '{contract.function_name}'...")
            func = exec_globals.get(self.contract.function_name)
            if func:
                # Use contract test cases if available
                if hasattr(self.contract, 'test_cases') and self.contract.test_cases:
                    for i, test_case in enumerate(self.contract.test_cases):
                        try:
                            test_input = test_case.get('input')
                            result = func(test_input)
                            results.append((f"test_{i}", str(result)))
                        except Exception as e:
                            results.append((f"test_{i}", f"ERROR: {type(e).__name__}"))
                else:
                    # Fallback: try to infer input type from function name for backward compatibility
                    if 'fibonacci' in self.contract.function_name.lower():
                        test_inputs = [0, 1, 2, 5, 10]
                        for test_input in test_inputs:
                            try:
                                result = func(test_input)
                                results.append((test_input, result))
                            except Exception as e:
                                results.append((test_input, f"ERROR: {type(e).__name__}"))
                                
                    elif 'merge_sort' in self.contract.function_name.lower() or 'sort' in self.contract.function_name.lower():
                        test_inputs = [[], [1], [3, 1, 2], [5, 2, 8, 1, 9]]
                        for test_input in test_inputs:
                            try:
                                result = func(test_input)
                                results.append((str(test_input), str(result)))
                            except Exception as e:
                                results.append((str(test_input), f"ERROR: {type(e).__name__}"))
                                
                    else:
                        # Generic fallback: try common input types
                        test_attempts = [
                            ("int_test", 5),
                            ("list_test", [1, 2, 3]),
                            ("str_test", "test"),
                            ("empty_test", [])
                        ]
                        for test_name, test_input in test_attempts:
                            try:
                                result = func(test_input)
                                results.append((test_name, str(result)))
                                break  # Stop after first successful test
                            except:
                                continue
                        
                        if not results:
                            results.append(("no_valid_test", "ERROR: No compatible input type found"))
            
        except Exception:
            results = [("execution_failed", "ERROR")]
        
        return results
    
    def _extract_semantic_properties(self, code: str) -> Dict[str, Any]:
        """Extract semantic properties for behavioral canonicalization"""
        properties = {}
        
        try:
            tree = ast.parse(code)
            
            # Control flow patterns
            properties['has_loops'] = any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(tree))
            properties['has_recursion'] = self._detect_recursion(tree)
            properties['has_conditionals'] = any(isinstance(node, ast.If) for node in ast.walk(tree))
            
            # Data structure usage
            properties['uses_lists'] = any(isinstance(node, ast.List) for node in ast.walk(tree))
            properties['uses_dicts'] = any(isinstance(node, ast.Dict) for node in ast.walk(tree))
            properties['uses_sets'] = any(isinstance(node, ast.Set) for node in ast.walk(tree))
            
            # Function characteristics
            func_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            if func_nodes:
                main_func = func_nodes[0]
                properties['param_count'] = len(main_func.args.args)
                properties['return_count'] = len([node for node in ast.walk(main_func) if isinstance(node, ast.Return)])
            
            # Algorithmic patterns
            properties['divide_and_conquer'] = self._detect_divide_and_conquer(tree)
            properties['iterative_pattern'] = self._detect_iterative_pattern(tree)
            
        except:
            properties = {'parse_failed': True}
        
        return properties
    
    def _analyze_complexity_signature(self, code: str) -> Dict[str, str]:
        """Analyze algorithmic complexity signature"""
        signature = {}
        
        try:
            tree = ast.parse(code)
            
            # Count nested loops (rough time complexity indicator)
            max_loop_depth = self._count_max_loop_depth(tree)
            signature['loop_depth'] = str(max_loop_depth)
            
            # Count recursive calls
            recursive_calls = self._count_recursive_calls(tree)
            signature['recursive_calls'] = str(recursive_calls)
            
            # Detect common patterns
            if max_loop_depth >= 2:
                signature['complexity_class'] = 'quadratic_or_higher'
            elif max_loop_depth == 1:
                signature['complexity_class'] = 'linear'
            elif recursive_calls > 0:
                signature['complexity_class'] = 'recursive'
            else:
                signature['complexity_class'] = 'constant'
                
        except:
            signature = {'analysis_failed': True}
        
        return signature
    
    def _detect_recursion(self, tree: ast.AST) -> bool:
        """Detect if function calls itself recursively"""
        func_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        if not func_nodes:
            return False
        
        func_name = func_nodes[0].name
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == func_name:
                    return True
        return False
    
    def _detect_divide_and_conquer(self, tree: ast.AST) -> bool:
        """Detect divide-and-conquer pattern"""
        # Look for recursive calls with array slicing
        has_recursion = self._detect_recursion(tree)
        has_slicing = any(isinstance(node, ast.Slice) for node in ast.walk(tree))
        return has_recursion and has_slicing
    
    def _detect_iterative_pattern(self, tree: ast.AST) -> bool:
        """Detect iterative processing pattern"""
        has_loops = any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(tree))
        no_recursion = not self._detect_recursion(tree)
        return has_loops and no_recursion
    
    def _count_max_loop_depth(self, tree: ast.AST) -> int:
        """Count maximum nesting depth of loops"""
        max_depth = 0
        
        def count_depth(node, current_depth=0):
            nonlocal max_depth
            if isinstance(node, (ast.For, ast.While)):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            
            for child in ast.iter_child_nodes(node):
                count_depth(child, current_depth)
        
        count_depth(tree)
        return max_depth
    
    def _count_recursive_calls(self, tree: ast.AST) -> int:
        """Count number of recursive function calls"""
        func_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        if not func_nodes:
            return 0
        
        func_name = func_nodes[0].name
        call_count = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == func_name:
                    call_count += 1
        
        return call_count
    
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

    def generate_canonical_template(self) -> str:
        """Generate canonical code template from contract specifications"""
        contract = self.contract
        
        # Build canonical template from contract
        template_parts = []
        
        # Function signature from contract
        if hasattr(contract, 'method_signature') and contract.method_signature:
            # Use exact signature from contract
            template_parts.append(f"# Contract signature: {contract.method_signature}")
        
        # Function definition with canonical structure
        function_name = contract.function_name
        
        # Derive parameter structure from test cases if available
        params = self._extract_canonical_parameters()
        
        # Build canonical function template
        canonical_func = f"""def {function_name}({params}):
    \"\"\"
    {contract.required_logic or 'Implement as per contract requirements'}
    
    Args:
        {self._generate_param_docs()}
    
    Returns:
        {contract.output_type}: {contract.output_format}
    \"\"\"
    {self._generate_canonical_body()}
"""
        
        template_parts.append(canonical_func)
        
        # Add test validation structure
        if contract.test_cases:
            template_parts.append(self._generate_test_validation())
        
        canonical_template = "\n".join(template_parts)
        
        # Apply standard canonicalization to template
        return self._apply_standard_canonicalization(canonical_template)
    
    def _extract_canonical_parameters(self) -> str:
        """Extract canonical parameter list from contract test cases"""
        if not self.contract.test_cases or not self.contract.test_cases:
            return "n"  # Default parameter
        
        # Analyze first test case to determine parameter structure
        first_test = self.contract.test_cases[0]
        if 'input' in first_test:
            input_data = first_test['input']
            if isinstance(input_data, dict):
                # Multiple parameters
                return ", ".join(sorted(input_data.keys()))
            else:
                # Single parameter
                return "n"
        return "n"
    
    def _generate_param_docs(self) -> str:
        """Generate canonical parameter documentation"""
        params = self._extract_canonical_parameters()
        if params == "n":
            return "n: Input parameter"
        else:
            param_list = params.split(", ")
            return "\n        ".join([f"{p}: Parameter {p}" for p in param_list])
    
    def _generate_canonical_body(self) -> str:
        """Generate canonical function body structure"""
        # Extract algorithmic pattern from required_logic
        if self.contract.required_logic:
            logic = self.contract.required_logic.lower()
            
            if "recursive" in logic:
                return """    # Canonical recursive structure
    if base_case_condition:
        return base_case_value
    return recursive_call_with_reduced_input"""
            
            elif "iterative" in logic or "loop" in logic:
                return """    # Canonical iterative structure
    result = initial_value
    for item in input_range:
        result = update_result(result, item)
    return result"""
            
            elif "sort" in logic:
                return """    # Canonical sorting structure
    if len(input_data) <= 1:
        return input_data
    return merge_or_combine_sorted_parts(input_data)"""
        
        # Default canonical structure
        return """    # Canonical implementation structure
    result = process_input(input_parameters)
    return format_output(result)"""
    
    def _generate_test_validation(self) -> str:
        """Generate canonical test validation structure"""
        test_calls = []
        for i, test_case in enumerate(self.contract.test_cases[:3]):  # Limit to first 3
            if 'input' in test_case and 'expected_output' in test_case:
                input_val = test_case['input']
                expected = test_case['expected_output']
                test_calls.append(f"assert {self.contract.function_name}({input_val}) == {expected}")
        
        if test_calls:
            return f"""
# Canonical test validation
if __name__ == "__main__":
    {chr(10).join(f"    {call}" for call in test_calls)}
    print("All tests passed")
"""
        return ""
    
    def _apply_standard_canonicalization(self, code: str) -> str:
        """Apply standard canonicalization transformations to template"""
        # Use existing canonicalization pipeline
        canonical_code = self._strip_comments_docstrings(code)
        canonical_code = self._format_with_tools(canonical_code)
        canonical_code = self._normalize_literals(canonical_code)
        canonical_code = self._normalize_control_flow(canonical_code)
        canonical_code = self._ensure_deterministic_ordering(canonical_code)
        
        return canonical_code

    def canonicalize_with_repair(self, code: str, contract: 'PromptContract') -> Tuple[str, bool]:
        """Canonicalize code with integrated repair for broken/non-compliant code"""
        
        # Step 1: Try basic canonicalization first
        try:
            canonical_code = self.canonicalize(code)
            # Test if canonicalized code is functional
            if self._is_code_functional(canonical_code, contract):
                return canonical_code, True
        except Exception:
            pass  # Fall through to repair
        
        # Step 2: Apply repair logic if canonicalization failed or code is broken
        repaired_code = self._repair_broken_code(code, contract)
        
        # Step 3: Canonicalize the repaired code
        try:
            canonical_code = self.canonicalize(repaired_code)
            return canonical_code, True
        except Exception as e:
            # If all else fails, return original with failure flag
            return code, False
    
    def _is_code_functional(self, code: str, contract: 'PromptContract') -> bool:
        """Test if code is functional by attempting to parse and validate"""
        try:
            import ast
            tree = ast.parse(code)
            
            # Check if function exists
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == contract.function_name:
                    return True
            return False
        except:
            return False
    
    def _repair_broken_code(self, code: str, contract: 'PromptContract') -> str:
        """Repair broken code using smart normalization logic"""
        from smart_normalizer import smart_normalize_code
        
        # Use existing smart normalizer for repair
        try:
            repaired = smart_normalize_code(code, contract)
            return repaired
        except Exception:
            # Fallback: basic repair attempts
            return self._basic_repair(code, contract)
    
    def _basic_repair(self, code: str, contract: 'PromptContract') -> str:
        """Basic repair for common issues"""
        lines = code.split('\n')
        repaired_lines = []
        
        # Add missing function definition if needed
        has_function = any(f"def {contract.function_name}" in line for line in lines)
        if not has_function:
            # Create basic function signature
            repaired_lines.append(f"def {contract.function_name}(data):")
            repaired_lines.append("    # Generated repair")
            repaired_lines.append("    pass")
        
        # Clean up and add existing lines
        for line in lines:
            if line.strip():
                repaired_lines.append(line)
        
        return '\n'.join(repaired_lines)

def canonicalize_code(code: str, contract: PromptContract) -> CanonicalizationResult:
    """Main canonicalization function using the complete Canonicalizer class"""
    print(f"      Canonicalizer: Processing {len(code)} chars of code...")
    
    try:
        # Use the complete Canonicalizer class instead of undefined functions
        canonicalizer = Canonicalizer(contract)
        result = canonicalizer.canonicalize(code)
        
        print(f"        Canonicalization complete: {len(result.transformations)} transformations applied")
        return result
        
    except Exception as e:
        print(f"        Canonicalization error: {e}, applying fallback...")
        # Return minimal result on failure
        return CanonicalizationResult(
            canonical_code=code,
            hashes=CanonicalHashes(
                canonical_hash=hashlib.sha256(code.encode('utf-8')).hexdigest()[:16],
                behavior_hash=hashlib.sha256(code.encode('utf-8')).hexdigest()[:16],
                raw_code_hash=hashlib.sha256(code.encode('utf-8')).hexdigest()[:16]
            ),
            transformations=["canonicalization_failed"],
            tool_versions={}
        )
