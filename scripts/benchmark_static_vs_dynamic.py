#!/usr/bin/env sage-python
"""
Benchmark script comparing static vs dynamic parallel processing modes.

Tests both static (fixed chunks) and dynamic (shared task queue) parallel modes
on 8-bit and 12-bit LFSRs with detailed performance profiling.
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


def create_8bit_lfsr():
    """Create an 8-bit LFSR with a primitive polynomial."""
    # Primitive polynomial: x^8 + x^4 + x^3 + x^2 + 1
    coeffs_vector = [1, 0, 1, 1, 1, 0, 0, 0]  # c0 to c7
    gf_order = 2
    degree = 8
    
    F = GF(gf_order)
    V = VectorSpace(F, degree)
    state_update_matrix, _ = build_state_update_matrix(coeffs_vector, gf_order)
    
    return state_update_matrix, V, gf_order, coeffs_vector, degree


def create_12bit_lfsr():
    """Create a 12-bit LFSR with a primitive polynomial."""
    # Primitive polynomial: x^12 + x^6 + x^4 + x + 1
    coeffs_vector = [1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0]  # c0 to c11
    gf_order = 2
    degree = 12
    
    F = GF(gf_order)
    V = VectorSpace(F, degree)
    state_update_matrix, _ = build_state_update_matrix(coeffs_vector, gf_order)
    
    return state_update_matrix, V, gf_order, coeffs_vector, degree


def run_sequential(C, V, gf_order, algorithm='enumeration', period_only=True):
    """Run sequential processing and measure time."""
    print("  Running sequential...", flush=True)
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
    print(f"  Running static parallel ({num_workers} workers)...", flush=True)
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
    print(f"  Running dynamic parallel ({num_workers} workers, batch_size={batch_size})...", flush=True)
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
    print(f"  Verifying correctness for {test_name}...", flush=True)
    
    # Compare period dictionaries
    seq_periods = sorted(seq_result['period_dict'].items())
    par_periods = sorted(parallel_result['period_dict'].items())
    
    if seq_periods != par_periods:
        print(f"    ERROR: Period dictionaries don't match!", flush=True)
        print(f"    Sequential: {len(seq_periods)} sequences", flush=True)
        print(f"    Parallel: {len(par_periods)} sequences", flush=True)
        return False
    
    # Compare periods_sum
    if seq_result['periods_sum'] != parallel_result['periods_sum']:
        print(f"    ERROR: Period sums don't match!", flush=True)
        print(f"    Sequential: {seq_result['periods_sum']}", flush=True)
        print(f"    Parallel: {parallel_result['periods_sum']}", flush=True)
        return False
    
    # Compare max_period
    if seq_result['max_period'] != parallel_result['max_period']:
        print(f"    ERROR: Max periods don't match!", flush=True)
        print(f"    Sequential: {seq_result['max_period']}", flush=True)
        print(f"    Parallel: {parallel_result['max_period']}", flush=True)
        return False
    
    print(f"    ✓ Correctness verified", flush=True)
    return True


def benchmark_lfsr(name, create_func, worker_counts=[1, 2, 4, 8]):
    """Benchmark a specific LFSR configuration."""
    print(f"\n{'='*80}", flush=True)
    print(f"Benchmarking {name} LFSR", flush=True)
    print(f"{'='*80}", flush=True)
    
    # Create LFSR
    C, V, gf_order, coeffs_vector, degree = create_func()
    state_space_size = int(gf_order) ** degree
    
    print(f"\nConfiguration:", flush=True)
    print(f"  Degree: {degree}", flush=True)
    print(f"  Field: GF({gf_order})", flush=True)
    print(f"  Coefficients: {coeffs_vector}", flush=True)
    print(f"  State space size: {state_space_size:,}", flush=True)
    
    algorithm = 'enumeration'
    period_only = True
    
    results = {
        'name': name,
        'degree': degree,
        'gf_order': gf_order,
        'state_space_size': state_space_size,
        'algorithm': algorithm,
        'period_only': period_only,
        'timestamp': datetime.now().isoformat(),
    }
    
    # Run sequential
    print(f"\n1. Sequential Execution", flush=True)
    seq_result = run_sequential(C, V, gf_order, algorithm=algorithm, period_only=period_only)
    results['sequential'] = seq_result
    print(f"  Time: {seq_result['elapsed']:.3f}s", flush=True)
    print(f"  Sequences: {seq_result['num_sequences']}", flush=True)
    
    # Run static parallel with different worker counts
    print(f"\n2. Static Parallel Execution", flush=True)
    static_results = {}
    for num_workers in worker_counts:
        result = run_static_parallel(C, V, gf_order, num_workers, algorithm=algorithm, period_only=period_only)
        static_results[num_workers] = result
        
        speedup = seq_result['elapsed'] / result['elapsed']
        print(f"  {num_workers} workers: {result['elapsed']:.3f}s (speedup: {speedup:.2f}x)", flush=True)
        
        # Verify correctness
        verify_correctness(seq_result, result, f"static-{num_workers}w")
    
    results['static'] = static_results
    
    # Run dynamic parallel with different worker counts
    print(f"\n3. Dynamic Parallel Execution", flush=True)
    dynamic_results = {}
    for num_workers in worker_counts:
        result = run_dynamic_parallel(C, V, gf_order, num_workers, algorithm=algorithm, period_only=period_only)
        dynamic_results[num_workers] = result
        
        speedup = seq_result['elapsed'] / result['elapsed']
        print(f"  {num_workers} workers: {result['elapsed']:.3f}s (speedup: {speedup:.2f}x)", flush=True)
        
        # Verify correctness
        verify_correctness(seq_result, result, f"dynamic-{num_workers}w")
    
    results['dynamic'] = dynamic_results
    
    # Compare static vs dynamic
    print(f"\n4. Static vs Dynamic Comparison", flush=True)
    print(f"  {'Workers':<10} {'Static':<12} {'Dynamic':<12} {'Static/Dynamic':<15}", flush=True)
    print(f"  {'-'*10} {'-'*12} {'-'*12} {'-'*15}", flush=True)
    for num_workers in worker_counts:
        static_time = static_results[num_workers]['elapsed']
        dynamic_time = dynamic_results[num_workers]['elapsed']
        ratio = static_time / dynamic_time if dynamic_time > 0 else 0
        print(f"  {num_workers:<10} {static_time:>10.3f}s  {dynamic_time:>10.3f}s  {ratio:>13.2f}x", flush=True)
    
    return results


def main():
    """Main benchmark function."""
    print("="*80, flush=True)
    print("Static vs Dynamic Parallel Processing Benchmark", flush=True)
    print("="*80, flush=True)
    print(f"Timestamp: {datetime.now().isoformat()}", flush=True)
    print(f"CPU count: {multiprocessing.cpu_count()}", flush=True)
    
    all_results = {
        'timestamp': datetime.now().isoformat(),
        'cpu_count': multiprocessing.cpu_count(),
        'benchmarks': [],
    }
    
    # Benchmark 8-bit LFSR
    results_8bit = benchmark_lfsr("8-bit", create_8bit_lfsr, worker_counts=[1, 2, 4, 8])
    all_results['benchmarks'].append(results_8bit)
    
    # Benchmark 12-bit LFSR
    results_12bit = benchmark_lfsr("12-bit", create_12bit_lfsr, worker_counts=[1, 2, 4, 8])
    all_results['benchmarks'].append(results_12bit)
    
    # Save results to JSON
    output_file = f"scripts/benchmark_static_vs_dynamic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n{'='*80}", flush=True)
    print(f"Benchmark complete! Results saved to: {output_file}", flush=True)
    print(f"{'='*80}", flush=True)
    
    return all_results


if __name__ == "__main__":
    main()
