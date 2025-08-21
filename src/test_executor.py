"""
Single test execution for A/B/C ablation study
Handles individual test runs with different configurations
"""

from typing import Optional, Dict, Any, List, Tuple
import json
import os
from pathlib import Path
import time

from test_config import TestConfiguration, TestMode, EnvironmentConfig
from test_prompts import TestPromptGenerator, AlgorithmPrompt
from llm_client import LLMClient
from contract import PromptContract
from compliance_checker import check_compliance
from canonicalizer import canonicalize_code
from smart_normalizer import smart_normalize_code
from log import save_final, save_raw_output
from prompt_enhancer import enhance_prompt
from acceptance_test_runner import run_acceptance_tests, AcceptanceTestReport

class TestExecutor:
    """Execute individual test runs with proper mode handling"""
    
    def __init__(self, llm_client: LLMClient, output_dir: str = "test_results"):
        self.llm_client = llm_client
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.prompt_generator = TestPromptGenerator()
    
    def run_single_test(self, prompt: AlgorithmPrompt, config: TestConfiguration, run_id: int, canonical_reference: str = None) -> Dict[str, Any]:
        """Run a single test with specified configuration and optional canonical reference"""
        
        print(f"\nStarting Test: {prompt.family}_{prompt.variant} (Mode {config.mode.value}, Run {run_id})")
        print(f"    Prompt Preview: {prompt.prompt_text[:100]}...")
        print(f"    LLM Parameters: temp={config.environment.temperature}, top_p={config.environment.top_p}, top_k={config.environment.top_k}")
        
        result = {
            "run_id": run_id,
            "family": prompt.family,
            "variant": prompt.variant,
            "mode": config.mode.value,
            "timestamp": time.time()
        }
        
        # Step 1: Check cache first (Mode C only)
        if config.enable_caching:
            cached_result = self._check_cache(prompt, config)
            if cached_result:
                print(f"   Cache hit: Using cached result")
                result.update(cached_result)
                result["cache_hit"] = True
                return result
        
        # Step 2: Get contract for this prompt
        contract = self.prompt_generator.create_contract_from_prompt(prompt)
        
        # Step 3: Build prompt based on mode
        # Mode A: Raw prompt only (no contracts, no enhancement)
        # Mode B & C: Enhanced prompt with dual intent capture
        if config.mode == TestMode.NO_CONTRACT:
            prompt_text = prompt.prompt_text
        else:
            # Modes B and C use enhanced prompting with contracts and LLM-based WHY extraction
            prompt_text = enhance_prompt(prompt, contract, self.llm_client)
        
        # Step 4: Get LLM output
        raw_output = self._get_llm_output(prompt_text, config)
        result["raw_output"] = raw_output
        print(f"   LLM generated {len(raw_output)} chars of code")
        
        # Mode A: No-contract (enhanced prompt + raw LLM only)
        if config.mode == TestMode.NO_CONTRACT:
            result["final_output"] = raw_output
            result["processing_steps"] = ["raw_llm"]
            print(f"✅ Test completed: {prompt.family}_{prompt.variant} (Mode {config.mode.value}, Run {run_id})")
            return result
        
        # Step 5: Establish canonical reference (Mode C only)
        if canonical_reference is None and config.enable_canonicalization:
            # First run: establish canonical reference from contract
            canonical_reference = self._generate_canonical_reference(contract)
            result["canonical_reference"] = canonical_reference
            print(f"   Established canonical reference ({len(canonical_reference)} chars)")
        
        # Step 6: Process according to configuration (Modes B & C)
        final_output = raw_output
        corrections = []
        status = "success"
        
        # Contract compliance check
        if config.enable_contracts:
            is_compliant, compliance_details = check_compliance(raw_output, contract)
            result["compliance"] = {"compliant": is_compliant, "details": compliance_details}
            if not is_compliant:
                print(f"   Contract compliance: FAILED - {compliance_details}")
            else:
                print(f"   Contract compliance: PASSED")
        
        # Canonicalization with reference-based transformation
        if config.enable_canonicalization and canonical_reference:
            if config.mode == TestMode.CANONICALIZE_WITH_REPAIR:
                final_output, transformation_success = canonicalize_code(raw_output, canonical_reference, contract)
            else:
                final_output, transformation_success = self._transform_to_canonical_reference(
                    raw_output, canonical_reference, contract
                )
            result["transformation_success"] = transformation_success
            if transformation_success:
                print(f"   Canonical transformation: SUCCESS")
            else:
                print(f"   Canonical transformation: FAILED - using best effort")
        
        # Repair if needed
        if config.enable_repair and config.mode != TestMode.CANONICALIZE_WITH_REPAIR:
            final_output, corrections, status = smart_normalize_code(final_output, contract)
            print(f"   Repair status: {status}")
        
        if corrections:
            print(f"   Corrections applied: {corrections}")
        
        result["final_output"] = final_output
        result["corrections"] = corrections
        result["status"] = status
        
        # Step 6: Run acceptance tests for correctness validation
        acceptance_report = None
        if hasattr(contract, 'acceptance_tests') and contract.acceptance_tests:
            try:
                acceptance_report = run_acceptance_tests(final_output, contract)
                print(f"        Acceptance tests: {acceptance_report.passed_tests}/{acceptance_report.total_tests} passed "
                      f"({acceptance_report.pass_rate:.1%}), correctness score: {acceptance_report.correctness_score:.3f}")
            except Exception as e:
                print(f"        Acceptance test execution failed: {e}")
                acceptance_report = None
        
        # Step 7: Cache result if enabled
        if config.enable_caching:
            result["cache_hit"] = False
            self._save_to_cache(prompt, config, final_output)
        
        result["processing_steps"] = self._get_processing_steps(config)
        result["acceptance_report"] = acceptance_report  # Add acceptance test results
        print(f"✅ Test completed: {prompt.family}_{prompt.variant} (Mode {config.mode.value}, Run {run_id})")
        return result
    
    def _transform_to_canonical_reference(self, code: str, canonical_reference: str, contract) -> tuple[str, bool]:
        """Transform code to match canonical reference"""
        try:
            from canonicalizer import Canonicalizer
            canonicalizer = Canonicalizer(contract)
            
            # Try to canonicalize the input code
            canonical_result = canonicalizer.canonicalize(code)
            canonical_code = canonical_result.canonical_code
            
            # Check if behavioral hashes match
            ref_canonicalizer = Canonicalizer(contract)
            ref_result = ref_canonicalizer.canonicalize(canonical_reference)
            
            if canonical_result.hashes.behavior_hash == ref_result.hashes.behavior_hash:
                # Behavioral match - use canonical reference for consistency
                return canonical_reference, True
            else:
                # No behavioral match - return canonicalized version but mark as failed transformation
                return canonical_code, False
                
        except Exception as e:
            print(f"   Canonicalization error: {e}")
            return code, False
    
    def _get_processing_steps(self, config: TestConfiguration) -> List[str]:
        """Get list of processing steps for the configuration"""
        steps = ["raw_llm"]
        
        if config.enable_contracts:
            steps.append("compliance_check")
        if config.enable_canonicalization:
            steps.append("canonicalization")
        if config.enable_repair and config.mode != TestMode.CANONICALIZE_WITH_REPAIR:
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
    
    def _get_llm_output(self, prompt: str, config: TestConfiguration) -> str:
        """Get LLM output using integrated LLM client"""
        if hasattr(self, 'llm_client') and self.llm_client:
            return self.llm_client.generate_code(prompt, config.environment)
        else:
            # Fallback placeholder for testing
            return f"def example_function():\n    return 'placeholder'"
    
    def _generate_canonical_reference(self, contract):
        """Generate canonical reference from contract"""
        from template_generator import generate_contract_template
        canonical_reference = generate_contract_template(contract)
        return canonical_reference
