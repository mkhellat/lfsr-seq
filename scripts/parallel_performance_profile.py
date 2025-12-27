#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance profiling tool for parallel LFSR state enumeration.

This script performs detailed timing and performance analysis of parallel
vs sequential processing to measure speedup and identify bottlenecks.
"""

import argparse
import cProfile
import io
import multiprocessing
import os
import pstats
import statistics
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
    lfsr_sequence_mapper,
    lfsr_sequence_mapper_parallel,
)
from lfsr.core import build_state_update_matrix
from lfsr.io import read_and_validate_csv


def measure_sequential(
    state_update_matrix: Any,
    state_vector_space: Any,
    gf_order: int,
    period_only: bool = True,
    algorithm: str = "auto",
) -> Tuple[float, Dict[str, Any]]:
    """Measure sequential processing performance."""
    import io
    import contextlib
    
    tracemalloc.start()
    start_time = time.perf_counter()
    
    # Suppress output
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
            state_update_matrix,
            state_vector_space,
            gf_order,
            output_file=None,
            no_progress=True,
            algorithm=algorithm,
            period_only=period_only,
        )
    
    end_time = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    elapsed = end_time - start_time
    
    stats = {
        'elapsed_time': elapsed,
        'peak_memory_mb': peak / (1024 * 1024),
        'current_memory_mb': current / (1024 * 1024),
        'num_sequences': len(seq_dict),
        'max_period': max_period,
        'periods_sum': periods_sum,
    }
    
    return elapsed, stats


def measure_parallel(
    state_update_matrix: Any,
    state_vector_space: Any,
    gf_order: int,
    num_workers: int,
    period_only: bool = True,
    algorithm: str = "auto",
) -> Tuple[float, Dict[str, Any]]:
    """Measure parallel processing performance."""
    import io
    import contextlib
    
    tracemalloc.start()
    start_time = time.perf_counter()
    
    # Suppress output
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel(
            state_update_matrix,
            state_vector_space,
            gf_order,
            output_file=None,
            no_progress=True,
            algorithm=algorithm,
            period_only=period_only,
            num_workers=num_workers,
        )
    
    end_time = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    elapsed = end_time - start_time
    
    stats = {
        'elapsed_time': elapsed,
        'peak_memory_mb': peak / (1024 * 1024),
        'current_memory_mb': current / (1024 * 1024),
        'num_sequences': len(seq_dict),
        'max_period': max_period,
        'periods_sum': periods_sum,
        'num_workers': num_workers,
    }
    
    return elapsed, stats


def verify_correctness(
    seq_stats: Dict[str, Any],
    par_stats: Dict[str, Any],
) -> Tuple[bool, List[str]]:
    """Verify that sequential and parallel results match."""
    errors = []
    
    if seq_stats['num_sequences'] != par_stats['num_sequences']:
        errors.append(
            f"Sequence count mismatch: sequential={seq_stats['num_sequences']}, "
            f"parallel={par_stats['num_sequences']}"
        )
    
    if seq_stats['max_period'] != par_stats['max_period']:
        errors.append(
            f"Max period mismatch: sequential={seq_stats['max_period']}, "
            f"parallel={par_stats['max_period']}"
        )
    
    if seq_stats['periods_sum'] != par_stats['periods_sum']:
        errors.append(
            f"Period sum mismatch: sequential={seq_stats['periods_sum']}, "
            f"parallel={par_stats['periods_sum']}"
        )
    
    return len(errors) == 0, errors


def benchmark_configuration(
    input_file: str,
    gf_order: int,
    num_workers: int,
    num_runs: int = 3,
    period_only: bool = True,
) -> Dict[str, Any]:
    """Benchmark a specific configuration with multiple runs."""
    print(f"\n{'='*70}")
    print(f"Benchmarking: {num_workers} worker(s), period_only={period_only}")
    print(f"{'='*70}")
    
    # Read input
    coeffs_list = read_and_validate_csv(input_file, gf_order)
    if not coeffs_list:
        print("ERROR: No valid coefficient vectors found")
        return {}
    
    coeffs = coeffs_list[0]
    d = len(coeffs)
    state_space_size = int(gf_order) ** d
    
    print(f"LFSR Configuration:")
    print(f"  Coefficients: {coeffs}")
    print(f"  Degree: {d}")
    print(f"  Field Order: {gf_order}")
    print(f"  State Space Size: {state_space_size:,}")
    print(f"  Number of Runs: {num_runs}")
    
    # Build matrix and vector space
    C, CS = build_state_update_matrix(coeffs, gf_order)
    V = VectorSpace(GF(gf_order), d)
    
    # Sequential runs
    print(f"\n{'─'*70}")
    print("Sequential Processing:")
    print(f"{'─'*70}")
    seq_times = []
    seq_stats_list = []
    
    for run in range(num_runs):
        print(f"  Run {run+1}/{num_runs}...", end=' ', flush=True)
        elapsed, stats = measure_sequential(C, V, gf_order, period_only=period_only)
        seq_times.append(elapsed)
        seq_stats_list.append(stats)
        print(f"{elapsed:.3f}s")
    
    seq_mean = statistics.mean(seq_times)
    seq_std = statistics.stdev(seq_times) if len(seq_times) > 1 else 0.0
    seq_stats = seq_stats_list[0]  # Use first run's stats
    
    print(f"\n  Mean Time: {seq_mean:.3f}s ± {seq_std:.3f}s")
    print(f"  Peak Memory: {seq_stats['peak_memory_mb']:.2f} MB")
    print(f"  Sequences: {seq_stats['num_sequences']}")
    print(f"  Max Period: {seq_stats['max_period']}")
    print(f"  Period Sum: {seq_stats['periods_sum']}")
    
    # Parallel runs
    print(f"\n{'─'*70}")
    print(f"Parallel Processing ({num_workers} workers):")
    print(f"{'─'*70}")
    par_times = []
    par_stats_list = []
    
    for run in range(num_runs):
        print(f"  Run {run+1}/{num_runs}...", end=' ', flush=True)
        elapsed, stats = measure_parallel(
            C, V, gf_order, num_workers, period_only=period_only
        )
        par_times.append(elapsed)
        par_stats_list.append(stats)
        print(f"{elapsed:.3f}s")
    
    par_mean = statistics.mean(par_times)
    par_std = statistics.stdev(par_times) if len(par_times) > 1 else 0.0
    par_stats = par_stats_list[0]  # Use first run's stats
    
    print(f"\n  Mean Time: {par_mean:.3f}s ± {par_std:.3f}s")
    print(f"  Peak Memory: {par_stats['peak_memory_mb']:.2f} MB")
    print(f"  Sequences: {par_stats['num_sequences']}")
    print(f"  Max Period: {par_stats['max_period']}")
    print(f"  Period Sum: {par_stats['periods_sum']}")
    
    # Verify correctness
    print(f"\n{'─'*70}")
    print("Correctness Verification:")
    print(f"{'─'*70}")
    is_correct, errors = verify_correctness(seq_stats, par_stats)
    
    if is_correct:
        print("  ✓ Results match between sequential and parallel")
    else:
        print("  ✗ ERRORS DETECTED:")
        for error in errors:
            print(f"    - {error}")
    
    # Calculate speedup
    speedup = seq_mean / par_mean if par_mean > 0 else 0.0
    efficiency = speedup / num_workers if num_workers > 0 else 0.0
    
    print(f"\n{'─'*70}")
    print("Performance Summary:")
    print(f"{'─'*70}")
    print(f"  Sequential Time: {seq_mean:.3f}s ± {seq_std:.3f}s")
    print(f"  Parallel Time:   {par_mean:.3f}s ± {par_std:.3f}s")
    print(f"  Speedup:         {speedup:.2f}x")
    print(f"  Efficiency:      {efficiency:.2%} ({efficiency * 100:.1f}% of theoretical max)")
    print(f"  Overhead:         {((par_mean * num_workers) / seq_mean - 1) * 100:.1f}%")
    
    return {
        'state_space_size': state_space_size,
        'num_workers': num_workers,
        'period_only': period_only,
        'sequential': {
            'mean_time': seq_mean,
            'std_time': seq_std,
            'times': seq_times,
            'stats': seq_stats,
        },
        'parallel': {
            'mean_time': par_mean,
            'std_time': par_std,
            'times': par_times,
            'stats': par_stats,
        },
        'speedup': speedup,
        'efficiency': efficiency,
        'correctness': is_correct,
        'errors': errors,
    }


def profile_with_cprofile(
    input_file: str,
    gf_order: int,
    num_workers: int,
    period_only: bool = True,
) -> None:
    """Profile parallel processing with cProfile."""
    print(f"\n{'='*70}")
    print("Profiling Parallel Processing (cProfile)")
    print(f"{'='*70}")
    
    # Read input
    coeffs_list = read_and_validate_csv(input_file, gf_order)
    if not coeffs_list:
        print("ERROR: No valid coefficient vectors found")
        return
    
    coeffs = coeffs_list[0]
    d = len(coeffs)
    
    # Build matrix and vector space
    C, CS = build_state_update_matrix(coeffs, gf_order)
    V = VectorSpace(GF(gf_order), d)
    
    # Profile parallel processing
    profiler = cProfile.Profile()
    profiler.enable()
    
    seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel(
        C, V, gf_order, output_file=None, no_progress=True,
        algorithm="auto", period_only=period_only, num_workers=num_workers
    )
    
    profiler.disable()
    
    # Print statistics
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats('cumulative')
    stats.print_stats(30)  # Top 30 functions
    
    print(stream.getvalue())


def main():
    parser = argparse.ArgumentParser(
        description="Performance profiling tool for parallel LFSR state enumeration"
    )
    parser.add_argument("input_file", help="CSV file with coefficient vectors")
    parser.add_argument("gf_order", type=int, help="Galois field order")
    parser.add_argument(
        "-w", "--workers", type=int, nargs="+", default=[2, 4],
        help="Number of workers to test (default: 2 4)"
    )
    parser.add_argument(
        "-r", "--runs", type=int, default=3,
        help="Number of runs per configuration (default: 3)"
    )
    parser.add_argument(
        "--period-only", action="store_true", default=True,
        help="Use period-only mode (default: True)"
    )
    parser.add_argument(
        "--full-sequence", action="store_true",
        help="Use full sequence mode (overrides --period-only)"
    )
    parser.add_argument(
        "--profile", action="store_true",
        help="Run cProfile profiling (single run with first worker count)"
    )
    parser.add_argument(
        "--all-workers", action="store_true",
        help="Test all worker counts from 1 to CPU count"
    )
    
    args = parser.parse_args()
    
    period_only = args.period_only and not args.full_sequence
    
    if args.profile:
        # Profile with first worker count
        num_workers = args.workers[0] if args.workers else 2
        profile_with_cprofile(args.input_file, args.gf_order, num_workers, period_only)
        return
    
    # Determine worker counts to test
    if args.all_workers:
        cpu_count = multiprocessing.cpu_count()
        worker_counts = list(range(1, cpu_count + 1))
    else:
        worker_counts = args.workers
    
    print(f"\n{'='*70}")
    print("Parallel LFSR State Enumeration Performance Profiling")
    print(f"{'='*70}")
    print(f"Input File: {args.input_file}")
    print(f"Field Order: {args.gf_order}")
    print(f"Mode: {'Period-Only' if period_only else 'Full Sequence'}")
    print(f"Worker Counts: {worker_counts}")
    print(f"Runs per Configuration: {args.runs}")
    print(f"CPU Cores Available: {multiprocessing.cpu_count()}")
    
    # Run benchmarks
    results = []
    for num_workers in worker_counts:
        result = benchmark_configuration(
            args.input_file,
            args.gf_order,
            num_workers,
            num_runs=args.runs,
            period_only=period_only,
        )
        if result:
            results.append(result)
    
    # Summary table
    if results:
        print(f"\n{'='*70}")
        print("Summary Table")
        print(f"{'='*70}")
        print(f"{'Workers':<10} {'Seq Time (s)':<15} {'Par Time (s)':<15} "
              f"{'Speedup':<10} {'Efficiency':<12} {'Correct':<10}")
        print(f"{'-'*70}")
        
        for result in results:
            seq_time = result['sequential']['mean_time']
            par_time = result['parallel']['mean_time']
            speedup = result['speedup']
            efficiency = result['efficiency']
            correct = "✓" if result['correctness'] else "✗"
            
            print(f"{result['num_workers']:<10} "
                  f"{seq_time:<15.3f} {par_time:<15.3f} "
                  f"{speedup:<10.2f} {efficiency:<12.1%} {correct:<10}")


if __name__ == "__main__":
    main()
