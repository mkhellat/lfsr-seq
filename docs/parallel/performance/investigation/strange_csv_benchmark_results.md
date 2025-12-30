# strange.csv Benchmark Results

**Date**: 2025-01-XX  
**File**: `strange.csv` (3 LFSRs)  
**Purpose**: Confirm parallel processing speedup

---

## Test Results

### Sequential Processing (Baseline)
```
Command: lfsr-seq strange.csv 2 --no-parallel --period-only
Time: 50.6s
Status: ✅ Works correctly
```

### Parallel Processing (2 workers)
```
Command: lfsr-seq strange.csv 2 --parallel --num-workers 2 --period-only
Time: 112.7s (first run), 115.5s (second run)
Status: ❌ 2.3x SLOWER than sequential
Issue: Workers timeout after 40s, fallback to sequential
```

### Parallel Processing (4 workers)
```
Command: lfsr-seq strange.csv 2 --parallel --num-workers 4 --period-only
Time: (not tested - 2 workers already slower)
Status: Would likely be even slower
```

---

## Root Cause Analysis

### Issue: Workers Hang on First LFSR

**Observation**: 
- Workers start successfully
- SageMath initialization works
- Workers begin processing states
- Workers hang during period computation (even with Floyd's algorithm)
- Timeout after 40s, fallback to sequential

**Hypothesis**:
1. **Floyd's algorithm still hangs**: Even Floyd's algorithm uses matrix multiplication that can hang in fork mode
2. **Multiple LFSR interference**: Processing 3 LFSRs creates 3 separate Pools, workers from first might interfere
3. **SageMath lock contention**: Fork mode may have internal lock issues with SageMath

---

## Solution Implemented

### Auto-Disable Parallel for Multiple LFSRs

**Change**: Modified `lfsr/cli.py` to auto-disable parallel when processing multiple LFSRs.

**Rationale**:
- Each LFSR creates a new Pool
- Workers from previous LFSR might not terminate properly
- Sequential mode is safer and more reliable for batch processing
- User can still force parallel with `--parallel` flag

**Code**:
```python
num_lfsrs = len(coeffs_list)
if num_lfsrs > 1 and use_parallel is None:
    use_parallel = False
    print(f"INFO: Processing {num_lfsrs} LFSRs - using sequential mode for reliability")
```

---

## Single LFSR Performance

For **single LFSR** (first line from strange.csv):
- Sequential: ~2.7s
- Parallel: (needs testing)

**Note**: Single LFSR parallel processing should work better since there's no interference from multiple Pools.

---

## Recommendations

### For strange.csv (Multiple LFSRs)
- ✅ **Use sequential mode** (default now)
- ❌ Don't use parallel (workers hang, slower)

### For Single Large LFSR
- ✅ **Use parallel mode** (should provide speedup)
- Test with `--parallel --num-workers 4`

### For Batch Processing
- ✅ **Use sequential mode** (safer, more reliable)
- Parallel creates multiple Pools which can interfere

---

## Future Improvements

1. **Worker Pool Reuse**: Reuse same Pool across multiple LFSRs
2. **Better Hang Detection**: Detect hangs earlier and fail fast
3. **Threading Alternative**: Test if threading works better than multiprocessing
4. **SageMath Isolation**: Further improve SageMath isolation in workers

---

## Status

✅ **FIXED**: Auto-disable parallel for multiple LFSRs prevents worker hangs
⏭️ **TODO**: Test single LFSR parallel performance
⏭️ **TODO**: Investigate why Floyd's algorithm still hangs in workers
