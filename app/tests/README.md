# LFSR-Seq Test Suite

This directory contains the test suite for the LFSR-Seq analysis tool.

## Test Structure

- `test_core.py` - Unit tests for core LFSR mathematics (matrix operations)
- `test_field.py` - Unit tests for finite field validation
- `test_polynomial.py` - Unit tests for polynomial operations
- `test_io.py` - Unit tests for I/O operations (CSV reading)
- `test_integration.py` - Integration tests for complete workflows
- `test_analysis.py` - Unit tests for cycle detection and state enumeration
- `test_parallel.py` - Tests for parallel state enumeration (static/dynamic/hybrid modes)
- `test_edge_cases.py` - Edge case and boundary condition tests
- `test_statistics.py` - Unit tests for statistical analysis
- `test_ciphers_grain.py` - Regression tests for the Grain-128 cipher implementation
- `test_cross_check_external.py` - Cross-checks our GF(2) output against two
  third-party LFSR libraries (PyLFSR, lfsr-tools). Optional: skips cleanly
  unless installed via `pip install -e ".[cross-check]"`. See the module's
  docstring for the coefficient-convention mapping between tools and known
  quality caveats in lfsr-tools.
- `conftest.py` - Pytest configuration and fixtures
- `fixtures/` - Test data files

## Running Tests

### Prerequisites

SageMath must be installed system-wide (it's not available via PyPI). The tests will automatically skip if SageMath is not available.

Optional: `test_cross_check_external.py`'s tests require PyLFSR and
lfsr-tools, installed via `pip install -e ".[cross-check]"` (not part
of the default `[dev]` extra, since these are only used by that one
test module). They also skip cleanly if not installed.

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

## Diagnosing an Intermittent Hang

A few real bugs in this project (all fixed) only manifested as a test
that hangs some fraction of the time rather than failing outright --
the kind of thing a single `pytest` run can't reliably reproduce or
debug. `scripts/diagnose-hang.sh` automates the technique that found
them: run the target repeatedly, catch it the moment it's still alive
past a grace period, and take a few `py-spy` stack-trace snapshots a
few seconds apart (comparing local variables across snapshots reveals
whether something is genuinely stuck versus just doing slow, real
work). Requires `py-spy` in the venv (`.venv/bin/pip install py-spy`)
and, to actually dump another process's stack, `sudo` (see the
script's `--help` for why).

```bash
./scripts/diagnose-hang.sh -- tests/some_test.py::SomeTest::test_flaky
```

Two real, unrelated bugs were found this way in the ML test suite:
a `conftest.py` wildcard import that fed a SageMath `LazyImport` object
into pytest's fixture-discovery scan (an intermittent collection-time
hang), and an unbounded retry loop in `lfsr.ml.training.generate_training_data`
that could spin forever once it exhausted the finite number of distinct
coefficient vectors at a small degree/field order. Both are fixed;
see their commit messages for the full diagnosis if you want the
worked example of what a `py-spy` trace of each looked like.

