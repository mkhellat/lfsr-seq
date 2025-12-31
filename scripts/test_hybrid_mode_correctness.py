#!/usr/bin/env python3
"""
Test correctness of hybrid mode (Phase 3.2).

This script verifies that hybrid mode doesn't affect correctness:
1. Results match sequential
2. Static chunks are processed correctly
3. Work stealing handles remaining work correctly

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
        # Get memory usage in MB
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
    """Test that hybrid mode doesn't affect correctness."""
    global _shutdown_requested
    
    # Check memory before starting
    initial_memory = check_memory()
    print(f"\n{'='*80}")
    print(f"Testing Hybrid Mode: {desc} LFSR ({len(coeffs)}-bit)")
    print(f"{'='*80}")
    print(f"Initial memory: {initial_memory:.1f}MB (limit: {MAX_MEMORY_MB}MB)")
    
    # Build state update matrix
    C, _ = build_state_update_matrix(coeffs, gf_order)
    d = len(coeffs)
    V = VectorSpace(GF(gf_order), d)
    
    # Calculate state space size
    state_space_size = gf_order ** len(coeffs)
    print(f"\nState space size: {state_space_size:,} states")
    
    # Check memory after setup
    setup_memory = check_memory()
    print(f"Memory after setup: {setup_memory:.1f}MB")
    
    if _shutdown_requested:
        print("⚠️  Emergency shutdown requested, aborting test")
        return False
    
    # Sequential baseline
    print(f"\n1. Sequential (baseline):")
    seq_memory_before = check_memory()
    start = time.time()
    seq_dict, seq_period_dict, seq_max_period, seq_periods_sum = lfsr_sequence_mapper(
        C, V, gf_order, period_only=True, algorithm="enumeration", no_progress=True
    )
    seq_time = time.time() - start
    seq_memory_after = check_memory()
    print(f"   ✓ Completed in {seq_time:.3f}s")
    print(f"   Memory: {seq_memory_before:.1f}MB -> {seq_memory_after:.1f}MB (delta: {seq_memory_after - seq_memory_before:.1f}MB)")
    print(f"   Sequences: {len(seq_period_dict)}, Sum: {seq_periods_sum}, Max: {seq_max_period}")
    
    if _shutdown_requested:
        print("⚠️  Emergency shutdown requested, aborting test")
        return False
    
    # Dynamic with hybrid mode (Phase 3.2) - auto-selected for medium problems
    print(f"\n2. Dynamic mode with hybrid mode ({num_workers} workers):")
    dyn_memory_before = check_memory()
    start = time.time()
    
    # Monitor memory during execution
    import threading
    memory_monitor_active = True
    
    def memory_monitor():
        """Background thread to monitor memory usage."""
        while memory_monitor_active and not _shutdown_requested:
            memory_mb = monitor_memory()
            time.sleep(MEMORY_CHECK_INTERVAL)
    
    monitor_thread = threading.Thread(target=memory_monitor, daemon=True)
    monitor_thread.start()
    
    try:
        dyn_dict, dyn_period_dict, dyn_max_period, dyn_periods_sum = lfsr_sequence_mapper_parallel_dynamic(
            C, V, gf_order, period_only=True, algorithm="enumeration",
            num_workers=num_workers, batch_size=None, no_progress=True
        )
    finally:
        memory_monitor_active = False
        monitor_thread.join(timeout=1.0)
    
    dyn_time = time.time() - start
    dyn_memory_after = check_memory()
    dyn_speedup = seq_time / dyn_time if dyn_time > 0 else 0
    
    print(f"   Memory: {dyn_memory_before:.1f}MB -> {dyn_memory_after:.1f}MB (delta: {dyn_memory_after - dyn_memory_before:.1f}MB)")
    
    if _shutdown_requested:
        print("⚠️  Emergency shutdown requested, aborting test")
        return False
    
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
    signal.signal(signal.SIGUSR1, memory_check_handler)  # Custom signal for memory check
    
    # Set memory limit (soft limit)
    try:
        # Set soft memory limit (4GB)
        resource.setrlimit(resource.RLIMIT_AS, (MAX_MEMORY_MB * 1024 * 1024, MAX_MEMORY_MB * 1024 * 1024))
    except (ValueError, OSError) as e:
        print(f"Warning: Could not set memory limit: {e}", file=sys.stderr)
    
    print("="*80)
    print("HYBRID MODE CORRECTNESS TEST (Phase 3.2)")
    print("="*80)
    print(f"Memory limit: {MAX_MEMORY_MB}MB")
    print(f"Memory monitoring: Every {MEMORY_CHECK_INTERVAL}s")
    print(f"Emergency shutdown: Enabled")
    
    # Test with medium-sized problem (should auto-select hybrid mode)
    test_cases = [
        ([1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], 2, "14-bit"),  # 16384 states - should use hybrid
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
        print("✅ ALL TESTS PASSED - Hybrid mode maintains correctness!")
    else:
        print("✗ SOME TESTS FAILED - Check errors above")
        sys.exit(1)
    print(f"{'='*80}")


if __name__ == '__main__':
    main()
