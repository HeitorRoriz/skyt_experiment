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

def create_test_prompts() -> TestPromptGenerator:
    """Factory function to create test prompt generator"""
    return TestPromptGenerator()
