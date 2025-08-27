# src/run_experiment.py
"""
Orchestrator to run prompts × runs, log results, and compute summary metrics
"""

import os
from typing import List, Dict
from dataclasses import dataclass

from .config import NUM_RUNS, RESULTS_DIR, DEFAULT_MODEL, DEFAULT_TEMPERATURE
from .experiment import LLMClient
from .contract_checker import create_fibonacci_checker, ContractResult
from .log import ExperimentLogger
from .metrics import calculate_metrics, MetricsResult


@dataclass
class ExperimentConfig:
    """Configuration for a single experiment"""
    prompt_id: str
    prompt: str
    model: str = DEFAULT_MODEL
    temperature: float = DEFAULT_TEMPERATURE
    num_runs: int = NUM_RUNS


class ExperimentRunner:
    """Main experiment orchestrator"""
    
    def __init__(self, results_dir: str = RESULTS_DIR):
        """
        Initialize experiment runner
        
        Args:
            results_dir: Directory to store results
        """
        self.results_dir = results_dir
        self.logger = ExperimentLogger(os.path.join(results_dir, "experiment_log.csv"))
        self.contract_checker = create_fibonacci_checker()
        
        # Ensure results directory exists
        os.makedirs(results_dir, exist_ok=True)
    
    def run_single_experiment(self, config: ExperimentConfig) -> MetricsResult:
        """
        Run a single experiment (multiple runs of the same prompt)
        
        Args:
            config: Experiment configuration
            
        Returns:
            MetricsResult with calculated metrics
        """
        print(f"Running experiment: {config.prompt_id}")
        print(f"Prompt: {config.prompt}")
        print(f"Model: {config.model}, Temperature: {config.temperature}, Runs: {config.num_runs}")
        
        # Initialize LLM client
        llm_client = LLMClient(model=config.model, temperature=config.temperature)
        
        # Storage for results
        raw_outputs = []
        canonical_outputs = []
        contract_passes = []
        contract_results = []
        
        # Run multiple iterations
        for run_id in range(1, config.num_runs + 1):
            print(f"  Run {run_id}/{config.num_runs}...", end=" ")
            
            try:
                # Generate code
                raw_code = llm_client.generate_code(config.prompt)
                raw_outputs.append(raw_code)
                
                # Check contract
                contract_result = self.contract_checker.check_contract(raw_code)
                contract_results.append(contract_result)
                
                # Store canonical output and contract pass status
                canonical_outputs.append(contract_result.canonical_code)
                contract_passes.append(contract_result.contract_pass)
                
                # Log the run
                self.logger.log_run(
                    prompt_id=config.prompt_id,
                    run_id=run_id,
                    model=config.model,
                    temperature=config.temperature,
                    raw_code=raw_code,
                    contract_result=contract_result
                )
                
                # Print status
                status = "[OK]" if contract_result.contract_pass else "[FAIL]"
                print(f"{status}")
                
            except Exception as e:
                print(f"ERROR: {str(e)}")
                # Log failed run
                failed_result = ContractResult(
                    passed=False,
                    canonical_code=None,
                    canonical_signature=None,
                    determinism_violations=[],
                    structural_ok=False,
                    canonicalization_ok=False,
                    oracle_result=None,
                    oracle_output=None,
                    contract_pass=False,
                    error_message=f"LLM call failed: {str(e)}"
                )
                
                raw_outputs.append("")  # Empty output for failed run
                canonical_outputs.append(None)
                contract_passes.append(False)
                contract_results.append(failed_result)
                
                self.logger.log_run(
                    prompt_id=config.prompt_id,
                    run_id=run_id,
                    model=config.model,
                    temperature=config.temperature,
                    raw_code="",
                    contract_result=failed_result
                )
        
        # Calculate metrics
        metrics = calculate_metrics(raw_outputs, canonical_outputs, contract_passes)
        
        print(f"Results: R_raw={metrics.r_raw:.3f}, R_canon={metrics.r_canon:.3f}, "
              f"Coverage={metrics.canon_coverage:.3f}, Delta={metrics.rescue_delta:.3f}")
        
        return metrics
    
    def run_multiple_experiments(self, configs: List[ExperimentConfig]) -> Dict[str, MetricsResult]:
        """
        Run multiple experiments
        
        Args:
            configs: List of experiment configurations
            
        Returns:
            Dictionary mapping prompt_id to MetricsResult
        """
        results = {}
        
        print(f"Running {len(configs)} experiments...")
        print("=" * 60)
        
        for i, config in enumerate(configs, 1):
            print(f"\nExperiment {i}/{len(configs)}")
            results[config.prompt_id] = self.run_single_experiment(config)
        
        print("\n" + "=" * 60)
        print("All experiments completed!")
        
        return results


def create_fibonacci_experiments() -> List[ExperimentConfig]:
    """Create standard fibonacci experiments"""
    return [
        ExperimentConfig(
            prompt_id="fib_basic",
            prompt="Write a Python function to generate the first 20 Fibonacci numbers."
        ),
        ExperimentConfig(
            prompt_id="fib_recursive", 
            prompt="Write a Python function that returns the first 20 Fibonacci numbers using recursion."
        ),
        ExperimentConfig(
            prompt_id="fib_list",
            prompt="Generate Python code to compute the first 20 Fibonacci numbers and return them as a list."
        ),
        ExperimentConfig(
            prompt_id="fib_named",
            prompt="Create a Python function named fibonacci that outputs the first 20 Fibonacci numbers."
        ),
        ExperimentConfig(
            prompt_id="fib_recursive2",
            prompt="Implement a recursive Python function to produce the first 20 Fibonacci numbers."
        )
    ]


def main():
    """Main entry point for running experiments"""
    # Create experiment runner
    runner = ExperimentRunner()
    
    # Create standard fibonacci experiments
    experiments = create_fibonacci_experiments()
    
    # Run all experiments
    results = runner.run_multiple_experiments(experiments)
    
    # Print summary
    print("\nFINAL SUMMARY:")
    print("-" * 60)
    for prompt_id, metrics in results.items():
        print(f"{prompt_id:15} | R_raw: {metrics.r_raw:.3f} | R_canon: {metrics.r_canon:.3f} | "
              f"Coverage: {metrics.canon_coverage:.3f} | Delta: {metrics.rescue_delta:.3f}")


if __name__ == "__main__":
    main()
