# lfsr-seq

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3+](https://img.shields.io/badge/license-GPL%20v3+-green.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Linear Feedback Shift Register (LFSR) Sequence Analysis Tool**

A comprehensive, production-ready tool for analyzing Linear Feedback
Shift Register sequences, computing periods, determining
characteristic polynomials, and performing advanced cryptanalysis over
finite fields. This tool is useful for cryptographic research, stream
cipher analysis, educational purposes, and security evaluation.


## Features

### Core Analysis
- **Sequence Analysis**: Analyze all possible LFSR state sequences and compute periods
- **Characteristic Polynomials**: Determine characteristic polynomials and their orders
- **Primitive Polynomial Detection**: Automatically detect primitive polynomials that yield maximum-period LFSRs
- **Matrix Operations**: Compute state update matrices and their orders
- **Polynomial Factorization**: Factor characteristic polynomials and analyze factor orders
- **Efficient Cycle Detection**: Multiple algorithms available (Floyd's, Brent's, enumeration) for cycle detection

### Advanced Features
- **Berlekamp-Massey Algorithm**: Synthesize LFSRs from sequences
- **Linear Complexity**: Calculate linear complexity and complexity profiles
- **Statistical Analysis**: Frequency tests, runs tests, autocorrelation, periodicity detection
- **Multi-format Export**: Export results in JSON, CSV, XML, or plain text formats

### Cryptographic Analysis
- **Correlation Attack Framework**: Comprehensive suite for analyzing combination generators
  - **Siegenthaler's Attack**: Basic correlation attack for detecting vulnerabilities
  - **Fast Correlation Attack (Meier-Staffelbach)**: Advanced attack using iterative decoding for state recovery
  - **Distinguishing Attacks**: Detect if keystream is distinguishable from random (correlation and statistical methods)
  - **Combining Function Analysis**: Analyze correlation immunity, bias, and security properties
  - **Attack Success Probability Estimation**: Estimate attack feasibility and required resources
- **NIST SP 800-22 Test Suite**: Industry-standard statistical tests for randomness (all 15 tests)
  - Frequency tests, runs tests, matrix rank, spectral tests
  - Template matching, Maurer's universal test, linear complexity test
  - Serial test, approximate entropy, cumulative sums, random excursions
  - Multi-format report generation (Text, JSON, CSV, XML, HTML)

### Field Support
- **Prime Fields**: Full support for GF(p) where p is prime
- **Prime Power Fields**: Support for GF(pⁿ) extension fields
- **Comprehensive Validation**: Input validation for field orders and coefficients

### User Experience
- **Modern CLI**: Command-line interface with argparse, help system, and multiple options
- **Progress Tracking**: Real-time progress bars with time estimates
- **Verbose/Quiet Modes**: Control output verbosity
- **Security Hardened**: Path traversal protection, file size limits, input sanitization

### Performance Optimizations
- **Multiple Cycle Detection Algorithms**: Floyd's (tortoise-and-hare), Brent's (powers-of-2), and enumeration methods
- **Period-Only Mode**: True O(1) space complexity for period computation without sequence storage
- **Parallel State Enumeration**: Multi-process parallelization for large state space analysis
- **Optimized State Tracking**: Set-based visited state tracking for O(1) lookups
- **Primitive Polynomial Optimization**: Fast period prediction for primitive polynomials
- **Scalable Architecture**: Designed to handle larger LFSRs efficiently

## Prerequisites

- **Python 3.8 or higher**
- **SageMath 9.7 or higher** - [Installation instructions](https://www.sagemath.org/)

### Installing SageMath

SageMath must be installed separately as it's not available via PyPI:

**Debian/Ubuntu:**
```bash
sudo apt-get update
sudo apt-get install sagemath
```

**Fedora/RHEL:**
```bash
sudo dnf install sagemath
```

**Arch Linux:**
```bash
sudo pacman -S sagemath
```

**macOS (Homebrew):**
```bash
brew install sagemath
```

**Conda:**
```bash
conda install -c conda-forge sage
```

## Installation

### Quick Install (Recommended)

Use the automated bootstrap script:

```bash
# Basic installation (creates virtual environment automatically)
./bootstrap

# With development dependencies
./bootstrap --dev

# Skip virtual environment (install system-wide)
./bootstrap --no-venv

# Clean build artifacts and caches
./bootstrap --clean

# Uninstall the package
./bootstrap --uninstall
```

The bootstrap script will:
- Check your Python and SageMath installation
- **Automatically create a virtual environment (`.venv`)** for PEP 668 compliance
- Upgrade pip and build tools
- Install the package in development mode
- Run smoke tests to verify installation

**Note:** 
- Virtual environment creation is the **default and recommended** approach (PEP 668 compliant)
- The virtual environment is automatically activated during installation
- After installation, activate it with: `source .venv/bin/activate`
- Use `--no-venv` only if you need system-wide installation (not recommended, may fail on PEP 668 systems)

### Manual Installation

1. **Check your environment:**
   ```bash
   ./scripts/check-environment.sh
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   # Create virtual environment
   python3 -m venv .venv

   # Activate it
   source .venv/bin/activate
   ```

3. **Install the package:**
   ```bash
   # Basic installation
   pip install -e .

   # With development dependencies
   pip install -e ".[dev]"
   ```

   **Note:** If you skip the virtual environment step, packages will
     be installed system-wide, which may require administrator
     privileges and can conflict with system packages.

### Using Make

If you have `make` installed:

```bash
# Quick development setup (automatically creates venv and installs dev dependencies)
make dev-setup
source .venv/bin/activate

# Or install manually (venv is automatically created)
make install-dev
source .venv/bin/activate

# Basic installation (venv is automatically created)
make install
source .venv/bin/activate
```

**Available Make targets:**
- `make venv` - Create virtual environment (`.venv`) - automatically called by other targets
- `make install` - Install package in development mode (auto-creates venv)
- `make install-dev` - Install with development dependencies (auto-creates venv)
- `make dev-setup` - Create venv, check environment, and install dev dependencies
- `make test` - Run tests (uses venv if available)
- `make test-cov` - Run tests with coverage report
- `make lint` - Run linting (uses venv if available)
- `make format` - Format code (uses venv if available)
- `make format-check` - Check code formatting without modifying
- `make type-check` - Run type checking (uses venv if available)
- `make build` - Build distribution packages (uses venv if available)
- `make clean` - Remove build artifacts
- `make clean-venv` - Remove virtual environment
- `make distclean` - Remove all generated files (including venv)
- `make uninstall` - Uninstall the package
- `make ci` - Run all CI checks (lint, format-check, type-check, test)

**Note:** All Make targets automatically create and use a virtual
  environment (`.venv`) to ensure PEP 668 compliance on modern Linux
  distributions.

## Quick Start

### Basic Usage

```bash
lfsr-seq <input_file> <gf_order> [options]
```

**Example:**
```bash
lfsr-seq strange.csv 2
```

This will:
- Read LFSR coefficients from `strange.csv`
- Analyze sequences over GF(2)
- Generate output in `strange.csv.out`

### Command-Line Options

```bash
lfsr-seq <input_file> <gf_order> [options]

Positional arguments:
  input_file            CSV file containing LFSR coefficient vectors
  gf_order              Galois field order (prime or prime power)

Optional arguments:
  -h, --help            Show help message and exit
  --version             Show version and exit
  -o, --output FILE     Specify output file (default: input_file.out)
  -v, --verbose         Enable verbose output
  -q, --quiet           Enable quiet mode (suppress non-essential output)
  --no-progress         Disable progress bar display
  --format {text,json,csv,xml}
                        Output format (default: text)
  --period-only         Compute periods only, without storing sequences
  --algorithm {floyd,brent,enumeration,auto}
                        Cycle detection algorithm (default: auto)
                        - floyd: Tortoise-and-hare method
                        - brent: Powers-of-2 method
                        - enumeration: Simple enumeration (default, faster)
                        - auto: Enumeration for full mode, floyd for period-only
  --check-primitive     Explicitly check for primitive polynomials
                        (detection is automatic, flag makes it explicit)
  --correlation-attack   Perform correlation attack analysis on combination
                        generators (requires --lfsr-configs)
  --lfsr-configs FILE   JSON file with combination generator configuration
  --fast-correlation-attack
                        Use fast correlation attack (Meier-Staffelbach)
  --distinguishing-attack
                        Perform distinguishing attack to detect vulnerabilities
  --nist-test          Run NIST SP 800-22 statistical test suite
  --sequence-file FILE  File containing binary sequence for NIST tests
  --nist-output-format {text,json,csv,xml,html}
                        Format for NIST test reports (default: text)
```

**Examples:**

```bash
# Basic analysis
lfsr-seq coefficients.csv 2

# Verbose output with custom output file
lfsr-seq coefficients.csv 2 --verbose --output results.txt

# Export to JSON format
lfsr-seq coefficients.csv 2 --format json --output results.json

# Quiet mode (no progress bar)
lfsr-seq coefficients.csv 2 --quiet --no-progress

# Analyze over GF(3)
lfsr-seq coefficients.csv 3

# Check for primitive polynomials (automatic, but flag makes it explicit)
lfsr-seq coefficients.csv 2 --check-primitive
```

### Input Format

The CSV file should contain one or more rows of LFSR
coefficients. Each row represents a different LFSR configuration:

```csv
1,1,1,0,0,0,0,0,1,1
1,1,1,0,0,0,0,0,1,1,0,1,1,1,0
1,1,1,0,0,0,0,0,1,1,0,1,1,1,1
```

Each coefficient should be in the range [0, GF_order-1].

**Security Limits:**
- Maximum file size: 10 MB
- Maximum CSV rows: 10,000
- Path traversal protection enabled

### Output Formats

The tool supports multiple output formats:

**Text Format (Default):**
Human-readable formatted output with tables and sections.

**JSON Format:**
Structured JSON output suitable for programmatic processing:
```bash
lfsr-seq strange.csv 2 --format json --output results.json
```

**CSV Format:**
Tabular CSV output:
```bash
lfsr-seq strange.csv 2 --format csv --output results.csv
```

**XML Format:**
Structured XML output:
```bash
lfsr-seq strange.csv 2 --format xml --output results.xml
```

### Output Contents

The tool generates detailed output including:
- State update matrix
- Matrix order (period of state transitions)
- All possible state sequences with their periods
- Characteristic polynomial and its order
- **Primitive polynomial indicator** ([PRIMITIVE] shown when polynomial is primitive)
- Factorization of the characteristic polynomial
- Statistical analysis (when using Python API)

Output is written to both:
- Console (summary, unless `--quiet` is used)
- Output file (full details)

## Python API

The tool can also be used as a Python library:

```python
from lfsr.cli import main
from lfsr.synthesis import berlekamp_massey, linear_complexity
from lfsr.statistics import statistical_summary
from lfsr.core import build_state_update_matrix
from lfsr.attacks import (
    CombinationGenerator, LFSRConfig,
    siegenthaler_correlation_attack,
    fast_correlation_attack,
    distinguishing_attack
)
from lfsr.nist import run_nist_test_suite

# Analyze LFSR from CSV
with open("output.txt", "w") as f:
    main("coefficients.csv", "2", output_file=f)

# Synthesize LFSR from sequence using Berlekamp-Massey
sequence = [1, 0, 1, 1, 0, 1, 0, 0, 1]
poly, complexity = berlekamp_massey(sequence, 2)
print(f"Linear complexity: {complexity}")

# Statistical analysis
stats = statistical_summary(sequence, 2)
print(f"Frequency ratio: {stats['frequency']['ratio']}")
print(f"Total runs: {stats['runs']['total_runs']}")

# Build state update matrix
coeffs = [1, 1, 0, 1]
C, CS = build_state_update_matrix(coeffs, 2)

# Correlation attack on combination generator
def majority(a, b, c):
    return 1 if (a + b + c) >= 2 else 0

gen = CombinationGenerator(
    lfsrs=[
        LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4),
        LFSRConfig(coefficients=[1, 1, 0, 1], field_order=2, degree=4),
        LFSRConfig(coefficients=[1, 0, 1, 1], field_order=2, degree=4)
    ],
    combining_function=majority
)

keystream = gen.generate_keystream(length=1000)

# Basic correlation attack
result = siegenthaler_correlation_attack(gen, keystream, target_lfsr_index=0)
print(f"Correlation: {result.correlation_coefficient:.4f}")

# Fast correlation attack
fast_result = fast_correlation_attack(gen, keystream, target_lfsr_index=0)
if fast_result.attack_successful:
    print(f"Recovered state: {fast_result.recovered_state}")

# Distinguishing attack
dist_result = distinguishing_attack(gen, keystream, method="correlation")
print(f"Distinguishable: {dist_result.distinguishable}")

# NIST statistical tests
nist_result = run_nist_test_suite(keystream)
print(f"Tests passed: {nist_result.passed_count}/{nist_result.total_tests}")
```

## Usage Examples

### Example 1: Basic Analysis

```bash
# Analyze LFSR over GF(2)
lfsr-seq strange.csv 2
```

### Example 2: Multiple LFSR Configurations

Create a CSV file with multiple coefficient vectors:

```csv
1,0,1,1
1,1,0,1,1
1,1,1,0,1,1
```

Then run:
```bash
lfsr-seq my_lfsrs.csv 2
```

The tool will process each row as a separate LFSR configuration.

### Example 3: Non-Binary Fields

```bash
# Analyze LFSR over GF(3)
lfsr-seq coefficients.csv 3

# Analyze LFSR over GF(4) = GF(2²)
lfsr-seq coefficients.csv 4
```

### Example 4: Export to JSON

```bash
lfsr-seq strange.csv 2 --format json --output results.json
```

The JSON file contains structured data:
```json
{
  "metadata": {
    "timestamp": "2025-12-26T...",
    "gf_order": 2,
    "coefficients": [1, 1, 0, 1],
    "lfsr_degree": 4
  },
  "characteristic_polynomial": {
    "polynomial": "t^4 + t^3 + t + 1",
    "order": "15"
  },
  "sequences": { ... },
  "statistics": { ... }
}
```

### Example 5: Verbose Mode

```bash
lfsr-seq strange.csv 2 --verbose
```

Shows detailed information about input files, output location, and processing steps.

### Example 6: Correlation Attack Analysis

```bash
# Basic correlation attack
lfsr-seq dummy.csv 2 --correlation-attack --lfsr-configs config.json

# Fast correlation attack with custom parameters
lfsr-seq dummy.csv 2 --correlation-attack --lfsr-configs config.json \
    --fast-correlation-attack --max-candidates 2000

# Distinguishing attack
lfsr-seq dummy.csv 2 --correlation-attack --lfsr-configs config.json \
    --distinguishing-attack --distinguishing-method correlation
```

### Example 7: NIST SP 800-22 Statistical Tests

```bash
# Run NIST test suite on a sequence
lfsr-seq dummy.csv 2 --nist-test --sequence-file keystream.txt

# Generate HTML report
lfsr-seq dummy.csv 2 --nist-test --sequence-file keystream.txt \
    --nist-output-format html --output nist_report.html
```

## Project Structure

```
lfsr-seq/
├── lfsr/                    # Main package
│   ├── __init__.py         # Package initialization
│   ├── core.py             # Core LFSR mathematics
│   ├── analysis.py         # Sequence analysis algorithms
│   ├── polynomial.py       # Polynomial operations
│   ├── field.py            # Finite field operations
│   ├── io.py               # Input/output handling
│   ├── formatter.py        # Output formatting
│   ├── cli.py              # Command-line interface
│   ├── synthesis.py         # Berlekamp-Massey & LFSR synthesis
│   ├── statistics.py       # Statistical analysis tools
│   ├── export.py           # Multi-format export functions
│   ├── attacks.py          # Correlation attack framework
│   ├── cli_correlation.py  # CLI for correlation attacks
│   ├── cli_nist.py         # CLI for NIST tests
│   ├── nist.py             # NIST SP 800-22 test suite
│   └── constants.py        # Named constants
├── tests/                   # Test suite
│   ├── test_core.py        # Core function tests
│   ├── test_field.py       # Field validation tests
│   ├── test_polynomial.py  # Polynomial operation tests
│   ├── test_io.py          # I/O operation tests
│   ├── test_integration.py # Integration tests
│   ├── test_edge_cases.py  # Edge case tests
│   ├── conftest.py         # Pytest configuration
│   └── fixtures/           # Test data
├── docs/                    # Documentation
│   ├── conf.py             # Sphinx configuration
│   ├── index.rst           # Documentation index
│   ├── installation.rst    # Installation guide
│   ├── user_guide.rst      # User guide
│   ├── api/                # API reference
│   ├── mathematical_background.rst
│   └── examples.rst
├── scripts/                 # Utility scripts
│   ├── check-environment.sh
│   ├── smoke-test.sh
│   ├── test-build.sh
│   └── test-install.sh
├── lfsr-seq                # Main executable script
├── bootstrap               # Automated installation script
├── Makefile                # Development tasks
├── pyproject.toml          # Project metadata and build config
├── requirements.txt        # Runtime dependencies
├── requirements-dev.txt    # Development dependencies
├── strange.csv             # Sample input file
└── README.md               # This file
```

## Development

### Setting Up Development Environment

**Using bootstrap (recommended):**
```bash
# Creates venv and installs dev dependencies
./bootstrap --dev

# Activate the virtual environment
source .venv/bin/activate
```

**Using Make:**
```bash
# Create venv and install dev dependencies
make dev-setup

# Activate the virtual environment
source .venv/bin/activate
```

**Manual setup:**
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"
```

**Important:** Always activate the virtual environment before working
  on the project:
```bash
source .venv/bin/activate
```

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run specific test file
pytest tests/test_core.py -v

# Run tests matching a pattern
pytest tests/ -k "test_matrix" -v

# Skip slow tests
pytest tests/ -m "not slow"
```

### Code Quality

```bash
# Format code
make format

# Check formatting
make format-check

# Run linting
make lint

# Type checking
make type-check

# Run all checks (for CI)
make ci
```

### Building Distribution Packages

```bash
make build
```

This creates distribution packages in the `dist/` directory.

### Building Documentation

The project uses Sphinx for documentation. See `docs/BUILDING.md` for
detailed instructions.

**Quick Start:**

```bash
# Build HTML documentation (recommended)
make docs

# Clean documentation build artifacts
make docs-clean

# Start live documentation server (auto-reload on changes)
make docs-live
```

**Manual Build:**

```bash
# Install Sphinx and theme
pip install sphinx sphinx-rtd-theme

# Build documentation
cd docs
sphinx-build -b html . _build/html

# Documentation will be in docs/_build/html/
# Open docs/_build/html/index.html in your browser
```

**Documentation Structure:**
- User documentation: Installation, user guide, examples, mathematical background
- API reference: Complete documentation for all modules and functions
- Build guide: See `docs/BUILDING.md` for detailed build instructions

The documentation includes:
- Comprehensive API reference for all modules
- Usage examples and tutorials
- Mathematical background and theory
- Installation and setup guides

### Cleaning and Uninstallation

```bash
# Remove build artifacts
make clean

# Remove virtual environment
make clean-venv

# Deep clean (remove all generated files including venv)
make distclean

# Uninstall the package
make uninstall
```

**Using bootstrap script:**

```bash
# Clean build artifacts and caches
./bootstrap --clean

# Uninstall the package
./bootstrap --uninstall
```

**Note:** The `--clean` and `--uninstall` options in bootstrap do not
  remove the virtual environment. To remove it, use `make clean-venv`
  or `rm -rf .venv`.

## Verification

After installation, verify everything works:

```bash
# Check environment
./scripts/check-environment.sh

# Run smoke tests
./scripts/smoke-test.sh

# Or use make
make check-env
make smoke-test
```

## Troubleshooting

### "SageMath not found"

Install SageMath via your system package manager (see Prerequisites
section). The tool will skip tests that require SageMath if it's not
available.

### "Permission denied" on script execution

Make the script executable:
```bash
chmod +x lfsr-seq
```

Or run directly with Python:
```bash
python3 lfsr-seq strange.csv 2
```

Or use the installed command (after installation):
```bash
lfsr-seq strange.csv 2
```

### "Module not found" after installation

Ensure you're in the project directory, have activated the virtual
environment, and the package is installed:
```bash
# Activate virtual environment (if using one)
source .venv/bin/activate

# Install the package
pip install -e .
```

### Virtual environment issues

If you encounter issues with the virtual environment:

```bash
# Remove and recreate
rm -rf .venv
make venv
# or
python3 -m venv .venv

# Activate and reinstall
source .venv/bin/activate
pip install -e ".[dev]"
```

### Tests fail with "SageMath not available"

This is expected if SageMath is not installed. Tests will
automatically skip if SageMath is not available. Install SageMath to
run the full test suite.

### "File too large" error

The tool has security limits:
- Maximum file size: 10 MB
- Maximum CSV rows: 10,000

If you need to process larger files, you can modify the limits in `lfsr/constants.py`.

## Mathematical Background

This tool is motivated by exercise 2 of Tanja Lange's cryptology course:
- [Course Website](https://www.hyperelliptic.org/tanja/teaching/CS22/)

The tool finds periods of all possible states with *d* number of
entries defined over *GF(gf_order)* for a specific LFSR, and arranges
them in sequences. The order of the Characteristic Polynomial of the
LFSR is also obtained alongside the orders of its factors to be
compared with the periods of the listed sequences.

### Key Concepts

- **Linear Feedback Shift Register (LFSR)**: A shift register whose input is a linear function of its previous state
- **State Update Matrix**: Matrix representation of LFSR state transitions
- **Characteristic Polynomial**: Polynomial whose roots determine LFSR properties
- **Period**: Length of cycle before LFSR returns to initial state
- **Primitive Polynomial**: Polynomial that yields maximum-period LFSRs
- **Linear Complexity**: Length of shortest LFSR that can generate a sequence
- **Berlekamp-Massey Algorithm**: Algorithm for synthesizing LFSRs from sequences
- **Combination Generator**: Multiple LFSRs combined with a non-linear function
- **Correlation Attack**: Cryptanalytic technique exploiting correlations in combination generators
- **Fast Correlation Attack**: Advanced attack using iterative decoding for state recovery
- **Distinguishing Attack**: Technique to detect if keystream is distinguishable from random
- **NIST SP 800-22**: Industry-standard statistical test suite for randomness

For detailed mathematical background, see the [documentation](docs/mathematical_background.rst).
For correlation attack theory and usage, see [Correlation Attacks Guide](docs/correlation_attacks.rst).
For NIST test suite documentation, see [NIST SP 800-22 Guide](docs/nist_sp800_22.rst).

## Contributing

Contributions are welcome! Please ensure:

1. **Code Quality:**
   - Code follows the project's style guidelines (black formatting)
   - Tests pass (`make test`)
   - Code is formatted (`make format`)
   - Linting passes (`make lint`)
   - Type checking passes (`make type-check`)

2. **Testing:**
   - Add tests for new features
   - Maintain test coverage above 90%
   - Run full test suite before submitting

3. **Documentation:**
   - Update docstrings for new functions
   - Add examples to docstrings
   - Update README if needed

4. **Commit Messages:**
   - Use clear, descriptive commit messages
   - Reference issue numbers if applicable

### Development Workflow

```bash
# 1. Create a feature branch
git checkout -b feature/my-feature

# 2. Make changes and test
make test
make lint
make format

# 3. Commit changes
git commit -m "Add feature X"

# 4. Push and create pull request
git push origin feature/my-feature
```

## Testing

The project includes comprehensive test coverage:

- **Unit Tests**: Test individual functions and modules
- **Integration Tests**: Test complete workflows
- **Edge Case Tests**: Test boundary conditions and special cases
- **Test Fixtures**: Known LFSR configurations for validation

Run tests with:
```bash
make test          # Run all tests
make test-cov      # Run with coverage report
pytest tests/ -v   # Run with verbose output
```

Test coverage is maintained above 90% and enforced in CI.

## CI/CD

The project uses GitHub Actions for continuous integration:

- **Automated Testing**: Tests run on Python 3.8-3.13
- **Linting**: Automated code quality checks
- **Type Checking**: Automated type validation
- **Build Verification**: Ensures package builds correctly

See `.github/workflows/ci.yml` for configuration.

## License

**GNU GPL v3+**

Copyright (C) 2023-2025 Mohammadreza Khellat

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3, or (at your option)
any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
USA.

See also https://www.gnu.org/licenses/gpl.html

## Acknowledgments

- Inspired by Tanja Lange's cryptology course exercises
- Built with [SageMath](https://www.sagemath.org/)
- Uses modern Python packaging standards (PEP 517, PEP 518, PEP 621)

## Related Resources

- [SageMath Documentation](https://doc.sagemath.org/)
- [Tanja Lange's Cryptology Course](https://www.hyperelliptic.org/tanja/teaching/CS22/)
- [GNU GPL License](https://www.gnu.org/licenses/gpl.html)

---

**Version**: 0.3.0  
**Last Updated**: 2025-12-27
