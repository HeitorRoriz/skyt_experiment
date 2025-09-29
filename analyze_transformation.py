import json

with open('outputs/merge_sort_temp1.5_20250929_145447.json', 'r') as f:
    data = json.load(f)

# Check one transformation result
t = data['transformation_results'][0]
print('📋 TRANSFORMATION ANALYSIS - Run 1')
print('='*60)
print(f'Original distance: 0.393')
print(f'Final distance: {t["final_distance"]:.3f}')
print(f'Transformations applied: {t.get("transformations_applied", [])}')
print(f'\n🔍 Original code (first 400 chars):')
print(t['original_code'][:400])
print(f'\n🔧 Transformed code (first 400 chars):')
print(t['transformed_code'][:400])
print(f'\n📊 Canon code (first 400 chars):')
print(data['canon_data']['canonical_code'][:400])

# Now check property differences
print(f'\n\n🔬 CHECKING PROPERTY CALCULATION')
print('='*60)
import sys
sys.path.insert(0, 'src')
from foundational_properties import FoundationalProperties

props = FoundationalProperties()
trans_props = props.extract_all_properties(t['transformed_code'])
canon_props = data['canon_data']['foundational_properties']

# Calculate distance per property
print('\n📊 Property-by-property distance:')
for prop_name in props.properties:
    if prop_name in trans_props and prop_name in canon_props:
        dist = props._calculate_property_distance(trans_props[prop_name], canon_props[prop_name], prop_name)
        if dist > 0:
            print(f'  {prop_name}: {dist:.3f}')
