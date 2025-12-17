#!/bin/sh
# test-build.sh - Test the build process for lfsr-seq
#
# This script tests that the build system works correctly.
# It should be run in a clean environment with proper Python setup.
#
# Usage: ./scripts/test-build.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Testing build process for lfsr-seq..."
echo ""

cd "$PROJECT_ROOT"

# Check if we're in a virtual environment or if build tools are available
if ! python3 -c "import build" 2>/dev/null; then
    echo "Installing build tools..."
    python3 -m pip install --upgrade pip build setuptools wheel
fi

# Clean any previous builds
echo "Cleaning previous build artifacts..."
rm -rf build/ dist/ *.egg-info

# Run the build
echo "Running build..."
python3 -m build

# Verify build artifacts were created
echo ""
echo "Verifying build artifacts..."
if [ -d "dist" ]; then
    echo "  ✓ dist/ directory created"
    
    # Check for source distribution
    if ls dist/*.tar.gz 1>/dev/null 2>&1; then
        SDIST_FILE=$(ls dist/*.tar.gz | head -1)
        echo "  ✓ Source distribution created: $(basename "$SDIST_FILE")"
    else
        echo "  ✗ Source distribution not found"
        exit 1
    fi
    
    # Check for wheel
    if ls dist/*.whl 1>/dev/null 2>&1; then
        WHEEL_FILE=$(ls dist/*.whl | head -1)
        echo "  ✓ Wheel created: $(basename "$WHEEL_FILE")"
    else
        echo "  ✗ Wheel not found"
        exit 1
    fi
    
    echo ""
    echo "Build test completed successfully!"
    echo ""
    echo "Build artifacts:"
    ls -lh dist/
else
    echo "  ✗ dist/ directory not created"
    exit 1
fi

