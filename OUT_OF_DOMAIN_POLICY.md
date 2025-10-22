# Out-of-Domain Policy System for SKYT

## Overview

The out-of-domain (OOD) policy system provides fine-grained control over how transformations may alter code behavior **outside** the contract's specified domain. This allows you to enforce specific requirements for OOD inputs while maintaining flexibility for in-domain behavior.

**Key Benefit**: Separate concerns between in-domain correctness (validated by oracle) and out-of-domain behavior (validated by OOD policy).

## Motivation

### The Problem

Contract-aware validation ensures transformations maintain correctness within the domain. However, you may have additional requirements for out-of-domain behavior:

- **Firmware/Embedded**: Error conditions must raise specific exceptions for hardware monitoring
- **API Contracts**: Out-of-domain inputs must return specific error codes
- **Debugging**: OOD behavior must remain unchanged for error tracing
- **Safety**: OOD handling must be explicit (no silent failures)

Without OOD policies, transformations could freely change OOD behavior (e.g., from raising `ValueError` to returning `0`), which might be unacceptable for your use case.

### The Solution

OOD policies let you specify exactly what's acceptable for out-of-domain inputs:

```json
{
  "out_of_domain": {
    "policy": "must_raise",
    "exception": "ValueError",
    "examples": [{"n": -1}, {"n": -5}],
    "max_checks": 3
  }
}
```

## Policy Types

### 1. `allow` (Default)

**Meaning**: Transformations may change OOD behavior freely.

**Use Cases**:
- General-purpose algorithms where OOD handling is implementation detail
- Research/experimentation where canonicalization is more important than OOD consistency
- Legacy code migration where OOD behavior is undefined

**Example**:
```json
{
  "out_of_domain": {
    "policy": "allow",
    "examples": [{"n": -1}]
  }
}
```

**Behavior**:
- ✅ Transform from `raise ValueError` → `return 0` (ALLOWED)
- ✅ Transform from `return 0` → `return -1` (ALLOWED)
- ✅ Transform from `return None` → `raise TypeError` (ALLOWED)

---

### 2. `must_raise`

**Meaning**: OOD inputs **must** raise an exception (optionally of specific type).

**Use Cases**:
- Firmware where error conditions must be signaled to hardware monitors
- APIs where exceptions are part of the contract
- Debugging infrastructure that catches exceptions for logging
- Safety-critical systems where silent failures are unacceptable

**Example**:
```json
{
  "out_of_domain": {
    "policy": "must_raise",
    "exception": "ValueError",
    "examples": [{"n": -1}, {"n": -100}],
    "max_checks": 2
  }
}
```

**Behavior**:
- ✅ `raise ValueError("negative")` (PASS - raises ValueError)
- ✅ `raise TypeError("wrong type")` if `exception: null` (PASS - any exception)
- ❌ `return 0` (FAIL - doesn't raise)
- ❌ `raise TypeError(...)` if `exception: "ValueError"` (FAIL - wrong exception type)

**Code Example**:
```python
# ACCEPTABLE with must_raise policy
def fibonacci(n):
    if n < 0:
        raise ValueError("Input must be non-negative")  # ✓ Raises
    # ... rest of implementation

# REJECTED with must_raise policy
def fibonacci(n):
    if n < 0:
        return 0  # ✗ Doesn't raise
    # ... rest of implementation
```

---

### 3. `must_return`

**Meaning**: OOD inputs **must** return a specific value.

**Use Cases**:
- APIs with defined error codes or sentinel values
- Functions where OOD returns have semantic meaning (e.g., `-1` = error)
- Chaining operations where specific values indicate failure
- Compatibility with existing systems expecting specific error returns

**Example**:
```json
{
  "out_of_domain": {
    "policy": "must_return",
    "return_value": 0,
    "examples": [{"n": -1}, {"n": -5}],
    "max_checks": 3
  }
}
```

**Behavior**:
- ✅ `return 0` (PASS - returns expected value)
- ❌ `return -1` (FAIL - wrong value)
- ❌ `raise ValueError(...)` (FAIL - raises instead of returning)
- ✅ Works with any JSON-serializable value: `null`, strings, numbers, booleans

**Code Example**:
```python
# ACCEPTABLE with must_return: 0
def fibonacci(n):
    if n < 0:
        return 0  # ✓ Returns 0
    # ... rest of implementation

# REJECTED with must_return: 0
def fibonacci(n):
    if n < 0:
        return -1  # ✗ Returns wrong value
    # ... rest of implementation
```

---

### 4. `forbid_transform`

**Meaning**: OOD behavior **must not change** from the baseline (pre-transformation).

**Use Cases**:
- Preserving error handling for debugging/tracing
- Maintaining compatibility with error-handling infrastructure
- Ensuring OOD behavior is intentional (not accidentally changed)
- Code review requirements where OOD changes need explicit approval

**Example**:
```json
{
  "out_of_domain": {
    "policy": "forbid_transform",
    "examples": [{"n": -1}, {"n": -5}],
    "max_checks": 3
  }
}
```

**Behavior**:
- ✅ Pre: `raise ValueError` → Post: `raise ValueError` (PASS - same behavior)
- ✅ Pre: `return 0` → Post: `return 0` (PASS - same behavior)
- ❌ Pre: `raise ValueError` → Post: `return 0` (FAIL - behavior changed)
- ❌ Pre: `return 0` → Post: `return -1` (FAIL - behavior changed)

**Code Example**:
```python
# PRE-TRANSFORMATION
def fibonacci(n):
    if n < 0:
        raise ValueError("negative input")
    # ... rest

# POST-TRANSFORMATION: ACCEPTABLE with forbid_transform
def fibonacci(n):
    if n < 0:
        raise ValueError("negative input")  # ✓ Same behavior
    # ... rest (can change in-domain code)

# POST-TRANSFORMATION: REJECTED with forbid_transform
def fibonacci(n):
    if n < 0:
        return 0  # ✗ Behavior changed
    # ... rest
```

---

## Contract Schema

### Full Specification

```json
{
  "id": "fibonacci_basic",
  "domain": {
    "inputs": [{"name": "n", "type": "int", "constraint": "n >= 0"}]
  },
  "out_of_domain": {
    "policy": "allow | must_raise | must_return | forbid_transform",
    "exception": "ValueError",
    "return_value": 0,
    "examples": [
      {"n": -1},
      {"n": -5},
      {"n": -100}
    ],
    "max_checks": 3
  }
}
```

### Field Descriptions

#### `policy` (string, required)
- `"allow"`: Default - no OOD restrictions
- `"must_raise"`: OOD must raise exception
- `"must_return"`: OOD must return specific value
- `"forbid_transform"`: OOD behavior must not change

#### `exception` (string, optional)
- For `must_raise` policy only
- Exception class name (e.g., `"ValueError"`, `"TypeError"`)
- If omitted, any exception is acceptable

#### `return_value` (any JSON-serializable, optional)
- For `must_return` policy only
- Expected return value for OOD inputs
- Can be: `null`, `0`, `""`, `false`, etc.

#### `examples` (array of dicts, required)
- List of out-of-domain input examples
- Each example is a dict mapping parameter names to values
- Examples should be **clearly** outside the domain
- Keep examples small and deterministic

#### `max_checks` (integer, optional, default: 3)
- Maximum number of examples to check (cap for performance)
- System will check at most `max_checks` examples
- Prevents unbounded execution loops

---

## Integration with Validation Pipeline

### Validation Flow

The OOD policy check is Step 3 in the transformation validation pipeline:

1. **In-Domain Oracle**: Both pre/post code must pass oracle tests within domain
2. **Monotonicity**: Distance to canon must not increase
3. **OOD Policy** (NEW): Transformation must comply with OOD policy

**Key Properties**:
- OOD check **only runs** if Steps 1 and 2 pass (short-circuit evaluation)
- OOD check is **opt-in** (only if `out_of_domain` block present)
- OOD failures return clear rejection messages

### Example Validation

```python
# Validation with OOD policy
is_valid, message = validate_transformation(
    pre_code, post_code, contract, contract_id
)

# Possible outcomes:
# ✓ "Contract-compliant and closer to canon (delta_d=0.189)"
# ✗ "Transformation broke working code (pre passed, post failed)"
# ✗ "Non-monotonic: distance increased (0.100 -> 0.200)"
# ✗ "Transformation violates out-of-domain policy"
```

---

## Best Practices

### Choosing Examples

**DO**:
- ✅ Choose examples **clearly** outside the domain
- ✅ Use small, deterministic inputs
- ✅ Cover edge cases (e.g., `-1`, `-100`, `null`, `""`)
- ✅ Keep `max_checks` ≤ 5 for performance

**DON'T**:
- ❌ Use boundary values that might be ambiguous (e.g., if domain is `n > 0`, don't use `n = 0`)
- ❌ Use random or non-deterministic inputs
- ❌ Use inputs that require expensive computation
- ❌ Provide too many examples (use `max_checks` to cap)

### Example Selection

```json
// GOOD: Clear OOD examples for domain "n >= 0"
"examples": [{"n": -1}, {"n": -5}, {"n": -100}]

// BAD: Boundary value (ambiguous if domain is n >= 0)
"examples": [{"n": 0}]  // This is IN domain!

// BAD: Too many examples without cap
"examples": [
  {"n": -1}, {"n": -2}, {"n": -3}, ..., {"n": -100}
],
"max_checks": 100  // Too expensive!
```

### Choosing a Policy

| Requirement | Policy | Example |
|-------------|--------|---------|
| No OOD requirements | `allow` | Research, general purpose |
| Must signal errors | `must_raise` | Firmware, APIs |
| Must return error code | `must_return` | Legacy compatibility |
| Must preserve OOD behavior | `forbid_transform` | Debugging, tracing |

### Multi-Parameter Examples

For functions with multiple parameters:

```json
{
  "domain": {
    "inputs": [
      {"name": "x", "type": "int", "constraint": "x >= 0"},
      {"name": "y", "type": "int", "constraint": "y >= 0"}
    ]
  },
  "out_of_domain": {
    "policy": "must_raise",
    "exception": "ValueError",
    "examples": [
      {"x": -1, "y": 0},
      {"x": 0, "y": -1},
      {"x": -1, "y": -1}
    ]
  }
}
```

---

## CLI Usage

### Flags

```bash
# Auto-detect OOD policy from contract (default)
python main.py --contract fibonacci_basic

# Explicitly enable OOD policy enforcement
python main.py --contract fibonacci_basic --enforce-ood-policy

# Override max_checks limit
python main.py --contract fibonacci_basic --max-ood-checks 5
```

### Flag Descriptions

- `--enforce-ood-policy`: Explicitly enable OOD checks (default: auto-detect from contract)
- `--max-ood-checks N`: Override `max_checks` from contract (default: 3)

---

## Examples

### Example 1: Firmware Error Signaling

```json
{
  "id": "gpio_toggle",
  "domain": {
    "inputs": [
      {"name": "pin", "type": "int", "constraint": "0 <= pin <= 15"}
    ]
  },
  "out_of_domain": {
    "policy": "must_raise",
    "exception": "ValueError",
    "examples": [
      {"pin": -1},
      {"pin": 16},
      {"pin": 100}
    ],
    "max_checks": 3
  }
}
```

**Rationale**: Hardware monitors catch `ValueError` for invalid pins.

---

### Example 2: API Error Codes

```json
{
  "id": "divide",
  "domain": {
    "inputs": [
      {"name": "a", "type": "float"},
      {"name": "b", "type": "float", "constraint": "b != 0"}
    ]
  },
  "out_of_domain": {
    "policy": "must_return",
    "return_value": null,
    "examples": [
      {"a": 10.0, "b": 0.0},
      {"a": 0.0, "b": 0.0}
    ],
    "max_checks": 2
  }
}
```

**Rationale**: API returns `null` for division by zero (no exceptions).

---

### Example 3: Debugging Preservation

```json
{
  "id": "parse_config",
  "domain": {
    "inputs": [
      {"name": "config_str", "type": "str", "constraint": "valid JSON"}
    ]
  },
  "out_of_domain": {
    "policy": "forbid_transform",
    "examples": [
      {"config_str": "invalid json"},
      {"config_str": ""},
      {"config_str": "null"}
    ],
    "max_checks": 3
  }
}
```

**Rationale**: Error handling must remain unchanged for debugging/tracing.

---

### Example 4: General Purpose (Default)

```json
{
  "id": "fibonacci_basic",
  "domain": {
    "inputs": [{"name": "n", "type": "int", "constraint": "n >= 0"}]
  },
  "out_of_domain": {
    "policy": "allow",
    "examples": [{"n": -1}]
  }
}
```

**Rationale**: Canonicalization more important than OOD consistency.

---

## Migration Guide

### Adding OOD Policy to Existing Contracts

**Step 1**: Identify OOD inputs
- What inputs are outside your domain constraint?
- Examples: negative numbers, empty strings, null values

**Step 2**: Determine requirements
- Must OOD inputs raise exceptions? → `must_raise`
- Must OOD inputs return specific value? → `must_return`
- Must OOD behavior stay unchanged? → `forbid_transform`
- No requirements? → `allow` (or omit `out_of_domain` block)

**Step 3**: Add to contract
```json
{
  "domain": {...},
  "out_of_domain": {
    "policy": "must_raise",
    "exception": "ValueError",
    "examples": [{"n": -1}, {"n": -5}],
    "max_checks": 3
  }
}
```

**Step 4**: Test
```bash
python tests/test_ood_integration.py
python main.py --contract your_contract --enforce-ood-policy
```

### Backward Compatibility

**No `out_of_domain` block**: Behavior is exactly as before
- No OOD checks run
- All transformations validated only by oracle + monotonicity
- Existing contracts work unchanged

**Empty examples**: System logs warning and skips OOD checks
- Graceful degradation
- Pipeline continues normally

---

## Implementation Details

### Files

- `src/policies/out_of_domain.py`: Core OOD policy logic
- `src/contract.py`: Contract parsing with OOD spec
- `src/contract_validator.py`: Integration point (Step 3)
- `contracts/templates.json`: Example contracts
- `tests/test_out_of_domain_policy.py`: Unit tests
- `tests/test_ood_integration.py`: Integration tests

### Safety Features

1. **Capped Execution**: `max_checks` prevents unbounded loops
2. **Exception Handling**: All execution errors caught → False (safe failure)
3. **Short-Circuit**: OOD check only runs if oracle + monotonicity pass
4. **Opt-In**: Only contracts with `out_of_domain` block are affected

### Performance

- **Minimal Overhead**: Only checks specified examples (default: 3)
- **Fast Path**: If policy is "allow", check returns immediately
- **Lazy Evaluation**: Only runs after oracle + monotonicity pass

---

## Testing

### Run Unit Tests

```bash
python tests/test_out_of_domain_policy.py
```

**Coverage**: 22 tests covering all policy types and edge cases

### Run Integration Tests

```bash
python tests/test_ood_integration.py
```

**Coverage**: 9 tests covering full validation pipeline integration

---

## Troubleshooting

### OOD check not running

**Symptom**: Transformations pass even though they violate OOD policy

**Causes**:
1. Contract missing `out_of_domain` block
2. Policy is `"allow"`
3. `examples` list is empty
4. Oracle or monotonicity check failed first (short-circuit)

**Fix**: Check contract has `out_of_domain` block with non-empty examples

### OOD check always fails

**Symptom**: All transformations rejected with "violates out-of-domain policy"

**Causes**:
1. Examples are actually in-domain (not OOD)
2. Wrong policy for your use case
3. `exception` or `return_value` doesn't match actual code

**Fix**: Review examples and policy type

### Performance issues

**Symptom**: Validation is slow

**Causes**:
1. Too many examples
2. `max_checks` set too high
3. Examples require expensive computation

**Fix**: Reduce examples or set `max_checks` to 3

---

## FAQ

**Q: Can I use multiple policies?**
A: No, one policy per contract. Use `forbid_transform` if you need strict preservation.

**Q: What if I want different policies for different parameters?**
A: Create separate contracts or use `forbid_transform` + manual validation.

**Q: Can examples be in-domain?**
A: No! Examples must be clearly outside the domain. System doesn't validate this automatically.

**Q: Does this affect existing contracts?**
A: No! Contracts without `out_of_domain` block work exactly as before.

**Q: Can I disable OOD checks at runtime?**
A: Remove `out_of_domain` block from contract, or set policy to `"allow"`.

---

## References

- Contract-aware validation: `CONTRACT_AWARE_VALIDATION.md`
- Variable naming constraints: `VARIABLE_NAMING_CONSTRAINTS.md`
- SKYT methodology: Main README

---

**Status**: ✅ Implemented and Tested
**Version**: 1.0
**Last Updated**: October 22, 2025
