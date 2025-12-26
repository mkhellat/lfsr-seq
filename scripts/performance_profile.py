#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance profiling tool for LFSR cycle detection algorithms.

This script performs detailed timing and memory analysis of Floyd's algorithm
vs enumeration method to verify performance claims and identify bottlenecks.
"""

import argparse
import cProfile
import io
import pstats
import sys
import time
import tracemalloc
from typing import Any, Dict, List, Tuple

# Try to import sage (same mechanism as CLI)
_sage_available = False
try:
    from sage.all import *
    _sage_available = True
except ImportError:
    # Try to find SageMath via 'sage' command
    import subprocess
    import os
    try:
        result = subprocess.run(
            ["sage", "-c", "import sys; print('\\n'.join(sys.path))"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            sage_paths = result.stdout.strip().split("\n")
            for path in sage_paths:
                if path and path not in sys.path and os.path.isdir(path):
                    sys.path.insert(0, path)
            from sage.all import *
            _sage_available = True
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError, ImportError):
        pass

if not _sage_available:
    print("ERROR: SageMath is required", file=sys.stderr)
    sys.exit(1)

from lfsr.analysis import (
    _find_sequence_cycle_enumeration,
    _find_sequence_cycle_floyd,
)
from lfsr.core import build_state_update_matrix
from lfsr.io import read_and_validate_csv


def time_algorithm(
    algorithm_func,
    start_state: Any,
    state_update_matrix: Any,
    visited_set: set,
    algorithm_name: str,
) -> Tuple[float, int, Dict[str, Any]]:
    """
    Time an algorithm and collect detailed metrics.
    
    Returns:
        (total_time, period, metrics_dict)
    """
    # Clear visited set for fair comparison
    visited_set.clear()
    
    # Start memory tracing
    tracemalloc.start()
    
    # Time the algorithm
    start_time = time.perf_counter()
    seq_lst, period = algorithm_func(start_state, state_update_matrix, visited_set)
    end_time = time.perf_counter()
    
    # Get memory stats
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    total_time = end_time - start_time
    
    metrics = {
        "total_time": total_time,
        "period": period,
        "sequence_length": len(seq_lst),
        "peak_memory_bytes": peak,
        "current_memory_bytes": current,
        "visited_states": len(visited_set),
    }
    
    return total_time, period, metrics


def profile_floyd_phases(
    start_state: Any,
    state_update_matrix: Any,
    visited_set: set,
) -> Dict[str, Any]:
    """
    Profile Floyd's algorithm by breaking it into phases.
    
    Returns detailed timing for Phase 1, Phase 2, and enumeration phase.
    """
    visited_set.clear()
    tracemalloc.start()
    
    metrics = {}
    
    # Phase 1: Find meeting point
    tortoise = start_state
    hare = start_state * state_update_matrix
    
    if tortoise == hare:
        metrics["phase1_time"] = 0.0
        metrics["phase1_steps"] = 0
        metrics["period"] = 1
        metrics["total_time"] = 0.0
        tracemalloc.stop()
        return metrics
    
    phase1_start = time.perf_counter()
    steps = 0
    max_steps = 10000000
    
    while tortoise != hare and steps < max_steps:
        tortoise = tortoise * state_update_matrix
        hare = (hare * state_update_matrix) * state_update_matrix
        steps += 1
    
    phase1_end = time.perf_counter()
    metrics["phase1_time"] = phase1_end - phase1_start
    metrics["phase1_steps"] = steps
    
    if steps >= max_steps:
        tracemalloc.stop()
        return metrics
    
    # Phase 2: Find period
    meeting_point = tortoise
    lambda_period = 1
    hare = meeting_point * state_update_matrix
    
    phase2_start = time.perf_counter()
    
    if meeting_point == hare:
        lambda_period = 1
        phase2_steps = 0
    else:
        phase2_steps = 1
        while meeting_point != hare and phase2_steps < max_steps:
            hare = hare * state_update_matrix
            phase2_steps += 1
        lambda_period = phase2_steps
    
    phase2_end = time.perf_counter()
    metrics["phase2_time"] = phase2_end - phase2_start
    metrics["phase2_steps"] = phase2_steps
    metrics["lambda_period"] = lambda_period
    
    # Enumeration phase
    enum_start = time.perf_counter()
    seq_lst = [start_state]
    start_state_tuple = tuple(start_state)
    visited_set.add(start_state_tuple)
    next_state = start_state * state_update_matrix
    seq_period = 1
    
    enum_steps = 0
    while next_state != start_state and seq_period < lambda_period:
        seq_lst.append(next_state)
        next_state_tuple = tuple(next_state)
        visited_set.add(next_state_tuple)
        seq_period += 1
        next_state = next_state * state_update_matrix
        enum_steps += 1
    
    enum_end = time.perf_counter()
    metrics["enumeration_time"] = enum_end - enum_start
    metrics["enumeration_steps"] = enum_steps
    metrics["sequence_length"] = len(seq_lst)
    
    metrics["total_time"] = (
        metrics["phase1_time"] + metrics["phase2_time"] + metrics["enumeration_time"]
    )
    metrics["period"] = lambda_period
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    metrics["peak_memory_bytes"] = peak
    metrics["current_memory_bytes"] = current
    metrics["visited_states"] = len(visited_set)
    
    return metrics


def profile_enumeration(
    start_state: Any,
    state_update_matrix: Any,
    visited_set: set,
) -> Dict[str, Any]:
    """
    Profile enumeration algorithm with detailed metrics.
    """
    visited_set.clear()
    tracemalloc.start()
    
    start_time = time.perf_counter()
    
    seq_lst = [start_state]
    start_state_tuple = tuple(start_state)
    visited_set.add(start_state_tuple)
    next_state = start_state * state_update_matrix
    seq_period = 1
    steps = 0
    
    while next_state != start_state:
        seq_lst.append(next_state)
        next_state_tuple = tuple(next_state)
        visited_set.add(next_state_tuple)
        seq_period += 1
        next_state = next_state * state_update_matrix
        steps += 1
    
    end_time = time.perf_counter()
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    metrics = {
        "total_time": end_time - start_time,
        "period": seq_period,
        "sequence_length": len(seq_lst),
        "steps": steps,
        "peak_memory_bytes": peak,
        "current_memory_bytes": current,
        "visited_states": len(visited_set),
    }
    
    return metrics


def compare_algorithms(
    input_file: str,
    gf_order_str: str,
    num_states: int = 10,
    output_file=None,
) -> None:
    """
    Compare Floyd's algorithm vs enumeration on real data.
    """
    from lfsr.field import validate_gf_order, validate_coefficient_vector
    
    gf_order = validate_gf_order(gf_order_str)
    coeffs_list = read_and_validate_csv(input_file, gf_order)
    
    if not coeffs_list:
        print("ERROR: No coefficient vectors found", file=sys.stderr)
        return
    
    # Use first coefficient vector
    coeffs_vector_str = coeffs_list[0]
    validate_coefficient_vector(coeffs_vector_str, gf_order, 1)
    coeffs_vector = [int(c) for c in coeffs_vector_str]
    
    # Build state update matrix
    C, CS = build_state_update_matrix(coeffs_vector, gf_order)
    V = VectorSpace(GF(gf_order), len(coeffs_vector))
    
    print("=" * 80)
    print("PERFORMANCE COMPARISON: Floyd vs Enumeration")
    print("=" * 80)
    print(f"Input file: {input_file}")
    print(f"GF order: {gf_order}")
    print(f"Coefficients: {coeffs_vector}")
    print(f"State space size: {gf_order ** len(coeffs_vector)}")
    print(f"Testing on first {num_states} non-zero states")
    print("=" * 80)
    print()
    
    # Collect states to test
    test_states = []
    for state in V:
        if state != V.zero():
            test_states.append(state)
            if len(test_states) >= num_states:
                break
    
    floyd_times = []
    enum_times = []
    floyd_metrics_list = []
    enum_metrics_list = []
    
    for i, state in enumerate(test_states, 1):
        print(f"\nState {i}/{len(test_states)}: {state}")
        print("-" * 80)
        
        # Test Floyd
        visited_set_floyd = set()
        floyd_metrics = profile_floyd_phases(state, C, visited_set_floyd)
        floyd_times.append(floyd_metrics["total_time"])
        floyd_metrics_list.append(floyd_metrics)
        
        # Test Enumeration
        visited_set_enum = set()
        enum_metrics = profile_enumeration(state, C, visited_set_enum)
        enum_times.append(enum_metrics["total_time"])
        enum_metrics_list.append(enum_metrics)
        
        # Verify results match
        if floyd_metrics["period"] != enum_metrics["period"]:
            print(f"WARNING: Period mismatch! Floyd={floyd_metrics['period']}, Enum={enum_metrics['period']}")
        
        # Print comparison
        print(f"Period: {enum_metrics['period']}")
        print(f"Floyd total time: {floyd_metrics['total_time']*1000:.3f} ms")
        print(f"  Phase 1: {floyd_metrics.get('phase1_time', 0)*1000:.3f} ms ({floyd_metrics.get('phase1_steps', 0)} steps)")
        print(f"  Phase 2: {floyd_metrics.get('phase2_time', 0)*1000:.3f} ms ({floyd_metrics.get('phase2_steps', 0)} steps)")
        print(f"  Enumeration: {floyd_metrics.get('enumeration_time', 0)*1000:.3f} ms ({floyd_metrics.get('enumeration_steps', 0)} steps)")
        print(f"Enumeration total time: {enum_metrics['total_time']*1000:.3f} ms ({enum_metrics['steps']} steps)")
        print(f"Speedup: {enum_metrics['total_time']/floyd_metrics['total_time']:.2f}x {'(enum faster)' if enum_metrics['total_time'] < floyd_metrics['total_time'] else '(floyd faster)'}")
        print(f"Floyd peak memory: {floyd_metrics['peak_memory_bytes']/1024:.2f} KB")
        print(f"Enum peak memory: {enum_metrics['peak_memory_bytes']/1024:.2f} KB")
        print(f"Memory ratio: {floyd_metrics['peak_memory_bytes']/enum_metrics['peak_memory_bytes']:.2f}x")
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Average Floyd time: {sum(floyd_times)/len(floyd_times)*1000:.3f} ms")
    print(f"Average Enumeration time: {sum(enum_times)/len(enum_times)*1000:.3f} ms")
    print(f"Average speedup: {sum(enum_times)/sum(floyd_times):.2f}x")
    print()
    
    # Analyze space complexity
    print("SPACE COMPLEXITY ANALYSIS")
    print("=" * 80)
    avg_floyd_memory = sum(m["peak_memory_bytes"] for m in floyd_metrics_list) / len(floyd_metrics_list)
    avg_enum_memory = sum(m["peak_memory_bytes"] for m in enum_metrics_list) / len(enum_metrics_list)
    avg_period = sum(m["period"] for m in enum_metrics_list) / len(enum_metrics_list)
    
    print(f"Average period: {avg_period:.1f}")
    print(f"Average Floyd memory: {avg_floyd_memory/1024:.2f} KB")
    print(f"Average Enumeration memory: {avg_enum_memory/1024:.2f} KB")
    print(f"Memory ratio: {avg_floyd_memory/avg_enum_memory:.2f}x")
    print()
    
    # Check if Floyd is O(1) - memory should not grow with period
    print("O(1) SPACE VERIFICATION")
    print("=" * 80)
    print("For O(1) space, Floyd's memory should be constant regardless of period.")
    print("Checking correlation between period and memory usage...")
    
    periods = [m["period"] for m in floyd_metrics_list]
    floyd_memories = [m["peak_memory_bytes"] for m in floyd_metrics_list]
    
    # Simple correlation check
    if len(periods) > 1:
        import statistics
        period_std = statistics.stdev(periods) if len(periods) > 1 else 0
        memory_std = statistics.stdev(floyd_memories) if len(floyd_memories) > 1 else 0
        period_mean = statistics.mean(periods)
        memory_mean = statistics.mean(floyd_memories)
        
        print(f"Period range: {min(periods)} - {max(periods)} (std: {period_std:.1f})")
        print(f"Floyd memory range: {min(floyd_memories)/1024:.2f} - {max(floyd_memories)/1024:.2f} KB (std: {memory_std/1024:.2f} KB)")
        
        if period_std > 0 and memory_std / memory_mean < 0.1:
            print("✓ Memory usage appears constant (O(1) space)")
        elif period_std > 0:
            print("⚠ Memory usage varies with period - may not be O(1)")
            print(f"  Coefficient of variation: {memory_std/memory_mean:.2%}")
        else:
            print("⚠ Cannot determine - all periods are similar")


def compare_period_only_algorithms(
    input_file: str,
    gf_order_str: str,
    num_states: int = 10,
    output_file=None,
) -> None:
    """
    Compare period-only algorithms (Floyd vs enumeration) in period-only mode.
    """
    from lfsr.field import validate_gf_order, validate_coefficient_vector
    from lfsr.analysis import _find_period_floyd, _find_period_enumeration
    
    gf_order = validate_gf_order(gf_order_str)
    coeffs_list = read_and_validate_csv(input_file, gf_order)
    
    if not coeffs_list:
        print("ERROR: No coefficient vectors found", file=sys.stderr)
        return
    
    # Use first coefficient vector
    coeffs_vector_str = coeffs_list[0]
    validate_coefficient_vector(coeffs_vector_str, gf_order, 1)
    coeffs_vector = [int(c) for c in coeffs_vector_str]
    
    # Build state update matrix
    C, CS = build_state_update_matrix(coeffs_vector, gf_order)
    V = VectorSpace(GF(gf_order), len(coeffs_vector))
    
    print("=" * 80)
    print("PERFORMANCE COMPARISON: Period-Only Mode (Floyd vs Enumeration)")
    print("=" * 80)
    print(f"Input file: {input_file}")
    print(f"GF order: {gf_order}")
    print(f"Coefficients: {coeffs_vector}")
    print(f"State space size: {gf_order ** len(coeffs_vector)}")
    print(f"Testing on first {num_states} non-zero states")
    print("=" * 80)
    print()
    
    # Collect states to test
    test_states = []
    for state in V:
        if state != V.zero():
            test_states.append(state)
            if len(test_states) >= num_states:
                break
    
    floyd_times = []
    enum_times = []
    floyd_metrics_list = []
    enum_metrics_list = []
    
    for i, state in enumerate(test_states, 1):
        print(f"\nState {i}/{len(test_states)}: {state}")
        print("-" * 80)
        
        # Test Floyd period-only
        tracemalloc.start()
        start_time = time.perf_counter()
        floyd_period = _find_period_floyd(state, C)
        end_time = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        floyd_time = end_time - start_time
        floyd_times.append(floyd_time)
        floyd_metrics = {
            "total_time": floyd_time,
            "period": floyd_period,
            "peak_memory_bytes": peak,
            "current_memory_bytes": current,
        }
        floyd_metrics_list.append(floyd_metrics)
        
        # Test Enumeration period-only
        tracemalloc.start()
        start_time = time.perf_counter()
        enum_period = _find_period_enumeration(state, C)
        end_time = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        enum_time = end_time - start_time
        enum_times.append(enum_time)
        enum_metrics = {
            "total_time": enum_time,
            "period": enum_period,
            "peak_memory_bytes": peak,
            "current_memory_bytes": current,
        }
        enum_metrics_list.append(enum_metrics)
        
        # Verify results match
        if floyd_period != enum_period:
            print(f"WARNING: Period mismatch! Floyd={floyd_period}, Enum={enum_period}")
        
        # Print comparison
        print(f"Period: {enum_period}")
        print(f"Floyd time: {floyd_time*1000:.3f} ms")
        print(f"Enumeration time: {enum_time*1000:.3f} ms")
        speedup = enum_time / floyd_time if floyd_time > 0 else float('inf')
        print(f"Speedup: {speedup:.2f}x {'(floyd faster)' if speedup > 1 else '(enum faster)'}")
        print(f"Floyd peak memory: {floyd_metrics['peak_memory_bytes']/1024:.2f} KB")
        print(f"Enum peak memory: {enum_metrics['peak_memory_bytes']/1024:.2f} KB")
        print(f"Memory ratio: {floyd_metrics['peak_memory_bytes']/enum_metrics['peak_memory_bytes']:.2f}x")
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS (Period-Only Mode)")
    print("=" * 80)
    print(f"Average Floyd time: {sum(floyd_times)/len(floyd_times)*1000:.3f} ms")
    print(f"Average Enumeration time: {sum(enum_times)/len(enum_times)*1000:.3f} ms")
    avg_speedup = sum(enum_times) / sum(floyd_times) if sum(floyd_times) > 0 else float('inf')
    print(f"Average speedup: {avg_speedup:.2f}x")
    print()
    
    # Analyze space complexity
    print("SPACE COMPLEXITY ANALYSIS (Period-Only Mode)")
    print("=" * 80)
    avg_floyd_memory = sum(m["peak_memory_bytes"] for m in floyd_metrics_list) / len(floyd_metrics_list)
    avg_enum_memory = sum(m["peak_memory_bytes"] for m in enum_metrics_list) / len(enum_metrics_list)
    avg_period = sum(m["period"] for m in enum_metrics_list) / len(enum_metrics_list)
    
    print(f"Average period: {avg_period:.1f}")
    print(f"Average Floyd memory: {avg_floyd_memory/1024:.2f} KB")
    print(f"Average Enumeration memory: {avg_enum_memory/1024:.2f} KB")
    print(f"Memory ratio: {avg_floyd_memory/avg_enum_memory:.2f}x")
    print()
    
    # Check if Floyd is O(1) - memory should not grow with period
    print("O(1) SPACE VERIFICATION (Period-Only Mode)")
    print("=" * 80)
    print("For O(1) space, Floyd's memory should be constant regardless of period.")
    print("Checking correlation between period and memory usage...")
    
    periods = [m["period"] for m in floyd_metrics_list]
    floyd_memories = [m["peak_memory_bytes"] for m in floyd_metrics_list]
    
    # Simple correlation check
    if len(periods) > 1:
        import statistics
        period_std = statistics.stdev(periods) if len(periods) > 1 else 0
        memory_std = statistics.stdev(floyd_memories) if len(floyd_memories) > 1 else 0
        period_mean = statistics.mean(periods)
        memory_mean = statistics.mean(floyd_memories)
        
        print(f"Period range: {min(periods)} - {max(periods)} (std: {period_std:.1f})")
        print(f"Floyd memory range: {min(floyd_memories)/1024:.2f} - {max(floyd_memories)/1024:.2f} KB (std: {memory_std/1024:.2f} KB)")
        
        if period_std > 0 and memory_std / memory_mean < 0.1:
            print("✓ Memory usage appears constant (O(1) space) - Floyd working correctly!")
        elif period_std > 0:
            print("⚠ Memory usage varies with period - may not be true O(1)")
            print(f"  Coefficient of variation: {memory_std/memory_mean:.2%}")
        else:
            print("⚠ Cannot determine - all periods are similar")


def main():
    parser = argparse.ArgumentParser(
        description="Performance profiling tool for LFSR cycle detection algorithms"
    )
    parser.add_argument("input_file", help="CSV file with coefficient vectors")
    parser.add_argument("gf_order", help="Galois field order")
    parser.add_argument(
        "-n", "--num-states", type=int, default=10,
        help="Number of states to test (default: 10)"
    )
    parser.add_argument(
        "--period-only", action="store_true",
        help="Compare period-only algorithms (Floyd vs enumeration without sequence storage)"
    )
    args = parser.parse_args()
    
    if args.period_only:
        compare_period_only_algorithms(args.input_file, args.gf_order, args.num_states)
    else:
        compare_algorithms(args.input_file, args.gf_order, args.num_states)


if __name__ == "__main__":
    main()
