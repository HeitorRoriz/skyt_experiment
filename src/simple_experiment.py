# src/simple_experiment.py
"""
Simplified Experiment Runner for SKYT
Generates LLM outputs and calculates R_raw and R_canon metrics
"""

import os
import json
import time
from typing import List, Dict, Any
from openai import OpenAI

from metrics import calculate_repeatability_metrics, print_metrics_summary, RepeatabilityResult
from simple_canonicalizer import canonicalize_code


class SimpleExperiment:
    """Minimal experiment runner for repeatability testing"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo", temperature: float = 0.0):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.temperature = temperature
    
    def run_prompt_experiment(self, prompt: str, num_runs: int = 50, expected_function: str = "fibonacci") -> RepeatabilityResult:
        """
        Run experiment for a single prompt
        
        Args:
            prompt: The prompt to test
            num_runs: Number of runs to execute
            expected_function: Expected function name for canonicalization
        
        Returns:
            RepeatabilityResult with R_raw and R_canon metrics
        """
        print(f"Running experiment: {num_runs} runs at temperature {self.temperature}")
        print(f"Prompt: {prompt[:100]}...")
        
        raw_outputs = []
        canonical_outputs = []
        
        for run in range(num_runs):
            print(f"Run {run + 1}/{num_runs}", end="\r")
            
            try:
                # Get LLM response
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    max_tokens=500
                )
                
                raw_output = response.choices[0].message.content.strip()
                raw_outputs.append(raw_output)
                
                # Canonicalize the output
                canonical_output = canonicalize_code(raw_output, expected_function)
                canonical_outputs.append(canonical_output)
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"\nError in run {run + 1}: {e}")
                # Add empty outputs for failed runs
                raw_outputs.append("")
                canonical_outputs.append("")
        
        print(f"\nCompleted {num_runs} runs")
        
        # Calculate metrics
        return calculate_repeatability_metrics(raw_outputs, canonical_outputs)
    
    def run_temperature_comparison(self, prompt: str, temperatures: List[float] = [0.0, 0.3], 
                                 num_runs: int = 50, expected_function: str = "fibonacci") -> Dict[float, RepeatabilityResult]:
        """
        Run experiment across multiple temperatures
        
        Args:
            prompt: The prompt to test
            temperatures: List of temperatures to test
            num_runs: Number of runs per temperature
            expected_function: Expected function name
        
        Returns:
            Dictionary mapping temperature to RepeatabilityResult
        """
        results = {}
        
        for temp in temperatures:
            print(f"\n{'='*60}")
            print(f"TEMPERATURE: {temp}")
            print(f"{'='*60}")
            
            # Update temperature
            original_temp = self.temperature
            self.temperature = temp
            
            # Run experiment
            result = self.run_prompt_experiment(prompt, num_runs, expected_function)
            results[temp] = result
            
            # Print results
            print_metrics_summary(result, f"T={temp}")
            
            # Restore original temperature
            self.temperature = original_temp
        
        return results
    
    def save_results(self, results: Dict[float, RepeatabilityResult], output_file: str):
        """Save experiment results to JSON file"""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Convert results to serializable format
        serializable_results = {}
        for temp, result in results.items():
            serializable_results[str(temp)] = {
                "total_runs": result.total_runs,
                "r_raw": result.r_raw,
                "r_canon": result.r_canon,
                "raw_distribution": result.raw_distribution,
                "canon_distribution": result.canon_distribution
            }
        
        with open(output_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"\nResults saved to: {output_file}")


def run_fibonacci_experiment():
    """Run the standard Fibonacci experiment"""
    
    # Standard Fibonacci prompt
    prompt = "Write a Python function called fibonacci that takes an integer n and returns the nth Fibonacci number."
    
    # Initialize experiment
    experiment = SimpleExperiment(temperature=0.0)
    
    # Run temperature comparison
    results = experiment.run_temperature_comparison(
        prompt=prompt,
        temperatures=[0.0, 0.3],
        num_runs=50,
        expected_function="fibonacci"
    )
    
    # Save results
    experiment.save_results(results, "outputs/fibonacci_experiment.json")
    
    # Print summary
    print(f"\n{'='*60}")
    print("EXPERIMENT SUMMARY")
    print(f"{'='*60}")
    
    for temp, result in results.items():
        print(f"\nTemperature {temp}:")
        print(f"  R_raw:   {result.r_raw:.3f}")
        print(f"  R_canon: {result.r_canon:.3f}")
        print(f"  Improvement: {result.r_canon - result.r_raw:+.3f}")


if __name__ == "__main__":
    run_fibonacci_experiment()
