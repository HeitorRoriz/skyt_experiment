# SKYT: PhD Research Roadmap

> **Transforming LLM Code Generation into a Publishable, Fundable, and Commercializable Research Program**

---

## Executive Summary

SKYT addresses a fundamental problem in LLM-assisted software engineering: **stochastic code generation produces non-repeatable outputs**, which is unacceptable for safety-critical domains. This roadmap outlines how to transform SKYT from an MVP into:

1. **Top-tier academic publications** (MSR, ICSE, FSE, TOSEM)
2. **PhD dissertation material**
3. **A fundable research program** (FAPESP, NSF, EU Horizon)
4. **A viable commercial product**

---

## Part 1: Research Contribution Framework

### 1.1 Core Research Questions

| ID | Question | Novelty | Venue Fit |
|----|----------|---------|-----------|
| **RQ1** | Can contract-based canonicalization transform stochastic LLM outputs into deterministic, repeatable code? | High | ICSE, FSE |
| **RQ2** | What is the trade-off between repeatability and implementation diversity? | Medium | MSR, TOSEM |
| **RQ3** | How do foundational properties (CFG, data flow, AST) correlate with semantic equivalence? | High | ICSE, PLDI |
| **RQ4** | Can monotonic AST transformations guarantee behavioral preservation? | High | FSE, OOPSLA |
| **RQ5** | What certification standards (DO-178C, MISRA) are achievable with LLM+SKYT pipelines? | Very High | ICSE-SEIP, ICSME |

### 1.2 Publication Strategy

```
Year 1 (2025-2026):
├── MSR 2026: "Measuring LLM Code Repeatability: Metrics and Benchmarks"
│   └── Focus: R_raw, R_canonical, methodology
│
├── Workshop: FORGE/ML4Code: "Contract-Driven LLM Canonicalization"
│   └── Focus: Early results, community feedback
│
Year 2 (2026-2027):
├── ICSE 2027: "SKYT: A Middleware for Deterministic LLM Code Generation"
│   └── Focus: Full system, transformations, industry validation
│
├── FSE 2027: "Monotonic Repair for LLM-Generated Code"
│   └── Focus: Theoretical foundations, proofs
│
Year 3 (2027-2028):
├── TOSEM Journal: "A Framework for Certifiable LLM-Assisted Development"
│   └── Focus: DO-178C compliance, case studies
│
├── PhD Dissertation Defense
```

### 1.3 Differentiation from Prior Work

| Existing Work | Gap | SKYT Contribution |
|--------------|-----|-------------------|
| CodeBERT, CodeT5 | No repeatability focus | First to measure R_raw vs R_canonical |
| CoPilot studies | Observe diversity, don't fix it | Active canonicalization pipeline |
| Program synthesis | Small programs, formal specs | Real-world LLM outputs, contracts |
| Code repair tools | Fix bugs | Fix non-determinism while preserving correctness |
| LLM evaluation benchmarks | Accuracy only | Repeatability as first-class metric |

---

## Part 2: Technical Roadmap

### 2.1 Core System (Current State)

```
✅ Implemented:
- 13 foundational properties for code equivalence
- Contract schema with oracle tests
- Canon anchoring system
- Property-driven transformers
- Three-tier metrics (R_raw, R_behavioral, R_structural)

🔧 Needs Improvement:
- Transformation success rate (currently ~70%)
- Cross-algorithm generalization
- Formal guarantees
```

### 2.2 Phase 1: Research Hardening (Weeks 1-8)

#### 2.2.1 Benchmark Suite

```python
# Target: 50+ contracts across 10 algorithm families
BENCHMARK_STRUCTURE = {
    "numerical": ["fibonacci", "factorial", "gcd", "lcm", "prime_check"],
    "search": ["binary_search", "linear_search", "interpolation"],
    "sort": ["merge_sort", "quick_sort", "bubble_sort", "insertion_sort"],
    "string": ["slugify", "palindrome", "anagram", "levenshtein"],
    "graph": ["dijkstra", "bfs", "dfs", "topological_sort"],
    "data_structures": ["lru_cache", "stack_ops", "queue_ops"],
    "validation": ["balanced_brackets", "email_validate", "json_parse"],
    "compression": ["run_length", "huffman_tree"],
    "crypto": ["caesar_cipher", "hash_function"],
    "embedded": ["crc32", "bitfield_ops", "register_map"],
}
```

#### 2.2.2 Formal Properties

Define and prove:
- **Monotonicity**: `d(transform(c), canon) ≤ d(c, canon)`
- **Idempotency**: `transform(transform(c)) = transform(c)`
- **Behavioral Preservation**: `oracle(c) = oracle(transform(c))`

#### 2.2.3 Statistical Framework

```
Experiment Design:
- N = 50 contracts
- K = 10 runs per temperature
- T = [0.0, 0.3, 0.5, 0.7, 1.0, 1.5]
- M = [gpt-4o, gpt-4o-mini, claude-3.5-sonnet, claude-3-haiku]
- Total: 50 × 10 × 6 × 4 = 12,000 LLM calls

Statistical Tests:
- Wilcoxon signed-rank for paired comparisons
- Kruskal-Wallis for cross-model comparisons
- Effect size via Cliff's delta
- Multiple comparison correction (Bonferroni)
```

### 2.3 Phase 2: Novel Contributions (Weeks 9-20)

#### 2.3.1 Foundational Property Theory

**Theorem 1 (Semantic Equivalence)**:
Two code fragments c₁, c₂ are semantically equivalent iff:
```
∀p ∈ P_foundational: dist(extract(c₁, p), extract(c₂, p)) = 0
```

**Theorem 2 (Monotonic Repair)**:
For any transformation t in SKYT's pipeline:
```
∀c, canon: d_structural(t(c), canon) ≤ d_structural(c, canon)
           ∧ oracle(c) = oracle(t(c))
```

#### 2.3.2 Canonicalization Algebra

Define an algebra of transformations:
```
T = {α-rename, normalize-loops, inline-constants, flatten-ifs, ...}

Properties:
- Associative: (t₁ ∘ t₂) ∘ t₃ = t₁ ∘ (t₂ ∘ t₃)
- Idempotent: t ∘ t = t
- Convergent: ∃n: tⁿ(c) = tⁿ⁺¹(c)
```

#### 2.3.3 Cross-LLM Analysis

Research question: Do different LLMs converge to the same canonical forms?

```
Hypothesis H1: canon(GPT(p)) ≈ canon(Claude(p)) for well-specified prompts
Hypothesis H2: Δ_rescue correlates with prompt specificity
Hypothesis H3: Temperature affects R_raw but not R_canonical
```

### 2.4 Phase 3: Industry Validation (Weeks 21-32)

#### 2.4.1 Partner Engagement

Target companies:
- **Aerospace**: Embraer, Boeing (DO-178C)
- **Automotive**: Continental, Bosch (MISRA)
- **Medical**: Philips, Siemens (IEC 62304)

#### 2.4.2 Case Study Design

```
Case Study Protocol:
1. Select real embedded codebase (partner-provided)
2. Extract 20 functions as contracts
3. Generate 100 outputs each (5 temps × 20 runs)
4. Measure R_raw, Δ_rescue, certification compliance
5. Interview engineers on acceptability thresholds
6. Quantify time saved vs manual review
```

#### 2.4.3 Certification Compliance Matrix

| Standard | Rule Count | Automatable | SKYT Coverage |
|----------|------------|-------------|---------------|
| NASA Power of 10 | 10 | 10 | 8/10 |
| MISRA C:2012 | 143 | ~100 | 40/100 |
| DO-178C | Variable | ~50 | 15/50 |
| AUTOSAR C++14 | 363 | ~200 | TBD |

---

## Part 3: Funding Strategy

### 3.1 Academic Funding

| Source | Amount | Focus | Deadline |
|--------|--------|-------|----------|
| FAPESP Regular | R$ 100-200K | PhD research | Rolling |
| FAPESP Thematic | R$ 1-2M | Multi-lab project | April 2026 |
| CNPq Universal | R$ 50-100K | Equipment, travel | March 2026 |
| NSF SHF Small | $500K | Core CS research | November |
| EU Horizon | €1-2M | Industry consortium | Varies |
| **DAAD Research Grant** | €1,200-1,800/month + travel | Sandwich PhD / full PhD stay in Germany; aligns with TU Munich, RWTH, or DFKI advisors | Nov & Apr cycles |

> **DAAD Fit:** Position SKYT as a binational research effort on certifiable AI engineering. Highlight collaboration with German labs focused on airborne or automotive safety (e.g., DLR, DFKI, TU Munich) and emphasize the embedded/firmware angle that matches Germany's industrial base.

### 3.2 Proposal Narrative

**Problem Statement**:
> LLM-assisted code generation is transforming software development, but its stochastic nature makes it incompatible with safety-critical domains that require reproducibility and auditability.

**Key Innovation**:
> SKYT introduces contract-based canonicalization that transforms stochastic LLM outputs into deterministic, repeatable code while preserving behavioral correctness.

**Broader Impact**:
> Enabling LLM use in aerospace, automotive, and medical software could accelerate development while maintaining certification compliance, impacting billions of lines of safety-critical code.

### 3.3 Budget Template

```
Personnel:
- PhD Student (3 years): $150K
- Postdoc (1 year): $80K
- Undergrad RAs: $20K

Equipment:
- GPU Cluster time (LLM experiments): $30K
- Cloud hosting (SaaS MVP): $10K

Travel:
- Conferences (3 years): $15K
- Industry visits: $10K

Other:
- LLM API costs: $20K
- Publication fees: $5K
- Software licenses: $5K

Total: ~$345K (3 years)
```

---

## Part 4: Commercialization Path

### 4.1 Business Model Evolution

```
Phase 1: Academic (Now - 2026)
├── Open source core engine
├── Free CLI tool
├── Academic papers establish credibility
└── Revenue: $0 (investment phase)

Phase 2: Developer Adoption (2026-2027)
├── SaaS playground (skyt.works)
├── Freemium model ($29-99/mo)
├── Community contracts repository
└── Revenue: $10-50K ARR

Phase 3: Enterprise (2027-2028)
├── Certification compliance packages
├── Custom restriction sets
├── On-premise deployment
├── Support SLAs
└── Revenue: $200K-1M ARR

Phase 4: Platform (2028+)
├── IDE integrations (VSCode, IntelliJ)
├── CI/CD pipeline plugins
├── Multi-language support
├── Partner ecosystem
└── Revenue: $1M+ ARR
```

### 4.2 Competitive Landscape

| Competitor | Focus | SKYT Advantage |
|------------|-------|----------------|
| GitHub Copilot | Productivity | Repeatability, certification |
| Amazon CodeWhisperer | AWS integration | Open core, vendor neutral |
| Tabnine | Privacy | Safety-critical focus |
| Cursor | UX | Contract-based quality |
| Codeium | Speed | Audit trails |

### 4.3 Go-to-Market Strategy

1. **Academic credibility**: Publish at top venues → industry awareness
2. **Open source adoption**: Developers use free CLI → organic growth
3. **Enterprise pilots**: Partner case studies → inbound leads
4. **Certification partnerships**: Integrate with DO-178C tools → enterprise sales

---

## Part 5: Immediate Action Items

### This Week

- [ ] **Test Suite**: Run existing Celery workflow tests
- [ ] **Benchmark**: Add 5 more contracts to reach 12 total
- [ ] **Metrics**: Validate R_raw, Δ_rescue calculations
- [ ] **Paper Draft**: Outline MSR 2026 submission

### This Month

- [ ] **Experiments**: Full temperature sweep on 12 contracts
- [ ] **Analysis**: Generate publication-quality figures
- [ ] **Documentation**: Complete API documentation
- [ ] **Demo**: Record screencast for funding proposals

### This Quarter

- [ ] **MSR Submission**: Full paper draft by deadline
- [ ] **FAPESP Proposal**: PhD project submission
- [ ] **Industry Contact**: Reach out to 3 aerospace/automotive companies
- [ ] **Production**: Deploy skyt.works MVP

---

## Part 6: Success Metrics

### Academic Success

| Metric | Target | Timeline |
|--------|--------|----------|
| Publications | 4 papers | 3 years |
| Citations | 50+ | 5 years |
| PhD completion | 1 defense | 4 years |
| Research funding | R$ 500K+ | 2 years |

### Commercial Success

| Metric | Target | Timeline |
|--------|--------|----------|
| GitHub stars | 1000 | 18 months |
| Monthly users | 500 | 2 years |
| Enterprise pilots | 3 | 2.5 years |
| ARR | $100K | 3 years |

### Technical Success

| Metric | Target | Timeline |
|--------|--------|----------|
| Contracts in benchmark | 50 | 6 months |
| Transformation success | 95% | 12 months |
| LLM models supported | 6 | 6 months |
| Certification rules | 100 | 18 months |

---

## Appendix: Key References

### Essential Reading

1. **LLM Code Generation**
   - "Evaluating Large Language Models Trained on Code" (Codex paper)
   - "Program Synthesis with Large Language Models" (Austin et al.)

2. **Program Repair**
   - "Automatic Patch Generation" (Le Goues et al.)
   - "Neural Program Repair" (Xia et al.)

3. **Software Certification**
   - DO-178C: Software Considerations in Airborne Systems
   - MISRA C:2012 Guidelines
   - NASA JPL Coding Standard

4. **Code Similarity**
   - "Clone Detection: A Survey" (Roy et al.)
   - "Semantic Code Clone Detection" (Svajlenko et al.)

### Datasets to Use

- CodeSearchNet
- HumanEval
- MBPP
- DS-1000
- EvalPlus

---

*Document Version: 1.0 | Created: 2025-11-27*
