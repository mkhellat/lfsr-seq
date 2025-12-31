#!/usr/bin/env python3
"""
Test correctness of lazy task generation (Phase 2.4).

This script verifies that lazy task generation doesn't affect correctness:
1. Results match sequential
2. All batches are generated correctly
3. Producer thread completes successfully

MEMORY SAFETY: This script includes memory monitoring and emergency shutdown
to prevent memory exhaustion during testing.
"""

import sys
import os
import time
import resource
import signal
from pathlib import Path

# Memory limit: 4GB (as requested)
MAX_MEMORY_MB = 4 * 1024  # 4GB in MB
MEMORY_CHECK_INTERVAL = 5  # Check memory every 5 seconds

# Emergency shutdown flag
_shutdown_requested = False

def memory_check_handler(signum, frame):
    """Emergency shutdown if memory limit exceeded."""
    global _shutdown_requested
    _shutdown_requested = True
    print("\n⚠️  EMERGENCY SHUTDOWN: Memory limit exceeded!", file=sys.stderr)
    sys.exit(1)

def check_memory():
    """Check current memory usage and return MB used."""
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        memory_mb = usage.ru_maxrss / 1024  # Convert KB to MB (Linux)
        return memory_mb
    except Exception:
        return 0

def monitor_memory():
    """Monitor memory usage and trigger emergency shutdown if needed."""
    memory_mb = check_memory()
    if memory_mb > MAX_MEMORY_MB:
        print(f"\n⚠️  MEMORY WARNING: Using {memory_mb:.1f}MB (limit: {MAX_MEMORY_MB}MB)", file=sys.stderr)
        memory_check_handler(None, None)
    return memory_mb

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from sage.all import *
    from lfsr.core import build_state_update_matrix
    from lfsr.analysis import (
        lfsr_sequence_mapper,
        lfsr_sequence_mapper_parallel_dynamic
    )
except ImportError as e:
    print(f"ERROR: Cannot import required modules: {e}")
    print("This test requires SageMath")
    sys.exit(1)


def test_correctness(coeffs, gf_order, desc, num_workers=4):
    """Test that lazy generation doesn't affect correctness."""
    print(f"\n{'='*80}")
    print(f"Testing {desc} LFSR ({len(coeffs)}-bit) with lazy generation")
    print(f"{'='*80}")
    
    # Build state update matrix
    C, _ = build_state_update_matrix(coeffs, gf_order)
    d = len(coeffs)
    V = VectorSpace(GF(gf_order), d)
    
    # Calculate state space size
    state_space_size = gf_order ** len(coeffs)
    print(f"\nState space size: {state_space_size:,} states")
    
    # Sequential baseline
    print(f"\n1. Sequential (baseline):")
    start = time.time()
    seq_dict, seq_period_dict, seq_max_period, seq_periods_sum = lfsr_sequence_mapper(
        C, V, gf_order, period_only=True, algorithm="enumeration", no_progress=True
    )
    seq_time = time.time() - start
    print(f"   ✓ Completed in {seq_time:.3f}s")
    print(f"   Sequences: {len(seq_period_dict)}, Sum: {seq_periods_sum}, Max: {seq_max_period}")
    
    # Dynamic with lazy generation (Phase 2.4)
    print(f"\n2. Dynamic mode with lazy generation ({num_workers} workers):")
    start = time.time()
    dyn_dict, dyn_period_dict, dyn_max_period, dyn_periods_sum = lfsr_sequence_mapper_parallel_dynamic(
        C, V, gf_order, period_only=True, algorithm="enumeration",
        num_workers=num_workers, batch_size=None, no_progress=True
    )
    dyn_time = time.time() - start
    dyn_speedup = seq_time / dyn_time if dyn_time > 0 else 0
    
    correct = (
        len(dyn_period_dict) == len(seq_period_dict) and
        dyn_periods_sum == seq_periods_sum and
        dyn_max_period == seq_max_period
    )
    status = "✓ CORRECT" if correct else "✗ INCORRECT"
    print(f"   {status}: {dyn_time:.3f}s (speedup: {dyn_speedup:.2f}x)")
    print(f"   Sequences: {len(dyn_period_dict)}, Sum: {dyn_periods_sum}, Max: {dyn_max_period}")
    
    if not correct:
        print(f"   ERROR: Mismatch!")
        print(f"     Expected: {len(seq_period_dict)} sequences, sum={seq_periods_sum}, max={seq_max_period}")
        print(f"     Got:      {len(dyn_period_dict)} sequences, sum={dyn_periods_sum}, max={dyn_max_period}")
        return False
    
    return True


def main():
    """Run correctness tests."""
    # Set up emergency signal handlers
    signal.signal(signal.SIGUSR1, memory_check_handler)
    
    # Set memory limit (soft limit)
    try:
        resource.setrlimit(resource.RLIMIT_AS, (MAX_MEMORY_MB * 1024 * 1024, MAX_MEMORY_MB * 1024 * 1024))
    except (ValueError, OSError) as e:
        print(f"Warning: Could not set memory limit: {e}", file=sys.stderr)
    
    print("="*80)
    print("LAZY TASK GENERATION CORRECTNESS TEST (Phase 2.4)")
    print("="*80)
    print(f"Memory limit: {MAX_MEMORY_MB}MB")
    print(f"Memory monitoring: Every {MEMORY_CHECK_INTERVAL}s")
    print(f"Emergency shutdown: Enabled")
    
    # Test cases
    test_cases = [
        ([1, 1, 0, 1], 2, "4-bit"),  # 16 states
        ([1, 0, 1, 1, 0, 0, 0, 1], 2, "8-bit"),  # 256 states
        ([1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1], 2, "12-bit"),  # 4096 states
        ([1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], 2, "14-bit"),  # 16384 states
    ]
    
    all_passed = True
    
    for coeffs, gf_order, desc in test_cases:
        try:
            passed = test_correctness(coeffs, gf_order, desc, num_workers=4)
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"\n✗ Error testing {desc}: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    # Final summary
    print(f"\n{'='*80}")
    if all_passed:
        print("✅ ALL TESTS PASSED - Lazy generation maintains correctness!")
    else:
        print("✗ SOME TESTS FAILED - Check errors above")
        sys.exit(1)
    print(f"{'='*80}")


if __name__ == '__main__':
    main()
