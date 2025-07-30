# src/contract_generator.py

import os
import re
from contract import PromptContract
from config import EXPERIMENT_TEMPLATES, CONTRACTS_DIR

def extract_function_name_from_prompt(prompt):
    """Extract function name from prompt text, with fallback to 'fibonacci'"""
    # Look for explicit function name mentions
    name_patterns = [
        r'function named (\w+)',
        r'function called (\w+)',
        r'named (\w+)',
        r'called (\w+)'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, prompt.lower())
        if match:
            return match.group(1)
    
    # Default fallback for Fibonacci-related prompts
    return "fibonacci"

def extract_constraints_from_prompt(prompt):
    """Extract constraints and requirements from prompt text"""
    constraints = []
    prompt_lower = prompt.lower()
    
    # Check for recursion requirement
    if 'recursion' in prompt_lower or 'recursive' in prompt_lower:
        constraints.append("use recursion")
    
    # Check for specific output format requirements
    if 'list' in prompt_lower:
        constraints.append("return as list")
    
    # Check for number requirements
    if '20' in prompt:
        constraints.append("first 20 numbers")
    
    # Default constraint for clean output
    constraints.append("no comments")
    
    return constraints

def extract_required_logic_from_prompt(prompt):
    """Extract required logic approach from prompt"""
    prompt_lower = prompt.lower()
    
    if 'recursion' in prompt_lower or 'recursive' in prompt_lower:
        return "recursion"
    
    return None

def generate_contracts_from_prompts():
    """Generate contract files from EXPERIMENT_TEMPLATES in config.py"""
    
    # Ensure contracts directory exists
    if not os.path.exists(CONTRACTS_DIR):
        os.makedirs(CONTRACTS_DIR)
        print(f"Created contracts directory: {CONTRACTS_DIR}")
    
    generated_contracts = []
    
    for i, template in enumerate(EXPERIMENT_TEMPLATES):
        prompt = template["prompt"]
        
        # Extract contract components from prompt
        function_name = extract_function_name_from_prompt(prompt)
        constraints = extract_constraints_from_prompt(prompt)
        required_logic = extract_required_logic_from_prompt(prompt)
        
        # Create unique function name for each variant
        if i > 0:
            function_name = f"{function_name}_{i+1}"
        
        # Create contract
        contract = PromptContract(
            function_name=function_name,
            language="python",
            output_type="list",
            constraints=constraints,
            output_format="code only",
            required_logic=required_logic,
            extra_fields={"description": f"Generate Fibonacci numbers - Variant {i+1}"}
        )
        
        # Save contract to file
        contract_filename = f"{function_name}_contract.json"
        contract_path = os.path.join(CONTRACTS_DIR, contract_filename)
        
        contract.to_json(contract_path)
        generated_contracts.append(contract_path)
        
        print(f"Generated contract: {contract_filename}")
        print(f"  Function: {function_name}")
        print(f"  Constraints: {constraints}")
        print(f"  Required Logic: {required_logic}")
        print()
    
    return generated_contracts

if __name__ == "__main__":
    print("Generating contracts from experiment templates...")
    contracts = generate_contracts_from_prompts()
    print(f"Successfully generated {len(contracts)} contracts in '{CONTRACTS_DIR}' directory")
