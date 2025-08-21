"""
Test executor for A/B/C ablation study
A: No-contract (raw LLM only)
B: Contract-only (contract + lint + canonicalization + repair; no cache)  
C: Full Skyt (B + replay/cache)
"""

from typing import Optional, Dict, Any, List, Tuple
import json
import os
from pathlib import Path
import time
from collections import Counter

from test_config import TestConfiguration, TestMode, EnvironmentConfig
from test_prompts import TestPromptGenerator, AlgorithmPrompt
from llm_client import LLMClient
from contract import PromptContract
from compliance_checker import check_compliance
from canonicalizer import canonicalize_code
from smart_normalizer import smart_normalize_code
from log import save_final, save_raw_output

class TestExecutor:
    """Execute A/B/C ablation tests with proper mode handling"""
    
    def __init__(self, llm_client: LLMClient, output_dir: str = "test_results"):
        self.llm_client = llm_client
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.prompt_generator = TestPromptGenerator()
    
    def run_single_test(self, prompt: AlgorithmPrompt, config: TestConfiguration, run_id: int) -> Dict[str, Any]:
        """Run a single test with specified configuration"""
        
        print(f"\n🧪 Starting Test: {prompt.family}_{prompt.variant} (Mode {config.mode.value}, Run {run_id})")
        print(f"   📝 Prompt: {prompt.prompt_text[:100]}...")
        print(f"   ⚙️ Config: temp={config.environment.temperature}, top_p={config.environment.top_p}, top_k={config.environment.top_k}")
        print(f"   🔧 Capabilities: caching={config.enable_caching}, contracts={config.enable_contracts}, canonicalization={config.enable_canonicalization}")
        
        result = {
            "run_id": run_id,
            "mode": config.mode.value,
            "family": prompt.family,
            "variant": prompt.variant,
            "config": config.to_dict()
        }
        
        # Step 1: Get raw LLM output
        raw_output = self._get_llm_output(prompt.prompt_text, config)
        
        result["raw_output"] = raw_output
        
        # Mode A: No-contract (raw LLM only)
        if config.mode == TestMode.NO_CONTRACT:
            result["final_output"] = raw_output
            result["processing_steps"] = ["raw_only"]
            return result
        
        # Mode B & C: Contract-based processing
        contract = self.prompt_generator.create_contract_from_prompt(prompt)
        
        # Step 2: Check cache first (Mode C only)
        if config.enable_caching:
            print(f"🔍 Step 2: Checking cache...")
            cached_result = self._check_cache(prompt, config)
            if cached_result:
                print(f"✅ Cache hit! Using cached result")
                result["final_output"] = cached_result["output"]
                result["cache_hit"] = True
                result["processing_steps"] = self._get_processing_steps(config)
                return result
            else:
                print(f"❌ Cache miss, proceeding with processing")
        
        # Step 2: Compliance checking (if contracts enabled)
        if config.enable_contracts:
            compliance_result = check_compliance(raw_output, contract)
            result["compliance"] = compliance_result
            
            if all(compliance_result.values()):
                result["final_output"] = raw_output
                result["processing_steps"] = ["raw_compliant"]
                return result
        
        # Step 3: Smart normalization (includes canonicalization and repair)
        print(f"🔧 Step 3: Starting smart normalization...")
        final_output, corrections, status = smart_normalize_code(
            raw_output, contract, run_number=run_id
        )
        
        print(f"📊 Normalization complete: status={status}, corrections={len(corrections)}")
        if corrections:
            print(f"   Corrections applied: {corrections}")
        
        result["final_output"] = final_output
        result["corrections"] = corrections
        result["status"] = status
        
        # Step 4: Cache handling (Mode C only)
        if config.enable_caching:
            result["cache_hit"] = False
            self._save_to_cache(prompt, config, final_output)
        
        result["processing_steps"] = self._get_processing_steps(config)
        print(f"✅ Test completed: {prompt.family}_{prompt.variant} (Mode {config.mode.value}, Run {run_id})")
        return result
    
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
            print(f"\n📋 Testing Algorithm: {prompt.family} (variant {prompt.variant})")
            print(f"   Expected function: {prompt.expected_function_name}")
            print(f"   Expected output: {prompt.expected_output_type}")
            
            for mode_config in [
                TestConfiguration.create_mode_a(env_config),
                TestConfiguration.create_mode_b(env_config), 
                TestConfiguration.create_mode_c(env_config)
            ]:
                print(f"\n🔄 Mode {mode_config.mode.value} Configuration:")
                print(f"   Environment: model={env_config.model_identifier}, temp={env_config.temperature}")
                print(f"   Capabilities: {[k for k, v in mode_config.to_dict()['capabilities'].items() if v]}")
                # Run multiple times for repeatability analysis
                mode_results = []
                for run in range(num_runs):
                    result = self.run_single_test(prompt, mode_config, run + 1)
                    mode_results.append(result)
                
                # Calculate repeatability for this mode
                repeatability = self._calculate_repeatability(mode_results)
                print(f"\n📊 Mode {mode_config.mode.value} Results: {repeatability:.1%} repeatability ({num_runs} runs)")
                
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
    
    def _get_llm_output(self, prompt: str, config: TestConfiguration) -> str:
        """Get LLM output using integrated LLM client"""
        if hasattr(self, 'llm_client') and self.llm_client:
            return self.llm_client.generate_code(prompt, config.environment)
        else:
            # Fallback placeholder for testing
            return f"def example_function():\n    return 'placeholder'"
    
    def _get_processing_steps(self, config: TestConfiguration) -> List[str]:
        """Get list of processing steps for the configuration"""
        steps = ["raw_llm"]
        
        if config.enable_contracts:
            steps.append("compliance_check")
        if config.enable_canonicalization:
            steps.append("canonicalization")
        if config.enable_repair:
            steps.append("repair")
        if config.enable_replay:
            steps.append("cache_replay")
            
        return steps
    
    def _check_cache(self, prompt: AlgorithmPrompt, config: TestConfiguration) -> Optional[Dict[str, Any]]:
        """Check cache for existing results (Mode C only)"""
        # Simplified cache implementation
        cache_key = f"{prompt.family}_{prompt.variant}_{config.environment.get_cache_key()}"
        cache_file = self.output_dir / "cache" / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def _save_to_cache(self, prompt: AlgorithmPrompt, config: TestConfiguration, output: str):
        """Save result to cache (Mode C only)"""
        cache_dir = self.output_dir / "cache"
        cache_dir.mkdir(exist_ok=True)
        
        cache_key = f"{prompt.family}_{prompt.variant}_{config.environment.get_cache_key()}"
        cache_file = cache_dir / f"{cache_key}.json"
        
        cache_data = {
            "output": output,
            "timestamp": time.time(),
            "config": config.to_dict()
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
    
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
