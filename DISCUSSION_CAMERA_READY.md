# Discussion Points for Camera-Ready Revision

This document addresses key reviewer concerns for the MSR 2026 camera-ready revision.

---

## 1. Clarification: SKYT's Scope and Determinism

### Reviewer Concern
> "The approach does not make generation deterministic."

### Our Response

**SKYT does not claim to make LLM generation deterministic.** This would require modifying the LLM itself, which is:
- Outside the scope of middleware research
- Controlled exclusively by LLM providers (OpenAI, Anthropic, etc.)
- Impossible to achieve even with `temperature=0` (which still produces variance)

### What SKYT Actually Does

SKYT operates as **deterministic post-processing** of **non-deterministic LLM outputs**:

```
┌─────────────────────────────────────────────────────────────┐
│  Prompt: "Implement fibonacci(n)"                           │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  LLM Generation (Non-Deterministic, Outside Our Control)    │
│  - Temperature, sampling, model updates cause variance      │
│  - We measure this as R_raw (baseline repeatability)        │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
   Output 1          Output 2          Output 3
   (for loop)        (while loop)      (recursion)
   Syntactically     Different         Different
   Different         Syntax            Approach
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  SKYT Canonicalization (Deterministic, Our Contribution)    │
│  - Contract enforcement                                      │
│  - Property-based transformation                            │
│  - Monotonic AST repair                                     │
│  - We measure this as Δ_rescue (improvement)                │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
                  Canonical Output
                  (Identical Form)
                  - We measure this as R_structural
```

### Analogy

**SKYT is like a compiler**: A compiler doesn't make programmers deterministic—it transforms diverse source code (written by different programmers with different styles) into consistent machine code. Similarly, SKYT transforms diverse LLM outputs into canonical forms.

### Empirical Evidence

Our experiments demonstrate this three-layer architecture:

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **R_raw** | 0.4-0.6 | LLM is non-deterministic (baseline) |
| **Δ_rescue** | 0.2-0.8 | SKYT's transformation effectiveness (contribution) |
| **R_structural** | 0.85-1.0 | Post-transformation repeatability (outcome) |

**The value proposition**: Given that LLMs are inherently non-deterministic, SKYT provides a middleware layer to achieve repeatable canonical outcomes for audit and compliance contexts.

### Revised Framing

**Replace "same prompt, same code" with:**
> "SKYT achieves repeatable canonical outcomes from non-deterministic LLM generation through contract-driven post-processing."

**Key messaging:**
- SKYT is **middleware** (operates post-generation)
- LLM non-determinism is **given** (not our problem to solve)
- Canonical transformation is **our contribution** (what we measure)

---

## 2. Relationship to N-Version Programming

### Reviewer Concern
> "N-Version Programming suggests implementation diversity reduces common-mode failures. By forcing all outputs to converge to a single implementation, SKYT may actually remove the layer of safety provided by the probabilistic nature of LLMs."

### Our Response

Recent work on **Galápagos** [Ron et al., 2024, arXiv:2408.09536] demonstrates that LLM-generated diversity can enhance fault tolerance through N-Version Programming. This raises an important question: does SKYT's convergence approach sacrifice the safety benefits of implementation diversity?

**We argue these approaches serve complementary goals in different contexts.**

### SKYT: Repeatability for Audit and Compliance

**Target contexts:**
- **Certification requirements** (DO-178C, ISO 26262): Need deterministic, auditable artifacts
- **CI/CD pipelines**: Need reproducible builds for change tracking
- **Code review**: Need stable references for human inspection
- **Regulatory compliance**: Need to demonstrate "same input → same output"

**Goal**: Eliminate variance for traceability and auditability

**Mechanism**: Contract-driven canonicalization to single reference implementation

### Galápagos: Diversity for Fault Tolerance

**Target contexts:**
- **Compiler miscompilations**: Protect against optimizer bugs
- **Side-channel attacks**: Diverse execution paths prevent timing attacks
- **Common-mode failures**: Multiple implementations vote to detect anomalies

**Goal**: Maximize variance for robustness

**Mechanism**: Generate and verify diverse equivalent implementations, assemble N-Version binaries

### Complementary, Not Contradictory

These approaches address **different phases of the software lifecycle**:

```
Development Phase          Deployment Phase
─────────────────         ──────────────────
Use SKYT                  Use Galápagos
↓                         ↓
Repeatable outputs        Diverse variants
↓                         ↓
Code review               Runtime voting
Change tracking           Fault detection
Compliance audit          Anomaly detection
```

**They are not mutually exclusive.** A complete workflow could:

1. **Development**: Use SKYT to ensure repeatable, auditable code generation
2. **Review**: Audit the canonical implementation for correctness
3. **Deployment**: Use Galápagos to generate verified diverse variants for N-Version execution

### Key Distinctions

| Dimension | SKYT | Galápagos |
|-----------|------|-----------|
| **Goal** | Repeatability | Diversity |
| **Metric** | R_structural (maximize) | Variant uniqueness (maximize) |
| **Use Case** | Audit, compliance, CI/CD | Fault tolerance, security |
| **Output** | Single canonical form | Multiple diverse variants |
| **Verification** | Behavioral equivalence to contract | Semantic equivalence via formal verification |
| **Lifecycle Phase** | Development, review | Deployment, runtime |

### Future Work: Hybrid Approaches

An interesting direction for future research:

1. Use SKYT to establish a **canonical reference** (auditable, reviewable)
2. Use Galápagos to generate **verified diverse variants** from that reference
3. Deploy N-Version system with **both repeatability and diversity**

This would provide:
- **Traceability**: Canonical reference for audit
- **Robustness**: Diverse variants for fault tolerance
- **Formal guarantees**: All variants verified equivalent

### Addressing the Safety Concern

The reviewer's concern about "removing safety" assumes that:
- LLM variance is inherently beneficial (true for fault tolerance)
- All contexts benefit from variance (false—audit contexts require repeatability)

**Our position**: Different contexts have different requirements. SKYT targets contexts where repeatability is a requirement, not a limitation. For contexts requiring diversity (e.g., safety-critical runtime systems), Galápagos-style approaches are more appropriate.

---

## 3. Text Changes for Camera-Ready

### Abstract
```markdown
BEFORE:
"We present SKYT, a middleware that enables 'same prompt, same code' 
repeatability for LLM-generated software."

AFTER:
"We present SKYT, a middleware that achieves repeatable canonical outputs 
from non-deterministic LLM generation through contract-driven post-processing."
```

### Introduction (Add Scope Clarification)
```markdown
**Scope Clarification**: SKYT does not make LLM generation itself 
deterministic—that is controlled by model providers and remains inherently 
stochastic even at temperature=0. Instead, SKYT operates as a deterministic 
post-processor: given diverse LLM outputs (which may differ syntactically), 
SKYT transforms them into a single canonical form (which is identical). 

This distinction is captured in our three-tier metrics:
- R_raw (0.4-0.6): measures LLM's inherent non-determinism (baseline)
- Δ_rescue (0.2-0.8): measures SKYT's transformation effectiveness (contribution)
- R_structural (0.85-1.0): measures post-transformation repeatability (outcome)

The key insight: deterministic outcomes can be achieved from non-deterministic 
inputs through systematic post-processing, analogous to how compilers transform 
diverse source code into consistent machine code.
```

### Discussion Section (Add N-Version Programming Comparison)
```markdown
## Relationship to N-Version Programming

Recent work on Galápagos [Ron et al., 2024] demonstrates that LLM-generated 
diversity can enhance fault tolerance through N-Version Programming. This 
raises an important question: does SKYT's convergence approach sacrifice 
the safety benefits of implementation diversity?

We argue these approaches serve complementary goals:

**SKYT targets audit and compliance contexts** where repeatability is a 
requirement (e.g., DO-178C certification, CI/CD pipelines, regulatory 
compliance). In these settings, deterministic canonical outputs enable 
code review, change tracking, and traceability.

**Galápagos targets fault-tolerance contexts** where diversity protects 
against compiler bugs, side-channel attacks, and common-mode failures. 
Here, multiple diverse implementations vote to detect anomalies at runtime.

**These are not mutually exclusive.** A complete workflow could use SKYT 
during development (for repeatable review and audit) and Galápagos for 
deployment (for runtime diversity and fault tolerance). The key insight 
is that repeatability and diversity serve different phases of the software 
lifecycle.

Future work could explore hybrid approaches: using SKYT to establish a 
canonical reference (auditable), then generating verified diverse variants 
(à la Galápagos) for N-Version deployment. This would provide both 
traceability and robustness with formal guarantees.
```

### Limitations Section (Add)
```markdown
## Limitations

**Single Canonical Form**: SKYT converges all outputs to a single canonical 
implementation. This is appropriate for audit/compliance contexts but may 
not be suitable for fault-tolerance scenarios where implementation diversity 
is beneficial (e.g., N-Version Programming [Ron et al., 2024]). Different 
contexts have different requirements: SKYT prioritizes repeatability over 
diversity.

**LLM Non-Determinism**: SKYT operates post-generation and cannot control 
LLM sampling behavior. While we achieve high R_structural (0.85-1.0), 
perfect repeatability (1.0) depends on the LLM producing outputs within 
SKYT's transformation capabilities. Future work could explore tighter 
LLM integration (e.g., constrained decoding).
```

---

## References

Ron, J., Gaspar, D., Cabrera-Arteaga, J., Baudry, B., & Monperrus, M. (2024). 
Galápagos: Automated N-Version Programming with LLMs. arXiv:2408.09536.
