import json

print('='*70)
print('FIBONACCI Transformation Results:')
print('='*70)
with open('outputs/fibonacci_basic_temp1.5_20250929_144431.json', 'r') as f:
    fib_data = json.load(f)

for i, t in enumerate(fib_data['transformation_results'][:3], 1):
    trans = t.get('transformations_applied', [])
    dist = t.get('final_distance', 1)
    print(f'Run {i}: distance={dist:.3f}, transforms={trans}')

print('\n' + '='*70)
print('MERGE_SORT Transformation Results:')
print('='*70)
with open('outputs/merge_sort_temp1.5_20250929_145447.json', 'r') as f:
    merge_data = json.load(f)

for i, t in enumerate(merge_data['transformation_results'][:3], 1):
    trans = t.get('transformations_applied', [])
    dist = t.get('final_distance', 1)
    print(f'Run {i}: distance={dist:.3f}, transforms={trans}')

print('\n' + '='*70)
print('KEY DIFFERENCE FOUND!')
print('='*70)
