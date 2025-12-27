#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example: Correlation Attack on Combination Generator

This example demonstrates how to use the correlation attack framework to
analyze combination generators and identify vulnerabilities.

Example Usage:
    python3 examples/correlation_attack_example.py
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

from lfsr.attacks import (
    CombinationGenerator,
    LFSRConfig,
    siegenthaler_correlation_attack,
    fast_correlation_attack,
    distinguishing_attack,
    compute_correlation_coefficient,
    analyze_combining_function
)


def example_basic_correlation_attack():
    """Basic example of correlation attack."""
    print("=" * 70)
    print("Example 1: Basic Correlation Attack")
    print("=" * 70)
    
    # Define a majority function (correlation immune of order 1)
    def majority(a, b, c):
        """Majority function: returns 1 if at least 2 inputs are 1."""
        return 1 if (a + b + c) >= 2 else 0
    
    # Create combination generator with 3 LFSRs
    gen = CombinationGenerator(
        lfsrs=[
            LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4),
            LFSRConfig(coefficients=[1, 1, 0, 1], field_order=2, degree=4),
            LFSRConfig(coefficients=[1, 0, 1, 1], field_order=2, degree=4)
        ],
        combining_function=majority,
        function_name='majority'
    )
    
    print(f"\nCombination Generator Configuration:")
    print(f"  Number of LFSRs: {len(gen.lfsrs)}")
    print(f"  Combining function: {gen.function_name}")
    print(f"  LFSR degrees: {[lfsr.degree for lfsr in gen.lfsrs]}")
    
    # Generate keystream
    keystream_length = 1000
    keystream = gen.generate_keystream(length=keystream_length)
    
    print(f"\nGenerated keystream: {keystream_length} bits")
    print(f"  First 20 bits: {keystream[:20]}")
    
    # Attack each LFSR
    print(f"\n{'─'*70}")
    print("Correlation Attack Results:")
    print(f"{'─'*70}")
    print(f"{'LFSR':<6} {'Correlation':<15} {'P-value':<12} {'Success':<10}")
    print(f"{'─'*70}")
    
    for i in range(len(gen.lfsrs)):
        result = siegenthaler_correlation_attack(
            combination_generator=gen,
            keystream=keystream,
            target_lfsr_index=i
        )
        
        success_str = "✓ Yes" if result.attack_successful else "✗ No"
        print(f"{i+1:<6} {result.correlation_coefficient:>13.6f}  "
              f"{result.p_value:>10.6f}  {success_str:<10}  {result.success_probability:>6.2%}")
    
    # Detailed analysis of first LFSR
    print(f"\n{'─'*70}")
    print("Detailed Analysis (LFSR 1):")
    print(f"{'─'*70}")
    result = siegenthaler_correlation_attack(gen, keystream, target_lfsr_index=0)
    print(f"  Correlation coefficient: {result.correlation_coefficient:.6f}")
    print(f"  P-value: {result.p_value:.6f}")
    print(f"  Match ratio: {result.match_ratio:.4f} ({result.matches}/{result.total_bits})")
    print(f"  Attack successful: {result.attack_successful}")
    print(f"  Success probability: {result.success_probability:.2%}")
    print(f"  Required keystream bits: {result.required_keystream_bits}")
    print(f"  Complexity estimate: {result.complexity_estimate:.0f} operations")


def example_combining_function_analysis():
    """Example of analyzing combining functions."""
    print("\n" + "=" * 70)
    print("Example 2: Combining Function Analysis")
    print("=" * 70)
    
    # Define different combining functions
    def majority(a, b, c):
        return 1 if (a + b + c) >= 2 else 0
    
    def xor_combiner(a, b):
        return a ^ b
    
    def and_combiner(a, b):
        return a & b
    
    functions = [
        ("Majority (3 inputs)", majority, 3),
        ("XOR (2 inputs)", xor_combiner, 2),
        ("AND (2 inputs)", and_combiner, 2)
    ]
    
    print(f"\n{'─'*70}")
    print("Combining Function Properties:")
    print(f"{'─'*70}")
    print(f"{'Function':<25} {'Balanced':<12} {'Bias':<12} {'CI Order':<12}")
    print(f"{'─'*70}")
    
    for name, func, num_inputs in functions:
        analysis = analyze_combining_function(func, num_inputs, field_order=2)
        balanced_str = "Yes" if analysis['balanced'] else "No"
        ci_order = analysis['correlation_immunity']
        print(f"{name:<25} {balanced_str:<12} {analysis['bias']:>10.4f}  {ci_order:<12}")
    
    # Detailed analysis of majority function
    print(f"\n{'─'*70}")
    print("Detailed Analysis: Majority Function (3 inputs)")
    print(f"{'─'*70}")
    analysis = analyze_combining_function(majority, 3, field_order=2)
    print(f"  Balanced: {analysis['balanced']}")
    print(f"  Bias: {analysis['bias']:.4f}")
    print(f"  Correlation immunity order: {analysis['correlation_immunity']}")
    print(f"  Output distribution: {analysis['output_distribution']}")
    print(f"  Truth table (first 4 entries):")
    for inputs, output in analysis['truth_table'][:4]:
        print(f"    {inputs} -> {output}")


def example_correlation_computation():
    """Example of computing correlation coefficients."""
    print("\n" + "=" * 70)
    print("Example 3: Correlation Coefficient Computation")
    print("=" * 70)
    
    # Create sequences with known correlation
    seq1 = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0]
    seq2 = [1, 1, 1, 0, 0, 1, 1, 0, 0, 1]  # Some correlation
    seq3 = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]  # Negative correlation with seq1
    
    print(f"\nSequence 1: {seq1}")
    print(f"Sequence 2: {seq2}")
    print(f"Sequence 3: {seq3}")
    
    # Compute correlations
    print(f"\n{'─'*70}")
    print("Correlation Analysis:")
    print(f"{'─'*70}")
    
    rho12, p12, stats12 = compute_correlation_coefficient(seq1, seq2)
    rho13, p13, stats13 = compute_correlation_coefficient(seq1, seq3)
    
    print(f"\nCorrelation between seq1 and seq2:")
    print(f"  Correlation coefficient: {rho12:.4f}")
    print(f"  P-value: {p12:.4f}")
    print(f"  Matches: {stats12['matches']}/{stats12['total_bits']}")
    print(f"  Match ratio: {stats12['match_ratio']:.4f}")
    
    print(f"\nCorrelation between seq1 and seq3:")
    print(f"  Correlation coefficient: {rho13:.4f}")
    print(f"  P-value: {p13:.4f}")
    print(f"  Matches: {stats13['matches']}/{stats13['total_bits']}")
    print(f"  Match ratio: {stats13['match_ratio']:.4f}")


def example_vulnerable_combination():
    """Example showing a vulnerable combination generator."""
    print("\n" + "=" * 70)
    print("Example 4: Vulnerable Combination Generator")
    print("=" * 70)
    
    # AND function is NOT correlation immune
    def and_combiner(a, b):
        return a & b
    
    gen = CombinationGenerator(
        lfsrs=[
            LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4),
            LFSRConfig(coefficients=[1, 1, 0, 1], field_order=2, degree=4)
        ],
        combining_function=and_combiner,
        function_name='and'
    )
    
    print(f"\nCombination Generator:")
    print(f"  Combining function: AND (vulnerable to correlation attacks)")
    print(f"  Number of LFSRs: {len(gen.lfsrs)}")
    
    # Generate keystream
    keystream = gen.generate_keystream(length=2000)
    
    # Attack both LFSRs
    print(f"\n{'─'*70}")
    print("Attack Results:")
    print(f"{'─'*70}")
    
    for i in range(len(gen.lfsrs)):
        result = siegenthaler_correlation_attack(gen, keystream, target_lfsr_index=i)
        print(f"\nLFSR {i+1}:")
        print(f"  Correlation: {result.correlation_coefficient:.6f}")
        print(f"  P-value: {result.p_value:.6f}")
        print(f"  Attack successful: {result.attack_successful}")
        print(f"  Success probability: {result.success_probability:.2%}")
        if result.attack_successful:
            print(f"  ⚠ VULNERABLE: Significant correlation detected!")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("Correlation Attack Framework Examples")
    print("=" * 70)
    print("\nThis script demonstrates correlation attack capabilities")
    print("for analyzing combination generators.\n")
    
    try:
        example_basic_correlation_attack()
        example_combining_function_analysis()
        example_correlation_computation()
        example_vulnerable_combination()
        example_fast_correlation_attack()
        example_distinguishing_attack()
        
        print("\n" + "=" * 70)
        print("Examples Complete!")
        print("=" * 70)
        print("\nFor more information, see:")
        print("  - Correlation Attacks Guide: docs/correlation_attacks.rst")
        print("  - API Documentation: docs/api/attacks.rst")
        print("  - Mathematical Background: docs/mathematical_background.rst")
        
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
