# main.py
"""
SKYT Comprehensive Experiment System - Main Entry Point
Implements the complete research pipeline for LLM code repeatability analysis
"""

import argparse
import sys
import os
from src.comprehensive_experiment import ComprehensiveExperiment
from src.config import OUTPUTS_DIR


def main():
    """Main entry point for SKYT experiments"""
    
    print("🚀 SKYT: Comprehensive LLM Code Repeatability Experiment System")
    print("=" * 70)
    print("Research Question: Can prompt contracts and SKYT improve LLM-generated code repeatability?")
    print("=" * 70)
    
    parser = argparse.ArgumentParser(
        description="Run comprehensive SKYT repeatability experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run single experiment
  python main.py --contract fibonacci_basic --runs 5 --temperature 0.0
  
  # Run temperature sweep
  python main.py --contract fibonacci_basic --sweep --temperatures 0.0 0.5 1.0
  
  # Run multiple contracts
  python main.py --contract fibonacci_basic fibonacci_recursive --runs 10
        """
    )
    
    parser.add_argument(
        "--contract", 
        nargs="+",
        default=["fibonacci_basic"],
        help="Contract ID(s) to test (default: fibonacci_basic)"
    )
    
    parser.add_argument(
        "--runs",
        type=int,
        default=5,
        help="Number of LLM runs per experiment (default: 5)"
    )
    
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="LLM sampling temperature (default: 0.0)"
    )
    
    parser.add_argument(
        "--sweep",
        action="store_true",
        help="Run temperature sweep experiment"
    )
    
    parser.add_argument(
        "--temperatures",
        nargs="+",
        type=float,
        default=[0.0, 0.5, 1.0],
        help="Temperatures for sweep (default: 0.0 0.5 1.0)"
    )
    
    parser.add_argument(
        "--templates",
        default="contracts/templates.json",
        help="Path to contract templates (default: contracts/templates.json)"
    )
    
    parser.add_argument(
        "--output-dir",
        default=OUTPUTS_DIR,
        help=f"Output directory (default: {OUTPUTS_DIR})"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.templates):
        print(f"❌ Error: Contract templates file not found: {args.templates}")
        sys.exit(1)
    
    # Initialize experiment system
    experiment = ComprehensiveExperiment(args.output_dir)
    
    # Run experiments
    try:
        for contract_id in args.contract:
            print(f"\n🔬 Processing Contract: {contract_id}")
            print("-" * 50)
            
            if args.sweep:
                # Run temperature sweep
                result = experiment.run_temperature_sweep(
                    args.templates, 
                    contract_id, 
                    args.temperatures,
                    args.runs
                )
                
                if "error" in result:
                    print(f"❌ Temperature sweep failed: {result['error']}")
                    continue
                
                print(f"\n📊 Temperature Sweep Results for {contract_id}:")
                print(f"  🌡️  Temperatures tested: {args.temperatures}")
                
                aggregate = result.get("aggregate_metrics", {})
                if aggregate:
                    print(f"  📈 Average R_raw: {aggregate.get('mean_R_raw', 0.0):.3f}")
                    print(f"  🎯 Average R_behavioral: {aggregate.get('mean_R_behavioral', 0.0):.3f}")
                    print(f"  🏗️  Average R_structural: {aggregate.get('mean_R_structural', 0.0):.3f}")
                
                hypothesis = result.get("final_hypothesis_evaluation", {})
                if hypothesis:
                    print(f"  🔬 Hypothesis: {hypothesis.get('conclusion', 'Unknown')}")
                
                print(f"  📊 Research summary: {result.get('research_summary_plot', 'N/A')}")
                
            else:
                # Run single experiment
                result = experiment.run_full_experiment(
                    args.templates,
                    contract_id,
                    args.runs,
                    args.temperature
                )
                
                if "error" in result:
                    print(f"❌ Experiment failed: {result['error']}")
                    continue
                
                print(f"\n📊 Single Experiment Results for {contract_id}:")
                
                metrics = result.get("metrics", {})
                if metrics:
                    print(f"  📈 R_raw: {metrics.get('R_raw', 0.0):.3f}")
                    print(f"  🎯 R_behavioral: {metrics.get('R_behavioral', 0.0):.3f}")
                    print(f"  🏗️  R_structural: {metrics.get('R_structural', 0.0):.3f}")
                    print(f"  📊 Behavioral improvement: {metrics.get('behavioral_improvement', 0.0):.3f}")
                    print(f"  📊 Structural improvement: {metrics.get('structural_improvement', 0.0):.3f}")
                
                hypothesis = result.get("hypothesis_evaluation", {})
                if hypothesis:
                    print(f"  🔬 Hypothesis: {hypothesis.get('conclusion', 'Unknown')}")
                
                bell_curve = result.get("bell_curve_analysis", {})
                if "plot_path" in bell_curve:
                    print(f"  📈 Bell curve plot: {bell_curve['plot_path']}")
        
        print(f"\n🎉 All experiments completed successfully!")
        print(f"📁 Results saved to: {args.output_dir}")
        print(f"📊 Check the analysis plots and CSV summaries for detailed results.")
        
        # Research conclusion
        print(f"\n🔬 RESEARCH CONCLUSION:")
        print(f"The SKYT system has been designed to test the hypothesis:")
        print(f"'Can prompt contracts and SKYT improve LLM-generated code repeatability?'")
        print(f"")
        print(f"Review the generated plots and metrics to evaluate:")
        print(f"1. Raw vs Behavioral vs Structural repeatability")
        print(f"2. Distance variance bell curves")
        print(f"3. Transformation success rates")
        print(f"4. Overall hypothesis support")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Experiment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
