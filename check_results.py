#!/usr/bin/env python3
"""Check transformation results"""

import json

with open('outputs/slugify_temp0.8_20251021_182107.json') as f:
    data = json.load(f)

print("="*80)
print("TRANSFORMATION RESULTS")
print("="*80)

for r in data['transformation_results']:
    run_id = r['run_id']
    final_dist = r['final_distance']
    trans_applied = len(r.get('transformations_applied', []))
    needed = r.get('transformation_needed', False)
    success = r.get('transformation_success', False)
    
    status = "✓ MATCH" if final_dist == 0.0 else f"✗ dist={final_dist:.3f}"
    trans_info = f"{trans_applied} transforms" if trans_applied > 0 else "NO transforms"
    
    print(f"Run {run_id}: {status} | {trans_info} | needed={needed}, success={success}")
    
    if trans_applied > 0:
        print(f"  Transformations: {r['transformations_applied']}")
