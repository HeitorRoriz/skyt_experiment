# SKYT Middleware - Single Canon Repeatability System

## Overview

The SKYT Middleware provides a comprehensive system for measuring LLM code generation repeatability through single canon establishment, distance measurement, bounded repair, and metrics computation. The system wraps existing experiment runners without breaking API compatibility.

## Core Concepts

### Single Canon
- **Immutable Reference**: First compliant output establishes the canonical form
- **Contract-Driven**: Canon is derived from contract specifications and oracle validation
- **Persistent Storage**: Canon stored in `outputs/canon/` with signature and metadata
- **Invariant Enforcement**: Any attempt to modify canon after establishment fails loudly

### Distance Measurement
- **Pre/Post Tracking**: Measures distance before and after repair operations
- **Normalized Levenshtein**: Distance d ∈ [0,1] based on edit distance over normalized text
- **Signature-Based**: SHA-256 signatures for deterministic comparison
- **Comprehensive Logging**: All distance measurements logged to CSV with full context

### Bounded Repair System
- **Monotonic Constraint**: Distance must decrease or remain same at each step
- **Step Limits**: Maximum repair attempts bounded by `MAX_REPAIR_STEPS`
- **Idempotent**: No changes when d=0 at entry
- **Targeted Fixes**: Function name correction, comment removal, print cleanup

### Metrics Computation
- **R_raw**: Raw repeatability (modal signature mass)
- **R_anchor**: Canon repeatability (fraction with d=0)
- **Rescue Rate**: Successful repair rate (d>0 → d=0)
- **Distance Statistics**: Mean distances pre/post, P_tau thresholds
- **Delta Analysis**: Improvement measurements (Δμ, ΔR_anchor, ΔP_tau)

## Data Flow

The middleware implements a 7-step pipeline that wraps existing LLM calls:

1. **Call Upstream**: Execute original LLM callable to get raw output
2. **Normalize & Sign**: Apply normalization pipeline and compute SHA-256 signature
3. **Canon Management**: Establish canon if first compliant run, else assert immutability
4. **Pre-Distance**: Compute and log distance to canon before repair
5. **Repair Attempt**: Apply bounded, monotonic repair if non-compliant
6. **Post-Distance**: Compute and log distance after repair
7. **Return Original**: Pass through original output for API compatibility

## File Structure

```
src/middleware/
├── schema.py           # Data contracts and CSV schemas
├── canon_anchor.py     # Immutable canon lifecycle
├── distance.py         # Signature and distance computation
├── repair.py          # Bounded monotonic repair
├── contract_enforcer.py # Oracle validation
├── logger.py          # Atomic CSV operations
├── metrics.py         # Repeatability calculations
├── pipeline.py        # Main wrapper system
└── viz.py             # Visualization generation

outputs/
├── canon/
│   ├── canon.json     # Canon metadata
│   └── canon_signature.txt # Canon signature
├── logs/
│   ├── runs.csv       # Run specifications
│   ├── distances_pre.csv # Pre-repair distances
│   ├── distances_post.csv # Post-repair distances
│   ├── repairs.csv    # Repair operations
│   └── metrics_summary.csv # Aggregated metrics
└── figs/
    ├── pre_vs_post_overlay.png # Distance distributions
    ├── violin_pre.png # Pre-repair by prompt
    ├── violin_post.png # Post-repair by prompt
    └── summary_dashboard.png # Comprehensive metrics
```

## Usage

### Single Experiment
```bash
python -m src.runners.run_single --prompt-id fibonacci_v1 --n 10 --mode contract
```

### Experiment Suite
```bash
python -m src.runners.run_suite --matrix contracts/templates.json --n 5
```

### Integration with Existing Code
```python
from src.middleware.pipeline import wrap_contract_run, create_pipeline_context

# Create context
context = create_pipeline_context("fibonacci_v1", contract, "gpt-4o-mini", 0.0)

# Wrap LLM call
def llm_callable():
    return query_llm(messages, model, temperature)

result = wrap_contract_run(llm_callable, context)
```

## Key Features

### Invariant Enforcement
- **Canon Immutability**: Once established, canon cannot be changed
- **Monotonic Repair**: Distance never increases during repair steps
- **Bounded Operations**: All operations have maximum step limits
- **Deterministic Signatures**: Identical code always produces identical signatures

### Comprehensive Logging
- **Atomic Operations**: All CSV writes are atomic to prevent corruption
- **Schema Validation**: Headers validated against centralized schema
- **Versioning**: Normalization and oracle versions tracked
- **Audit Trail**: Complete record of all operations and decisions

### Metrics & Analysis
- **Multi-Dimensional**: Raw, canonical, and behavioral repeatability
- **Statistical Analysis**: Mean, variance, threshold-based metrics
- **Improvement Tracking**: Delta measurements show repair effectiveness
- **Visualization**: Automated generation of analysis plots

## Configuration

Key configuration constants in `schema.py`:
- `MAX_REPAIR_STEPS = 5`: Maximum repair attempts
- `DEFAULT_TAU = 0.10`: Default threshold for P_tau metrics
- `NORMALIZATION_VERSION`: Version tracking for normalization pipeline
- `ORACLE_VERSION`: Version tracking for contract validation

## Links

- [Detailed Metrics Definitions](metrics_definitions.md)
- [CSV Schema Reference](../src/middleware/schema.py)
- [Test Suite](../tests_mw/)
- [Build Instructions](Skyt_middleware_build_instructions.md)
