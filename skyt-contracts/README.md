# SKYT Contracts Repository

> Versioned contracts, restriction sets, and certification standards for the SKYT repeatability system.

## Overview

This repository contains the **definitions** that configure SKYT experiments:

- **Contracts**: Code generation specifications with oracles and constraints
- **Restrictions**: Coding standards and certification rules (NASA, MISRA, DO-178C)
- **Mappings**: Default restriction sets for specific domains

## Structure

```
skyt-contracts/
├── schema/                        # JSON Schema definitions
│   ├── contract.schema.json       # Contract validation schema
│   └── restriction.schema.json    # Restriction set schema
│
├── contracts/                     # Code generation contracts
│   ├── algorithms/                # General algorithms
│   │   ├── fibonacci_basic.json
│   │   ├── fibonacci_recursive.json
│   │   ├── binary_search.json
│   │   ├── gcd.json
│   │   └── lru_cache.json
│   └── strings/
│       ├── slugify.json
│       └── balanced_brackets.json
│
├── restrictions/                  # Certification standards
│   ├── presets/                   # Official standards (read-only)
│   │   ├── nasa_power_of_10.json
│   │   ├── misra_c_2012.json      # (future)
│   │   └── do_178c_dal_a.json     # (future)
│   └── community/                 # Community-contributed
│
└── mappings/                      # Domain defaults
    └── aerospace.json
```

## Usage

### With SKYT CLI

```bash
# Use a specific contract
python main.py --contract fibonacci_basic --runs 10

# Apply restriction set
python main.py --contract fibonacci_basic --restriction nasa_power_of_10
```

### With SKYT API

```python
from skyt import Pipeline

pipeline = Pipeline(
    contract="fibonacci_basic",
    restrictions=["nasa_power_of_10"],
)
result = await pipeline.run(num_runs=10, temperature=0.3)
```

## Contract Schema

Contracts define:

| Field | Description |
|-------|-------------|
| `id` | Unique contract identifier |
| `version` | Semantic version |
| `task_intent` | What the code should do |
| `prompt` | The LLM prompt |
| `constraints` | Function names, variable naming, etc. |
| `oracle_requirements` | Test cases for validation |
| `rescue_bounds` | Allowed transformations |

Example:

```json
{
  "id": "fibonacci_basic",
  "version": "1.0.0",
  "task_intent": "Generate nth Fibonacci number using iteration",
  "prompt": "Write a Python function called 'fibonacci'...",
  "constraints": {
    "function_name": "fibonacci",
    "implementation_style": "iterative"
  },
  "oracle_requirements": {
    "test_cases": [
      {"input": 0, "expected": 0},
      {"input": 10, "expected": 55}
    ]
  }
}
```

## Restriction Schema

Restriction sets define coding rules:

| Field | Description |
|-------|-------------|
| `id` | Unique identifier |
| `name` | Human-readable name |
| `version` | Semantic version |
| `source` | "preset" or "user" |
| `authority` | Standard body (NASA, MISRA, etc.) |
| `rules` | List of rule definitions |

Example:

```json
{
  "id": "nasa_power_of_10",
  "name": "NASA/JPL Power of 10 Rules",
  "version": "1.0.0",
  "source": "preset",
  "authority": "NASA/JPL Laboratory for Reliable Software",
  "rules": [
    {
      "id": "P10-R1",
      "name": "Simple Control Flow",
      "severity": "mandatory",
      "description": "No goto, setjmp, longjmp, or recursion"
    }
  ]
}
```

## Contributing

1. Fork this repository
2. Add your contract/restriction in the appropriate directory
3. Validate against the JSON schema
4. Submit a pull request

## License

- **Contracts**: CC-BY-4.0 (attribution required)
- **Restriction presets**: As specified by original standards body

## Related

- [SKYT Core](https://github.com/skyt/skyt) - The SKYT engine
- [SKYT Paper](https://example.com) - MSR 2026 publication
