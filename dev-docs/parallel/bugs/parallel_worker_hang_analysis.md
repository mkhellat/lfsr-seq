# Parallel Worker Hang Analysis - strange.csv

 
**Status**: Investigation Complete 
**Issue**: Workers hang when processing strange.csv in parallel mode

---

## Problem Summary

When processing `strange.csv` (3 LFSRs) with parallel processing:
- **Sequential**: 50.6s 
- **Parallel (2 workers)**: 115.5s (2.3x SLOWER)
- **Workers timeout**: After 40s, workers are terminated and fallback to sequential

**Root Cause**: Workers hang during period computation, causing timeout and fallback to sequential.

---

## Investigation Results

### Test 1: Sequential Baseline
```
Time: 50.6s
Status: Works correctly
```

### Test 2: Parallel with Debug Output
```
Workers start successfully
SageMath initialization: OK
Matrix reconstruction: OK
State processing starts: OK
Period computation: HANGS at state 2
```

**Observation**: Workers hang when calling `_find_period()` with enumeration algorithm.

---

## Root Cause Analysis

### Issue 1: Enumeration Algorithm in Fork Mode

**Problem**: Enumeration algorithm uses a tight matrix multiplication loop:
```python
for i in range(period):
 current = current * state_update_matrix
 if current == start_state:
 return i + 1
```

**Why it hangs in fork mode**:
1. Fork mode inherits parent's SageMath state
2. Matrix multiplication in tight loops can deadlock with SageMath's internal locks
3. Category mismatch errors can occur with shared SageMath objects
4. Even with fresh objects, tight loops can cause issues

**Solution**: Force Floyd's algorithm in workers (already implemented)

### Issue 2: Min_State Computation Loop

**Problem**: Computing min_state requires iterating through cycle:
```python
for _ in range(max_check - 1):
 current = current * state_update_matrix
 current_tuple = tuple(current)
 if current_tuple < min_state:
 min_state = current_tuple
```

**Why it might hang**:
- Still uses matrix multiplication in a loop
- Even with Floyd for period computation, min_state loop can hang
- Large periods (up to 100 iterations) increase hang probability

**Solution**: Added exception handling and periodic checks (already implemented)

### Issue 3: Multiple LFSR Processing

**Problem**: `strange.csv` contains 3 LFSRs:
1. 10-bit LFSR (1024 states)
2. 15-bit LFSR (32768 states) 
3. 15-bit LFSR (32768 states)

**Issue**: Each LFSR creates a new Pool, but if workers from previous LFSR are still hanging, they could interfere.

**Solution**: Context manager ensures proper cleanup (already implemented)

---

## Current Status

### What Works
- Sequential processing: 50.6s
- Worker initialization: SageMath isolation works
- Fallback mechanism: Times out and falls back to sequential
- Worker termination: Proper cleanup with context manager

### What Doesn't Work
- Parallel processing: Workers hang, timeout, fallback to sequential
- Speedup: Parallel is 2.3x SLOWER than sequential
- Period computation: Hangs even with Floyd's algorithm

---

## Hypothesis

The hang is likely occurring in one of these places:

1. **`_find_period()` with Floyd's algorithm**: Even Floyd might have issues in fork mode
2. **Min_state computation loop**: Matrix multiplication loop for deduplication
3. **SageMath internal locks**: Fork mode may have lock contention issues

---

## Proposed Solutions

### Solution 1: Use Spawn Mode (Not Recommended)
- **Pros**: Avoids fork mode issues
- **Cons**: 13-17x slower process creation, defeats the purpose

### Solution 2: Simplify Deduplication (Recommended)
- **Problem**: Min_state computation requires matrix multiplication loop
- **Solution**: Use simpler deduplication key (period + start_state hash)
- **Trade-off**: Less accurate deduplication, but avoids hangs

### Solution 3: Increase Timeout
- **Problem**: 40s timeout might be too short for large LFSRs
- **Solution**: Increase timeout to 120s for large state spaces
- **Trade-off**: Longer wait before fallback

### Solution 4: Disable Parallel for Multiple LFSRs
- **Problem**: Processing multiple LFSRs creates multiple Pools
- **Solution**: Auto-disable parallel when processing multiple LFSRs
- **Trade-off**: No parallel speedup for batch processing

### Solution 5: Use Threading Instead (If GIL Released)
- **Problem**: Multiprocessing has overhead and hang issues
- **Solution**: Test if SageMath releases GIL, use threading
- **Trade-off**: Only works if GIL is released

---

## Recommended Solution

**Hybrid Approach**:
1. **For single LFSR**: Use parallel with increased timeout (120s)
2. **For multiple LFSRs**: Auto-disable parallel (use sequential)
3. **Simplify deduplication**: Use period + start_state hash instead of min_state
4. **Add progress reporting**: Show which worker is processing which state

---

## Next Steps

1. Test with Floyd's algorithm (done - still hangs)
2. ⏭ Simplify deduplication to avoid min_state loop
3. ⏭ Test with increased timeout
4. ⏭ Consider disabling parallel for multiple LFSRs
5. ⏭ Test threading if SageMath releases GIL

---

## References

- Worker hang investigation: This document
- Fork mode migration: `plans/PARALLEL_FORK_MIGRATION_COMPLETE.md`
- Overhead analysis: `scripts/PARALLEL_OVERHEAD_ANALYSIS.md`
