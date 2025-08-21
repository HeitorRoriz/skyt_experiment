# src/prompt_enhancer.py

from typing import Dict, Any, List
from contract import PromptContract
from test_prompts import AlgorithmPrompt
from dual_intent_capture import DualIntentCapture

class PromptEnhancer:
    """Handle prompt enhancement with dual intent capture"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.dual_intent_capturer = DualIntentCapture(llm_client) if llm_client else None
    
    def build_enhanced_prompt(self, prompt: AlgorithmPrompt, contract: PromptContract) -> str:
        """Build enhanced prompt with dual intent capture (static + LLM-based WHY)"""
        
        # Base prompt
        base_text = prompt.prompt_text
        
        # Developer Intent Section
        developer_intent = self._extract_developer_intent(contract)
        
        # User Intent Section with LLM enhancement
        if self.dual_intent_capturer:
            # Use advanced dual intent capture with LLM WHY extraction
            intent_data = self.dual_intent_capturer.capture_user_intent_with_llm(prompt, contract)
            user_intent = self.dual_intent_capturer.format_enhanced_user_intent(intent_data)
        else:
            # Fallback to existing static logic
            user_intent = self._extract_user_intent(contract)
        
        # Contract Constraints
        constraints_text = self._format_constraints(contract)
        
        # Build enhanced prompt
        enhanced_prompt = f"""
{base_text}

## IMPLEMENTATION GUIDANCE (Developer Intent)
{developer_intent}

## BEHAVIORAL REQUIREMENTS (User Intent)  
{user_intent}

## CONTRACT CONSTRAINTS
{constraints_text}

## OUTPUT REQUIREMENTS
- Function name: {contract.function_name}
- Return type: {contract.output_type}
- Output format: {contract.output_format}
- Include comprehensive docstring
- Follow contract specifications exactly

Please implement the function following both the developer's implementation approach and the user's behavioral expectations.
"""
        
        return enhanced_prompt.strip()
    
    def _extract_developer_intent(self, contract: PromptContract) -> str:
        """Extract developer implementation intent from contract"""
        intent_parts = []
        
        # Algorithm approach from required_logic
        if contract.required_logic:
            logic = contract.required_logic
            intent_parts.append(f"- Algorithmic approach: {logic}")
            
            # Specific implementation hints
            if "recursive" in logic.lower():
                intent_parts.append("- Use recursive implementation with clear base case")
                intent_parts.append("- Ensure tail recursion optimization where possible")
            elif "iterative" in logic.lower() or "loop" in logic.lower():
                intent_parts.append("- Use iterative approach with explicit loop structure")
                intent_parts.append("- Minimize loop complexity and nesting")
            elif "sort" in logic.lower():
                intent_parts.append("- Implement efficient sorting algorithm")
                intent_parts.append("- Handle edge cases (empty, single element)")
        
        # Library preferences
        if contract.allowed_libraries:
            intent_parts.append(f"- Preferred libraries: {', '.join(contract.allowed_libraries)}")
        if contract.disallowed_libraries:
            intent_parts.append(f"- Avoid libraries: {', '.join(contract.disallowed_libraries)}")
        
        # Code style preferences
        if contract.docstring_required:
            intent_parts.append("- Include comprehensive docstrings")
        
        return "\n".join(intent_parts) if intent_parts else "- Follow standard implementation practices"
    
    def _extract_user_intent(self, contract: PromptContract) -> str:
        """Extract user behavioral intent from contract including WHY reasoning"""
        intent_parts = []
        
        # Expected behavior from test cases
        if contract.test_cases:
            intent_parts.append("- Expected behavior:")
            for i, test_case in enumerate(contract.test_cases[:3]):  # Show first 3
                if 'input' in test_case and 'expected_output' in test_case:
                    input_val = test_case['input']
                    expected = test_case['expected_output']
                    intent_parts.append(f"  * Input {input_val} → Output {expected}")
        
        # WHY: User motivation and reasoning
        intent_parts.append("- User motivation (WHY this behavior is needed):")
        why_reasoning = self._extract_user_motivation(contract)
        intent_parts.extend([f"  * {reason}" for reason in why_reasoning])
        
        # Performance expectations
        if contract.hardware_constraints:
            hw = contract.hardware_constraints
            if 'max_latency_us' in hw:
                intent_parts.append(f"- Maximum latency: {hw['max_latency_us']} microseconds")
                intent_parts.append("  * WHY: User needs real-time response for interactive applications")
            if 'memory_limit' in hw:
                intent_parts.append(f"- Memory limit: {hw['memory_limit']}")
                intent_parts.append("  * WHY: User operates in resource-constrained environment")
        
        # Safety and reliability
        if contract.safety_critical:
            intent_parts.append("- Safety-critical: Handle all edge cases robustly")
            intent_parts.append("  * WHY: User needs guaranteed correctness to prevent system failures")
        
        # Determinism requirements
        if contract.determinism:
            intent_parts.append(f"- Determinism: {contract.determinism}")
            intent_parts.append("  * WHY: User needs predictable outputs for testing, debugging, or compliance")
        
        return "\n".join(intent_parts) if intent_parts else "- Provide correct and reliable behavior"
    
    def _extract_user_motivation(self, contract: PromptContract) -> List[str]:
        """Extract WHY reasoning based on algorithm family and contract context"""
        motivations = []
        
        # Algorithm-specific motivations
        if contract.function_name:
            func_name = contract.function_name.lower()
            
            if "sort" in func_name:
                motivations.extend([
                    "User needs data organized in ascending order for efficient searching and analysis",
                    "Sorted data enables binary search, range queries, and ordered processing",
                    "User expects stable, predictable ordering for consistent application behavior"
                ])
            
            elif "search" in func_name:
                motivations.extend([
                    "User needs fast data retrieval from large datasets",
                    "Efficient search reduces response time and improves user experience",
                    "User expects reliable 'not found' indication when data doesn't exist"
                ])
            
            elif "fibonacci" in func_name:
                motivations.extend([
                    "User needs mathematical sequence computation for modeling or analysis",
                    "Efficient calculation prevents timeout in recursive scenarios",
                    "User expects mathematically correct results for validation purposes"
                ])
            
            elif "sieve" in func_name or "prime" in func_name:
                motivations.extend([
                    "User needs prime numbers for cryptographic operations or mathematical analysis",
                    "Complete prime enumeration ensures no security vulnerabilities from missed primes",
                    "User expects mathematically proven correctness for critical applications"
                ])
            
            elif "dijkstra" in func_name or "shortest" in func_name:
                motivations.extend([
                    "User needs optimal path finding for navigation, routing, or network optimization",
                    "Shortest path minimizes cost, time, or distance in real-world applications",
                    "User expects globally optimal solution, not just locally optimal approximation"
                ])
        
        # Contract-specific motivations
        if contract.required_logic:
            logic = contract.required_logic.lower()
            if "recursive" in logic:
                motivations.append("User prefers recursive approach for mathematical elegance and proof correctness")
            elif "iterative" in logic:
                motivations.append("User needs iterative approach for memory efficiency and stack safety")
        
        # Output type motivations
        if contract.output_type:
            output_type = contract.output_type.lower()
            if "list" in output_type:
                motivations.append("User needs collection output for further processing, filtering, or iteration")
            elif "dict" in output_type:
                motivations.append("User needs key-value mapping for efficient lookups and data relationships")
            elif "int" in output_type:
                motivations.append("User needs single numeric result for calculations or decision making")
        
        # Default motivation if none found
        if not motivations:
            motivations.append("User needs reliable, correct implementation that meets specified requirements")
        
        return motivations
    
    def _format_constraints(self, contract: PromptContract) -> str:
        """Format contract constraints for prompt"""
        constraints = []
        
        # Add contract constraints
        if contract.constraints:
            constraints.extend([f"- {c}" for c in contract.constraints])
        
        # Add method signature if specified
        if contract.method_signature:
            constraints.append(f"- Method signature: {contract.method_signature}")
        
        # Add variable requirements
        if contract.variables:
            var_list = [f"{v['name']} ({v['type']})" for v in contract.variables]
            constraints.append(f"- Required variables: {', '.join(var_list)}")
        
        return "\n".join(constraints) if constraints else "- Follow standard coding practices"

def enhance_prompt(prompt: AlgorithmPrompt, contract: PromptContract, llm_client=None) -> str:
    """Factory function to enhance prompt with dual intent capture"""
    enhancer = PromptEnhancer(llm_client)
    return enhancer.build_enhanced_prompt(prompt, contract)
