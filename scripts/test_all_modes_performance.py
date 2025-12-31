#!/usr/bin/env python3
"""
Performance comparison across all parallel modes.

This script compares:
- Sequential (baseline)
- Static mode
- Dynamic mode (shared queue)
- Dynamic mode with work stealing (Phase 3.1)
- Dynamic mode with hybrid (Phase 3.2)
"""

import sys
import os
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from sage.all import *
    from lfsr.core import build_state_update_matrix
    from lfsr.analysis import (
        lfsr_sequence_mapper,
        lfsr_sequence_mapper_parallel,
        lfsr_sequence_mapper_parallel_dynamic
    )
except ImportError as e:
    print(f"ERROR: Cannot import required modules: {e}")
    print("This test requires SageMath")
    sys.exit(1)


def test_mode(coeffs, gf_order, desc, mode, num_workers=4):
    """Test a specific mode and return timing."""
    C, _ = build_state_update_matrix(coeffs, gf_order)
    d = len(coeffs)
    V = VectorSpace(GF(gf_order), d)
    
    # Suppress output
    import sys
    from io import StringIO
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    start = time.time()
    try:
        if mode == "sequential":
            seq_dict, seq_period_dict, seq_max_period, seq_periods_sum = lfsr_sequence_mapper(
                C, V, gf_order, period_only=True, algorithm="enumeration", no_progress=True
            )
        elif mode == "static":
            seq_dict, seq_period_dict, seq_max_period, seq_periods_sum = lfsr_sequence_mapper_parallel(
                C, V, gf_order, period_only=True, algorithm="enumeration",
                num_workers=num_workers, no_progress=True
            )
        elif mode == "dynamic":
            seq_dict, seq_period_dict, seq_max_period, seq_periods_sum = lfsr_sequence_mapper_parallel_dynamic(
                C, V, gf_order, period_only=True, algorithm="enumeration",
                num_workers=num_workers, batch_size=None, no_progress=True
            )
        else:
            return None, None
    finally:
        sys.stdout = old_stdout
    
    elapsed = time.time() - start
    return elapsed, (len(seq_period_dict), seq_periods_sum, seq_max_period)


def main():
    """Run performance comparison."""
    print("="*80)
    print("PERFORMANCE COMPARISON - ALL MODES")
    print("="*80)
    
    # Test with medium problem (should use hybrid mode)
    coeffs = [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
    gf_order = 2
    desc = "14-bit"
    num_workers = 4
    
    C, _ = build_state_update_matrix(coeffs, gf_order)
    d = len(coeffs)
    V = VectorSpace(GF(gf_order), d)
    state_space_size = gf_order ** len(coeffs)
    
    print(f"\nTesting {desc} LFSR ({len(coeffs)}-bit)")
    print(f"State space size: {state_space_size:,} states")
    print(f"Workers: {num_workers}")
    
    # Sequential baseline
    print(f"\n1. Sequential (baseline):")
    seq_time, seq_results = test_mode(coeffs, gf_order, desc, "sequential", num_workers)
    print(f"   Time: {seq_time:.3f}s")
    print(f"   Sequences: {seq_results[0]}, Sum: {seq_results[1]}, Max: {seq_results[2]}")
    
    # Static mode
    print(f"\n2. Static mode:")
    static_time, static_results = test_mode(coeffs, gf_order, desc, "static", num_workers)
    static_speedup = seq_time / static_time if static_time > 0 else 0
    correct = static_results == seq_results
    status = "✓" if correct else "✗"
    print(f"   {status} Time: {static_time:.3f}s (speedup: {static_speedup:.2f}x)")
    
    # Dynamic mode (shared queue)
    print(f"\n3. Dynamic mode (shared queue):")
    dyn_time, dyn_results = test_mode(coeffs, gf_order, desc, "dynamic", num_workers)
    dyn_speedup = seq_time / dyn_time if dyn_time > 0 else 0
    correct = dyn_results == seq_results
    status = "✓" if correct else "✗"
    print(f"   {status} Time: {dyn_time:.3f}s (speedup: {dyn_speedup:.2f}x)")
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Sequential:  {seq_time:.3f}s (baseline)")
    print(f"Static:      {static_time:.3f}s ({static_speedup:.2f}x)")
    print(f"Dynamic:     {dyn_time:.3f}s ({dyn_speedup:.2f}x)")
    
    if dyn_time > 0 and static_time > 0:
        improvement = ((static_time - dyn_time) / static_time) * 100
        print(f"\nDynamic vs Static: {improvement:+.1f}% change")
    
    print(f"{'='*80}")


if __name__ == '__main__':
    main()
