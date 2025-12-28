#!/usr/bin/env python3
"""
Benchmark parallel vs sequential processing on strange.csv.

This script tests the speedup on strange.csv which contains multiple LFSRs.
Each LFSR should be processed independently, and parallel workers should
terminate properly between LFSRs.
"""

import sys
import os
import time
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def run_benchmark(command, description):
    """Run a command and measure execution time."""
    print(f"\n{'=' * 70}")
    print(f"{description}")
    print(f"{'=' * 70}")
    print(f"Command: {command}")
    print()
    
    start_time = time.time()
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ SUCCESS")
            print(f"   Time: {elapsed:.2f}s")
            # Extract execution time from output if available
            for line in result.stdout.split('\n'):
                if 'TOTAL execusion time' in line or 'TOTAL execution time' in line:
                    print(f"   {line.strip()}")
            return elapsed, True
        else:
            print(f"❌ FAILED (exit code: {result.returncode})")
            print(f"   Time: {elapsed:.2f}s")
            if result.stderr:
                print(f"   Error: {result.stderr[:500]}")
            return elapsed, False
            
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"⏱️  TIMEOUT after {elapsed:.2f}s")
        return elapsed, False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ ERROR: {e}")
        print(f"   Time: {elapsed:.2f}s")
        return elapsed, False


def main():
    """Run benchmarks on strange.csv."""
    print("=" * 70)
    print("BENCHMARK: Parallel vs Sequential on strange.csv")
    print("=" * 70)
    print("\nThis script benchmarks parallel processing speedup on strange.csv")
    print("which contains 3 LFSRs. Each LFSR should be processed independently.")
    print()
    
    # Check if strange.csv exists
    strange_csv = os.path.join(os.path.dirname(__file__), '..', 'strange.csv')
    if not os.path.exists(strange_csv):
        print(f"ERROR: {strange_csv} not found")
        return 1
    
    # Activate venv if it exists
    venv_python = os.path.join(os.path.dirname(__file__), '..', '.venv', 'bin', 'python3')
    if os.path.exists(venv_python):
        python_cmd = venv_python
    else:
        python_cmd = 'python3'
    
    base_cmd = f"{python_cmd} -m lfsr.cli"
    
    results = {}
    
    # Test 1: Sequential processing
    seq_time, seq_success = run_benchmark(
        f"{base_cmd} strange.csv 2 --no-parallel --period-only",
        "Test 1: Sequential Processing (Baseline)"
    )
    results['sequential'] = (seq_time, seq_success)
    
    if not seq_success:
        print("\n❌ Sequential processing failed - cannot compare")
        return 1
    
    # Test 2: Parallel processing (2 workers)
    par2_time, par2_success = run_benchmark(
        f"{base_cmd} strange.csv 2 --parallel --num-workers 2 --period-only",
        "Test 2: Parallel Processing (2 workers)"
    )
    results['parallel_2'] = (par2_time, par2_success)
    
    # Test 3: Parallel processing (4 workers)
    par4_time, par4_success = run_benchmark(
        f"{base_cmd} strange.csv 2 --parallel --num-workers 4 --period-only",
        "Test 3: Parallel Processing (4 workers)"
    )
    results['parallel_4'] = (par4_time, par4_success)
    
    # Summary
    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)
    
    print(f"\nSequential: {seq_time:.2f}s")
    
    if par2_success:
        speedup2 = seq_time / par2_time if par2_time > 0 else 0
        print(f"Parallel (2 workers): {par2_time:.2f}s (speedup: {speedup2:.2f}x)")
    
    if par4_success:
        speedup4 = seq_time / par4_time if par4_time > 0 else 0
        print(f"Parallel (4 workers): {par4_time:.2f}s (speedup: {speedup4:.2f}x)")
    
    # Check for hung workers
    print("\n" + "=" * 70)
    print("WORKER TERMINATION CHECK")
    print("=" * 70)
    print("\nChecking for zombie/hung worker processes...")
    
    try:
        result = subprocess.run(
            "ps aux | grep -E '[p]ython.*lfsr|pool|worker' | grep -v grep",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.stdout.strip():
            print("⚠️  WARNING: Found potential hung worker processes:")
            print(result.stdout)
        else:
            print("✅ No hung worker processes found")
    except Exception as e:
        print(f"⚠️  Could not check for hung processes: {e}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
