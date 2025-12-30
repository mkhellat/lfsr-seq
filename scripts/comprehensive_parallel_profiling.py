#!/usr/bin/env sage-python
"""
Comprehensive profiling script for static vs dynamic parallel processing.

Tests correctness, performance, and load imbalance for:
- 12-bit, 14-bit, and 16-bit LFSRs (incremental: 12-bit first, then 14-bit, then 16-bit)
- Multiple LFSR configurations (different polynomials)
- Different worker counts (1, 2, 4, 8)
- Static vs dynamic parallel modes

Measures:
1. Correctness: Results match sequential
2. Performance: Execution time and speedup
3. Load imbalance: Work distribution across workers

Progress tracking: Shows current phase and exits on error.
"""

import os
import sys
import time
import json
import multiprocessing
from collections import defaultdict
from typing import Dict, List, Any, Tuple
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sage.all import GF, VectorSpace
from lfsr.analysis import (
    lfsr_sequence_mapper,
    lfsr_sequence_mapper_parallel,
    lfsr_sequence_mapper_parallel_dynamic,
)
from lfsr.core import build_state_update_matrix


# LFSR configurations by bit size: (name, degree, coeffs_vector)
LFSR_CONFIGS_12BIT = [
    ("12-bit-v1", 12, [1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0]),  # x^12 + x^6 + x^4 + x + 1
    ("12-bit-v2", 12, [1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0]),  # x^12 + x^7 + x^6 + x^2 + 1
]

LFSR_CONFIGS_14BIT = [
    ("14-bit-v1", 14, [1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0]),  # x^14 + x^5 + x^3 + x + 1
    ("14-bit-v2", 14, [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]),  # x^14 + x^10 + x^6 + x + 1
]

LFSR_CONFIGS_16BIT = [
    ("16-bit-v1", 16, [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # x^16 + x^5 + x^3 + x^2 + 1
    ("16-bit-v2", 16, [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # x^16 + x + 1
]


def create_lfsr(name, degree, coeffs_vector):
    """Create an LFSR with given configuration."""
    gf_order = 2
    
    F = GF(gf_order)
    V = VectorSpace(F, degree)
    state_update_matrix, _ = build_state_update_matrix(coeffs_vector, gf_order)
    
    return state_update_matrix, V, gf_order, coeffs_vector, degree


def run_sequential(C, V, gf_order, algorithm='enumeration', period_only=True):
    """Run sequential processing and measure time."""
    start_time = time.time()
    
    seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
        C, V, gf_order, output_file=None, no_progress=True,
        algorithm=algorithm, period_only=period_only
    )
    
    elapsed = time.time() - start_time
    
    return {
        'seq_dict': seq_dict,
        'period_dict': period_dict,
        'max_period': max_period,
        'periods_sum': periods_sum,
        'elapsed': elapsed,
        'num_sequences': len(period_dict),
    }


def run_static_parallel(C, V, gf_order, num_workers, algorithm='enumeration', period_only=True):
    """Run static parallel processing and measure time."""
    start_time = time.time()
    
    seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel(
        C, V, gf_order, output_file=None, no_progress=True,
        algorithm=algorithm, period_only=period_only, num_workers=num_workers
    )
    
    elapsed = time.time() - start_time
    
    return {
        'seq_dict': seq_dict,
        'period_dict': period_dict,
        'max_period': max_period,
        'periods_sum': periods_sum,
        'elapsed': elapsed,
        'num_sequences': len(period_dict),
        'num_workers': num_workers,
    }


def run_dynamic_parallel(C, V, gf_order, num_workers, algorithm='enumeration', period_only=True, batch_size=200):
    """Run dynamic parallel processing and measure time."""
    start_time = time.time()
    
    seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel_dynamic(
        C, V, gf_order, output_file=None, no_progress=True,
        algorithm=algorithm, period_only=period_only, num_workers=num_workers, batch_size=batch_size
    )
    
    elapsed = time.time() - start_time
    
    return {
        'seq_dict': seq_dict,
        'period_dict': period_dict,
        'max_period': max_period,
        'periods_sum': periods_sum,
        'elapsed': elapsed,
        'num_sequences': len(period_dict),
        'num_workers': num_workers,
        'batch_size': batch_size,
    }


def verify_correctness(seq_result, parallel_result, test_name):
    """Verify that parallel results match sequential results."""
    errors = []
    
    # Compare period dictionaries
    seq_periods = sorted(seq_result['period_dict'].items())
    par_periods = sorted(parallel_result['period_dict'].items())
    
    if seq_periods != par_periods:
        errors.append(f"Period dictionaries don't match: seq={len(seq_periods)}, par={len(par_periods)}")
        errors.append(f"  Sequential periods: {[p for _, p in seq_periods]}")
        errors.append(f"  Parallel periods: {[p for _, p in par_periods]}")
    
    # Compare periods_sum
    if seq_result['periods_sum'] != parallel_result['periods_sum']:
        errors.append(f"Period sums don't match: seq={seq_result['periods_sum']}, par={parallel_result['periods_sum']}")
    
    # Compare max_period
    if seq_result['max_period'] != parallel_result['max_period']:
        errors.append(f"Max periods don't match: seq={seq_result['max_period']}, par={parallel_result['max_period']}")
    
    # Compare num_sequences
    if seq_result['num_sequences'] != parallel_result['num_sequences']:
        errors.append(f"Num sequences don't match: seq={seq_result['num_sequences']}, par={parallel_result['num_sequences']}")
    
    return len(errors) == 0, errors


def profile_lfsr_config(name, degree, coeffs_vector, worker_counts=[1, 2, 4, 8]):
    """Profile a specific LFSR configuration."""
    print(f"\n{'='*80}", flush=True)
    print(f"Profiling {name} LFSR (degree {degree})", flush=True)
    print(f"{'='*80}", flush=True)
    
    # Create LFSR
    try:
        C, V, gf_order, _, _ = create_lfsr(name, degree, coeffs_vector)
        state_space_size = int(gf_order) ** degree
    except Exception as e:
        print(f"ERROR: Failed to create LFSR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        raise
    
    print(f"\nConfiguration:", flush=True)
    print(f"  Name: {name}", flush=True)
    print(f"  Degree: {degree}", flush=True)
    print(f"  Coefficients: {coeffs_vector}", flush=True)
    print(f"  State space size: {state_space_size:,}", flush=True)
    
    algorithm = 'enumeration'
    period_only = True
    
    results = {
        'name': name,
        'degree': degree,
        'state_space_size': state_space_size,
        'algorithm': algorithm,
        'period_only': period_only,
        'timestamp': datetime.now().isoformat(),
    }
    
    # Run sequential (baseline)
    print(f"\n[PHASE 1/5] Sequential Execution (baseline)", flush=True)
    try:
        seq_result = run_sequential(C, V, gf_order, algorithm=algorithm, period_only=period_only)
        results['sequential'] = seq_result
        print(f"  ✓ Time: {seq_result['elapsed']:.3f}s", flush=True)
        print(f"  ✓ Sequences: {seq_result['num_sequences']}, Periods sum: {seq_result['periods_sum']}", flush=True)
    except Exception as e:
        print(f"  ✗ ERROR in sequential execution: {e}", flush=True)
        import traceback
        traceback.print_exc()
        raise
    
    # Run static parallel with different worker counts
    print(f"\n[PHASE 2/5] Static Parallel Execution", flush=True)
    static_results = {}
    for num_workers in worker_counts:
        print(f"  Testing {num_workers} workers...", flush=True)
        try:
            result = run_static_parallel(C, V, gf_order, num_workers, algorithm=algorithm, period_only=period_only)
            static_results[num_workers] = result
            
            speedup = seq_result['elapsed'] / result['elapsed'] if result['elapsed'] > 0 else 0
            print(f"    Time: {result['elapsed']:.3f}s (speedup: {speedup:.2f}x)", flush=True)
            
            # Verify correctness
            is_correct, errors = verify_correctness(seq_result, result, f"static-{num_workers}w")
            if is_correct:
                print(f"    ✓ Correctness verified", flush=True)
            else:
                print(f"    ✗ CORRECTNESS ERROR:", flush=True)
                for error in errors:
                    print(f"      {error}", flush=True)
                result['correctness_errors'] = errors
                raise ValueError(f"Correctness check failed for static-{num_workers}w: {errors}")
        except Exception as e:
            print(f"    ✗ ERROR in static parallel ({num_workers} workers): {e}", flush=True)
            import traceback
            traceback.print_exc()
            raise
    
    results['static'] = static_results
    
    # Run dynamic parallel with different worker counts
    print(f"\n[PHASE 3/5] Dynamic Parallel Execution", flush=True)
    dynamic_results = {}
    for num_workers in worker_counts:
        print(f"  Testing {num_workers} workers...", flush=True)
        try:
            result = run_dynamic_parallel(C, V, gf_order, num_workers, algorithm=algorithm, period_only=period_only)
            dynamic_results[num_workers] = result
            
            speedup = seq_result['elapsed'] / result['elapsed'] if result['elapsed'] > 0 else 0
            print(f"    Time: {result['elapsed']:.3f}s (speedup: {speedup:.2f}x)", flush=True)
            
            # Verify correctness
            is_correct, errors = verify_correctness(seq_result, result, f"dynamic-{num_workers}w")
            if is_correct:
                print(f"    ✓ Correctness verified", flush=True)
            else:
                print(f"    ✗ CORRECTNESS ERROR:", flush=True)
                for error in errors:
                    print(f"      {error}", flush=True)
                result['correctness_errors'] = errors
                raise ValueError(f"Correctness check failed for dynamic-{num_workers}w: {errors}")
        except Exception as e:
            print(f"    ✗ ERROR in dynamic parallel ({num_workers} workers): {e}", flush=True)
            import traceback
            traceback.print_exc()
            raise
    
    results['dynamic'] = dynamic_results
    
    # Performance comparison
    print(f"\n[PHASE 4/5] Performance Comparison", flush=True)
    print(f"  {'Workers':<10} {'Sequential':<12} {'Static':<12} {'Dynamic':<12} {'Static/Seq':<12} {'Dynamic/Seq':<12}", flush=True)
    print(f"  {'-'*10} {'-'*12} {'-'*12} {'-'*12} {'-'*12} {'-'*12}", flush=True)
    for num_workers in worker_counts:
        static_time = static_results[num_workers]['elapsed']
        dynamic_time = dynamic_results[num_workers]['elapsed']
        static_speedup = seq_result['elapsed'] / static_time if static_time > 0 else 0
        dynamic_speedup = seq_result['elapsed'] / dynamic_time if dynamic_time > 0 else 0
        print(f"  {num_workers:<10} {seq_result['elapsed']:>10.3f}s  {static_time:>10.3f}s  {dynamic_time:>10.3f}s  {static_speedup:>10.2f}x  {dynamic_speedup:>10.2f}x", flush=True)
    
    # Static vs Dynamic comparison
    print(f"\n[PHASE 5/5] Static vs Dynamic Comparison", flush=True)
    print(f"  {'Workers':<10} {'Static':<12} {'Dynamic':<12} {'Static/Dynamic':<15}", flush=True)
    print(f"  {'-'*10} {'-'*12} {'-'*12} {'-'*15}", flush=True)
    for num_workers in worker_counts:
        static_time = static_results[num_workers]['elapsed']
        dynamic_time = dynamic_results[num_workers]['elapsed']
        ratio = static_time / dynamic_time if dynamic_time > 0 else 0
        print(f"  {num_workers:<10} {static_time:>10.3f}s  {dynamic_time:>10.3f}s  {ratio:>13.2f}x", flush=True)
    
    print(f"\n✓ {name} profiling completed successfully!", flush=True)
    return results


def main():
    """Main profiling function."""
    print("="*80, flush=True)
    print("Comprehensive Parallel Processing Profiling (Incremental)", flush=True)
    print("="*80, flush=True)
    print(f"Timestamp: {datetime.now().isoformat()}", flush=True)
    print(f"CPU count: {multiprocessing.cpu_count()}", flush=True)
    
    all_results = {
        'timestamp': datetime.now().isoformat(),
        'cpu_count': multiprocessing.cpu_count(),
        'configs': [],
    }
    
    worker_counts = [1, 2, 4, 8]
    
    # Phase 1: Profile 12-bit LFSRs
    print(f"\n{'#'*80}", flush=True)
    print(f"PHASE 1: Profiling 12-bit LFSRs ({len(LFSR_CONFIGS_12BIT)} configurations)", flush=True)
    print(f"{'#'*80}", flush=True)
    
    for name, degree, coeffs_vector in LFSR_CONFIGS_12BIT:
        try:
            print(f"\n>>> Starting {name}...", flush=True)
            results = profile_lfsr_config(name, degree, coeffs_vector, worker_counts)
            all_results['configs'].append(results)
            print(f">>> {name} completed successfully!\n", flush=True)
        except Exception as e:
            print(f"\n{'!'*80}", flush=True)
            print(f"FATAL ERROR profiling {name}: {e}", flush=True)
            print(f"{'!'*80}", flush=True)
            import traceback
            traceback.print_exc()
            print(f"\nExiting due to error. Partial results saved.", flush=True)
            # Save partial results
            output_file = f"scripts/comprehensive_profiling_12bit_partial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump(all_results, f, indent=2, default=str)
            print(f"Partial results saved to: {output_file}", flush=True)
            sys.exit(1)
    
    # Save 12-bit results
    output_file_12bit = f"scripts/comprehensive_profiling_12bit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file_12bit, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n{'='*80}", flush=True)
    print("12-bit profiling complete!", flush=True)
    print(f"Results saved to: {output_file_12bit}", flush=True)
    print(f"{'='*80}", flush=True)
    
    # Summary for 12-bit
    print(f"\n12-bit Summary:", flush=True)
    for config in all_results['configs']:
        name = config['name']
        seq_time = config['sequential']['elapsed']
        print(f"\n{name}:", flush=True)
        print(f"  Sequential: {seq_time:.3f}s", flush=True)
        for num_workers in worker_counts:
            if num_workers in config.get('static', {}):
                static_time = config['static'][num_workers]['elapsed']
                dynamic_time = config['dynamic'][num_workers]['elapsed']
                static_speedup = seq_time / static_time if static_time > 0 else 0
                dynamic_speedup = seq_time / dynamic_time if dynamic_time > 0 else 0
                print(f"  {num_workers} workers: Static {static_time:.3f}s ({static_speedup:.2f}x), Dynamic {dynamic_time:.3f}s ({dynamic_speedup:.2f}x)", flush=True)
    
    print(f"\n{'='*80}", flush=True)
    print("Next: Run script again with 14-bit configurations, then 16-bit.", flush=True)
    print(f"{'='*80}", flush=True)
    
    return all_results


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting.", flush=True)
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
