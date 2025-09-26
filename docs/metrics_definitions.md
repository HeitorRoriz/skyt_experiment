# SKYT Middleware - Metrics Definitions

## Overview

This document provides precise mathematical definitions for all repeatability metrics computed by the SKYT middleware system, including edge cases and version requirements.

## Core Principle: Single Canon

**Critical Constraint**: Only one canon exists per prompt, established by the first compliant output plus contract snapshot. The canon is immutable thereafter.

**Canon Establishment**:
- Canon is fixed when: `oracle_check(output, contract) == True` AND no prior canon exists
- Canon includes: normalized code, signature, contract snapshot, oracle version, normalization version
- All subsequent runs are measured against this single reference point

## Primary Metrics

### R_raw: Raw LLM Repeatability

**Definition**: Modal probability mass of pre-repair signatures within a prompt set.

```
R_raw = max(count(sig_i)) / N
where sig_i are unique signatures in pre-repair outputs
```

**Interpretation**: 
- R_raw = 1.0: All raw outputs are byte-identical
- R_raw = 1/N: All outputs are unique (minimum repeatability)
- Measures pure LLM consistency before any processing

**Edge Cases**:
- Empty output set: R_raw = 0.0
- Single output: R_raw = 1.0

### R_anchor: Canonical Repeatability

**Definition**: Fraction of post-repair outputs with distance d=0 to the established canon.

```
R_anchor = count(d_post == 0.0) / N
where d_post are post-repair distances to canon
```

**Interpretation**:
- R_anchor = 1.0: All outputs converge to canon after repair
- R_anchor = 0.0: No outputs reach canon (repair ineffective)
- Measures canonicalization system effectiveness

**Edge Cases**:
- No canon established: R_anchor = 0.0 by definition
- Canon not available for distance computation: R_anchor = 0.0

### Rescue Rate: Repair Effectiveness

**Definition**: Fraction of samples that transition from non-canonical (d>0) to canonical (d=0).

```
rescue_rate = count(d_pre > 0 AND d_post == 0) / N
```

**Interpretation**:
- rescue_rate = 1.0: All non-canonical inputs successfully repaired
- rescue_rate = 0.0: No successful repairs
- Measures repair system capability

**Edge Cases**:
- All inputs already canonical (d_pre = 0): rescue_rate = 0.0
- No repair attempts made: rescue_rate = 0.0

## Distance Statistics

### μ_pre, μ_post: Mean Distances

**Definition**: Arithmetic mean of distances before and after repair.

```
μ_pre = Σ(d_pre_i) / N
μ_post = Σ(d_post_i) / N
```

**Properties**:
- Range: [0.0, 1.0]
- Lower values indicate closer proximity to canon
- μ_post ≤ μ_pre (monotonic repair constraint)

### P_τ: Threshold Success Rate

**Definition**: Fraction of outputs within distance threshold τ of canon.

```
P_τ_pre = count(d_pre ≤ τ) / N
P_τ_post = count(d_post ≤ τ) / N
```

**Default**: τ = 0.10 (configurable via CLI)

**Interpretation**:
- P_τ = 1.0: All outputs within threshold
- P_τ = 0.0: No outputs within threshold
- Measures "near-canonical" success rate

## Delta Metrics

### ΔR_anchor: Anchor Repeatability Improvement

**Definition**: Improvement in canonical repeatability.

```
ΔR_anchor = R_anchor_post - R_anchor_pre
where R_anchor_pre = 0.0 by definition (no canon exists pre-repair)
```

**Simplification**: `ΔR_anchor = R_anchor`

**Range**: [0.0, 1.0]

### Δμ: Mean Distance Improvement

**Definition**: Reduction in mean distance to canon.

```
Δμ = μ_post - μ_pre
```

**Properties**:
- Range: [-1.0, 0.0] (negative indicates improvement)
- Δμ = 0.0: No change in mean distance
- More negative values indicate better repair effectiveness

### ΔP_τ: Threshold Success Improvement

**Definition**: Improvement in threshold-based success rate.

```
ΔP_τ = P_τ_post - P_τ_pre
```

**Properties**:
- Range: [-1.0, 1.0]
- Positive values indicate improvement
- ΔP_τ = 0.0: No change in threshold success

## Distance Function

### Normalized Levenshtein Distance

**Definition**: Edit distance normalized by maximum string length.

```
d(a, b) = levenshtein(a, b) / max(len(a), len(b))
```

**Properties**:
- Range: [0.0, 1.0]
- d(a, a) = 0.0 (identical strings)
- d("", s) = 1.0 for non-empty s
- d("", "") = 0.0

**Deterministic Requirement**: 
- Identical normalized text MUST yield d = 0.0
- Identical normalized text MUST yield identical SHA-256 signatures

**Future Extension**: 
- AST-based distance may replace Levenshtein without changing CSV schema
- Distance function versioning tracked in logs

## Signature Computation

### SHA-256 Over Normalized Text

**Definition**: Deterministic hash of normalized code bytes.

```
signature = SHA256(normalized_text.encode('utf-8')).hexdigest()
```

**Requirements**:
- MUST be deterministic: identical input → identical signature
- MUST use UTF-8 encoding consistently
- Normalization MUST be applied before signature computation

## Version Requirements

### Normalization Version Impact

**Critical**: Changing normalization breaks signature compatibility.

**Requirements**:
- All logs MUST record `normalization_version`
- Version changes invalidate cross-version comparisons
- Canon established with version X only valid for version X

### Oracle Version Impact

**Critical**: Oracle rule changes affect canon establishment.

**Requirements**:
- All logs MUST record `oracle_version`
- Canon validity tied to oracle version
- Version changes may require canon re-establishment

## Edge Cases and Error Handling

### Empty or Invalid Inputs

1. **Empty normalized text**: 
   - Signature: SHA-256 of empty string
   - Distance to non-empty: 1.0
   - Distance to empty: 0.0

2. **Syntax errors in code**:
   - Normalization may fail → fallback normalization
   - Oracle check fails → no canon establishment
   - Repair attempts may fail → bounded failure

3. **Missing canon**:
   - All distances default to 1.0 (maximum)
   - R_anchor = 0.0
   - Repair effectiveness unmeasurable

### Computational Limits

1. **Very long strings**: 
   - Levenshtein computation O(n²) → may timeout
   - Fallback: truncate or use approximate distance

2. **Large experiment sets**:
   - Memory usage for signature storage
   - CSV file size management

## Validation Requirements

### Metric Consistency

1. **Range Validation**:
   - All probabilities ∈ [0.0, 1.0]
   - All distances ∈ [0.0, 1.0]
   - Delta metrics within expected ranges

2. **Logical Consistency**:
   - R_anchor ≤ 1.0 always
   - μ_post ≤ μ_pre (monotonic repair)
   - P_τ_post ≥ P_τ_pre (repair should not worsen)

3. **Determinism Validation**:
   - Repeated computation yields identical results
   - Signature consistency across runs
   - Distance function symmetry where applicable

## Implementation Notes

### Precision Requirements

- Floating point: Use standard double precision
- Rounding: Round to 3 decimal places for display
- Storage: Full precision in CSV, rounded for visualization

### Performance Considerations

- Signature computation: O(n) where n = text length
- Distance computation: O(n²) for Levenshtein
- Metrics aggregation: O(N) where N = sample count

### Memory Management

- Streaming CSV processing for large datasets
- Signature caching for repeated computations
- Lazy loading of distance matrices
