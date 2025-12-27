#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example: Parallel State Enumeration

This example demonstrates how to use parallel processing for LFSR analysis.
Parallel processing provides significant speedup for larger LFSRs by
utilizing multiple CPU cores.

Example Usage:
    python3 examples/parallel_processing_example.py
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

from lfsr.analysis import (
    lfsr_sequence_mapper,
    lfsr_sequence_mapper_parallel,
)
from lfsr.core import build_state_update_matrix


def example_basic_parallel():
    """Basic example of parallel processing."""
    print("=" * 70)
    print("Example 1: Basic Parallel Processing")
    print("=" * 70)
    
    # Create a simple 4-bit LFSR
    coeffs = [1, 0, 0, 1]
    C, CS = build_state_update_matrix(coeffs, 2)
    V = VectorSpace(GF(2), 4)
    
    print(f"\nLFSR Configuration:")
    print(f"  Coefficients: {coeffs}")
    print(f"  Field Order: 2")
    print(f"  State Space Size: {2**4} = 16")
    
    # Sequential processing
    print(f"\n{'─'*70}")
    print("Sequential Processing:")
    print(f"{'─'*70}")
    start_time = time.perf_counter()
    seq_dict_seq, period_dict_seq, max_period_seq, periods_sum_seq = lfsr_sequence_mapper(
        C, V, 2, output_file=None, no_progress=True, period_only=True
    )
    seq_time = time.perf_counter() - start_time
    
    print(f"  Time: {seq_time:.3f}s")
    print(f"  Sequences found: {len(seq_dict_seq)}")
    print(f"  Max period: {max_period_seq}")
    print(f"  Period sum: {periods_sum_seq}")
    
    # Parallel processing
    print(f"\n{'─'*70}")
    print("Parallel Processing (2 workers):")
    print(f"{'─'*70}")
    start_time = time.perf_counter()
    seq_dict_par, period_dict_par, max_period_par, periods_sum_par = lfsr_sequence_mapper_parallel(
        C, V, 2, output_file=None, no_progress=True, period_only=True, num_workers=2
    )
    par_time = time.perf_counter() - start_time
    
    print(f"  Time: {par_time:.3f}s")
    print(f"  Sequences found: {len(seq_dict_par)}")
    print(f"  Max period: {max_period_par}")
    print(f"  Period sum: {periods_sum_par}")
    
    # Compare results
    print(f"\n{'─'*70}")
    print("Comparison:")
    print(f"{'─'*70}")
    speedup = seq_time / par_time if par_time > 0 else 0
    print(f"  Speedup: {speedup:.2f}x")
    print(f"  Max period match: {max_period_seq == max_period_par}")
    print(f"  Period sum match: {periods_sum_seq == periods_sum_par}")
    print(f"  Correctness: {'✓' if periods_sum_par == 16 else '✗'}")


def example_worker_scaling():
    """Example showing performance with different worker counts."""
    print("\n" + "=" * 70)
    print("Example 2: Worker Count Scaling")
    print("=" * 70)
    
    # Create a larger LFSR for better parallel benefits
    coeffs = [1, 0, 0, 1, 0, 1]  # 6-bit LFSR (64 states)
    C, CS = build_state_update_matrix(coeffs, 2)
    V = VectorSpace(GF(2), 6)
    
    print(f"\nLFSR Configuration:")
    print(f"  Coefficients: {coeffs}")
    print(f"  Field Order: 2")
    print(f"  State Space Size: {2**6} = 64")
    
    import multiprocessing
    cpu_count = multiprocessing.cpu_count()
    worker_counts = [1, 2, min(4, cpu_count)]
    
    print(f"\n{'─'*70}")
    print("Performance by Worker Count:")
    print(f"{'─'*70}")
    print(f"{'Workers':<10} {'Time (s)':<15} {'Speedup':<15} {'Efficiency':<15}")
    print(f"{'─'*70}")
    
    # Sequential baseline
    start_time = time.perf_counter()
    seq_dict_seq, _, _, _ = lfsr_sequence_mapper(
        C, V, 2, output_file=None, no_progress=True, period_only=True
    )
    seq_time = time.perf_counter() - start_time
    
    print(f"{'Sequential':<10} {seq_time:<15.3f} {'1.00x':<15} {'100.0%':<15}")
    
    # Parallel with different worker counts
    for num_workers in worker_counts:
        start_time = time.perf_counter()
        seq_dict_par, _, _, _ = lfsr_sequence_mapper_parallel(
            C, V, 2, output_file=None, no_progress=True, period_only=True, num_workers=num_workers
        )
        par_time = time.perf_counter() - start_time
        
        speedup = seq_time / par_time if par_time > 0 else 0
        efficiency = (speedup / num_workers * 100) if num_workers > 0 else 0
        
        print(f"{num_workers:<10} {par_time:<15.3f} {speedup:<15.2f} {efficiency:<15.1f}%")


def example_period_only_mode():
    """Example demonstrating period-only mode requirement."""
    print("\n" + "=" * 70)
    print("Example 3: Period-Only Mode (Required for Parallel)")
    print("=" * 70)
    
    coeffs = [1, 0, 0, 1]
    C, CS = build_state_update_matrix(coeffs, 2)
    V = VectorSpace(GF(2), 4)
    
    print(f"\nParallel processing requires period-only mode (--period-only flag).")
    print(f"This is because full sequence mode causes workers to hang due to")
    print(f"SageMath/multiprocessing interaction issues.")
    
    print(f"\n{'─'*70}")
    print("Period-Only Mode (Recommended for Parallel):")
    print(f"{'─'*70}")
    
    seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel(
        C, V, 2, output_file=None, no_progress=True, period_only=True, num_workers=2
    )
    
    print(f"  Sequences: {len(seq_dict)}")
    print(f"  Periods: {list(period_dict.values())[:5]}...")  # Show first 5
    print(f"  Max period: {max_period}")
    print(f"  Period sum: {periods_sum} (should equal state space size: 16)")
    print(f"  Note: Sequence lists are empty in period-only mode")
    print(f"        (periods are computed but sequences not stored)")


def example_auto_detection():
    """Example showing automatic parallel detection."""
    print("\n" + "=" * 70)
    print("Example 4: Automatic Parallel Detection")
    print("=" * 70)
    
    print(f"\nParallel processing is automatically enabled when:")
    print(f"  - State space size > 10,000 states")
    print(f"  - Multiple CPU cores available (>= 2)")
    print(f"  - --parallel flag is not explicitly disabled")
    
    print(f"\nYou can also explicitly control parallel processing:")
    print(f"  --parallel        : Force parallel processing")
    print(f"  --no-parallel    : Force sequential processing")
    print(f"  --num-workers N  : Set number of workers")
    
    import multiprocessing
    cpu_count = multiprocessing.cpu_count()
    print(f"\n  Available CPU cores: {cpu_count}")
    print(f"  Default workers: {cpu_count} (when parallel enabled)")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("Parallel State Enumeration Examples")
    print("=" * 70)
    print("\nThis script demonstrates parallel processing capabilities")
    print("for LFSR state enumeration.\n")
    
    try:
        example_basic_parallel()
        example_worker_scaling()
        example_period_only_mode()
        example_auto_detection()
        
        print("\n" + "=" * 70)
        print("Examples Complete!")
        print("=" * 70)
        print("\nFor more information, see:")
        print("  - User Guide: docs/user_guide.rst")
        print("  - Mathematical Background: docs/mathematical_background.rst")
        print("  - API Documentation: docs/api/analysis.rst")
        
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
