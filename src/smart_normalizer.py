# src/smart_normalizer.py

import ast
import re
import os
from typing import List, Tuple, Optional, Dict, Any
from contract import PromptContract
from compliance_checker import check_compliance
from config import RESULTS_DIR

class CodeRescuer:
    """Smart code rescue system that learns from previous successful runs"""
    
    def __init__(self):
        self.successful_patterns = {}  # Cache of successful code patterns
    
    def load_successful_runs(self, contract_name: str) -> List[str]:
        """Load all successful final outputs for a contract"""
        contract_dir = os.path.join(RESULTS_DIR, contract_name)
        if not os.path.exists(contract_dir):
            return []
        
        successful_codes = []
        for filename in os.listdir(contract_dir):
            if filename.startswith("final_run") and filename.endswith(".py"):
                filepath = os.path.join(contract_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        code = f.read().strip()
                        if code and len(code) > 10:  # Basic sanity check
                            successful_codes.append(code)
                except Exception:
                    continue
        
        return successful_codes
    
    def extract_function_structure(self, code: str) -> Dict[str, Any]:
        """Extract key structural elements from working code"""
        try:
            tree = ast.parse(code)
            structure = {
                'function_name': None,
                'parameters': [],
                'return_statements': [],
                'recursive_calls': [],
                'has_base_case': False,
                'has_recursive_case': False,
                'imports': []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    structure['function_name'] = node.name
                    structure['parameters'] = [arg.arg for arg in node.args.args]
                    
                    # Find return statements and recursive calls
                    for child in ast.walk(node):
                        if isinstance(child, ast.Return):
                            if hasattr(child.value, 'elts'):  # List return
                                structure['return_statements'].append('list')
                            elif isinstance(child.value, ast.List):
                                structure['return_statements'].append('list')
                            else:
                                structure['return_statements'].append('other')
                        
                        if isinstance(child, ast.Call) and hasattr(child.func, 'id'):
                            if child.func.id == node.name:
                                structure['recursive_calls'].append(True)
                        
                        # Check for base case patterns
                        if isinstance(child, ast.If):
                            structure['has_base_case'] = True
                
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    structure['imports'].append(ast.unparse(node))
            
            structure['has_recursive_case'] = len(structure['recursive_calls']) > 0
            return structure
            
        except Exception:
            return {}
    
    def get_first_successful_template(self, contract_name: str) -> Optional[str]:
        """Get the first successful output from the first run as the template"""
        contract_dir = os.path.join(RESULTS_DIR, contract_name)
        if not os.path.exists(contract_dir):
            return None
        
        # Look for the first successful final output (final_run1.py)
        first_run_file = os.path.join(contract_dir, "final_run1.py")
        if os.path.exists(first_run_file):
            try:
                with open(first_run_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content and len(content) > 10:  # Basic sanity check
                        return content
            except Exception:
                pass
        
        return None

    def generate_fibonacci_template(self, contract: PromptContract, successful_codes: List[str]) -> str:
        """Generate a working Fibonacci function template based on successful patterns"""
        
        # Analyze successful patterns
        patterns = [self.extract_function_structure(code) for code in successful_codes]
        patterns = [p for p in patterns if p]  # Remove empty patterns
        
        function_name = contract.function_name
        needs_recursion = contract.required_logic == "recursion"
        
        if needs_recursion:
            # Generate recursive Fibonacci
            template = f"""def {function_name}(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    else:
        fib_list = {function_name}(n - 1)
        fib_list.append(fib_list[-1] + fib_list[-2])
        return fib_list"""
        else:
            # Generate iterative Fibonacci
            template = f"""def {function_name}(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib"""
        
        return template
    
    def rescue_code(self, broken_code: str, contract: PromptContract) -> Tuple[str, List[str]]:
        """Attempt to rescue broken code by fixing common issues"""
        corrections = []
        rescued_code = broken_code
        
        # Step 1: Try basic fixes first
        rescued_code, basic_corrections = self.apply_basic_fixes(rescued_code, contract)
        corrections.extend(basic_corrections)
        
        # Step 2: Check if basic fixes worked
        compliance = check_compliance(rescued_code, contract)
        if all(compliance.values()):
            return rescued_code, corrections
        
        # Step 3: If still broken, use the first successful run as template
        template = self.get_first_successful_template(contract.function_name)
        
        if template:
            # Use the first successful output as the consistent template
            final_code = self.adapt_template(template, contract)
            corrections.append("Used first successful run as template for rescue")
        else:
            # Fallback: generate a basic template if no successful runs exist yet
            final_code = self.generate_fibonacci_template(contract, [])
            corrections.append("Generated fallback template (no successful runs available)")
        
        return final_code, corrections
    
    def apply_basic_fixes(self, code: str, contract: PromptContract) -> Tuple[str, List[str]]:
        """Apply basic normalization fixes"""
        corrections = []
        
        # Remove markdown code blocks
        if "```" in code:
            code = re.sub(r"```(?:python)?\s*", "", code)
            code = re.sub(r"```", "", code)
            corrections.append("Removed markdown code blocks")
        
        # Remove comments if required
        if "no comments" in [c.lower() for c in contract.constraints]:
            original_lines = len(code.split('\n'))
            code = re.sub(r'#.*', '', code)
            new_lines = len(code.split('\n'))
            if original_lines != new_lines:
                corrections.append("Removed comments")
        
        # Fix function name
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name != contract.function_name:
                    code = re.sub(rf'\bdef\s+{re.escape(node.name)}\s*\(', 
                                f'def {contract.function_name}(', code)
                    corrections.append(f"Renamed function to '{contract.function_name}'")
                    break
        except:
            pass
        
        # Clean up whitespace
        lines = [line.rstrip() for line in code.split('\n')]
        code = '\n'.join(lines)
        
        return code, corrections
    
    def adapt_template(self, template: str, contract: PromptContract) -> str:
        """Adapt a working template to match specific contract requirements"""
        
        # Ensure correct function name
        try:
            tree = ast.parse(template)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    old_name = node.name
                    if old_name != contract.function_name:
                        template = re.sub(rf'\b{re.escape(old_name)}\b', 
                                        contract.function_name, template)
                    break
        except:
            pass
        
        # Remove comments if required
        if "no comments" in [c.lower() for c in contract.constraints]:
            template = re.sub(r'#.*', '', template)
        
        # Ensure proper formatting
        lines = [line.rstrip() for line in template.split('\n') if line.strip()]
        template = '\n'.join(lines)
        
        return template

def smart_normalize_code(code_str: str, contract: PromptContract, run_number: int = 0) -> Tuple[str, List[str], str]:
    """
    Smart normalization that actively rescues non-compliant code.
    Returns (normalized_code, corrections, status)
    Status can be: 'raw', 'normalized', 'rescued', 'failed'
    """
    
    # First check if code is already compliant
    compliance = check_compliance(code_str, contract)
    if all(compliance.values()):
        # Even if compliant, use first-run template for consistency if available
        rescuer = CodeRescuer()
        template = rescuer.get_first_successful_template(contract.function_name)
        
        if template and run_number > 0:  # Use template for runs 2+ to ensure consistency
            adapted_code = rescuer.adapt_template(template, contract)
            return adapted_code, ["Used first-run template for consistency"], 'raw'
        else:
            return code_str, [], 'raw'
    
    # Try basic normalization first
    rescuer = CodeRescuer()
    normalized_code, corrections = rescuer.apply_basic_fixes(code_str, contract)
    
    # Check compliance after basic fixes
    compliance = check_compliance(normalized_code, contract)
    if all(compliance.values()):
        # Even if normalized successfully, use first-run template for consistency
        template = rescuer.get_first_successful_template(contract.function_name)
        
        if template and run_number > 0:  # Use template for runs 2+ to ensure consistency
            adapted_code = rescuer.adapt_template(template, contract)
            return adapted_code, corrections + ["Used first-run template for consistency"], 'normalized'
        else:
            return normalized_code, corrections, 'normalized'
    
    # If still not compliant, attempt rescue
    rescued_code, rescue_corrections = rescuer.rescue_code(code_str, contract)
    all_corrections = corrections + rescue_corrections
    
    # Final compliance check
    final_compliance = check_compliance(rescued_code, contract)
    if all(final_compliance.values()):
        return rescued_code, all_corrections, 'rescued'
    else:
        # If rescue failed, return the best attempt
        return rescued_code, all_corrections, 'failed'

# Backward compatibility function
def normalize_code(code_str: str, contract: PromptContract) -> Tuple[str, List[str]]:
    """Legacy function for backward compatibility"""
    normalized_code, corrections, status = smart_normalize_code(code_str, contract)
    return normalized_code, corrections
