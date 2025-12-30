#!/usr/bin/env sage-python
"""
Investigate parallel execution correctness and performance.

Questions to answer:
1. Are parallel results correct (match sequential)?
2. What is the actual speedup?
3. Why are 4/8 workers slower than 2 workers?
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


def create_12bit_lfsr():
    """Create a 12-bit LFSR."""
    coeffs_vector = [1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0]
    gf_order = 2
    degree = 12
    
    F = GF(gf_order)
    V = VectorSpace(F, degree)
    state_update_matrix, _ = build_state_update_matrix(coeffs_vector, gf_order)
    
    return state_update_matrix, V, gf_order, coeffs_vector, degree


def extract_cycles_from_results(sequences, periods):
    """
    Extract cycle information from results in a normalized format.
    
    Returns:
        Dict mapping period -> list of cycle signatures (min_state tuples)
    """
    cycles_by_period = defaultdict(list)
    
    # Handle both sequential and parallel result formats
    if isinstance(sequences, dict):
        # Parallel format: {worker_id: [sequences]}
        for worker_id, seq_list in sequences.items():
            for seq in seq_list:
                states = seq.get('states', [])
                period = seq.get('period', 0)
                
                if not states or period == 0:
                    continue
                
                # Get min_state
                if isinstance(states, tuple) and len(states) == 1:
                    min_state = states[0]
                elif isinstance(states, list) and len(states) > 0:
                    min_state = min(states)
                else:
                    continue
                
                min_state_tuple = tuple(min_state) if not isinstance(min_state, tuple) else min_state
                cycles_by_period[period].append(min_state_tuple)
    else:
        # Sequential format: {period: [sequences]}
        for period, seq_list in sequences.items():
            for seq in seq_list:
                states = seq.get('states', [])
                
                if not states:
                    continue
                
                # Get min_state
                if isinstance(states, tuple) and len(states) == 1:
                    min_state = states[0]
                elif isinstance(states, list) and len(states) > 0:
                    min_state = min(states)
                else:
                    continue
                
                min_state_tuple = tuple(min_state) if not isinstance(min_state, tuple) else min_state
                cycles_by_period[period].append(min_state_tuple)
    
    # Deduplicate within each period
    for period in cycles_by_period:
        cycles_by_period[period] = list(set(cycles_by_period[period]))
    
    return cycles_by_period


def compare_results(seq_cycles, par_cycles, seq_periods, par_periods):
    """Compare sequential and parallel results in detail."""
    print("\n" + "="*80)
    print("DETAILED CORRECTNESS COMPARISON")
    print("="*80)
    
    # Compare cycles by period
    all_periods = set(seq_cycles.keys()) | set(par_cycles.keys())
    
    match = True
    issues = []
    
    for period in sorted(all_periods):
        seq_cycle_sigs = set(seq_cycles.get(period, []))
        par_cycle_sigs = set(par_cycles.get(period, []))
        
        if seq_cycle_sigs != par_cycle_sigs:
            match = False
            missing = seq_cycle_sigs - par_cycle_sigs
            extra = par_cycle_sigs - seq_cycle_sigs
            
            if missing:
                issues.append(f"Period {period}: Missing cycles: {len(missing)}")
                for sig in list(missing)[:3]:
                    issues.append(f"  - {sig[:20]}...")
            if extra:
                issues.append(f"Period {period}: Extra cycles: {len(extra)}")
                for sig in list(extra)[:3]:
                    issues.append(f"  - {sig[:20]}...")
        else:
            print(f"Period {period}: ✓ Match ({len(seq_cycle_sigs)} cycles)")
    
    # Compare period counts
    seq_total = sum(seq_periods.values())
    par_total = sum(par_periods.values())
    
    print(f"\nPeriod sum comparison:")
    print(f"  Sequential: {seq_total}")
    print(f"  Parallel: {par_total}")
    print(f"  Match: {'✓' if seq_total == par_total else '✗'}")
    
    if not match:
        print("\n" + "="*80)
        print("ISSUES FOUND:")
        print("="*80)
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✓ ALL RESULTS MATCH!")
    
    return match and (seq_total == par_total)


def profile_worker_timing(num_workers):
    """Profile worker execution with detailed timing."""
    print("\n" + "="*80)
    print(f"PROFILING {num_workers} WORKERS")
    print("="*80)
    
    C, V, gf_order, coeffs_vector, degree = create_12bit_lfsr()
    
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
    
    # Wait for results (this is where we measure actual work)
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
        processed = worker_results[worker_id][1].get('processed_count', 0)
        sequences = len(worker_results[worker_id][1].get('sequences', []))
        print(f"  Worker {worker_id}: {worker_time:.4f}s ({processed} states, {sequences} sequences)")
    
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
    
    # Check shared cycles usage
    print(f"\nShared Cycle Registry:")
    print(f"  Total cycles claimed: {len(shared_cycles)}")
    for min_state, worker_id in shared_cycles.items():
        print(f"    {tuple(min_state)[:12]}... -> Worker {worker_id}")
    
    return {
        'total_time': total_time,
        'partition_time': partition_time,
        'prepare_time': prepare_time,
        'pool_time': pool_time,
        'submit_time': submit_time,
        'execution_time': execution_time,
        'worker_times': worker_times,
        'worker_results': worker_results,
        'shared_cycles': dict(shared_cycles)
    }


def main():
    """Main investigation."""
    print("="*80)
    print("PARALLEL EXECUTION INVESTIGATION")
    print("="*80)
    
    C, V, gf_order, coeffs_vector, degree = create_12bit_lfsr()
    algorithm = 'enumeration'
    period_only = True
    
    # 1. Run sequential
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
    
    seq_cycles = extract_cycles_from_results(seq_sequences, seq_periods)
    
    print(f"\nSequential Results:")
    print(f"  Time: {seq_time:.4f}s")
    print(f"  Total states: {seq_total_states}")
    print(f"  Max period: {seq_max_period}")
    print(f"  Cycles by period:")
    for period in sorted(seq_cycles.keys()):
        print(f"    Period {period}: {len(seq_cycles[period])} cycles")
    
    # 2. Run parallel with different worker counts
    worker_counts = [1, 2, 4, 8]
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
        
        par_cycles = extract_cycles_from_results(par_sequences, par_periods)
        
        print(f"\nParallel Results ({num_workers} workers):")
        print(f"  Time: {par_time:.4f}s")
        print(f"  Total states: {par_total_states}")
        print(f"  Max period: {par_max_period}")
        print(f"  Cycles by period:")
        for period in sorted(par_cycles.keys()):
            print(f"    Period {period}: {len(par_cycles[period])} cycles")
        
        # Compare correctness
        correct = compare_results(seq_cycles, par_cycles, seq_periods, par_periods)
        
        # Calculate speedup
        speedup = seq_time / par_time if par_time > 0 else 0
        efficiency = speedup / num_workers if num_workers > 0 else 0
        
        results[num_workers] = {
            'time': par_time,
            'speedup': speedup,
            'efficiency': efficiency,
            'correct': correct,
            'cycles': par_cycles
        }
        
        # Detailed profiling
        profile = profile_worker_timing(num_workers)
        results[num_workers]['profile'] = profile
    
    # 3. Summary and analysis
    print("\n" + "="*80)
    print("3. SUMMARY AND ANALYSIS")
    print("="*80)
    
    print(f"\nSequential time: {seq_time:.4f}s")
    print(f"\nPerformance Summary:")
    print(f"{'Workers':<10} {'Time (s)':<12} {'Speedup':<10} {'Efficiency':<12} {'Correct':<10}")
    print("-" * 60)
    print(f"{'Sequential':<10} {seq_time:<12.4f} {'1.00x':<10} {'-':<12} {'✓':<10}")
    
    for num_workers in worker_counts:
        r = results[num_workers]
        print(f"{num_workers:<10} {r['time']:<12.4f} {r['speedup']:<10.2f}x {r['efficiency']:<12.1%} {'✓' if r['correct'] else '✗':<10}")
    
    # Analyze why 4/8 workers are slower
    print("\n" + "="*80)
    print("4. WHY ARE 4/8 WORKERS SLOWER?")
    print("="*80)
    
    if results[2]['time'] < results[4]['time']:
        print(f"\n2 workers: {results[2]['time']:.4f}s")
        print(f"4 workers: {results[4]['time']:.4f}s ({results[4]['time']/results[2]['time']:.2f}x slower)")
        
        p2 = results[2]['profile']
        p4 = results[4]['profile']
        
        print(f"\nEvidence from profiling:")
        print(f"  2 workers - Worker execution: {p2['execution_time']:.4f}s")
        print(f"  4 workers - Worker execution: {p4['execution_time']:.4f}s")
        print(f"  Difference: {p4['execution_time'] - p2['execution_time']:.4f}s")
        
        print(f"\n  2 workers - Max worker time: {max(p2['worker_times']):.4f}s")
        print(f"  4 workers - Max worker time: {max(p4['worker_times']):.4f}s")
        
        print(f"\n  2 workers - Load imbalance: {(max(p2['worker_times']) - min(p2['worker_times'])) / (sum(p2['worker_times'])/len(p2['worker_times'])):.1%}")
        print(f"  4 workers - Load imbalance: {(max(p4['worker_times']) - min(p4['worker_times'])) / (sum(p4['worker_times'])/len(p4['worker_times'])):.1%}")
        
        print(f"\n  2 workers - Overhead (non-execution): {p2['total_time'] - p2['execution_time']:.4f}s ({100*(p2['total_time'] - p2['execution_time'])/p2['total_time']:.1f}%)")
        print(f"  4 workers - Overhead (non-execution): {p4['total_time'] - p4['execution_time']:.4f}s ({100*(p4['total_time'] - p4['execution_time'])/p4['total_time']:.1f}%)")
        
        print(f"\nConclusion:")
        if p4['execution_time'] > p2['execution_time']:
            print(f"  - Worker execution time increased: {p4['execution_time'] - p2['execution_time']:.4f}s")
            print(f"  - Possible causes: Lock contention, load imbalance, or more workers processing same cycles")
        if (p4['total_time'] - p4['execution_time']) > (p2['total_time'] - p2['execution_time']):
            overhead_diff = (p4['total_time'] - p4['execution_time']) - (p2['total_time'] - p2['execution_time'])
            print(f"  - Overhead increased: {overhead_diff:.4f}s")
            print(f"  - Possible causes: More pool creation overhead, more IPC overhead")
    
    if results[4]['time'] < results[8]['time']:
        print(f"\n4 workers: {results[4]['time']:.4f}s")
        print(f"8 workers: {results[8]['time']:.4f}s ({results[8]['time']/results[4]['time']:.2f}x slower)")
        
        p4 = results[4]['profile']
        p8 = results[8]['profile']
        
        print(f"\nEvidence from profiling:")
        print(f"  4 workers - Worker execution: {p4['execution_time']:.4f}s")
        print(f"  8 workers - Worker execution: {p8['execution_time']:.4f}s")
        print(f"  Difference: {p8['execution_time'] - p4['execution_time']:.4f}s")
        
        print(f"\n  4 workers - Overhead: {p4['total_time'] - p4['execution_time']:.4f}s")
        print(f"  8 workers - Overhead: {p8['total_time'] - p8['execution_time']:.4f}s")
        print(f"  Overhead increase: {(p8['total_time'] - p8['execution_time']) - (p4['total_time'] - p4['execution_time']):.4f}s")


if __name__ == '__main__':
    main()
