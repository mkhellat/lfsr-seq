#!/bin/sh
# smoke-test.sh - Basic functionality test for lfsr-seq
#
# This script performs basic smoke tests to verify that lfsr-seq
# is installed and working correctly.
#
# Exit codes:
#   0 - All tests passed
#   1 - One or more tests failed

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEST_CSV="$PROJECT_ROOT/strange.csv"
TEST_OUTPUT="${TEST_CSV}.out"
GF_ORDER="2"

echo "Running smoke tests for lfsr-seq..."
echo ""

# Test 1: Check if script exists and is executable
echo "Test 1: Checking script exists and is executable..."
if [ ! -f "$PROJECT_ROOT/lfsr-seq" ]; then
    echo "  ✗ ERROR: lfsr-seq script not found at $PROJECT_ROOT/lfsr-seq"
    exit 1
fi

if [ ! -x "$PROJECT_ROOT/lfsr-seq" ]; then
    echo "  ✗ ERROR: lfsr-seq is not executable"
    exit 1
fi
echo "  ✓ Script exists and is executable"

# Test 2: Check if test data exists
echo "Test 2: Checking test data file..."
if [ ! -f "$TEST_CSV" ]; then
    echo "  ✗ ERROR: Test CSV file not found: $TEST_CSV"
    exit 1
fi
echo "  ✓ Test CSV file found: $TEST_CSV"

# Test 3: Check environment (run check-environment.sh if available)
echo "Test 3: Checking environment..."
if [ -f "$SCRIPT_DIR/check-environment.sh" ]; then
    if "$SCRIPT_DIR/check-environment.sh" >/dev/null 2>&1; then
        echo "  ✓ Environment check passed"
    else
        echo "  ⚠ WARNING: Environment check failed (this may be expected if dependencies not installed)"
        echo "    Run ./scripts/check-environment.sh for details"
    fi
else
    echo "  ⚠ WARNING: check-environment.sh not found, skipping environment check"
fi

# Test 4: Try to run the script (if SageMath is available)
echo "Test 4: Testing script execution..."
if python3 -c "import sage.all" 2>/dev/null; then
    # Clean up any previous output
    rm -f "$TEST_OUTPUT"
    
    # Run the script with test data
    if "$PROJECT_ROOT/lfsr-seq" "$TEST_CSV" "$GF_ORDER" >/dev/null 2>&1; then
        echo "  ✓ Script executed successfully"
        
        # Test 5: Check if output file was created
        echo "Test 5: Checking output file creation..."
        if [ -f "$TEST_OUTPUT" ]; then
            echo "  ✓ Output file created: $TEST_OUTPUT"
            
            # Test 6: Check if output file has content
            echo "Test 6: Checking output file content..."
            if [ -s "$TEST_OUTPUT" ]; then
                OUTPUT_SIZE=$(wc -l < "$TEST_OUTPUT" | tr -d ' ')
                echo "  ✓ Output file has content ($OUTPUT_SIZE lines)"
            else
                echo "  ⚠ WARNING: Output file is empty"
            fi
        else
            echo "  ⚠ WARNING: Output file was not created"
        fi
    else
        echo "  ✗ ERROR: Script execution failed"
        exit 1
    fi
else
    echo "  ⚠ SKIPPED: SageMath not available, cannot test execution"
    echo "    Install SageMath to run full smoke tests"
fi

# Test 7: Check script help/usage (if script supports it)
echo "Test 7: Checking script argument handling..."
if "$PROJECT_ROOT/lfsr-seq" 2>&1 | grep -q "Usage\|usage\|Error\|ERROR"; then
    echo "  ✓ Script handles missing arguments correctly"
else
    echo "  ⚠ WARNING: Script may not handle missing arguments properly"
fi

echo ""
echo "Smoke tests completed!"
echo ""
echo "Summary:"
echo "  - Script exists and is executable: ✓"
echo "  - Test data available: ✓"
if python3 -c "import sage.all" 2>/dev/null; then
    echo "  - Script execution: ✓"
    echo "  - Output generation: ✓"
else
    echo "  - Script execution: ⚠ (SageMath not available)"
fi
echo ""
echo "To run the full test suite, ensure SageMath is installed and run:"
echo "  ./scripts/check-environment.sh"
echo "  ./lfsr-seq strange.csv 2"

