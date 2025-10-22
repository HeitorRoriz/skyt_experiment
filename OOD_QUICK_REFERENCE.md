# Out-of-Domain Policy - Quick Reference

## 30-Second Overview

OOD policies control transformation behavior **outside** the contract domain.

**4 Policy Types**: `allow`, `must_raise`, `must_return`, `forbid_transform`

---

## Policy Cheat Sheet

| Policy | Meaning | Use Case |
|--------|---------|----------|
| `allow` | Any OOD behavior OK | General purpose, research |
| `must_raise` | OOD must raise exception | Firmware, error signaling |
| `must_return` | OOD must return value | API error codes |
| `forbid_transform` | OOD behavior must not change | Debugging, tracing |

---

## Quick Start

### 1. Add to Contract

```json
{
  "id": "my_function",
  "domain": {
    "inputs": [{"name": "n", "type": "int", "constraint": "n >= 0"}]
  },
  "out_of_domain": {
    "policy": "must_raise",
    "exception": "ValueError",
    "examples": [{"n": -1}, {"n": -5}],
    "max_checks": 3
  }
}
```

### 2. Run

```bash
python main.py --contract my_function
```

Done! ✅

---

## Common Patterns

### Firmware: Must Signal Errors
```json
{
  "policy": "must_raise",
  "exception": "ValueError",
  "examples": [{"pin": -1}, {"pin": 999}]
}
```

### API: Return Error Code
```json
{
  "policy": "must_return",
  "return_value": null,
  "examples": [{"x": 0}]
}
```

### Debugging: Preserve Behavior
```json
{
  "policy": "forbid_transform",
  "examples": [{"input": "invalid"}]
}
```

### Research: No Restrictions
```json
{
  "policy": "allow",
  "examples": [{"n": -1}]
}
```

---

## Validation Flow

```
1. Oracle (in-domain) → Pass?
   ↓
2. Monotonicity → Pass?
   ↓
3. OOD Policy → Pass?
   ↓
✅ Accept Transformation
```

---

## CLI Flags

```bash
--enforce-ood-policy      # Explicit enable (auto by default)
--max-ood-checks N        # Override max checks (default: 3)
```

---

## Field Reference

```json
{
  "policy": "allow | must_raise | must_return | forbid_transform",
  "exception": "ValueError",    // For must_raise only
  "return_value": 0,            // For must_return only
  "examples": [                 // Required, OOD inputs
    {"param1": value1},
    {"param2": value2}
  ],
  "max_checks": 3               // Optional, default 3
}
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| OOD not running | Add `out_of_domain` block to contract |
| Always fails | Check examples are truly OOD |
| Slow | Reduce examples or set `max_checks: 3` |

---

## Testing

```bash
# Unit tests (22 tests)
python tests/test_out_of_domain_policy.py

# Integration tests (9 tests)
python tests/test_ood_integration.py
```

---

## Documentation

- **Full Guide**: `OUT_OF_DOMAIN_POLICY.md` (600 lines)
- **Implementation**: `OOD_IMPLEMENTATION_SUMMARY.md`
- **This Card**: Quick reference

---

**TIP**: Start with `"policy": "allow"` and tighten as needed!
