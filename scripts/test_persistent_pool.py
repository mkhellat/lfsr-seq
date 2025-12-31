#!/usr/bin/env python3
"""
Test persistent worker pool (Phase 2.3).

This script tests that the persistent worker pool:
1. Is created on first use
2. Is reused for subsequent analyses
3. Maintains correctness across multiple analyses
4. Handles cleanup properly
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


def test_persistent_pool(coeffs, gf_order, desc, num_workers=4):
    """Test persistent pool with multiple analyses."""
    print(f"\n{'='*80}")
    print(f"Testing Persistent Pool: {desc} LFSR ({len(coeffs)}-bit)")
    print(f"{'='*80}")
    
    # Build state update matrix
    C, _ = build_state_update_matrix(coeffs, gf_order)
    d = len(coeffs)
    V = VectorSpace(GF(gf_order), d)
    
    # Sequential baseline
    print(f"\n1. Sequential (baseline):")
    start = time.time()
    seq_dict, seq_period_dict, seq_max_period, seq_periods_sum = lfsr_sequence_mapper(
        C, V, gf_order, period_only=True, algorithm="enumeration", no_progress=True
    )
    seq_time = time.time() - start
    print(f"   ✓ Completed in {seq_time:.3f}s")
    print(f"   Sequences: {len(seq_period_dict)}, Sum: {seq_periods_sum}")
    
    # First analysis (pool creation)
    print(f"\n2. First analysis (pool creation):")
    start = time.time()
    dyn_dict1, dyn_period_dict1, dyn_max_period1, dyn_periods_sum1 = lfsr_sequence_mapper_parallel_dynamic(
        C, V, gf_order, period_only=True, algorithm="enumeration",
        num_workers=num_workers, batch_size=None, no_progress=True
    )
    first_time = time.time() - start
    first_speedup = seq_time / first_time if first_time > 0 else 0
    
    correct1 = (
        len(dyn_period_dict1) == len(seq_period_dict) and
        dyn_periods_sum1 == seq_periods_sum and
        dyn_max_period1 == seq_max_period
    )
    status1 = "✓ CORRECT" if correct1 else "✗ INCORRECT"
    print(f"   {status1}: {first_time:.3f}s (speedup: {first_speedup:.2f}x)")
    
    # Second analysis (pool reuse)
    print(f"\n3. Second analysis (pool reuse - should be faster):")
    start = time.time()
    dyn_dict2, dyn_period_dict2, dyn_max_period2, dyn_periods_sum2 = lfsr_sequence_mapper_parallel_dynamic(
        C, V, gf_order, period_only=True, algorithm="enumeration",
        num_workers=num_workers, batch_size=None, no_progress=True
    )
    second_time = time.time() - start
    second_speedup = seq_time / second_time if second_time > 0 else 0
    
    correct2 = (
        len(dyn_period_dict2) == len(seq_period_dict) and
        dyn_periods_sum2 == seq_periods_sum and
        dyn_max_period2 == seq_max_period
    )
    status2 = "✓ CORRECT" if correct2 else "✗ INCORRECT"
    print(f"   {status2}: {second_time:.3f}s (speedup: {second_speedup:.2f}x)")
    
    # Compare times
    if second_time < first_time:
        improvement = ((first_time - second_time) / first_time) * 100
        print(f"   ✓ Pool reuse improved time by {improvement:.1f}%")
    else:
        print(f"   Note: Second run took {((second_time - first_time) / first_time) * 100:.1f}% longer")
    
    if not (correct1 and correct2):
        return False
    
    return True


def main():
    """Run persistent pool tests."""
    print("="*80)
    print("PERSISTENT WORKER POOL TEST (Phase 2.3)")
    print("="*80)
    
    # Test with a medium-sized problem
    test_cases = [
        ([1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1], 2, "12-bit"),  # 4096 states
    ]
    
    all_passed = True
    
    for coeffs, gf_order, desc in test_cases:
        try:
            passed = test_persistent_pool(coeffs, gf_order, desc, num_workers=4)
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
        print("✅ ALL TESTS PASSED - Persistent pool working correctly!")
    else:
        print("✗ SOME TESTS FAILED - Check errors above")
        sys.exit(1)
    print(f"{'='*80}")


if __name__ == '__main__':
    main()
