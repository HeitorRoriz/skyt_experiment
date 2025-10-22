#!/usr/bin/env python3
"""Test StringLiteralExplainer"""

from src.transformations.property_explainers import StringLiteralExplainer
from src.transformations.transformation_strategies import StringNormalizationStrategy

code1 = """def slugify(text):
    import re
    text = text.lower()
    text = re.sub(r'[^a-z0-9\\s-]', '', text)
    text = re.sub(r'\\s+', '-', text)
    text = text.strip('-')
    return text"""

canon = """def slugify(text):
    import re
    text = text.lower()
    text = re.sub(r'[^a-z0-9\\s-]', '', text)
    text = re.sub(r'[\\s]+', '-', text)
    return text.strip('-')"""

print("="*80)
print("TEST: StringLiteralExplainer")
print("="*80)
print("Code has:  r'\\s+' and  separate return")
print("Canon has: r'[\\s]+' and inline return")
print()

explainer = StringLiteralExplainer()
diff = explainer.explain_difference(None, None, code1, canon)

if diff:
    print(f"✓ Difference detected: {diff.difference_type}")
    print(f"  Explanation: {diff.explanation}")
    print(f"  Severity: {diff.severity}")
    print(f"  Hints: {diff.transformation_hints}")
    print()
    
    # Try strategy
    strategy = StringNormalizationStrategy()
    if strategy.can_handle(diff):
        print("✓ Strategy can handle this")
        
        transformed = strategy.generate_transformation(diff, code1)
        if transformed:
            print("\n✓ Transformed!")
            print(transformed)
        else:
            print("\n✗ Transformation returned None")
    else:
        print("✗ Strategy cannot handle this")
else:
    print("✗ No difference detected")
