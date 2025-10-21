#!/usr/bin/env python3
"""Test the complete transformation pipeline"""

from src.transformations.property_driven_transformer import PropertyDrivenTransformer

# Test case: slugify with separate text.strip('-') + return text
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
print("Testing PropertyDrivenTransformer")
print("="*80)
print("\nCode:")
print(code)
print("\nCanon:")
print(canon)
print()

transformer = PropertyDrivenTransformer(contract=None, debug_mode=True)
result = transformer.transform(code, canon)

print("\n" + "="*80)
print("RESULT")
print("="*80)
print(f"Success: {result.success}")
print(f"\nTransformed Code:")
print(result.transformed_code)
print(f"\nCode == Canon: {result.transformed_code.strip() == canon.strip()}")
print(f"\nTransformations: {len(transformer.transformation_history)}")
for t in transformer.transformation_history:
    print(f"  - {t['strategy']}: {t['property']}.{t['difference_type']}")
