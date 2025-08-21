# src/experiment_runner.py

from typing import Dict, Any, List
import json
from pathlib import Path
from collections import Counter

from test_config import TestConfiguration, TestMode, EnvironmentConfig
from test_prompts import TestPromptGenerator, AlgorithmPrompt
from test_executor import TestExecutor
from llm_client import LLMClient

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
                repeatability = self._calculate_repeatability(mode_results)
                print(f"\n      Mode {mode_config.mode.value} Results: {repeatability:.2f} repeatability ({num_runs} runs)")
                
                results["results"].append({
                    "family": prompt.family,
                    "variant": prompt.variant,
                    "mode": mode_config.mode.value,
                    "runs": mode_results,
                    "repeatability_score": repeatability
                })
        
        # Save results
        self._save_experiment_results(results)
        return results
    
    def _calculate_repeatability(self, results: List[Dict[str, Any]]) -> float:
        """Calculate repeatability score for a set of results"""
        if len(results) < 2:
            return 1.0
        
        final_outputs = [r["final_output"] for r in results]
        
        # Normalize outputs for comparison
        normalized_outputs = []
        for output in final_outputs:
            # Remove whitespace and comments for comparison
            normalized = output.strip().replace(" ", "").replace("\n", "")
            normalized_outputs.append(normalized)
        
        # Count identical outputs
        unique_outputs = set(normalized_outputs)
        if len(unique_outputs) == 1:
            return 1.0
        
        # Find most common output
        counter = Counter(normalized_outputs)
        most_common_count = counter.most_common(1)[0][1]
        
        return most_common_count / len(results)
    
    def _save_experiment_results(self, results: Dict[str, Any]):
        """Save complete experiment results"""
        results_file = self.output_dir / "ablation_study_results.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Experiment results saved to: {results_file}")

def run_experiment(num_runs: int = 2, selected_families: List[str] = None) -> Dict[str, Any]:
    """Factory function to run experiment with default LLM client"""
    llm_client = LLMClient()  # Uses default configuration
    runner = ExperimentRunner(llm_client)
    return runner.run_full_experiment(num_runs, selected_families)
