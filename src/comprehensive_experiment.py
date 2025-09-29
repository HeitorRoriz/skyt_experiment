# src/comprehensive_experiment.py
"""
Comprehensive SKYT experiment runner
Implements the complete pipeline: contracts → LLM → canon → transform → metrics → analysis
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from .contract import Contract
from .llm_client import LLMClient
from .canon_system import CanonSystem
from .oracle_system import OracleSystem
from .code_transformer import CodeTransformer
from .metrics import ComprehensiveMetrics
from .bell_curve_analysis import BellCurveAnalyzer
from .config import TARGET_RUNS_PER_PROMPT, OUTPUTS_DIR


class ComprehensiveExperiment:
    """
    Complete SKYT experiment pipeline implementation
    """
    
    def __init__(self, output_dir: str = OUTPUTS_DIR):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize all systems
        self.llm_client = LLMClient()
        self.canon_system = CanonSystem(os.path.join(output_dir, "canon"))
        self.oracle_system = OracleSystem()
        self.code_transformer = CodeTransformer(self.canon_system)
        self.metrics_calculator = ComprehensiveMetrics(self.canon_system)
        self.bell_curve_analyzer = BellCurveAnalyzer(os.path.join(output_dir, "analysis"))
        
        print("🚀 SKYT Comprehensive Experiment System Initialized")
        print("📋 Components: Contract → LLM → Canon → Transform → Metrics → Analysis")
    
    def run_full_experiment(self, contract_template_path: str, contract_id: str,
                          num_runs: int = TARGET_RUNS_PER_PROMPT,
                          temperature: float = 0.0) -> Dict[str, Any]:
        """
        Run complete SKYT experiment pipeline
        
        Args:
            contract_template_path: Path to contract templates JSON
            contract_id: Contract identifier to use
            num_runs: Number of LLM runs to execute
            temperature: LLM sampling temperature
            
        Returns:
            Complete experiment results
        """
        print(f"\n🔬 Starting Full SKYT Experiment")
        print(f"📄 Contract: {contract_id}")
        print(f"🎯 Runs: {num_runs}, Temperature: {temperature}")
        
        # Step 1: Load contract from template
        print("\n📋 Step 1: Loading Contract...")
        try:
            contract = Contract.from_template(contract_template_path, contract_id)
            print(f"✅ Contract loaded: {contract.data['task_intent']}")
        except Exception as e:
            return {"error": f"Failed to load contract: {e}"}
        
        # Step 2: Generate multiple LLM outputs
        print(f"\n🤖 Step 2: Generating {num_runs} LLM outputs...")
        raw_outputs = []
        llm_results = []
        
        for run_idx in range(num_runs):
            print(f"  🔄 Run {run_idx + 1}/{num_runs}...")
            
            try:
                # Generate code with enhanced prompt
                enhanced_prompt = self._enhance_prompt(contract.data["prompt"], contract.data)
                raw_output = self.llm_client.generate_code(enhanced_prompt, temperature)
                
                raw_outputs.append(raw_output)
                llm_results.append({
                    "run_id": run_idx + 1,
                    "raw_output": raw_output,
                    "success": True,
                    "enhanced_prompt": enhanced_prompt
                })
                
            except Exception as e:
                print(f"    ❌ Error in run {run_idx + 1}: {e}")
                llm_results.append({
                    "run_id": run_idx + 1,
                    "raw_output": None,
                    "success": False,
                    "error": str(e)
                })
        
        successful_outputs = [output for output in raw_outputs if output is not None]
        print(f"✅ Generated {len(successful_outputs)}/{num_runs} successful outputs")
        
        if not successful_outputs:
            return {"error": "No successful LLM outputs generated"}
        
        # Step 3: Create canon from first compliant output
        print(f"\n⚓ Step 3: Creating Canon...")
        canon_created = False
        canon_data = None
        
        # Check if canon already exists
        existing_canon = self.canon_system.load_canon(contract_id)
        if existing_canon:
            print("✅ Using existing canon")
            canon_data = existing_canon
            canon_created = True
        else:
            # Find first compliant output to create canon
            for i, code in enumerate(successful_outputs):
                oracle_result = self.oracle_system.run_oracle_tests(code, contract.data)
                
                if oracle_result["passed"]:
                    print(f"✅ Creating canon from run {i + 1} (first compliant output)")
                    canon_data = self.canon_system.create_canon(contract, code)
                    canon_created = True
                    break
                else:
                    print(f"  ❌ Run {i + 1} failed oracle tests")
            
            if not canon_created:
                print("⚠️  No compliant outputs found, using first output as canon")
                canon_data = self.canon_system.create_canon(contract, successful_outputs[0])
                canon_created = True
        
        # Step 4: Transform subsequent outputs to match canon
        print(f"\n🔧 Step 4: Transforming outputs to canon...")
        transformation_results = []
        
        for i, code in enumerate(successful_outputs):
            print(f"  🔄 Transforming output {i + 1}...")
            
            # Compare to canon first
            comparison = self.canon_system.compare_to_canon(contract_id, code)
            
            if comparison["is_identical"]:
                print(f"    ✅ Already matches canon (distance: {comparison['distance']:.3f})")
                transformation_results.append({
                    "run_id": i + 1,
                    "original_code": code,
                    "transformed_code": code,
                    "transformation_needed": False,
                    "final_distance": comparison["distance"]
                })
            else:
                print(f"    🔧 Transforming (distance: {comparison['distance']:.3f})")
                transform_result = self.code_transformer.transform_to_canon(code, contract_id)
                
                transformation_results.append({
                    "run_id": i + 1,
                    "original_code": code,
                    "transformed_code": transform_result["transformed_code"],
                    "transformation_needed": True,
                    "transformation_success": transform_result["success"],
                    "final_distance": transform_result["final_distance"],
                    "transformations_applied": transform_result["transformations_applied"]
                })
                
                if transform_result["success"]:
                    print(f"    ✅ Transformation successful (final distance: {transform_result['final_distance']:.3f})")
                else:
                    print(f"    ⚠️  Transformation incomplete (final distance: {transform_result['final_distance']:.3f})")
        
        # Step 5: Calculate comprehensive metrics
        print(f"\n📊 Step 5: Calculating Three-Tier Metrics...")
        metrics_result = self.metrics_calculator.calculate_three_tier_metrics(
            successful_outputs, contract.data, contract_id
        )
        
        print(f"✅ Metrics calculated:")
        print(f"  📈 R_raw: {metrics_result['R_raw']:.3f}")
        print(f"  🎯 R_behavioral: {metrics_result['R_behavioral']:.3f}")
        print(f"  🏗️  R_structural: {metrics_result['R_structural']:.3f}")
        
        # Step 6: Generate bell curve analysis
        print(f"\n📈 Step 6: Generating Bell Curve Analysis...")
        distance_data = metrics_result.get("distance_variance", {})
        
        if "distances" in distance_data:
            bell_curve_result = self.bell_curve_analyzer.plot_distance_distribution(
                distance_data["distances"], 
                f"{contract_id}_temp{temperature}",
                f"Distance Distribution - {contract_id}"
            )
            print(f"✅ Bell curve plot saved: {bell_curve_result.get('plot_path', 'N/A')}")
        else:
            bell_curve_result = {"error": "No distance data available"}
            print("⚠️  No distance data for bell curve analysis")
        
        # Step 7: Compile comprehensive results
        experiment_result = {
            # Experiment metadata
            "experiment_id": f"{contract_id}_temp{temperature}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "contract_id": contract_id,
            "temperature": temperature,
            "timestamp": datetime.now().isoformat(),
            "num_runs": num_runs,
            "successful_runs": len(successful_outputs),
            
            # Contract and canon
            "contract": contract.to_dict(),
            "canon_data": canon_data,
            "canon_created": canon_created,
            
            # LLM outputs
            "llm_results": llm_results,
            "raw_outputs": successful_outputs,
            
            # Transformations
            "transformation_results": transformation_results,
            
            # Comprehensive metrics
            "metrics": metrics_result,
            
            # Analysis
            "bell_curve_analysis": bell_curve_result,
            
            # Research hypothesis evaluation
            "hypothesis_evaluation": self._evaluate_hypothesis(metrics_result)
        }
        
        # Save complete results
        self._save_experiment_results(experiment_result)
        
        print(f"\n🎉 Experiment Complete!")
        print(f"📁 Results saved to: {self.output_dir}")
        
        return experiment_result
    
    def run_temperature_sweep(self, contract_template_path: str, contract_id: str,
                            temperatures: List[float] = [0.0, 0.5, 1.0]) -> Dict[str, Any]:
        """
        Run experiment across multiple temperatures for comprehensive analysis
        
        Args:
            contract_template_path: Path to contract templates
            contract_id: Contract to test
            temperatures: List of temperatures to test
            
        Returns:
            Comprehensive temperature sweep results
        """
        print(f"\n🌡️  Starting Temperature Sweep Experiment")
        print(f"📄 Contract: {contract_id}")
        print(f"🎯 Temperatures: {temperatures}")
        
        all_results = []
        
        for temp in temperatures:
            print(f"\n{'='*60}")
            print(f"🌡️  Temperature: {temp}")
            print(f"{'='*60}")
            
            result = self.run_full_experiment(
                contract_template_path, contract_id, 
                temperature=temp
            )
            
            if "error" not in result:
                all_results.append(result)
            else:
                print(f"❌ Temperature {temp} failed: {result['error']}")
        
        if not all_results:
            return {"error": "All temperature experiments failed"}
        
        # Aggregate analysis
        print(f"\n📊 Generating Aggregate Analysis...")
        
        # Extract data for comparison
        temp_comparison_data = {}
        all_distances = []
        
        for result in all_results:
            temp = result["temperature"]
            metrics = result["metrics"]
            
            temp_comparison_data[f"T={temp}"] = metrics.get("distance_variance", {}).get("distances", [])
            all_distances.extend(metrics.get("distance_variance", {}).get("distances", []))
        
        # Generate comparison plots
        comparison_result = self.bell_curve_analyzer.compare_distributions(
            temp_comparison_data, 
            f"Temperature Comparison - {contract_id}"
        )
        
        # Create research summary
        research_summary_data = {
            "R_raw_values": [r["metrics"]["R_raw"] for r in all_results],
            "R_behavioral_values": [r["metrics"]["R_behavioral"] for r in all_results],
            "R_structural_values": [r["metrics"]["R_structural"] for r in all_results],
            "all_distances": all_distances
        }
        
        summary_plot_path = self.bell_curve_analyzer.create_research_summary_plot(research_summary_data)
        
        # Compile sweep results
        sweep_result = {
            "sweep_id": f"{contract_id}_sweep_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "contract_id": contract_id,
            "temperatures": temperatures,
            "timestamp": datetime.now().isoformat(),
            "individual_results": all_results,
            "comparison_analysis": comparison_result,
            "research_summary_plot": summary_plot_path,
            "aggregate_metrics": self.metrics_calculator.calculate_aggregate_metrics(
                [r["metrics"] for r in all_results]
            ),
            "final_hypothesis_evaluation": self._evaluate_sweep_hypothesis(all_results)
        }
        
        # Save sweep results
        sweep_path = os.path.join(self.output_dir, f"{sweep_result['sweep_id']}_sweep.json")
        with open(sweep_path, 'w') as f:
            json.dump(sweep_result, f, indent=2)
        
        print(f"\n🎉 Temperature Sweep Complete!")
        print(f"📊 Research summary: {summary_plot_path}")
        print(f"📁 Full results: {sweep_path}")
        
        return sweep_result
    
    def _enhance_prompt(self, base_prompt: str, contract_data: Dict[str, Any]) -> str:
        """Enhance prompt with contract constraints and dual intent"""
        enhanced = base_prompt
        
        # Add function name constraint if specified
        constraints = contract_data.get("constraints", {})
        if "function_name" in constraints:
            enhanced += f"\n\nIMPORTANT: The function must be named '{constraints['function_name']}'."
        
        # Add implementation hints
        if "requires_recursion" in constraints and constraints["requires_recursion"]:
            enhanced += "\nUse a recursive implementation."
        
        # Add output format requirements
        output_format = contract_data.get("output_format", "raw_code")
        if output_format == "raw_code":
            enhanced += "\n\nProvide only the Python code, no explanations or markdown."
        
        return enhanced
    
    def _evaluate_hypothesis(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate research hypothesis based on metrics"""
        r_raw = metrics.get("R_raw", 0.0)
        r_behavioral = metrics.get("R_behavioral", 0.0)
        r_structural = metrics.get("R_structural", 0.0)
        
        behavioral_improvement = r_behavioral - r_raw
        structural_improvement = r_structural - r_raw
        
        # Hypothesis: SKYT improves repeatability
        hypothesis_supported = structural_improvement > 0.1  # 10% improvement threshold
        
        return {
            "hypothesis": "SKYT improves LLM code repeatability through contract-driven canonicalization",
            "supported": hypothesis_supported,
            "evidence": {
                "raw_repeatability": r_raw,
                "behavioral_improvement": behavioral_improvement,
                "structural_improvement": structural_improvement,
                "total_improvement": structural_improvement
            },
            "conclusion": (
                "Hypothesis SUPPORTED: Significant improvement detected" if hypothesis_supported
                else "Hypothesis NOT SUPPORTED: No significant improvement"
            )
        }
    
    def _evaluate_sweep_hypothesis(self, all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate hypothesis across temperature sweep"""
        improvements = []
        
        for result in all_results:
            metrics = result["metrics"]
            improvement = metrics.get("R_structural", 0.0) - metrics.get("R_raw", 0.0)
            improvements.append(improvement)
        
        avg_improvement = sum(improvements) / len(improvements) if improvements else 0.0
        consistent_improvement = all(imp > 0.05 for imp in improvements)  # 5% threshold
        
        return {
            "hypothesis": "SKYT consistently improves repeatability across temperatures",
            "supported": consistent_improvement and avg_improvement > 0.1,
            "evidence": {
                "average_improvement": avg_improvement,
                "improvements_by_temperature": improvements,
                "consistent_improvement": consistent_improvement
            },
            "conclusion": (
                "Hypothesis SUPPORTED: Consistent improvement across temperatures" 
                if consistent_improvement and avg_improvement > 0.1
                else "Hypothesis PARTIALLY SUPPORTED: Some improvement detected"
                if avg_improvement > 0.05
                else "Hypothesis NOT SUPPORTED: No consistent improvement"
            )
        }
    
    def _save_experiment_results(self, result: Dict[str, Any]):
        """Save experiment results to multiple formats"""
        experiment_id = result["experiment_id"]
        
        # Save detailed JSON
        json_path = os.path.join(self.output_dir, f"{experiment_id}.json")
        with open(json_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Save summary CSV
        csv_path = os.path.join(self.output_dir, "experiment_summary.csv")
        
        # Check if CSV exists to write header
        write_header = not os.path.exists(csv_path)
        
        with open(csv_path, 'a') as f:
            if write_header:
                f.write("experiment_id,contract_id,temperature,total_runs,successful_runs,"
                       "R_raw,R_behavioral,R_structural,behavioral_improvement,structural_improvement,"
                       "hypothesis_supported,timestamp\n")
            
            metrics = result["metrics"]
            hypothesis = result["hypothesis_evaluation"]
            
            f.write(f"{experiment_id},{result['contract_id']},{result['temperature']},"
                   f"{result['num_runs']},{result['successful_runs']},"
                   f"{metrics['R_raw']:.3f},{metrics['R_behavioral']:.3f},{metrics['R_structural']:.3f},"
                   f"{metrics.get('behavioral_improvement', 0.0):.3f},"
                   f"{metrics.get('structural_improvement', 0.0):.3f},"
                   f"{hypothesis['supported']},{result['timestamp']}\n")
        
        print(f"💾 Results saved:")
        print(f"  📄 Detailed: {json_path}")
        print(f"  📊 Summary: {csv_path}")
