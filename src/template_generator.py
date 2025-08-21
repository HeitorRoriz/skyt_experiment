# src/template_generator.py

from typing import Dict, Any, List
from contract import PromptContract

class ContractTemplateGenerator:
    """Generate code templates and references from contract specifications"""
    
    def __init__(self, contract: PromptContract):
        self.contract = contract
    
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
        
        # Apply basic formatting
        return self._apply_basic_formatting(canonical_template)
    
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
    
    def _apply_basic_formatting(self, code: str) -> str:
        """Apply basic formatting to template"""
        # Remove excessive whitespace
        lines = code.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Remove trailing whitespace
            formatted_line = line.rstrip()
            formatted_lines.append(formatted_line)
        
        # Remove excessive blank lines
        result_lines = []
        prev_blank = False
        
        for line in formatted_lines:
            is_blank = len(line.strip()) == 0
            if not (is_blank and prev_blank):
                result_lines.append(line)
            prev_blank = is_blank
        
        return '\n'.join(result_lines)

def generate_contract_template(contract: PromptContract) -> str:
    """Factory function to generate canonical template from contract"""
    generator = ContractTemplateGenerator(contract)
    return generator.generate_canonical_template()
