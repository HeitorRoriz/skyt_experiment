# SKYT: Comprehensive LLM Code Repeatability Experiment System

## Research Question
**"Can prompt contracts and SKYT improve LLM-generated code repeatability?"**

This system implements a comprehensive pipeline to test whether contract-driven canonicalization can improve the repeatability of LLM-generated code through:
- **Contract-driven prompting** with explicit constraints and oracle tests
- **13 foundational properties** for semantic code equivalence
- **Three-tier repeatability metrics** (raw, behavioral, structural)
- **Canonical anchoring** and code transformation
- **Bell curve analysis** of distance variance from canonical forms

## System Architecture

### Core Pipeline
```
Contract → LLM → Canon → Transform → Metrics → Analysis
    ↓        ↓      ↓        ↓         ↓        ↓
Templates → Code → Anchor → Repair → R_raw → Bell Curve
                                   → R_behavioral
                                   → R_structural
```

### Key Components

#### 1. **Contract System** (`contract.py`)
- **Core Properties**: Task intent, constraints, language/environment
- **Oracle Requirements**: Acceptance test definitions and thresholds  
- **Normalization Rules**: Canonicalization policies
- **Repeatability Anchoring**: Canon signatures and distance metrics
- **Meta Properties**: Model specs, versioning, timestamps

#### 2. **13 Foundational Properties** (`foundational_properties.py`)
Defines code sameness through comprehensive semantic analysis:
1. **Control Flow Signature** - Topology of branches, loops, function calls
2. **Data Dependency Graph** - Variable dependency relationships
3. **Execution Paths** - Canonical execution path representation
4. **Function Contracts** - Input/output type relationships
5. **Complexity Class** - Algorithmic complexity (O-notation)
6. **Side Effect Profile** - Pure vs stateful operations
7. **Termination Properties** - Base cases, loop bounds
8. **Algebraic Structure** - Commutativity, associativity
9. **Numerical Behavior** - Precision, overflow handling
10. **Logical Equivalence** - Boolean expression normalization
11. **Normalized AST Structure** - Canonical AST representation
12. **Operator Precedence** - Explicit precedence normalization
13. **Statement Ordering** - Canonical statement sequence

#### 3. **Canon System** (`canon_system.py`)
- Creates canonical anchors from first compliant output
- Stores foundational properties alongside code
- Calculates distance metrics for variance analysis
- Provides persistent canon storage across experiments

#### 4. **Oracle System** (`oracle_system.py`)
- Algorithm-specific behavioral testing (Fibonacci, Merge Sort, Binary Search, etc.)
- Comprehensive test coverage: unit tests, edge cases, property tests
- Pass/fail determination for behavioral equivalence
- Quality gate enforcement with configurable thresholds

#### 5. **Code Transformer** (`code_transformer.py`)
- Transforms code to match canonical form using foundational properties
- Iterative repair with monotonic convergence
- Bounded transformations to preserve algorithmic intent
- Success/failure metrics for transformation attempts

#### 6. **Three-Tier Metrics** (`metrics.py`)
- **R_raw**: Raw LLM repeatability (identical string outputs)
- **R_behavioral**: Behavioral equivalence (oracle test results)
- **R_structural**: Structural equivalence (foundational properties)
- Distance variance calculations for bell curve analysis
- Entropy and diversity metrics

#### 7. **Bell Curve Analysis** (`bell_curve_analysis.py`)
- Plots distance distributions from canonical anchors
- Statistical analysis: normality tests, percentiles, variance
- Temperature comparison across experiments
- Research hypothesis evaluation with visual summaries

## Usage

### Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# Run single experiment
python main.py --contract fibonacci_basic --runs 5 --temperature 0.0

# Run temperature sweep
python main.py --contract fibonacci_basic --sweep --temperatures 0.0 0.5 1.0

# Run multiple contracts
python main.py --contract fibonacci_basic fibonacci_recursive merge_sort --runs 10
```

### Command Line Options
```
--contract        Contract ID(s) to test (default: fibonacci_basic)
--runs           Number of LLM runs per experiment (default: 5)
--temperature    LLM sampling temperature (default: 0.0)
--sweep          Run temperature sweep experiment
--temperatures   Temperatures for sweep (default: 0.0 0.5 1.0)
--templates      Path to contract templates (default: contracts/templates.json)
--output-dir     Output directory (default: outputs)
```

### Available Contracts
- **fibonacci_basic**: Iterative Fibonacci implementation
- **fibonacci_recursive**: Recursive Fibonacci implementation  
- **fibonacci_list**: Fibonacci sequence as list output
- **merge_sort**: Merge sort algorithm implementation
- **binary_search**: Binary search algorithm implementation

## Output Structure

### Generated Files
```
outputs/
├── experiment_summary.csv           # Aggregate results across all experiments
├── {experiment_id}.json            # Detailed experiment results
├── canon/                          # Canonical anchors storage
│   └── {contract_id}_canon.json    
├── analysis/                       # Plots and visualizations
│   ├── bell_curve_{experiment}.png # Distance distribution plots
│   ├── distribution_comparison.png # Temperature comparisons
│   ├── variance_trends.png         # Trend analysis
│   └── research_summary.png        # Comprehensive research summary
└── {sweep_id}_sweep.json          # Temperature sweep results
```

### Key Metrics in Results
- **R_raw**: Raw repeatability score (0.0-1.0)
- **R_behavioral**: Behavioral repeatability score (0.0-1.0)  
- **R_structural**: Structural repeatability score (0.0-1.0)
- **Distance Statistics**: Mean, std, variance of distances from canon
- **Transformation Success**: Rate of successful code repairs
- **Hypothesis Evaluation**: Whether SKYT improves repeatability

## Research Hypothesis Evaluation

The system automatically evaluates the research hypothesis:
> "SKYT improves LLM code repeatability through contract-driven canonicalization"

### Success Criteria
- **Structural Improvement > 10%**: R_structural - R_raw > 0.1
- **Consistent Improvement**: Improvement across multiple temperatures
- **Statistical Significance**: Bell curve analysis shows reduced variance

### Interpretation
- ✅ **HYPOTHESIS SUPPORTED**: Significant and consistent improvement
- ⚠️ **PARTIAL SUPPORT**: Some improvement but not consistent
- ❌ **NOT SUPPORTED**: No significant improvement detected

## Configuration

### Environment Variables
```bash
export OPENAI_API_KEY="your-api-key"           # Required: OpenAI API key
export SKYT_MODEL="gpt-4o-mini"               # Optional: Model to use
export SKYT_TEMPERATURE="0.0"                 # Optional: Default temperature
```

### Contract Templates
Contracts are defined in `contracts/templates.json` with:
- **Task Intent**: What the user wants (e.g., "generate Fibonacci numbers")
- **Constraints**: Implementation requirements (recursion, function names, etc.)
- **Oracle Requirements**: Acceptance tests and pass thresholds
- **Normalization Rules**: Canonicalization policies

## System Requirements

### Dependencies
- Python 3.8+
- OpenAI API access
- Required packages (see `requirements.txt`):
  - `openai>=1.0.0`
  - `numpy>=1.21.0`
  - `matplotlib>=3.5.0`
  - `seaborn>=0.11.0`
  - `scipy>=1.7.0`
  - `astor>=0.8.1`

### Hardware
- Minimal: Any system capable of running Python
- Recommended: Multi-core CPU for faster analysis
- Storage: ~100MB for results and plots per experiment

## Key Research Contributions

### 1. **Contract-Driven Canonicalization**
- First system to use explicit contracts for LLM code generation
- Deterministic canonical reference points instead of arbitrary first runs
- Comprehensive constraint specification and validation

### 2. **13 Foundational Properties Framework**
- Novel semantic equivalence definition beyond syntax matching
- Comprehensive coverage of all aspects of code sameness
- Property-based distance metrics for precise variance measurement

### 3. **Three-Tier Repeatability Metrics**
- **R_raw**: Measures pure LLM consistency
- **R_behavioral**: Measures functional correctness consistency  
- **R_structural**: Measures semantic structure consistency
- Eliminates artificial inflation from rescue systems

### 4. **Bell Curve Variance Analysis**
- Statistical analysis of code distance distributions
- Normality testing and variance characterization
- Visual research hypothesis evaluation

## Troubleshooting

### Common Issues
1. **Missing API Key**: Set `OPENAI_API_KEY` environment variable
2. **Import Errors**: Install requirements with `pip install -r requirements.txt`
3. **Empty Results**: Check contract templates exist and are valid JSON
4. **Transformation Failures**: Review contract constraints for feasibility

### Debug Mode
Add `--verbose` flag (if implemented) or check detailed JSON outputs for:
- LLM generation errors
- Oracle test failures  
- Transformation step details
- Distance calculation breakdowns

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Citation

If you use this system in your research, please cite:
```bibtex
@software{skyt_repeatability_2025,
  title={SKYT: Comprehensive LLM Code Repeatability Experiment System},
  author={[Your Name]},
  year={2025},
  url={https://github.com/[your-repo]/skyt_experiment}
}
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Acknowledgments

- OpenAI for providing the LLM API
- The research community for foundational work on code similarity and canonicalization
- Contributors to the AST manipulation and analysis libraries
