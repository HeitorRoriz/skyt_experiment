#!/usr/bin/env python3
"""
SKYT Experiment Main Entry Point
Uses the new middleware architecture for LLM repeatability experiments
"""

import sys
import argparse
from src.runners.run_single import main as run_single_main
from src.runners.run_suite import main as run_suite_main

def main():
    """Main entry point with subcommand routing"""
    parser = argparse.ArgumentParser(
        description='SKYT LLM Repeatability Experiment System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run single prompt experiment
  python main.py single --prompt-id fibonacci_v1 --n 10

  # Run full experiment suite
  python main.py suite --matrix contracts/templates.json

  # Run with custom parameters
  python main.py single --prompt-id slugify_v1 --n 5 --tau 0.15 --temperature 0.2
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Single experiment subcommand
    single_parser = subparsers.add_parser('single', help='Run single prompt experiment')
    single_parser.add_argument('--prompt-id', required=True, help='Prompt identifier')
    single_parser.add_argument('--n', type=int, default=5, help='Number of samples')
    single_parser.add_argument('--mode', choices=['contract', 'simple'], default='contract')
    single_parser.add_argument('--tau', type=float, default=0.10, help='P_tau threshold')
    single_parser.add_argument('--model', default='gpt-4o-mini', help='LLM model')
    single_parser.add_argument('--temperature', type=float, default=0.0, help='Temperature')
    
    # Suite experiment subcommand
    suite_parser = subparsers.add_parser('suite', help='Run experiment suite')
    suite_parser.add_argument('--matrix', default='contracts/templates.json', help='Matrix file')
    suite_parser.add_argument('--n', type=int, default=5, help='Samples per prompt')
    suite_parser.add_argument('--mode', choices=['contract', 'simple'], default='contract')
    suite_parser.add_argument('--tau', type=float, default=0.10, help='P_tau threshold')
    suite_parser.add_argument('--model', default='gpt-4o-mini', help='LLM model')
    suite_parser.add_argument('--temperature', type=float, default=0.0, help='Temperature')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate subcommand
    if args.command == 'single':
        # Prepare sys.argv for run_single
        sys.argv = ['run_single.py'] + [
            '--prompt-id', args.prompt_id,
            '--n', str(args.n),
            '--mode', args.mode,
            '--tau', str(args.tau),
            '--model', args.model,
            '--temperature', str(args.temperature)
        ]
        return run_single_main()
    
    elif args.command == 'suite':
        # Prepare sys.argv for run_suite
        sys.argv = ['run_suite.py'] + [
            '--matrix', args.matrix,
            '--n', str(args.n),
            '--mode', args.mode,
            '--tau', str(args.tau),
            '--model', args.model,
            '--temperature', str(args.temperature)
        ]
        return run_suite_main()

if __name__ == '__main__':
    sys.exit(main())
