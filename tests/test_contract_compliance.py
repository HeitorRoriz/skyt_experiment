"""
Unit tests for Contract Compliance Checker

Tests validation of:
- Function/class names
- Required methods/classes/attributes
- Recursion requirements  
- Algorithm patterns (doubly-linked list, binary search, etc.)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.contract_compliance_checker import ContractComplianceChecker


def test_function_name_compliance():
    """Test function name validation"""
    checker = ContractComplianceChecker()
    
    code_correct = """
def fibonacci(n):
    return n
"""
    
    code_wrong = """
def fib(n):
    return n
"""
    
    contract = {
        "constraints": {
            "function_name": "fibonacci"
        }
    }
    
    # Test correct
    result = checker.check_compliance(code_correct, contract)
    assert result.fully_compliant, "Should be compliant"
    assert result.score == 1.0
    
    # Test wrong
    result = checker.check_compliance(code_wrong, contract)
    assert not result.fully_compliant, "Should not be compliant"
    assert "fibonacci" in result.violations[0]
    
    print("✅ test_function_name_compliance passed")


def test_class_and_methods_compliance():
    """Test class name and methods validation"""
    checker = ContractComplianceChecker()
    
    code_correct = """
class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
    
    def get(self, key):
        return -1
    
    def put(self, key, value):
        pass
"""
    
    code_missing_method = """
class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
    
    def get(self, key):
        return -1
"""
    
    contract = {
        "constraints": {
            "class_name": "LRUCache",
            "methods": ["__init__", "get", "put"]
        }
    }
    
    # Test correct
    result = checker.check_compliance(code_correct, contract)
    assert result.fully_compliant, "Should be compliant"
    
    # Test missing method
    result = checker.check_compliance(code_missing_method, contract)
    assert not result.fully_compliant, "Should not be compliant"
    assert "put" in result.violations[0]
    
    print("✅ test_class_and_methods_compliance passed")


def test_required_classes_compliance():
    """Test required classes validation"""
    checker = ContractComplianceChecker()
    
    code_with_node = """
class Node:
    def __init__(self, key, value):
        self.key = key
        self.value = value

class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
"""
    
    code_without_node = """
class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
"""
    
    contract = {
        "constraints": {
            "required_classes": ["Node", "LRUCache"]
        }
    }
    
    # Test with Node
    result = checker.check_compliance(code_with_node, contract)
    assert result.fully_compliant, "Should be compliant"
    
    # Test without Node
    result = checker.check_compliance(code_without_node, contract)
    assert not result.fully_compliant, "Should not be compliant"
    assert "Node" in result.violations[0]
    
    print("✅ test_required_classes_compliance passed")


def test_required_attributes_compliance():
    """Test required attributes validation"""
    checker = ContractComplianceChecker()
    
    code_with_prev_next = """
class Node:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None
"""
    
    code_without_prev_next = """
class Node:
    def __init__(self, key, value):
        self.key = key
        self.value = value
"""
    
    contract = {
        "constraints": {
            "required_attributes": {
                "Node": ["key", "value", "prev", "next"]
            }
        }
    }
    
    # Test with prev/next
    result = checker.check_compliance(code_with_prev_next, contract)
    assert result.fully_compliant, "Should be compliant"
    
    # Test without prev/next
    result = checker.check_compliance(code_without_prev_next, contract)
    assert not result.fully_compliant, "Should not be compliant"
    assert len(result.violations) == 2  # Missing prev and next
    
    print("✅ test_required_attributes_compliance passed")


def test_recursion_compliance():
    """Test recursion requirement validation"""
    checker = ContractComplianceChecker()
    
    code_recursive = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    
    code_iterative = """
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
"""
    
    contract_requires_recursive = {
        "constraints": {
            "requires_recursion": True
        }
    }
    
    contract_requires_iterative = {
        "constraints": {
            "requires_recursion": False
        }
    }
    
    # Test recursive code with recursive requirement
    result = checker.check_compliance(code_recursive, contract_requires_recursive)
    assert result.fully_compliant, "Recursive code should comply with recursive requirement"
    
    # Test iterative code with recursive requirement
    result = checker.check_compliance(code_iterative, contract_requires_recursive)
    assert not result.fully_compliant, "Iterative code should not comply with recursive requirement"
    
    # Test iterative code with iterative requirement
    result = checker.check_compliance(code_iterative, contract_requires_iterative)
    assert result.fully_compliant, "Iterative code should comply with iterative requirement"
    
    print("✅ test_recursion_compliance passed")


def test_doubly_linked_list_algorithm():
    """Test doubly-linked list algorithm detection"""
    checker = ContractComplianceChecker()
    
    code_doubly_linked = """
class Node:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None

class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}
        self.head = Node(0, 0)
        self.tail = Node(0, 0)
"""
    
    code_simple_list = """
class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}
        self.order = []
"""
    
    contract = {
        "constraints": {
            "algorithm": "doubly-linked list with hash map"
        }
    }
    
    # Test doubly-linked list
    result = checker.check_compliance(code_doubly_linked, contract)
    assert result.fully_compliant, "Should detect doubly-linked list"
    
    # Test simple list
    result = checker.check_compliance(code_simple_list, contract)
    assert not result.fully_compliant, "Should reject simple list"
    assert "doubly-linked list" in result.violations[0].lower()
    
    print("✅ test_doubly_linked_list_algorithm passed")


def test_binary_search_algorithm():
    """Test binary search algorithm detection"""
    checker = ContractComplianceChecker()
    
    code_binary = """
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
"""
    
    code_linear = """
def binary_search(arr, target):
    for i, val in enumerate(arr):
        if val == target:
            return i
    return -1
"""
    
    contract = {
        "constraints": {
            "algorithm": "binary search"
        }
    }
    
    # Test binary search
    result = checker.check_compliance(code_binary, contract)
    assert result.fully_compliant, "Should detect binary search"
    
    # Test linear search
    result = checker.check_compliance(code_linear, contract)
    assert not result.fully_compliant, "Should reject linear search"
    
    print("✅ test_binary_search_algorithm passed")


def test_euclidean_algorithm():
    """Test Euclidean algorithm detection"""
    checker = ContractComplianceChecker()
    
    code_euclidean = """
def gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return a
"""
    
    code_brute_force = """
def gcd(a, b):
    result = 1
    for i in range(1, min(a, b) + 1):
        if a % i == 0 and b % i == 0:
            result = i
    return result
"""
    
    contract = {
        "constraints": {
            "algorithm": "euclidean algorithm"
        }
    }
    
    # Test Euclidean
    result = checker.check_compliance(code_euclidean, contract)
    assert result.fully_compliant, "Should detect Euclidean algorithm"
    
    # Test brute force
    result = checker.check_compliance(code_brute_force, contract)
    assert not result.fully_compliant, "Should reject brute force"
    
    print("✅ test_euclidean_algorithm passed")


def test_empty_contract():
    """Test that code is compliant when contract has no constraints"""
    checker = ContractComplianceChecker()
    
    code = """
def anything():
    pass
"""
    
    contract = {}
    
    result = checker.check_compliance(code, contract)
    assert result.fully_compliant, "Should be compliant with empty contract"
    assert result.score == 1.0
    
    print("✅ test_empty_contract passed")


def test_partial_compliance_score():
    """Test compliance scoring when some requirements met"""
    checker = ContractComplianceChecker()
    
    code = """
class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
    
    def get(self, key):
        return -1
"""
    
    contract = {
        "constraints": {
            "class_name": "LRUCache",  # ✅ Met
            "methods": ["__init__", "get", "put"],  # ❌ Missing put
            "required_classes": ["Node", "LRUCache"]  # ❌ Missing Node
        }
    }
    
    result = checker.check_compliance(code, contract)
    assert not result.fully_compliant
    assert 0.0 < result.score < 1.0, "Score should be between 0 and 1"
    assert len(result.violations) == 2  # Missing put and Node
    
    print("✅ test_partial_compliance_score passed")


if __name__ == "__main__":
    test_function_name_compliance()
    test_class_and_methods_compliance()
    test_required_classes_compliance()
    test_required_attributes_compliance()
    test_recursion_compliance()
    test_doubly_linked_list_algorithm()
    test_binary_search_algorithm()
    test_euclidean_algorithm()
    test_empty_contract()
    test_partial_compliance_score()
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED")
    print("="*70)
