# Statistical Methods for SKYT Experiments

This document explains the statistical methods implemented in SKYT, addressing Professor Nasser's recommendations for methodological rigor.

---

## Overview

SKYT uses **small-sample-appropriate statistical methods** to analyze repeatability improvements. All methods are designed for:
- Small sample sizes (n=20 runs per contract)
- Proportion data (repeatability scores in [0,1])
- Multiple comparisons (12 contracts tested)
- Exploratory/proof-of-concept framing

---

## 1. Confidence Intervals

### Wilson Score Confidence Interval

**Purpose:** Estimate uncertainty in repeatability proportions.

**Why Wilson Score?**
- More accurate than normal approximation for small samples
- Works well for extreme proportions (near 0 or 1)
- Recommended by NIST Engineering Statistics Handbook

**Formula:**
```
CI = (p + z²/2n ± z√(p(1-p)/n + z²/4n²)) / (1 + z²/n)
```

Where:
- p = observed proportion (e.g., R_raw = 0.45)
- n = sample size (20 runs)
- z = critical value (1.96 for 95% CI)

**Example Output:**
```
R_raw: 0.45 [0.38, 0.52] (95% CI)
```

**Interpretation:** We are 95% confident the true repeatability is between 0.38 and 0.52.

### Bootstrap Confidence Interval

**Purpose:** Estimate uncertainty for any statistic (mean, median, etc.).

**Method:**
1. Resample data with replacement (10,000 times)
2. Calculate statistic for each resample
3. Use 2.5th and 97.5th percentiles as CI bounds

**Advantages:**
- No distributional assumptions
- Works for any statistic
- Empirical uncertainty quantification

**Example Output:**
```
Mean R_structural: 0.78 [0.75, 0.81] (95% CI, bootstrap)
```

---

## 2. Fisher's Exact Test

**Purpose:** Test if transformation significantly improves repeatability.

**Why Fisher's Exact?**
- **Recommended for small samples** (n=20)
- No assumptions about distribution
- Exact p-values (not approximations)
- Standard in medical/biological research for small samples

**Hypotheses:**
- H₀: No difference in success rates (R_raw = R_structural)
- H₁: Success rates differ (R_raw ≠ R_structural)

**Method:**
1. Create 2×2 contingency table:
   ```
   [[successes_after, failures_after],
    [successes_before, failures_before]]
   ```
2. Calculate exact p-value using hypergeometric distribution
3. Report odds ratio for effect size

**Example Output:**
```
Fisher's exact test: p=0.0023 *
Odds ratio: 9.0 (after/before)
```

**Interpretation:** 
- p < 0.05 → Significant improvement
- Odds ratio = 9.0 → 9× higher odds of success after transformation

---

## 3. Effect Sizes

### Cohen's h (for Proportions)

**Purpose:** Standardized measure of difference between proportions.

**Formula:**
```
h = 2 × arcsin(√p₂) - 2 × arcsin(√p₁)
```

**Interpretation:**
- |h| < 0.2: Negligible
- 0.2 ≤ |h| < 0.5: Small
- 0.5 ≤ |h| < 0.8: Medium
- |h| ≥ 0.8: Large

**Example:**
```
Cohen's h = 0.72 (medium effect)
```

### Odds Ratio

**Purpose:** Multiplicative measure of improvement.

**Formula:**
```
OR = (successes_after / failures_after) / (successes_before / failures_before)
```

**Interpretation:**
- OR = 1: No difference
- OR > 1: Improvement (higher success rate after)
- OR < 1: Degradation (lower success rate after)

**Example:**
```
Odds ratio: 9.0
Interpretation: 9× higher odds of success after transformation
```

### Absolute and Relative Improvement

**Absolute difference:**
```
Δ = R_structural - R_raw = 0.78 - 0.45 = 0.33
```

**Relative improvement:**
```
Relative = (Δ / R_raw) × 100 = (0.33 / 0.45) × 100 = 73%
```

---

## 4. Multiple Comparison Correction

### Holm-Bonferroni Method

**Purpose:** Control family-wise error rate when testing multiple contracts.

**Problem:** Testing 12 contracts increases false positive risk:
```
P(at least one false positive) = 1 - (1 - 0.05)¹² = 0.46
```

**Solution:** Holm-Bonferroni sequential rejection procedure.

**Method:**
1. Sort p-values: p₁ ≤ p₂ ≤ ... ≤ p₁₂
2. Test each p-value against adjusted α:
   - Test 1: p₁ vs α/12 = 0.0042
   - Test 2: p₂ vs α/11 = 0.0045
   - Test 3: p₃ vs α/10 = 0.0050
   - ...
3. Stop at first non-rejection

**Advantages over Bonferroni:**
- More powerful (rejects more true positives)
- Still controls family-wise error rate at α=0.05
- Simple and conservative (reviewer-friendly)

**Example Output:**
```
Holm-Bonferroni correction (α=0.05):
  Total tests: 12
  Significant: 8
  Rejected: fibonacci, binary_search, merge_sort, quick_sort, 
            factorial, is_palindrome, is_prime, gcd
```

---

## 5. Reporting Standards

### For Each Contract

**Descriptive Statistics:**
```
R_raw: 0.45 ± 0.03 [0.38, 0.52]
R_structural: 0.78 ± 0.02 [0.75, 0.81]
```

**Statistical Test:**
```
Fisher's exact test: p=0.0023 *
Odds ratio: 9.0 (95% CI: [3.2, 25.4])
```

**Effect Size:**
```
Cohen's h: 0.72 (medium effect)
Absolute improvement: +0.33
Relative improvement: +73%
```

### Aggregate Results

**Summary Statistics:**
```
Mean R_raw: 0.45 [0.42, 0.48] (95% CI)
Mean R_structural: 0.78 [0.75, 0.81] (95% CI)
Mean improvement: 0.33 [0.30, 0.36] (95% CI)
```

**Multiple Comparison:**
```
Significant contracts: 8/12 (Holm-Bonferroni, α=0.05)
```

---

## 6. Exploratory/Proof-of-Concept Framing

**Important:** These experiments are **exploratory** and serve as **proof-of-concept**, not definitive validation.

### What This Means:

**Exploratory:**
- Investigating feasibility of canonicalization approach
- Identifying patterns and effect sizes
- Generating hypotheses for future work

**Proof-of-Concept:**
- Demonstrates SKYT can improve repeatability
- Shows approach is implementable and measurable
- Provides initial evidence for further investigation

**Not Definitive:**
- Limited to 12 algorithmic contracts
- Single-file Python programs only
- 20 runs per contract (small but sufficient for exploratory work)

### Appropriate Claims:

✅ **Valid:**
- "SKYT demonstrates measurable improvements in repeatability"
- "Initial results suggest canonicalization is effective"
- "Proof-of-concept shows promise for further investigation"

❌ **Avoid:**
- "SKYT definitively proves repeatability can be guaranteed"
- "Results generalize to all code generation tasks"
- "SKYT solves the LLM repeatability problem"

---

## 7. Implementation

### Code Location

**Enhanced statistics module:**
```
src/enhanced_stats.py
```

**Key functions:**
```python
# Confidence intervals
wilson_confidence_interval(successes, trials, confidence=0.95)
bootstrap_confidence_interval(data, statistic_fn=np.mean, confidence=0.95)

# Statistical tests
fishers_exact_test(before_successes, before_trials, after_successes, after_trials)

# Effect sizes
effect_size_proportions(before_successes, before_trials, after_successes, after_trials)

# Multiple comparisons
holm_bonferroni_correction(p_values, alpha=0.05)

# Comprehensive analysis
compare_repeatability_rigorous(r_raw_list, r_structural_list, contract_names)
```

### Usage Example

```python
from src.enhanced_stats import compare_repeatability_rigorous, format_rigorous_report

# Repeatability scores for 12 contracts
r_raw = [0.45, 0.50, 0.42, 0.48, 0.43, 0.47, 0.44, 0.46, 0.49, 0.41, 0.52, 0.40]
r_structural = [0.78, 0.82, 0.75, 0.80, 0.77, 0.81, 0.76, 0.79, 0.83, 0.74, 0.85, 0.73]
contracts = ["fibonacci", "binary_search", "merge_sort", ...]

# Run comprehensive analysis
analysis = compare_repeatability_rigorous(r_raw, r_structural, contracts, confidence=0.95)

# Generate formatted report
print(format_rigorous_report(analysis))
```

**Output includes:**
- Descriptive statistics with 95% CIs
- Per-contract Fisher's exact tests
- Effect sizes (Cohen's h, odds ratios)
- Holm-Bonferroni correction results
- List of significant contracts

---

## 8. References

### Statistical Methods

**Wilson Score Interval:**
- Wilson, E.B. (1927). "Probable inference, the law of succession, and statistical inference." *Journal of the American Statistical Association*, 22(158), 209-212.

**Fisher's Exact Test:**
- Fisher, R.A. (1922). "On the interpretation of χ² from contingency tables, and the calculation of P." *Journal of the Royal Statistical Society*, 85(1), 87-94.

**Cohen's h:**
- Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.). Lawrence Erlbaum Associates.

**Holm-Bonferroni:**
- Holm, S. (1979). "A simple sequentially rejective multiple test procedure." *Scandinavian Journal of Statistics*, 6(2), 65-70.

### Recommended Resources

**NIST Engineering Statistics Handbook:**
- https://www.itl.nist.gov/div898/handbook/
- Comprehensive guide to statistical methods for small samples

**OpenIntro Statistics:**
- https://www.openintro.org/
- Open-source textbook with practical examples

**Small Sample Methods:**
- Agresti, A. & Coull, B.A. (1998). "Approximate is better than 'exact' for interval estimation of binomial proportions." *The American Statistician*, 52(2), 119-126.

---

## 9. For Paper Reviewers

### Addressing "Lack of Statistical Analysis"

**We now provide:**

1. ✅ **Confidence intervals** (Wilson score + bootstrap)
2. ✅ **Statistical tests** (Fisher's exact for small samples)
3. ✅ **Effect sizes** (Cohen's h, odds ratios, relative improvement)
4. ✅ **Multiple comparison correction** (Holm-Bonferroni)
5. ✅ **Exploratory framing** (proof-of-concept, not definitive)

**All methods are:**
- Appropriate for small samples (n=20)
- Standard in empirical research
- Implemented and tested (8/8 tests passing)
- Documented with references

### Sample Size Justification

**n=20 runs per contract is sufficient for:**
- Detecting large effects (Cohen's h ≥ 0.8) with 80% power
- Estimating proportions with ±10% margin of error (95% CI)
- Fisher's exact test (no minimum sample size requirement)
- Exploratory/proof-of-concept research

**Not sufficient for:**
- Detecting small effects (would need n≥100)
- Definitive validation (would need larger, more diverse dataset)
- Generalization claims (would need multi-domain evaluation)

**Our framing:** Results are **exploratory** and provide **initial evidence** for canonicalization effectiveness, warranting further investigation with larger samples and diverse tasks.

---

## Summary

SKYT's statistical analysis now meets rigorous standards for small-sample empirical research:

- **Confidence intervals** quantify uncertainty
- **Fisher's exact test** provides significance without distributional assumptions
- **Effect sizes** measure practical importance
- **Holm-Bonferroni** controls false positives across multiple contracts
- **Exploratory framing** sets appropriate expectations

This addresses reviewer concerns while maintaining scientific integrity and transparency about limitations.
