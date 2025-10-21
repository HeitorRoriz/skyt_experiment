#!/usr/bin/env python3
"""Test why PropertyDrivenTransformer doesn't fire in real experiments"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.transformations.property_driven_transformer import PropertyDrivenTransformer

# Exact code from slugify run that should transform
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

print("Testing PropertyDrivenTransformer integration...")
print("="*80)

# Load contract
import json
with open('contracts/templates.json') as f:
    contracts = json.load(f)
    contract = contracts['slugify']

print("Contract loaded:", contract['id'])
print()

# Test transformer
transformer = PropertyDrivenTransformer(contract=contract, debug_mode=False)

print("Calling transformer.transform()...")
result = transformer.transform(code, canon)

print(f"\nResult:")
print(f"  Success: {result.success}")
print(f"  Code changed: {result.transformed_code != code}")
print(f"  Matches canon: {result.transformed_code.strip() == canon.strip()}")
print(f"  Transformation history: {len(transformer.transformation_history)}")

if transformer.transformation_history:
    print("\nTransformations applied:")
    for t in transformer.transformation_history:
        print(f"  - {t['strategy']}: {t['difference_type']}")
else:
    print("\nNO TRANSFORMATIONS APPLIED - This is the bug!")
    
print("\nTransformed code:")
print(result.transformed_code)
