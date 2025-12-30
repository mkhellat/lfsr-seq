#!/usr/bin/env sage-python
"""
Profile a different 14-bit LFSR to test load imbalance hypothesis.

Hypothesis: Different cycle distributions should produce different load imbalance patterns
with static threading, since work is partitioned by state indices, not cycle structure.
"""

import os
import sys
import time
import multiprocessing
from collections import defaultdict

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sage.all import GF, VectorSpace
from lfsr.analysis import (
    lfsr_sequence_mapper,
    lfsr_sequence_mapper_parallel,
    _partition_state_space,
)
from lfsr.core import build_state_update_matrix


def create_14bit_lfsr_v2():
    """Create a different 14-bit LFSR with a different primitive polynomial."""
    # Primitive polynomial: x^14 + x^10 + x^6 + x + 1
    # Coefficients: [c0, c1, ..., c13]
    # c0=1, c1=1, c2=0, c3=0, c4=0, c5=0, c6=1, c7=0, c8=0, c9=0, c10=1, c11=0, c12=0, c13=0
    coeffs_vector = [1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]  # c0 to c13
    
    gf_order = 2
    degree = 14
    
    F = GF(gf_order)
    V = VectorSpace(F, degree)
    state_update_matrix, _ = build_state_update_matrix(coeffs_vector, gf_order)
    
    return state_update_matrix, V, gf_order, coeffs_vector, degree


def profile_worker_timing(num_workers):
    """Profile worker execution with detailed timing."""
    print("\n" + "="*80)
    print(f"PROFILING {num_workers} WORKERS")
    print("="*80)
    
    C, V, gf_order, coeffs_vector, degree = create_14bit_lfsr_v2()
    
    # Partition
    partition_start = time.time()
    chunks = _partition_state_space(V, num_workers)
    partition_time = time.time() - partition_start
    
    # Prepare data
    prepare_start = time.time()
    d = degree
    algorithm = 'enumeration'
    period_only = True
    
    manager = multiprocessing.Manager()
    shared_cycles = manager.dict()
    cycle_lock = manager.Lock()
    
    chunk_data_list = []
    for worker_id, chunk in enumerate(chunks):
        chunk_data = (
            chunk,
            coeffs_vector,
            gf_order,
            d,
            algorithm,
            period_only,
            worker_id,
            shared_cycles,
            cycle_lock,
        )
        chunk_data_list.append(chunk_data)
    prepare_time = time.time() - prepare_start
    
    # Create pool
    pool_start = time.time()
    pool = multiprocessing.Pool(processes=num_workers)
    pool_time = time.time() - pool_start
    
    # Submit tasks
    submit_start = time.time()
    from lfsr.analysis import _process_state_chunk
    async_results = [
        pool.apply_async(_process_state_chunk, (chunk_data,))
        for chunk_data in chunk_data_list
    ]
    submit_time = time.time() - submit_start
    
    # Wait for results
    execution_start = time.time()
    worker_results = []
    worker_times = []
    
    for i, async_result in enumerate(async_results):
        result_start = time.time()
        result = async_result.get()
        result_time = time.time() - result_start
        worker_results.append((i, result))
        worker_times.append(result_time)
    
    execution_time = time.time() - execution_start
    
    # Close pool
    pool.close()
    pool.join()
    
    total_time = time.time() - partition_start
    
    # Analyze results
    print(f"\nTiming Breakdown:")
    print(f"  Partitioning: {partition_time:.4f}s ({100*partition_time/total_time:.1f}%)")
    print(f"  Prepare data: {prepare_time:.4f}s ({100*prepare_time/total_time:.1f}%)")
    print(f"  Pool creation: {pool_time:.4f}s ({100*pool_time/total_time:.1f}%)")
    print(f"  Submit tasks: {submit_time:.4f}s ({100*submit_time/total_time:.1f}%)")
    print(f"  Worker execution: {execution_time:.4f}s ({100*execution_time/total_time:.1f}%)")
    print(f"  Total: {total_time:.4f}s")
    
    print(f"\nPer-Worker Execution Times:")
    for worker_id, worker_time in enumerate(worker_times):
        result = worker_results[worker_id][1]
        processed = result.get('processed_count', 0)
        sequences = len(result.get('sequences', []))
        work_metrics = result.get('work_metrics', {})
        
        print(f"  Worker {worker_id}: {worker_time:.4f}s")
        print(f"    States processed: {processed}")
        print(f"    Sequences found: {sequences}")
        if work_metrics:
            print(f"    Work metrics:")
            print(f"      States in chunk: {work_metrics.get('total_states_in_chunk', 0):,}")
            print(f"      States processed: {work_metrics.get('states_processed', 0):,}")
            print(f"      States skipped (visited): {work_metrics.get('states_skipped_visited', 0):,}")
            print(f"      States skipped (claimed): {work_metrics.get('states_skipped_claimed', 0):,}")
            print(f"      Cycles found: {work_metrics.get('cycles_found', 0):,}")
            print(f"      Cycles claimed: {work_metrics.get('cycles_claimed', 0):,}")
            print(f"      Cycles skipped: {work_metrics.get('cycles_skipped', 0):,}")
    
    # Analyze load balancing
    if len(worker_times) > 1:
        max_time = max(worker_times)
        min_time = min(worker_times)
        avg_time = sum(worker_times) / len(worker_times)
        imbalance = (max_time - min_time) / avg_time if avg_time > 0 else 0
        
        print(f"\nLoad Balancing:")
        print(f"  Max worker time: {max_time:.4f}s")
        print(f"  Min worker time: {min_time:.4f}s")
        print(f"  Average: {avg_time:.4f}s")
        print(f"  Imbalance ratio: {imbalance:.2%} (lower is better)")
        print(f"  Efficiency: {avg_time/max_time:.1%} (if all workers took max_time)")
    
    return {
        'total_time': total_time,
        'execution_time': execution_time,
        'worker_times': worker_times,
        'worker_results': worker_results,
    }


def main():
    """Main profiling."""
    print("="*80)
    print("14-BIT LFSR V2 PARALLEL EXECUTION PROFILING")
    print("Different primitive polynomial: x^14 + x^10 + x^6 + x + 1")
    print("="*80)
    
    C, V, gf_order, coeffs_vector, degree = create_14bit_lfsr_v2()
    algorithm = 'enumeration'
    period_only = True
    
    state_space_size = 2 ** degree
    print(f"\nLFSR Configuration:")
    print(f"  Degree: {degree}")
    print(f"  State space size: {state_space_size:,} states")
    print(f"  Coefficients: {coeffs_vector}")
    print(f"  Polynomial: x^14 + x^10 + x^6 + x + 1")
    
    # Run sequential
    print("\n" + "="*80)
    print("1. SEQUENTIAL EXECUTION")
    print("="*80)
    seq_start = time.time()
    seq_sequences, seq_periods, seq_total_states, seq_max_period = lfsr_sequence_mapper(
        C, V, gf_order,
        algorithm=algorithm,
        period_only=period_only,
        no_progress=True
    )
    seq_time = time.time() - seq_start
    
    print(f"\nSequential Results:")
    print(f"  Time: {seq_time:.4f}s")
    print(f"  Total states: {seq_total_states:,}")
    print(f"  Max period: {seq_max_period:,}")
    print(f"  Period sum: {sum(seq_periods.values()):,}")
    print(f"  Number of cycles: {len(seq_sequences)}")
    
    # Run parallel with different worker counts
    worker_counts = [2, 4, 8]
    results = {}
    
    for num_workers in worker_counts:
        print("\n" + "="*80)
        print(f"2. PARALLEL EXECUTION ({num_workers} workers)")
        print("="*80)
        
        par_start = time.time()
        par_sequences, par_periods, par_total_states, par_max_period = lfsr_sequence_mapper_parallel(
            C, V, gf_order,
            algorithm=algorithm,
            period_only=period_only,
            num_workers=num_workers,
            no_progress=True
        )
        par_time = time.time() - par_start
        
        print(f"\nParallel Results ({num_workers} workers):")
        print(f"  Time: {par_time:.4f}s")
        print(f"  Period sum: {sum(par_periods.values()):,}")
        print(f"  Correct: {'✓' if sum(par_periods.values()) == sum(seq_periods.values()) else '✗'}")
        
        # Calculate speedup
        speedup = seq_time / par_time if par_time > 0 else 0
        efficiency = speedup / num_workers if num_workers > 0 else 0
        
        results[num_workers] = {
            'time': par_time,
            'speedup': speedup,
            'efficiency': efficiency,
        }
        
        # Detailed profiling
        profile = profile_worker_timing(num_workers)
        results[num_workers]['profile'] = profile
    
    # Summary
    print("\n" + "="*80)
    print("3. SUMMARY AND COMPARISON")
    print("="*80)
    
    print(f"\nSequential time: {seq_time:.4f}s")
    print(f"\nPerformance Summary:")
    print(f"{'Workers':<10} {'Time (s)':<12} {'Speedup':<10} {'Efficiency':<12}")
    print("-" * 50)
    print(f"{'Sequential':<10} {seq_time:<12.4f} {'1.00x':<10} {'-':<12}")
    
    for num_workers in worker_counts:
        r = results[num_workers]
        print(f"{num_workers:<10} {r['time']:<12.4f} {r['speedup']:<10.2f}x {r['efficiency']:<12.1%}")
    
    # Load imbalance comparison
    print(f"\nLoad Imbalance Comparison:")
    for num_workers in worker_counts:
        profile = results[num_workers]['profile']
        worker_times = profile['worker_times']
        if len(worker_times) > 1:
            max_time = max(worker_times)
            min_time = min(worker_times)
            avg_time = sum(worker_times) / len(worker_times)
            imbalance = (max_time - min_time) / avg_time if avg_time > 0 else 0
            print(f"  {num_workers} workers: {imbalance:.1%} imbalance")


if __name__ == '__main__':
    main()
