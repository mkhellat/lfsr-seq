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
import random

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


def example_basic_nist_testing():
    """Basic example of NIST testing."""
    print("=" * 70)
    print("Example 1: Basic NIST Testing")
    print("=" * 70)
    
    # Generate a random-looking sequence
    random.seed(42)
    sequence = [random.randint(0, 1) for _ in range(1000)]
    
    print(f"\nSequence Information:")
    print(f"  Length: {len(sequence)} bits")
    print(f"  First 20 bits: {sequence[:20]}")
    print(f"  Balance: {sum(sequence)} ones, {len(sequence) - sum(sequence)} zeros")
    
    # Run individual test
    print(f"\n{'─'*70}")
    print("Individual Test: Frequency (Monobit) Test")
    print(f"{'─'*70}")
    result = frequency_test(sequence)
    print(f"  Test: {result.test_name}")
    print(f"  P-value: {result.p_value:.6f}")
    print(f"  Passed: {result.passed}")
    print(f"  Statistic: {result.statistic:.6f}")
    print(f"  Details: {result.details}")
    
    # Run complete test suite
    print(f"\n{'─'*70}")
    print("Complete NIST Test Suite (Tests 1-5)")
    print(f"{'─'*70}")
    suite_result = run_nist_test_suite(sequence)
    
    print(f"\nSuite Results:")
    print(f"  Sequence length: {suite_result.sequence_length}")
    print(f"  Significance level: {suite_result.significance_level}")
    print(f"  Tests passed: {suite_result.tests_passed}/{suite_result.total_tests}")
    print(f"  Tests failed: {suite_result.tests_failed}")
    print(f"  Pass rate: {suite_result.pass_rate:.2%}")
    print(f"  Overall assessment: {suite_result.overall_assessment}")
    
    print(f"\n{'─'*70}")
    print("Individual Test Results:")
    print(f"{'─'*70}")
    print(f"{'Test':<45} {'P-value':<12} {'Status':<10}")
    print(f"{'─'*70}")
    for test_result in suite_result.results:
        status = "✓ PASS" if test_result.passed else "✗ FAIL"
        print(f"{test_result.test_name:<45} {test_result.p_value:>10.6f}  {status:<10}")


def example_biased_sequence():
    """Example showing how NIST tests detect bias."""
    print("\n" + "=" * 70)
    print("Example 2: Detecting Bias with NIST Tests")
    print("=" * 70)
    
    # Create a biased sequence (70% ones)
    biased_sequence = []
    for _ in range(1000):
        if random.random() < 0.7:
            biased_sequence.append(1)
        else:
            biased_sequence.append(0)
    
    print(f"\nBiased Sequence:")
    print(f"  Length: {len(biased_sequence)} bits")
    print(f"  Balance: {sum(biased_sequence)} ones ({sum(biased_sequence)/len(biased_sequence):.1%})")
    print(f"  Expected: ~500 ones (50%)")
    
    # Run frequency test
    print(f"\n{'─'*70}")
    print("Frequency Test Results:")
    print(f"{'─'*70}")
    result = frequency_test(biased_sequence)
    print(f"  P-value: {result.p_value:.6f}")
    print(f"  Passed: {result.passed}")
    if not result.passed:
        print(f"  ⚠ BIAS DETECTED: Sequence is significantly imbalanced!")
    
    # Run complete suite
    suite_result = run_nist_test_suite(biased_sequence)
    print(f"\n  Overall: {suite_result.overall_assessment}")
    print(f"  Tests passed: {suite_result.tests_passed}/{suite_result.total_tests}")


def example_perfect_alternating():
    """Example showing how NIST tests detect patterns."""
    print("\n" + "=" * 70)
    print("Example 3: Detecting Patterns (Perfect Alternating)")
    print("=" * 70)
    
    # Create a perfectly alternating sequence (very non-random)
    alternating = [i % 2 for i in range(1000)]
    
    print(f"\nAlternating Sequence:")
    print(f"  Length: {len(alternating)} bits")
    print(f"  Pattern: 0, 1, 0, 1, 0, 1, ...")
    print(f"  First 20 bits: {alternating[:20]}")
    
    # Run runs test (should detect too many runs)
    print(f"\n{'─'*70}")
    print("Runs Test Results:")
    print(f"{'─'*70}")
    result = runs_test(alternating)
    print(f"  P-value: {result.p_value:.6f}")
    print(f"  Passed: {result.passed}")
    print(f"  Runs: {result.details.get('runs', 'N/A')}")
    print(f"  Expected runs: {result.details.get('expected_runs', 'N/A'):.2f}")
    if not result.passed:
        print(f"  ⚠ PATTERN DETECTED: Too many runs (oscillation pattern)!")
    
    # Run complete suite
    suite_result = run_nist_test_suite(alternating)
    print(f"\n  Overall: {suite_result.overall_assessment}")
    print(f"  Tests passed: {suite_result.tests_passed}/{suite_result.total_tests}")


def example_all_individual_tests():
    """Example running all individual tests."""
    print("\n" + "=" * 70)
    print("Example 4: All Individual Tests")
    print("=" * 70)
    
    # Generate test sequence
    random.seed(123)
    sequence = [random.randint(0, 1) for _ in range(2000)]
    
    print(f"\nTest Sequence: {len(sequence)} bits")
    
    tests = [
        ("Frequency (Monobit) Test", lambda s: frequency_test(s)),
        ("Frequency Test within a Block", lambda s: block_frequency_test(s, block_size=128)),
        ("Runs Test", lambda s: runs_test(s)),
        ("Longest Run of Ones Test", lambda s: longest_run_of_ones_test(s, block_size=8)),
        ("Binary Matrix Rank Test", lambda s: binary_matrix_rank_test(s, matrix_rows=32, matrix_cols=32)),
    ]
    
    print(f"\n{'─'*70}")
    print("Test Results:")
    print(f"{'─'*70}")
    print(f"{'Test':<45} {'P-value':<12} {'Status':<10}")
    print(f"{'─'*70}")
    
    for test_name, test_func in tests:
        try:
            result = test_func(sequence)
            status = "✓ PASS" if result.passed else "✗ FAIL"
            print(f"{test_name:<45} {result.p_value:>10.6f}  {status:<10}")
        except Exception as e:
            print(f"{test_name:<45} {'ERROR':<12} {str(e)[:30]}")


def example_interpretation_guide():
    """Example showing how to interpret NIST test results."""
    print("\n" + "=" * 70)
    print("Example 5: Interpreting NIST Test Results")
    print("=" * 70)
    
    # Generate sequence
    random.seed(456)
    sequence = [random.randint(0, 1) for _ in range(1000)]
    
    suite_result = run_nist_test_suite(sequence)
    
    print(f"\nInterpreting Results:")
    print(f"  Sequence length: {suite_result.sequence_length} bits")
    print(f"  Significance level: {suite_result.significance_level} (1%)")
    print(f"  Tests passed: {suite_result.tests_passed}/{suite_result.total_tests}")
    print(f"  Pass rate: {suite_result.pass_rate:.2%}")
    
    print(f"\n{'─'*70}")
    print("Interpretation Guidelines:")
    print(f"{'─'*70}")
    print(f"  • P-value ≥ 0.01: Test PASSES (sequence appears random)")
    print(f"  • P-value < 0.01: Test FAILS (sequence appears non-random)")
    print(f"  • A single test failure does not necessarily mean the")
    print(f"    sequence is non-random - consider the overall pattern")
    print(f"  • For cryptographic applications, sequences should pass")
    print(f"    all or nearly all tests")
    
    print(f"\n  Overall Assessment: {suite_result.overall_assessment}")
    if suite_result.overall_assessment == "PASSED":
        print(f"  ✓ Sequence appears random based on NIST tests")
    else:
        print(f"  ✗ Sequence shows evidence of non-randomness")
    
    # Show p-value distribution
    p_values = [r.p_value for r in suite_result.results]
    print(f"\n  P-value range: {min(p_values):.6f} to {max(p_values):.6f}")
    print(f"  Average p-value: {sum(p_values)/len(p_values):.6f}")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("NIST SP 800-22 Statistical Test Suite Examples")
    print("=" * 70)
    print("\nThis script demonstrates NIST test suite capabilities")
    print("for evaluating the randomness of binary sequences.\n")
    
    try:
        example_basic_nist_testing()
        example_biased_sequence()
        example_perfect_alternating()
        example_all_individual_tests()
        example_interpretation_guide()
        
        print("\n" + "=" * 70)
        print("Examples Complete!")
        print("=" * 70)
        print("\nFor more information, see:")
        print("  - NIST SP 800-22 Guide: docs/nist_sp800_22.rst")
        print("  - API Documentation: docs/api/nist.rst")
        print("  - Official NIST Specification: https://csrc.nist.gov/publications/detail/sp/800-22/rev-1a/final")
        
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
