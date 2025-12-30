#!/usr/bin/env sage-python
"""
Debug script to understand worker behavior and redundancy.

Logs detailed information about:
- States processed vs skipped per worker
- Cycles found and their min_states
- Visited marking behavior
- Deduplication results
"""

import os
import sys
import multiprocessing
from collections import defaultdict

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sage.all import GF, VectorSpace
from lfsr.analysis import _partition_state_space, _process_state_chunk
from lfsr.core import build_state_update_matrix


def create_12bit_lfsr():
    """Create a 12-bit LFSR."""
    coeffs_vector = [1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0]
    gf_order = 2
    degree = 12
    
    F = GF(gf_order)
    V = VectorSpace(F, degree)
    state_update_matrix, _ = build_state_update_matrix(coeffs_vector, gf_order)
    
    return state_update_matrix, V, gf_order, coeffs_vector, degree


def analyze_worker_results(num_workers=2):
    """Run parallel execution and analyze worker behavior."""
    print("="*80)
    print(f"DEBUGGING WORKER BEHAVIOR ({num_workers} workers)")
    print("="*80)
    
    C, V, gf_order, coeffs_vector, degree = create_12bit_lfsr()
    
    # Partition
    chunks = _partition_state_space(V, num_workers)
    print(f"\nPartitioned into {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i}: {len(chunk)} states (indices {chunk[0][1]}-{chunk[-1][1]})")
    
    # Prepare chunk data
    d = degree
    algorithm = 'enumeration'
    period_only = True
    
    chunk_data_list = []
    for worker_id, chunk in enumerate(chunks):
        chunk_data = (
            chunk,
            coeffs_vector,
            gf_order,
            d,
            algorithm,
            period_only,
            worker_id,
        )
        chunk_data_list.append(chunk_data)
    
    # Enable debug logging
    os.environ['DEBUG_PARALLEL'] = '1'
    
    # Process in parallel
    print(f"\nProcessing with {num_workers} workers...")
    with multiprocessing.Pool(processes=num_workers) as pool:
        worker_results = pool.map(_process_state_chunk, chunk_data_list)
    
    os.environ['DEBUG_PARALLEL'] = '0'
    
    # Analyze results
    print("\n" + "="*80)
    print("WORKER RESULTS ANALYSIS")
    print("="*80)
    
    all_cycles = {}  # min_state -> list of (worker_id, start_state, period)
    
    for worker_id, result in enumerate(worker_results):
        sequences = result.get('sequences', [])
        processed = result.get('processed_count', 0)
        errors = result.get('errors', [])
        
        print(f"\nWorker {worker_id}:")
        print(f"  States processed: {processed}")
        print(f"  Sequences found: {len(sequences)}")
        print(f"  Errors: {len(errors)}")
        
        for seq in sequences:
            states = seq.get('states', [])
            period = seq.get('period', 0)
            start_state = seq.get('start_state')
            
            if isinstance(states, tuple) and len(states) == 1:
                min_state = states[0]
            elif isinstance(states, list) and len(states) > 0:
                min_state = min(states)
            else:
                continue
            
            min_state_tuple = tuple(min_state) if not isinstance(min_state, tuple) else min_state
            
            if min_state_tuple not in all_cycles:
                all_cycles[min_state_tuple] = []
            
            all_cycles[min_state_tuple].append({
                'worker_id': worker_id,
                'start_state': start_state,
                'period': period
            })
            
            print(f"    Cycle: period={period}, min_state={min_state_tuple[:8]}..., start_state={start_state}")
    
    # Check for redundancy
    print("\n" + "="*80)
    print("REDUNDANCY ANALYSIS")
    print("="*80)
    
    redundant = []
    for min_state, occurrences in all_cycles.items():
        worker_ids = [occ['worker_id'] for occ in occurrences]
        if len(set(worker_ids)) > 1:
            redundant.append({
                'min_state': min_state,
                'period': occurrences[0]['period'],
                'workers': list(set(worker_ids)),
                'count': len(occurrences)
            })
            print(f"\nREDUNDANT CYCLE:")
            print(f"  Min_state: {min_state[:12]}...")
            print(f"  Period: {occurrences[0]['period']}")
            print(f"  Found by workers: {list(set(worker_ids))}")
            print(f"  Total occurrences: {len(occurrences)}")
            for occ in occurrences:
                print(f"    Worker {occ['worker_id']}: start_state={occ['start_state']}")
    
    print(f"\nTotal unique cycles: {len(all_cycles)}")
    print(f"Redundant cycles: {len(redundant)}")
    
    # Check chunk boundaries for redundant cycles
    if redundant:
        print("\n" + "="*80)
        print("CHUNK BOUNDARY ANALYSIS FOR REDUNDANT CYCLES")
        print("="*80)
        
        for red_cycle in redundant:
            min_state = red_cycle['min_state']
            print(f"\nCycle with min_state {min_state[:12]}...:")
            print(f"  Found by workers: {red_cycle['workers']}")
            
            # Check which chunks contain states from this cycle
            # We'd need to iterate the cycle to check, but for now just show chunk boundaries
            for worker_id in red_cycle['workers']:
                chunk = chunks[worker_id]
                print(f"  Worker {worker_id} chunk: indices {chunk[0][1]}-{chunk[-1][1]} ({len(chunk)} states)")


if __name__ == '__main__':
    print("Testing with 2 workers...")
    analyze_worker_results(2)
    
    print("\n\n" + "="*80)
    print("Testing with 4 workers...")
    print("="*80)
    analyze_worker_results(4)
