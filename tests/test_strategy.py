#!/usr/bin/env python3
"""Test if strategy actually works on variation 2"""

from src.transformations.property_explainers import StatementOrderingExplainer
from src.transformations.transformation_strategies import StatementConsolidationStrategy

code = """def slugify(string):
    import re
    string = string.lower()
    string = re.sub(r'[^a-z0-9\\s-]', '', string)
    string = re.sub(r'\\s+', '-', string)
    string = string.strip('-')
    return string"""

canon = """def slugify(text):
    import re
    text = text.lower()
    text = re.sub(r'[^a-z0-9\\s-]', '', text)
    text = re.sub(r'[\\s]+', '-', text)
    return text.strip('-')"""

print("="*80)
print("TESTING STRATEGY ON VARIATION 2")
print("="*80)
print("\nOriginal code:")
print(code)
print()

# Try explainer
explainer = StatementOrderingExplainer()
from src.foundational_properties import FoundationalProperties

props_extractor = FoundationalProperties()
code_props = props_extractor.extract_all_properties(code)
canon_props = props_extractor.extract_all_properties(canon)

diff = explainer.explain_difference(
    code_props.get("statement_ordering"),
    canon_props.get("statement_ordering"),
    code, canon
)

if diff:
    print(f"✓ Difference detected: {diff.difference_type}")
    print(f"  Explanation: {diff.explanation}")
    print()
    
    # Try strategy
    strategy = StatementConsolidationStrategy()
    
    if strategy.can_handle(diff):
        print("✓ Strategy can handle this difference")
        
        transformed = strategy.generate_transformation(diff, code)
        
        if transformed:
            print("\n✓ Transformation successful!")
            print("\nTransformed code:")
            print(transformed)
            
            if transformed != code:
                print("\n✓ Code was actually changed")
            else:
                print("\n✗ Code unchanged")
        else:
            print("\n✗ Strategy returned None")
    else:
        print("✗ Strategy cannot handle this difference")
else:
    print("✗ No difference detected")
