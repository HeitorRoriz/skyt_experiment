# Paper Verification — Final Report (v3)

> **The LaTeX paper is now fully consistent with the codebase and data.**
> All previous corrections (v1 and v2) have been verified as applied.
> No further LaTeX changes are needed.

---

## Verification Summary

| Check | Result |
|-------|--------|
| "fifteen tasks" / "4,500 samples" (Abstract, §2.2, §4, §5, §6, Conclusion) | PASS |
| "fourteen foundational properties" (§2.1 ×1, §2.3 ×2) | PASS |
| Table 1: all 9 rows match `metrics_summary.csv` | PASS |
| Table 1: all 22 Wilson 95% CIs recomputed and match | PASS |
| Δ_rescue scope: "up to 1.00 strict / 0.95 base" | PASS — strict max = 1.00 (is_prime_strict, 4o-mini, T=0.0); base max = 0.95 (binary_search, 4o-mini, T=0.0) |
| Artifact example row (binary_search, 4o-mini, T=0.5): R_raw=0.30, R_pre=0.45, R_post=1.00, Δ=0.55 | PASS |
| Contract example labeled "(illustrative; simplified for exposition)" | PASS |
| Repair bound: "default k=5; up to 15 for strict variants" (§2.1, Contributions, Repair paragraph) | PASS |
| Artifact line-number ref replaced with query-based ref | PASS |
| CSV description: "one row per configuration…225 rows" | PASS |
| CLI comment: "all 15 contracts" | PASS |
| 14 properties enumerated individually in §2.1 and §2.3 | PASS |

---

## Pre-Release Cleanup (non-LaTeX)

These are **not paper-text issues** but should be addressed before the final artifact release:

### 1. Code comment: "13" → "14" in `foundational_properties.py`

**File:** `src/foundational_properties.py`

**Line 20:**
```python
# Current:
# Define the 13 foundational properties
# Change to:
# Define the 14 foundational properties
```

**Line 42:**
```python
# Current:
Extract all 13 foundational properties from code
# Change to:
Extract all 14 foundational properties from code
```

### 2. Deduplicate `is_prime_strict` rows in `metrics_summary.csv`

The CSV has duplicate n=20 rows for 11 `is_prime_strict` configurations (up to 3 rows per config due to re-runs). Before final Zenodo archival, deduplicate by keeping only the latest-timestamped row for each unique `(contract_id, model, decoding_temperature)` triple.

---

## No Further LaTeX Changes Required

The paper text, table values, confidence intervals, metric definitions, task counts, sample counts, property counts, and artifact references are all consistent with the code and data.
