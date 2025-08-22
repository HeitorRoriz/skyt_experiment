# src/dual_intent_capture.py

from typing import Dict, Any, List
from contract import PromptContract
from test_prompts import AlgorithmPrompt
from llm import call_llm_simple

class DualIntentCapture:
    """Advanced dual intent capture with LLM-based WHY extraction"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    def capture_user_intent_with_llm(self, prompt: AlgorithmPrompt, contract: PromptContract) -> Dict[str, Any]:
        """Capture user intent using LLM to extract WHY reasoning"""
        
        # Static analysis (existing logic)
        static_intent = self._extract_static_user_intent(contract)
        
        # LLM-based WHY extraction (new logic)
        if self.llm_client:
            llm_intent = self._extract_llm_why_reasoning(prompt, contract)
        else:
            llm_intent = {"why_reasoning": ["LLM client not available for WHY extraction"]}
        
        # Combine both approaches
        combined_intent = {
            "static_analysis": static_intent,
            "llm_extracted": llm_intent,
            "combined_why": static_intent.get("why_reasoning", []) + llm_intent.get("why_reasoning", [])
        }
        
        return combined_intent
    
    def _extract_static_user_intent(self, contract: PromptContract) -> Dict[str, Any]:
        """Extract user intent using static analysis (existing logic from prompt_enhancer)"""
        intent_parts = []
        why_reasoning = []
        
        # Expected behavior from test cases
        if contract.test_cases:
            intent_parts.append("- Expected behavior:")
            for i, test_case in enumerate(contract.test_cases[:3]):
                if 'input' in test_case and 'expected_output' in test_case:
                    input_val = test_case['input']
                    expected = test_case['expected_output']
                    intent_parts.append(f"  * Input {input_val} → Output {expected}")
        
        # Static WHY reasoning based on algorithm patterns
        why_reasoning.extend(self._extract_static_motivation(contract))
        
        # Performance expectations
        if contract.hardware_constraints:
            hw = contract.hardware_constraints
            if 'max_latency_us' in hw:
                intent_parts.append(f"- Maximum latency: {hw['max_latency_us']} microseconds")
                why_reasoning.append("User needs real-time response for interactive applications")
            if 'memory_limit' in hw:
                intent_parts.append(f"- Memory limit: {hw['memory_limit']}")
                why_reasoning.append("User operates in resource-constrained environment")
        
        # Safety and reliability
        if contract.safety_critical:
            intent_parts.append("- Safety-critical: Handle all edge cases robustly")
            why_reasoning.append("User needs guaranteed correctness to prevent system failures")
        
        # Determinism requirements
        if contract.determinism:
            intent_parts.append(f"- Determinism: {contract.determinism}")
            why_reasoning.append("User needs predictable outputs for testing, debugging, or compliance")
        
        return {
            "behavioral_requirements": intent_parts,
            "why_reasoning": why_reasoning
        }
    
    def _extract_static_motivation(self, contract: PromptContract) -> List[str]:
        """Extract WHY reasoning using static algorithm analysis"""
        motivations = []
        
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
        
        if not motivations:
            motivations.append("User needs reliable, correct implementation that meets specified requirements")
        
        return motivations
    
    def _extract_llm_why_reasoning(self, prompt: AlgorithmPrompt, contract: PromptContract) -> Dict[str, Any]:
        """Use LLM to extract deeper WHY reasoning from prompt and contract context"""
        
        analysis_prompt = f"""
Analyze this algorithm request and extract the user's underlying motivations and reasoning:

ALGORITHM REQUEST:
{prompt.prompt_text}

FUNCTION: {contract.function_name}
OUTPUT TYPE: {contract.output_type}
REQUIRED LOGIC: {contract.required_logic}

Please analyze WHY the user would want this specific algorithm implementation. Consider:
1. What business problem or use case drives this need?
2. Why this specific approach (recursive vs iterative, etc.)?
3. What are the user's likely constraints or priorities?
4. What downstream usage patterns might they have?

Provide 3-5 concise bullet points explaining the user's likely motivations:
"""

        try:
            # Use direct llm.py call for analysis
            llm_response = call_llm_simple(analysis_prompt)
            
            # Parse LLM response into structured format
            why_reasoning = self._parse_llm_why_response(llm_response)
            
            return {
                "why_reasoning": why_reasoning,
                "llm_raw_response": llm_response
            }
            
        except Exception as e:
            return {
                "why_reasoning": [f"LLM WHY extraction failed: {str(e)}"],
                "llm_raw_response": None
            }
    
    def _parse_llm_why_response(self, llm_response: str) -> List[str]:
        """Parse LLM response to extract WHY reasoning bullets"""
        lines = llm_response.strip().split('\n')
        why_points = []
        
        for line in lines:
            line = line.strip()
            # Look for bullet points or numbered items
            if line.startswith(('•', '-', '*', '1.', '2.', '3.', '4.', '5.')):
                # Clean up the bullet point
                cleaned = line.lstrip('•-*123456789. ').strip()
                if cleaned and len(cleaned) > 10:  # Filter out very short responses
                    why_points.append(cleaned)
        
        # Fallback: if no bullets found, try to extract sentences
        if not why_points:
            sentences = llm_response.split('.')
            for sentence in sentences[:3]:  # Take first 3 sentences
                sentence = sentence.strip()
                if len(sentence) > 20:
                    why_points.append(sentence)
        
        return why_points[:5]  # Limit to 5 points
    
    def format_enhanced_user_intent(self, intent_data: Dict[str, Any]) -> str:
        """Format the combined intent data for use in prompts"""
        lines = []
        
        # Static behavioral requirements
        if intent_data.get("static_analysis", {}).get("behavioral_requirements"):
            lines.extend(intent_data["static_analysis"]["behavioral_requirements"])
        
        # Combined WHY reasoning
        if intent_data.get("combined_why"):
            lines.append("- User motivation (WHY this behavior is needed):")
            for why in intent_data["combined_why"]:
                lines.append(f"  * {why}")
        
        return "\n".join(lines) if lines else "- Provide correct and reliable behavior"

def capture_dual_intent_with_llm(prompt: AlgorithmPrompt, contract: PromptContract, llm_client=None) -> Dict[str, Any]:
    """Factory function for dual intent capture with LLM enhancement"""
    capturer = DualIntentCapture(llm_client)
    return capturer.capture_user_intent_with_llm(prompt, contract)
