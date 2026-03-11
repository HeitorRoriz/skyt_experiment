# Paper Corrections — Revision 2 (Updated LaTeX Review)

> **Previous corrections (v1) have been applied.** This revision verifies those fixes
> and identifies **one new issue** discovered during the re-check.

---

## Previously Reported Issues — Status

| # | Issue | Status |
|---|-------|--------|
| 1a | Task count 12 → 15; samples 3,600 → 4,500 | ✅ **FIXED** — Abstract, §2.2, §4, §5, §6, Conclusion all say "fifteen" / "4,500" |
| 1b | Max Δ_rescue scope unclear | ✅ **FIXED** — Abstract now says "up to 1.00 on strict…and up to 0.95 on base tasks" |
| 2a | Example contract schema mismatch | ✅ **FIXED** — Relabeled "(illustrative; simplified for exposition)" |
| 2b | Repair bound "default k=5" without noting strict variants | ✅ **FIXED** — §2.1, Contributions #4, and Repair paragraph all say "up to 15 for strict variants" |
| 3a | 13 properties enumerated as 12 due to grouping | ✅ **FIXED** — Both §2.1 and §2.3 now list algebraic structure, numerical behavior, logical equivalence separately |
| 4a | Task count in §4.1 | ✅ **FIXED** — "fifteen algorithmic tasks: twelve base…plus three strict-compliance variants" |
| 4b | Sample total in §4.1 | ✅ **FIXED** — "15 × 5 × 3 × 20 = 4,500" |
| 5a | Table 1 Binary-Search / 4o-mini wrong values | ✅ **FIXED** — Now shows .39/.10/.40/+.30 with correct CIs |
| 5b | Other 8 table rows | ✅ **CONFIRMED CORRECT** — No changes needed |
| 6a | Binary-Search headline Δ_rescue in prose | ✅ **FIXED** — §2.2 says "Δ_rescue=0.95" (per-temperature, correct); table shows pooled +.30 |
| 7a | Duplicate is_prime_strict rows in CSV | ⚠️ **DATA ISSUE** — Not a paper-text fix; CSV still needs deduplication in artifact |
| 7b | Fragile line-number reference in artifact section | ✅ **FIXED** — Now uses query-based reference: "the row matching contract_id=binary_search…" |

---

## NEW Issue Found in Revision 2

### 🔴 Property count: paper says "thirteen" but code has **fourteen** active properties

**Locations in paper (3 occurrences):**
1. §2.1: "The canon distance instantiates **thirteen** foundational properties"
2. §2.3: "a structural distance derived from **thirteen** foundational properties"
3. §2.3 (canonical distance definition): "derived from the **thirteen** properties"

**Problem:**
The code (`src/foundational_properties.py`, lines 22–38) defines **14 active** properties:

```
 1. control_flow_signature
 2. data_dependency_graph
 3. execution_paths
 4. function_contracts
 5. complexity_class
 6. side_effect_profile
 7. termination_properties
 8. algebraic_structure
 9. numerical_behavior
10. logical_equivalence
11. normalized_ast_structure
12. operator_precedence
13. statement_ordering
14. recursion_schema          ← added later
    # behavioral_signature   ← DISABLED
```

The original design had 13 properties. `behavioral_signature` was later disabled and `recursion_schema` was added, but the net count became 14 (13 original − 1 disabled + 1 new + the 1 that was already there = 14). The code comment on line 20 still says "Define the 13 foundational properties" but `len(fp.properties)` returns **14**.

The paper's enumeration in both §2.1 and §2.3 also lists 14 items (now that algebraic/numerical/logical are ungrouped), which contradicts the word "thirteen."

**Correction — choose one:**

- **Option A (recommended): Say "fourteen."** Change all three occurrences of "thirteen" to "fourteen." The enumeration already lists 14 items, so this makes everything consistent. Also update the code comment.

- **Option B: Merge two properties to keep 13.** For example, merge `algebraic_structure` and `numerical_behavior` into a single `algebraic_numerical` property in the code. This would require a code change and potentially re-running experiments (since the fingerprint would change).

- **Option C: Drop `recursion_schema` from the list for paper purposes.** Mention it as an optional/supplementary property but exclude it from the count. Less recommended since it's actively used in the distance computation.

---

## Minor Observations (not errors, just notes)

### Artifact section: "4,500 rows, one per run"

The text says:
> "The aggregated results are in `outputs/metrics_summary.csv` (4,500 rows, one per run)."

This is slightly misleading. The CSV has **one row per configuration** (contract × model × temperature), not one row per individual LLM run. With 15 × 3 × 5 = 225 unique configs (plus some duplicate/older rows), the CSV has ~308 rows total, not 4,500. Each row *aggregates* 20 runs.

**Suggestion:** Change to "(one row per configuration, each aggregating n=20 runs; 225 rows for the primary dataset)."

### Artifact section: CLI example says "all 12 contracts"

The text says:
```
# Full evaluation (all 12 contracts)
python run_phase2_full.py
```

Should say "all 15 contracts" for consistency with the rest of the paper.

### Conclusion: "0.95 on base tasks in per-temperature configurations"

The conclusion says:
> "Δ_rescue reaching up to 1.00 on strict-compliance variants and 0.95 on base tasks"

This is correct. The qualifier "in per-temperature configurations" was dropped, which is fine since the 0.95 is indeed a per-temperature value (Binary-Search, 4o-mini, T=0.0). No change needed, but the reader should understand this is a single-config maximum, not a pooled value.

---

## Summary of Remaining Changes

| Priority | Location | Change |
|----------|----------|--------|
| 🔴 Must fix | §2.1, §2.3 (×3 occurrences) | "thirteen" → "**fourteen**" foundational properties |
| 🟡 Should fix | §5 Artifact | "4,500 rows, one per run" → clarify it's one row per config (~225 rows) |
| 🟡 Should fix | §5 Artifact CLI example | "all 12 contracts" → "all 15 contracts" |
| ⚠️ Data | `metrics_summary.csv` | Deduplicate is_prime_strict rows before final artifact release |
| ⚠️ Code | `foundational_properties.py` line 20 | Update comment "13" → "14" |
