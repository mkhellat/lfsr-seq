#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example: Time-Memory Trade-Off Attacks

This example demonstrates how to use time-memory trade-off attacks to
recover LFSR states efficiently using precomputed tables.

Example Usage:
    python3 examples/tmto_attack_example.py
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import SageMath
try:
    from sage.all import *
except ImportError:
    print("ERROR: SageMath is required for this example", file=sys.stderr)
    sys.exit(1)

from lfsr.attacks import LFSRConfig
from lfsr.tmto import (
    HellmanTable,
    RainbowTable,
    tmto_attack,
    optimize_tmto_parameters
)


def example_hellman_table():
    """Example of Hellman table generation and lookup."""
    print("=" * 70)
    print("Example 1: Hellman Table")
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
    print(f"  State space size: {lfsr.field_order ** lfsr.degree}")
    
    # Create Hellman table
    print(f"\nGenerating Hellman table...")
    print(f"  Chain count: 100")
    print(f"  Chain length: 50")
    
    table = HellmanTable(chain_count=100, chain_length=50)
    start_time = time.perf_counter()
    table.generate(lfsr)
    generation_time = time.perf_counter() - start_time
    
    print(f"  ✓ Table generated in {generation_time:.2f} seconds")
    print(f"  Chains created: {len(table.chains)}")
    
    # Test lookup
    target_state = [1, 0, 1, 1]
    print(f"\nLooking up target state: {target_state}")
    
    lookup_start = time.perf_counter()
    recovered = table.lookup(target_state, lfsr)
    lookup_time = time.perf_counter() - lookup_start
    
    if recovered:
        print(f"  ✓ State recovered: {recovered}")
        print(f"  Lookup time: {lookup_time:.4f} seconds")
    else:
        print(f"  ✗ State not found in table")
        print(f"    (May need larger table or different target)")


def example_rainbow_table():
    """Example of Rainbow table generation and lookup."""
    print("\n" + "=" * 70)
    print("Example 2: Rainbow Table")
    print("=" * 70)
    
    lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
    
    print(f"\nGenerating Rainbow table...")
    print(f"  Chain count: 100")
    print(f"  Chain length: 50")
    
    table = RainbowTable(chain_count=100, chain_length=50)
    start_time = time.perf_counter()
    table.generate(lfsr)
    generation_time = time.perf_counter() - start_time
    
    print(f"  ✓ Table generated in {generation_time:.2f} seconds")
    print(f"  Chains created: {len(table.chains)}")
    print(f"  Reduction functions: {len(table.reduction_functions)}")
    
    # Test lookup
    target_state = [1, 0, 1, 1]
    print(f"\nLooking up target state: {target_state}")
    
    recovered = table.lookup(target_state, lfsr)
    if recovered:
        print(f"  ✓ State recovered: {recovered}")
    else:
        print(f"  ✗ State not found in table")


def example_tmto_attack():
    """Example of using tmto_attack function."""
    print("\n" + "=" * 70)
    print("Example 3: TMTO Attack Function")
    print("=" * 70)
    
    lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
    target_state = [1, 0, 1, 1]
    
    print(f"\nPerforming Hellman table attack...")
    result = tmto_attack(
        lfsr_config=lfsr,
        target_state=target_state,
        method="hellman",
        chain_count=100,
        chain_length=50
    )
    
    print(f"\n{'─'*70}")
    print("Attack Results:")
    print(f"{'─'*70}")
    print(f"  Method: {result.method_used}")
    print(f"  Attack successful: {result.attack_successful}")
    if result.attack_successful:
        print(f"  ✓ Recovered state: {result.recovered_state}")
    print(f"  Table size: {result.table_size} chains")
    print(f"  Coverage: {result.coverage:.2%}")
    print(f"  Precomputation time: {result.precomputation_time:.2f} seconds")
    print(f"  Lookup time: {result.lookup_time:.4f} seconds")


def example_parameter_optimization():
    """Example of parameter optimization."""
    print("\n" + "=" * 70)
    print("Example 4: Parameter Optimization")
    print("=" * 70)
    
    state_space_size = 16  # 2^4 for degree 4 LFSR
    available_memory = 10000
    
    print(f"\nOptimizing parameters:")
    print(f"  State space size: {state_space_size}")
    print(f"  Available memory: {available_memory} states")
    
    params = optimize_tmto_parameters(
        state_space_size=state_space_size,
        available_memory=available_memory,
        target_success_probability=0.5
    )
    
    print(f"\n{'─'*70}")
    print("Optimal Parameters:")
    print(f"{'─'*70}")
    print(f"  Chain count: {params['chain_count']}")
    print(f"  Chain length: {params['chain_length']}")
    print(f"  Estimated coverage: {params['estimated_coverage']:.2%}")
    print(f"  Estimated success probability: {params['estimated_success_prob']:.2%}")
    print(f"  Time×Memory product: {params['time_memory_product']}")


def example_comparison():
    """Example comparing Hellman and Rainbow tables."""
    print("\n" + "=" * 70)
    print("Example 5: Hellman vs Rainbow Comparison")
    print("=" * 70)
    
    lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
    target_state = [1, 0, 1, 1]
    
    chain_count = 100
    chain_length = 50
    
    print(f"\nComparing methods with same parameters:")
    print(f"  Chain count: {chain_count}")
    print(f"  Chain length: {chain_length}")
    
    # Hellman
    print(f"\n1. Hellman Table:")
    hellman_result = tmto_attack(
        lfsr_config=lfsr,
        target_state=target_state,
        method="hellman",
        chain_count=chain_count,
        chain_length=chain_length
    )
    print(f"   Success: {hellman_result.attack_successful}")
    print(f"   Coverage: {hellman_result.coverage:.2%}")
    print(f"   Precomputation: {hellman_result.precomputation_time:.2f}s")
    
    # Rainbow
    print(f"\n2. Rainbow Table:")
    rainbow_result = tmto_attack(
        lfsr_config=lfsr,
        target_state=target_state,
        method="rainbow",
        chain_count=chain_count,
        chain_length=chain_length
    )
    print(f"   Success: {rainbow_result.attack_successful}")
    print(f"   Coverage: {rainbow_result.coverage:.2%}")
    print(f"   Precomputation: {rainbow_result.precomputation_time:.2f}s")
    
    print(f"\nNote: Rainbow tables typically have fewer collisions and")
    print(f"      better coverage for the same memory usage.")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("Time-Memory Trade-Off Attacks Examples")
    print("=" * 70)
    print("\nThis script demonstrates TMTO attacks on LFSRs.\n")
    
    try:
        example_hellman_table()
        example_rainbow_table()
        example_tmto_attack()
        example_parameter_optimization()
        example_comparison()
        
        print("\n" + "=" * 70)
        print("Examples Complete!")
        print("=" * 70)
        print("\nFor more information, see:")
        print("  - TMTO Attacks Guide: docs/time_memory_tradeoff.rst")
        print("  - API Documentation: docs/api/tmto.rst")
        print("  - Mathematical Background: docs/mathematical_background.rst")
        
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
