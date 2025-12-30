# Parallel Processing Optimization Options

**Date**: 2025-01-XX  
**Status**: Analysis Document  
**Problem**: Parallel processing is 4-6x SLOWER than sequential due to overhead

---

## Current Bottleneck Analysis

From profiling (6-bit LFSR, 2 workers):
- **State Space Partitioning**: 60.6% of time (converting VectorSpace to tuples)
- **Multiprocessing Pool**: 38.2% of time (process creation/termination)
- **Worker Processing**: 1.2% of time (actual computation)

**Key Insight**: The actual computation is FAST (1.2%), but overhead dominates (98.8%)!

---

## Optimization Options

### Option 1: Use Fork Instead of Spawn (Linux) ⭐ RECOMMENDED

**Current Issue**: We switched to `spawn` to avoid SageMath category mismatch errors, but spawn is slower.

**Solution**: Use `fork` (Linux default) but fix SageMath initialization more carefully:
- Fork is 10-100x faster for process creation (no Python interpreter startup)
- SageMath objects are inherited (no re-initialization needed)
- Category mismatch errors can be avoided by not sharing SageMath objects between processes

**Implementation**:
```python
# Use fork on Linux (faster), spawn on Windows/Mac
if sys.platform == 'linux':
    ctx = multiprocessing.get_context('fork')
else:
    ctx = multiprocessing.get_context('spawn')
```

**Expected Speedup**: 2-4x (eliminates process creation overhead)

**Risk**: Low - fork is the default on Linux anyway

---

### Option 2: Use Threading Instead of Multiprocessing ⭐⭐ HIGHEST POTENTIAL

**Key Insight**: Python's GIL prevents true parallelism for CPU-bound tasks, BUT:
- SageMath matrix operations may release the GIL (need to verify)
- Threading has ZERO process creation overhead
- Threading has minimal IPC overhead (shared memory)

**Test First**:
```python
import threading
from concurrent.futures import ThreadPoolExecutor

# Test if SageMath releases GIL
# If yes, threading could be 10x faster than multiprocessing
```

**Expected Speedup**: 5-10x if GIL is released, 0x if not

**Risk**: Medium - Need to verify GIL behavior

---

### Option 3: Use Joblib (Better Overhead) ⭐

**Why**: Joblib is optimized for scientific computing and has better overhead:
- Better process/thread management
- Can use threading or multiprocessing
- Better memory sharing
- Optimized for NumPy/SciPy (SageMath uses similar)

**Implementation**:
```python
from joblib import Parallel, delayed

results = Parallel(n_jobs=num_workers)(
    delayed(_process_state_chunk)(chunk_data) 
    for chunk_data in chunk_data_list
)
```

**Expected Speedup**: 1.5-3x (better overhead management)

**Risk**: Low - joblib is well-tested

---

### Option 4: Pre-initialize Worker Pool (Persistent Workers)

**Current Issue**: Workers are created/destroyed for each run, causing overhead.

**Solution**: Use a persistent worker pool that stays alive:
- SageMath initialized once per worker (not per task)
- Process creation overhead eliminated
- Workers can be reused across multiple LFSRs

**Implementation**:
```python
# Create persistent pool
_pool = None

def get_pool(num_workers):
    global _pool
    if _pool is None:
        _pool = multiprocessing.Pool(processes=num_workers)
    return _pool
```

**Expected Speedup**: 2-3x (amortize process creation)

**Risk**: Low - standard pattern

---

### Option 5: Larger Chunks (Better Amortization)

**Current Issue**: Small chunks mean overhead dominates.

**Solution**: Make chunks much larger:
- Current: ~256 states per chunk (for 1024 states, 4 workers)
- Better: ~1000+ states per chunk
- Overhead is amortized over more work

**Expected Speedup**: 1.5-2x

**Risk**: Low - simple change

---

### Option 6: Shared Memory for Visited Set

**Current Issue**: Each worker has its own visited set, causing duplicate work.

**Solution**: Use `multiprocessing.shared_memory` for shared visited set:
- Workers can check if state is already processed
- Reduces duplicate work
- But adds synchronization overhead

**Expected Speedup**: 1.2-1.5x (if duplicate work is significant)

**Risk**: Medium - synchronization complexity

---

### Option 7: Hybrid Approach (Threading + Multiprocessing)

**Strategy**: 
- Use threading for small/medium LFSRs (low overhead)
- Use multiprocessing for large LFSRs (true parallelism if needed)
- Auto-select based on state space size

**Expected Speedup**: 2-5x (best of both worlds)

**Risk**: Medium - complexity

---

### Option 8: SageMath Native Parallel

**Investigation Needed**: Does SageMath have built-in parallel capabilities?
- `sage.parallel` module exists
- May have parallel matrix operations
- May have parallel polynomial operations

**Expected Speedup**: Unknown (need to investigate)

**Risk**: High - may not be applicable to our use case

---

## Recommended Approach

### Phase 1: Quick Wins (Low Risk, High Impact)
1. **Use fork instead of spawn** (Option 1) - 2-4x speedup
2. **Larger chunks** (Option 5) - 1.5-2x speedup
3. **Pre-initialize pool** (Option 4) - 2-3x speedup

**Combined Expected**: 6-24x speedup (but multiplicative, so probably 4-8x)

### Phase 2: Test Threading (High Potential)
4. **Test if SageMath releases GIL** - If yes, threading could be 10x faster
5. **Implement threading if GIL is released** - Massive speedup

### Phase 3: Advanced (If Needed)
6. **Joblib** - If threading doesn't work
7. **Shared memory** - If duplicate work is significant

---

## Testing Plan

1. **Test fork vs spawn overhead**:
   ```python
   # Measure process creation time
   # fork: ~0.1ms, spawn: ~10-50ms
   ```

2. **Test GIL release**:
   ```python
   # Run SageMath operations in threads
   # Check if CPU usage > 100% (indicates parallelism)
   ```

3. **Benchmark each option**:
   - Small LFSR (1024 states)
   - Medium LFSR (32768 states)
   - Large LFSR (1M+ states)

---

## Decision Matrix

| Option | Expected Speedup | Risk | Effort | Priority |
|--------|----------------|------|--------|----------|
| Fork instead of spawn | 2-4x | Low | Low | ⭐⭐⭐ |
| Threading (if GIL released) | 5-10x | Medium | Medium | ⭐⭐⭐ |
| Joblib | 1.5-3x | Low | Low | ⭐⭐ |
| Pre-initialize pool | 2-3x | Low | Low | ⭐⭐ |
| Larger chunks | 1.5-2x | Low | Low | ⭐ |
| Shared memory | 1.2-1.5x | Medium | Medium | ⭐ |
| SageMath native | Unknown | High | High | ⭐ |

---

## Next Steps

1. **Immediate**: Test fork vs spawn overhead
2. **Critical**: Test if SageMath releases GIL (threading test)
3. **Quick wins**: Implement fork + larger chunks + pre-initialize pool
4. **If threading works**: Implement threading version
5. **If threading doesn't work**: Try joblib
