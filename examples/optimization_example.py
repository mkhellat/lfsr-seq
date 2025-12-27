#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example: Optimization Techniques

This example demonstrates the optimization techniques available in lfsr-seq:
- Period computation via factorization
- Mathematical shortcut detection
- Result caching

Example Usage:
    python3 examples/optimization_example.py
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

from lfsr.polynomial import (
    compute_period_via_factorization,
    detect_mathematical_shortcuts
)
from lfsr.optimization import ResultCache, get_global_cache


def example_period_via_factorization():
    """Example of period computation via factorization."""
    print("=" * 70)
    print("Example 1: Period Computation via Factorization")
    print("=" * 70)
    
    # LFSR with coefficients [1, 0, 0, 1] over GF(2)
    coefficients = [1, 0, 0, 1]
    field_order = 2
    
    print(f"\nLFSR Configuration:")
    print(f"  Coefficients: {coefficients}")
    print(f"  Field order: {field_order}")
    
    # Compute period via factorization
    print(f"\nComputing period via factorization...")
    period = compute_period_via_factorization(coefficients, field_order)
    
    if period is not None:
        print(f"  ✓ Period: {period}")
        print(f"  This method is much faster than enumeration for large LFSRs!")
    else:
        print(f"  ✗ Factorization failed, fall back to enumeration")
    
    # Try with a larger LFSR
    print(f"\n" + "-" * 70)
    print("Testing with larger LFSR (degree 8):")
    large_coeffs = [1, 0, 0, 0, 0, 0, 1, 1, 1]  # Degree 8
    large_period = compute_period_via_factorization(large_coeffs, field_order)
    
    if large_period is not None:
        print(f"  ✓ Period: {large_period}")
        print(f"  Factorization handles large LFSRs efficiently!")
    else:
        print(f"  ✗ Factorization failed")


def example_shortcut_detection():
    """Example of mathematical shortcut detection."""
    print("\n" + "=" * 70)
    print("Example 2: Mathematical Shortcut Detection")
    print("=" * 70)
    
    test_cases = [
        ([1, 0, 0, 1], 2, "Primitive polynomial"),
        ([1, 1, 0, 1], 2, "Non-primitive irreducible"),
        ([1, 0, 1, 1], 2, "Another polynomial"),
    ]
    
    for coefficients, field_order, description in test_cases:
        print(f"\n{description}:")
        print(f"  Coefficients: {coefficients}")
        
        shortcuts = detect_mathematical_shortcuts(coefficients, field_order)
        
        print(f"  Is primitive: {shortcuts['is_primitive']}")
        print(f"  Is irreducible: {shortcuts['is_irreducible']}")
        print(f"  Recommended method: {shortcuts['recommended_method']}")
        print(f"  Complexity estimate: {shortcuts['complexity_estimate']}")
        
        if shortcuts['expected_period']:
            print(f"  Expected period: {shortcuts['expected_period']}")
        
        if shortcuts['shortcuts_available']:
            print(f"  Shortcuts available: {', '.join(shortcuts['shortcuts_available'])}")


def example_result_caching():
    """Example of result caching."""
    print("\n" + "=" * 70)
    print("Example 3: Result Caching")
    print("=" * 70)
    
    # Create a cache (or use global cache)
    cache = ResultCache(cache_file=None)  # In-memory only for this example
    
    coefficients = [1, 0, 0, 1]
    field_order = 2
    
    # Generate cache key
    key = cache.generate_key(coefficients, field_order, "period")
    print(f"\nCache key: {key[:16]}...")
    
    # First access (cache miss)
    print(f"\nFirst access (cache miss):")
    if key in cache:
        period = cache.get(key)
        print(f"  Found in cache: {period}")
    else:
        print(f"  Not in cache, computing...")
        period = compute_period_via_factorization(coefficients, field_order)
        cache.set(key, period)
        print(f"  Computed and cached: {period}")
    
    # Second access (cache hit)
    print(f"\nSecond access (cache hit):")
    if key in cache:
        period = cache.get(key)
        print(f"  ✓ Found in cache: {period}")
        print(f"  No computation needed!")
    else:
        print(f"  ✗ Not in cache (unexpected)")
    
    # Get cache statistics
    stats = cache.get_stats()
    print(f"\nCache Statistics:")
    print(f"  Hits: {stats['hits']}")
    print(f"  Misses: {stats['misses']}")
    print(f"  Hit rate: {stats['hit_rate']:.2%}")
    print(f"  Sets: {stats['sets']}")


def example_global_cache():
    """Example of using global cache."""
    print("\n" + "=" * 70)
    print("Example 4: Global Cache")
    print("=" * 70)
    
    from lfsr.optimization import get_global_cache
    
    # Get global cache (persistent by default)
    cache = get_global_cache()
    
    print(f"\nUsing global cache (persistent storage)")
    print(f"  Cache file: {cache.cache_file}")
    
    # Use cache
    key = cache.generate_key([1, 0, 0, 1], 2, "period")
    
    if key in cache:
        period = cache.get(key)
        print(f"  ✓ Found in persistent cache: {period}")
    else:
        period = compute_period_via_factorization([1, 0, 0, 1], 2)
        cache.set(key, period)
        print(f"  Computed and saved to persistent cache: {period}")
    
    stats = cache.get_stats()
    print(f"\n  Cache statistics: {stats['hits']} hits, {stats['misses']} misses")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("Optimization Techniques Examples")
    print("=" * 70)
    print("\nThis script demonstrates optimization techniques for LFSR analysis.\n")
    
    try:
        example_period_via_factorization()
        example_shortcut_detection()
        example_result_caching()
        example_global_cache()
        
        print("\n" + "=" * 70)
        print("Examples Complete!")
        print("=" * 70)
        print("\nFor more information, see:")
        print("  - Optimization Techniques Guide: docs/optimization_techniques.rst")
        print("  - API Documentation: docs/api/optimization.rst")
        print("  - Mathematical Background: docs/mathematical_background.rst")
        
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
