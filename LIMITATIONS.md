# Limitations and Threats to Validity

This document outlines the limitations of the SKYT approach and threats to the validity of our experimental results, following best practices for empirical software engineering research.

---

## 1. Scope Limitations

### 1.1 Single-File Programs Only

**Limitation:** SKYT currently only handles single-file Python programs.

**Impact:**
- Cannot evaluate repeatability for multi-file projects
- Real-world software often spans multiple modules
- Inter-module dependencies not considered

**Rationale:**
- Single-file scope allows controlled experiments
- Focuses on algorithmic repeatability (core research question)
- Multi-file support is engineering work, not fundamental limitation

**Future Work:**
- Extend to multi-file projects with import resolution
- Investigate repeatability at module/package level
- Study cross-file canonicalization strategies
- **See MULTI_FILE_ROADMAP.md for comprehensive 12-week implementation plan**

### 1.2 Algorithmic Tasks Only

**Limitation:** Evaluated on 12 algorithmic contracts (sorting, searching, math, string processing).

**Impact:**
- Results may not generalize to other domains (web apps, data processing, ML pipelines)
- Algorithmic tasks have clear correctness criteria (oracle tests)
- May not capture complexity of real-world software

**Rationale:**
- Algorithmic tasks have objective correctness measures
- Enables rigorous oracle-based validation
- Standard benchmark in code generation research

**Future Work:**
- Evaluate on web development tasks (REST APIs, UI components)
- Study data processing pipelines (ETL, data cleaning)
- Investigate open-ended tasks without clear oracles

### 1.3 Simple Contracts (Minimal Constraints)

**Limitation:** Current contracts specify minimal constraints (function names, basic types, oracle tests). In embedded/firmware engineering, contracts are significantly stricter.

**Impact:**
- "Easy" contracts (is_prime, factorial, gcd) show 90%+ baseline repeatability
- Little room for SKYT improvement when LLMs already produce consistent outputs
- Results represent a **lower bound** on SKYT's potential benefit

**Rationale:**
- Simple contracts validate framework correctness
- Isolates repeatability measurement from constraint complexity
- Provides baseline for future strict contract evaluation

**Embedded SW Reality:**
Real-world embedded contracts include:
- Memory constraints (no heap, max stack depth)
- Hardware register mappings (fixed variable names → addresses)
- Forbidden patterns (no recursion, no floating point)
- Safety-critical patterns (mandatory null checks, bounds checks)
- Timing constraints (max execution time, ISR requirements)

**Prediction:**
As contracts become stricter, even simple algorithms will require more transformation:
- Current: is_prime at 99.3% baseline → +0.7% improvement
- With strict rules: is_prime at ~60% baseline → +25-35% improvement (predicted)

**Future Work:**
- Create MISRA-C inspired strict contract suite
- Evaluate on real embedded firmware patterns
- Demonstrate SKYT's full industrial potential

**See CONTRACT_DESIGN.md for detailed contract extensibility discussion.**

### 1.4 Python Only

**Limitation:** SKYT is implemented for Python only.

**Impact:**
- Language-specific AST parsing and transformations
- Results may not generalize to other languages
- Different languages have different idioms and patterns

**Rationale:**
- Python is dominant in LLM code generation research
- Simplifies implementation and evaluation
- Proof-of-concept for canonicalization approach

**Future Work:**
- Port to other languages (JavaScript, Java, C++)
- Study language-specific canonicalization patterns
- Compare repeatability across languages

---

## 2. Threats to Internal Validity

### 2.1 Oracle Test Completeness

**Threat:** Oracle tests may not fully capture correctness.

**Description:**
- Contracts include 5-10 test cases per task
- May miss edge cases or corner cases
- Code passing tests could still be incorrect

**Mitigation:**
- Test cases designed to cover typical inputs, edge cases, and error conditions
- Multiple test cases per contract (not just happy path)
- Manual inspection of generated code during development

**Residual Risk:**
- Some incorrect implementations may pass tests
- Affects anchor selection (first passing output may be wrong)
- Acknowledged limitation in paper

### 2.2 Transformation Completeness

**Threat:** SKYT transformations may not rescue all rescuable outputs.

**Description:**
- Transformation system uses 13 foundational properties
- May miss valid transformations not covered by these properties
- Conservative approach may leave some outputs untransformed

**Mitigation:**
- Properties based on semantic equivalence literature
- Iterative refinement during development
- Transformation success rate reported as metric

**Residual Risk:**
- Δ_rescue may underestimate true canonicalization potential
- Some outputs incorrectly classified as "unrepairable"
- Future work: expand property set

### 2.3 Distance Metric Validity

**Threat:** Normalized Levenshtein distance on AST may not perfectly capture semantic similarity.

**Description:**
- Treats all AST edits equally (e.g., `+` to `-` same cost as variable rename)
- May not capture deep semantic equivalences
- Normalization may not be perfect for very different code lengths

**Mitigation:**
- AST-based distance focuses on structure, not formatting
- Oracle tests ensure behavioral correctness
- Standard metric in code similarity research

**Residual Risk:**
- Semantically equivalent code may have high distance
- Distance is structural approximation of semantic similarity
- See DISTANCE_METRICS.md for detailed discussion

---

## 3. Threats to External Validity

### 3.1 Model Selection

**Threat:** Results may not generalize to all LLMs.

**Description:**
- Evaluated on 3 models: GPT-4o-mini, GPT-5.2, Claude-Sonnet-4.5
- All are frontier models (late 2024/early 2025)
- May not represent smaller or older models

**Mitigation:**
- Cross-model validation (OpenAI + Anthropic)
- Multiple model sizes/capabilities
- Temperature sweep (0.0 to 1.0) captures variance

**Residual Risk:**
- Results may differ for open-source models (Llama, CodeLlama)
- Future models may have different repeatability characteristics
- Model drift over time (API updates)

### 3.2 Task Selection

**Threat:** 12 algorithmic contracts may not represent all code generation tasks.

**Description:**
- Focus on well-defined algorithmic problems
- May not capture complexity of real-world software
- Tasks chosen for clear correctness criteria

**Mitigation:**
- Diverse task set: sorting, searching, math, string processing, data structures
- Range of difficulty (simple to moderate complexity)
- Standard benchmarks in code generation research

**Residual Risk:**
- Results may not generalize to open-ended tasks
- Real-world code often lacks clear specifications
- See Section 1.2 for detailed discussion

### 3.3 Prompt Engineering

**Threat:** Results may be sensitive to prompt wording.

**Description:**
- Contracts use specific prompt templates
- Different prompts may yield different repeatability
- Prompt engineering is known to affect LLM behavior

**Mitigation:**
- Prompts designed to be clear and unambiguous
- Consistent prompt structure across all contracts
- Includes constraints and normalization rules

**Residual Risk:**
- Different prompt styles may yield different results
- Prompt sensitivity is inherent to LLM behavior
- Future work: study prompt robustness

---

## 4. Threats to Construct Validity

### 4.1 Repeatability Definition

**Threat:** Our definition of repeatability may not align with all use cases.

**Description:**
- We measure structural similarity (AST-based)
- Other definitions: behavioral equivalence, semantic similarity, user preference
- Repeatability is multi-faceted concept

**Mitigation:**
- Three-tier metrics: R_raw, R_behavioral, R_structural
- Oracle tests ensure behavioral correctness
- Clear definition in paper (structural repeatability)

**Residual Risk:**
- Different stakeholders may care about different aspects
- Structural repeatability is one lens, not the only lens
- Future work: user studies on preferred implementations

### 4.2 Anchor Selection Strategy

**Limitation:** "First contract-adherent, oracle-passing output" is pragmatic but not optimal.

**Description:**
- Current strategy: Select first output that passes both contract adherence and oracle tests
- While deterministic and objective, "first" is a pragmatic choice among valid outputs
- Temporal order has no inherent theoretical superiority over alternatives (last, shortest, median complexity)
- The anchor quality directly affects all downstream metrics and canonicalization effectiveness
- A suboptimal anchor may lead to unnecessary transformations or missed canonicalization opportunities

**Why This Matters:**
- **Anchor quality affects repeatability metrics:** A poorly structured anchor increases distances to other valid implementations
- **Transformation efficiency:** Better anchors require fewer transformations to reach
- **Representativeness:** The anchor should ideally represent the "typical" or "best" valid implementation, not just the first one encountered

**Current Justification:**
- Deterministic and reproducible (same outputs → same anchor)
- Objective (no subjective judgment in selection)
- Efficient (O(1) selection, no need to evaluate all outputs)
- Transparent (easy to explain and implement)
- Unbiased (no cherry-picking for favorable results)

**Future Work: Quality-Based Anchor Selection**

A more principled approach would select the **best** contract-adherent, oracle-passing output based on a multi-dimensional quality score:

**Proposed Quality Scoring System:**

1. **Structural Simplicity (30% weight)**
   - Cyclomatic complexity (fewer branches = simpler)
   - Nesting depth (shallower = more readable)
   - Lines of code (more concise = better, within reason)
   - AST node count (smaller tree = simpler structure)

2. **Code Quality Metrics (25% weight)**
   - Pythonic idioms usage (list comprehensions, generators, context managers)
   - Standard library usage (prefer built-ins over manual implementations)
   - Naming clarity (descriptive variable/function names)
   - Absence of code smells (magic numbers, deep nesting, long functions)

3. **Canonicalization Potential (25% weight)**
   - Distance to other valid outputs (lower mean distance = more central)
   - Transformation coverage (how many outputs can reach this anchor)
   - Property satisfaction (how many foundational properties already satisfied)

4. **Robustness (20% weight)**
   - Edge case handling (explicit checks vs implicit assumptions)
   - Error handling (try/except, validation)
   - Oracle test margin (how "safely" it passes tests)

**Selection Algorithm:**
```python
def select_best_anchor(valid_outputs):
    """Select anchor with highest quality score"""
    scores = []
    for output in valid_outputs:
        score = (
            0.30 * structural_simplicity(output) +
            0.25 * code_quality(output) +
            0.25 * canonicalization_potential(output, valid_outputs) +
            0.20 * robustness(output)
        )
        scores.append((score, output))
    
    # Return output with highest score
    return max(scores, key=lambda x: x[0])[1]
```

**Benefits of Quality-Based Selection:**
- **Better anchor quality:** Selects structurally simpler, more canonical implementations
- **Improved canonicalization:** Better anchor → easier transformations → higher Δ_rescue
- **More representative:** Anchor reflects "ideal" implementation, not just first valid one
- **Theoretically justified:** Selection based on measurable quality criteria, not temporal order
- **Still deterministic:** Same outputs → same scores → same anchor (reproducible)

**Implementation Considerations:**
- Requires defining and validating quality metrics
- More computationally expensive (O(n) vs O(1) selection)
- Weights may need tuning per domain (algorithms vs web vs data processing)
- Risk of overfitting to specific quality metrics

**Research Questions:**
- How much does anchor quality affect Δ_rescue and repeatability metrics?
- What quality dimensions matter most for canonicalization effectiveness?
- How stable are quality-based selections across different contracts?
- Does quality-based selection generalize across domains and LLMs?

**Mitigation for Current Work:**
- Acknowledge "first" is pragmatic, not optimal
- Validate that first output is not an outlier (report statistics)
- Emphasize determinism and objectivity over optimality
- Position quality-based selection as important future work

**Residual Risk:**
- Current anchor may not be optimal for canonicalization
- Metrics may underestimate SKYT's potential with better anchors
- Results are conservative (likely lower bound on effectiveness)

### 4.3 Canonicalization Success

**Threat:** Δ_rescue may not fully capture SKYT's value.

**Description:**
- Δ_rescue measures improvement in repeatability
- Doesn't capture other benefits: debugging, code review, maintenance
- Single metric may oversimplify complex phenomenon

**Mitigation:**
- Multiple metrics reported (R_raw, R_anchor, R_structural, Δ_rescue)
- Transformation success rate and coverage reported
- Qualitative analysis of transformations

**Residual Risk:**
- Quantitative metrics may miss qualitative benefits
- Long-term maintenance value not measured
- Future work: longitudinal studies

---

## 5. Model Drift and Reproducibility

### 5.1 API Model Drift

**Threat:** LLM APIs may change over time, affecting reproducibility.

**Description:**
- OpenAI and Anthropic update models periodically
- API endpoints may return different results over time
- Model versions may be deprecated

**Mitigation:**
- Use specific model versions (e.g., `gpt-5.2-2025-12-11`)
- Document exact model identifiers in results
- Timestamp all experiments
- Archive raw outputs for replication

**Residual Risk:**
- Perfect reproducibility not guaranteed with API models
- Model versions may become unavailable
- Recommendation: Use versioned models when available

### 5.2 Stochastic Behavior

**Threat:** LLM outputs are stochastic, even at temperature=0.0.

**Description:**
- Same prompt may yield different outputs across runs
- Temperature=0.0 reduces but doesn't eliminate variance
- Affects exact replication of results

**Mitigation:**
- 20 runs per contract/temperature to capture distribution
- Statistical tests (Wilcoxon) account for variance
- Report mean ± std for all metrics

**Residual Risk:**
- Exact outputs not reproducible
- Aggregate statistics should be stable
- Standard limitation in LLM research

---

## 6. Implementation Limitations

### 6.1 Transformation Performance

**Limitation:** Transformation system may be slow for large codebases.

**Description:**
- AST parsing and property extraction are O(n) in code size
- Pairwise distance calculation is O(n²) in number of outputs
- May not scale to hundreds of outputs

**Mitigation:**
- Optimized for typical use case (20 outputs per contract)
- Caching of AST representations
- Parallel processing possible (not implemented)

**Future Work:**
- Optimize for large-scale experiments
- Incremental canonicalization
- Approximate distance metrics for scalability

### 6.2 Property Coverage

**Limitation:** 13 foundational properties may not cover all equivalences.

**Description:**
- Properties based on literature review and empirical observation
- May miss domain-specific equivalences
- Conservative approach (only apply safe transformations)

**Mitigation:**
- Properties cover common patterns (loops, conditionals, expressions)
- Extensible architecture (easy to add new properties)
- Transformation success rate reported

**Future Work:**
- Expand property set based on empirical analysis
- Domain-specific properties (e.g., web, data science)
- Machine learning to discover new properties

---

## 7. Generalizability

### 7.1 Beyond Code Generation

**Limitation:** SKYT designed for code generation, may not apply to other domains.

**Description:**
- Canonicalization assumes code has structural patterns
- May not apply to natural language, images, etc.
- Domain-specific approach

**Future Work:**
- Explore canonicalization in other domains
- Study repeatability in multi-modal generation
- Generalize principles beyond code

### 7.2 Human-Written Code

**Limitation:** SKYT targets LLM-generated code, not human code.

**Description:**
- Human code may have different diversity patterns
- Canonicalization may not be useful for human code review
- Different use case than LLM output

**Observation:**
- SKYT could apply to human code (e.g., code review, plagiarism detection)
- Not primary use case in this work
- Future work: human code canonicalization

---

## 8. Ethical Considerations

### 8.1 Energy Consumption

**Concern:** Running 3,600 LLM calls consumes energy.

**Mitigation:**
- Necessary for rigorous evaluation
- Relatively small scale compared to model training
- Results enable more efficient LLM use in practice

### 8.2 API Costs

**Concern:** Experiments require paid API access.

**Mitigation:**
- Total cost ~$16.50 (affordable for research)
- Replication package includes raw outputs (no need to re-run)
- Open-source implementation for community use

---

## Summary

SKYT is a **proof-of-concept** for canonicalization-based repeatability improvement in LLM code generation. Key limitations:

1. **Scope:** Single-file Python programs, algorithmic tasks
2. **Generalizability:** 3 models, 12 contracts, may not represent all scenarios
3. **Metrics:** Structural distance approximates semantic similarity
4. **Reproducibility:** API model drift and stochastic behavior

These limitations are **acknowledged and mitigated** where possible. They represent opportunities for future work rather than fundamental flaws in the approach.

---

## For Reviewers

We have designed SKYT with these limitations in mind:

- **Transparent:** All limitations documented
- **Mitigated:** Where possible, we reduce threats (cross-model validation, statistical tests, multiple metrics)
- **Realistic:** We acknowledge what SKYT can and cannot do
- **Extensible:** Architecture supports future improvements

The core contribution—**canonicalization improves LLM code repeatability**—remains valid within the stated scope.
