"""
Unit tests for ClassMethodReorderer

Tests the reordering of class methods to canonical order
"""

import unittest
from src.transformations.structural.class_method_reorderer import ClassMethodReorderer


class TestClassMethodReorderer(unittest.TestCase):
    """Test cases for ClassMethodReorderer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.reorderer = ClassMethodReorderer()
        self.reorderer.enable_debug()
    
    def test_reorder_simple_methods(self):
        """Test reordering of simple methods"""
        
        code = """class LRUCache:
    def put(self, key, value):
        pass
    
    def __init__(self, capacity):
        pass
    
    def get(self, key):
        pass"""
        
        canon = """class LRUCache:
    def __init__(self, capacity):
        pass
    
    def get(self, key):
        pass
    
    def put(self, key, value):
        pass"""
        
        # Check if transformation is needed
        self.assertTrue(self.reorderer.can_transform(code, canon))
        
        # Apply transformation
        result = self.reorderer.transform(code, canon)
        
        # Verify transformation succeeded
        self.assertTrue(result.success)
        
        # Verify methods are in correct order
        self.assertIn("def __init__", result.transformed_code)
        self.assertIn("def get", result.transformed_code)
        self.assertIn("def put", result.transformed_code)
        
        # Verify __init__ comes before get
        init_pos = result.transformed_code.find("def __init__")
        get_pos = result.transformed_code.find("def get")
        put_pos = result.transformed_code.find("def put")
        
        self.assertLess(init_pos, get_pos, "__init__ should come before get")
        self.assertLess(get_pos, put_pos, "get should come before put")
    
    def test_already_ordered(self):
        """Test that already ordered code is not transformed"""
        
        code = """class LRUCache:
    def __init__(self, capacity):
        pass
    
    def get(self, key):
        pass
    
    def put(self, key, value):
        pass"""
        
        canon = code  # Same as code
        
        # Should not need transformation
        self.assertFalse(self.reorderer.can_transform(code, canon))
    
    def test_special_methods_first(self):
        """Test that special methods come before regular methods"""
        
        code = """class MyClass:
    def custom_method(self):
        pass
    
    def __str__(self):
        return "MyClass"
    
    def __init__(self):
        pass
    
    def another_method(self):
        pass"""
        
        canon = """class MyClass:
    def __init__(self):
        pass
    
    def __str__(self):
        return "MyClass"
    
    def another_method(self):
        pass
    
    def custom_method(self):
        pass"""
        
        # Apply transformation
        result = self.reorderer.transform(code, canon)
        
        # Verify transformation succeeded
        self.assertTrue(result.success)
        
        # Verify order: __init__, __str__, then alphabetical
        init_pos = result.transformed_code.find("def __init__")
        str_pos = result.transformed_code.find("def __str__")
        another_pos = result.transformed_code.find("def another_method")
        custom_pos = result.transformed_code.find("def custom_method")
        
        self.assertLess(init_pos, str_pos, "__init__ should come before __str__")
        self.assertLess(str_pos, another_pos, "__str__ should come before another_method")
        self.assertLess(another_pos, custom_pos, "another_method should come before custom_method (alphabetical)")
    
    def test_preserves_method_bodies(self):
        """Test that method bodies are preserved"""
        
        code = """class LRUCache:
    def put(self, key, value):
        self.cache[key] = value
        print("Put:", key, value)
    
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}
    
    def get(self, key):
        return self.cache.get(key, -1)"""
        
        canon = """class LRUCache:
    def __init__(self, capacity):
        pass
    
    def get(self, key):
        pass
    
    def put(self, key, value):
        pass"""
        
        result = self.reorderer.transform(code, canon)
        
        # Verify method bodies are preserved
        self.assertIn("self.capacity = capacity", result.transformed_code)
        self.assertIn("self.cache = {}", result.transformed_code)
        self.assertIn("self.cache[key] = value", result.transformed_code)
        # ast.unparse may change quote style, so check for either
        self.assertTrue(
            'print("Put:", key, value)' in result.transformed_code or
            "print('Put:', key, value)" in result.transformed_code,
            "print statement not found in transformed code"
        )
        self.assertIn("return self.cache.get(key, -1)", result.transformed_code)
    
    def test_multiple_classes(self):
        """Test reordering with multiple classes"""
        
        code = """class ClassA:
    def method_b(self):
        pass
    
    def method_a(self):
        pass

class ClassB:
    def __init__(self):
        pass
    
    def method_z(self):
        pass
    
    def method_a(self):
        pass"""
        
        canon = """class ClassA:
    def method_a(self):
        pass
    
    def method_b(self):
        pass

class ClassB:
    def __init__(self):
        pass
    
    def method_a(self):
        pass
    
    def method_z(self):
        pass"""
        
        result = self.reorderer.transform(code, canon)
        
        # Verify both classes are reordered
        self.assertTrue(result.success)
        self.assertIn("class ClassA", result.transformed_code)
        self.assertIn("class ClassB", result.transformed_code)
    
    def test_preserves_class_attributes(self):
        """Test that class attributes are preserved"""
        
        code = """class LRUCache:
    MAX_SIZE = 100
    
    def put(self, key, value):
        pass
    
    def __init__(self, capacity):
        pass
    
    DEFAULT_CAPACITY = 10
    
    def get(self, key):
        pass"""
        
        canon = """class LRUCache:
    def __init__(self, capacity):
        pass
    
    def get(self, key):
        pass
    
    def put(self, key, value):
        pass"""
        
        result = self.reorderer.transform(code, canon)
        
        # Verify class attributes are preserved
        self.assertIn("MAX_SIZE = 100", result.transformed_code)
        self.assertIn("DEFAULT_CAPACITY = 10", result.transformed_code)
    
    def test_no_classes(self):
        """Test that code without classes is not transformed"""
        
        code = """def standalone_function():
    pass

def another_function():
    pass"""
        
        canon = code
        
        # Should not need transformation
        self.assertFalse(self.reorderer.can_transform(code, canon))
    
    def test_extract_method_order(self):
        """Test the method order extraction"""
        
        import ast
        
        code = """class LRUCache:
    def put(self, key, value):
        pass
    
    def __init__(self, capacity):
        pass
    
    def get(self, key):
        pass"""
        
        tree = ast.parse(code)
        method_order = self.reorderer._extract_method_order(tree)
        
        self.assertEqual(len(method_order), 3)
        self.assertEqual(method_order[0], ('LRUCache', 'put'))
        self.assertEqual(method_order[1], ('LRUCache', '__init__'))
        self.assertEqual(method_order[2], ('LRUCache', 'get'))


if __name__ == '__main__':
    unittest.main()
