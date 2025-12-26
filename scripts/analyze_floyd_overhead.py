#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze why Floyd does more operations and when it becomes beneficial.
"""

import sys
import time
from typing import Any

# Try to import sage
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


def analyze_operation_count(start_state: Any, state_update_matrix: Any, period: int):
    """Analyze operation counts for Floyd vs Enumeration."""
    print(f"\nPeriod: {period}")
    print("-" * 80)
    
    # Floyd operations
    # Phase 1: Find meeting point
    # - Tortoise moves: steps (where steps ≈ period/2 on average for LFSRs)
    # - Hare moves: 2*steps (double speed)
    # - Total Phase 1: steps + 2*steps = 3*steps operations
    # Phase 2: Find period
    # - Hare moves: period steps
    # Total Floyd: 3*steps + period operations
    
    # For LFSRs, the meeting point is typically around period/2
    # So steps ≈ period/2
    estimated_steps = period // 2
    floyd_ops_phase1 = 3 * estimated_steps  # tortoise + 2*hare
    floyd_ops_phase2 = period
    floyd_total_ops = floyd_ops_phase1 + floyd_ops_phase2
    
    # Enumeration operations
    enum_ops = period  # Just period operations
    
    print(f"Floyd estimated operations:")
    print(f"  Phase 1: ~{floyd_ops_phase1} (3 * {estimated_steps})")
    print(f"  Phase 2: {floyd_ops_phase2}")
    print(f"  Total: ~{floyd_total_ops}")
    print(f"Enumeration operations: {enum_ops}")
    print(f"Ratio: {floyd_total_ops/enum_ops:.2f}x more operations for Floyd")
    
    # Floyd becomes beneficial when:
    # - The overhead is amortized over very large periods
    # - Or when you can't afford to enumerate (memory constraints)
    # - Or when enumeration would be too slow
    
    # Break-even point: when Floyd's overhead is acceptable
    # For small periods (< ~100), enumeration is better
    # For very large periods (> ~1000), Floyd might be better IF there are other benefits
    
    print(f"\nAnalysis:")
    print(f"  For period {period}:")
    if period < 50:
        print(f"    Enumeration is better (small period, Floyd overhead dominates)")
    elif period < 200:
        print(f"    Close call - depends on implementation details")
    else:
        print(f"    Floyd might be better for very large periods")
    
    return floyd_total_ops, enum_ops


def test_actual_operations(start_state: Any, state_update_matrix: Any):
    """Test actual operation counts."""
    # Count Floyd operations
    tortoise = start_state
    hare = start_state * state_update_matrix
    
    phase1_ops = 0
    steps = 0
    while tortoise != hare and steps < 1000000:
        tortoise = tortoise * state_update_matrix
        hare = (hare * state_update_matrix) * state_update_matrix
        phase1_ops += 3  # tortoise + 2*hare
        steps += 1
    
    meeting_point = tortoise
    phase2_ops = 0
    hare = meeting_point * state_update_matrix
    if meeting_point != hare:
        while meeting_point != hare and phase2_ops < 1000000:
            hare = hare * state_update_matrix
            phase2_ops += 1
    
    floyd_total = phase1_ops + phase2_ops
    
    # Count enumeration operations
    next_state = start_state * state_update_matrix
    enum_ops = 1
    while next_state != start_state:
        next_state = next_state * state_update_matrix
        enum_ops += 1
    
    period = enum_ops
    
    print(f"\nActual Operation Counts:")
    print(f"  Floyd Phase 1: {phase1_ops} operations")
    print(f"  Floyd Phase 2: {phase2_ops} operations")
    print(f"  Floyd Total: {floyd_total} operations")
    print(f"  Enumeration: {enum_ops} operations")
    print(f"  Ratio: {floyd_total/enum_ops:.2f}x")
    
    return floyd_total, enum_ops, period


def main():
    from lfsr.io import read_and_validate_csv
    from lfsr.field import validate_gf_order, validate_coefficient_vector
    
    if len(sys.argv) < 3:
        print("Usage: python3 analyze_floyd_overhead.py <input_file> <gf_order>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    gf_order_str = sys.argv[2]
    
    gf_order = validate_gf_order(gf_order_str)
    coeffs_list = read_and_validate_csv(input_file, gf_order)
    
    if not coeffs_list:
        print("ERROR: No coefficient vectors found", file=sys.stderr)
        return
    
    coeffs_vector_str = coeffs_list[0]
    validate_coefficient_vector(coeffs_vector_str, gf_order, 1)
    coeffs_vector = [int(c) for c in coeffs_vector_str]
    
    C, CS = build_state_update_matrix(coeffs_vector, gf_order)
    V = VectorSpace(GF(gf_order), len(coeffs_vector))
    
    print("=" * 80)
    print("FLOYD OVERHEAD ANALYSIS")
    print("=" * 80)
    
    # Test with different states/periods
    test_states = []
    for state in V:
        if state != V.zero():
            period = _find_period_enumeration(state, C)
            test_states.append((state, period))
            if len(test_states) >= 5:
                break
    
    # Sort by period
    test_states.sort(key=lambda x: x[1])
    
    for state, period in test_states:
        print(f"\n{'='*80}")
        analyze_operation_count(state, C, period)
        floyd_ops, enum_ops, actual_period = test_actual_operations(state, C)
        
        # Time both
        start = time.perf_counter()
        _find_period_floyd(state, C)
        floyd_time = time.perf_counter() - start
        
        start = time.perf_counter()
        _find_period_enumeration(state, C)
        enum_time = time.perf_counter() - start
        
        print(f"\nTiming:")
        print(f"  Floyd: {floyd_time*1000:.3f} ms ({floyd_ops} ops)")
        print(f"  Enum:  {enum_time*1000:.3f} ms ({enum_ops} ops)")
        print(f"  Floyd time per op: {floyd_time/floyd_ops*1000:.4f} ms" if floyd_ops > 0 else "N/A")
        print(f"  Enum time per op:  {enum_time/enum_ops*1000:.4f} ms" if enum_ops > 0 else "N/A")
        print(f"  Speedup: {enum_time/floyd_time:.2f}x {'(enum faster)' if enum_time < floyd_time else '(floyd faster)'}")


if __name__ == "__main__":
    main()
