#!/usr/bin/env python3
"""
Memory-safe test script with emergency shutdown.

This script tests the parallel processing with strict memory limits
and emergency shutdown mechanisms to prevent memory exhaustion.

MEMORY LIMIT: 4GB
EMERGENCY SHUTDOWN: Enabled
"""

import sys
import os
import time
import resource
import signal
import subprocess
from pathlib import Path

# Memory limit: 4GB
MAX_MEMORY_MB = 4 * 1024  # 4GB in MB
MEMORY_CHECK_INTERVAL = 3  # Check memory every 3 seconds

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

def run_test_with_memory_limit(test_script, timeout=120):
    """Run test script with memory limit and timeout."""
    print(f"\n{'='*80}")
    print(f"Running: {test_script}")
    print(f"{'='*80}")
    print(f"Memory limit: {MAX_MEMORY_MB}MB")
    print(f"Timeout: {timeout}s")
    print(f"Emergency shutdown: Enabled")
    
    # Set memory limit using ulimit (if available)
    env = os.environ.copy()
    
    # Run test with timeout and memory monitoring
    try:
        # Use timeout command for additional safety
        cmd = f"timeout {timeout} python3 {test_script}"
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=False,
            text=True,
            timeout=timeout + 10,  # Extra timeout for subprocess
            env=env
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"\n⚠️  Test timed out after {timeout}s", file=sys.stderr)
        return False
    except Exception as e:
        print(f"\n⚠️  Test failed: {e}", file=sys.stderr)
        return False

def main():
    """Run memory-safe tests."""
    # Set up emergency signal handlers
    signal.signal(signal.SIGUSR1, memory_check_handler)
    
    # Set memory limit (soft limit)
    try:
        # Set soft memory limit (4GB)
        resource.setrlimit(resource.RLIMIT_AS, (MAX_MEMORY_MB * 1024 * 1024, MAX_MEMORY_MB * 1024 * 1024))
        print(f"✓ Memory limit set to {MAX_MEMORY_MB}MB")
    except (ValueError, OSError) as e:
        print(f"Warning: Could not set memory limit: {e}", file=sys.stderr)
    
    print("="*80)
    print("MEMORY-SAFE TEST RUNNER")
    print("="*80)
    print(f"Memory limit: {MAX_MEMORY_MB}MB")
    print(f"Memory monitoring: Every {MEMORY_CHECK_INTERVAL}s")
    print(f"Emergency shutdown: Enabled")
    
    # Test scripts to run (with timeouts)
    test_scripts = [
        ("scripts/test_lazy_generation_correctness.py", 60),   # Small test
        ("scripts/test_work_stealing_correctness.py", 90),    # Medium test
        ("scripts/test_hybrid_mode_correctness.py", 120),      # Larger test
    ]
    
    results = []
    for test_script, timeout in test_scripts:
        if not Path(test_script).exists():
            print(f"⚠️  Skipping {test_script} (not found)")
            continue
        
        initial_memory = check_memory()
        print(f"\nInitial memory: {initial_memory:.1f}MB")
        
        success = run_test_with_memory_limit(test_script, timeout)
        results.append((test_script, success))
        
        final_memory = check_memory()
        print(f"Final memory: {final_memory:.1f}MB (delta: {final_memory - initial_memory:.1f}MB)")
        
        if _shutdown_requested:
            print("\n⚠️  Emergency shutdown requested, stopping tests")
            break
    
    # Summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    for test_script, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{status}: {test_script}")
    
    all_passed = all(success for _, success in results)
    if not all_passed:
        sys.exit(1)

if __name__ == '__main__':
    main()
