#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example: Algebraic Attacks on LFSRs

This example demonstrates how to use the algebraic attack framework to
analyze LFSRs and identify vulnerabilities through algebraic methods.

Example Usage:
    python3 examples/algebraic_attack_example.py
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
    LFSRConfig,
    compute_algebraic_immunity,
    groebner_basis_attack,
    cube_attack
)


def example_algebraic_immunity():
    """Example of computing algebraic immunity."""
    print("=" * 70)
    print("Example 1: Algebraic Immunity Computation")
    print("=" * 70)
    
    # Define different filtering functions
    def linear_function(x0, x1, x2, x3):
        """Linear function: vulnerable to algebraic attacks."""
        return x0
    
    def and_function(x0, x1, x2, x3):
        """AND function: low algebraic immunity."""
        return x0 & x1
    
    def majority_function(x0, x1, x2, x3):
        """Majority function: better algebraic immunity."""
        return 1 if (x0 + x1 + x2) >= 2 else 0
    
    functions = [
        ("Linear (x0)", linear_function, 4),
        ("AND (x0 & x1)", and_function, 4),
        ("Majority (3 inputs)", majority_function, 4),
    ]
    
    print(f"\n{'─'*70}")
    print("Algebraic Immunity Analysis:")
    print(f"{'─'*70}")
    print(f"{'Function':<30} {'AI':<8} {'Max':<8} {'Optimal':<10}")
    print(f"{'─'*70}")
    
    for name, func, num_inputs in functions:
        result = compute_algebraic_immunity(func, num_inputs)
        optimal_str = "Yes" if result['optimal'] else "No"
        print(f"{name:<30} {result['algebraic_immunity']:<8} "
              f"{result['max_possible']:<8} {optimal_str:<10}")
    
    # Detailed analysis
    print(f"\n{'─'*70}")
    print("Detailed Analysis: AND Function")
    print(f"{'─'*70}")
    result = compute_algebraic_immunity(and_function, 4)
    print(f"  Algebraic immunity: {result['algebraic_immunity']}")
    print(f"  Maximum possible: {result['max_possible']}")
    print(f"  Optimal: {result['optimal']}")
    if not result['optimal']:
        print(f"  ⚠ VULNERABLE: Function does not achieve maximum algebraic immunity")
        print(f"    (Vulnerable to algebraic attacks of degree {result['algebraic_immunity']})")


def example_groebner_basis_attack():
    """Example of Gröbner basis attack."""
    print("\n" + "=" * 70)
    print("Example 2: Gröbner Basis Attack")
    print("=" * 70)
    
    # Create LFSR configuration
    lfsr = LFSRConfig(
        coefficients=[1, 0, 0, 1],
        field_order=2,
        degree=4
    )
    
    print(f"\nLFSR Configuration:")
    print(f"  Coefficients: {lfsr.coefficients}")
    print(f"  Degree: {lfsr.degree}")
    print(f"  Field order: {lfsr.field_order}")
    
    # Generate keystream (simplified - in practice would be observed)
    # For demonstration, we'll use a short keystream
    keystream = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1]
    
    print(f"\nKeystream: {len(keystream)} bits")
    print(f"  First 10 bits: {keystream[:10]}")
    
    # Perform Gröbner basis attack
    print(f"\nPerforming Gröbner basis attack...")
    result = groebner_basis_attack(
        lfsr_config=lfsr,
        keystream=keystream,
        max_equations=100
    )
    
    print(f"\n{'─'*70}")
    print("Gröbner Basis Attack Results:")
    print(f"{'─'*70}")
    print(f"  Method: {result.method_used}")
    print(f"  Attack successful: {result.attack_successful}")
    if result.attack_successful:
        print(f"  ✓ Recovered state: {result.recovered_state}")
    else:
        print(f"  ✗ Attack failed")
        if 'error' in result.details:
            print(f"  Error: {result.details['error']}")
    print(f"  Equations solved: {result.equations_solved}")
    print(f"  Complexity estimate: {result.complexity_estimate:.0f} operations")
    print(f"  Algebraic immunity: {result.algebraic_immunity}")


def example_cube_attack():
    """Example of cube attack."""
    print("\n" + "=" * 70)
    print("Example 3: Cube Attack")
    print("=" * 70)
    
    # Create LFSR configuration
    lfsr = LFSRConfig(
        coefficients=[1, 0, 0, 1],
        field_order=2,
        degree=4
    )
    
    print(f"\nLFSR Configuration:")
    print(f"  Coefficients: {lfsr.coefficients}")
    print(f"  Degree: {lfsr.degree}")
    
    # Generate keystream
    keystream = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1]
    
    print(f"\nKeystream: {len(keystream)} bits")
    
    # Perform cube attack
    print(f"\nPerforming cube attack (max cube size: 5)...")
    result = cube_attack(
        lfsr_config=lfsr,
        keystream=keystream,
        max_cube_size=5
    )
    
    print(f"\n{'─'*70}")
    print("Cube Attack Results:")
    print(f"{'─'*70}")
    print(f"  Attack successful: {result.attack_successful}")
    if result.attack_successful:
        print(f"  ✓ Attack succeeded!")
        print(f"  Cubes found: {result.cubes_found}")
        print(f"  Superpolies computed: {result.superpolies_computed}")
        print(f"  Recovered bits: {result.recovered_bits}")
    else:
        print(f"  ✗ Attack failed")
        if 'error' in result.details:
            print(f"  Error: {result.details['error']}")
    print(f"  Complexity estimate: {result.complexity_estimate:.0f} operations")


def example_comparison():
    """Example comparing different attack methods."""
    print("\n" + "=" * 70)
    print("Example 4: Attack Method Comparison")
    print("=" * 70)
    
    lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
    keystream = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1]
    
    print(f"\nComparing attack methods on same LFSR and keystream:")
    print(f"  LFSR: {lfsr.coefficients}")
    print(f"  Keystream length: {len(keystream)}")
    
    # Gröbner basis attack
    print(f"\n1. Gröbner Basis Attack:")
    gb_result = groebner_basis_attack(lfsr, keystream)
    print(f"   Success: {gb_result.attack_successful}")
    print(f"   Complexity: {gb_result.complexity_estimate:.0f}")
    
    # Cube attack
    print(f"\n2. Cube Attack:")
    cube_result = cube_attack(lfsr, keystream, max_cube_size=5)
    print(f"   Success: {cube_result.attack_successful}")
    print(f"   Complexity: {cube_result.complexity_estimate:.0f}")
    
    print(f"\nNote: Actual success depends on LFSR structure and keystream length.")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("Algebraic Attacks Examples")
    print("=" * 70)
    print("\nThis script demonstrates algebraic attacks on LFSRs.\n")
    
    try:
        example_algebraic_immunity()
        example_groebner_basis_attack()
        example_cube_attack()
        example_comparison()
        
        print("\n" + "=" * 70)
        print("Examples Complete!")
        print("=" * 70)
        print("\nFor more information, see:")
        print("  - Algebraic Attacks Guide: docs/algebraic_attacks.rst")
        print("  - API Documentation: docs/api/attacks.rst")
        print("  - Mathematical Background: docs/mathematical_background.rst")
        
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
