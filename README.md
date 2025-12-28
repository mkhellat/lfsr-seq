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
- **Algebraic Attack Framework**: Advanced cryptanalytic techniques exploiting algebraic structure
  - **Algebraic Immunity Computation**: Compute resistance to algebraic attacks
  - **Gröbner Basis Attacks**: Solve polynomial systems to recover LFSR state
  - **Cube Attacks**: Exploit low-degree relations using cube selection
  - **Security Analysis**: Evaluate algebraic properties of filtering functions
- **Time-Memory Trade-Off Attacks**: Efficient state recovery through precomputation
  - **Hellman Tables**: Classic TMTO technique with chain-based tables
  - **Rainbow Tables**: Improved TMTO with multiple reduction functions
  - **Parameter Optimization**: Find optimal trade-off parameters
  - **Precomputation Support**: Generate and reuse tables for multiple attacks
- **Stream Cipher Analysis**: Real-world stream cipher analysis framework
  - **A5/1 and A5/2**: GSM mobile phone encryption ciphers (3-4 LFSRs with irregular clocking)
  - **E0**: Bluetooth encryption cipher (4 LFSRs with FSM combiner)
  - **Trivium**: eSTREAM finalist (3 shift registers with non-linear feedback)
  - **Grain Family**: Grain-128 and Grain-128a eSTREAM finalists (LFSR + NFSR with filter function)
  - **LILI-128**: Academic design demonstrating clock-controlled LFSRs
  - **Cipher Comparison**: Side-by-side analysis of multiple cipher designs
  - **Structure Analysis**: Analyze LFSR configurations, clocking mechanisms, combining functions
  - **Keystream Generation**: Generate keystreams from keys and IVs
- **Advanced LFSR Structures**: Extensions beyond basic linear LFSRs
  - **NFSRs**: Non-Linear Feedback Shift Registers (NOT LFSRs - non-linear feedback)
  - **Filtered LFSRs**: LFSRs with non-linear output filtering (ARE LFSRs - linear feedback)
  - **Clock-Controlled LFSRs**: LFSRs with irregular clocking patterns (ARE LFSRs - linear feedback)
  - **Multi-Output LFSRs**: LFSRs producing multiple output bits per step (ARE LFSRs - linear feedback)
  - **Irregular Clocking Patterns**: LFSRs with variable clocking patterns (ARE LFSRs - linear feedback)
  - **Structure Analysis**: Analyze properties, security, and sequence characteristics
- **Theoretical Analysis**: Research-oriented analysis and publication features
  - **Irreducible Polynomial Analysis**: Comprehensive factorization and order analysis
  - **LaTeX Export**: Publication-quality output for research papers
  - **Research Paper Generation**: Automatic generation of paper sections
  - **Known Result Database**: Compare with known theoretical results
  - **Benchmarking Framework**: Performance and accuracy comparisons
  - **Reproducibility Features**: Seed tracking, environment capture, configuration export
- **Machine Learning Integration**: ML-based analysis capabilities
  - **Period Prediction**: Predict LFSR periods from polynomial structure using ML
  - **Pattern Detection**: Automatically detect patterns in sequences and transitions
  - **Anomaly Detection**: Identify anomalies in sequences and distributions
  - **Model Training**: Train custom ML models for specific analysis tasks
  - **Feature Extraction**: Extract features from polynomials and sequences
- **Advanced Visualization**: Interactive and publication-quality visualizations
  - **Period Distribution Plots**: Histograms and statistical plots of period distributions
  - **State Transition Diagrams**: Graph visualizations of state transitions and cycles
  - **Statistical Plots**: Publication-quality plots (histograms, box plots, cumulative distributions)
  - **3D State Space Visualization**: Interactive 3D plots of state spaces
  - **Attack Visualization**: Visual representation of cryptanalytic attacks
  - **Multiple Formats**: Export to PNG, SVG, PDF, HTML (interactive)
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
- **Period Computation via Factorization**: 10-100x faster for large LFSRs (degree > 15)
- **Result Caching System**: In-memory and persistent caching for repeated analyses
- **Mathematical Shortcut Detection**: Automatic detection of special cases (primitive, irreducible, etc.)
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
  --algebraic-attack   Perform algebraic attack analysis on LFSRs
  --algebraic-method METHOD
                        Method: 'groebner_basis', 'cube_attack', or
                        'algebraic_immunity' (default: groebner_basis)
  --max-cube-size N    Maximum cube size for cube attack (default: 10)
  --max-equations N     Maximum equations for Gröbner basis (default: 1000)
  --tmto-attack        Perform time-memory trade-off attack
  --tmto-method METHOD
                        TMTO method: 'hellman' or 'rainbow' (default: hellman)
  --chain-count N      Number of chains in TMTO table (default: 1000)
  --chain-length N     Length of each chain (default: 100)
  --tmto-table-file FILE
                        File with precomputed TMTO table (JSON format)
  --cipher NAME         Select stream cipher: a5_1, a5_2, e0, trivium,
                        grain128, grain128a, or lili128
  --analyze-cipher      Analyze cipher structure (LFSRs, clocking, etc.)
  --generate-keystream  Generate keystream from key and IV
  --keystream-length N  Length of keystream to generate (default: 1000)
  --key-file FILE       File containing key bits (binary or text format)
  --iv-file FILE        File containing IV bits (binary or text format)
  --compare-ciphers     Compare multiple ciphers side-by-side
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
   
   # Algebraic attacks
   from lfsr.attacks import (
       LFSRConfig,
       compute_algebraic_immunity,
       groebner_basis_attack,
       cube_attack
   )
   
   lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
   
   # Compute algebraic immunity
   def filtering_function(x0, x1, x2, x3):
       return x0 & x1
   
   ai_result = compute_algebraic_immunity(filtering_function, 4)
   print(f"Algebraic immunity: {ai_result['algebraic_immunity']}")
   
   # Gröbner basis attack
   gb_result = groebner_basis_attack(lfsr, keystream)
   if gb_result.attack_successful:
       print(f"Recovered state: {gb_result.recovered_state}")
   
   # Cube attack
   cube_result = cube_attack(lfsr, keystream, max_cube_size=5)
   if cube_result.attack_successful:
       print(f"Cubes found: {cube_result.cubes_found}")
   
   # Time-Memory Trade-Off attacks
   from lfsr.tmto import tmto_attack, optimize_tmto_parameters
   
   target_state = [1, 0, 1, 1]
   tmto_result = tmto_attack(
       lfsr_config=lfsr,
       target_state=target_state,
       method="hellman",
       chain_count=1000,
       chain_length=100
   )
   if tmto_result.attack_successful:
       print(f"Recovered state: {tmto_result.recovered_state}")
       print(f"Coverage: {tmto_result.coverage:.2%}")
   
   # Parameter optimization
   params = optimize_tmto_parameters(
       state_space_size=16,
       available_memory=100000
   )
   print(f"Optimal chain count: {params['chain_count']}")
   
   # Stream cipher analysis
   from lfsr.ciphers import A5_1, E0, Trivium, Grain128
   from lfsr.ciphers.comparison import compare_ciphers, generate_comparison_report
   
   # Analyze A5/1 cipher
   a5_1 = A5_1()
   structure = a5_1.analyze_structure()
   print(f"A5/1 has {len(structure.lfsr_configs)} LFSRs")
   
   # Generate keystream
   key = [1] * 64
   iv = [0] * 22
   keystream = a5_1.generate_keystream(key, iv, 1000)
   print(f"Generated {len(keystream)} keystream bits")
   
   # Compare ciphers
   comparison = compare_ciphers([A5_1(), E0(), Trivium()])
   report = generate_comparison_report(comparison)
   print(report)
   
   # Optimization techniques
   from lfsr.polynomial import (
       compute_period_via_factorization,
       detect_mathematical_shortcuts
   )
   from lfsr.optimization import ResultCache, get_global_cache
   
   # Period computation via factorization (faster for large LFSRs)
   period = compute_period_via_factorization([1, 0, 0, 1], 2)
   
   # Detect mathematical shortcuts
   shortcuts = detect_mathematical_shortcuts([1, 0, 0, 1], 2)
   if shortcuts['is_primitive']:
       print(f"Primitive polynomial! Period = {shortcuts['expected_period']}")
   
   # Result caching
   cache = get_global_cache()
   key = cache.generate_key([1, 0, 0, 1], 2, "period")
   if key in cache:
       period = cache.get(key)
   else:
       period = compute_period_via_factorization([1, 0, 0, 1], 2)
       cache.set(key, period)
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

### Example 8: Algebraic Attacks

```bash
# Compute algebraic immunity
lfsr-seq coefficients.csv 2 --algebraic-attack \
    --algebraic-method algebraic_immunity

# Gröbner basis attack
lfsr-seq coefficients.csv 2 --algebraic-attack \
    --algebraic-method groebner_basis --max-equations 500

# Cube attack
lfsr-seq coefficients.csv 2 --algebraic-attack \
    --algebraic-method cube_attack --max-cube-size 8
```

### Example 9: Time-Memory Trade-Off Attacks

```bash
# Hellman table attack
lfsr-seq coefficients.csv 2 --tmto-attack --tmto-method hellman

# Rainbow table attack with custom parameters
lfsr-seq coefficients.csv 2 --tmto-attack --tmto-method rainbow \
    --chain-count 2000 --chain-length 150

# Use precomputed table
lfsr-seq coefficients.csv 2 --tmto-attack --tmto-table-file table.json
```

### Example 10: Stream Cipher Analysis

```bash
# Analyze A5/1 cipher structure
lfsr-seq --cipher a5_1 --analyze-cipher

# Generate keystream from key and IV
lfsr-seq --cipher a5_1 --generate-keystream \
    --key-file key.bin --iv-file iv.bin --keystream-length 1000

# Compare multiple ciphers
lfsr-seq --cipher a5_1 --compare-ciphers

# Analyze E0 Bluetooth cipher
lfsr-seq --cipher e0 --analyze-cipher --generate-keystream
```

### Example 11: Advanced LFSR Structures

```bash
# Analyze filtered LFSR structure
lfsr-seq coefficients.csv 2 --advanced-structure filtered \
    --analyze-advanced-structure

# Generate sequence from NFSR
lfsr-seq coefficients.csv 2 --advanced-structure nfsr \
    --generate-advanced-sequence --advanced-sequence-length 2000

# Analyze clock-controlled LFSR
lfsr-seq coefficients.csv 2 --advanced-structure clock_controlled \
    --analyze-advanced-structure --generate-advanced-sequence
```

### Example 12: Theoretical Analysis

```bash
# Export results to LaTeX
lfsr-seq coefficients.csv 2 --export-latex results.tex

# Generate research paper
lfsr-seq coefficients.csv 2 --generate-paper paper.tex

# Compare with known results
lfsr-seq coefficients.csv 2 --compare-known

# Run benchmarks
lfsr-seq coefficients.csv 2 --benchmark

# Generate reproducibility report
lfsr-seq coefficients.csv 2 --reproducibility-report report.json
```

### Example 13: Machine Learning Analysis

```bash
# Predict period using ML model
lfsr-seq coefficients.csv 2 --ml-predict-period

# Detect patterns in sequence
lfsr-seq coefficients.csv 2 --ml-detect-patterns --sequence-length 1000

# Detect anomalies
lfsr-seq coefficients.csv 2 --ml-detect-anomalies

# Train custom ML model
lfsr-seq coefficients.csv 2 --ml-train --model-type period_predictor
```

### Example 14: Visualization

```bash
# Generate period distribution plot
lfsr-seq coefficients.csv 2 --plot-period-distribution period_dist.png

# Generate state transition diagram
lfsr-seq coefficients.csv 2 --plot-state-transitions transitions.png

# Generate 3D state space visualization (interactive HTML)
lfsr-seq coefficients.csv 2 --plot-3d-state-space state_space.html --viz-interactive

# Generate statistical plots
lfsr-seq coefficients.csv 2 --plot-period-statistics stats.png

# Visualize attack results
lfsr-seq coefficients.csv 2 --visualize-attack attack.png
```

### Example 14: Advanced Visualization

```bash
# Generate period distribution plot
lfsr-seq coefficients.csv 2 --plot-period-distribution period_dist.png

# Generate state transition diagram
lfsr-seq coefficients.csv 2 --plot-state-transitions state_diagram.png

# Generate statistical plots
lfsr-seq coefficients.csv 2 --plot-period-statistics stats.png

# Generate interactive 3D visualization
lfsr-seq coefficients.csv 2 --plot-3d-state-space state_space.html --viz-interactive

# Visualize attack results
lfsr-seq coefficients.csv 2 --visualize-attack attack.png
```

## Project Structure

```
lfsr-seq/
├── lfsr/                    # Main package
│   ├── __init__.py         # Package initialization
│   ├── core.py             # Core LFSR mathematics
│   ├── analysis.py         # Sequence analysis algorithms
│   ├── polynomial.py       # Polynomial operations & optimization
│   ├── field.py            # Finite field operations
│   ├── io.py               # Input/output handling
│   ├── formatter.py        # Output formatting
│   ├── cli.py              # Command-line interface
│   ├── synthesis.py         # Berlekamp-Massey & LFSR synthesis
│   ├── statistics.py       # Statistical analysis tools
│   ├── export.py           # Multi-format export functions
│   ├── optimization.py     # Result caching & optimization utilities
│   ├── attacks.py          # Correlation & algebraic attack framework
│   ├── tmto.py             # Time-memory trade-off attacks
│   ├── ciphers/            # Stream cipher analysis
│   │   ├── __init__.py     # Cipher module initialization
│   │   ├── base.py         # Base classes and interfaces
│   │   ├── a5_1.py         # A5/1 GSM cipher
│   │   ├── a5_2.py         # A5/2 GSM cipher
│   │   ├── e0.py           # E0 Bluetooth cipher
│   │   ├── trivium.py      # Trivium eSTREAM finalist
│   │   ├── grain.py        # Grain family
│   │   ├── lili128.py      # LILI-128 academic design
│   │   └── comparison.py   # Cipher comparison framework
│   ├── advanced/           # Advanced LFSR structures
│   │   ├── __init__.py     # Advanced structures module initialization
│   │   ├── base.py         # Base classes and interfaces
│   │   ├── nonlinear.py    # NFSRs (Non-Linear Feedback Shift Registers)
│   │   ├── filtered.py     # Filtered LFSRs
│   │   ├── clock_controlled.py  # Clock-controlled LFSRs
│   │   ├── multi_output.py # Multi-output LFSRs
│   │   └── irregular_clocking.py  # Irregular clocking patterns
│   ├── theoretical.py     # Theoretical analysis (irreducible polynomials)
│   ├── export_latex.py    # LaTeX export functionality
│   ├── paper_generator.py # Research paper generation
│   ├── theoretical_db.py  # Known result database
│   ├── benchmarking.py    # Benchmarking framework
│   ├── reproducibility.py # Reproducibility features
│   └── ml/                # Machine learning integration
│       ├── __init__.py    # ML module initialization
│       ├── base.py        # Base ML classes and interfaces
│       ├── features.py    # Feature extraction
│       ├── models.py      # ML models
│       ├── period_prediction.py  # Period prediction models
│       ├── pattern_detection.py  # Pattern detection
│       ├── anomaly_detection.py  # Anomaly detection
│       └── training.py    # Model training pipeline
│   ├── visualization/     # Advanced visualization
│       ├── __init__.py    # Visualization module initialization
│       ├── base.py        # Base classes and configuration
│       ├── period_graphs.py  # Period distribution visualizations
│       ├── state_diagrams.py  # State transition diagrams
│       ├── statistical_plots.py  # Statistical distribution plots
│       ├── state_space_3d.py  # 3D state space visualizations
│       └── attack_visualization.py  # Attack visualizations
│   ├── cli_correlation.py  # CLI for correlation attacks
│   ├── cli_algebraic.py    # CLI for algebraic attacks
│   ├── cli_tmto.py         # CLI for TMTO attacks
│   ├── cli_ciphers.py      # CLI for stream cipher analysis
│   ├── cli_advanced.py     # CLI for advanced LFSR structures
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
- **Algebraic Attack**: Technique exploiting algebraic relationships to recover secrets
- **Algebraic Immunity**: Security measure for Boolean functions against algebraic attacks
- **Gröbner Basis**: Mathematical tool for solving polynomial systems
- **Cube Attack**: Algebraic attack exploiting low-degree relations
- **Time-Memory Trade-Off (TMTO)**: Technique trading memory for computation time
- **Hellman Table**: Precomputed table for fast state recovery
- **Rainbow Table**: Improved TMTO table with multiple reduction functions
- **Stream Cipher**: Symmetric encryption algorithm encrypting data one bit at a time
- **Keystream**: Pseudorandom sequence generated by stream cipher
- **Irregular Clocking**: LFSRs don't always advance (clock control mechanism)
- **Finite State Machine (FSM)**: Memory element providing non-linear combining
- **NFSR**: Non-Linear Feedback Shift Register (NOT an LFSR - non-linear feedback)
- **Filtered LFSR**: LFSR (linear feedback) with non-linear output filtering
- **Clock-Controlled LFSR**: LFSR (linear feedback) with irregular clocking
- **Multi-Output LFSR**: LFSR (linear feedback) with multiple outputs per step
- **Theoretical Analysis**: Research-oriented analysis comparing computed results with theoretical predictions
- **LaTeX Export**: Converting analysis results to LaTeX format for research papers
- **Reproducibility**: Ability to reproduce research results using same methods and parameters
- **Benchmarking**: Measuring and comparing performance of different analysis methods
- **Known Result Database**: Collection of known theoretical results for verification
- **Machine Learning Integration**: ML-based analysis for period prediction, pattern detection, and anomaly detection
- **Period Prediction**: ML models to predict LFSR periods from polynomial structure
- **Pattern Detection**: Automatic detection of patterns in sequences and state transitions
- **Anomaly Detection**: Identification of anomalies in sequences and distributions
- **Visualization**: Interactive and publication-quality graphical representations of analysis results
- **Period Distribution Plot**: Histogram showing distribution of periods across initial states
- **State Transition Diagram**: Graph showing how states transition and form cycles
- **3D State Space Visualization**: Interactive 3D representation of state spaces
- **Attack Visualization**: Visual representation of cryptanalytic attack progress and results
- **NIST SP 800-22**: Industry-standard statistical test suite for randomness
- **Period Computation via Factorization**: Efficient period computation using polynomial factorization
- **Result Caching**: Storing computed results for reuse without recomputation
- **Mathematical Shortcut Detection**: Automatic detection of special cases for optimized computation

For detailed mathematical background, see the [documentation](docs/mathematical_background.rst).
For correlation attack theory and usage, see [Correlation Attacks Guide](docs/correlation_attacks.rst).
For algebraic attack theory and usage, see [Algebraic Attacks Guide](docs/algebraic_attacks.rst).
For time-memory trade-off attacks, see [TMTO Attacks Guide](docs/time_memory_tradeoff.rst).
For stream cipher analysis, see [Stream Ciphers Guide](docs/stream_ciphers.rst).
For advanced LFSR structures, see [Advanced LFSR Structures Guide](docs/advanced_lfsr_structures.rst).
For theoretical analysis features, see [Theoretical Analysis Guide](docs/theoretical_analysis.rst).
For machine learning features, see [Machine Learning Guide](docs/machine_learning.rst) (if available).
For visualization features, see [Visualization Guide](docs/visualization.rst).
For NIST test suite documentation, see [NIST SP 800-22 Guide](docs/nist_sp800_22.rst).
For optimization techniques, see [Optimization Techniques Guide](docs/optimization_techniques.rst).

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
