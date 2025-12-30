# Worker Redundancy Fix - Design Document

**Date**: 2025-12-30  
**Problem**: Cycles spanning multiple chunks are processed by multiple workers, causing redundant work and worse performance.

---

## Problem Analysis

### Current Behavior
1. **State Space Partitioning**: States divided into chunks (e.g., 2048 states per chunk for 2 workers)
2. **Per-Worker Visited Sets**: Each worker has `local_visited` set (not shared)
3. **Cycle Spanning**: Large cycles (e.g., period 4095) span multiple chunks
4. **Redundancy**: Multiple workers process the same cycle because:
   - Worker 0 processes state X (in chunk 0), finds cycle, marks all 4095 states in `local_visited[0]`
   - Worker 1 processes state Y (in chunk 1, same cycle), doesn't see `local_visited[0]`, processes entire cycle again
5. **Result**: 2x (or more) redundant work, worse performance

### Evidence from Profiling
- **12-bit LFSR (4096 states)**:
  - Sequential: 0.49s
  - 2 workers: 0.91s (1.85x slower!)
  - Redundancy: Period-4095 cycle found by workers 0 and 1
- **Worker Statistics**:
  - Worker 0: 2 states processed, 2 sequences found
  - Worker 1: 1 state processed, 1 sequence found
  - But both found the same large cycle (period 4095)

---

## Solution Options

### Option A: Shared Visited Set with Lock
**Approach**: Use `multiprocessing.Manager().dict()` for shared visited set

**Pros**:
- Simple concept
- Workers can check if cycle is already being processed
- Prevents all redundancy

**Cons**:
- Lock contention (every state check needs lock)
- Performance overhead (lock acquisition/release)
- Could become bottleneck with many workers

**Implementation**:
```python
# In main process
manager = multiprocessing.Manager()
shared_visited = manager.dict()  # min_state_tuple -> worker_id

# In worker
if min_state_tuple in shared_visited:
    # Another worker is processing this cycle
    continue
else:
    # Acquire lock, check again, add if not present
    with lock:
        if min_state_tuple not in shared_visited:
            shared_visited[min_state_tuple] = worker_id
            # Process cycle
```

**Performance Impact**: Lock contention could make this slower than current approach.

---

### Option B: Shared Cycle Registry (Lightweight)
**Approach**: Shared set of cycle signatures (min_state), checked only when cycle is found

**Pros**:
- Minimal lock contention (only when cycle found, not per-state)
- Workers still use local_visited for fast path
- Prevents redundancy without major overhead

**Cons**:
- Still need to compute period/min_state before check (but we do this anyway)
- Some redundant period computation possible (but not full cycle processing)

**Implementation**:
```python
# In main process
manager = multiprocessing.Manager()
shared_cycles = manager.dict()  # min_state_tuple -> True

# In worker (after computing period and min_state)
min_state_tuple = tuple(min_state)
if min_state_tuple in shared_cycles:
    # Another worker already processed this cycle
    debug_log(f'Cycle with min_state {min_state_tuple} already processed, skipping')
    local_visited.add(state_tuple)  # Mark start state to skip
    continue
else:
    # Try to claim this cycle
    with lock:
        if min_state_tuple not in shared_cycles:
            shared_cycles[min_state_tuple] = True
            # Process and store cycle
        else:
            # Another worker claimed it first
            continue
```

**Performance Impact**: Minimal - only checks when cycle is found, not per-state.

---

### Option C: Min_State Chunk Ownership (Fixed)
**Approach**: Only process cycle if min_state is in this worker's chunk

**Pros**:
- No shared state needed
- Clean logic
- No lock contention

**Cons**:
- Need to compute min_state BEFORE processing (we do this anyway for deduplication)
- For cycles with period > 1000, min_state might be incomplete (we limit to 1000 states)
- **This was the flawed approach we removed!**

**Why It Failed Before**:
- We computed min_state from first 1000 states only
- For period 4095, true min_state might be in states 1001-4095
- Wrong min_state → wrong chunk assignment → redundancy persists

**Could It Work?**:
- If we compute FULL min_state (all 4095 states), it would work
- But computing full min_state is expensive and defeats the purpose
- **Not viable for large cycles**

---

### Option D: Two-Phase Processing
**Approach**: 
- Phase 1: Quick scan to identify cycle boundaries/min_states (lightweight)
- Phase 2: Assign cycles to workers, process assigned cycles only

**Pros**:
- Clean separation
- No redundancy

**Cons**:
- Two passes (overhead)
- Complex implementation
- Phase 1 still needs to identify cycles (similar work)

---

## Recommended Solution: Option B (Shared Cycle Registry)

### Design Rationale

1. **Minimal Overhead**: Only checks shared set when cycle is found (not per-state)
2. **Leverages Existing Work**: We already compute period and min_state for deduplication
3. **Prevents Redundancy**: Workers check before processing full cycle
4. **Scalable**: Lock contention is minimal (only when cycles are found)

### Detailed Design

#### Phase 1: Setup (Main Process)
```python
def lfsr_sequence_mapper_parallel(...):
    # ... existing code ...
    
    # Create shared cycle registry
    manager = multiprocessing.Manager()
    shared_cycles = manager.dict()  # min_state_tuple -> worker_id (who claimed it)
    cycle_lock = manager.Lock()  # Lock for atomic check-and-set
    
    # Pass to workers via chunk_data
    chunk_data = (
        chunk,
        coeffs_vector,
        gf_order,
        d,
        algorithm,
        period_only,
        worker_id,
        shared_cycles,  # NEW
        cycle_lock,     # NEW
    )
```

#### Phase 2: Worker Logic
```python
def _process_state_chunk(chunk_data):
    # ... unpack chunk_data ...
    shared_cycles, cycle_lock = chunk_data[-2:]  # NEW
    
    # ... existing code ...
    
    for state_tuple, state_idx in state_chunk:
        if state_tuple in local_visited:
            continue  # Fast path: already visited locally
        
        # ... compute period and min_state (existing code) ...
        
        # NEW: Check if cycle is already being processed
        min_state_tuple = tuple(min_state)
        
        # Fast check (no lock)
        if min_state_tuple in shared_cycles:
            debug_log(f'Cycle {min_state_tuple} already claimed by worker {shared_cycles[min_state_tuple]}, skipping')
            # Mark all states in cycle as visited locally (to skip in this worker)
            local_visited.add(state_tuple)
            current = state
            for _ in range(seq_period - 1):
                current = current * state_update_matrix
                current_tuple = tuple(current)
                local_visited.add(current_tuple)
            continue
        
        # Try to claim cycle (with lock)
        with cycle_lock:
            if min_state_tuple in shared_cycles:
                # Another worker claimed it between check and lock
                debug_log(f'Cycle {min_state_tuple} claimed by another worker, skipping')
                local_visited.add(state_tuple)
                # Mark all states in cycle
                current = state
                for _ in range(seq_period - 1):
                    current = current * state_update_matrix
                    current_tuple = tuple(current)
                    local_visited.add(current_tuple)
                continue
            else:
                # Claim this cycle
                shared_cycles[min_state_tuple] = worker_id
                debug_log(f'Claimed cycle {min_state_tuple} for worker {worker_id}')
        
        # Process cycle (existing code)
        # ... store sequence, mark states as visited ...
```

#### Phase 3: Cleanup
- Shared cycles dict is automatically cleaned up when manager is garbage collected
- No explicit cleanup needed

---

## Implementation Plan

### Step 1: Modify `lfsr_sequence_mapper_parallel`
- Create `multiprocessing.Manager()`
- Create `shared_cycles` dict and `cycle_lock`
- Pass to workers via `chunk_data`

### Step 2: Modify `_process_state_chunk`
- Add `shared_cycles` and `cycle_lock` to function signature
- After computing `min_state`, check `shared_cycles`
- If not present, acquire lock, check again, claim if available
- If claimed by another worker, skip and mark states as visited

### Step 3: Update Chunk Data Preparation
- Add `shared_cycles` and `cycle_lock` to `chunk_data` tuple

### Step 4: Testing
- Run 12-bit profiling script
- Verify: No redundancy, correct results, better performance
- Test with 1, 2, 4, 8 workers

### Step 5: Edge Cases
- Handle case where min_state computation is incomplete (period > 1000)
- Consider: If min_state is from first 1000 states only, might have collisions
- Solution: Use full min_state computation for cycles with period <= 1000, accept some redundancy for larger cycles (rare)

---

## Expected Outcomes

### Performance
- **12-bit LFSR**: Should see speedup with 2+ workers (currently slower)
- **Overhead**: Minimal (only lock when cycle found, not per-state)
- **Scalability**: Should scale better with more workers

### Correctness
- **No Redundancy**: Each cycle processed exactly once
- **Correct Results**: Should match sequential exactly

### Metrics to Track
- Lock contention (time spent waiting for lock)
- Cycles claimed vs skipped
- Performance improvement vs sequential

---

## Alternative: Hybrid Approach

If Option B shows lock contention issues, we can optimize:

1. **Batch Claiming**: Workers claim multiple cycles at once (reduce lock acquisitions)
2. **Lock-Free Check**: Use atomic operations for check (if available)
3. **Per-Worker Claiming**: Each worker has a "claiming queue", main process batches updates

But start with Option B (simplest) and optimize if needed.

---

## Risk Assessment

### Low Risk
- Adding shared state is straightforward
- Lock is only acquired when cycle is found (infrequent)
- Existing code structure supports this change

### Medium Risk
- Lock contention if many cycles found simultaneously
- Manager overhead (but should be minimal)

### Mitigation
- Profile lock contention
- If high, consider batching or lock-free alternatives
- Monitor performance to ensure improvement

---

## Success Criteria

1. ✅ **No Redundancy**: Profiling shows 0 redundant cycles
2. ✅ **Correct Results**: Parallel results match sequential exactly
3. ✅ **Performance Improvement**: 2 workers faster than sequential (currently slower)
4. ✅ **Scalability**: Performance improves with more workers (up to reasonable limit)

---

## Next Steps

1. Review this design
2. Implement Option B (Shared Cycle Registry)
3. Test and profile
4. Optimize if needed
