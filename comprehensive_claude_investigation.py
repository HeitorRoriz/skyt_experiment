#!/usr/bin/env python3
"""
Comprehensive investigation of Claude transformation failures.
Analyzes all 15 Claude experiments to understand why transformations fail.
"""

import json
import glob
from collections import defaultdict

def analyze_claude_experiments():
    """Analyze all Claude experiment files"""
    
    # Find all Claude experiment files
    files = sorted(glob.glob('outputs/*_strict_temp*.json'))
    
    claude_files = []
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if data.get('model') == 'claude-sonnet-4-5-20250929':
                    claude_files.append(f)
        except:
            pass
    
    print("=" * 80)
    print(f"COMPREHENSIVE CLAUDE TRANSFORMATION FAILURE ANALYSIS")
    print("=" * 80)
    print(f"Found {len(claude_files)} Claude experiment files\n")
    
    # Aggregate statistics
    total_transformations = 0
    successful_transformations = 0
    failed_transformations = 0
    transformation_needed_count = 0
    
    distance_distribution = []
    transformers_applied = defaultdict(int)
    
    # Analyze each experiment
    for idx, filepath in enumerate(claude_files, 1):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        contract_id = data.get('contract_id')
        temp = data.get('temperature')
        
        print(f"\n{'='*80}")
        print(f"Experiment {idx}/{len(claude_files)}: {contract_id} @ temp {temp}")
        print(f"{'='*80}")
        
        # Check canon
        canon_created = data.get('canon_created')
        canon_data = data.get('canon_data')
        
        print(f"Canon created: {canon_created}")
        if canon_data:
            print(f"Canon code length: {len(canon_data.get('code', ''))}")
        
        # Analyze transformations
        trans_results = data.get('transformation_results', [])
        print(f"\nTransformation results: {len(trans_results)} outputs")
        
        success_count = 0
        fail_count = 0
        needed_count = 0
        distances = []
        
        for t in trans_results:
            total_transformations += 1
            
            needed = t.get('transformation_needed', False)
            success = t.get('transformation_success', False)
            distance = t.get('final_distance', 0)
            applied = t.get('transformations_applied', [])
            
            if needed:
                needed_count += 1
                transformation_needed_count += 1
            
            if success:
                success_count += 1
                successful_transformations += 1
            else:
                fail_count += 1
                failed_transformations += 1
            
            distances.append(distance)
            
            for transformer in applied:
                transformers_applied[transformer] += 1
        
        distance_distribution.extend(distances)
        
        print(f"  Transformation needed: {needed_count}/{len(trans_results)}")
        print(f"  Successful: {success_count}/{len(trans_results)}")
        print(f"  Failed: {fail_count}/{len(trans_results)}")
        print(f"  Avg distance: {sum(distances)/len(distances):.4f}")
        print(f"  Min distance: {min(distances):.4f}")
        print(f"  Max distance: {max(distances):.4f}")
        
        # Check metrics
        metrics = data.get('metrics', {})
        print(f"\nMetrics:")
        print(f"  R_raw: {metrics.get('R_raw', 'N/A')}")
        print(f"  R_anchor_pre: {metrics.get('R_anchor_pre', 'N/A')}")
        print(f"  R_anchor_post: {metrics.get('R_anchor_post', 'N/A')}")
        print(f"  Delta_rescue: {metrics.get('Delta_rescue', 'N/A')}")
    
    # Overall summary
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)
    print(f"Total transformations attempted: {total_transformations}")
    print(f"Transformation needed: {transformation_needed_count} ({100*transformation_needed_count/total_transformations:.1f}%)")
    print(f"Successful: {successful_transformations} ({100*successful_transformations/total_transformations:.1f}%)")
    print(f"Failed: {failed_transformations} ({100*failed_transformations/total_transformations:.1f}%)")
    
    print(f"\nDistance distribution:")
    print(f"  Mean: {sum(distance_distribution)/len(distance_distribution):.4f}")
    print(f"  Min: {min(distance_distribution):.4f}")
    print(f"  Max: {max(distance_distribution):.4f}")
    print(f"  Zero distances: {sum(1 for d in distance_distribution if d == 0)}")
    
    print(f"\nTransformers applied (frequency):")
    for transformer, count in sorted(transformers_applied.items(), key=lambda x: x[1], reverse=True):
        print(f"  {transformer}: {count}")
    
    return claude_files

def compare_claude_vs_openai_code():
    """Compare code structure between Claude and OpenAI outputs"""
    
    print("\n" + "=" * 80)
    print("CLAUDE VS OPENAI CODE COMPARISON")
    print("=" * 80)
    
    # Get one example from each model for is_prime_strict
    files = glob.glob('outputs/is_prime_strict_temp1.0_*.json')
    
    claude_example = None
    openai_example = None
    
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
                model = data.get('model')
                
                if model == 'claude-sonnet-4-5-20250929' and not claude_example:
                    claude_example = data
                elif model in ['gpt-4o-mini', 'gpt-4o'] and not openai_example:
                    openai_example = data
                
                if claude_example and openai_example:
                    break
        except:
            pass
    
    if not claude_example or not openai_example:
        print("Could not find examples for comparison")
        return
    
    print("\n" + "-" * 80)
    print("CLAUDE OUTPUT (first raw output):")
    print("-" * 80)
    claude_code = claude_example.get('raw_outputs', [''])[0]
    print(claude_code[:500])
    
    print("\n" + "-" * 80)
    print("OPENAI OUTPUT (first raw output):")
    print("-" * 80)
    openai_code = openai_example.get('raw_outputs', [''])[0]
    print(openai_code[:500])
    
    print("\n" + "-" * 80)
    print("CLAUDE CANON:")
    print("-" * 80)
    claude_canon = claude_example.get('canon_data', {}).get('code', '')
    print(claude_canon[:500])
    
    print("\n" + "-" * 80)
    print("OPENAI CANON:")
    print("-" * 80)
    openai_canon = openai_example.get('canon_data', {}).get('code', '')
    print(openai_canon[:500])
    
    # Compare transformation results
    print("\n" + "-" * 80)
    print("TRANSFORMATION SUCCESS RATES:")
    print("-" * 80)
    
    claude_trans = claude_example.get('transformation_results', [])
    openai_trans = openai_example.get('transformation_results', [])
    
    claude_success = sum(1 for t in claude_trans if t.get('transformation_success', False))
    openai_success = sum(1 for t in openai_trans if t.get('transformation_success', False))
    
    print(f"Claude: {claude_success}/{len(claude_trans)} successful")
    print(f"OpenAI: {openai_success}/{len(openai_trans)} successful")
    
    # Check what transformers were applied
    print("\n" + "-" * 80)
    print("TRANSFORMERS APPLIED:")
    print("-" * 80)
    
    claude_transformers = set()
    for t in claude_trans:
        claude_transformers.update(t.get('transformations_applied', []))
    
    openai_transformers = set()
    for t in openai_trans:
        openai_transformers.update(t.get('transformations_applied', []))
    
    print(f"Claude: {claude_transformers}")
    print(f"OpenAI: {openai_transformers}")

def analyze_transformation_pipeline():
    """Analyze what's happening in the transformation pipeline"""
    
    print("\n" + "=" * 80)
    print("TRANSFORMATION PIPELINE ANALYSIS")
    print("=" * 80)
    
    # Get a Claude experiment with detailed transformation data
    claude_file = sorted(glob.glob('outputs/*_strict_temp*.json'))[-1]
    
    with open(claude_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if data.get('model') != 'claude-sonnet-4-5-20250929':
        print("Latest file is not Claude, skipping detailed analysis")
        return
    
    print(f"\nAnalyzing: {claude_file}")
    print(f"Contract: {data.get('contract_id')}")
    print(f"Temperature: {data.get('temperature')}")
    
    # Look at first failed transformation in detail
    trans_results = data.get('transformation_results', [])
    
    print(f"\n" + "-" * 80)
    print("DETAILED ANALYSIS OF FIRST TRANSFORMATION:")
    print("-" * 80)
    
    if trans_results:
        first = trans_results[0]
        
        print(f"Transformation needed: {first.get('transformation_needed')}")
        print(f"Transformation success: {first.get('transformation_success')}")
        print(f"Final distance: {first.get('final_distance')}")
        print(f"Transformations applied: {first.get('transformations_applied')}")
        
        print(f"\nOriginal code (first 300 chars):")
        print(first.get('original_code', '')[:300])
        
        print(f"\nTransformed code (first 300 chars):")
        print(first.get('transformed_code', '')[:300])
        
        print(f"\nCanon code (first 300 chars):")
        canon_code = data.get('canon_data', {}).get('code', '')
        print(canon_code[:300])
        
        # Check if codes are identical
        original = first.get('original_code', '')
        transformed = first.get('transformed_code', '')
        
        print(f"\n" + "-" * 80)
        print("CODE COMPARISON:")
        print("-" * 80)
        print(f"Original == Transformed: {original == transformed}")
        print(f"Original == Canon: {original == canon_code}")
        print(f"Transformed == Canon: {transformed == canon_code}")
        
        # Character-level diff
        if original != transformed:
            print(f"\nChanges made by transformation:")
            print(f"  Original length: {len(original)}")
            print(f"  Transformed length: {len(transformed)}")
            print(f"  Length diff: {len(transformed) - len(original)}")

if __name__ == "__main__":
    # Run all analyses
    claude_files = analyze_claude_experiments()
    compare_claude_vs_openai_code()
    analyze_transformation_pipeline()
    
    print("\n" + "=" * 80)
    print("INVESTIGATION COMPLETE")
    print("=" * 80)
