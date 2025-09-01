# SKYT Pipeline - Contract ↔ Canon ↔ Transform + ICE

A refactored LLM code generation evaluation framework with contract-driven canonicalization and unified repeatability metrics.

## Architecture

**Pipeline Order**: `ICE → Contract → Transform → LLM → Parse → Canon → Compliance → Retry → Log`

### Core Modules

- **`canon.py`** - Canonicalization with configurable policies
- **`compliance.py`** - Contract compliance checking  
- **`transform.py`** - LLM prompt building and repair hooks
- **`intent_capture.py`** - Developer/user intent extraction
- **`contract.py`** - Contract specification management
- **`normalize.py`** - Code parsing and extraction utilities
- **`llm.py`** - Unified LLM API interface
- **`matrix.py`** - Experiment scheduling and status tracking
- **`main.py`** - Main experiment runner
- **`delta.py`** - Code similarity analysis
- **`postprocess_repeatability.py`** - Metrics computation

## Setup

### Prerequisites

1. **Python 3.8+**
2. **OpenAI API Key** (set as environment variable)
3. **Required packages**: `pip install -r requirements.txt`

### Environment Variables

```bash
export OPENAI_API_KEY="your-api-key-here"
export SKYT_MODEL="gpt-4o-mini"  # Optional, defaults to gpt-4o-mini
export SKYT_TEMPERATURE="0.0"   # Optional, defaults to 0.0
```

## How to Run

### 1. Quick Smoke Test

Verify the pipeline works without API calls:

```bash
python smoke_test.py
```

Expected output:
```
SKYT Pipeline Smoke Tests
========================================
Testing canon.py...
OK Canon module working
...
SUCCESS: ALL SMOKE TESTS PASSED
```

### 2. Run Full Experiments

Execute the complete experiment matrix:

```bash
# Run all experiments
python -m src.main

# Run limited number of experiments
python -m src.main 10
```

This will:
- Load experiment matrix from `contracts/templates.json`
- Run experiments at T=0.0 and T=0.2
- Test both `with_contract` and `no_contract` modes
- Generate results in temperature-specific subdirectories

### 3. Generate Repeatability Reports

After experiments complete:

```bash
# Generate summary report
python -m src.postprocess_repeatability

# Or run directly
python src/postprocess_repeatability.py
```

## Output Structure

```
outputs/
├── with_contract_0.0/
│   └── results.csv
├── with_contract_0.2/
│   └── results.csv  
├── no_contract_0.0/
│   └── results.csv
├── no_contract_0.2/
│   └── results.csv
├── repeatability_summary.csv
├── hist_<prompt_id>_raw.csv
└── hist_<prompt_id>_canon.csv
```

## Key Metrics

- **R_raw** - Raw LLM repeatability (identical outputs before processing)
- **R_canon** - Canonical repeatability (after structural normalization)  
- **canon_coverage** - % with successful canonicalization
- **rescue_delta** - R_canon - R_raw (canonicalization benefit)

## Testing Protocol

### 1. Unit Tests (Smoke Tests)

```bash
python smoke_test.py
```

Tests individual modules:
- Canonicalization stability
- Code extraction robustness
- Contract compliance checking
- Intent capture functionality
- Logging and data persistence

### 2. Integration Tests

```bash
# Test single experiment
python -c "
from src.experiment import run_experiment
result = run_experiment('test', 'Generate fibonacci function', 'gpt-4o-mini', 0.0)
print('Contract pass:', result['contract_pass'])
"
```

### 3. End-to-End Validation

```bash
# Run 5 experiments and verify metrics
python -m src.main 5
python -m src.postprocess_repeatability
```

Verify:
- CSV files generated with all required fields
- Repeatability metrics computed correctly
- Canon signatures stable across runs
- Output directory structure correct

## Configuration

### Canonicalization Policy

Edit `src/config.py`:

```python
CANON_POLICY = CanonPolicy(
    strip_fences=True,      # Remove markdown fences
    strip_docstrings=True,  # Remove docstrings
    strip_comments=True,    # Remove comments
    normalize_ws=True,      # Normalize whitespace
    format_black=False,     # Black formatting (future)
    sort_imports=False,     # Import sorting (future)
    ident_normalize=True    # Normalize function names
)
```

### Experiment Templates

Edit `contracts/templates.json` to add new prompts:

```json
{
  "id": "my_prompt",
  "prompt": "Generate a Python function...",
  "enforce_function_name": "my_function",
  "oracle": "my_oracle"
}
```

## Troubleshooting

### Common Issues

1. **Unicode errors**: Use `chcp 65001` on Windows
2. **API key missing**: Set `OPENAI_API_KEY` environment variable
3. **Import errors**: Run from project root directory
4. **Empty results**: Check API key and network connectivity

### Debug Mode

Add debug prints to any module:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Development

### Adding New Modules

1. Create module in `src/`
2. Add imports to relevant files
3. Update smoke tests
4. Run full test suite

### Extending Metrics

Add new metrics to `postprocess_repeatability.py`:

```python
def compute_new_metric(records):
    # Your metric computation
    return metric_value
```

## Performance

- **Single experiment**: ~2-5 seconds (depends on LLM response time)
- **Full matrix (40 experiments)**: ~5-10 minutes
- **Memory usage**: <100MB for typical runs
- **Storage**: ~1MB per 1000 experiments

## License

See `LICENSE.txt`
