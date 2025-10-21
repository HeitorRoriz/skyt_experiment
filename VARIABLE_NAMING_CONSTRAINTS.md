# Variable Naming Constraints in SKYT Contracts

## Overview

SKYT contracts now support explicit variable naming constraints, allowing you to specify which variables **must remain fixed** (e.g., for firmware/embedded systems where names map to hardware registers) and which are **flexible** (can be renamed for canonicalization).

This is critical for embedded/firmware development where:
- Variable names may map to hardware registers or memory addresses
- API contracts require specific parameter names
- Code generation tools expect certain naming conventions

## Contract Schema

Add a `variable_naming` section to your contract's `constraints`:

```json
{
  "constraints": {
    "function_name": "is_balanced",
    "variable_naming": {
      "fixed_variables": ["s"],
      "flexible_variables": ["stack", "bracket_map", "brackets", "char"],
      "naming_policy": "flexible"
    }
  }
}
```

### Fields

#### `fixed_variables` (array of strings)
Variables that **MUST NOT be renamed** under any circumstances.

**Use cases:**
- Function parameters that are part of the API contract
- Variables that map to hardware registers (e.g., `GPIO_PIN_3`, `UART_TX`)
- Global variables with external linkage
- Variables required by code generation tools

**Example:**
```json
"fixed_variables": ["s", "n", "GPIO_PORT_A", "interrupt_handler"]
```

#### `flexible_variables` (array of strings)
Variables that **CAN be renamed** to match the canonical form.

**Use cases:**
- Local loop counters (e.g., `i`, `j`, `idx`)
- Temporary variables (e.g., `temp`, `tmp`, `result`)
- Internal data structures (e.g., `stack`, `queue`, `buffer`)

**Example:**
```json
"flexible_variables": ["stack", "bracket_map", "brackets", "char", "i", "temp"]
```

#### `naming_policy` (string: "flexible" | "strict")
Overall policy for variable renaming.

- **`"flexible"`** (default): Allow renaming of variables in `flexible_variables` list
- **`"strict"`**: Do NOT rename ANY variables, even if in `flexible_variables` list

**Use cases for "strict":**
- Firmware with strict coding standards
- Safety-critical systems requiring code review
- Generated code that must not be modified

## Examples

### Example 1: Fibonacci (Flexible Naming)

```json
{
  "id": "fibonacci_basic",
  "constraints": {
    "function_name": "fibonacci",
    "variable_naming": {
      "fixed_variables": ["n"],
      "flexible_variables": ["a", "b", "i", "prev", "curr", "next"],
      "naming_policy": "flexible"
    }
  }
}
```

**Behavior:**
- ✅ `n` will NEVER be renamed (it's the API parameter)
- ✅ `a`, `b`, `i` can be renamed to match canon (e.g., `a` → `prev`)
- ✅ Any other variables not in either list will NOT be renamed (safe default)

### Example 2: Balanced Brackets (Flexible Naming)

```json
{
  "id": "balanced_brackets",
  "constraints": {
    "function_name": "is_balanced",
    "variable_naming": {
      "fixed_variables": ["s"],
      "flexible_variables": ["stack", "bracket_map", "brackets", "char"],
      "naming_policy": "flexible"
    }
  }
}
```

**Behavior:**
- ✅ `s` will NEVER be renamed (it's the API parameter)
- ✅ `bracket_map` can be renamed to `brackets` to match canon
- ✅ `stack` and `char` can be renamed if canon uses different names

### Example 3: Firmware GPIO (Strict Naming)

```json
{
  "id": "gpio_toggle",
  "constraints": {
    "function_name": "toggle_led",
    "variable_naming": {
      "fixed_variables": ["GPIO_PORT_A", "LED_PIN", "delay_ms"],
      "flexible_variables": [],
      "naming_policy": "strict"
    }
  }
}
```

**Behavior:**
- ❌ NO variables will be renamed (strict policy)
- ✅ All variable names preserved exactly as written
- ✅ Suitable for firmware where names have semantic meaning

### Example 4: Embedded System (Mixed)

```json
{
  "id": "uart_transmit",
  "constraints": {
    "function_name": "uart_send",
    "variable_naming": {
      "fixed_variables": ["UART_TX_REG", "UART_STATUS", "data"],
      "flexible_variables": ["i", "byte", "checksum"],
      "naming_policy": "flexible"
    }
  }
}
```

**Behavior:**
- ✅ `UART_TX_REG`, `UART_STATUS`, `data` will NEVER be renamed (hardware registers + API)
- ✅ `i`, `byte`, `checksum` can be renamed to match canon
- ✅ Any other variables (not in either list) will NOT be renamed

## Implementation

The `SnapToCanonFinalizer` transformer respects these constraints:

```python
class SnapToCanonFinalizer(TransformationBase):
    def __init__(self, contract: dict = None):
        self.contract = contract
    
    def _can_rename_variable(self, var_name, fixed_vars, flexible_vars):
        # If variable is in fixed list, cannot rename
        if var_name in fixed_vars:
            return False
        
        # If flexible list is specified and variable is in it, can rename
        if flexible_vars and var_name in flexible_vars:
            return True
        
        # If flexible list is specified but variable is not in it, cannot rename
        if flexible_vars:
            return False
        
        # If no lists specified, allow renaming (default flexible)
        return True
```

## Validation Rules

1. **Fixed variables are NEVER renamed**, regardless of naming_policy
2. **Flexible variables CAN be renamed** only if naming_policy is "flexible"
3. **Unlisted variables are NOT renamed** (safe default)
4. **Empty flexible_variables list** means only explicitly listed variables can be renamed
5. **No variable_naming section** defaults to flexible policy with no constraints

## Use Cases

### Firmware/Embedded Systems
```json
"variable_naming": {
  "fixed_variables": ["GPIO_PIN_3", "ADC_CHANNEL_0", "interrupt_vector"],
  "flexible_variables": ["i", "j", "temp", "result"],
  "naming_policy": "flexible"
}
```

### API Contracts
```json
"variable_naming": {
  "fixed_variables": ["request", "response", "callback"],
  "flexible_variables": ["data", "buffer", "index"],
  "naming_policy": "flexible"
}
```

### Safety-Critical Code
```json
"variable_naming": {
  "fixed_variables": [],
  "flexible_variables": [],
  "naming_policy": "strict"
}
```

### General Purpose (Default)
```json
"variable_naming": {
  "fixed_variables": ["n", "s", "text"],
  "flexible_variables": ["i", "j", "temp", "result", "buffer"],
  "naming_policy": "flexible"
}
```

## Benefits

1. **Firmware Safety**: Prevents renaming of hardware-mapped variables
2. **API Compliance**: Ensures public interface parameters remain unchanged
3. **Code Review**: Strict policy preserves original variable names for review
4. **Flexibility**: Allows canonicalization where it's safe
5. **Documentation**: Makes naming requirements explicit in the contract

## Migration Guide

### Existing Contracts

If your contract doesn't have `variable_naming`, the default behavior is:
- All variables can potentially be renamed (flexible policy)
- No explicit constraints

### Adding Constraints

1. Identify which variables are part of your API/hardware interface → `fixed_variables`
2. Identify which variables are internal/temporary → `flexible_variables`
3. Choose policy: `"flexible"` for most cases, `"strict"` for safety-critical

### Example Migration

**Before:**
```json
{
  "constraints": {
    "function_name": "fibonacci"
  }
}
```

**After:**
```json
{
  "constraints": {
    "function_name": "fibonacci",
    "variable_naming": {
      "fixed_variables": ["n"],
      "flexible_variables": ["a", "b", "i"],
      "naming_policy": "flexible"
    }
  }
}
```

---

**Status**: ✅ Implemented
**Version**: 1.0
**Last Updated**: October 21, 2025
