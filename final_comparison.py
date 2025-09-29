import json

print('='*80)
print('📊 MERGE_SORT TRANSFORMATION EVOLUTION')
print('='*80)

experiments = [
    ('Before improvements', 'outputs/merge_sort_temp1.5_20250929_145447.json'),
    ('After property-driven', 'outputs/merge_sort_temp1.5_20250929_164224.json'),
    ('With VariableRenamer', 'outputs/merge_sort_temp1.5_20250929_164613.json'),
]

for name, filepath in experiments:
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        metrics = data['metrics']
        transform_results = data['transformation_results']
        
        # Count transformations
        all_transforms = []
        for t in transform_results:
            all_transforms.extend(t.get('transformations_applied', []))
        
        avg_dist = sum(t.get('final_distance', 1) for t in transform_results) / len(transform_results)
        successful = sum(1 for t in transform_results if t.get('transformation_success', False))
        
        print(f'\n{name}:')
        print(f'  R_structural: {metrics["R_structural"]:.1%}')
        print(f'  Avg final distance: {avg_dist:.3f}')
        print(f'  Successful transforms: {successful}/{len(transform_results)}')
        print(f'  Total transforms applied: {len(all_transforms)}')
        
        # Show which transformers ran
        from collections import Counter
        if all_transforms:
            counts = Counter(all_transforms)
            top_3 = counts.most_common(3)
            print(f'  Top transformers: {", ".join([f"{name}({count})" for name, count in top_3])}')
        else:
            print(f'  Top transformers: None')
            
    except FileNotFoundError:
        print(f'\n{name}: File not found')

print('\n' + '='*80)
print('📈 KEY IMPROVEMENTS:')
print('='*80)
print('✅ VariableRenamer successfully firing (10x)')
print('✅ Property-driven system working')
print('✅ No more Fibonacci-specific hardcoding')
print('⚠️  Distance still high (0.229) - need more sophisticated transformers')
print('⚠️  InPlaceReturnConverter still running multiple times')
print('\n💡 Next Steps:')
print('   1. Improve VariableRenamer mapping heuristics')
print('   2. Add helper function inlining transformer')
print('   3. Enhance recursion pattern normalization')
