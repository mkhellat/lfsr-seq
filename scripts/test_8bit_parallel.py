#!/usr/bin/env python3
"""
Test script for 8-bit LFSR parallel execution verification.

Tests:
1. Correctness: Results match sequential
2. Redundancy: No cycles processed by multiple workers
3. Performance: Compare 1, 2, 4, 8 workers vs sequential
"""

import os
import sys
import time
import json
from collections import defaultdict
from typing import Dict, List, Any, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sage.all import GF, VectorSpace, vector
from lfsr.analysis import lfsr_sequence_mapper, lfsr_sequence_mapper_parallel
from lfsr.core import build_state_update_matrix


def create_8bit_lfsr():
    """Create an 8-bit LFSR with a primitive polynomial."""
    # Primitive polynomial for GF(2)^8: x^8 + x^4 + x^3 + x^2 + 1
    # Coefficients: [c0, c1, ..., c7] where c_i is coefficient of x^i
    # For x^8 + x^4 + x^3 + x^2 + 1, we have:
    # c0=1, c1=0, c2=1, c3=1, c4=1, c5=0, c6=0, c7=0, c8=1
    # But we store as [c0, c1, ..., c7] for degree 8
    coeffs = [1, 0, 1, 1, 1, 0, 0, 0, 1]  # Including c8 for degree 8
    # Actually, for degree 8, we need 8 coefficients c0..c7
    # The polynomial is x^8 + x^4 + x^3 + x^2 + 1
    # So: c0=1, c1=0, c2=1, c3=1, c4=1, c5=0, c6=0, c7=0
    # And the leading coefficient (c8) is implicit
    coeffs_vector = [1, 0, 1, 1, 1, 0, 0, 0]  # c0 to c7
    
    gf_order = 2
    degree = 8
    
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
            'worker_ids': List[int]  # Which workers found this cycle
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
            
            # Get min_state (first element in period-only mode, or min of all)
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
                    'worker_ids': []
                }
            
            signatures[min_state_tuple]['start_states'].append(tuple(start_state) if start_state else None)
            if worker_id not in signatures[min_state_tuple]['worker_ids']:
                signatures[min_state_tuple]['worker_ids'].append(worker_id)
    
    return signatures


def test_sequential(C, V, gf_order, algorithm='enumeration', period_only=True):
    """Run sequential execution and collect results."""
    print("\n" + "="*80)
    print("SEQUENTIAL EXECUTION")
    print("="*80)
    
    start_time = time.time()
    
    sequences, periods, total_states, max_period = lfsr_sequence_mapper(
        C, V, gf_order,
        algorithm=algorithm,
        period_only=period_only,
        no_progress=True
    )
    
    elapsed = time.time() - start_time
    
    # Convert sequences to dict format for comparison
    seq_dict = {0: []}  # Single "worker" with id 0
    for period, seq_list in sequences.items():
        for seq in seq_list:
            seq_dict[0].append({
                'states': seq.get('states', []),
                'period': period,
                'start_state': tuple(seq.get('start_state', ()))
            })
    
    signatures = extract_cycle_signatures(seq_dict)
    
    print(f"\nSequential Results:")
    print(f"  Time: {elapsed:.4f}s")
    print(f"  Total states: {total_states}")
    print(f"  Unique cycles: {len(signatures)}")
    print(f"  Max period: {max_period}")
    print(f"  Total period sum: {sum(p for p in periods.values() for _ in periods[p])}")
    
    return {
        'time': elapsed,
        'sequences': seq_dict,
        'signatures': signatures,
        'total_states': total_states,
        'max_period': max_period,
        'periods': periods
    }


def test_parallel(C, V, gf_order, num_workers, algorithm='enumeration', period_only=True):
    """Run parallel execution and collect detailed results."""
    print("\n" + "="*80)
    print(f"PARALLEL EXECUTION ({num_workers} workers)")
    print("="*80)
    
    # Enable debug logging
    os.environ['DEBUG_PARALLEL'] = '1'
    
    start_time = time.time()
    
    sequences, periods, total_states, max_period = lfsr_sequence_mapper_parallel(
        C, V, gf_order,
        algorithm=algorithm,
        period_only=period_only,
        num_workers=num_workers,
        no_progress=True
    )
    
    elapsed = time.time() - start_time
    
    # Disable debug logging
    os.environ['DEBUG_PARALLEL'] = '0'
    
    signatures = extract_cycle_signatures(sequences)
    
    # Check for redundancy
    redundant_cycles = []
    for min_state, info in signatures.items():
        if len(info['worker_ids']) > 1:
            redundant_cycles.append({
                'min_state': min_state,
                'period': info['period'],
                'workers': info['worker_ids'],
                'start_states': info['start_states']
            })
    
    print(f"\nParallel Results ({num_workers} workers):")
    print(f"  Time: {elapsed:.4f}s")
    print(f"  Total states: {total_states}")
    print(f"  Unique cycles: {len(signatures)}")
    print(f"  Max period: {max_period}")
    print(f"  Redundant cycles (found by multiple workers): {len(redundant_cycles)}")
    
    if redundant_cycles:
        print(f"\n  ⚠️  REDUNDANCY DETECTED:")
        for cycle in redundant_cycles[:5]:  # Show first 5
            print(f"    Cycle (min_state={cycle['min_state'][:8]}...): period={cycle['period']}, workers={cycle['workers']}")
        if len(redundant_cycles) > 5:
            print(f"    ... and {len(redundant_cycles) - 5} more")
    
    return {
        'time': elapsed,
        'sequences': sequences,
        'signatures': signatures,
        'total_states': total_states,
        'max_period': max_period,
        'periods': periods,
        'redundant_cycles': redundant_cycles,
        'num_workers': num_workers
    }


def compare_results(seq_result: Dict, par_result: Dict) -> Dict[str, Any]:
    """Compare sequential and parallel results."""
    comparison = {
        'correctness': {},
        'redundancy': {},
        'performance': {}
    }
    
    # Correctness: Compare cycle signatures
    seq_sigs = seq_result['signatures']
    par_sigs = par_result['signatures']
    
    seq_cycles = set(seq_sigs.keys())
    par_cycles = set(par_sigs.keys())
    
    missing_in_parallel = seq_cycles - par_cycles
    extra_in_parallel = par_cycles - seq_cycles
    
    comparison['correctness'] = {
        'sequential_cycles': len(seq_cycles),
        'parallel_cycles': len(par_cycles),
        'missing_in_parallel': len(missing_in_parallel),
        'extra_in_parallel': len(extra_in_parallel),
        'cycles_match': len(missing_in_parallel) == 0 and len(extra_in_parallel) == 0,
        'period_sum_match': (
            sum(s['period'] for s in seq_sigs.values()) == 
            sum(p['period'] for p in par_sigs.values())
        )
    }
    
    # Redundancy
    redundant = par_result.get('redundant_cycles', [])
    comparison['redundancy'] = {
        'redundant_cycles_count': len(redundant),
        'no_redundancy': len(redundant) == 0,
        'redundant_cycles': redundant[:10]  # First 10
    }
    
    # Performance
    seq_time = seq_result['time']
    par_time = par_result['time']
    speedup = seq_time / par_time if par_time > 0 else 0
    efficiency = speedup / par_result['num_workers'] if par_result['num_workers'] > 0 else 0
    
    comparison['performance'] = {
        'sequential_time': seq_time,
        'parallel_time': par_time,
        'speedup': speedup,
        'efficiency': efficiency,
        'num_workers': par_result['num_workers']
    }
    
    return comparison


def generate_report(all_results: Dict[str, Any]):
    """Generate a comprehensive test report."""
    report = []
    report.append("# 8-Bit LFSR Parallel Execution Test Report\n")
    report.append(f"**Test Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append(f"**LFSR**: 8-bit, primitive polynomial x^8 + x^4 + x^3 + x^2 + 1\n")
    report.append(f"**Total States**: {all_results['sequential']['total_states']}\n")
    report.append(f"**Algorithm**: {all_results.get('algorithm', 'enumeration')}\n")
    report.append(f"**Period-Only Mode**: {all_results.get('period_only', True)}\n\n")
    
    report.append("## Summary\n\n")
    
    # Performance summary table
    report.append("### Performance Summary\n\n")
    report.append("| Workers | Time (s) | Speedup | Efficiency | Correct | No Redundancy |\n")
    report.append("|---------|----------|---------|------------|----------|---------------|\n")
    
    seq_time = all_results['sequential']['time']
    report.append(f"| Sequential | {seq_time:.4f} | 1.00x | - | ✓ | ✓ |\n")
    
    for num_workers in sorted([k for k in all_results.keys() if isinstance(k, int)]):
        par_result = all_results[num_workers]
        comp = all_results['comparisons'][num_workers]
        
        time_str = f"{par_result['time']:.4f}"
        speedup_str = f"{comp['performance']['speedup']:.2f}x"
        efficiency_str = f"{comp['performance']['efficiency']:.1%}"
        correct_str = "✓" if comp['correctness']['cycles_match'] and comp['correctness']['period_sum_match'] else "✗"
        no_redundancy_str = "✓" if comp['redundancy']['no_redundancy'] else f"✗ ({comp['redundancy']['redundant_cycles_count']})"
        
        report.append(f"| {num_workers} | {time_str} | {speedup_str} | {efficiency_str} | {correct_str} | {no_redundancy_str} |\n")
    
    # Detailed results
    report.append("\n## Detailed Results\n\n")
    
    for num_workers in sorted([k for k in all_results.keys() if isinstance(k, int)]):
        par_result = all_results[num_workers]
        comp = all_results['comparisons'][num_workers]
        
        report.append(f"### {num_workers} Workers\n\n")
        report.append(f"- **Time**: {par_result['time']:.4f}s\n")
        report.append(f"- **Speedup**: {comp['performance']['speedup']:.2f}x\n")
        report.append(f"- **Efficiency**: {comp['performance']['efficiency']:.1%}\n")
        report.append(f"- **Correctness**: ")
        
        if comp['correctness']['cycles_match'] and comp['correctness']['period_sum_match']:
            report.append("✓ PASS\n")
        else:
            report.append("✗ FAIL\n")
            if comp['correctness']['missing_in_parallel'] > 0:
                report.append(f"  - Missing cycles: {comp['correctness']['missing_in_parallel']}\n")
            if comp['correctness']['extra_in_parallel'] > 0:
                report.append(f"  - Extra cycles: {comp['correctness']['extra_in_parallel']}\n")
        
        report.append(f"- **Redundancy**: ")
        if comp['redundancy']['no_redundancy']:
            report.append("✓ No redundancy detected\n")
        else:
            report.append(f"✗ {comp['redundancy']['redundant_cycles_count']} cycles found by multiple workers\n")
            if comp['redundancy']['redundant_cycles']:
                report.append("  - Examples:\n")
                for cycle in comp['redundancy']['redundant_cycles'][:5]:
                    report.append(f"    - Period {cycle['period']}, Workers {cycle['workers']}\n")
        
        report.append("\n")
    
    # Recommendations
    report.append("## Recommendations\n\n")
    
    best_workers = max(
        [k for k in all_results.keys() if isinstance(k, int)],
        key=lambda w: all_results['comparisons'][w]['performance']['speedup']
    )
    best_speedup = all_results['comparisons'][best_workers]['performance']['speedup']
    
    report.append(f"- **Best configuration**: {best_workers} workers (speedup: {best_speedup:.2f}x)\n")
    
    # Check for issues
    has_redundancy = any(
        not all_results['comparisons'][w]['redundancy']['no_redundancy']
        for w in all_results['comparisons'].keys()
    )
    
    if has_redundancy:
        report.append("- ⚠️  **Redundancy detected**: Some cycles are processed by multiple workers\n")
    
    all_correct = all(
        all_results['comparisons'][w]['correctness']['cycles_match'] and
        all_results['comparisons'][w]['correctness']['period_sum_match']
        for w in all_results['comparisons'].keys()
    )
    
    if not all_correct:
        report.append("- ⚠️  **Correctness issues**: Results don't match sequential execution\n")
    
    if not has_redundancy and all_correct:
        report.append("- ✓ **All tests passed**: Correctness verified, no redundancy detected\n")
    
    return ''.join(report)


def main():
    """Main test function."""
    print("="*80)
    print("8-Bit LFSR Parallel Execution Verification Test")
    print("="*80)
    
    # Create 8-bit LFSR
    print("\nCreating 8-bit LFSR...")
    C, V, gf_order, coeffs_vector, degree = create_8bit_lfsr()
    print(f"  Degree: {degree}")
    print(f"  Field: GF({gf_order})")
    print(f"  Coefficients: {coeffs_vector}")
    print(f"  Total states: {2**degree}")
    
    algorithm = 'enumeration'
    period_only = True
    
    all_results = {
        'algorithm': algorithm,
        'period_only': period_only,
        'comparisons': {}
    }
    
    # Run sequential
    seq_result = test_sequential(C, V, gf_order, algorithm=algorithm, period_only=period_only)
    all_results['sequential'] = seq_result
    
    # Run parallel with different worker counts
    worker_counts = [1, 2, 4, 8]
    
    for num_workers in worker_counts:
        par_result = test_parallel(C, V, gf_order, num_workers, algorithm=algorithm, period_only=period_only)
        all_results[num_workers] = par_result
        
        # Compare with sequential
        comparison = compare_results(seq_result, par_result)
        all_results['comparisons'][num_workers] = comparison
        
        # Print comparison
        print(f"\n{'='*80}")
        print(f"COMPARISON: Sequential vs {num_workers} Workers")
        print(f"{'='*80}")
        print(f"Correctness: ", end="")
        if comparison['correctness']['cycles_match'] and comparison['correctness']['period_sum_match']:
            print("✓ PASS")
        else:
            print("✗ FAIL")
            print(f"  Missing cycles: {comparison['correctness']['missing_in_parallel']}")
            print(f"  Extra cycles: {comparison['correctness']['extra_in_parallel']}")
        
        print(f"Redundancy: ", end="")
        if comparison['redundancy']['no_redundancy']:
            print("✓ No redundancy")
        else:
            print(f"✗ {comparison['redundancy']['redundant_cycles_count']} redundant cycles")
        
        print(f"Performance: {comparison['performance']['speedup']:.2f}x speedup, {comparison['performance']['efficiency']:.1%} efficiency")
    
    # Generate report
    report = generate_report(all_results)
    
    report_file = 'scripts/8bit_parallel_test_report.md'
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\n{'='*80}")
    print(f"Report saved to: {report_file}")
    print(f"{'='*80}\n")
    
    # Print summary
    print("FINAL SUMMARY:")
    print(f"  Sequential time: {seq_result['time']:.4f}s")
    for num_workers in worker_counts:
        par_result = all_results[num_workers]
        comp = all_results['comparisons'][num_workers]
        print(f"  {num_workers} workers: {par_result['time']:.4f}s ({comp['performance']['speedup']:.2f}x, "
              f"correct={'✓' if comp['correctness']['cycles_match'] else '✗'}, "
              f"redundancy={'✓' if comp['redundancy']['no_redundancy'] else '✗'})")


if __name__ == '__main__':
    main()
