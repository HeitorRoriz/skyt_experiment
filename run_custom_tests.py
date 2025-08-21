#!/usr/bin/env python3
"""
Runner for custom test executor
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from test_executor import TestExecutor
from llm_client import LLMClient

def main():
    # Set up your OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Please set OPENAI_API_KEY environment variable")
        return 1
    
    # Initialize LLM client
    llm_client = LLMClient(api_key, provider="openai")
    
    # Create test executor
    executor = TestExecutor(llm_client, output_dir="test_results")
    
    print("🧪 Starting A/B/C ablation study...")
    
    # Run experiment with 5 runs per prompt/mode combination
    results = executor.run_full_experiment(num_runs=5)
    
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
