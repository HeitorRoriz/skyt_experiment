"""
Unit tests for ImportNormalizer

Tests the addition of missing import statements to match canonical form
"""

import unittest
from src.transformations.structural.import_normalizer import ImportNormalizer


class TestImportNormalizer(unittest.TestCase):
    """Test cases for ImportNormalizer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.normalizer = ImportNormalizer()
        self.normalizer.enable_debug()
    
    def test_add_missing_from_import(self):
        """Test adding missing 'from X import Y' statement"""
        
        code = """class LRUCache:
    def __init__(self, capacity):
        self.cache = OrderedDict()
        self.capacity = capacity"""
        
        canon = """from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity):
        self.cache = OrderedDict()
        self.capacity = capacity"""
        
        # Check if transformation is needed
        self.assertTrue(self.normalizer.can_transform(code, canon))
        
        # Apply transformation
        result = self.normalizer.transform(code, canon)
        
        # Verify transformation succeeded
        self.assertTrue(result.success)
        
        # Verify import was added
        self.assertIn("from collections import OrderedDict", result.transformed_code)
        self.assertIn("class LRUCache", result.transformed_code)
    
    def test_add_missing_regular_import(self):
        """Test adding missing 'import X' statement"""
        
        code = """def process_data():
    data = json.loads('{"key": "value"}')
    return data"""
        
        canon = """import json

def process_data():
    data = json.loads('{"key": "value"}')
    return data"""
        
        # Apply transformation
        result = self.normalizer.transform(code, canon)
        
        # Verify transformation succeeded
        self.assertTrue(result.success)
        
        # Verify import was added
        self.assertIn("import json", result.transformed_code)
    
    def test_already_has_imports(self):
        """Test that code with correct imports is not transformed"""
        
        code = """from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity):
        self.cache = OrderedDict()"""
        
        canon = code  # Same as code
        
        # Should not need transformation
        self.assertFalse(self.normalizer.can_transform(code, canon))
    
    def test_multiple_missing_imports(self):
        """Test adding multiple missing imports"""
        
        code = """def process():
    data = json.loads('{}')
    dt = datetime.now()
    return data, dt"""
        
        canon = """import json
from datetime import datetime

def process():
    data = json.loads('{}')
    dt = datetime.now()
    return data, dt"""
        
        # Apply transformation
        result = self.normalizer.transform(code, canon)
        
        # Verify both imports were added
        self.assertIn("import json", result.transformed_code)
        self.assertIn("from datetime import datetime", result.transformed_code)
    
    def test_preserves_existing_code(self):
        """Test that existing code is preserved when adding imports"""
        
        code = """class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = OrderedDict()
    
    def get(self, key):
        return self.cache.get(key, -1)
    
    def put(self, key, value):
        self.cache[key] = value"""
        
        canon = """from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity):
        pass"""
        
        result = self.normalizer.transform(code, canon)
        
        # Verify import was added
        self.assertIn("from collections import OrderedDict", result.transformed_code)
        
        # Verify all methods are preserved
        self.assertIn("def __init__", result.transformed_code)
        self.assertIn("def get", result.transformed_code)
        self.assertIn("def put", result.transformed_code)
        self.assertIn("self.capacity = capacity", result.transformed_code)
        self.assertIn("self.cache[key] = value", result.transformed_code)
    
    def test_import_with_alias(self):
        """Test adding import with alias"""
        
        code = """def process():
    df = pd.DataFrame()
    return df"""
        
        canon = """import pandas as pd

def process():
    df = pd.DataFrame()
    return df"""
        
        # Apply transformation
        result = self.normalizer.transform(code, canon)
        
        # Verify import with alias was added
        self.assertIn("import pandas as pd", result.transformed_code)
    
    def test_from_import_with_alias(self):
        """Test adding from import with alias"""
        
        code = """def process():
    cache = OD()
    return cache"""
        
        canon = """from collections import OrderedDict as OD

def process():
    cache = OD()
    return cache"""
        
        # Apply transformation
        result = self.normalizer.transform(code, canon)
        
        # Verify from import with alias was added
        self.assertIn("from collections import OrderedDict as OD", result.transformed_code)
    
    def test_no_imports_needed(self):
        """Test code that doesn't need any imports"""
        
        code = """def add(a, b):
    return a + b"""
        
        canon = """def add(a, b):
    return a + b"""
        
        # Should not need transformation
        self.assertFalse(self.normalizer.can_transform(code, canon))
    
    def test_extract_imports(self):
        """Test the import extraction method"""
        
        import ast
        
        code = """import json
from collections import OrderedDict
from datetime import datetime as dt"""
        
        tree = ast.parse(code)
        imports = self.normalizer._extract_imports(tree)
        
        # Verify all imports were extracted
        self.assertIn(('import', 'json', None), imports)
        self.assertIn(('from', 'collections', 'OrderedDict', None), imports)
        self.assertIn(('from', 'datetime', 'datetime', 'dt'), imports)
        self.assertEqual(len(imports), 3)
    
    def test_import_ordering(self):
        """Test that imports are added at the beginning"""
        
        code = """# This is a comment

class MyClass:
    pass"""
        
        canon = """from collections import OrderedDict

class MyClass:
    pass"""
        
        result = self.normalizer.transform(code, canon)
        
        # Verify import comes before class
        import_pos = result.transformed_code.find("from collections import OrderedDict")
        class_pos = result.transformed_code.find("class MyClass")
        
        self.assertLess(import_pos, class_pos, "Import should come before class definition")


if __name__ == '__main__':
    unittest.main()
