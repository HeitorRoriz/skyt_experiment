"""
Test prompt templates for 5 algorithm families with 2 paraphrases each
Total: 10 prompts for comprehensive repeatability testing
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Any
import os
import json
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
        """Convert algorithm prompt to PromptContract with comprehensive acceptance tests"""
        
        # Generate algorithm-specific acceptance tests
        acceptance_tests = self._generate_acceptance_tests(prompt)
        
        # Set embedded/firmware quality gates by default
        test_config = {
            "timeout_seconds": 5.0,
            "required_pass_rate": 1.0,
            "correctness_threshold": 1.0,
            "allow_approximate": False,
            "tolerance": 1e-9
        }
        
        contract = PromptContract(
            function_name=prompt.expected_function_name,
            language="python",
            output_type=prompt.expected_output_type,
            output_format="function",
            required_logic=prompt.required_logic,
            constraints=prompt.constraints,
            acceptance_tests=acceptance_tests,
            test_config=test_config
        )
        
        # Save contract to JSON file
        contract_dict = contract.__dict__
        with open(f"{prompt.family}_{prompt.variant}.json", 'w') as f:
            json.dump(contract_dict, f, indent=4)
        
        return contract
    
    def _generate_acceptance_tests(self, prompt: AlgorithmPrompt) -> Dict[str, Any]:
        """Generate comprehensive acceptance tests based on algorithm family"""
        
        if prompt.family == "fibonacci":
            return self._fibonacci_acceptance_tests()
        elif prompt.family == "merge_sort":
            return self._merge_sort_acceptance_tests()
        elif prompt.family == "binary_search":
            return self._binary_search_acceptance_tests()
        elif prompt.family == "sieve_eratosthenes":
            return self._sieve_acceptance_tests()
        elif prompt.family == "dijkstra":
            return self._dijkstra_acceptance_tests()
        else:
            return self._default_acceptance_tests(prompt)
    
    def _fibonacci_acceptance_tests(self) -> Dict[str, Any]:
        """Comprehensive Fibonacci acceptance tests"""
        return {
            "unit_tests": [
                {"name": "fibonacci_base_case_0", "input": 0, "expected_output": [], "description": "Empty sequence for n=0"},
                {"name": "fibonacci_base_case_1", "input": 1, "expected_output": [0], "description": "Single element for n=1"},
                {"name": "fibonacci_small", "input": 5, "expected_output": [0, 1, 1, 2, 3], "description": "First 5 Fibonacci numbers"},
                {"name": "fibonacci_medium", "input": 10, "expected_output": [0, 1, 1, 2, 3, 5, 8, 13, 21, 34], "description": "First 10 Fibonacci numbers"}
            ],
            "edge_cases": [
                {"name": "fibonacci_negative", "input": -1, "expected_output": [], "description": "Negative input handling"},
                {"name": "fibonacci_zero", "input": 0, "expected_output": [], "description": "Zero input handling"},
                {"name": "fibonacci_large", "input": 20, "expected_output": [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181], "description": "Large sequence"}
            ],
            "property_tests": [
                {"name": "fibonacci_property", "property": "for n >= 2: result[n] == result[n-1] + result[n-2]", "description": "Each element is sum of previous two"},
                {"name": "fibonacci_length", "property": "len(result) == input_n", "description": "Output length matches input"},
                {"name": "fibonacci_starts_correctly", "property": "result[0] == 0 and result[1] == 1", "description": "Sequence starts with 0, 1"}
            ],
            "performance_tests": [
                {"name": "fibonacci_performance", "input": 30, "max_time_seconds": 2.0, "description": "Reasonable performance for n=30"}
            ]
        }
    
    def _merge_sort_acceptance_tests(self) -> Dict[str, Any]:
        """Comprehensive merge sort acceptance tests"""
        return {
            "unit_tests": [
                {"name": "merge_sort_empty", "input": [], "expected_output": [], "description": "Empty list"},
                {"name": "merge_sort_single", "input": [5], "expected_output": [5], "description": "Single element"},
                {"name": "merge_sort_two", "input": [3, 1], "expected_output": [1, 3], "description": "Two elements"},
                {"name": "merge_sort_basic", "input": [64, 34, 25, 12, 22, 11, 90], "expected_output": [11, 12, 22, 25, 34, 64, 90], "description": "Basic sorting"}
            ],
            "edge_cases": [
                {"name": "merge_sort_already_sorted", "input": [1, 2, 3, 4, 5], "expected_output": [1, 2, 3, 4, 5], "description": "Already sorted"},
                {"name": "merge_sort_reverse_sorted", "input": [5, 4, 3, 2, 1], "expected_output": [1, 2, 3, 4, 5], "description": "Reverse sorted"},
                {"name": "merge_sort_duplicates", "input": [3, 1, 4, 1, 5, 9, 2, 6, 5], "expected_output": [1, 1, 2, 3, 4, 5, 5, 6, 9], "description": "With duplicates"}
            ],
            "property_tests": [
                {"name": "merge_sort_sorted", "property": "all(result[i] <= result[i+1] for i in range(len(result)-1))", "description": "Output is sorted"},
                {"name": "merge_sort_same_length", "property": "len(result) == len(input)", "description": "Same length as input"},
                {"name": "merge_sort_same_elements", "property": "sorted(result) == sorted(input)", "description": "Contains same elements"}
            ],
            "performance_tests": [
                {"name": "merge_sort_performance", "input": list(range(1000, 0, -1)), "max_time_seconds": 1.0, "description": "Performance on 1000 elements"}
            ]
        }
    
    def _binary_search_acceptance_tests(self) -> Dict[str, Any]:
        """Comprehensive binary search acceptance tests"""
        return {
            "unit_tests": [
                {"name": "binary_search_found", "input": ([1, 2, 3, 4, 5], 3), "expected_output": 2, "description": "Element found"},
                {"name": "binary_search_not_found", "input": ([1, 2, 4, 5], 3), "expected_output": -1, "description": "Element not found"},
                {"name": "binary_search_first", "input": ([1, 2, 3, 4, 5], 1), "expected_output": 0, "description": "First element"},
                {"name": "binary_search_last", "input": ([1, 2, 3, 4, 5], 5), "expected_output": 4, "description": "Last element"}
            ],
            "edge_cases": [
                {"name": "binary_search_empty", "input": ([], 1), "expected_output": -1, "description": "Empty array"},
                {"name": "binary_search_single_found", "input": ([5], 5), "expected_output": 0, "description": "Single element found"},
                {"name": "binary_search_single_not_found", "input": ([5], 3), "expected_output": -1, "description": "Single element not found"}
            ],
            "property_tests": [
                {"name": "binary_search_correctness", "property": "result == -1 or arr[result] == target", "description": "Returns correct index or -1"},
                {"name": "binary_search_bounds", "property": "result == -1 or (0 <= result < len(arr))", "description": "Index within bounds"}
            ],
            "performance_tests": [
                {"name": "binary_search_performance", "input": (list(range(10000)), 5000), "max_time_seconds": 0.1, "description": "Logarithmic time complexity"}
            ]
        }
    
    def _sieve_acceptance_tests(self) -> Dict[str, Any]:
        """Comprehensive sieve of Eratosthenes acceptance tests"""
        return {
            "unit_tests": [
                {"name": "sieve_small", "input": 10, "expected_output": [2, 3, 5, 7], "description": "Primes up to 10"},
                {"name": "sieve_medium", "input": 30, "expected_output": [2, 3, 5, 7, 11, 13, 17, 19, 23, 29], "description": "Primes up to 30"},
                {"name": "sieve_edge_2", "input": 2, "expected_output": [2], "description": "Only prime 2"}
            ],
            "edge_cases": [
                {"name": "sieve_zero", "input": 0, "expected_output": [], "description": "No primes below 0"},
                {"name": "sieve_one", "input": 1, "expected_output": [], "description": "No primes below 1"},
                {"name": "sieve_negative", "input": -5, "expected_output": [], "description": "Negative input"}
            ],
            "property_tests": [
                {"name": "sieve_all_prime", "property": "all(is_prime(p) for p in result)", "description": "All results are prime"},
                {"name": "sieve_in_range", "property": "all(2 <= p <= n for p in result)", "description": "All primes in range"},
                {"name": "sieve_sorted", "property": "result == sorted(result)", "description": "Results are sorted"}
            ],
            "performance_tests": [
                {"name": "sieve_performance", "input": 1000, "max_time_seconds": 0.5, "description": "Performance for n=1000"}
            ]
        }
    
    def _dijkstra_acceptance_tests(self) -> Dict[str, Any]:
        """Comprehensive Dijkstra's algorithm acceptance tests"""
        return {
            "unit_tests": [
                {"name": "dijkstra_simple", "input": ({'A': {'B': 1, 'C': 4}, 'B': {'C': 2, 'D': 5}, 'C': {'D': 1}, 'D': {}}, 'A'), 
                 "expected_output": {'A': 0, 'B': 1, 'C': 3, 'D': 4}, "description": "Simple graph"},
                {"name": "dijkstra_single_node", "input": ({'A': {}}, 'A'), "expected_output": {'A': 0}, "description": "Single node"}
            ],
            "edge_cases": [
                {"name": "dijkstra_disconnected", "input": ({'A': {'B': 1}, 'B': {}, 'C': {}}, 'A'), 
                 "expected_output": {'A': 0, 'B': 1, 'C': float('inf')}, "description": "Disconnected graph"},
                {"name": "dijkstra_empty", "input": ({}, 'A'), "expected_output": {}, "description": "Empty graph"}
            ],
            "property_tests": [
                {"name": "dijkstra_source_zero", "property": "result[source] == 0", "description": "Source distance is 0"},
                {"name": "dijkstra_non_negative", "property": "all(d >= 0 for d in result.values() if d != float('inf'))", "description": "Non-negative distances"}
            ],
            "performance_tests": [
                {"name": "dijkstra_performance", "input": "large_graph", "max_time_seconds": 2.0, "description": "Performance on large graph"}
            ]
        }
    
    def _default_acceptance_tests(self, prompt: AlgorithmPrompt) -> Dict[str, Any]:
        """Default acceptance tests for unknown algorithm families"""
        return {
            "unit_tests": [
                {"name": "basic_functionality", "input": "test_input", "expected_output": "expected", "description": "Basic functionality test"}
            ],
            "edge_cases": [
                {"name": "empty_input", "input": None, "expected_output": None, "description": "Handle empty input"}
            ],
            "property_tests": [
                {"name": "output_type", "property": f"isinstance(result, {prompt.expected_output_type})", "description": f"Output is {prompt.expected_output_type}"}
            ]
        }
    
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
