import json

with open('outputs/merge_sort_temp1.5_20250929_145447.json', 'r') as f:
    data = json.load(f)

metrics = data['metrics']
print('📊 MERGE_SORT EXPERIMENT RESULTS (with improvements):')
print(f'  📈 R_raw: {metrics["R_raw"]:.1%}')
print(f'  🎯 R_behavioral: {metrics["R_behavioral"]:.1%}')
print(f'  🏗️  R_structural: {metrics["R_structural"]:.1%}')
print(f'  📊 Behavioral improvement: {metrics.get("behavioral_improvement", 0):.1%}')
print(f'  📊 Structural improvement: {metrics.get("structural_improvement", 0):.1%}')

print(f'\n🔧 Transformation Stats:')
transform_results = data['transformation_results']
successful = sum(1 for t in transform_results if t.get('transformation_success', False) or not t.get('transformation_needed', True))
print(f'  ✅ Successful: {successful}/{len(transform_results)}')
avg_dist = sum(t.get("final_distance", 1) for t in transform_results) / len(transform_results)
print(f'  📏 Avg final distance: {avg_dist:.3f}')

print(f'\n📋 Per-run breakdown:')
for i, t in enumerate(transform_results[:5], 1):
    status = "✅" if t.get('transformation_success', False) or not t.get('transformation_needed', True) else "⚠️"
    dist = t.get('final_distance', 1)
    print(f'  Run {i}: {status} distance={dist:.3f}')
