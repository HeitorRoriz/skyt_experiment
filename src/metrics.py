# src/metrics.py
"""
Simplified Repeatability Metrics for SKYT Experiment
Only two core metrics: R_raw and R_canon
"""

import hashlib
from typing import List, Dict, Any
from collections import Counter
from dataclasses import dataclass


@dataclass
class RepeatabilityResult:
    """Simple result structure for the two core metrics"""
    total_runs: int
    r_raw: float      # Raw repeatability: identical outputs / total runs
    r_canon: float    # Canonical repeatability: identical canonical forms / total runs
    raw_distribution: Dict[str, int]      # Hash -> count for raw outputs
    canon_distribution: Dict[str, int]    # Hash -> count for canonical outputs


def calculate_r_raw(outputs: List[str]) -> float:
    """Calculate raw repeatability: most frequent identical output / total runs"""
    if len(outputs) <= 1:
        return 1.0
    
    # Count identical raw outputs
    output_counts = Counter(outputs)
    max_identical = max(output_counts.values())
    
    return max_identical / len(outputs)


def calculate_r_canon(canonical_hashes: List[str]) -> float:
    """Calculate canonical repeatability: most frequent canonical form / total runs"""
    if len(canonical_hashes) <= 1:
        return 1.0
    
    # Count identical canonical forms
    hash_counts = Counter(canonical_hashes)
    max_identical = max(hash_counts.values())
    
    return max_identical / len(canonical_hashes)


def hash_output(output: str) -> str:
    """Generate SHA-256 hash for output comparison"""
    return hashlib.sha256(output.encode('utf-8')).hexdigest()[:16]


def calculate_repeatability_metrics(raw_outputs: List[str], canonical_outputs: List[str]) -> RepeatabilityResult:
    """
    Calculate both R_raw and R_canon metrics
    
    Args:
        raw_outputs: List of raw LLM outputs
        canonical_outputs: List of canonicalized outputs (same order as raw)
    
    Returns:
        RepeatabilityResult with both metrics
    """
    if len(raw_outputs) != len(canonical_outputs):
        raise ValueError("Raw and canonical output lists must have same length")
    
    total_runs = len(raw_outputs)
    
    # Calculate R_raw
    r_raw = calculate_r_raw(raw_outputs)
    
    # Calculate R_canon using canonical hashes
    canonical_hashes = [hash_output(output) for output in canonical_outputs]
    r_canon = calculate_r_canon(canonical_hashes)
    
    # Generate distributions for analysis
    raw_hashes = [hash_output(output) for output in raw_outputs]
    raw_distribution = dict(Counter(raw_hashes))
    canon_distribution = dict(Counter(canonical_hashes))
    
    return RepeatabilityResult(
        total_runs=total_runs,
        r_raw=r_raw,
        r_canon=r_canon,
        raw_distribution=raw_distribution,
        canon_distribution=canon_distribution
    )


def print_metrics_summary(result: RepeatabilityResult, prompt_name: str = ""):
    """Print concise summary of the two core metrics"""
    print(f"\n{'='*50}")
    if prompt_name:
        print(f"REPEATABILITY METRICS: {prompt_name}")
    else:
        print("REPEATABILITY METRICS")
    print(f"{'='*50}")
    
    print(f"Total Runs: {result.total_runs}")
    print(f"R_raw:      {result.r_raw:.3f} ({result.r_raw:.1%})")
    print(f"R_canon:    {result.r_canon:.3f} ({result.r_canon:.1%})")
    
    print(f"\nRaw Distribution:")
    for hash_val, count in result.raw_distribution.items():
        print(f"  {hash_val}: {count} runs")
    
    print(f"\nCanonical Distribution:")
    for hash_val, count in result.canon_distribution.items():
        print(f"  {hash_val}: {count} runs")
