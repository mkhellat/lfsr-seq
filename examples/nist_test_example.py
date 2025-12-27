#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example: NIST SP 800-22 Statistical Test Suite

This example demonstrates how to use the NIST SP 800-22 test suite to
evaluate the randomness of binary sequences.

Example Usage:
    python3 examples/nist_test_example.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import SageMath
try:
    from sage.all import *
except ImportError:
    print("ERROR: SageMath is required for this example", file=sys.stderr)
    sys.exit(1)

from lfsr.nist import (
    run_nist_test_suite,
    frequency_test,
    block_frequency_test,
    runs_test,
    longest_run_of_ones_test,
    binary_matrix_rank_test
)


def example_single_test():
    """Example of running a single NIST test."""
    print("=" * 70)
    print("Example 1: Single Test - Frequency (Monobit) Test")
    print("=" * 70)
    
    # Generate a balanced binary sequence
    sequence = [1, 0] * 500  # 1000 bits, perfectly balanced
    
    print(f"\nSequence: {len(sequence)} bits")
    print(f"  First 20 bits: {sequence[:20]}")
    print(f"  Balance: {sum(sequence)} ones, {len(sequence) - sum(sequence)} zeros")
    
    # Run frequency test
    result = frequency_test(sequence)
    
    print(f"\n{'─'*70}")
    print("Test Results:")
    print(f"{'─'*70}")
    print(f"  Test Name: {result.test_name}")
    print(f"  P-value: {result.p_value:.6f}")
    print(f"  Passed: {result.passed}")
    print(f"  Statistic: {result.statistic:.6f}")
    print(f"  Details:")
    print(f"    - Zeros: {result.details.get('n0', 'N/A')}")
    print(f"    - Ones: {result.details.get('n1', 'N/A')}")
    print(f"    - Ratio: {result.details.get('ratio', 0):.4f}")
    
    if result.passed:
        print(f"\n  ✓ Test PASSED: Sequence appears random")
    else:
        print(f"\n  ✗ Test FAILED: Sequence appears non-random")


def example_all_tests():
    """Example of running all implemented NIST tests."""
    print("\n" + "=" * 70)
    print("Example 2: Complete Test Suite (Tests 1-5)")
    print("=" * 70)
    
    # Generate a sequence
    sequence = [1, 0, 1, 0, 1, 1, 0, 0, 1, 0] * 100  # 1000 bits
    
    print(f"\nSequence: {len(sequence)} bits")
    print(f"  Balance: {sum(sequence)} ones, {len(sequence) - sum(sequence)} zeros")
    
    # Run complete test suite
    suite_result = run_nist_test_suite(sequence)
    
    print(f"\n{'─'*70}")
    print("Test Suite Results:")
    print(f"{'─'*70}")
    print(f"  Sequence Length: {suite_result.sequence_length} bits")
    print(f"  Significance Level: {suite_result.significance_level}")
    print(f"  Tests Passed: {suite_result.tests_passed}/{suite_result.total_tests}")
    print(f"  Tests Failed: {suite_result.tests_failed}")
    print(f"  Pass Rate: {suite_result.pass_rate:.1%}")
    print(f"  Overall Assessment: {suite_result.overall_assessment}")
    
    print(f"\n{'─'*70}")
    print("Individual Test Results:")
    print(f"{'─'*70}")
    print(f"{'Test':<45} {'P-value':<12} {'Status':<10}")
    print(f"{'─'*70}")
    
    for result in suite_result.results:
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"{result.test_name:<45} {result.p_value:>10.6f}  {status:<10}")
    
    print(f"\n{'─'*70}")
    if suite_result.overall_assessment == "PASSED":
        print("✓ Overall: Sequence appears RANDOM")
    else:
        print("✗ Overall: Sequence appears NON-RANDOM")


def example_individual_tests():
    """Example of running each test individually."""
    print("\n" + "=" * 70)
    print("Example 3: Individual Tests")
    print("=" * 70)
    
    # Generate sequence
    sequence = [1, 0, 1, 0, 1, 1, 0, 0, 1, 0] * 100  # 1000 bits
    
    print(f"\nTesting sequence: {len(sequence)} bits")
    
    # Test 1: Frequency
    print(f"\n{'─'*70}")
    print("Test 1: Frequency (Monobit) Test")
    print(f"{'─'*70}")
    result1 = frequency_test(sequence)
    print(f"  P-value: {result1.p_value:.6f}")
    print(f"  Passed: {result1.passed}")
    
    # Test 2: Block Frequency
    print(f"\n{'─'*70}")
    print("Test 2: Frequency Test within a Block")
    print(f"{'─'*70}")
    result2 = block_frequency_test(sequence, block_size=128)
    print(f"  P-value: {result2.p_value:.6f}")
    print(f"  Passed: {result2.passed}")
    print(f"  Blocks: {result2.details.get('num_blocks', 'N/A')}")
    
    # Test 3: Runs
    print(f"\n{'─'*70}")
    print("Test 3: Runs Test")
    print(f"{'─'*70}")
    result3 = runs_test(sequence)
    print(f"  P-value: {result3.p_value:.6f}")
    print(f"  Passed: {result3.passed}")
    print(f"  Runs: {result3.details.get('runs', 'N/A')}")
    print(f"  Expected: {result3.details.get('expected_runs', 'N/A'):.2f}")
    
    # Test 4: Longest Run
    print(f"\n{'─'*70}")
    print("Test 4: Tests for Longest-Run-of-Ones in a Block")
    print(f"{'─'*70}")
    result4 = longest_run_of_ones_test(sequence, block_size=8)
    print(f"  P-value: {result4.p_value:.6f}")
    print(f"  Passed: {result4.passed}")
    print(f"  Blocks: {result4.details.get('num_blocks', 'N/A')}")
    
    # Test 5: Matrix Rank
    print(f"\n{'─'*70}")
    print("Test 5: Binary Matrix Rank Test")
    print(f"{'─'*70}")
    result5 = binary_matrix_rank_test(sequence, matrix_rows=32, matrix_cols=32)
    print(f"  P-value: {result5.p_value:.6f}")
    print(f"  Passed: {result5.passed}")
    print(f"  Matrices: {result5.details.get('num_matrices', 'N/A')}")
    print(f"  Full rank: {result5.details.get('rank_full', 'N/A')}")


def example_non_random_sequence():
    """Example showing how NIST tests detect non-random sequences."""
    print("\n" + "=" * 70)
    print("Example 4: Detecting Non-Random Sequences")
    print("=" * 70)
    
    # Create a non-random sequence (all ones)
    non_random = [1] * 1000
    
    print(f"\nNon-random sequence: {len(non_random)} bits (all ones)")
    print(f"  Balance: {sum(non_random)} ones, {len(non_random) - sum(non_random)} zeros")
    
    # Run tests
    suite_result = run_nist_test_suite(non_random)
    
    print(f"\n{'─'*70}")
    print("Test Results:")
    print(f"{'─'*70}")
    print(f"  Tests Passed: {suite_result.tests_passed}/{suite_result.total_tests}")
    print(f"  Overall Assessment: {suite_result.overall_assessment}")
    
    print(f"\n  Individual Results:")
    for result in suite_result.results:
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"    {result.test_name:<40} {result.p_value:>10.6f}  {status}")
    
    if suite_result.overall_assessment == "FAILED":
        print(f"\n  ⚠ Correctly detected as NON-RANDOM!")


def example_sequence_from_lfsr():
    """Example using sequence generated from an LFSR."""
    print("\n" + "=" * 70)
    print("Example 5: Testing LFSR-Generated Sequence")
    print("=" * 70)
    
    from lfsr.core import build_state_update_matrix
    
    # Create a simple LFSR
    coeffs = [1, 0, 0, 1]
    C, CS = build_state_update_matrix(coeffs, 2)
    
    # Generate sequence from LFSR
    state = vector(GF(2), [1, 0, 0, 0])
    sequence = []
    for _ in range(1000):
        output = int(state[0])
        sequence.append(output)
        state = C * state
    
    print(f"\nLFSR Configuration:")
    print(f"  Coefficients: {coeffs}")
    print(f"  Generated sequence: {len(sequence)} bits")
    print(f"  Balance: {sum(sequence)} ones, {len(sequence) - sum(sequence)} zeros")
    
    # Run NIST tests
    suite_result = run_nist_test_suite(sequence)
    
    print(f"\n{'─'*70}")
    print("NIST Test Results:")
    print(f"{'─'*70}")
    print(f"  Tests Passed: {suite_result.tests_passed}/{suite_result.total_tests}")
    print(f"  Pass Rate: {suite_result.pass_rate:.1%}")
    print(f"  Overall Assessment: {suite_result.overall_assessment}")
    
    print(f"\n  Individual Test Results:")
    for result in suite_result.results:
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"    {result.test_name:<40} {result.p_value:>10.6f}  {status}")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("NIST SP 800-22 Statistical Test Suite Examples")
    print("=" * 70)
    print("\nThis script demonstrates NIST statistical testing capabilities")
    print("for evaluating the randomness of binary sequences.\n")
    
    try:
        example_single_test()
        example_all_tests()
        example_individual_tests()
        example_non_random_sequence()
        example_sequence_from_lfsr()
        
        print("\n" + "=" * 70)
        print("Examples Complete!")
        print("=" * 70)
        print("\nFor more information, see:")
        print("  - NIST SP 800-22 Guide: docs/nist_sp800_22.rst")
        print("  - API Documentation: docs/api/nist.rst")
        print("  - Mathematical Background: docs/mathematical_background.rst")
        
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
