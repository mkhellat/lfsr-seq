#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detailed performance analysis to understand why Floyd is slower than expected.
"""

import sys
import time
import tracemalloc
from typing import Any

# Try to import sage (same mechanism as CLI)
_sage_available = False
try:
    from sage.all import *
    _sage_available = True
except ImportError:
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

from lfsr.analysis import _find_period_floyd, _find_period_enumeration
from lfsr.core import build_state_update_matrix


def analyze_floyd_phases(start_state: Any, state_update_matrix: Any) -> dict:
    """Break down Floyd's algorithm into phases for detailed timing."""
    metrics = {}
    
    # Phase 1: Find meeting point
    tortoise = start_state
    hare = start_state * state_update_matrix
    
    if tortoise == hare:
        return {"phase1_time": 0, "phase1_steps": 0, "phase2_time": 0, "phase2_steps": 0, "total_time": 0, "period": 1}
    
    # Phase 1 timing
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
    metrics["total_time"] = metrics["phase1_time"] + metrics["phase2_time"]
    metrics["period"] = lambda_period
    
    return metrics


def analyze_enumeration_operations(start_state: Any, state_update_matrix: Any) -> dict:
    """Analyze enumeration operations in detail."""
    start_time = time.perf_counter()
    
    next_state = start_state * state_update_matrix
    period = 1
    matrix_ops = 1  # Count matrix multiplications
    
    while next_state != start_state:
        period += 1
        next_state = next_state * state_update_matrix
        matrix_ops += 1
        
        if period > 10000000:
            raise ValueError("Period exceeds maximum limit")
    
    end_time = time.perf_counter()
    
    return {
        "total_time": end_time - start_time,
        "period": period,
        "matrix_operations": matrix_ops,
        "time_per_operation": (end_time - start_time) / matrix_ops if matrix_ops > 0 else 0,
    }


def compare_operations(start_state: Any, state_update_matrix: Any):
    """Compare the actual operations performed by each algorithm."""
    print("=" * 80)
    print("DETAILED OPERATION ANALYSIS")
    print("=" * 80)
    
    # Floyd analysis
    print("\nFloyd's Algorithm:")
    print("-" * 80)
    floyd_metrics = analyze_floyd_phases(start_state, state_update_matrix)
    print(f"Phase 1 (find meeting): {floyd_metrics['phase1_steps']} steps, {floyd_metrics['phase1_time']*1000:.3f} ms")
    print(f"Phase 2 (find period): {floyd_metrics['phase2_steps']} steps, {floyd_metrics['phase2_time']*1000:.3f} ms")
    print(f"Total: {floyd_metrics['phase1_steps'] + floyd_metrics['phase2_steps']} steps, {floyd_metrics['total_time']*1000:.3f} ms")
    print(f"Period: {floyd_metrics['period']}")
    
    # Count matrix operations for Floyd
    # Phase 1: tortoise moves 'steps' times, hare moves 2*'steps' times
    # Phase 2: hare moves 'phase2_steps' times
    floyd_matrix_ops = floyd_metrics['phase1_steps'] + 2 * floyd_metrics['phase1_steps'] + floyd_metrics['phase2_steps']
    print(f"Matrix operations: {floyd_matrix_ops}")
    print(f"Time per operation: {floyd_metrics['total_time']*1000/floyd_matrix_ops:.4f} ms" if floyd_matrix_ops > 0 else "N/A")
    
    # Enumeration analysis
    print("\nEnumeration Algorithm:")
    print("-" * 80)
    enum_metrics = analyze_enumeration_operations(start_state, state_update_matrix)
    print(f"Steps: {enum_metrics['period'] - 1}")
    print(f"Total: {enum_metrics['total_time']*1000:.3f} ms")
    print(f"Period: {enum_metrics['period']}")
    print(f"Matrix operations: {enum_metrics['matrix_operations']}")
    print(f"Time per operation: {enum_metrics['time_per_operation']*1000:.4f} ms")
    
    # Comparison
    print("\nComparison:")
    print("-" * 80)
    print(f"Floyd matrix ops: {floyd_matrix_ops}")
    print(f"Enum matrix ops: {enum_metrics['matrix_operations']}")
    print(f"Ratio: {floyd_matrix_ops / enum_metrics['matrix_operations']:.2f}x more operations for Floyd")
    print(f"Floyd time: {floyd_metrics['total_time']*1000:.3f} ms")
    print(f"Enum time: {enum_metrics['total_time']*1000:.3f} ms")
    print(f"Speedup: {enum_metrics['total_time']/floyd_metrics['total_time']:.2f}x {'(enum faster)' if enum_metrics['total_time'] < floyd_metrics['total_time'] else '(floyd faster)'}")


def test_memory_patterns(start_state: Any, state_update_matrix: Any, num_iterations: int = 5):
    """Test memory usage patterns across multiple calls."""
    print("\n" + "=" * 80)
    print("MEMORY USAGE PATTERN ANALYSIS")
    print("=" * 80)
    
    print("\nFloyd's Algorithm (period-only):")
    print("-" * 80)
    floyd_memories = []
    for i in range(num_iterations):
        tracemalloc.start()
        period = _find_period_floyd(start_state, state_update_matrix)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        floyd_memories.append(peak)
        print(f"Iteration {i+1}: Period={period}, Peak memory={peak/1024:.2f} KB")
    
    print(f"\nFloyd memory stats:")
    print(f"  Min: {min(floyd_memories)/1024:.2f} KB")
    print(f"  Max: {max(floyd_memories)/1024:.2f} KB")
    print(f"  Avg: {sum(floyd_memories)/len(floyd_memories)/1024:.2f} KB")
    print(f"  Std: {(max(floyd_memories) - min(floyd_memories))/1024:.2f} KB")
    
    print("\nEnumeration Algorithm (period-only):")
    print("-" * 80)
    enum_memories = []
    for i in range(num_iterations):
        tracemalloc.start()
        period = _find_period_enumeration(start_state, state_update_matrix)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        enum_memories.append(peak)
        print(f"Iteration {i+1}: Period={period}, Peak memory={peak/1024:.2f} KB")
    
    print(f"\nEnum memory stats:")
    print(f"  Min: {min(enum_memories)/1024:.2f} KB")
    print(f"  Max: {max(enum_memories)/1024:.2f} KB")
    print(f"  Avg: {sum(enum_memories)/len(enum_memories)/1024:.2f} KB")
    print(f"  Std: {(max(enum_memories) - min(enum_memories))/1024:.2f} KB")


def main():
    from lfsr.io import read_and_validate_csv
    from lfsr.field import validate_gf_order, validate_coefficient_vector
    
    if len(sys.argv) < 3:
        print("Usage: python3 detailed_performance_analysis.py <input_file> <gf_order>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    gf_order_str = sys.argv[2]
    
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
    
    # Get a test state
    test_state = None
    for state in V:
        if state != V.zero():
            test_state = state
            break
    
    if test_state is None:
        print("ERROR: No non-zero states found", file=sys.stderr)
        return
    
    print(f"Test state: {test_state}")
    print(f"Period (from Floyd): {_find_period_floyd(test_state, C)}")
    print(f"Period (from Enum): {_find_period_enumeration(test_state, C)}")
    print()
    
    # Detailed operation analysis
    compare_operations(test_state, C)
    
    # Memory pattern analysis
    test_memory_patterns(test_state, C, num_iterations=5)


if __name__ == "__main__":
    main()
