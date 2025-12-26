#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Floyd vs Enumeration with progressively larger periods to find break-even point.
"""

import sys
import time
from typing import Any, List, Tuple

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


def find_states_by_period(
    state_update_matrix: Any, state_vector_space: Any, target_periods: List[int]
) -> List[Tuple[Any, int]]:
    """Find states with specific periods."""
    results = []
    period_counts = {p: 0 for p in target_periods}
    
    for state in state_vector_space:
        if state == state_vector_space.zero():
            continue
        
        period = _find_period_enumeration(state, state_update_matrix)
        
        if period in target_periods and period_counts[period] < 3:
            results.append((state, period))
            period_counts[period] += 1
            
            # Check if we have enough
            if all(count >= 3 for count in period_counts.values()):
                break
    
    return results


def test_performance_scaling():
    """Test with different period sizes to find break-even point."""
    print("=" * 80)
    print("PERFORMANCE SCALING ANALYSIS")
    print("=" * 80)
    print("Testing Floyd vs Enumeration with different period sizes")
    print("=" * 80)
    
    # Create LFSR with larger state space for bigger periods
    # Use a primitive polynomial for maximum period
    # x^12 + x^6 + x^4 + x + 1 is primitive over GF(2)
    coeffs = [1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1]  # degree 12 (13 coefficients)
    C, CS = build_state_update_matrix(coeffs, 2)
    d = len(coeffs)
    V = VectorSpace(GF(2), d)
    
    print(f"\nLFSR degree: 12")
    print(f"State space size: {2**12}")
    print(f"Maximum possible period: {2**12 - 1} = 4095")
    
    # Find states with different periods
    target_periods = [10, 50, 100, 200, 500, 1000, 2000]
    print(f"\nLooking for states with periods: {target_periods}")
    
    test_cases = find_states_by_period(C, V, target_periods)
    
    if not test_cases:
        print("Could not find states with target periods. Testing with available states...")
        # Fall back to testing first few states
        count = 0
        for state in V:
            if state != V.zero() and count < 20:
                period = _find_period_enumeration(state, C)
                test_cases.append((state, period))
                count += 1
    
    # Sort by period
    test_cases.sort(key=lambda x: x[1])
    
    print(f"\nFound {len(test_cases)} test cases")
    print("=" * 80)
    
    results = []
    
    for state, period in test_cases:
        print(f"\nPeriod: {period}")
        print("-" * 80)
        
        # Time Floyd (multiple runs for average)
        floyd_times = []
        for _ in range(3):
            start = time.perf_counter()
            floyd_period = _find_period_floyd(state, C)
            floyd_times.append(time.perf_counter() - start)
        floyd_avg = sum(floyd_times) / len(floyd_times)
        
        # Time Enumeration (multiple runs for average)
        enum_times = []
        for _ in range(3):
            start = time.perf_counter()
            enum_period = _find_period_enumeration(state, C)
            enum_times.append(time.perf_counter() - start)
        enum_avg = sum(enum_times) / len(enum_times)
        
        # Verify periods match
        if floyd_period != enum_period:
            print(f"WARNING: Period mismatch! Floyd={floyd_period}, Enum={enum_period}")
        
        speedup = enum_avg / floyd_avg if floyd_avg > 0 else float('inf')
        faster = "enum" if speedup > 1 else "floyd"
        
        print(f"Floyd:    {floyd_avg*1000:.3f} ms (avg of 3 runs)")
        print(f"Enum:     {enum_avg*1000:.3f} ms (avg of 3 runs)")
        print(f"Speedup:  {speedup:.2f}x ({faster} faster)")
        
        results.append({
            "period": period,
            "floyd_time": floyd_avg,
            "enum_time": enum_avg,
            "speedup": speedup,
            "faster": faster,
        })
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"{'Period':<10} {'Floyd (ms)':<12} {'Enum (ms)':<12} {'Speedup':<10} {'Winner':<10}")
    print("-" * 80)
    
    for r in results:
        print(f"{r['period']:<10} {r['floyd_time']*1000:<12.3f} {r['enum_time']*1000:<12.3f} {r['speedup']:<10.2f} {r['faster']:<10}")
    
    # Find break-even point
    floyd_wins = [r for r in results if r['faster'] == 'floyd']
    if floyd_wins:
        min_period_floyd_wins = min(r['period'] for r in floyd_wins)
        print(f"\nFloyd becomes faster at period >= {min_period_floyd_wins}")
    else:
        print(f"\nEnumeration is faster for all tested periods (up to {max(r['period'] for r in results)})")
        print("Floyd's overhead dominates even for larger periods in this test.")


if __name__ == "__main__":
    test_performance_scaling()
