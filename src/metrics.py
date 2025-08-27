# src/metrics.py
"""
Four Core Metrics for SKYT Experiment:
- R_raw: Raw repeatability
- R_canon: Canonical repeatability  
- canon_coverage: Canonicalization success rate
- rescue_delta: Improvement from canonicalization
"""

import hashlib
from typing import List, Dict, Any, Optional
from collections import Counter
from dataclasses import dataclass


@dataclass
class MetricsResult:
    """Result structure for the four core metrics"""
    total_runs: int
    r_raw: float           # Raw repeatability: most frequent raw output / total runs
    r_canon: float         # Canonical repeatability: most frequent canonical form / total runs  
    canon_coverage: float  # Canonicalization success rate: successful canonicalizations / total runs
    rescue_delta: float    # Improvement from canonicalization: R_canon - R_raw


def calculate_r_raw(outputs: List[str]) -> float:
    """Calculate raw repeatability: most frequent identical output / total runs"""
    if len(outputs) <= 1:
        return 1.0
    
    output_counts = Counter(outputs)
    max_identical = max(output_counts.values())
    return max_identical / len(outputs)


def calculate_r_canon(canonical_outputs: List[Optional[str]], contract_passes: List[bool]) -> float:
    """Calculate canonical repeatability: most frequent canonical form among contract-passing runs / total runs"""
    # Only consider outputs from runs that passed the full contract
    valid_outputs = []
    for i, (output, passed) in enumerate(zip(canonical_outputs, contract_passes)):
        if passed and output is not None:
            valid_outputs.append(output)
    
    if len(valid_outputs) <= 1:
        return 1.0 if len(valid_outputs) == 1 else 0.0
    
    output_counts = Counter(valid_outputs)
    max_identical = max(output_counts.values())
    return max_identical / len(canonical_outputs)  # Denominator is total runs, not just valid ones


def calculate_canon_coverage(canonical_outputs: List[Optional[str]]) -> float:
    """Calculate canonicalization success rate"""
    if not canonical_outputs:
        return 0.0
    
    successful = sum(1 for output in canonical_outputs if output is not None)
    return successful / len(canonical_outputs)


def calculate_rescue_delta(r_raw: float, r_canon: float) -> float:
    """Calculate improvement from canonicalization"""
    return r_canon - r_raw


def hash_output(output: str) -> str:
    """Generate SHA-256 hash for output comparison"""
    return hashlib.sha256(output.encode('utf-8')).hexdigest()[:16]


def calculate_metrics(raw_outputs: List[str], canonical_outputs: List[Optional[str]], contract_passes: List[bool]) -> MetricsResult:
    """
    Calculate all four core metrics
    
    Args:
        raw_outputs: List of raw LLM outputs
        canonical_outputs: List of canonicalized outputs (None if canonicalization failed)
        contract_passes: List of boolean flags indicating full contract pass
    
    Returns:
        MetricsResult with all four metrics
    """
    if len(raw_outputs) != len(canonical_outputs) or len(raw_outputs) != len(contract_passes):
        raise ValueError("All input lists must have same length")
    
    total_runs = len(raw_outputs)
    
    # Calculate all four metrics
    r_raw = calculate_r_raw(raw_outputs)
    r_canon = calculate_r_canon(canonical_outputs, contract_passes)
    canon_coverage = calculate_canon_coverage(canonical_outputs)
    rescue_delta = calculate_rescue_delta(r_raw, r_canon)
    
    return MetricsResult(
        total_runs=total_runs,
        r_raw=r_raw,
        r_canon=r_canon,
        canon_coverage=canon_coverage,
        rescue_delta=rescue_delta
    )
