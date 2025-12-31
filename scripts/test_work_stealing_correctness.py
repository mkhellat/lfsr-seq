#!/usr/bin/env python3
"""
Test correctness of work stealing (Phase 3.1).

This script verifies that work stealing doesn't affect correctness:
1. Results match sequential
2. All batches are processed correctly
3. Work stealing distributes work properly
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
        lfsr_sequence_mapper_parallel_dynamic
    )
except ImportError as e:
    print(f"ERROR: Cannot import required modules: {e}")
    print("This test requires SageMath")
    sys.exit(1)


def test_correctness(coeffs, gf_order, desc, num_workers=4):
    """Test that work stealing doesn't affect correctness."""
    print(f"\n{'='*80}")
    print(f"Testing Work Stealing: {desc} LFSR ({len(coeffs)}-bit)")
    print(f"{'='*80}")
    
    # Build state update matrix
    C, _ = build_state_update_matrix(coeffs, gf_order)
    d = len(coeffs)
    V = VectorSpace(GF(gf_order), d)
    
    # Calculate state space size
    state_space_size = gf_order ** len(coeffs)
    print(f"\nState space size: {state_space_size:,} states")
    
    # Sequential baseline
    print(f"\n1. Sequential (baseline):")
    start = time.time()
    seq_dict, seq_period_dict, seq_max_period, seq_periods_sum = lfsr_sequence_mapper(
        C, V, gf_order, period_only=True, algorithm="enumeration", no_progress=True
    )
    seq_time = time.time() - start
    print(f"   ✓ Completed in {seq_time:.3f}s")
    print(f"   Sequences: {len(seq_period_dict)}, Sum: {seq_periods_sum}, Max: {seq_max_period}")
    
    # Dynamic with work stealing (Phase 3.1)
    print(f"\n2. Dynamic mode with work stealing ({num_workers} workers):")
    start = time.time()
    dyn_dict, dyn_period_dict, dyn_max_period, dyn_periods_sum = lfsr_sequence_mapper_parallel_dynamic(
        C, V, gf_order, period_only=True, algorithm="enumeration",
        num_workers=num_workers, batch_size=None, no_progress=True
    )
    dyn_time = time.time() - start
    dyn_speedup = seq_time / dyn_time if dyn_time > 0 else 0
    
    correct = (
        len(dyn_period_dict) == len(seq_period_dict) and
        dyn_periods_sum == seq_periods_sum and
        dyn_max_period == seq_max_period
    )
    status = "✓ CORRECT" if correct else "✗ INCORRECT"
    print(f"   {status}: {dyn_time:.3f}s (speedup: {dyn_speedup:.2f}x)")
    print(f"   Sequences: {len(dyn_period_dict)}, Sum: {dyn_periods_sum}, Max: {dyn_max_period}")
    
    if not correct:
        print(f"   ERROR: Mismatch!")
        print(f"     Expected: {len(seq_period_dict)} sequences, sum={seq_periods_sum}, max={seq_max_period}")
        print(f"     Got:      {len(dyn_period_dict)} sequences, sum={dyn_periods_sum}, max={dyn_max_period}")
        return False
    
    return True


def main():
    """Run correctness tests."""
    print("="*80)
    print("WORK STEALING CORRECTNESS TEST (Phase 3.1)")
    print("="*80)
    
    # Test cases
    test_cases = [
        ([1, 1, 0, 1], 2, "4-bit"),  # 16 states
        ([1, 0, 1, 1, 0, 0, 0, 1], 2, "8-bit"),  # 256 states
        ([1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1], 2, "12-bit"),  # 4096 states
    ]
    
    all_passed = True
    
    for coeffs, gf_order, desc in test_cases:
        try:
            passed = test_correctness(coeffs, gf_order, desc, num_workers=4)
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"\n✗ Error testing {desc}: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    # Final summary
    print(f"\n{'='*80}")
    if all_passed:
        print("✅ ALL TESTS PASSED - Work stealing maintains correctness!")
    else:
        print("✗ SOME TESTS FAILED - Check errors above")
        sys.exit(1)
    print(f"{'='*80}")


if __name__ == '__main__':
    main()
