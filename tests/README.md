# LFSR-Seq Test Suite

This directory contains the test suite for the LFSR-Seq analysis tool.

## Test Structure

- `test_core.py` - Unit tests for core LFSR mathematics (matrix operations)
- `test_field.py` - Unit tests for finite field validation
- `test_polynomial.py` - Unit tests for polynomial operations
- `test_io.py` - Unit tests for I/O operations (CSV reading)
- `test_integration.py` - Integration tests for complete workflows
- `conftest.py` - Pytest configuration and fixtures
- `fixtures/` - Test data files

## Running Tests

### Prerequisites

SageMath must be installed system-wide (it's not available via PyPI). The tests will automatically skip if SageMath is not available.

### Basic Test Execution

```bash
# Run all tests
make test

# Or directly with pytest
pytest tests/

# Run with coverage
make test-cov
```

### Running Specific Tests

```bash
# Run only unit tests
pytest tests/test_core.py tests/test_field.py

# Run only integration tests
pytest tests/test_integration.py

# Run a specific test
pytest tests/test_core.py::TestBuildStateUpdateMatrix::test_simple_4bit_lfsr_gf2

# Skip slow tests
pytest tests/ -m "not slow"
```

### Test Markers

Tests can be marked with:
- `@pytest.mark.slow` - Slow-running tests (can be skipped with `-m "not slow"`)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.sagemath` - Tests requiring SageMath (automatically applied)

## Test Coverage

To generate coverage reports:

```bash
make test-cov
```

This will:
- Run all tests with coverage tracking
- Generate a terminal report
- Generate an HTML report in `htmlcov/index.html`

## Writing New Tests

When adding new tests:

1. Follow the existing test structure
2. Use descriptive test names (e.g., `test_simple_4bit_lfsr_gf2`)
3. Add docstrings explaining what the test verifies
4. Use fixtures from `conftest.py` when available
5. Mark slow tests with `@pytest.mark.slow`
6. Use `tmp_path` fixture for temporary files

Example:

```python
def test_new_feature(self):
    """Test description of what this test verifies."""
    # Arrange
    input_data = ...
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_value
```

## Known Issues

- Tests require SageMath to be installed system-wide
- Some tests may be slow for large LFSRs (marked with `@pytest.mark.slow`)
- Integration tests may take longer due to full workflow execution

