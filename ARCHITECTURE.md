# SKYT Experiment Architecture

## Overview
SKYT (Semantic Kernel Yielding Transformations) is a research framework for measuring LLM code generation repeatability through foundational property-based canonicalization.

## Core Research Question
**"Can prompt contracts and SKYT improve repeatability of LLM-generated code?"**

## Architecture Principles

### 1. **Foundational Property-Based Canonicalization**
- Code sameness defined by 13 foundational properties
- True semantic equivalence beyond surface syntax
- Contract-driven canonical form establishment

### 2. **Immutable Canon System**
- Single canonical form per prompt type
- Immutable once established (prevents artificial repeatability)
- Property-based signatures for deterministic comparison

### 3. **Monotonic Repair System**
- Property-based transformations only
- Repairs only proceed if they improve property matching
- Bounded by maximum steps to prevent infinite loops

### 4. **SPC-Style Statistical Analysis**
- Bell-shaped curve distributions for distance analysis
- Six Sigma quality control principles
- μ ± 3σ control limits for process capability

## System Components

### **Core Modules** (src/)
```
src/
├── contract.py          # Contract loading and validation
├── llm.py              # LLM API interface
├── normalize.py        # Code normalization pipeline
├── prompt_builder.py   # LLM prompt construction
└── config.py          # System configuration
```

### **Middleware** (src/middleware/)
```
middleware/
├── schema.py           # Data structures and constants
├── canon_anchor.py     # Immutable canonical form management
├── code_properties.py  # 13 foundational property extraction
├── property_repair.py  # Property-based code transformation
├── distance.py         # Property-based distance computation
├── contract_enforcer.py # Oracle compliance checking
├── pipeline.py         # Main experiment execution flow
├── logger.py           # Comprehensive audit logging
├── metrics.py          # Repeatability metrics computation
└── viz.py             # SPC-style visualizations
```

### **Runners** (src/runners/)
```
runners/
├── run_single.py       # Single prompt experiment
└── run_suite.py        # Full experiment suite
```

## Data Flow Architecture

### **Experiment Pipeline**
```
Contract → LLM → Normalize → Properties → Canon Check → Repair → Metrics
```

### **Detailed Flow**
1. **Load Contract**: JSON template with constraints
2. **LLM Generation**: Property-enhanced prompting
3. **Normalization**: Extract clean code
4. **Property Extraction**: 13 foundational properties
5. **Canon Management**: Establish/validate immutable canon
6. **Distance Computation**: Property-based distance measurement
7. **Repair (if needed)**: Property-based transformations
8. **Metrics Computation**: R_raw, R_anchor, rescue rates
9. **Visualization**: SPC bell curves and statistical analysis

## Foundational Properties (13 Core Properties)

### **Computational Structure**
1. **Control Flow Signature** - Branch/loop topology
2. **Data Dependency Graph** - Variable relationships
3. **Execution Paths** - Canonical path representation

### **Semantic Invariants**
4. **Function Contracts** - I/O relationships
5. **Complexity Class** - Algorithmic complexity
6. **Side Effect Profile** - Pure vs stateful
7. **Termination Properties** - Base cases, bounds

### **Mathematical Properties**
8. **Algebraic Structure** - Commutativity, associativity
9. **Numerical Behavior** - Precision, overflow
10. **Logical Equivalence** - Boolean normalization

### **Syntax Properties**
11. **Normalized AST Structure** - Canonical representation
12. **Operator Precedence** - Explicit precedence
13. **Statement Ordering** - Canonical sequence

## Key Metrics

### **Repeatability Measures**
- **R_raw**: Raw LLM repeatability (identical outputs)
- **R_anchor**: Canonical repeatability (property matches)
- **R_behavioral**: Functional correctness repeatability

### **Quality Measures**
- **Rescue Rate**: Successful repair percentage
- **μ_pre/μ_post**: Mean distances before/after repair
- **P_tau**: Fraction within tolerance threshold
- **σ_variance**: Statistical process control variance

## Scalability Features

### **Horizontal Scaling**
- Independent prompt processing
- Parallel experiment execution
- Modular component architecture

### **Vertical Scaling**
- Property-based caching
- Incremental canon establishment
- Bounded repair algorithms

### **Extensibility**
- Plugin-based property extractors
- Configurable repair strategies
- Multiple visualization backends

## Quality Assurance

### **Deterministic Guarantees**
- Property extraction is deterministic
- Canon establishment is immutable
- Distance computation is consistent

### **Monotonic Convergence**
- Repair only improves property matching
- Bounded iteration prevents infinite loops
- Early termination on perfect matches

### **Statistical Rigor**
- SPC-based quality control
- Bell curve distribution analysis
- Six Sigma process capability metrics

## Configuration

### **Contract Templates** (contracts/templates.json)
```json
{
  "id": "anchor_fib_v1",
  "prompt": "Generate Fibonacci function...",
  "enforce_function_name": "fibonacci",
  "requires_recursion": true,
  "oracle": "fibonacci20"
}
```

### **Execution Modes**
- **Contract Mode**: Full property-based canonicalization
- **Simple Mode**: Basic text-based comparison
- **Debug Mode**: Comprehensive logging and tracing

## Usage Examples

### **Single Experiment**
```bash
python main.py single --prompt-id anchor_fib_v1 --n 10
```

### **Full Suite**
```bash
python main.py suite --matrix contracts/templates.json
```

### **Custom Parameters**
```bash
python main.py single --prompt-id slugify_v1 --n 5 --tau 0.15 --temperature 0.2
```

## Output Structure

### **Logs** (outputs/logs/)
- `runs.csv` - Experiment run specifications
- `distances_pre.csv` - Pre-repair distances
- `distances_post.csv` - Post-repair distances
- `repairs.csv` - Repair operation records
- `metrics_summary.csv` - Aggregated metrics

### **Visualizations** (outputs/figs/)
- `pre_vs_post_overlay.png` - Distribution overlay
- `bell_curve_{prompt_id}.png` - SPC analysis per prompt
- `bar_pairs_R_anchor.png` - Repeatability comparisons
- `summary_dashboard.png` - Comprehensive metrics

### **Canonical Forms** (outputs/canon/)
```
canon/
└── {prompt_id}/
    ├── canon.json          # Canon metadata
    ├── canon_signature.txt # Property signature
    ├── canon_code.txt      # Canonical code
    └── canon_properties.json # Foundational properties
```

## Research Impact

### **Novel Contributions**
1. **Foundational Property Framework**: 13-property semantic equivalence
2. **Immutable Canon System**: Prevents artificial repeatability inflation
3. **Property-Based Repair**: Semantic transformations vs syntax fixes
4. **SPC Integration**: Six Sigma quality control for LLM outputs

### **Measurable Outcomes**
- True LLM repeatability measurement
- Semantic canonicalization effectiveness
- Contract-driven quality improvement
- Statistical process control for AI systems

This architecture provides a robust, scalable foundation for measuring and improving LLM code generation repeatability through rigorous semantic analysis and statistical quality control.
