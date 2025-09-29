import json

# Load the latest merge_sort results
with open('outputs/merge_sort_temp1.5_20250929_164613.json', 'r') as f:
    data = json.load(f)

metrics = data['metrics']
print('='*70)
print('📊 MERGE_SORT RESULTS (Property-Driven Transformations)')
print('='*70)
print(f'  📈 R_raw: {metrics["R_raw"]:.1%}')
print(f'  🎯 R_behavioral: {metrics["R_behavioral"]:.1%}')
print(f'  🏗️  R_structural: {metrics["R_structural"]:.1%}')
print(f'  📊 Behavioral improvement: {metrics.get("behavioral_improvement", 0):.1%}')
print(f'  📊 Structural improvement: {metrics.get("structural_improvement", 0):.1%}')

print(f'\n🔧 Transformation Analysis:')
transform_results = data['transformation_results']
successful = sum(1 for t in transform_results if t.get('transformation_success', False) or not t.get('transformation_needed', True))
print(f'  ✅ Successful: {successful}/{len(transform_results)}')

# Check what keys are actually in the data
sample = transform_results[0] if transform_results else {}
print(f'  Keys available: {list(sample.keys())[:5]}...')

avg_dist_after = sum(t.get('final_distance', 1) for t in transform_results) / len(transform_results)
print(f'  📏 Avg final distance: {avg_dist_after:.3f}')

print(f'\n📋 Transformations Applied:')
all_transforms = []
for t in transform_results:
    transforms = t.get('transformations_applied', [])
    all_transforms.extend(transforms)

if all_transforms:
    from collections import Counter
    transform_counts = Counter(all_transforms)
    for name, count in transform_counts.most_common():
        print(f'  • {name}: {count}x')
else:
    print('  ⚠️  No transformations were applied!')

print(f'\n📊 Per-run details:')
for i, t in enumerate(transform_results[:5], 1):
    dist_after = t.get('final_distance', 1) 
    transforms = t.get('transformations_applied', [])
    needed = t.get('transformation_needed', True)
    success = t.get('transformation_success', False)
    status = '✅' if success or not needed else '⚠️'
    print(f'  Run {i}: {status} final_dist={dist_after:.3f} | {len(transforms)} transforms')
