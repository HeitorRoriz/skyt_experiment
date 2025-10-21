#!/usr/bin/env python3
"""Debug why StatementOrderingExplainer doesn't detect the pattern"""

from src.transformations.property_explainers import StatementOrderingExplainer
from src.foundational_properties import FoundationalProperties

# Run 2 from latest slugify experiment
code = """def slugify(text):
    import re
    text = text.lower()
    text = re.sub(r'[^a-z0-9\\s-]', '', text)
    text = re.sub(r'[\\s]+', '-', text)
    text = text.strip('-')
    return text"""

canon = """def slugify(text):
    import re
    text = text.lower()
    text = re.sub(r'[^a-z0-9\\s-]', '', text)
    text = re.sub(r'[\\s]+', '-', text)
    return text.strip('-')"""

print("="*80)
print("TESTING STATEMENT ORDERING EXPLAINER")
print("="*80)
print("\nCode (has separate text.strip + return):")
print(code)
print("\nCanon (has inline return text.strip):")
print(canon)
print()

# Extract properties
props_extractor = FoundationalProperties()
code_props = props_extractor.extract_all_properties(code)
canon_props = props_extractor.extract_all_properties(canon)

print("Code statement_ordering property:")
print(code_props.get('statement_ordering'))
print("\nCanon statement_ordering property:")
print(canon_props.get('statement_ordering'))
print()

# Try explainer
explainer = StatementOrderingExplainer()
diff = explainer.explain_difference(
    code_props.get('statement_ordering'),
    canon_props.get('statement_ordering'),
    code,
    canon
)

if diff:
    print("✓ DIFFERENCE DETECTED!")
    print(f"  Type: {diff.difference_type}")
    print(f"  Explanation: {diff.explanation}")
    print(f"  Hints: {diff.transformation_hints}")
else:
    print("✗ NO DIFFERENCE DETECTED - THIS IS THE BUG!")
    print("\nDebugging why...")
    
    # Manually check pattern analysis
    import ast
    code_tree = ast.parse(code)
    canon_tree = ast.parse(canon)
    
    code_pattern = explainer._analyze_statement_pattern(code_tree)
    canon_pattern = explainer._analyze_statement_pattern(canon_tree)
    
    print(f"  Code pattern: {code_pattern}")
    print(f"  Canon pattern: {canon_pattern}")
