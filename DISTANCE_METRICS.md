# Distance Metrics and Anchor Selection in SKYT

## Overview

SKYT uses **distance metrics** to measure how different two code implementations are, and **anchor selection** to choose a canonical reference point. This document explains the rationale behind these design decisions.

---

## Distance Metric: Normalized Levenshtein Distance

### What We Measure

SKYT uses **normalized Levenshtein distance** on AST (Abstract Syntax Tree) representations:

```python
distance = levenshtein(ast1, ast2) / max(len(ast1), len(ast2))
```

**Range:** [0.0, 1.0]
- **0.0** = Identical code (structurally)
- **1.0** = Completely different code

### Why Levenshtein on AST?

**1. Structural Focus**
- Ignores whitespace, comments, variable names
- Focuses on code structure (what matters for behavior)
- Example: `x = 1 + 2` and `x=1+2` have distance 0.0

**2. Normalization**
- Bounded [0,1] makes distances comparable across different code lengths
- Prevents bias toward longer/shorter implementations

**3. Simple and Interpretable**
- Easy to understand: "How many edits to transform A into B?"
- No complex hyperparameters or training required
- Reproducible across experiments

**4. Proven in SE Research**
- Standard metric in code similarity research
- Used in clone detection, code search, plagiarism detection
- Well-understood properties and limitations

### Alternative Metrics Considered

| Metric | Why Not Used |
|--------|--------------|
| **Token-based similarity** | Too sensitive to variable naming |
| **Tree edit distance** | Computationally expensive, complex to tune |
| **Embedding-based (CodeBERT)** | Black-box, not reproducible, requires GPU |
| **Cyclomatic complexity** | Only measures control flow, not structure |
| **Raw text diff** | Sensitive to formatting, comments |

---

## Anchor Selection: First Contract-Adherent, Oracle-Passing Output

### What is the Anchor?

The **anchor** (or **canon**) is the reference implementation that all other outputs are compared against.

**SKYT's Rule:** Use the **first LLM output that satisfies BOTH:**
1. **Contract adherence** - Follows all specified constraints (normalization rules, rescue bounds, domain restrictions)
2. **Oracle passing** - Passes all behavioral test cases

**This is NOT arbitrary** - it's a well-defined, deterministic selection criterion based on correctness.

### Why First Contract-Adherent, Oracle-Passing Output?

**1. Non-Arbitrary and Deterministic**
- **Not arbitrary:** Selection based on objective correctness criteria (contract + oracle)
- **Deterministic:** Same anchor every time you run the experiment
- **Reproducible:** No subjective judgment or randomness involved
- **Well-defined:** Clear pass/fail criteria from contract specification

**2. Dual Correctness Guarantee**
- **Behavioral correctness:** Passes oracle tests (correct functionality)
- **Structural correctness:** Adheres to contract constraints (proper form)
- **Complete validation:** Both behavior AND structure verified
- **Avoids broken code:** Cannot select incorrect or malformed implementations

**3. Unbiased Selection**
- **No cherry-picking:** Don't select "best" or "simplest" implementation
- **No subjective judgment:** Contract and oracle are objective
- **Representative:** First valid output represents model's natural behavior
- **Fair:** All outputs evaluated against same criteria

**4. Practical and Efficient**
- **Fast:** O(1) selection - stop at first valid output
- **Simple:** No complex selection algorithm needed
- **Transparent:** Easy to explain and justify in paper

### Addressing the "Arbitrary Selection" Concern

**Claim:** "Selecting the first output is arbitrary."

**Response:** This is incorrect. Our selection is **non-arbitrary** because:

1. **Objective Criteria:** Selection based on two objective measures:
   - Contract adherence (structural correctness)
   - Oracle passing (behavioral correctness)
   
2. **Well-Defined:** Contract specifies exact constraints (normalization rules, rescue bounds, domain restrictions). Oracle provides test cases with expected outputs. Both are deterministic pass/fail checks.

3. **No Subjective Judgment:** We don't evaluate "quality," "elegance," or "simplicity." Only: Does it meet the contract? Does it pass tests?

4. **Deterministic:** Given the same LLM outputs in the same order, anchor selection is always identical. No randomness, no human judgment.

5. **First ≠ Arbitrary:** "First" is a well-defined ordering criterion (temporal order of generation). Combined with objective correctness criteria, it's a principled selection strategy.

**Contrast with truly arbitrary selection:**
- ❌ "Pick whichever output looks best" - subjective
- ❌ "Randomly select from passing outputs" - non-deterministic
- ✅ "First output meeting objective correctness criteria" - deterministic and objective

### Alternative Anchor Selection Strategies

| Strategy | Why Not Used |
|----------|--------------|
| **Random passing output** | Non-deterministic, hurts reproducibility, ACTUALLY arbitrary |
| **Shortest passing output** | Biases toward terse code, may not be typical |
| **Most common output** | Requires clustering, adds complexity, subjective similarity threshold |
| **Human-written reference** | Not representative of LLM behavior, introduces human bias |
| **Median complexity output** | Requires defining "complexity", subjective judgment |
| **"Best" output** | Undefined criteria, subjective, ACTUALLY arbitrary |

---

## Distance Aggregation: Pairwise Mean

### How We Calculate Repeatability

**R_raw** (raw repeatability):
```python
# Calculate all pairwise distances
distances = []
for i in range(n):
    for j in range(i+1, n):
        distances.append(distance(output_i, output_j))

# Repeatability = 1 - mean distance
R_raw = 1.0 - mean(distances)
```

**R_anchor** (anchor-based repeatability):
```python
# Calculate distance from each output to anchor
distances = [distance(output_i, anchor) for i in range(n)]

# Repeatability = 1 - mean distance
R_anchor = 1.0 - mean(distances)
```

### Why Pairwise Mean?

**1. Captures Overall Consistency**
- Considers all pairs of outputs, not just one reference
- Robust to single outliers
- Represents average similarity across all outputs

**2. Bounded and Interpretable**
- R = 1.0 → All outputs identical
- R = 0.5 → Outputs moderately similar
- R = 0.0 → Outputs completely different

**3. Standard in Repeatability Research**
- Used in N-version programming studies
- Aligns with software diversity metrics
- Comparable to prior work

### Alternative Aggregation Methods

| Method | Why Not Used |
|--------|--------------|
| **Median distance** | Less sensitive to distribution shape |
| **Max distance** | Too sensitive to single outlier |
| **Min distance** | Ignores most of the data |
| **Variance of distances** | Harder to interpret than mean |

---

## Rationale Summary

### Distance Metric: Normalized Levenshtein on AST
✅ **Structural focus** (ignores formatting)  
✅ **Normalized** (comparable across code lengths)  
✅ **Simple** (no hyperparameters)  
✅ **Standard** (proven in SE research)

### Anchor Selection: First Contract-Adherent, Oracle-Passing Output
✅ **Non-Arbitrary** (objective correctness criteria: contract + oracle)  
✅ **Deterministic** (reproducible, no randomness)  
✅ **Dual Correctness** (behavioral AND structural validation)  
✅ **Unbiased** (no cherry-picking or subjective judgment)  
✅ **Simple** (O(1) selection, transparent)

### Aggregation: Pairwise Mean
✅ **Comprehensive** (all pairs considered)  
✅ **Robust** (not dominated by outliers)  
✅ **Interpretable** (bounded [0,1])  
✅ **Standard** (used in prior work)

---

## Threats to Validity

### Distance Metric Limitations

**1. AST-based distance may not capture semantic equivalence**
- Example: `for` loop vs `while` loop with same behavior
- Mitigation: Oracle tests ensure behavioral correctness
- Future work: Semantic-aware distance metrics

**2. Levenshtein treats all edits equally**
- Changing `+` to `-` has same cost as renaming variable
- Mitigation: Focus on structural patterns, not individual tokens
- Future work: Weighted edit distances

**3. Normalization may not be perfect for very different code lengths**
- Comparing 5-line vs 50-line implementations
- Mitigation: Contracts constrain problem scope, limiting length variance
- Observation: In practice, LLM outputs have similar lengths for same task

### Anchor Selection Limitations

**1. "First" is pragmatic, not optimal**
- Temporal order has no theoretical superiority over alternatives (last, shortest, median)
- "First" chosen for simplicity and efficiency (O(1) selection), not optimality
- A quality-based scoring system could select better anchors
- Mitigation: Deterministic and objective, though not theoretically optimal
- Future work: Quality-based anchor selection (see LIMITATIONS.md §4.2)

**2. Anchor quality affects canonicalization effectiveness**
- Better anchor → easier transformations → higher Δ_rescue
- Current approach may underestimate SKYT's potential
- Suboptimal anchor may require more transformations
- Mitigation: Results represent conservative lower bound
- Future work: Multi-dimensional quality scoring (structural simplicity, code quality, canonicalization potential, robustness)

**3. First output may not be "typical" or "best"**
- Could be lucky/unlucky first sample
- May not represent ideal implementation structure
- Mitigation: With 20 runs, first passing output is generally representative
- Validation: Experiments show first output is not an outlier
- Future work: Select anchor based on centrality to other valid outputs

**4. Assumes oracle tests are comprehensive**
- Anchor may pass tests but still be incorrect
- Mitigation: Contracts include multiple test cases covering edge cases
- Limitation: Acknowledged in paper's threats to validity

---

## Implementation Details

### Code Location

**Distance calculation:**
- `src/foundational_properties.py` - AST normalization
- `src/metrics.py` - Distance aggregation

**Anchor selection:**
- `src/canon_system.py` - Canon creation and storage
- `src/comprehensive_experiment.py` - First oracle-passing logic

### Example Usage

```python
from src.metrics import ComprehensiveMetrics
from src.canon_system import CanonSystem

# Initialize systems
canon_system = CanonSystem("outputs/canon")
metrics = ComprehensiveMetrics(canon_system)

# Create anchor from first passing output
anchor = canon_system.create_canon(
    contract_id="fibonacci",
    code=first_passing_output,
    properties=extracted_properties
)

# Calculate distances
distances = [
    metrics._calculate_distance(output, anchor)
    for output in all_outputs
]

# Calculate repeatability
R_anchor = 1.0 - np.mean(distances)
```

---

## References

**Distance Metrics in SE:**
- Jiang et al. (2007): "DECKARD: Scalable and Accurate Tree-Based Detection of Code Clones"
- Roy & Cordy (2008): "A Survey on Software Clone Detection Research"

**Anchor Selection:**
- Knight & Leveson (1986): "An Experimental Evaluation of the Assumption of Independence in Multiversion Programming"
- Hatton (1997): "N-Version Design Versus One Good Version"

**Repeatability Metrics:**
- Littlewood & Miller (1989): "Conceptual Modeling of Coincident Failures in Multiversion Software"
- Popov et al. (2003): "Stochastic Modeling of Coincident Failures in Fault-Tolerant Software"

---

## For Reviewers

**Q: Isn't selecting the "first" output arbitrary?**  
A: No. Selection requires **both** contract adherence (structural correctness) **and** oracle passing (behavioral correctness). This is an objective, deterministic criterion, not arbitrary. "First" refers to temporal order among outputs meeting these objective criteria. Truly arbitrary would be "pick whichever looks best" or "randomly select."

**Q: Why not use semantic similarity (e.g., CodeBERT embeddings)?**  
A: Embeddings are black-box and not reproducible. AST-based distance is transparent, deterministic, and sufficient for measuring structural repeatability.

**Q: Why not use the "best" output as anchor?**  
A: "Best" is subjective and introduces bias. First contract-adherent, oracle-passing output is deterministic, objective, and representative of LLM behavior.

**Q: Does anchor choice affect conclusions?**  
A: We validated that first output is not an outlier. The dual correctness requirement (contract + oracle) ensures anchor quality. Future work could explore multi-anchor analysis, but deterministic selection is critical for reproducibility.
