#!/bin/sh
# test-install.sh - Test the installation process for lfsr-seq
#
# This script tests that the package can be installed correctly.
# It should be run in a clean virtual environment.
#
# Usage: ./scripts/test-install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Testing installation process for lfsr-seq..."
echo ""

cd "$PROJECT_ROOT"

# Check if we're in a virtual environment (recommended)
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠ WARNING: Not in a virtual environment"
    echo "  It's recommended to test installation in a virtual environment"
    echo "  Create one with: python3 -m venv test-venv && source test-venv/bin/activate"
    echo ""
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [ ! "$REPLY" = "y" ] && [ ! "$REPLY" = "Y" ]; then
        exit 1
    fi
fi

# Verify pyproject.toml exists
if [ ! -f "pyproject.toml" ]; then
    echo "✗ ERROR: pyproject.toml not found"
    exit 1
fi
echo "✓ pyproject.toml found"

# Test basic installation
echo "Testing basic installation (pip install -e .)..."
if pip install -e . >/dev/null 2>&1; then
    echo "  ✓ Basic installation successful"
else
    echo "  ✗ Basic installation failed"
    exit 1
fi

# Test installation with dev dependencies
echo "Testing installation with dev dependencies (pip install -e .[dev])..."
if pip install -e ".[dev]" >/dev/null 2>&1; then
    echo "  ✓ Installation with dev dependencies successful"
else
    echo "  ⚠ Installation with dev dependencies failed (may be expected if dependencies unavailable)"
fi

# Verify package metadata
echo ""
echo "Verifying package installation..."
if python3 -c "import pkg_resources; dist = pkg_resources.get_distribution('lfsr-seq'); print(f'  ✓ Package installed: {dist.project_name} version {dist.version}')" 2>/dev/null; then
    echo "  ✓ Package metadata accessible"
else
    echo "  ⚠ Could not verify package metadata (may be expected in editable mode)"
fi

echo ""
echo "Installation test completed!"
echo ""
echo "Note: Entry point verification requires package refactoring"
echo "      (currently lfsr-seq is a standalone script)"

