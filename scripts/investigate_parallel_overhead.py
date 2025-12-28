#!/usr/bin/env python3
"""
Investigate parallel processing overhead in lfsr-seq.

This script profiles different aspects of parallel processing overhead:
1. SageMath initialization cost
2. Process creation overhead (fork vs spawn)
3. IPC (Inter-Process Communication) overhead
4. GIL behavior with SageMath
5. Threading vs multiprocessing
6. State space partitioning overhead
"""

import time
import multiprocessing
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import sys
import os

# Add parent directory to path to import lfsr modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from sage.all import GF, VectorSpace, vector
    from lfsr.core import build_state_update_matrix
    SAGEMATH_AVAILABLE = True
except ImportError:
    print("WARNING: SageMath not available, some tests will be skipped")
    SAGEMATH_AVAILABLE = False


def test_sagemath_initialization():
    """Test overhead of SageMath initialization."""
    print("\n" + "=" * 70)
    print("TEST 1: SageMath Initialization Overhead")
    print("=" * 70)
    
    if not SAGEMATH_AVAILABLE:
        print("Skipped: SageMath not available")
        return
    
    # Test 1a: Basic initialization
    print("\n1a. Basic GF and VectorSpace creation:")
    start = time.time()
    for _ in range(100):
        F = GF(2)
        V = VectorSpace(F, 10)
    elapsed = time.time() - start
    print(f"   100 initializations: {elapsed:.3f}s ({elapsed/100*1000:.2f}ms each)")
    
    # Test 1b: With vector creation
    print("\n1b. GF, VectorSpace, and vector creation:")
    start = time.time()
    for _ in range(100):
        F = GF(2)
        V = VectorSpace(F, 10)
        v = vector(F, [0]*10)
    elapsed = time.time() - start
    print(f"   100 initializations: {elapsed:.3f}s ({elapsed/100*1000:.2f}ms each)")
    
    # Test 1c: Matrix creation
    print("\n1c. Matrix creation (state update matrix):")
    coeffs = [1, 1, 1, 0, 0, 0, 0, 0, 1, 1]
    start = time.time()
    for _ in range(10):
        C, CS = build_state_update_matrix(coeffs, 2)
    elapsed = time.time() - start
    print(f"   10 matrix creations: {elapsed:.3f}s ({elapsed/10*1000:.2f}ms each)")


def dummy_worker(x):
    """Dummy worker function for overhead testing."""
    return x * 2


def sagemath_worker(x):
    """Worker that initializes SageMath."""
    if SAGEMATH_AVAILABLE:
        F = GF(2)
        V = VectorSpace(F, 10)
        v = vector(F, [0]*10)
    return x * 2


def test_process_creation_overhead():
    """Test process creation overhead (fork vs spawn)."""
    print("\n" + "=" * 70)
    print("TEST 2: Process Creation Overhead (Fork vs Spawn)")
    print("=" * 70)
    
    num_tasks = 100
    num_workers = 4
    
    # Test 2a: Fork mode
    print(f"\n2a. Fork mode ({num_workers} workers, {num_tasks} tasks):")
    try:
        ctx_fork = multiprocessing.get_context('fork')
        start = time.time()
        with ctx_fork.Pool(processes=num_workers) as pool:
            results = pool.map(dummy_worker, range(num_tasks))
        fork_time = time.time() - start
        print(f"   Total time: {fork_time:.3f}s")
        print(f"   Per task: {fork_time/num_tasks*1000:.2f}ms")
        print(f"   Overhead per task: {fork_time/num_tasks*1000:.2f}ms")
    except Exception as e:
        print(f"   Failed: {e}")
        fork_time = None
    
    # Test 2b: Spawn mode
    print(f"\n2b. Spawn mode ({num_workers} workers, {num_tasks} tasks):")
    try:
        ctx_spawn = multiprocessing.get_context('spawn')
        start = time.time()
        with ctx_spawn.Pool(processes=num_workers) as pool:
            results = pool.map(dummy_worker, range(num_tasks))
        spawn_time = time.time() - start
        print(f"   Total time: {spawn_time:.3f}s")
        print(f"   Per task: {spawn_time/num_tasks*1000:.2f}ms")
        if fork_time:
            print(f"   Overhead vs fork: {spawn_time/fork_time:.2f}x slower")
    except Exception as e:
        print(f"   Failed: {e}")
        spawn_time = None


def test_sagemath_in_workers():
    """Test SageMath initialization overhead in workers."""
    print("\n" + "=" * 70)
    print("TEST 3: SageMath Initialization in Workers")
    print("=" * 70)
    
    if not SAGEMATH_AVAILABLE:
        print("Skipped: SageMath not available")
        return
    
    num_tasks = 50
    num_workers = 4
    
    # Test 3a: Fork mode with SageMath
    print(f"\n3a. Fork mode with SageMath ({num_workers} workers, {num_tasks} tasks):")
    try:
        ctx_fork = multiprocessing.get_context('fork')
        start = time.time()
        with ctx_fork.Pool(processes=num_workers) as pool:
            results = pool.map(sagemath_worker, range(num_tasks))
        fork_sage_time = time.time() - start
        print(f"   Total time: {fork_sage_time:.3f}s")
        print(f"   Per task: {fork_sage_time/num_tasks*1000:.2f}ms")
    except Exception as e:
        print(f"   Failed: {e}")
        fork_sage_time = None
    
    # Test 3b: Spawn mode with SageMath
    print(f"\n3b. Spawn mode with SageMath ({num_workers} workers, {num_tasks} tasks):")
    try:
        ctx_spawn = multiprocessing.get_context('spawn')
        start = time.time()
        with ctx_spawn.Pool(processes=num_workers) as pool:
            results = pool.map(sagemath_worker, range(num_tasks))
        spawn_sage_time = time.time() - start
        print(f"   Total time: {spawn_sage_time:.3f}s")
        print(f"   Per task: {spawn_sage_time/num_tasks*1000:.2f}ms")
        if fork_sage_time:
            print(f"   Overhead vs fork: {spawn_sage_time/fork_sage_time:.2f}x slower")
    except Exception as e:
        print(f"   Failed: {e}")


def test_threading_vs_multiprocessing():
    """Test threading vs multiprocessing for CPU-bound tasks."""
    print("\n" + "=" * 70)
    print("TEST 4: Threading vs Multiprocessing (GIL Behavior)")
    print("=" * 70)
    
    if not SAGEMATH_AVAILABLE:
        print("Skipped: SageMath not available")
        return
    
    def cpu_bound_task(x):
        """CPU-bound task: matrix multiplication."""
        F = GF(2)
        V = VectorSpace(F, 10)
        v1 = vector(F, [1]*10)
        v2 = vector(F, [1]*10)
        # Do some computation
        result = sum(v1[i] + v2[i] for i in range(10))
        return result
    
    num_tasks = 50
    num_workers = 4
    
    # Test 4a: Threading
    print(f"\n4a. Threading ({num_workers} threads, {num_tasks} tasks):")
    start = time.time()
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(cpu_bound_task, range(num_tasks)))
    threading_time = time.time() - start
    print(f"   Total time: {threading_time:.3f}s")
    print(f"   Per task: {threading_time/num_tasks*1000:.2f}ms")
    print(f"   Note: GIL may limit parallelism for CPU-bound tasks")
    
    # Test 4b: Multiprocessing (fork)
    print(f"\n4b. Multiprocessing - Fork ({num_workers} processes, {num_tasks} tasks):")
    try:
        ctx_fork = multiprocessing.get_context('fork')
        start = time.time()
        with ctx_fork.Pool(processes=num_workers) as pool:
            results = pool.map(cpu_bound_task, range(num_tasks))
        multiproc_time = time.time() - start
        print(f"   Total time: {multiproc_time:.3f}s")
        print(f"   Per task: {multiproc_time/num_tasks*1000:.2f}ms")
        print(f"   Speedup vs threading: {threading_time/multiproc_time:.2f}x")
    except Exception as e:
        print(f"   Failed: {e}")


def test_state_space_partitioning():
    """Test overhead of state space partitioning."""
    print("\n" + "=" * 70)
    print("TEST 5: State Space Partitioning Overhead")
    print("=" * 70)
    
    if not SAGEMATH_AVAILABLE:
        print("Skipped: SageMath not available")
        return
    
    # Test with different state space sizes
    test_sizes = [
        (4, 2),   # 16 states
        (5, 2),   # 32 states
        (6, 2),   # 64 states
        (7, 2),   # 128 states
        (10, 2),  # 1024 states
    ]
    
    for degree, gf_order in test_sizes:
        print(f"\n5. Partitioning {gf_order}^{degree} = {gf_order**degree} states:")
        F = GF(gf_order)
        V = VectorSpace(F, degree)
        
        # Time the partitioning
        start = time.time()
        states_list = []
        for state in V:
            states_list.append((tuple(state), 0))
        partition_time = time.time() - start
        
        print(f"   Iteration + tuple conversion: {partition_time:.3f}s")
        print(f"   Per state: {partition_time/len(states_list)*1000:.2f}ms")
        
        # Test chunking
        num_chunks = 4
        chunk_size = len(states_list) // num_chunks
        start = time.time()
        chunks = [states_list[i:i+chunk_size] for i in range(0, len(states_list), chunk_size)]
        chunk_time = time.time() - start
        print(f"   Chunking into {num_chunks} chunks: {chunk_time:.3f}s")


def worker_with_data(data):
    """Worker that receives and returns data (module-level for pickling)."""
    return len(data), sum(data)


def test_ipc_overhead():
    """Test IPC (Inter-Process Communication) overhead."""
    print("\n" + "=" * 70)
    print("TEST 6: IPC (Inter-Process Communication) Overhead")
    print("=" * 70)
    
    # Test with different data sizes
    data_sizes = [10, 100, 1000, 10000]
    num_workers = 4
    
    for size in data_sizes:
        data = list(range(size))
        print(f"\n6. IPC with {size} elements:")
        
        # Fork mode
        try:
            ctx_fork = multiprocessing.get_context('fork')
            start = time.time()
            with ctx_fork.Pool(processes=num_workers) as pool:
                results = pool.map(worker_with_data, [data] * num_workers)
            fork_time = time.time() - start
            print(f"   Fork mode: {fork_time:.3f}s ({fork_time/num_workers*1000:.2f}ms per worker)")
        except Exception as e:
            print(f"   Fork mode failed: {e}")
        
        # Spawn mode
        try:
            ctx_spawn = multiprocessing.get_context('spawn')
            start = time.time()
            with ctx_spawn.Pool(processes=num_workers) as pool:
                results = pool.map(worker_with_data, [data] * num_workers)
            spawn_time = time.time() - start
            print(f"   Spawn mode: {spawn_time:.3f}s ({spawn_time/num_workers*1000:.2f}ms per worker)")
        except Exception as e:
            print(f"   Spawn mode failed: {e}")


def test_real_lfsr_processing():
    """Test real LFSR processing overhead."""
    print("\n" + "=" * 70)
    print("TEST 7: Real LFSR Processing Overhead")
    print("=" * 70)
    
    if not SAGEMATH_AVAILABLE:
        print("Skipped: SageMath not available")
        return
    
    from lfsr.analysis import _find_period
    
    # Small LFSR
    coeffs = [1, 1, 1, 0, 0, 0, 0, 0, 1, 1]
    C, CS = build_state_update_matrix(coeffs, 2)
    V = VectorSpace(GF(2), 10)
    
    # Get first 20 states
    states = []
    for i, state in enumerate(V):
        if i >= 20:
            break
        states.append(state)
    
    print(f"\n7. Processing {len(states)} states:")
    
    # Sequential
    start = time.time()
    for state in states:
        period = _find_period(state, C, algorithm="enumeration")
    seq_time = time.time() - start
    print(f"   Sequential: {seq_time:.3f}s ({seq_time/len(states)*1000:.2f}ms per state)")
    
    # Parallel (fork)
    def process_state(state_tuple):
        """Worker function to process a state."""
        F = GF(2)
        V = VectorSpace(F, 10)
        state = vector(F, state_tuple)
        C, _ = build_state_update_matrix(coeffs, 2)
        period = _find_period(state, C, algorithm="enumeration")
        return period
    
    try:
        ctx_fork = multiprocessing.get_context('fork')
        state_tuples = [tuple(s) for s in states]
        start = time.time()
        with ctx_fork.Pool(processes=4) as pool:
            results = pool.map(process_state, state_tuples)
        par_time = time.time() - start
        print(f"   Parallel (fork): {par_time:.3f}s ({par_time/len(states)*1000:.2f}ms per state)")
        print(f"   Speedup: {seq_time/par_time:.2f}x")
    except Exception as e:
        print(f"   Parallel (fork) failed: {e}")


def main():
    """Run all overhead tests."""
    print("=" * 70)
    print("PARALLEL PROCESSING OVERHEAD INVESTIGATION")
    print("=" * 70)
    print("\nThis script investigates various sources of overhead in parallel")
    print("processing to identify bottlenecks and optimization opportunities.")
    
    test_sagemath_initialization()
    test_process_creation_overhead()
    test_sagemath_in_workers()
    test_threading_vs_multiprocessing()
    test_state_space_partitioning()
    test_ipc_overhead()
    test_real_lfsr_processing()
    
    print("\n" + "=" * 70)
    print("INVESTIGATION COMPLETE")
    print("=" * 70)
    print("\nKey Findings:")
    print("1. SageMath initialization overhead per worker")
    print("2. Process creation overhead (fork vs spawn)")
    print("3. IPC overhead for data serialization")
    print("4. State space partitioning overhead")
    print("5. GIL behavior with threading vs multiprocessing")
    print("\nRecommendations will be based on these findings.")


if __name__ == "__main__":
    main()
