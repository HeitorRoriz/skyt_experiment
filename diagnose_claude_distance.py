#!/usr/bin/env python3
"""
Diagnose why Claude transformations all result in exactly 0.2083 distance.
"""

import json
import glob
from src.foundational_properties import FoundationalProperties

def main():
    print("="*80)
    print("CLAUDE DISTANCE DIAGNOSIS")
    print("="*80)
    
    # Get a Claude experiment
    files = sorted(glob.glob('outputs/is_prime_strict_temp*.json'))
    
    claude_file = None
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if data.get('model') == 'claude-sonnet-4-5-20250929':
                    claude_file = f
                    break
        except:
            pass
    
    if not claude_file:
        print("No Claude experiment found!")
        return
    
    print(f"\nAnalyzing: {claude_file}")
    
    with open(claude_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    canon_data = data.get('canon_data', {})
    canon_code = canon_data.get('code', '')
    
    print(f"\n## Canon Code:")
    print(canon_code)
    
    # Get a failed transformation
    trans_results = data.get('transformation_results', [])
    failed_trans = [t for t in trans_results if not t.get('transformation_success', False)]
    
    if not failed_trans:
        print("\nNo failed transformations found!")
        return
    
    sample = failed_trans[0]
    transformed_code = sample.get('transformed_code', '')
    
    print(f"\n## Transformed Code (Failed):")
    print(transformed_code)
    
    print(f"\n## Distance: {sample.get('final_distance', 'N/A')}")
    
    # Calculate properties to see differences
    props_extractor = FoundationalProperties()
    
    canon_props = props_extractor.extract_all_properties(canon_code)
    trans_props = props_extractor.extract_all_properties(transformed_code)
    
    print(f"\n## Property-by-Property Comparison:")
    
    total_distance = 0
    property_distances = []
    
    for prop_name in canon_props.keys():
        if prop_name in trans_props:
            canon_val = canon_props[prop_name]
            trans_val = trans_props[prop_name]
            
            # Calculate distance for this property
            if isinstance(canon_val, (int, float)) and isinstance(trans_val, (int, float)):
                dist = abs(canon_val - trans_val)
            elif canon_val == trans_val:
                dist = 0.0
            else:
                dist = 1.0
            
            if dist > 0:
                property_distances.append((prop_name, dist, canon_val, trans_val))
                total_distance += dist
    
    print(f"\nProperties with differences:")
    for prop_name, dist, canon_val, trans_val in sorted(property_distances, key=lambda x: -x[1]):
        print(f"\n  {prop_name}:")
        print(f"    Distance: {dist}")
        print(f"    Canon: {canon_val}")
        print(f"    Transformed: {trans_val}")
    
    print(f"\n## Total Distance: {total_distance}")
    print(f"## Normalized Distance: {total_distance / len(canon_props) if canon_props else 0:.4f}")
    
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    
    if property_distances:
        print(f"\nThe 0.2083 distance is caused by {len(property_distances)} property differences.")
        print("These are likely minor differences that don't affect correctness.")
        print("\nOptions:")
        print("1. Increase success threshold from 0.1 to 0.3")
        print("2. Adjust property comparison to be more lenient")
        print("3. Fix specific property differences identified above")

if __name__ == "__main__":
    main()
