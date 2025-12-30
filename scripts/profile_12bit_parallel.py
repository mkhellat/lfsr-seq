#!/usr/bin/env sage-python
"""
Comprehensive profiling script for 12-bit LFSR parallel execution.

Profiles both sequential and parallel execution with detailed metrics:
- Time breakdown by stage
- Per-worker statistics
- Redundancy detection
- Performance analysis
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

from sage.all import GF, VectorSpace, vector
from lfsr.analysis import (
    lfsr_sequence_mapper,
    lfsr_sequence_mapper_parallel,
    _partition_state_space,
)
from lfsr.core import build_state_update_matrix


def create_12bit_lfsr():
    """Create a 12-bit LFSR with a primitive polynomial."""
    # Primitive polynomial for GF(2)^12: x^12 + x^6 + x^4 + x + 1
    # Coefficients: [c0, c1, ..., c11] where c_i is coefficient of x^i
    # For x^12 + x^6 + x^4 + x + 1:
    # c0=1, c1=1, c2=0, c3=0, c4=1, c5=0, c6=1, c7=0, c8=0, c9=0, c10=0, c11=0
    coeffs_vector = [1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0]  # c0 to c11
    
    gf_order = 2
    degree = 12
    
    F = GF(gf_order)
    V = VectorSpace(F, degree)
    
    # Build state update matrix
    state_update_matrix, _ = build_state_update_matrix(coeffs_vector, gf_order)
    
    return state_update_matrix, V, gf_order, coeffs_vector, degree


def extract_cycle_signatures(sequences: Dict[int, List[Any]]) -> Dict[Tuple, Dict]:
    """
    Extract cycle signatures (min_state) and metadata.
    
    Returns:
        Dict mapping (min_state_tuple) -> {
            'period': int,
            'start_states': List[Tuple],
            'worker_ids': List[int],
            'count': int  # How many times this cycle was found
        }
    """
    signatures = {}
    
    for worker_id, seq_list in sequences.items():
        for seq in seq_list:
            states = seq.get('states', [])
            period = seq.get('period', 0)
            start_state = seq.get('start_state')
            
            if not states or period == 0:
                continue
            
            # Get min_state
            if isinstance(states, tuple) and len(states) == 1:
                # Period-only mode: states is (min_state,)
                min_state = states[0]
            elif isinstance(states, list) and len(states) > 0:
                # Full mode: find min
                min_state = min(states)
            else:
                continue
            
            min_state_tuple = tuple(min_state) if not isinstance(min_state, tuple) else min_state
            
            if min_state_tuple not in signatures:
                signatures[min_state_tuple] = {
                    'period': period,
                    'start_states': [],
                    'worker_ids': [],
                    'count': 0
                }
            
            signatures[min_state_tuple]['start_states'].append(tuple(start_state) if start_state else None)
            if worker_id not in signatures[min_state_tuple]['worker_ids']:
                signatures[min_state_tuple]['worker_ids'].append(worker_id)
            signatures[min_state_tuple]['count'] += 1
    
    return signatures


def profile_sequential(C, V, gf_order, algorithm='enumeration', period_only=True):
    """Profile sequential execution."""
    print("\n" + "="*80)
    print("SEQUENTIAL EXECUTION PROFILING")
    print("="*80)
    
    profile = {
        'start_time': time.time(),
        'stages': {}
    }
    
    # Stage 1: Execution
    stage_start = time.time()
    sequences, periods, total_states, max_period = lfsr_sequence_mapper(
        C, V, gf_order,
        algorithm=algorithm,
        period_only=period_only,
        no_progress=True
    )
    stage_end = time.time()
    
    profile['stages']['execution'] = stage_end - stage_start
    profile['end_time'] = stage_end
    profile['total_time'] = stage_end - profile['start_time']
    
    # Convert sequences to dict format
    seq_dict = {0: []}  # Single "worker" with id 0
    for period, seq_list in sequences.items():
        for seq in seq_list:
            seq_dict[0].append({
                'states': seq.get('states', []),
                'period': period,
                'start_state': tuple(seq.get('start_state', ()))
            })
    
    signatures = extract_cycle_signatures(seq_dict)
    
    profile['results'] = {
        'sequences': seq_dict,
        'signatures': signatures,
        'total_states': total_states,
        'max_period': max_period,
        'periods': periods,
        'unique_cycles': len(signatures),
        'total_sequences': sum(len(seq_list) for seq_list in seq_dict.values())
    }
    
    print(f"\nSequential Profile:")
    print(f"  Total time: {profile['total_time']:.4f}s")
    print(f"  Execution time: {profile['stages']['execution']:.4f}s")
    print(f"  Total states: {total_states}")
    print(f"  Unique cycles: {len(signatures)}")
    print(f"  Max period: {max_period}")
    
    return profile


def profile_parallel(C, V, gf_order, num_workers, algorithm='enumeration', period_only=True):
    """Profile parallel execution with detailed stage breakdown."""
    print("\n" + "="*80)
    print(f"PARALLEL EXECUTION PROFILING ({num_workers} workers)")
    print("="*80)
    
    profile = {
        'start_time': time.time(),
        'stages': {},
        'num_workers': num_workers
    }
    
    # Stage 1: Partitioning
    print("  Stage 1: Partitioning state space...", flush=True)
    stage_start = time.time()
    chunks = _partition_state_space(V, num_workers)
    stage_end = time.time()
    profile['stages']['partitioning'] = stage_end - stage_start
    profile['partitioning_details'] = {
        'num_chunks': len(chunks),
        'chunk_sizes': [len(chunk) for chunk in chunks],
        'total_states_partitioned': sum(len(chunk) for chunk in chunks)
    }
    print(f"    Time: {profile['stages']['partitioning']:.4f}s")
    print(f"    Chunks: {len(chunks)}, Sizes: {profile['partitioning_details']['chunk_sizes']}")
    
    # Stage 2: Prepare chunk data
    print("  Stage 2: Preparing chunk data...", flush=True)
    stage_start = time.time()
    # Extract coefficients from matrix
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
    stage_end = time.time()
    profile['stages']['prepare_data'] = stage_end - stage_start
    print(f"    Time: {profile['stages']['prepare_data']:.4f}s")
    
    # Stage 3: Create pool and submit tasks
    print("  Stage 3: Creating pool and submitting tasks...", flush=True)
    stage_start = time.time()
    pool = multiprocessing.Pool(processes=num_workers)
    stage_end = time.time()
    profile['stages']['pool_creation'] = stage_end - stage_start
    
    stage_start = time.time()
    from lfsr.analysis import _process_state_chunk
    async_results = [
        pool.apply_async(_process_state_chunk, (chunk_data,))
        for chunk_data in chunk_data_list
    ]
    stage_end = time.time()
    profile['stages']['submit_tasks'] = stage_end - stage_start
    print(f"    Pool creation: {profile['stages']['pool_creation']:.4f}s")
    print(f"    Submit tasks: {profile['stages']['submit_tasks']:.4f}s")
    
    # Stage 4: Wait for results
    print("  Stage 4: Waiting for worker results...", flush=True)
    stage_start = time.time()
    worker_results = []
    for i, async_result in enumerate(async_results):
        result = async_result.get()
        worker_results.append((i, result))
    stage_end = time.time()
    profile['stages']['worker_execution'] = stage_end - stage_start
    profile['worker_results'] = {}
    
    # Analyze worker results
    total_worker_time = 0
    total_processed = 0
    total_sequences = 0
    
    for worker_id, result in worker_results:
        processed = result.get('processed_count', 0)
        sequences_count = len(result.get('sequences', []))
        max_period = result.get('max_period', 0)
        errors = result.get('errors', [])
        
        profile['worker_results'][worker_id] = {
            'processed_count': processed,
            'sequences_count': sequences_count,
            'max_period': max_period,
            'errors': len(errors)
        }
        
        total_processed += processed
        total_sequences += sequences_count
    
    print(f"    Time: {profile['stages']['worker_execution']:.4f}s")
    print(f"    Total states processed: {total_processed}")
    print(f"    Total sequences found: {total_sequences}")
    
    # Stage 5: Merge results
    print("  Stage 5: Merging results...", flush=True)
    stage_start = time.time()
    sequences, periods, total_states, max_period = lfsr_sequence_mapper_parallel(
        C, V, gf_order,
        algorithm=algorithm,
        period_only=period_only,
        num_workers=num_workers,
        no_progress=True
    )
    stage_end = time.time()
    profile['stages']['merging'] = stage_end - stage_start
    
    # Close pool
    pool.close()
    pool.join()
    
    profile['end_time'] = time.time()
    profile['total_time'] = profile['end_time'] - profile['start_time']
    
    signatures = extract_cycle_signatures(sequences)
    
    # Check for redundancy
    redundant_cycles = []
    for min_state, info in signatures.items():
        if len(info['worker_ids']) > 1 or info['count'] > 1:
            redundant_cycles.append({
                'min_state': min_state,
                'period': info['period'],
                'workers': info['worker_ids'],
                'count': info['count']
            })
    
    profile['results'] = {
        'sequences': sequences,
        'signatures': signatures,
        'total_states': total_states,
        'max_period': max_period,
        'periods': periods,
        'unique_cycles': len(signatures),
        'total_sequences': sum(len(seq_list) for seq_list in sequences.values()),
        'redundant_cycles': redundant_cycles,
        'redundant_count': len(redundant_cycles)
    }
    
    print(f"    Time: {profile['stages']['merging']:.4f}s")
    print(f"\nParallel Profile Summary:")
    print(f"  Total time: {profile['total_time']:.4f}s")
    print(f"  Partitioning: {profile['stages']['partitioning']:.4f}s ({100*profile['stages']['partitioning']/profile['total_time']:.1f}%)")
    print(f"  Prepare data: {profile['stages']['prepare_data']:.4f}s ({100*profile['stages']['prepare_data']/profile['total_time']:.1f}%)")
    print(f"  Pool creation: {profile['stages']['pool_creation']:.4f}s ({100*profile['stages']['pool_creation']/profile['total_time']:.1f}%)")
    print(f"  Submit tasks: {profile['stages']['submit_tasks']:.4f}s ({100*profile['stages']['submit_tasks']/profile['total_time']:.1f}%)")
    print(f"  Worker execution: {profile['stages']['worker_execution']:.4f}s ({100*profile['stages']['worker_execution']/profile['total_time']:.1f}%)")
    print(f"  Merging: {profile['stages']['merging']:.4f}s ({100*profile['stages']['merging']/profile['total_time']:.1f}%)")
    print(f"  Redundant cycles: {len(redundant_cycles)}")
    
    return profile


def compare_profiles(seq_profile: Dict, par_profile: Dict) -> Dict[str, Any]:
    """Compare sequential and parallel profiles."""
    comparison = {
        'correctness': {},
        'redundancy': {},
        'performance': {},
        'breakdown': {}
    }
    
    # Correctness
    seq_sigs = seq_profile['results']['signatures']
    par_sigs = par_profile['results']['signatures']
    
    seq_cycles = set(seq_sigs.keys())
    par_cycles = set(par_sigs.keys())
    
    missing = seq_cycles - par_cycles
    extra = par_cycles - seq_cycles
    
    comparison['correctness'] = {
        'cycles_match': len(missing) == 0 and len(extra) == 0,
        'missing_cycles': len(missing),
        'extra_cycles': len(extra),
        'period_sum_match': (
            sum(s['period'] for s in seq_sigs.values()) == 
            sum(p['period'] for p in par_sigs.values())
        )
    }
    
    # Redundancy
    redundant = par_profile['results'].get('redundant_cycles', [])
    comparison['redundancy'] = {
        'redundant_count': len(redundant),
        'no_redundancy': len(redundant) == 0,
        'redundant_cycles': redundant[:10]
    }
    
    # Performance
    seq_time = seq_profile['total_time']
    par_time = par_profile['total_time']
    speedup = seq_time / par_time if par_time > 0 else 0
    efficiency = speedup / par_profile['num_workers'] if par_profile['num_workers'] > 0 else 0
    
    comparison['performance'] = {
        'sequential_time': seq_time,
        'parallel_time': par_time,
        'speedup': speedup,
        'efficiency': efficiency,
        'num_workers': par_profile['num_workers']
    }
    
    # Breakdown
    comparison['breakdown'] = {
        'partitioning': {
            'time': par_profile['stages']['partitioning'],
            'percentage': 100 * par_profile['stages']['partitioning'] / par_time
        },
        'prepare_data': {
            'time': par_profile['stages']['prepare_data'],
            'percentage': 100 * par_profile['stages']['prepare_data'] / par_time
        },
        'pool_creation': {
            'time': par_profile['stages']['pool_creation'],
            'percentage': 100 * par_profile['stages']['pool_creation'] / par_time
        },
        'submit_tasks': {
            'time': par_profile['stages']['submit_tasks'],
            'percentage': 100 * par_profile['stages']['submit_tasks'] / par_time
        },
        'worker_execution': {
            'time': par_profile['stages']['worker_execution'],
            'percentage': 100 * par_profile['stages']['worker_execution'] / par_time
        },
        'merging': {
            'time': par_profile['stages']['merging'],
            'percentage': 100 * par_profile['stages']['merging'] / par_time
        }
    }
    
    return comparison


def generate_detailed_report(all_profiles: Dict[str, Any]):
    """Generate comprehensive profiling report."""
    report = []
    report.append("# 12-Bit LFSR Parallel Execution Profiling Report\n")
    report.append(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append(f"**LFSR**: 12-bit, primitive polynomial x^12 + x^6 + x^4 + x + 1\n")
    report.append(f"**Total States**: {all_profiles['sequential']['results']['total_states']}\n")
    report.append(f"**Algorithm**: {all_profiles.get('algorithm', 'enumeration')}\n")
    report.append(f"**Period-Only Mode**: {all_profiles.get('period_only', True)}\n\n")
    
    # Executive Summary
    report.append("## Executive Summary\n\n")
    report.append("| Workers | Time (s) | Speedup | Efficiency | Correct | No Redundancy |\n")
    report.append("|---------|----------|--------|-----------|---------|---------------|\n")
    
    seq_time = all_profiles['sequential']['total_time']
    report.append(f"| Sequential | {seq_time:.4f} | 1.00x | - | ✓ | ✓ |\n")
    
    for num_workers in sorted([k for k in all_profiles.keys() if isinstance(k, int)]):
        par_profile = all_profiles[num_workers]
        comp = all_profiles['comparisons'][num_workers]
        
        time_str = f"{par_profile['total_time']:.4f}"
        speedup_str = f"{comp['performance']['speedup']:.2f}x"
        efficiency_str = f"{comp['performance']['efficiency']:.1%}"
        correct_str = "✓" if comp['correctness']['cycles_match'] and comp['correctness']['period_sum_match'] else "✗"
        no_redundancy_str = "✓" if comp['redundancy']['no_redundancy'] else f"✗ ({comp['redundancy']['redundant_count']})"
        
        report.append(f"| {num_workers} | {time_str} | {speedup_str} | {efficiency_str} | {correct_str} | {no_redundancy_str} |\n")
    
    # Detailed Performance Breakdown
    report.append("\n## Performance Breakdown\n\n")
    
    for num_workers in sorted([k for k in all_profiles.keys() if isinstance(k, int)]):
        par_profile = all_profiles[num_workers]
        comp = all_profiles['comparisons'][num_workers]
        
        report.append(f"### {num_workers} Workers\n\n")
        report.append(f"**Total Time**: {par_profile['total_time']:.4f}s\n")
        report.append(f"**Speedup**: {comp['performance']['speedup']:.2f}x\n")
        report.append(f"**Efficiency**: {comp['performance']['efficiency']:.1%}\n\n")
        
        report.append("**Time Breakdown**:\n\n")
        report.append("| Stage | Time (s) | Percentage |\n")
        report.append("|-------|----------|------------|\n")
        
        for stage_name, stage_data in comp['breakdown'].items():
            report.append(f"| {stage_name.replace('_', ' ').title()} | {stage_data['time']:.4f} | {stage_data['percentage']:.1f}% |\n")
        
        # Worker statistics
        if 'worker_results' in par_profile:
            report.append("\n**Per-Worker Statistics**:\n\n")
            report.append("| Worker | States Processed | Sequences Found | Max Period | Errors |\n")
            report.append("|--------|------------------|-----------------|------------|--------|\n")
            
            for worker_id in sorted(par_profile['worker_results'].keys()):
                wr = par_profile['worker_results'][worker_id]
                report.append(f"| {worker_id} | {wr['processed_count']} | {wr['sequences_count']} | {wr['max_period']} | {wr['errors']} |\n")
        
        report.append("\n")
    
    # Correctness Analysis
    report.append("## Correctness Analysis\n\n")
    
    for num_workers in sorted([k for k in all_profiles.keys() if isinstance(k, int)]):
        comp = all_profiles['comparisons'][num_workers]
        report.append(f"### {num_workers} Workers\n\n")
        
        if comp['correctness']['cycles_match'] and comp['correctness']['period_sum_match']:
            report.append("✓ **PASS**: All cycles match sequential execution\n\n")
        else:
            report.append("✗ **FAIL**: Mismatch detected\n\n")
            if comp['correctness']['missing_cycles'] > 0:
                report.append(f"- Missing cycles: {comp['correctness']['missing_cycles']}\n")
            if comp['correctness']['extra_cycles'] > 0:
                report.append(f"- Extra cycles: {comp['correctness']['extra_cycles']}\n")
            report.append("\n")
    
    # Redundancy Analysis
    report.append("## Redundancy Analysis\n\n")
    
    for num_workers in sorted([k for k in all_profiles.keys() if isinstance(k, int)]):
        comp = all_profiles['comparisons'][num_workers]
        report.append(f"### {num_workers} Workers\n\n")
        
        if comp['redundancy']['no_redundancy']:
            report.append("✓ **No redundancy detected**: Each cycle processed by exactly one worker\n\n")
        else:
            report.append(f"✗ **Redundancy detected**: {comp['redundancy']['redundant_count']} cycles found by multiple workers\n\n")
            if comp['redundancy']['redundant_cycles']:
                report.append("Examples:\n\n")
                for cycle in comp['redundancy']['redundant_cycles'][:5]:
                    report.append(f"- Period {cycle['period']}, Workers {cycle['workers']}, Count {cycle['count']}\n")
                report.append("\n")
    
    # Recommendations
    report.append("## Recommendations\n\n")
    
    best_workers = max(
        [k for k in all_profiles.keys() if isinstance(k, int)],
        key=lambda w: all_profiles['comparisons'][w]['performance']['speedup']
    )
    best_speedup = all_profiles['comparisons'][best_workers]['performance']['speedup']
    
    report.append(f"- **Optimal worker count**: {best_workers} workers (speedup: {best_speedup:.2f}x)\n")
    
    # Check for issues
    has_redundancy = any(
        not all_profiles['comparisons'][w]['redundancy']['no_redundancy']
        for w in all_profiles['comparisons'].keys()
    )
    
    if has_redundancy:
        report.append("- ⚠️  **Redundancy detected**: Some cycles processed by multiple workers\n")
    
    all_correct = all(
        all_profiles['comparisons'][w]['correctness']['cycles_match'] and
        all_profiles['comparisons'][w]['correctness']['period_sum_match']
        for w in all_profiles['comparisons'].keys()
    )
    
    if not all_correct:
        report.append("- ⚠️  **Correctness issues**: Results don't match sequential execution\n")
    
    if not has_redundancy and all_correct:
        report.append("- ✓ **All tests passed**: Correctness verified, no redundancy detected\n")
    
    return ''.join(report)


def main():
    """Main profiling function."""
    import sys
    import traceback
    
    try:
        sys.stdout.flush()
        sys.stderr.flush()
        
        print("="*80, flush=True)
        print("12-Bit LFSR Parallel Execution Profiling", flush=True)
        print("="*80, flush=True)
    
        # Create 12-bit LFSR
        print("\nCreating 12-bit LFSR...", flush=True)
        C, V, gf_order, coeffs_vector, degree = create_12bit_lfsr()
        print(f"  Degree: {degree}", flush=True)
        print(f"  Field: GF({gf_order})", flush=True)
        print(f"  Coefficients: {coeffs_vector}", flush=True)
        print(f"  Total states: {2**degree}", flush=True)
        sys.stdout.flush()
        
        algorithm = 'enumeration'
        period_only = True
        
        all_profiles = {
            'algorithm': algorithm,
            'period_only': period_only,
            'comparisons': {}
        }
        
        # Profile sequential
        seq_profile = profile_sequential(C, V, gf_order, algorithm=algorithm, period_only=period_only)
        all_profiles['sequential'] = seq_profile
        
        # Profile parallel with different worker counts
        worker_counts = [1, 2, 4, 8]
        
        for num_workers in worker_counts:
            par_profile = profile_parallel(C, V, gf_order, num_workers, algorithm=algorithm, period_only=period_only)
            all_profiles[num_workers] = par_profile
            
            # Compare with sequential
            comparison = compare_profiles(seq_profile, par_profile)
            all_profiles['comparisons'][num_workers] = comparison
            
            # Print comparison
            print(f"\n{'='*80}")
            print(f"COMPARISON: Sequential vs {num_workers} Workers")
            print(f"{'='*80}")
            print(f"Correctness: ", end="")
            if comparison['correctness']['cycles_match'] and comparison['correctness']['period_sum_match']:
                print("✓ PASS")
            else:
                print("✗ FAIL")
                print(f"  Missing cycles: {comparison['correctness']['missing_cycles']}")
                print(f"  Extra cycles: {comparison['correctness']['extra_cycles']}")
            
            print(f"Redundancy: ", end="")
            if comparison['redundancy']['no_redundancy']:
                print("✓ No redundancy")
            else:
                print(f"✗ {comparison['redundancy']['redundant_count']} redundant cycles")
            
            print(f"Performance: {comparison['performance']['speedup']:.2f}x speedup, {comparison['performance']['efficiency']:.1%} efficiency")
        
        # Generate report
        report = generate_detailed_report(all_profiles)
        
        report_file = 'scripts/12bit_parallel_profiling_report.md'
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\n{'='*80}")
        print(f"Detailed report saved to: {report_file}")
        print(f"{'='*80}\n")
        
        # Print final summary
        print("FINAL SUMMARY:")
        print(f"  Sequential time: {seq_profile['total_time']:.4f}s")
        for num_workers in worker_counts:
            par_profile = all_profiles[num_workers]
            comp = all_profiles['comparisons'][num_workers]
            print(f"  {num_workers} workers: {par_profile['total_time']:.4f}s ({comp['performance']['speedup']:.2f}x, "
                  f"correct={'✓' if comp['correctness']['cycles_match'] else '✗'}, "
                  f"redundancy={'✓' if comp['redundancy']['no_redundancy'] else '✗'})")
    
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
