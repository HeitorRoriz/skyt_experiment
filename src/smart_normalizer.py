# src/smart_normalizer.py

import ast
import re
import os
from typing import List, Tuple, Optional, Dict, Any
from contract import PromptContract
from compliance_checker import check_compliance
from determinism_lint import lint_for_determinism, DeterminismViolation
from canonicalizer import canonicalize_code, CanonicalizationResult
from config import RESULTS_DIR

class CanonicalRepairSystem:
    """Canonicalization-based repair system that replaces template replay"""
    
    def __init__(self):
        pass
    
    def repair_code(self, raw_code: str, contract: PromptContract) -> Tuple[str, List[str], str]:
        """
        Apply canonicalization-based repair instead of template replay
        Returns (repaired_code, repair_steps, status)
        Status: 'raw', 'normalized', 'repaired', 'failed'
        """
        repair_steps = []
        
        # Step 1: Check determinism first
        is_deterministic, violations = lint_for_determinism(raw_code, contract)
        if not is_deterministic:
            # Attempt targeted repairs for determinism violations
            repaired_code, determinism_repairs = self._repair_determinism_violations(
                raw_code, violations, contract
            )
            repair_steps.extend(determinism_repairs)
        else:
            repaired_code = raw_code
        
        # Step 2: Check contract compliance
        compliance = check_compliance(repaired_code, contract)
        if not all(compliance.values()):
            # Apply targeted compliance repairs
            repaired_code, compliance_repairs = self._repair_compliance_violations(
                repaired_code, compliance, contract
            )
            repair_steps.extend(compliance_repairs)
        
        # Step 3: Canonicalize the repaired code
        try:
            canonicalization_result = canonicalize_code(repaired_code, contract)
            canonical_code = canonicalization_result.canonical_code
            repair_steps.extend([f"canonicalization_{t}" for t in canonicalization_result.transformations])
            
            # Final compliance check on canonical code
            final_compliance = check_compliance(canonical_code, contract)
            if all(final_compliance.values()):
                if repair_steps:
                    return canonical_code, repair_steps, 'repaired'
                else:
                    return canonical_code, repair_steps, 'raw'
            else:
                return canonical_code, repair_steps, 'failed'
                
        except Exception as e:
            repair_steps.append(f"canonicalization_failed_{type(e).__name__}")
            return repaired_code, repair_steps, 'failed'
    
    def _repair_determinism_violations(self, code: str, violations: List[DeterminismViolation], 
                                     contract: PromptContract) -> Tuple[str, List[str]]:
        """Apply targeted repairs for determinism violations"""
        repairs = []
        repaired_code = code
        
        try:
            tree = ast.parse(code)
            modified = False
            
            for violation in violations:
                if violation.rule == "forbidden_import":
                    # Remove forbidden imports
                    repaired_code = self._remove_forbidden_imports(repaired_code, violation)
                    repairs.append(f"removed_forbidden_import_{violation.message.split("'")[1]}")
                    modified = True
                
                elif violation.rule == "forbidden_call":
                    # Remove or replace forbidden calls
                    repaired_code = self._remove_forbidden_calls(repaired_code, violation)
                    repairs.append(f"removed_forbidden_call_{violation.message.split("'")[1]}")
                    modified = True
                
                elif violation.rule == "nondeterministic_return":
                    # Convert set returns to sorted lists
                    repaired_code = self._fix_nondeterministic_returns(repaired_code)
                    repairs.append("converted_set_to_sorted_list")
                    modified = True
            
            return repaired_code, repairs
            
        except SyntaxError:
            # If AST parsing fails, return original with error note
            repairs.append("determinism_repair_failed_syntax_error")
            return code, repairs
    
    def _repair_compliance_violations(self, code: str, compliance: Dict[str, bool], 
                                    contract: PromptContract) -> Tuple[str, List[str]]:
        """Apply targeted repairs for compliance violations"""
        repairs = []
        repaired_code = code
        
        try:
            tree = ast.parse(code)
            
            # Fix function name if incorrect
            if not compliance.get('function_name', True):
                repaired_code = self._fix_function_name(repaired_code, contract.function_name)
                repairs.append(f"fixed_function_name_to_{contract.function_name}")
            
            # Remove comments if required
            if not compliance.get('no_comments', True) and "no comments" in contract.constraints:
                repaired_code = self._remove_comments(repaired_code)
                repairs.append("removed_comments")
            
            # Fix output type issues
            if not compliance.get('output_type', True):
                repaired_code = self._fix_output_type(repaired_code, contract.output_type)
                repairs.append(f"fixed_output_type_to_{contract.output_type}")
            
            return repaired_code, repairs
            
        except SyntaxError:
            repairs.append("compliance_repair_failed_syntax_error")
            return code, repairs
    
    def _remove_forbidden_imports(self, code: str, violation: DeterminismViolation) -> str:
        """Remove forbidden import statements"""
        lines = code.split('\n')
        filtered_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            # Skip import lines that contain forbidden modules
            if (line_stripped.startswith('import ') or line_stripped.startswith('from ')) and \
               any(forbidden in line_stripped for forbidden in ['random', 'time', 'os', 'pathlib']):
                continue
            filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def _remove_forbidden_calls(self, code: str, violation: DeterminismViolation) -> str:
        """Remove or comment out forbidden function calls"""
        try:
            tree = ast.parse(code)
            
            # Find and remove forbidden calls
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = self._get_function_name(node.func)
                    if func_name in ['print', 'input', 'eval', 'exec']:
                        # Replace with pass or remove the statement
                        if isinstance(node.parent, ast.Expr):
                            # If it's a standalone expression, replace with pass
                            node.parent.value = ast.Constant(value=None)
            
            return ast.unparse(tree)
        except:
            # Fallback: regex-based removal
            forbidden_calls = ['print', 'input', 'eval', 'exec', 'random', 'time']
            for call in forbidden_calls:
                code = re.sub(rf'\b{call}\s*\([^)]*\)', '# removed forbidden call', code)
            return code
    
    def _fix_nondeterministic_returns(self, code: str) -> str:
        """Convert set literals in returns to sorted lists"""
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Return) and node.value:
                    if isinstance(node.value, ast.Set):
                        # Convert set to sorted list
                        list_node = ast.List(elts=sorted(node.value.elts, key=lambda x: ast.dump(x)), ctx=ast.Load())
                        sorted_call = ast.Call(
                            func=ast.Name(id='sorted', ctx=ast.Load()),
                            args=[list_node],
                            keywords=[]
                        )
                        node.value = sorted_call
            
            return ast.unparse(tree)
        except:
            return code
    
    def _fix_function_name(self, code: str, required_name: str) -> str:
        """Fix function name to match contract requirement"""
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    node.name = required_name
                    break
            
            return ast.unparse(tree)
        except:
            # Fallback: regex replacement
            return re.sub(r'def\s+\w+\s*\(', f'def {required_name}(', code)
    
    def _remove_comments(self, code: str) -> str:
        """Remove comments from code"""
        lines = []
        for line in code.split('\n'):
            if '#' in line and not self._is_in_string(line, line.find('#')):
                line = line[:line.find('#')].rstrip()
            if line.strip():
                lines.append(line)
        return '\n'.join(lines)
    
    def _fix_output_type(self, code: str, required_type: str) -> str:
        """Attempt to fix output type mismatches"""
        # This is a placeholder - would need more sophisticated type analysis
        return code
    
    def _get_function_name(self, node: ast.AST) -> str:
        """Extract function name from call node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        else:
            return ""
    
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

def smart_normalize_code(code_str: str, contract: PromptContract, run_number: int = 0) -> Tuple[str, List[str], str]:
    """
    New canonicalization-based normalization (replaces template replay)
    Returns (normalized_code, corrections, status)
    Status can be: 'raw', 'normalized', 'repaired', 'failed'
    """
    
    # Use the new canonical repair system instead of template replay
    repair_system = CanonicalRepairSystem()
    return repair_system.repair_code(code_str, contract)

# Backward compatibility function
def normalize_code(code_str: str, contract: PromptContract) -> Tuple[str, List[str]]:
    """Legacy function for backward compatibility"""
    normalized_code, corrections, status = smart_normalize_code(code_str, contract)
    return normalized_code, corrections
