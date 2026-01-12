# Cross-Model Support for Camera-Ready Experiments

## Overview

SKYT now supports cross-model experiments to address reviewer concerns about "single model" evaluation.

## Supported Models

### OpenAI Models
- `gpt-4o-mini` (default)
- `gpt-4o`
- `o1-preview`
- `o1-mini`

### Anthropic Models
- `claude-3-5-sonnet-20241022` (Claude 3.5 Sonnet)
- `claude-3-opus-20240229` (Claude 3 Opus)
- `claude-3-sonnet-20240229` (Claude 3 Sonnet)

## Installation

### OpenAI Only (Default)
```bash
pip install -r requirements.txt
export OPENAI_API_KEY="your-key-here"
```

### With Anthropic Support
```bash
pip install -r requirements.txt
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

## Usage

### Single Model Experiment
```bash
# Using GPT-4o-mini (default)
python main.py --contract fibonacci_basic --runs 20 --temperature 0.5

# Using Claude 3.5 Sonnet
python main.py --contract fibonacci_basic --runs 20 --temperature 0.5 --model claude-3-5-sonnet-20241022
```

### Cross-Model Comparison
```bash
# Run with GPT-4o-mini
python main.py --contract fibonacci_basic --runs 20 --temperature 0.5 --model gpt-4o-mini --output-dir outputs/gpt4o-mini

# Run with Claude 3.5 Sonnet
python main.py --contract fibonacci_basic --runs 20 --temperature 0.5 --model claude-3-5-sonnet-20241022 --output-dir outputs/claude-3.5-sonnet
```

### Temperature Sweep with Multiple Models
```bash
# GPT-4o-mini sweep
python main.py --contract fibonacci_basic --sweep --temperatures 0.0 0.3 0.5 0.7 1.0 --runs 20 --model gpt-4o-mini

# Claude 3.5 Sonnet sweep
python main.py --contract fibonacci_basic --sweep --temperatures 0.0 0.3 0.5 0.7 1.0 --runs 20 --model claude-3-5-sonnet-20241022
```

## Implementation Details

### Provider Detection
The `LLMClient` automatically detects the provider based on model name:
- Models starting with `gpt-` or `o1-` → OpenAI
- Models starting with `claude-` → Anthropic

### Unified Interface
Both providers use the same `generate_code(prompt, temperature)` interface:
```python
from src.llm_client import LLMClient

# OpenAI
client_openai = LLMClient(model="gpt-4o-mini")
code = client_openai.generate_code("Write a fibonacci function", temperature=0.5)

# Anthropic
client_anthropic = LLMClient(model="claude-3-5-sonnet-20241022")
code = client_anthropic.generate_code("Write a fibonacci function", temperature=0.5)
```

### Code Extraction
Both providers return code wrapped in markdown blocks. The `_extract_python_code()` method handles:
- ```python\n...\n``` blocks
- ```\n...\n``` blocks
- Raw text (fallback)

## Experimental Design for Camera-Ready

### Recommended Cross-Model Experiments

**12 contracts × 2 models × 5 temperatures × 20 runs = 2,400 LLM calls**

**Models:**
1. GPT-4o-mini (baseline)
2. Claude-3.5-Sonnet (cross-model validation)

**Temperatures:**
- 0.0 (deterministic)
- 0.3 (low variance)
- 0.5 (moderate variance)
- 0.7 (high variance)
- 1.0 (maximum variance)

**Contracts:**
1. fibonacci_basic
2. fibonacci_recursive
3. slugify
4. balanced_brackets
5. gcd
6. binary_search
7. lru_cache
8. merge_sort
9. quick_sort
10. factorial
11. is_palindrome
12. is_prime

### Expected Outcomes

**Research Questions:**
1. Does SKYT improve repeatability across different LLM providers?
2. Do different models show different R_raw baselines?
3. Is Δ_rescue consistent across models?
4. Does R_structural converge regardless of model?

**Hypothesis:**
SKYT's canonicalization should work regardless of LLM provider, showing:
- Model-specific R_raw (different baselines)
- Consistent Δ_rescue (transformation effectiveness)
- High R_structural across models (canonical convergence)

## Files Modified

### Core Changes
- `src/llm_client.py` - Added multi-provider support
- `src/comprehensive_experiment.py` - Added model parameter
- `main.py` - Added --model CLI argument
- `requirements.txt` - Added anthropic package

### New Files
- `CROSS_MODEL_SUPPORT.md` - This documentation

## Testing

### Verify OpenAI Support
```bash
python -c "from src.llm_client import LLMClient; c = LLMClient(model='gpt-4o-mini'); print(f'Provider: {c.provider}')"
# Expected: Provider: openai
```

### Verify Anthropic Support (requires anthropic package)
```bash
pip install anthropic
python -c "from src.llm_client import LLMClient; c = LLMClient(model='claude-3-5-sonnet-20241022'); print(f'Provider: {c.provider}')"
# Expected: Provider: anthropic
```

## Cost Estimation

### GPT-4o-mini
- Input: $0.150 / 1M tokens
- Output: $0.600 / 1M tokens
- ~1,200 calls × ~500 tokens = ~$0.50

### Claude 3.5 Sonnet
- Input: $3.00 / 1M tokens
- Output: $15.00 / 1M tokens
- ~1,200 calls × ~500 tokens = ~$10.00

**Total estimated cost: ~$10.50 for full cross-model experiments**

## Notes for Paper

### Discussion Section
> "To address concerns about single-model evaluation, we conducted cross-model experiments using GPT-4o-mini (OpenAI) and Claude-3.5-Sonnet (Anthropic). Results demonstrate that SKYT's canonicalization effectiveness (Δ_rescue) is consistent across providers, validating the approach's generalizability beyond a single LLM family."

### Results Section
> "Cross-model analysis (N=2,400 generations across 12 contracts, 2 models, 5 temperatures, 20 runs each) shows:
> - R_raw varies by model (GPT-4o-mini: 0.45±0.12, Claude-3.5: 0.52±0.15)
> - Δ_rescue remains consistent (GPT-4o-mini: 0.38±0.08, Claude-3.5: 0.35±0.09)
> - R_structural converges (GPT-4o-mini: 0.83±0.05, Claude-3.5: 0.87±0.04)"

(Note: Replace with actual experimental results)
