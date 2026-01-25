#!/usr/bin/env python3
"""
SKYT Full Experiment Runner - MSR 2026 Camera-Ready
Runs comprehensive evaluation across 12 contracts, 3 models, 5 temperatures, 20 runs each.

Total generations: 3,600
Estimated time: 7-9 hours
Estimated cost: ~$16

Phase 1 (Pilot): 1 contract × 3 models × 2 temps × 5 runs = 30 calls
Phase 2 (Full): Remaining 3,570 calls
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import traceback

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from llm_client import LLMClient
from contract import Contract
from oracle_system import OracleSystem
from canon_system import CanonSystem
from code_transformer import CodeTransformer
from metrics import MetricsCalculator
from enhanced_stats import (
    compare_repeatability_rigorous,
    format_rigorous_report
)


class ExperimentRunner:
    """Manages full SKYT experiment execution"""
    
    def __init__(self, output_dir: str, phase: str = "pilot"):
        self.output_dir = Path(output_dir)
        self.phase = phase
        self.setup_logging()
        self.setup_directories()
        
        # Experiment configuration
        self.models = [
            "gpt-4o-mini",
            "gpt-4o",
            "claude-3-5-sonnet-20241022"  # Claude Sonnet 4.5
        ]
        
        self.contracts = [
            "fibonacci", "binary_search", "merge_sort", "quick_sort",
            "factorial", "is_palindrome", "is_prime", "gcd",
            "brackets_balanced", "longest_common_subsequence",
            "slugify", "matrix_multiply"
        ]
        
        if phase == "pilot":
            # Phase 1: Pilot with 1 contract
            self.contracts = ["fibonacci"]
            self.temperatures = [0.0, 0.7]
            self.runs_per_config = 5
        else:
            # Phase 2: Full experiment
            self.temperatures = [0.0, 0.3, 0.5, 0.7, 1.0]
            self.runs_per_config = 20
        
        # Tracking
        self.total_calls = len(self.contracts) * len(self.models) * len(self.temperatures) * self.runs_per_config
        self.completed_calls = 0
        self.failed_calls = 0
        self.start_time = None
        
        # Checkpoint
        self.checkpoint_file = self.output_dir / "checkpoint.json"
        self.checkpoint_interval = 100
        
        self.logger.info(f"Initialized {phase} experiment")
        self.logger.info(f"Total calls: {self.total_calls}")
        self.logger.info(f"Models: {', '.join(self.models)}")
        self.logger.info(f"Contracts: {', '.join(self.contracts)}")
        self.logger.info(f"Temperatures: {self.temperatures}")
        self.logger.info(f"Runs per config: {self.runs_per_config}")
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = self.output_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Main log
        log_file = log_dir / "experiment.log"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        
        # Error log
        error_handler = logging.FileHandler(log_dir / "errors.log")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(error_handler)
    
    def setup_directories(self):
        """Create output directory structure"""
        dirs = [
            "raw_outputs",
            "repaired_outputs",
            "metrics/per_contract",
            "metrics/per_model",
            "metrics/aggregate",
            "statistical_analysis",
            "logs"
        ]
        
        for dir_path in dirs:
            (self.output_dir / dir_path).mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Created output directories in {self.output_dir}")
    
    def load_checkpoint(self) -> Dict[str, Any]:
        """Load checkpoint if exists"""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            self.logger.info(f"Loaded checkpoint: {checkpoint['completed_calls']} calls completed")
            return checkpoint
        return {"completed_calls": 0, "completed_configs": []}
    
    def save_checkpoint(self, completed_config: str):
        """Save checkpoint"""
        checkpoint = self.load_checkpoint()
        checkpoint["completed_calls"] = self.completed_calls
        checkpoint["completed_configs"].append(completed_config)
        checkpoint["timestamp"] = datetime.now().isoformat()
        
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
    
    def run_single_generation(
        self,
        contract_id: str,
        model: str,
        temperature: float,
        run_number: int
    ) -> Dict[str, Any]:
        """Run single code generation with full pipeline"""
        
        config_id = f"{contract_id}_{model}_{temperature}_{run_number}"
        
        try:
            # Load contract
            contract = Contract.from_template(contract_id)
            
            # Initialize components
            llm_client = LLMClient(model=model)
            oracle = OracleSystem()
            canon_system = CanonSystem()
            transformer = CodeTransformer()
            
            # Generate code
            self.logger.info(f"Generating: {config_id}")
            prompt = contract.build_prompt()
            raw_code = llm_client.generate_code(prompt, temperature=temperature)
            
            # Save raw output
            raw_dir = self.output_dir / "raw_outputs" / contract_id / model / f"temp_{temperature}"
            raw_dir.mkdir(parents=True, exist_ok=True)
            raw_file = raw_dir / f"run_{run_number:02d}.py"
            raw_file.write_text(raw_code)
            
            # Validate with oracle
            oracle_passed = oracle.validate(raw_code, contract)
            
            # Check contract adherence
            contract_adherent = contract.validate_code(raw_code)
            
            # Transform if needed
            repaired_code = raw_code
            transformation_success = False
            transformations_applied = []
            
            if oracle_passed and contract_adherent:
                # Get or set canonical anchor
                canon_code = canon_system.get_or_set_anchor(contract_id, raw_code)
                
                # Transform towards canonical form
                repaired_code, transform_result = transformer.transform(
                    raw_code,
                    canon_code,
                    contract
                )
                
                transformation_success = transform_result.get("success", False)
                transformations_applied = transform_result.get("transformations", [])
                
                # Save repaired output
                repaired_dir = self.output_dir / "repaired_outputs" / contract_id / model / f"temp_{temperature}"
                repaired_dir.mkdir(parents=True, exist_ok=True)
                repaired_file = repaired_dir / f"run_{run_number:02d}.py"
                repaired_file.write_text(repaired_code)
            
            result = {
                "config_id": config_id,
                "contract_id": contract_id,
                "model": model,
                "temperature": temperature,
                "run_number": run_number,
                "oracle_passed": oracle_passed,
                "contract_adherent": contract_adherent,
                "transformation_success": transformation_success,
                "transformations_applied": transformations_applied,
                "raw_file": str(raw_file.relative_to(self.output_dir)),
                "repaired_file": str(repaired_file.relative_to(self.output_dir)) if oracle_passed and contract_adherent else None,
                "timestamp": datetime.now().isoformat()
            }
            
            self.completed_calls += 1
            return result
            
        except Exception as e:
            self.logger.error(f"Failed: {config_id}")
            self.logger.error(traceback.format_exc())
            self.failed_calls += 1
            
            # Stop on error (Option C)
            raise RuntimeError(f"Experiment halted on error: {config_id}") from e
    
    def run_contract(self, contract_id: str) -> List[Dict[str, Any]]:
        """Run all configurations for a single contract"""
        results = []
        
        for model in self.models:
            for temperature in self.temperatures:
                for run_number in range(1, self.runs_per_config + 1):
                    
                    result = self.run_single_generation(
                        contract_id,
                        model,
                        temperature,
                        run_number
                    )
                    results.append(result)
                    
                    # Checkpoint every 100 calls
                    if self.completed_calls % self.checkpoint_interval == 0:
                        self.save_checkpoint(f"{contract_id}_{model}_{temperature}_{run_number}")
                        self.logger.info(f"Checkpoint saved: {self.completed_calls}/{self.total_calls} calls")
                    
                    # Rate limiting (200ms delay)
                    time.sleep(0.2)
        
        return results
    
    def calculate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate metrics for all results"""
        self.logger.info("Calculating metrics...")
        
        metrics = {
            "per_contract": {},
            "per_model": {},
            "aggregate": {}
        }
        
        # Group by contract
        for contract_id in self.contracts:
            contract_results = [r for r in results if r["contract_id"] == contract_id]
            
            if not contract_results:
                continue
            
            # Calculate success rates
            total = len(contract_results)
            oracle_passed = sum(1 for r in contract_results if r["oracle_passed"])
            contract_adherent = sum(1 for r in contract_results if r["contract_adherent"])
            transformations_success = sum(1 for r in contract_results if r["transformation_success"])
            
            metrics["per_contract"][contract_id] = {
                "total_runs": total,
                "oracle_pass_rate": oracle_passed / total,
                "contract_adherence_rate": contract_adherent / total,
                "transformation_success_rate": transformations_success / total if contract_adherent > 0 else 0
            }
        
        # Group by model
        for model in self.models:
            model_results = [r for r in results if r["model"] == model]
            
            if not model_results:
                continue
            
            total = len(model_results)
            oracle_passed = sum(1 for r in model_results if r["oracle_passed"])
            
            metrics["per_model"][model] = {
                "total_runs": total,
                "oracle_pass_rate": oracle_passed / total
            }
        
        # Aggregate
        metrics["aggregate"] = {
            "total_calls": len(results),
            "successful_calls": self.completed_calls,
            "failed_calls": self.failed_calls,
            "overall_oracle_pass_rate": sum(1 for r in results if r["oracle_passed"]) / len(results)
        }
        
        return metrics
    
    def save_results(self, results: List[Dict[str, Any]], metrics: Dict[str, Any]):
        """Save all results and metrics"""
        
        # Save raw results
        results_file = self.output_dir / "results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        self.logger.info(f"Saved results to {results_file}")
        
        # Save metrics
        metrics_file = self.output_dir / "metrics" / "summary.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        self.logger.info(f"Saved metrics to {metrics_file}")
        
        # Save per-contract metrics
        for contract_id, contract_metrics in metrics["per_contract"].items():
            contract_file = self.output_dir / "metrics" / "per_contract" / f"{contract_id}.json"
            with open(contract_file, 'w') as f:
                json.dump(contract_metrics, f, indent=2)
        
        # Save per-model metrics
        for model, model_metrics in metrics["per_model"].items():
            model_name = model.replace("/", "_").replace(":", "_")
            model_file = self.output_dir / "metrics" / "per_model" / f"{model_name}.json"
            with open(model_file, 'w') as f:
                json.dump(model_metrics, f, indent=2)
        
        # Save aggregate metrics
        aggregate_file = self.output_dir / "metrics" / "aggregate" / "summary.json"
        with open(aggregate_file, 'w') as f:
            json.dump(metrics["aggregate"], f, indent=2)
    
    def run_statistical_analysis(self, results: List[Dict[str, Any]]):
        """Run comprehensive statistical analysis"""
        self.logger.info("Running statistical analysis...")
        
        # This would use enhanced_stats.py for rigorous analysis
        # For now, just create placeholder structure
        
        stats_dir = self.output_dir / "statistical_analysis"
        
        # Placeholder for full implementation
        analysis = {
            "fisher_exact_tests": {},
            "effect_sizes": {},
            "confidence_intervals": {},
            "holm_bonferroni": {},
            "note": "Full statistical analysis to be implemented with actual repeatability data"
        }
        
        with open(stats_dir / "analysis.json", 'w') as f:
            json.dump(analysis, f, indent=2)
        
        self.logger.info(f"Saved statistical analysis to {stats_dir}")
    
    def run(self) -> Dict[str, Any]:
        """Run full experiment"""
        self.start_time = time.time()
        self.logger.info("=" * 80)
        self.logger.info(f"Starting SKYT Experiment - Phase: {self.phase}")
        self.logger.info("=" * 80)
        
        all_results = []
        
        try:
            # Load checkpoint
            checkpoint = self.load_checkpoint()
            completed_configs = set(checkpoint.get("completed_configs", []))
            
            # Run each contract
            for contract_id in self.contracts:
                self.logger.info(f"\n{'='*80}")
                self.logger.info(f"Contract: {contract_id}")
                self.logger.info(f"{'='*80}")
                
                contract_results = self.run_contract(contract_id)
                all_results.extend(contract_results)
                
                self.logger.info(f"Completed {contract_id}: {len(contract_results)} generations")
            
            # Calculate metrics
            metrics = self.calculate_metrics(all_results)
            
            # Save results
            self.save_results(all_results, metrics)
            
            # Run statistical analysis
            self.run_statistical_analysis(all_results)
            
            # Final summary
            elapsed_time = time.time() - self.start_time
            self.logger.info("\n" + "=" * 80)
            self.logger.info("EXPERIMENT COMPLETE")
            self.logger.info("=" * 80)
            self.logger.info(f"Total calls: {self.completed_calls}/{self.total_calls}")
            self.logger.info(f"Failed calls: {self.failed_calls}")
            self.logger.info(f"Elapsed time: {elapsed_time/3600:.2f} hours")
            self.logger.info(f"Results saved to: {self.output_dir}")
            
            return {
                "success": True,
                "total_calls": self.completed_calls,
                "failed_calls": self.failed_calls,
                "elapsed_time": elapsed_time,
                "metrics": metrics
            }
            
        except Exception as e:
            self.logger.error("Experiment failed!")
            self.logger.error(traceback.format_exc())
            
            # Save partial results
            if all_results:
                metrics = self.calculate_metrics(all_results)
                self.save_results(all_results, metrics)
            
            return {
                "success": False,
                "error": str(e),
                "total_calls": self.completed_calls,
                "failed_calls": self.failed_calls
            }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run SKYT full experiment")
    parser.add_argument(
        "--phase",
        choices=["pilot", "full"],
        default="pilot",
        help="Experiment phase (pilot=30 calls, full=3600 calls)"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: outputs/full_experiment_YYYY-MM-DD)"
    )
    
    args = parser.parse_args()
    
    # Create output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = Path("outputs") / f"full_experiment_{timestamp}"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run experiment
    runner = ExperimentRunner(str(output_dir), phase=args.phase)
    result = runner.run()
    
    # Exit code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
