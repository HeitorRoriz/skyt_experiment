"""
Test prompt templates for 5 algorithm families with 2 paraphrases each
Total: 10 prompts for comprehensive repeatability testing
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple
from contract import PromptContract

@dataclass
class AlgorithmPrompt:
    """Single algorithm prompt with metadata"""
    family: str
    variant: str  # "A" or "B" for paraphrases
    prompt_text: str
    expected_function_name: str
    expected_output_type: str
    required_logic: str
    constraints: List[str]

class TestPromptGenerator:
    """Generate standardized test prompts for algorithm families"""
    
    def __init__(self):
        self.prompts = self._create_all_prompts()
    
    def _create_all_prompts(self) -> List[AlgorithmPrompt]:
        """Create all 10 test prompts (5 families × 2 paraphrases)"""
        return [
            # Merge Sort Family
            AlgorithmPrompt(
                family="merge_sort",
                variant="A",
                prompt_text="Write a Python function called merge_sort that takes a list of integers and returns a sorted list using the merge sort algorithm. The function should be recursive and divide the list into halves.",
                expected_function_name="merge_sort",
                expected_output_type="list",
                required_logic="recursion",
                constraints=["no comments", "code only"]
            ),
            AlgorithmPrompt(
                family="merge_sort",
                variant="B", 
                prompt_text="Implement a recursive merge_sort function in Python. Given an array of numbers, split it recursively and merge the sorted halves to produce a completely sorted array.",
                expected_function_name="merge_sort",
                expected_output_type="list",
                required_logic="recursion",
                constraints=["no comments", "code only"]
            ),
            
            # Sieve of Eratosthenes Family
            AlgorithmPrompt(
                family="sieve_eratosthenes",
                variant="A",
                prompt_text="Create a Python function named sieve_of_eratosthenes that finds all prime numbers up to a given limit n. Use the classical sieve algorithm that marks multiples as composite.",
                expected_function_name="sieve_of_eratosthenes",
                expected_output_type="list",
                required_logic="iteration",
                constraints=["no comments", "code only"]
            ),
            AlgorithmPrompt(
                family="sieve_eratosthenes",
                variant="B",
                prompt_text="Write a sieve_of_eratosthenes function that returns all prime numbers less than or equal to n. Implement the sieve by iteratively marking composite numbers.",
                expected_function_name="sieve_of_eratosthenes", 
                expected_output_type="list",
                required_logic="iteration",
                constraints=["no comments", "code only"]
            ),
            
            # BFS Shortest Path Family
            AlgorithmPrompt(
                family="bfs_shortest_path",
                variant="A",
                prompt_text="Implement a Python function bfs_shortest_path that takes a graph (as adjacency list) and finds the shortest path between two nodes using breadth-first search. Return the path as a list.",
                expected_function_name="bfs_shortest_path",
                expected_output_type="list", 
                required_logic="iteration",
                constraints=["no comments", "code only"]
            ),
            AlgorithmPrompt(
                family="bfs_shortest_path",
                variant="B",
                prompt_text="Create a bfs_shortest_path function that uses BFS to find the shortest route between start and end nodes in a graph. The graph is given as an adjacency list dictionary.",
                expected_function_name="bfs_shortest_path",
                expected_output_type="list",
                required_logic="iteration", 
                constraints=["no comments", "code only"]
            ),
            
            # Balanced Brackets Family
            AlgorithmPrompt(
                family="balanced_brackets",
                variant="A",
                prompt_text="Write a Python function is_balanced that checks if a string of brackets (parentheses, square brackets, curly braces) is properly balanced. Return True if balanced, False otherwise.",
                expected_function_name="is_balanced",
                expected_output_type="bool",
                required_logic="iteration",
                constraints=["no comments", "code only"]
            ),
            AlgorithmPrompt(
                family="balanced_brackets", 
                variant="B",
                prompt_text="Implement an is_balanced function that determines whether brackets in a string are correctly matched and nested. Handle (), [], and {} bracket types.",
                expected_function_name="is_balanced",
                expected_output_type="bool",
                required_logic="iteration",
                constraints=["no comments", "code only"]
            ),
            
            # Dijkstra's Algorithm Family
            AlgorithmPrompt(
                family="dijkstra",
                variant="A", 
                prompt_text="Create a Python function dijkstra_shortest_path that implements Dijkstra's algorithm to find shortest paths from a source node to all other nodes in a weighted graph. Return distances as a dictionary.",
                expected_function_name="dijkstra_shortest_path",
                expected_output_type="dict",
                required_logic="iteration",
                constraints=["no comments", "code only"]
            ),
            AlgorithmPrompt(
                family="dijkstra",
                variant="B",
                prompt_text="Write a dijkstra_shortest_path function using Dijkstra's algorithm. Given a weighted graph and source vertex, compute the minimum distance to every other vertex.",
                expected_function_name="dijkstra_shortest_path", 
                expected_output_type="dict",
                required_logic="iteration",
                constraints=["no comments", "code only"]
            )
        ]
    
    def get_all_prompts(self) -> List[AlgorithmPrompt]:
        """Get all 10 test prompts"""
        return self.prompts
    
    def get_prompts_by_family(self, family: str) -> List[AlgorithmPrompt]:
        """Get both paraphrases for a specific algorithm family"""
        return [p for p in self.prompts if p.family == family]
    
    def get_families(self) -> List[str]:
        """Get list of all algorithm families"""
        return list(set(p.family for p in self.prompts))
    
    def create_contract_from_prompt(self, prompt: AlgorithmPrompt) -> PromptContract:
        """Convert algorithm prompt to PromptContract for testing"""
        return PromptContract(
            function_name=prompt.expected_function_name,
            language="python",
            output_type=prompt.expected_output_type,
            output_format="function",
            required_logic=prompt.required_logic,
            constraints=prompt.constraints
        )
    
    def get_test_matrix(self) -> List[Tuple[str, str, AlgorithmPrompt, PromptContract]]:
        """Get complete test matrix: (family, variant, prompt, contract)"""
        matrix = []
        for prompt in self.prompts:
            contract = self.create_contract_from_prompt(prompt)
            matrix.append((prompt.family, prompt.variant, prompt, contract))
        return matrix
    
    def build_enhanced_prompt(self, prompt: AlgorithmPrompt, contract: 'PromptContract') -> str:
        """Build enhanced prompt with dual intent capture"""
        
        # Base prompt
        base_text = prompt.prompt_text
        
        # Developer Intent Section
        developer_intent = self._extract_developer_intent(contract)
        
        # User Intent Section  
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
    
    def _extract_developer_intent(self, contract: 'PromptContract') -> str:
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
    
    def _extract_user_intent(self, contract: 'PromptContract') -> str:
        """Extract user behavioral intent from contract"""
        intent_parts = []
        
        # Expected behavior from test cases
        if contract.test_cases:
            intent_parts.append("- Expected behavior:")
            for i, test_case in enumerate(contract.test_cases[:3]):  # Show first 3
                if 'input' in test_case and 'expected_output' in test_case:
                    input_val = test_case['input']
                    expected = test_case['expected_output']
                    intent_parts.append(f"  * Input {input_val} → Output {expected}")
        
        # Performance expectations
        if contract.hardware_constraints:
            hw = contract.hardware_constraints
            if 'max_latency_us' in hw:
                intent_parts.append(f"- Maximum latency: {hw['max_latency_us']} microseconds")
            if 'memory_limit' in hw:
                intent_parts.append(f"- Memory limit: {hw['memory_limit']}")
        
        # Safety and reliability
        if contract.safety_critical:
            intent_parts.append("- Safety-critical: Handle all edge cases robustly")
        
        # Determinism requirements
        if contract.determinism:
            intent_parts.append(f"- Determinism: {contract.determinism}")
        
        return "\n".join(intent_parts) if intent_parts else "- Provide correct and reliable behavior"
    
    def _format_constraints(self, contract: 'PromptContract') -> str:
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

def create_test_prompts() -> TestPromptGenerator:
    """Factory function to create test prompt generator"""
    return TestPromptGenerator()
