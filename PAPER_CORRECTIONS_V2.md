# Paper Corrections — Remaining Changes (v2)

> All v1 corrections have been verified and applied. This document lists the
> **remaining issues** that still need fixing in the LaTeX and code.

---

## 1. MUST FIX: "thirteen" → "fourteen" foundational properties

The code (`src/foundational_properties.py`) has **14 active properties** in the list.
The paper says "thirteen" in three places. The enumeration in the paper already
lists 14 items, so only the word needs changing.

### Location 1 — Section 2.1 (Tooling)

**Current:**
```latex
The canon distance instantiates \textbf{thirteen} foundational properties
```

**Change to:**
```latex
The canon distance instantiates \textbf{fourteen} foundational properties
```

### Location 2 — Section 2.3 (Metrics and Canon Distance)

**Current:**
```latex
\textbf{Distance to canon} \(d(\cdot,\cdot)\): a structural distance derived from
thirteen foundational properties:
```

**Change to:**
```latex
\textbf{Distance to canon} \(d(\cdot,\cdot)\): a structural distance derived from
fourteen foundational properties:
```

### Location 3 — Section 2.3 (Canonical distance definition)

**Current:**
```latex
We instantiate \(d(\cdot,\cdot)\) as a normalized edit distance between serialized
fingerprints derived from the thirteen properties:
```

**Change to:**
```latex
We instantiate \(d(\cdot,\cdot)\) as a normalized edit distance between serialized
fingerprints derived from the fourteen properties:
```

---

## 2. SHOULD FIX: Artifact section — "4,500 rows, one per run"

The CSV has **one row per configuration** (contract x model x temperature),
not one row per individual LLM run. There are ~225 unique configs, each
aggregating n=20 runs.

**Current:**
```latex
The aggregated results
are in \texttt{outputs/metrics\_summary.csv} (4,500 rows, one per run).
```

**Change to:**
```latex
The aggregated results
are in \texttt{outputs/metrics\_summary.csv} (one row per configuration,
each aggregating $n{=}20$ runs; 225 rows for the primary dataset).
```

---

## 3. SHOULD FIX: Artifact CLI example says "all 12 contracts"

**Current:**
```latex
# Full evaluation (all 12 contracts)
python run_phase2_full.py
```

**Change to:**
```latex
# Full evaluation (all 15 contracts)
python run_phase2_full.py
```

---

## 4. DATA: Deduplicate is_prime_strict rows in metrics_summary.csv

Not a paper-text change, but the artifact CSV has duplicate n=20 rows for
11 `is_prime_strict` configurations (up to 3 rows per config). Before the
final artifact release, deduplicate by keeping only the latest-timestamped
row for each unique `(contract_id, model, decoding_temperature)` triple.

---

## 5. CODE: Update stale comment in foundational_properties.py

**File:** `src/foundational_properties.py`, line 20

**Current:**
```python
# Define the 13 foundational properties
```

**Change to:**
```python
# Define the 14 foundational properties
```

Also line 42:
```python
"""
Extract all 13 foundational properties from code
```

**Change to:**
```python
"""
Extract all 14 foundational properties from code
```

---

## Summary

| # | Priority | Type | Change |
|---|----------|------|--------|
| 1 | 🔴 Must fix | LaTeX | "thirteen" → "fourteen" in §2.1 and §2.3 (3 places) |
| 2 | 🟡 Should fix | LaTeX | Artifact: "4,500 rows, one per run" → "225 rows, one per config" |
| 3 | 🟡 Should fix | LaTeX | Artifact CLI comment: "12 contracts" → "15 contracts" |
| 4 | ⚠️ Pre-release | Data | Deduplicate is_prime_strict rows in metrics_summary.csv |
| 5 | ⚠️ Pre-release | Code | Update "13" → "14" comments in foundational_properties.py |
