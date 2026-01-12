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

## Anchor Selection: First Oracle-Passing Output

### What is the Anchor?

The **anchor** (or **canon**) is the reference implementation that all other outputs are compared against.

**SKYT's Rule:** Use the **first LLM output that passes the oracle tests**.

### Why First Oracle-Passing Output?

**1. Deterministic and Reproducible**
- No arbitrary choices or randomness
- Same anchor every time you run the experiment
- Critical for reproducibility in research

**2. Behaviorally Correct**
- Anchor is guaranteed to be functionally correct (passes tests)
- Ensures we're comparing against a valid implementation
- Avoids canonicalizing to broken code

**3. Unbiased Selection**
- No cherry-picking "best" or "simplest" implementation
- Represents natural LLM output distribution
- First output is representative of model's default behavior

**4. Practical and Simple**
- No complex selection algorithm needed
- Fast: O(1) selection (stop at first passing output)
- Easy to explain and justify in paper

### Alternative Anchor Selection Strategies

| Strategy | Why Not Used |
|----------|--------------|
| **Random passing output** | Non-deterministic, hurts reproducibility |
| **Shortest passing output** | Biases toward terse code, may not be typical |
| **Most common output** | Requires clustering, adds complexity |
| **Human-written reference** | Not representative of LLM behavior |
| **Median complexity output** | Requires defining "complexity", subjective |

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

### Anchor Selection: First Oracle-Passing Output
✅ **Deterministic** (reproducible)  
✅ **Correct** (passes oracle tests)  
✅ **Unbiased** (no cherry-picking)  
✅ **Simple** (O(1) selection)

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

**1. First output may not be "typical"**
- Could be lucky/unlucky first sample
- Mitigation: With 20 runs, first passing output is representative
- Validation: Experiments show first output is not an outlier

**2. Anchor choice affects all downstream metrics**
- Different anchor → different distances
- Mitigation: Deterministic selection ensures consistency
- Future work: Multi-anchor analysis

**3. Assumes oracle tests are comprehensive**
- Anchor may pass tests but still be incorrect
- Mitigation: Contracts include multiple test cases
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

**Q: Why not use semantic similarity (e.g., CodeBERT embeddings)?**  
A: Embeddings are black-box and not reproducible. AST-based distance is transparent, deterministic, and sufficient for measuring structural repeatability.

**Q: Why not use the "best" output as anchor?**  
A: "Best" is subjective and introduces bias. First oracle-passing output is deterministic, unbiased, and representative of LLM behavior.

**Q: Does anchor choice affect conclusions?**  
A: We validated that first output is not an outlier. Future work could explore multi-anchor analysis, but deterministic selection is critical for reproducibility.
