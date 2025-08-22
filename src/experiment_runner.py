# src/experiment_runner.py

from typing import Dict, Any, List
import json
from pathlib import Path
from collections import Counter

from test_config import TestConfiguration, TestMode, EnvironmentConfig
from test_prompts import TestPromptGenerator, AlgorithmPrompt
from test_executor import TestExecutor
from llm_client import LLMClient
from enhanced_repeatability import calculate_enhanced_repeatability, print_repeatability_report

class ExperimentRunner:
    """Orchestrate A/B/C ablation experiments"""
    
    def __init__(self, llm_client: LLMClient, output_dir: str = "test_results"):
        self.llm_client = llm_client
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.prompt_generator = TestPromptGenerator()
        self.test_executor = TestExecutor(llm_client, output_dir)
    
    def run_full_experiment(self, num_runs: int = 5, selected_families: List[str] = None) -> Dict[str, Any]:
        """Run complete A/B/C ablation experiment"""
        
        # Get all prompts, optionally filtered by family
        all_prompts = self.prompt_generator.get_all_prompts()
        if selected_families:
            all_prompts = [p for p in all_prompts if p.family in selected_families]
        
        results = {
            "experiment_config": {
                "num_runs": num_runs,
                "selected_families": selected_families or "all",
                "total_tests": len(all_prompts) * 3 * num_runs  # N prompts × 3 modes × N runs
            },
            "results": []
        }
        
        # Create environment config
        env_config = EnvironmentConfig(
            model_identifier="gpt-4",
            temperature=0.0,
            seed=42
        )
        
        # Test each prompt across all modes
        for prompt in all_prompts:
            print(f"\nTesting Algorithm: {prompt.family} (variant {prompt.variant})")
            print(f"   Expected function: {prompt.expected_function_name}")
            print(f"   Required logic: {prompt.required_logic}")
            
            # Test across all three modes (A, B, C)
            for mode_config in [
                TestConfiguration.create_mode_a(env_config),
                TestConfiguration.create_mode_b(env_config), 
                TestConfiguration.create_mode_c(env_config)
            ]:
                print(f"\n      Mode {mode_config.mode.value}: {mode_config.mode.value}")
                print(f"         Capabilities: {[k for k, v in mode_config.to_dict()['capabilities'].items() if v]}")
                
                # Run multiple times for repeatability analysis
                mode_results = []
                canonical_reference = None
                
                for run in range(num_runs):
                    result = self.test_executor.run_single_test(prompt, mode_config, run + 1, canonical_reference)
                    mode_results.append(result)
                    if canonical_reference is None and 'canonical_reference' in result:
                        canonical_reference = result['canonical_reference']
                
                # Calculate repeatability for this mode
                repeatability_metrics = calculate_enhanced_repeatability(mode_results)
                print_repeatability_report(repeatability_metrics)
                print(f"\n      Mode {mode_config.mode.value} Results: {repeatability_metrics.valid_repeatability:.2f} repeatability ({num_runs} runs)")
                
                results["results"].append({
                    "family": prompt.family,
                    "variant": prompt.variant,
                    "mode": mode_config.mode.value,
                    "runs": mode_results,
                    "repeatability_score": repeatability_metrics.valid_repeatability
                })
        
        # Save results
        self._save_experiment_results(results)
        return results
    
    def _save_experiment_results(self, results: Dict[str, Any]):
        """Save complete experiment results"""
        results_file = self.output_dir / "ablation_study_results.json"
        
        # Convert AcceptanceTestReport objects to dictionaries for JSON serialization
        def convert_for_json(obj):
            if hasattr(obj, '__dict__'):
                # Convert dataclass/object to dict recursively
                result = {}
                for key, value in obj.__dict__.items():
                    result[key] = convert_for_json(value)
                return result
            elif isinstance(obj, list):
                return [convert_for_json(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: convert_for_json(value) for key, value in obj.items()}
            else:
                return obj
        
        serializable_results = convert_for_json(results)
        
        with open(results_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"Experiment results saved to: {results_file}")

def run_experiment(num_runs: int = 2, selected_families: List[str] = None) -> Dict[str, Any]:
    """Factory function to run experiment with default LLM client"""
    llm_client = LLMClient()  # Uses default configuration
    runner = ExperimentRunner(llm_client)
    return runner.run_full_experiment(num_runs, selected_families)
