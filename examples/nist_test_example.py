#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example: NIST SP 800-22 Statistical Test Suite

This example demonstrates how to use the NIST SP 800-22 test suite to evaluate
the randomness of binary sequences.

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
    binary_matrix_rank_test,
    discrete_fourier_transform_test,
    non_overlapping_template_matching_test,
    overlapping_template_matching_test,
    maurers_universal_test,
    linear_complexity_test
)


def example_single_test():
    """Example of running a single NIST test."""
    print("=" * 70)
    print("Example 1: Single Test - Frequency (Monobit) Test")
    print("=" * 70)
    
    # Generate a balanced sequence
    sequence = [1, 0] * 500  # 1000 bits
    
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
    print(f"    Zeros: {result.details.get('n0', 'N/A')}")
    print(f"    Ones: {result.details.get('n1', 'N/A')}")
    print(f"    Ratio: {result.details.get('ratio', 0.0):.4f}")


def example_test_suite():
    """Example of running the complete test suite."""
    print("\n" + "=" * 70)
    print("Example 2: Complete Test Suite")
    print("=" * 70)
    
    # Generate a longer sequence for comprehensive testing
    sequence = [1, 0, 1, 1, 0, 0, 1, 0] * 125  # 1000 bits
    
    print(f"\nSequence: {len(sequence)} bits")
    print(f"  First 20 bits: {sequence[:20]}")
    
    # Run complete test suite
    suite_result = run_nist_test_suite(sequence, significance_level=0.01)
    
    print(f"\n{'─'*70}")
    print("Test Suite Results:")
    print(f"{'─'*70}")
    print(f"  Sequence Length: {suite_result.sequence_length}")
    print(f"  Significance Level: {suite_result.significance_level}")
    print(f"  Tests Passed: {suite_result.tests_passed}/{suite_result.total_tests}")
    print(f"  Tests Failed: {suite_result.tests_failed}")
    print(f"  Pass Rate: {suite_result.pass_rate:.2%}")
    print(f"  Overall Assessment: {suite_result.overall_assessment}")
    
    print(f"\n{'─'*70}")
    print("Individual Test Results:")
    print(f"{'─'*70}")
    print(f"{'Test':<45} {'P-value':<12} {'Status':<10}")
    print(f"{'─'*70}")
    
    for result in suite_result.results:
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"{result.test_name:<45} {result.p_value:>10.6f}  {status:<10}")


def example_all_tests():
    """Example showing all individual tests."""
    print("\n" + "=" * 70)
    print("Example 3: All Individual Tests")
    print("=" * 70)
    
    # Generate a test sequence
    sequence = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1] * 100  # 1000 bits
    
    print(f"\nSequence: {len(sequence)} bits")
    
    tests = [
        ("Frequency Test", lambda s: frequency_test(s)),
        ("Block Frequency Test", lambda s: block_frequency_test(s, block_size=128)),
        ("Runs Test", lambda s: runs_test(s)),
        ("Longest Run Test", lambda s: longest_run_of_ones_test(s, block_size=8)),
        ("Matrix Rank Test", lambda s: binary_matrix_rank_test(s)),
        ("DFT (Spectral) Test", lambda s: discrete_fourier_transform_test(s)),
        ("Non-overlapping Template Test", lambda s: non_overlapping_template_matching_test(s)),
        ("Overlapping Template Test", lambda s: overlapping_template_matching_test(s)),
        ("Maurer's Universal Test", lambda s: maurers_universal_test(s)),
        ("Linear Complexity Test", lambda s: linear_complexity_test(s, block_size=500)),
    ]
    
    print(f"\n{'─'*70}")
    print("Test Results:")
    print(f"{'─'*70}")
    print(f"{'Test':<40} {'P-value':<12} {'Status':<10}")
    print(f"{'─'*70}")
    
    for test_name, test_func in tests:
        try:
            result = test_func(sequence)
            status = "✓ PASS" if result.passed else "✗ FAIL"
            print(f"{test_name:<40} {result.p_value:>10.6f}  {status:<10}")
        except Exception as e:
            print(f"{test_name:<40} {'ERROR':<12} {str(e)[:30]:<10}")


def example_interpretation():
    """Example showing how to interpret test results."""
    print("\n" + "=" * 70)
    print("Example 4: Interpreting Test Results")
    print("=" * 70)
    
    # Generate sequences with different properties
    balanced = [1, 0] * 500  # Balanced sequence
    biased = [1] * 800 + [0] * 200  # Biased sequence (80% ones)
    periodic = [1, 0, 1, 0] * 250  # Periodic sequence
    
    sequences = [
        ("Balanced", balanced),
        ("Biased (80% ones)", biased),
        ("Periodic", periodic)
    ]
    
    print(f"\n{'─'*70}")
    print("Comparing Different Sequences:")
    print(f"{'─'*70}")
    
    for name, seq in sequences:
        print(f"\n{name} Sequence ({len(seq)} bits):")
        result = frequency_test(seq)
        print(f"  Frequency Test:")
        print(f"    P-value: {result.p_value:.6f}")
        print(f"    Passed: {result.passed}")
        print(f"    Interpretation: ", end="")
        if result.passed:
            print("Sequence appears balanced (random-like)")
        else:
            print("Sequence is significantly imbalanced (non-random)")
        
        # Run a few more tests
        runs_result = runs_test(seq)
        print(f"  Runs Test:")
        print(f"    P-value: {runs_result.p_value:.6f}")
        print(f"    Passed: {runs_result.passed}")


def example_significance_levels():
    """Example showing effect of different significance levels."""
    print("\n" + "=" * 70)
    print("Example 5: Effect of Significance Levels")
    print("=" * 70")
    
    sequence = [1, 0, 1, 1, 0, 0, 1, 0] * 125  # 1000 bits
    
    significance_levels = [0.01, 0.05, 0.10]
    
    print(f"\nSequence: {len(sequence)} bits")
    print(f"\n{'─'*70}")
    print("Effect of Significance Level:")
    print(f"{'─'*70}")
    print(f"{'Significance Level':<20} {'Tests Passed':<15} {'Assessment':<15}")
    print(f"{'─'*70}")
    
    for alpha in significance_levels:
        suite_result = run_nist_test_suite(sequence, significance_level=alpha)
        print(f"{alpha:<20.2f} {suite_result.tests_passed:<15}/{suite_result.total_tests:<4} {suite_result.overall_assessment:<15}")
    
    print(f"\nNote: Lower significance level (e.g., 0.01) is stricter -")
    print(f"      fewer random sequences will pass, but fewer false positives.")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("NIST SP 800-22 Statistical Test Suite Examples")
    print("=" * 70)
    print("\nThis script demonstrates the NIST SP 800-22 test suite")
    print("for evaluating randomness of binary sequences.\n")
    
    try:
        example_single_test()
        example_test_suite()
        example_all_tests()
        example_interpretation()
        example_significance_levels()
        
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
