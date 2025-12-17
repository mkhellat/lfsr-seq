#!/bin/sh
# check-environment.sh - Verify execution environment for lfsr-seq
#
# This script checks that all required dependencies are available
# for running lfsr-seq on a POSIX-compliant system.
#
# Exit codes:
#   0 - All checks passed
#   1 - One or more checks failed

set -e

echo "Checking execution environment for lfsr-seq..."
echo ""

# Check Python version
echo "Checking Python..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo "  ✗ ERROR: Python 3.8+ required, found $PYTHON_VERSION"
    exit 1
fi
echo "  ✓ Python version: $PYTHON_VERSION"

# Check SageMath
echo "Checking SageMath..."
if ! python3 -c "import sage.all" 2>/dev/null; then
    echo "  ✗ ERROR: SageMath not found"
    echo ""
    echo "  Please install SageMath via your system package manager:"
    echo "    Debian/Ubuntu: sudo apt-get install sagemath"
    echo "    Fedora/RHEL:   sudo dnf install sagemath"
    echo "    Arch Linux:    sudo pacman -S sagemath"
    echo "    macOS:         brew install sagemath"
    echo "    Conda:         conda install -c conda-forge sage"
    exit 1
fi

SAGE_VERSION=$(python3 -c "import sage; print(sage.__version__)" 2>/dev/null || echo "unknown")
echo "  ✓ SageMath version: $SAGE_VERSION"

# Check required Python standard library modules
echo "Checking Python standard library modules..."
REQUIRED_MODULES="sys csv os platform datetime textwrap"
MISSING_MODULES=""

for module in $REQUIRED_MODULES; do
    if ! python3 -c "import $module" 2>/dev/null; then
        MISSING_MODULES="$MISSING_MODULES $module"
    fi
done

if [ -n "$MISSING_MODULES" ]; then
    echo "  ✗ WARNING: Missing standard library modules:$MISSING_MODULES"
    echo "    This is unusual - Python installation may be incomplete"
else
    echo "  ✓ All required standard library modules available"
fi

# Check optional curses module (used for progress display)
if python3 -c "import curses" 2>/dev/null; then
    echo "  ✓ curses module available (for progress display)"
else
    echo "  ⚠ WARNING: curses module not available (progress display may be limited)"
fi

# Check pip availability (for installation)
echo "Checking pip..."
if command -v pip3 >/dev/null 2>&1 || python3 -m pip --version >/dev/null 2>&1; then
    echo "  ✓ pip available for package installation"
else
    echo "  ⚠ WARNING: pip not found (needed for package installation)"
fi

echo ""
echo "Environment check completed successfully!"
echo ""
echo "You can now:"
echo "  - Run the script directly: ./lfsr-seq <csv_file> <gf_order>"
echo "  - Or install the package: pip install -e ."

