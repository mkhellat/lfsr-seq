# Worker Redundancy Fix Plan

**Goal**: Fix worker redundancy bug - prevent workers from processing the same cycles

---

## Problem Statement

**Current Behavior**:
- When cycles span chunks, BOTH workers process the ENTIRE cycle
- Worker 0: Processes state 1 (chunk 0), finds cycle period 65535, processes all 65535 states
- Worker 1: Processes state X (chunk 1, same cycle), finds cycle, processes all 65535 states
- **Result**: 2x redundant work!

**Impact**:
- Workers do 1.5-2x more work than necessary
- Prevents optimal speedup (currently 1.48x, could be ~1.8x)

---

## Solution Design

### Core Idea: Only Process Cycles Whose Min_State is in This Worker's Chunk

**Key Insight**: Each cycle has a unique canonical representation (min_state). Only ONE worker should process each cycle - the worker whose chunk contains the min_state.

### Algorithm

1. **Worker receives chunk data**:
 - `state_chunk`: List of (state_tuple, index) pairs
 - Worker can determine its chunk boundaries: `min_idx = min(c[1] for c in state_chunk)`, `max_idx = max(c[1] for c in state_chunk)`

2. **For each state in chunk**:
 - Compute period (already done)
 - Compute min_state (already done, but limited to 1000 states)
 - **NEW**: Convert min_state tuple to state index
 - **NEW**: Check if min_state index is in this worker's chunk range
 - **NEW**: If min_state is NOT in this chunk, SKIP processing (another worker will handle it)

3. **Result**:
 - Only the worker whose chunk contains the min_state processes the cycle
 - Other workers skip it
 - No redundant work!

### Implementation Steps

#### Step 1: Add Helper Function
```python
def tuple_to_state_index(state_tuple: Tuple[int, ...], degree: int, gf_order: int) -> int:
 """Convert state tuple back to state index."""
 if gf_order == 2:
 # Binary to integer
 index = 0
 for i, bit in enumerate(state_tuple):
 index |= (bit << i)
 return index
 else:
 # Base-q to integer
 index = 0
 power = 1
 for digit in state_tuple:
 index += digit * power
 power *= gf_order
 return index
```

#### Step 2: Determine Chunk Boundaries in Worker
```python
# In _process_state_chunk, at the start:
if state_chunk:
 chunk_indices = [idx for _, idx in state_chunk]
 chunk_min_idx = min(chunk_indices)
 chunk_max_idx = max(chunk_indices)
else:
 chunk_min_idx = 0
 chunk_max_idx = 0
```

#### Step 3: Check Min_State Before Processing
```python
# After computing min_state:
min_state_index = tuple_to_state_index(min_state, lfsr_degree, gf_order)

# Check if min_state is in this worker's chunk
if not (chunk_min_idx <= min_state_index < chunk_max_idx + 1):
 # Min_state is in another worker's chunk - skip this cycle
 debug_log(f'State {idx+1}: Min_state {min_state_index} not in chunk [{chunk_min_idx}, {chunk_max_idx}], skipping')
 continue # Skip processing - another worker will handle it
```

#### Step 4: Handle Edge Cases
- **Empty chunks**: Skip
- **Min_state computation limited to 1000 states**: May not find true min_state for large cycles
 - **Solution**: If min_state is not in chunk but we only checked 1000 states, we might have missed the true min_state
 - **Fix**: For cycles with period > 1000, check if ANY state in first 1000 is in chunk
 - **Or**: Accept that we might process some cycles twice, but it's better than processing ALL cycles twice

---

## Expected Impact

### Before Fix
- Both workers process cycles that span chunks
- Worker execution: ~8.7s (redundant work)
- Speedup: 1.48x

### After Fix
- Only one worker processes each cycle
- Worker execution: ~4.4s (half the work)
- Speedup: ~1.8-1.9x (closer to theoretical 2.0x)

### Edge Cases
- **Large cycles (period > 1000)**: Min_state computation is limited to 1000 states
 - May not find true min_state
 - Some cycles might still be processed by multiple workers
 - But this is much better than processing ALL cycles twice

---

## Implementation Considerations

### Performance
- **Tuple to index conversion**: O(d) where d = degree (fast, ~0.001ms per state)
- **Chunk boundary check**: O(1) (simple comparison)
- **Overhead**: Minimal (~0.01s total for 65K states)

### Correctness
- **Min_state is canonical**: All states in same cycle have same min_state
- **Chunk boundaries are known**: Workers can determine from chunk data
- **Edge case**: Large cycles may have min_state beyond first 1000 states
 - **Mitigation**: Check if ANY state in first 1000 is in chunk (more conservative)

### Alternative Approach (More Conservative)
Instead of checking min_state, check if ANY state in the cycle (up to first 1000) is in this worker's chunk:
- If NO states in first 1000 are in this chunk, skip
- This is more conservative and handles large cycles better
- But might skip cycles that should be processed

---

## Testing Plan

1. **Test with 16-bit LFSR**:
 - Verify only one worker processes each cycle
 - Check that results are correct (same sequences, same periods)
 - Measure speedup improvement

2. **Test with 15-bit LFSR**:
 - Verify performance improvement
 - Check for edge cases

3. **Test with cycles that span chunks**:
 - Verify min_state check works correctly
 - Verify no cycles are missed

---

## Rollout Plan

1. Implement helper function `tuple_to_state_index`
2. Add chunk boundary detection in `_process_state_chunk`
3. Add min_state check before processing cycle
4. Test thoroughly
5. Measure performance improvement
6. Commit if successful

---

## Risks

1. **Min_state computation limited**: For large cycles, might not find true min_state
 - **Mitigation**: Use more conservative check (any state in first 1000)
 
2. **Chunk boundaries**: Need to ensure correct calculation
 - **Mitigation**: Use min/max of chunk indices

3. **Edge cases**: Cycles with min_state exactly at chunk boundary
 - **Mitigation**: Use inclusive range check

---

## Success Criteria

- Only one worker processes each cycle
- Results are correct (same as sequential)
- Speedup improves from 1.48x to ~1.8x
- No cycles are missed
- Performance is stable
