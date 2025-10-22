# SKYT Tests Directory

This directory contains all test and debugging utilities for the SKYT experiment system.

## Test Files

### Integration Tests
- **test_integration.py** - End-to-end integration tests
- **test_transformation_validation.py** - Validates transformation system behavior

### Component Tests
- **test_pipeline_call.py** - Tests transformation pipeline calls
- **test_transform_pipeline.py** - Tests transformation pipeline components
- **test_strategy.py** - Tests transformation strategies
- **test_string_explainer.py** - Tests property explainer components

### Debug Utilities
- **debug_slugify.py** - Debug utilities for slugify algorithm
- **debug_statement_explainer.py** - Debug utilities for statement ordering explainer

### Analysis Utilities
- **check_results.py** - Result validation and analysis
- **compare_codes.py** - Code comparison utilities

## Running Tests

From the project root:

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_integration.py

# Run with verbose output
python -m pytest tests/ -v
```

## Adding New Tests

All new test files should be placed in this directory and follow the naming convention:
- Test files: `test_*.py`
- Debug utilities: `debug_*.py`
- Analysis utilities: descriptive names like `check_*.py` or `compare_*.py`

## Test Organization

Tests are organized by:
1. **Integration tests** - Test multiple components working together
2. **Component tests** - Test individual modules in isolation
3. **Debug utilities** - Helper scripts for debugging specific issues
4. **Analysis utilities** - Tools for analyzing experiment results
