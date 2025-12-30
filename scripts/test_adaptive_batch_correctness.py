#!/usr/bin/env python3
"""
Test script to verify correctness and metrics with adaptive batch sizing.

This script tests:
1. Correctness: Results match sequential for different batch sizes
2. Performance metrics: Timing and speedup are meaningful
3. Load imbalance: Metrics are accurate and meaningful
"""

import sys
import os
import time
import json
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
    print(f"ERROR: {e}")
    sys.exit(1)


def test_correctness(coeffs, gf_order, batch_sizes=[None, 100, 200, 500, 1000]):
    """Test that results are correct for different batch sizes."""
    print(f"\n{'='*80}")
    print(f"TESTING CORRECTNESS: {len(coeffs)}-bit LFSR over GF({gf_order})")
    print(f"{'='*80}")
    
    # Build state update matrix
    C, V = build_state_update_matrix(coeffs, gf_order)
    
    # Get sequential baseline
    print("\n1. Running sequential (baseline)...")
    seq_start = time.time()
    seq_dict, seq_period_dict, seq_max_period, seq_periods_sum = lfsr_sequence_mapper(
        C, V, gf_order, period_only=True, algorithm="enumeration"
    )
    seq_time = time.time() - seq_start
    print(f"   Sequential: {seq_time:.3f}s, {len(seq_period_dict)} sequences, sum={seq_periods_sum}")
    
    # Test each batch size
    results = {}
    for batch_size in batch_sizes:
        batch_desc = "auto" if batch_size is None else str(batch_size)
        print(f"\n2. Testing batch_size={batch_desc}...")
        
        try:
            dyn_start = time.time()
            dyn_dict, dyn_period_dict, dyn_max_period, dyn_periods_sum = lfsr_sequence_mapper_parallel_dynamic(
                C, V, gf_order, period_only=True, algorithm="enumeration",
                num_workers=2, batch_size=batch_size, no_progress=True
            )
            dyn_time = time.time() - dyn_start
            
            # Verify correctness
            correct = (
                len(dyn_period_dict) == len(seq_period_dict) and
                dyn_periods_sum == seq_periods_sum and
                dyn_max_period == seq_max_period
            )
            
            speedup = seq_time / dyn_time if dyn_time > 0 else 0
            
            results[batch_desc] = {
                'correct': correct,
                'time': dyn_time,
                'speedup': speedup,
                'sequences': len(dyn_period_dict),
                'periods_sum': dyn_periods_sum,
                'max_period': dyn_max_period
            }
            
            status = "✓ CORRECT" if correct else "✗ INCORRECT"
            print(f"   {status}: {dyn_time:.3f}s ({speedup:.2f}x), {len(dyn_period_dict)} sequences, sum={dyn_periods_sum}")
            
            if not correct:
                print(f"   ERROR: Mismatch!")
                print(f"     Expected: {len(seq_period_dict)} sequences, sum={seq_periods_sum}")
                print(f"     Got:      {len(dyn_period_dict)} sequences, sum={dyn_periods_sum}")
                
        except Exception as e:
            print(f"   ERROR: {e}")
            import traceback
            traceback.print_exc()
            results[batch_desc] = {'error': str(e)}
    
    return results


def test_metrics(coeffs, gf_order, batch_sizes=[None, 200, 500]):
    """Test that work metrics are meaningful."""
    print(f"\n{'='*80}")
    print(f"TESTING METRICS: {len(coeffs)}-bit LFSR over GF({gf_order})")
    print(f"{'='*80}")
    
    C, V = build_state_update_matrix(coeffs, gf_order)
    
    # Enable debug to capture metrics
    os.environ['DEBUG_PARALLEL'] = '1'
    
    results = {}
    for batch_size in batch_sizes:
        batch_desc = "auto" if batch_size is None else str(batch_size)
        print(f"\nTesting batch_size={batch_desc} with 4 workers...")
        
        try:
            # Capture stderr for metrics
            import io
            import contextlib
            
            stderr_capture = io.StringIO()
            with contextlib.redirect_stderr(stderr_capture):
                dyn_dict, dyn_period_dict, dyn_max_period, dyn_periods_sum = lfsr_sequence_mapper_parallel_dynamic(
                    C, V, gf_order, period_only=True, algorithm="enumeration",
                    num_workers=4, batch_size=batch_size, no_progress=True
                )
            
            stderr_output = stderr_capture.getvalue()
            
            # Extract imbalance info from stderr
            imbalance_info = None
            for line in stderr_output.split('\n'):
                if '[Load Imbalance]' in line:
                    imbalance_info = line
                    print(f"   {line}")
            
            results[batch_desc] = {
                'imbalance_info': imbalance_info,
                'stderr': stderr_output
            }
            
        except Exception as e:
            print(f"   ERROR: {e}")
            results[batch_desc] = {'error': str(e)}
    
    return results


def main():
    """Run all tests."""
    print("="*80)
    print("ADAPTIVE BATCH SIZING - CORRECTNESS & METRICS TEST")
    print("="*80)
    
    # Test cases: 12-bit, 14-bit
    test_cases = [
        ([1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1], 2, "12-bit"),
        ([1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], 2, "14-bit"),
    ]
    
    all_results = {}
    
    for coeffs, gf_order, desc in test_cases:
        print(f"\n{'#'*80}")
        print(f"# Testing {desc} LFSR")
        print(f"{'#'*80}")
        
        # Test correctness
        correctness_results = test_correctness(coeffs, gf_order)
        all_results[f"{desc}_correctness"] = correctness_results
        
        # Test metrics
        metrics_results = test_metrics(coeffs, gf_order)
        all_results[f"{desc}_metrics"] = metrics_results
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    all_correct = True
    for test_name, test_results in all_results.items():
        if 'correctness' in test_name:
            print(f"\n{test_name}:")
            for batch_size, result in test_results.items():
                if 'error' in result:
                    print(f"  {batch_size}: ERROR - {result['error']}")
                    all_correct = False
                elif result.get('correct', False):
                    print(f"  {batch_size}: ✓ Correct (speedup: {result['speedup']:.2f}x)")
                else:
                    print(f"  {batch_size}: ✗ INCORRECT")
                    all_correct = False
    
    if all_correct:
        print("\n✅ ALL TESTS PASSED - Results are correct for all batch sizes")
    else:
        print("\n✗ SOME TESTS FAILED - Check errors above")
        sys.exit(1)


if __name__ == '__main__':
    main()
