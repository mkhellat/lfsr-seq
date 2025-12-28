#!/usr/bin/env python3
"""
Test fork mode with SageMath isolation to avoid category mismatch errors.

This script tests if we can use fork mode (faster) while avoiding SageMath
category mismatch errors by properly isolating SageMath in workers.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import multiprocessing
import time

try:
    from sage.all import GF, VectorSpace, vector
    from lfsr.core import build_state_update_matrix
    from lfsr.analysis import _find_period
    SAGEMATH_AVAILABLE = True
except ImportError:
    print("ERROR: SageMath not available")
    sys.exit(1)


def worker_with_sagemath_isolated(chunk_data):
    """
    Worker function that isolates SageMath to avoid category mismatches.
    
    Strategy:
    1. Import SageMath fresh in worker (even though fork inherits it)
    2. Create fresh GF/VectorSpace objects
    3. Rebuild matrix from coefficients (don't share parent's matrix)
    """
    state_tuple, coeffs, gf_order, degree = chunk_data
    
    # CRITICAL: Create fresh SageMath objects in worker
    # Even though fork inherits parent's memory, creating fresh objects
    # avoids category mismatch errors
    F = GF(gf_order)
    V = VectorSpace(F, degree)
    
    # Reconstruct state vector from tuple
    state_list = [F(x) for x in state_tuple]
    state = vector(F, state_list)
    
    # Rebuild matrix from coefficients (don't use parent's matrix)
    C, _ = build_state_update_matrix(coeffs, gf_order)
    
    # Compute period
    period = _find_period(state, C, algorithm="enumeration")
    
    return period


def test_fork_mode():
    """Test fork mode with SageMath isolation."""
    print("=" * 70)
    print("TEST: Fork Mode with SageMath Isolation")
    print("=" * 70)
    
    # Create test data
    coeffs = [1, 1, 1, 0, 0, 0, 0, 0, 1, 1]
    gf_order = 2
    degree = 10
    
    # Build matrix in parent
    C, CS = build_state_update_matrix(coeffs, gf_order)
    V = VectorSpace(GF(gf_order), degree)
    
    # Get first 20 states
    states = []
    for i, state in enumerate(V):
        if i >= 20:
            break
        states.append((tuple(state), coeffs, gf_order, degree))
    
    print(f"\nProcessing {len(states)} states with fork mode...")
    
    # Test with fork mode
    try:
        ctx = multiprocessing.get_context('fork')
        
        start = time.time()
        with ctx.Pool(processes=4) as pool:
            results = pool.map(worker_with_sagemath_isolated, states)
        elapsed = time.time() - start
        
        print(f"✅ Fork mode SUCCESS")
        print(f"   Time: {elapsed:.3f}s")
        print(f"   Results: {len(results)} periods computed")
        print(f"   Sample periods: {results[:5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fork mode FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sequential_baseline():
    """Test sequential processing for comparison."""
    print("\n" + "=" * 70)
    print("BASELINE: Sequential Processing")
    print("=" * 70)
    
    coeffs = [1, 1, 1, 0, 0, 0, 0, 0, 1, 1]
    C, CS = build_state_update_matrix(coeffs, 2)
    V = VectorSpace(GF(2), 10)
    
    states = []
    for i, state in enumerate(V):
        if i >= 20:
            break
        states.append(state)
    
    print(f"\nProcessing {len(states)} states sequentially...")
    
    start = time.time()
    results = []
    for state in states:
        period = _find_period(state, C, algorithm="enumeration")
        results.append(period)
    elapsed = time.time() - start
    
    print(f"   Time: {elapsed:.3f}s")
    print(f"   Results: {len(results)} periods computed")
    print(f"   Sample periods: {results[:5]}")
    
    return elapsed


def main():
    """Run tests."""
    print("\n" + "=" * 70)
    print("FORK MODE WITH SAGEMATH ISOLATION TEST")
    print("=" * 70)
    print("\nThis test verifies if fork mode works with proper SageMath isolation.")
    print("If successful, we can use fork mode (13-17x faster than spawn).\n")
    
    # Test sequential baseline
    seq_time = test_sequential_baseline()
    
    # Test fork mode
    fork_success = test_fork_mode()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Sequential time: {seq_time:.3f}s")
    print(f"Fork mode: {'✅ SUCCESS' if fork_success else '❌ FAILED'}")
    
    if fork_success:
        print("\n✅ RECOMMENDATION: Use fork mode with SageMath isolation")
        print("   - Fork is 13-17x faster than spawn for process creation")
        print("   - Proper isolation avoids category mismatch errors")
        print("   - Expected 10-15x improvement over current spawn mode")
    else:
        print("\n❌ RECOMMENDATION: Continue using spawn mode or investigate further")
        print("   - Fork mode has SageMath compatibility issues")
        print("   - May need alternative approach (threading, joblib, etc.)")


if __name__ == "__main__":
    main()
