# src/middleware/schema.py
"""
[TODO schema.py]
Goal: define data contracts, CSV column schemas, and stable field names. No code.

1. Declare RunSpec fields: run_id, prompt_id, mode, model, temperature, seed, oracle_version, contract_id, normalization_version, timestamp.
2. Declare Canon fields: contract_id, canon_signature, oracle_version, normalization_version, fixed_at_timestamp, prompt_id, model, temperature, function_signatures, constraints_snapshot.
3. Declare DistanceRecord fields: run_id, sample_id, prompt_id, stage(pre|post), signature, d, compliant(bool), normalization_version, timestamp.
4. Declare RepairRecord fields: run_id, sample_id, before_signature, after_signature, d_before, d_after, steps, success, reason, timestamp.
5. Declare MetricsRecord fields: prompt_id, N, R_raw, R_anchor, mu_pre, mu_post, delta_R_anchor, delta_mu, P_tau_pre, P_tau_post, delta_P_tau, rescue_rate, tau.
6. Specify exact CSV headers for runs.csv, distances_pre.csv, distances_post.csv, repairs.csv, metrics_summary.csv.
7. Note: all writers/readers must reference these names (no magic strings).
8. Acceptance: all other modules import these names only; schema centralizes truth.
"""

import os
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime

# Version constants
NORMALIZATION_VERSION = "2025-09-26"
ORACLE_VERSION = "1.1.0"  # Updated with enhanced repair integration

@dataclass
class RunSpec:
    """Specification for a single experiment run"""
    run_id: str
    prompt_id: str
    mode: str  # "contract" or "simple"
    model: str
    temperature: float
    seed: Optional[int]
    oracle_version: str
    contract_id: str
    normalization_version: str
    timestamp: datetime

@dataclass
class Canon:
    """Immutable canonical reference for a prompt"""
    contract_id: str
    canon_signature: str
    oracle_version: str
    normalization_version: str
    fixed_at_timestamp: datetime
    prompt_id: str
    model: str
    temperature: float
    function_signatures: str
    constraints_snapshot: str

@dataclass
class DistanceRecord:
    """Distance measurement record (pre or post repair)"""
    run_id: str
    sample_id: str
    prompt_id: str
    stage: str  # "pre" or "post"
    signature: str
    d: float  # Distance [0,1]
    compliant: bool
    oracle_version: str
    normalization_version: str
    timestamp: datetime

@dataclass
class RepairRecord:
    """Repair operation record"""
    run_id: str
    sample_id: str
    before_signature: str
    after_signature: str
    d_before: float
    d_after: float
    steps: int
    success: bool
    reason: str
    normalization_version: str
    oracle_version: str
    timestamp: datetime

@dataclass
class MetricsRecord:
    """Aggregated metrics for a prompt"""
    prompt_id: str
    N: int  # Number of samples
    R_raw: float  # Raw repeatability (modal mass)
    R_anchor: float  # Anchor repeatability (d=0 fraction)
    mu_pre: float  # Mean distance pre-repair
    mu_post: float  # Mean distance post-repair
    delta_R_anchor: float  # R_anchor improvement
    delta_mu: float  # Mean distance improvement
    P_tau_pre: float  # Fraction ≤ tau pre-repair
    P_tau_post: float  # Fraction ≤ tau post-repair
    delta_P_tau: float  # P_tau improvement
    rescue_rate: float  # Successful repair rate
    tau: float  # Threshold for P_tau

# CSV Schema Definitions - Centralized truth for all CSV operations
RUNS_CSV_HEADERS = [
    "run_id", "prompt_id", "mode", "timestamp", "model", "temperature", 
    "seed", "oracle_version", "normalization_version", "contract_id"
]

DISTANCES_CSV_HEADERS = [
    "run_id", "sample_id", "prompt_id", "stage", "signature", "d", 
    "compliant", "oracle_version", "normalization_version", "timestamp"
]

REPAIRS_CSV_HEADERS = [
    "run_id", "sample_id", "before_signature", "after_signature", 
    "d_before", "d_after", "steps", "success", "reason", 
    "normalization_version", "oracle_version", "timestamp"
]

METRICS_CSV_HEADERS = [
    "prompt_id", "N", "R_raw", "R_anchor", "mu_pre", "mu_post", 
    "delta_R_anchor", "delta_mu", "P_tau_pre", "P_tau_post", 
    "delta_P_tau", "rescue_rate", "tau"
]

CANON_JSON_FIELDS = [
    "contract_id", "canon_signature", "oracle_version", "normalization_version",
    "fixed_at_timestamp", "prompt_id", "model", "temperature", 
    "function_signatures", "constraints_snapshot"
]

# File paths
RUNS_CSV_PATH = "outputs/logs/runs.csv"
DISTANCES_PRE_CSV_PATH = "outputs/logs/distances_pre.csv"
DISTANCES_POST_CSV_PATH = "outputs/logs/distances_post.csv"
REPAIRS_CSV_PATH = "outputs/logs/repairs.csv"
METRICS_CSV_PATH = "outputs/logs/metrics_summary.csv"
CANON_BASE_DIR = "outputs/canon"
CANON_JSON_PATH = "outputs/canon/canon.json"  # Deprecated: use get_canon_paths()
CANON_SIGNATURE_PATH = "outputs/canon/canon_signature.txt"  # Deprecated
CANON_CODE_FILENAME = "canon_code.txt"
CANON_DIR_TEMPLATE = os.path.join(CANON_BASE_DIR, "{prompt_id}")


def get_canon_paths(prompt_id: str) -> Dict[str, str]:
    """Return canonical file paths for a given prompt."""
    canon_dir = CANON_DIR_TEMPLATE.format(prompt_id=prompt_id)
    return {
        "dir": canon_dir,
        "json": os.path.join(canon_dir, "canon.json"),
        "signature": os.path.join(canon_dir, "canon_signature.txt"),
        "code": os.path.join(canon_dir, CANON_CODE_FILENAME),
    }

# Configuration constants
MAX_REPAIR_STEPS = 5
DEFAULT_TAU = 0.10
