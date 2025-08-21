#!/usr/bin/env python3
"""
Runner for custom test executor
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from experiment_runner import ExperimentRunner
from llm_client import LLMClient

def main():
    # Set up your OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Please set OPENAI_API_KEY environment variable")
        return 1
    
    # Initialize LLM client
    llm_client = LLMClient(api_key, provider="openai")
    
    # Create experiment runner
    runner = ExperimentRunner(llm_client, output_dir="test_results")
    
    print("Starting A/B/C ablation study...")
    print(f"Test Configuration:")
    print(f"   Model: gpt-4")
    print(f"   Temperature: 0.0")
    print(f"   Top-p: None")
    print(f"   Top-k: None")
    print(f"   Seed: 42")
    print(f"   Selected families: ['merge_sort']")
    print(f"   Runs per test: 2")
    print(f"   Total tests: 12 (2 variants × 3 modes × 2 runs)")
    print("-" * 60)
    
    # Run experiment with 2 runs per prompt/mode combination
    # To test just one algorithm family, use: selected_families=["merge_sort"]
    results = runner.run_full_experiment(num_runs=2, selected_families=["merge_sort"])
    
    print("✅ Experiment completed!")
    print(f"📁 Results saved in: test_results/ablation_study_results.json")
    
    # Print summary
    total_tests = len(results["results"])
    print(f"📊 Total test combinations: {total_tests}")
    
    for result in results["results"]:
        family = result["family"]
        mode = result["mode"]
        repeatability = result["repeatability_score"]
        print(f"  {family} (Mode {mode}): {repeatability:.1%} repeatability")

if __name__ == "__main__":
    sys.exit(main())
