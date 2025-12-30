#!/usr/bin/env python3
"""
Test adaptive batch sizing with different problem sizes.

This script tests the adaptive batch sizing feature across various LFSR sizes
to verify that:
1. Batch sizes are selected appropriately for different problem sizes
2. Correctness is maintained
3. Performance metrics are meaningful
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


def run_test(coeffs, gf_order, desc, num_workers=4):
    """Run a test with different batch sizes."""
    print(f"\n{'='*80}")
    print(f"Testing {desc} LFSR ({len(coeffs)}-bit)")
    print(f"{'='*80}")
    
    # Build state update matrix
    C, V = build_state_update_matrix(coeffs, gf_order)
    
    # Calculate state space size
    state_space_size = gf_order ** len(coeffs)
    print(f"\nState space size: {state_space_size:,} states")
    
    # Expected batch size ranges based on adaptive logic
    if state_space_size < 8192:
        expected_range = "500-1000"
        category = "Small"
    elif state_space_size < 65536:
        expected_range = "200-500"
        category = "Medium"
    else:
        expected_range = "100-200"
        category = "Large"
    
    print(f"Category: {category} problem")
    print(f"Expected batch size range: {expected_range}")
    
    # Test 1: Sequential baseline
    print(f"\n1. Sequential (baseline):")
    start = time.time()
    seq_dict, seq_period_dict, seq_max_period, seq_periods_sum = lfsr_sequence_mapper(
        C, V, gf_order, period_only=True, algorithm="enumeration", no_progress=True
    )
    seq_time = time.time() - start
    print(f"   ✓ Completed in {seq_time:.3f}s")
    print(f"   Sequences: {len(seq_period_dict)}, Sum: {seq_periods_sum}, Max: {seq_max_period}")
    
    # Test 2: Dynamic with auto batch size
    print(f"\n2. Dynamic mode (auto batch size, {num_workers} workers):")
    start = time.time()
    dyn_dict, dyn_period_dict, dyn_max_period, dyn_periods_sum = lfsr_sequence_mapper_parallel_dynamic(
        C, V, gf_order, period_only=True, algorithm="enumeration",
        num_workers=num_workers, batch_size=None, no_progress=True
    )
    dyn_auto_time = time.time() - start
    dyn_auto_speedup = seq_time / dyn_auto_time if dyn_auto_time > 0 else 0
    
    correct = (
        len(dyn_period_dict) == len(seq_period_dict) and
        dyn_periods_sum == seq_periods_sum and
        dyn_max_period == seq_max_period
    )
    status = "✓ CORRECT" if correct else "✗ INCORRECT"
    print(f"   {status}: {dyn_auto_time:.3f}s (speedup: {dyn_auto_speedup:.2f}x)")
    print(f"   Sequences: {len(dyn_period_dict)}, Sum: {dyn_periods_sum}, Max: {dyn_max_period}")
    
    # Test 3-5: Dynamic with manual batch sizes
    manual_batch_sizes = []
    if state_space_size < 8192:
        manual_batch_sizes = [100, 500, 1000]
    elif state_space_size < 65536:
        manual_batch_sizes = [100, 200, 500]
    else:
        manual_batch_sizes = [50, 100, 200]
    
    results = {}
    for batch_size in manual_batch_sizes:
        print(f"\n3. Dynamic mode (batch_size={batch_size}, {num_workers} workers):")
        start = time.time()
        dyn_dict, dyn_period_dict, dyn_max_period, dyn_periods_sum = lfsr_sequence_mapper_parallel_dynamic(
            C, V, gf_order, period_only=True, algorithm="enumeration",
            num_workers=num_workers, batch_size=batch_size, no_progress=True
        )
        dyn_manual_time = time.time() - start
        dyn_manual_speedup = seq_time / dyn_manual_time if dyn_manual_time > 0 else 0
        
        correct = (
            len(dyn_period_dict) == len(seq_period_dict) and
            dyn_periods_sum == seq_periods_sum and
            dyn_max_period == seq_max_period
        )
        status = "✓ CORRECT" if correct else "✗ INCORRECT"
        print(f"   {status}: {dyn_manual_time:.3f}s (speedup: {dyn_manual_speedup:.2f}x)")
        print(f"   Sequences: {len(dyn_period_dict)}, Sum: {dyn_periods_sum}, Max: {dyn_max_period}")
        results[batch_size] = {
            'time': dyn_manual_time,
            'speedup': dyn_manual_speedup,
            'correct': correct
        }
    
    # Summary
    print(f"\n{'─'*80}")
    print(f"Summary for {desc}:")
    print(f"  Sequential: {seq_time:.3f}s")
    print(f"  Dynamic (auto): {dyn_auto_time:.3f}s ({dyn_auto_speedup:.2f}x speedup)")
    for batch_size, result in results.items():
        print(f"  Dynamic (batch={batch_size}): {result['time']:.3f}s ({result['speedup']:.2f}x speedup)")
    
    return {
        'desc': desc,
        'state_space_size': state_space_size,
        'category': category,
        'expected_range': expected_range,
        'seq_time': seq_time,
        'dyn_auto_time': dyn_auto_time,
        'dyn_auto_speedup': dyn_auto_speedup,
        'manual_results': results
    }


def main():
    """Run tests for different problem sizes."""
    print("="*80)
    print("ADAPTIVE BATCH SIZING - COMPREHENSIVE TEST")
    print("="*80)
    
    # Test cases: different LFSR sizes
    test_cases = [
        ([1, 1, 0, 1], 2, "4-bit"),  # 16 states - Small
        ([1, 0, 1, 1, 0, 0, 0, 1], 2, "8-bit"),  # 256 states - Small
        ([1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1], 2, "12-bit"),  # 4096 states - Small
        ([1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], 2, "14-bit"),  # 16384 states - Medium
        ([1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], 2, "16-bit"),  # 65536 states - Medium
    ]
    
    all_results = []
    
    for coeffs, gf_order, desc in test_cases:
        try:
            result = run_test(coeffs, gf_order, desc, num_workers=4)
            if result:
                all_results.append(result)
        except Exception as e:
            print(f"\n✗ Error testing {desc}: {e}")
            import traceback
            traceback.print_exc()
    
    # Final summary
    print(f"\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}")
    
    print("\nProblem Size Categories:")
    for result in all_results:
        print(f"\n{result['desc']} ({result['category']}):")
        print(f"  State space: {result['state_space_size']:,} states")
        print(f"  Expected batch range: {result['expected_range']}")
        print(f"  Sequential: {result['seq_time']:.3f}s")
        print(f"  Dynamic (auto): {result['dyn_auto_time']:.3f}s ({result['dyn_auto_speedup']:.2f}x)")
        for batch_size, manual_result in result['manual_results'].items():
            print(f"  Batch {batch_size}: {manual_result['time']:.3f}s ({manual_result['speedup']:.2f}x)")
    
    print(f"\n{'='*80}")
    print("✅ Testing complete!")
    print(f"{'='*80}")


if __name__ == '__main__':
    main()
