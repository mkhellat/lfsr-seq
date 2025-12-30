#!/usr/bin/env python3
"""
Comprehensive profiling script for 16-bit LFSR parallel execution.

This script profiles both sequential and parallel execution modes,
collecting detailed timing information at each stage to identify bottlenecks.
"""

import time
import sys
import os
import multiprocessing
from typing import Dict, Any, Tuple
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lfsr.core import build_state_update_matrix
from sage.all import GF, VectorSpace
from lfsr.analysis import (
    lfsr_sequence_mapper,
    lfsr_sequence_mapper_parallel,
    _partition_state_space,
    _process_state_chunk,
)


class Profiler:
    """Profiling context manager for timing operations."""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, *args):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        return False


def profile_sequential(
    C: Any,
    V: Any,
    gf_order: int,
    algorithm: str = 'enumeration',
    period_only: bool = True,
) -> Dict[str, Any]:
    """Profile sequential execution with detailed timing."""
    
    results = {
        'mode': 'sequential',
        'total_time': 0,
        'breakdown': {},
        'results': None,
    }
    
    print("\n" + "="*70)
    print("PROFILING SEQUENTIAL EXECUTION")
    print("="*70)
    
    # Total time
    start_time = time.time()
    seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
        C, V, gf_order,
        no_progress=True,
        algorithm=algorithm,
        period_only=period_only,
    )
    end_time = time.time()
    results['total_time'] = end_time - start_time
    results['results'] = {
        'sequences': len(period_dict),
        'periods_sum': periods_sum,
        'max_period': max_period,
    }
    
    print(f"Total Time: {results['total_time']:.3f}s")
    print(f"Sequences Found: {results['results']['sequences']}")
    print(f"Period Sum: {results['results']['periods_sum']}")
    print(f"Max Period: {results['results']['max_period']}")
    
    return results


def profile_parallel(
    C: Any,
    V: Any,
    gf_order: int,
    num_workers: int,
    algorithm: str = 'enumeration',
    period_only: bool = True,
) -> Dict[str, Any]:
    """Profile parallel execution with detailed timing breakdown."""
    
    results = {
        'mode': 'parallel',
        'num_workers': num_workers,
        'total_time': 0,
        'breakdown': {},
        'results': None,
    }
    
    print("\n" + "="*70)
    print(f"PROFILING PARALLEL EXECUTION ({num_workers} workers)")
    print("="*70)
    
    # Step 1: Partitioning
    print("\n[Step 1] Partitioning state space...")
    t1 = time.time()
    chunks = _partition_state_space(V, num_workers)
    t2 = time.time()
    results['breakdown']['partitioning'] = t2 - t1
    results['breakdown']['num_chunks'] = len(chunks)
    results['breakdown']['chunk_sizes'] = [len(c) for c in chunks]
    
    print(f"  Time: {results['breakdown']['partitioning']:.3f}s")
    print(f"  Chunks: {results['breakdown']['num_chunks']}")
    print(f"  Chunk sizes: {results['breakdown']['chunk_sizes']}")
    
    # Step 2: Prepare chunk data
    print("\n[Step 2] Preparing chunk data...")
    t3 = time.time()
    d = C.dimensions()[0]
    coeffs_vector = [int(C[i, d-1]) for i in range(d)]
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
        )
        chunk_data_list.append(chunk_data)
    t4 = time.time()
    results['breakdown']['prepare_data'] = t4 - t3
    
    print(f"  Time: {results['breakdown']['prepare_data']:.3f}s")
    
    # Step 3: Create pool and submit tasks
    print("\n[Step 3] Creating pool and submitting tasks...")
    ctx = multiprocessing.get_context('fork')
    
    t5 = time.time()
    with ctx.Pool(processes=num_workers) as pool:
        t6 = time.time()
        pool_creation_time = t6 - t5
        
        async_result = pool.map_async(_process_state_chunk, chunk_data_list)
        t7 = time.time()
        submit_time = t7 - t6
        
        # Step 4: Wait for results
        print("\n[Step 4] Waiting for worker results...")
        t8 = time.time()
        try:
            worker_results = async_result.get(timeout=600)  # 10 min timeout
            t9 = time.time()
            wait_time = t9 - t8
            results['breakdown']['wait_for_results'] = wait_time
            results['breakdown']['pool_creation'] = pool_creation_time
            results['breakdown']['submit_tasks'] = submit_time
            
            print(f"  Pool creation: {pool_creation_time:.3f}s")
            print(f"  Submit tasks: {submit_time:.3f}s")
            print(f"  Wait for results: {wait_time:.3f}s")
            
            # Analyze worker results
            total_processed = sum(r.get('processed_count', 0) for r in worker_results)
            total_sequences = sum(len(r.get('sequences', [])) for r in worker_results)
            total_errors = sum(len(r.get('errors', [])) for r in worker_results)
            
            print(f"  Total states processed: {total_processed}")
            print(f"  Total sequences found: {total_sequences}")
            print(f"  Total errors: {total_errors}")
                
        except multiprocessing.TimeoutError:
            wait_time = time.time() - t8
            results['breakdown']['wait_for_results'] = wait_time
            results['breakdown']['timeout'] = True
            print(f"  TIMEOUT after {wait_time:.3f}s")
            pool.terminate()
            pool.join()
            return results
    
    # Step 5: Merge results
    print("\n[Step 5] Merging results...")
    from lfsr.analysis import _merge_parallel_results
    t10 = time.time()
    d = C.dimensions()[0]
    par_dict, par_period_dict, par_max_period, par_periods_sum = _merge_parallel_results(
        worker_results, gf_order, d
    )
    t11 = time.time()
    results['breakdown']['merge_results'] = t11 - t10
    results['results'] = {
        'sequences': len(par_period_dict),
        'periods_sum': par_periods_sum,
        'max_period': par_max_period,
    }
    
    print(f"  Time: {results['breakdown']['merge_results']:.3f}s")
    print(f"  Sequences: {results['results']['sequences']}")
    print(f"  Period Sum: {results['results']['periods_sum']}")
    
    # Calculate total time
    results['total_time'] = (
        results['breakdown']['partitioning'] +
        results['breakdown']['prepare_data'] +
        results['breakdown'].get('pool_creation', 0) +
        results['breakdown'].get('submit_tasks', 0) +
        results['breakdown'].get('wait_for_results', 0) +
        results['breakdown']['merge_results']
    )
    
    print(f"\nTotal Parallel Time: {results['total_time']:.3f}s")
    
    return results


def generate_report(
    seq_results: Dict[str, Any],
    par_results: Dict[str, Any],
    state_space_size: int,
    output_file: str = 'profile_report_16bit.md',
):
    """Generate a comprehensive profiling report."""
    
    report = []
    report.append("# 16-bit LFSR Parallel Execution Profiling Report")
    report.append("")
    report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    report.append("## Test Configuration")
    report.append("")
    report.append(f"- **State Space Size**: {state_space_size:,} states")
    report.append(f"- **Algorithm**: enumeration")
    report.append(f"- **Period-Only Mode**: Yes")
    report.append(f"- **Number of Workers**: {par_results['num_workers']}")
    report.append("")
    
    report.append("## Results Summary")
    report.append("")
    report.append("| Metric | Sequential | Parallel | Difference |")
    report.append("|--------|------------|----------|------------|")
    
    seq_time = seq_results['total_time']
    par_time = par_results['total_time']
    speedup = seq_time / par_time if par_time > 0 else 0
    
    report.append(f"| **Total Time** | {seq_time:.3f}s | {par_time:.3f}s | {par_time - seq_time:+.3f}s ({speedup:.2f}x) |")
    report.append(f"| **Sequences Found** | {seq_results['results']['sequences']} | {par_results['results']['sequences']} | {par_results['results']['sequences'] - seq_results['results']['sequences']:+d} |")
    report.append(f"| **Period Sum** | {seq_results['results']['periods_sum']} | {par_results['results']['periods_sum']} | {par_results['results']['periods_sum'] - seq_results['results']['periods_sum']:+d} |")
    report.append("")
    
    report.append("## Sequential Execution Breakdown")
    report.append("")
    report.append(f"- **Total Time**: {seq_time:.3f}s")
    report.append(f"- **Time per State**: {seq_time / state_space_size * 1000:.3f}ms")
    report.append("")
    
    report.append("## Parallel Execution Breakdown")
    report.append("")
    
    breakdown = par_results['breakdown']
    
    report.append("| Stage | Time (s) | % of Total |")
    report.append("|-------|----------|------------|")
    
    total = par_time
    for stage, time_val in breakdown.items():
        if isinstance(time_val, (int, float)) and stage not in ['num_chunks']:
            pct = (time_val / total * 100) if total > 0 else 0
            report.append(f"| {stage.replace('_', ' ').title()} | {time_val:.3f} | {pct:.1f}% |")
    
    report.append("")
    
    # Calculate overhead
    computation_time = breakdown.get('wait_for_results', 0)
    overhead = total - computation_time
    
    report.append("## Overhead Analysis")
    report.append("")
    report.append(f"- **Computation Time** (worker execution): {computation_time:.3f}s ({computation_time/total*100:.1f}%)")
    report.append(f"- **Total Overhead**: {overhead:.3f}s ({overhead/total*100:.1f}%)")
    report.append(f"  - Partitioning: {breakdown.get('partitioning', 0):.3f}s")
    report.append(f"  - Data preparation: {breakdown.get('prepare_data', 0):.3f}s")
    report.append(f"  - Pool creation: {breakdown.get('pool_creation', 0):.3f}s")
    report.append(f"  - Task submission: {breakdown.get('submit_tasks', 0):.3f}s")
    report.append(f"  - Result merging: {breakdown.get('merge_results', 0):.3f}s")
    report.append("")
    
    # Efficiency
    theoretical_time = seq_time / par_results['num_workers']
    efficiency = (theoretical_time / par_time * 100) if par_time > 0 else 0
    
    report.append("## Performance Analysis")
    report.append("")
    report.append(f"- **Theoretical Speedup** (ideal): {par_results['num_workers']:.1f}x")
    report.append(f"- **Theoretical Time** (if perfect parallelization): {theoretical_time:.3f}s")
    report.append(f"- **Actual Speedup**: {speedup:.2f}x")
    report.append(f"- **Efficiency**: {efficiency:.1f}%")
    report.append("")
    
    # Bottleneck identification
    report.append("## Bottleneck Identification")
    report.append("")
    
    max_overhead_stage = max(
        [(k, v) for k, v in breakdown.items() if isinstance(v, (int, float)) and k not in ['num_chunks']],
        key=lambda x: x[1],
        default=(None, 0)
    )
    
    if max_overhead_stage[0]:
        report.append(f"**Largest Overhead Stage**: {max_overhead_stage[0].replace('_', ' ').title()} ({max_overhead_stage[1]:.3f}s, {max_overhead_stage[1]/total*100:.1f}%)")
        report.append("")
    
    if speedup < 1.0:
        report.append("### ⚠️ Parallel is SLOWER than Sequential")
        report.append("")
        report.append("**Reasons:**")
        report.append("")
        report.append(f"1. **Overhead Dominates**: {overhead:.3f}s overhead vs {computation_time:.3f}s computation")
        report.append(f"2. **Partitioning Cost**: {breakdown.get('partitioning', 0):.3f}s to partition {state_space_size:,} states")
        report.append(f"3. **IPC Overhead**: Data serialization/deserialization between processes")
        report.append(f"4. **Cycles Spanning Chunks**: Workers may process overlapping cycles")
        report.append("")
    else:
        report.append("### ✅ Parallel provides speedup")
        report.append("")
        report.append(f"**Speedup**: {speedup:.2f}x")
        report.append("")
    
    # Recommendations
    report.append("## Recommendations")
    report.append("")
    
    if speedup < 1.0:
        report.append("For this LFSR size, **sequential execution is recommended**.")
        report.append("")
        report.append("Parallel processing would be beneficial for:")
        report.append(f"- State spaces > {state_space_size * 10:,} states")
        report.append("- Very long periods (> 10,000)")
        report.append("- When computation time >> overhead time")
    else:
        report.append("Parallel processing provides benefit for this case.")
        report.append("")
        report.append("To improve further:")
        report.append(f"- Reduce partitioning overhead (currently {breakdown.get('partitioning', 0):.3f}s)")
        report.append(f"- Optimize IPC (currently significant overhead)")
    
    report.append("")
    report.append("---")
    report.append("")
    report.append("*Report generated by profile_16bit.py*")
    
    # Write report
    with open(output_file, 'w') as f:
        f.write('\n'.join(report))
    
    print("\n" + "="*70)
    print(f"Report written to: {output_file}")
    print("="*70)


def main():
    """Main profiling function."""
    
    # 16-bit LFSR: coefficients for a 16-bit LFSR
    # Using a known 16-bit primitive polynomial: x^16 + x^5 + x^3 + x^2 + 1
    # Coefficients are [c0, c1, ..., c15] where polynomial is x^16 + c15*x^15 + ... + c0
    # For x^16 + x^5 + x^3 + x^2 + 1: c0=1, c2=1, c3=1, c5=1, all others 0
    # But we need 16 coefficients for a 16-bit LFSR (degree 16)
    coeffs = [1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # 16 coefficients for degree 16
    
    print("="*70)
    print("16-BIT LFSR PARALLEL EXECUTION PROFILING")
    print("="*70)
    print(f"\nLFSR Coefficients: {coeffs}")
    print(f"LFSR Degree: {len(coeffs) - 1}")
    
    # Build state update matrix
    C, CS = build_state_update_matrix(coeffs, 2)
    V = VectorSpace(GF(2), 16)
    
    # Get actual state space size from VectorSpace
    state_space_size = 2 ** len(coeffs)
    print(f"State Space Size: {state_space_size:,} states")
    print(f"LFSR Degree: {len(coeffs)}")
    
    # Profile sequential
    seq_results = profile_sequential(C, V, 2, algorithm='enumeration', period_only=True)
    
    # Profile parallel (2 workers)
    par_results = profile_parallel(C, V, 2, num_workers=2, algorithm='enumeration', period_only=True)
    
    # Generate report
    generate_report(seq_results, par_results, state_space_size, 'profile_report_16bit.md')
    
    print("\n" + "="*70)
    print("PROFILING COMPLETE")
    print("="*70)
    print(f"\nSequential: {seq_results['total_time']:.3f}s")
    print(f"Parallel:   {par_results['total_time']:.3f}s")
    speedup = seq_results['total_time'] / par_results['total_time'] if par_results['total_time'] > 0 else 0
    print(f"Speedup:    {speedup:.2f}x")
    print("\nSee profile_report_16bit.md for detailed analysis.")


if __name__ == '__main__':
    main()
