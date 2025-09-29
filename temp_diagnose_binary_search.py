import json
import sys
sys.path.insert(0, 'src')
from foundational_properties import FoundationalProperties

with open('outputs/binary_search_temp1.5_20250929_170021.json', 'r') as f:
    data = json.load(f)

# Get one example transformation
result = data['transformation_results'][0]  # First run
canon_code = data['canon_data']['canonical_code']

print('='*80)
print('DIAGNOSTIC: Why Transformations Failing for Binary Search')
print('='*80)

print('\nCANONICAL CODE:')
print(canon_code)

print('\nORIGINAL LLM OUTPUT (Run 1):')
print(result['original_code'][:500])

print('\nAFTER TRANSFORMATION (Run 1):')
print(result['transformed_code'][:500])

print('\nTRANSFORMATIONS APPLIED:')
print(result.get('transformations_applied', []))

print('\nCOMPUTING PROPERTY DIFFERENCES...')
props = FoundationalProperties()
original_props = props.extract_all_properties(result['original_code'])
canon_props = data['canon_data']['foundational_properties']

print('\nPROPERTY DISTANCES (Original vs Canon):')
for prop_name in props.properties:
    if prop_name in original_props and prop_name in canon_props:
        dist = props._calculate_property_distance(
            original_props[prop_name],
            canon_props[prop_name],
            prop_name
        )
        if dist > 0:
            print(f'  {prop_name}: {dist:.3f}')

# Check variable names
print('\nVARIABLE NAME ANALYSIS:')
import re
def extract_vars(code):
    vars = set(re.findall(r'\b[a-z_][a-z0-9_]*\b', code))
    keywords = {'if', 'else', 'for', 'while', 'def', 'return', 'len', 'range', 'in', 'and', 'or', 'not'}
    return vars - keywords

canon_vars = extract_vars(canon_code)
original_vars = extract_vars(result['original_code'])
print(f'  Canon variables: {sorted(canon_vars)}')
print(f'  Original variables: {sorted(original_vars)}')
print(f'  Difference: {original_vars - canon_vars}')

# Check if VariableRenamer should have fired
print('\nWHY DIDNT VARIABLERENAMER FIRE MORE?')
alpha_curr = original_props.get('normalized_ast_structure', {}).get('alpha_renamed_hash')
alpha_canon = canon_props.get('normalized_ast_structure', {}).get('alpha_renamed_hash')
hash_curr = original_props.get('normalized_ast_structure', {}).get('ast_hash')
hash_canon = canon_props.get('normalized_ast_structure', {}).get('ast_hash')

print(f'  Alpha-renamed match: {alpha_curr == alpha_canon}')
print(f'  Regular AST match: {hash_curr == hash_canon}')
print(f'  Should trigger VariableRenamer: {alpha_curr == alpha_canon and hash_curr != hash_canon}')
