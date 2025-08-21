#!/usr/bin/env python3
"""
Main test runner for SKYT repeatability evaluation
Executes the complete A/B/C test matrix with statistical analysis and reporting
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from test_executor import TestExecutor, run_smoke_test
from test_config import EnvironmentConfig, TestConfiguration
from statistical_analysis import analyze_repeatability_by_config, compare_configurations
from repeatability_metrics import generate_repeatability_report
from llm_client import LLMClient

def main():
    parser = argparse.ArgumentParser(description='Run SKYT repeatability test suite')
    parser.add_argument('--mode', choices=['smoke', 'minimal', 'full'], default='smoke',
                       help='Test mode: smoke (300 runs), minimal (1800 runs), full (3000 runs)')
    parser.add_argument('--api-key', required=True, help='OpenAI API key')
    parser.add_argument('--model', default='gpt-4o-mini', help='Model identifier')
    parser.add_argument('--output-dir', default='test_results', help='Output directory')
    parser.add_argument('--temperatures', nargs='+', type=float, default=[0.0, 0.3],
                       help='Temperature values to test')
    
    args = parser.parse_args()
    
    # Set up test parameters based on mode
    runs_per_cell = {
        'smoke': 10,
        'minimal': 30,
        'full': 50
    }[args.mode]
    
    print(f"🧪 Starting SKYT repeatability test suite in {args.mode} mode")
    print(f"📊 {runs_per_cell} runs per cell, temperatures: {args.temperatures}")
    print(f"🎯 Total expected runs: {10 * len(args.temperatures) * 3 * runs_per_cell}")
    
    # Initialize LLM client
    llm_client = LLMClient(args.api_key, provider="openai")
    
    # Create test executor
    executor = TestExecutor(results_dir=args.output_dir)
    
    # Update executor to use LLM client
    executor.llm_client = llm_client
    
    # Create test matrix
    test_runs = executor.create_test_matrix(
        temperatures=args.temperatures,
        runs_per_cell=runs_per_cell
    )
    
    print(f"📋 Created test matrix with {len(test_runs)} runs")
    
    # Execute tests
    results = []
    start_time = time.time()
    
    for i, test_run in enumerate(test_runs):
        print(f"⚡ Executing run {i+1}/{len(test_runs)}: {test_run.run_id}")
        
        try:
            result = executor.execute_single_run(test_run)
            results.append(result)
            
            # Progress update every 50 runs
            if (i + 1) % 50 == 0:
                elapsed = time.time() - start_time
                success_rate = sum(1 for r in results if r.success) / len(results)
                print(f"📈 Progress: {i+1}/{len(test_runs)} ({success_rate:.1%} success rate, {elapsed:.1f}s elapsed)")
                
        except Exception as e:
            print(f"❌ Error in run {test_run.run_id}: {str(e)}")
            continue
    
    total_time = time.time() - start_time
    print(f"✅ Test execution completed in {total_time:.1f}s")
    
    # Statistical analysis
    print("📊 Performing statistical analysis...")
    
    # Convert results to format expected by analysis functions
    analysis_results = []
    for result in results:
        analysis_results.append({
            'success': result.success,
            'audit_trail': result.audit_trail,
            'execution_time': result.execution_time,
            'run_id': result.run_id
        })
    
    # Analyze by configuration
    config_analysis = analyze_repeatability_by_config(analysis_results)
    
    # Generate repeatability report
    repeatability_report = generate_repeatability_report(args.output_dir)
    
    # Save comprehensive results
    final_report = {
        'test_metadata': {
            'mode': args.mode,
            'model': args.model,
            'temperatures': args.temperatures,
            'runs_per_cell': runs_per_cell,
            'total_runs': len(results),
            'execution_time': total_time,
            'timestamp': time.time()
        },
        'configuration_analysis': config_analysis,
        'repeatability_report': repeatability_report,
        'raw_results': [r.__dict__ for r in results]
    }
    
    # Save final report
    report_file = os.path.join(args.output_dir, f"final_report_{args.mode}_{int(time.time())}.json")
    with open(report_file, 'w') as f:
        json.dump(final_report, f, indent=2, default=str)
    
    print(f"📄 Final report saved to: {report_file}")
    
    # Print summary
    print("\n" + "="*60)
    print("🎯 TEST SUMMARY")
    print("="*60)
    
    overall_success = sum(1 for r in results if r.success) / len(results) if results else 0
    print(f"Overall success rate: {overall_success:.1%}")
    
    for config, analysis in config_analysis.items():
        print(f"\nConfiguration {config}:")
        print(f"  Success rate: {analysis['success_rate'].proportion:.1%} "
              f"[{analysis['success_rate'].lower_ci:.1%}, {analysis['success_rate'].upper_ci:.1%}]")
        print(f"  Determinism compliance: {analysis['determinism_compliance_rate'].proportion:.1%}")
        if config == 'C':
            print(f"  Cache rescue rate: {analysis['cache_rescue_rate'].proportion:.1%}")
    
    # Configuration comparisons
    if 'A' in config_analysis and 'B' in config_analysis:
        a_results = [r for r in analysis_results if r['audit_trail'].get('config_mode') == 'A']
        b_results = [r for r in analysis_results if r['audit_trail'].get('config_mode') == 'B']
        comparison = compare_configurations(a_results, b_results)
        
        print(f"\n📈 A vs B Comparison:")
        print(f"  Success rate improvement: {comparison['success_rate'].effect_size:+.1f} pp "
              f"(p={comparison['success_rate'].p_value:.3f})")
    
    print(f"\n🎉 Test suite completed successfully!")
    print(f"📁 Results saved in: {args.output_dir}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
