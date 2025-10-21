#!/usr/bin/env python3
"""Test PropertyDrivenTransformer when called through TransformationPipeline"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.transformations.transformation_pipeline import TransformationPipeline

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

print("Testing TransformationPipeline...")
print("="*80)

# Load contract
import json
with open('contracts/templates.json') as f:
    contracts = json.load(f)
    contract = contracts['slugify']

print("Contract loaded:", contract['id'])
print()

# Create pipeline
pipeline = TransformationPipeline(debug_mode=False, contract=contract)

print("Calling pipeline.transform_code()...")
result = pipeline.transform_code(code, canon, max_iterations=3, contract=contract, contract_id='slugify')

print(f"\nResult:")
print(f"  Transformation success: {result['transformation_success']}")
print(f"  Code changed: {result['final_code'] != code}")
print(f"  Matches canon: {result['final_code'].strip() == canon.strip()}")
print(f"  Successful transformations: {result['successful_transformations']}")

if result['successful_transformations']:
    print("\nTransformations applied:")
    for t in result['successful_transformations']:
        print(f"  - {t}")
else:
    print("\nNO TRANSFORMATIONS APPLIED - This would be the bug!")
    
print("\nFinal code:")
print(result['final_code'])
