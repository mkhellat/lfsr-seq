# lfsr-seq

**Linear Feedback Shift Register (LFSR) Sequence Analysis Tool**

A tool for analyzing Linear Feedback Shift Register sequences, computing periods, and determining characteristic polynomials over finite fields. This tool is useful for cryptographic research, stream cipher analysis, and educational purposes.

## Features

- Analyze LFSR sequences and compute periods
- Determine characteristic polynomials and their orders
- Support for multiple finite fields (GF(p) where p is prime)
- Process multiple LFSR coefficient vectors from CSV files
- Detailed output with sequence tables and polynomial factorization

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
# Basic installation
./bootstrap

# With development dependencies
./bootstrap --dev
```

The bootstrap script will:
- Check your Python and SageMath installation
- Upgrade pip and build tools
- Install the package in development mode
- Run smoke tests to verify installation

### Manual Installation

1. **Check your environment:**
   ```bash
   ./scripts/check-environment.sh
   ```

2. **Install the package:**
   ```bash
   # Basic installation
   pip install -e .

   # With development dependencies
   pip install -e ".[dev]"
   ```

### Using Make

If you have `make` installed:

```bash
# Install with development dependencies
make install-dev

# Or just basic installation
make install
```

## Quick Start

### Basic Usage

```bash
./lfsr-seq <coeffs_csv_filename> <GF_order>
```

**Example:**
```bash
./lfsr-seq strange.csv 2
```

This will:
- Read LFSR coefficients from `strange.csv`
- Analyze sequences over GF(2)
- Generate output in `strange.csv.out`

### Input Format

The CSV file should contain one or more rows of LFSR coefficients. Each row represents a different LFSR configuration:

```csv
1,1,1,0,0,0,0,0,1,1
1,1,1,0,0,0,0,0,1,1,0,1,1,1,0
1,1,1,0,0,0,0,0,1,1,0,1,1,1,1
```

Each coefficient should be in the range [0, GF_order-1].

### Output

The tool generates detailed output including:
- State update matrix
- All possible state sequences with their periods
- Characteristic polynomial and its order
- Factorization of the characteristic polynomial

Output is written to both:
- Console (summary)
- Output file (`<input_file>.out` with full details)

## Development

### Setting Up Development Environment

```bash
# Run bootstrap with dev dependencies
./bootstrap --dev

# Or use make
make dev-setup
```

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run smoke tests
make smoke-test
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

### Cleaning

```bash
# Remove build artifacts
make clean

# Deep clean (remove all generated files)
make distclean
```

## Project Structure

```
lfsr-seq/
├── lfsr-seq              # Main script
├── bootstrap             # Automated installation script
├── Makefile              # Development tasks
├── pyproject.toml        # Project metadata and build config
├── requirements.txt      # Runtime dependencies
├── requirements-dev.txt  # Development dependencies
├── scripts/
│   ├── check-environment.sh  # Environment validation
│   └── smoke-test.sh         # Basic functionality tests
├── strange.csv           # Sample input file
└── README.md             # This file
```

## Usage Examples

### Example 1: Basic Analysis

```bash
# Analyze LFSR over GF(2)
./lfsr-seq strange.csv 2
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
./lfsr-seq my_lfsrs.csv 2
```

The tool will process each row as a separate LFSR configuration.

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

Install SageMath via your system package manager (see Prerequisites section).

### "Permission denied" on script execution

Make the script executable:
```bash
chmod +x lfsr-seq
```

Or run directly with Python:
```bash
python3 lfsr-seq strange.csv 2
```

### "Module not found" after installation

Ensure you're in the project directory and the package is installed:
```bash
pip install -e .
```

## Mathematical Background

This tool is motivated by exercise 2 of Tanja Lange's cryptology course:
- [Course Website](https://www.hyperelliptic.org/tanja/teaching/CS22/)

The tool finds periods of all possible states with *d* number of entries defined over *GF(gf_order)* for a specific LFSR, and arranges them in sequences. The order of the Characteristic Polynomial of the LFSR is also obtained alongside the orders of its factors to be compared with the periods of the listed sequences.

## Contributing

Contributions are welcome! Please ensure:
- Code follows the project's style guidelines
- Tests pass (`make test`)
- Code is formatted (`make format`)
- Linting passes (`make lint`)

## License

**GNU GPL v3+**

Copyright (C) 2023 Mohammadreza Khellat

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 3, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

See also https://www.gnu.org/licenses/gpl.html

## Acknowledgments

- Inspired by Tanja Lange's cryptology course exercises
- Built with [SageMath](https://www.sagemath.org/)
