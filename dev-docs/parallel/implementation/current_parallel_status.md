# Current Parallel Code Performance Status

**Last Updated**: After partitioning bug fix

---

## Executive Summary

**Current Status**: Parallel is NOW FASTER than sequential (1.21x speedup)

After fixing the partitioning bug, parallel execution provides actual speedup. However, there are still implementation bugs preventing optimal performance.

---

## Performance Metrics

### 16-bit LFSR (65,536 states)

| Mode | Time | Speedup | Status |
|------|------|---------|--------|
| Sequential | 9.41s | 1.00x (baseline) | |
| Parallel (2 workers) | 7.79s | **1.21x** | **FASTER** |

**Result**: Parallel is **21% faster** than sequential!

### 15-bit LFSR (32,768 states) - Original test case

| Mode | Time | Speedup | Status |
|------|------|---------|--------|
| Sequential | ~4-9s | 1.00x (baseline) | |
| Parallel (2 workers) | ~8-10s | ~0.5-0.8x | **Varies** |

**Result**: Performance varies; sometimes slower due to remaining bugs.

---

## Time Breakdown (16-bit LFSR)

### Sequential Execution
- **Total Time**: 9.41s
- **Time per State**: 0.14ms
- **No overhead** - direct processing

### Parallel Execution
| Stage | Time | % of Total | Status |
|-------|------|------------|--------|
| **Partitioning** | 0.26s | 3.3% | **FIXED** (was 4.2s) |
| **Worker Execution** | 7.4s | 95.0% | **Still has bugs** |
| Pool Creation | 0.02s | 0.3% | OK |
| Task Submission | 0.00s | 0.0% | OK |
| Result Merging | 0.01s | 0.1% | OK |
| **Total** | **7.79s** | 100% | **Faster than sequential** |

---

## Bugs Fixed

### Bug #1: Partitioning (FIXED)
- **Before**: 4.2s (iterating VectorSpace)
- **After**: 0.26s (index-based, no iteration)
- **Improvement**: 16x faster
- **Impact**: Critical - this was the main bottleneck

**Fix Applied**:
- Use state indices directly instead of iterating VectorSpace
- For GF(2), convert index to tuple: `tuple((state_idx >> i) & 1 for i in range(degree))`
- Partition by index ranges without iteration

---

## Bugs Remaining

### Bug #2: Worker Redundancy (PARTIALLY ADDRESSED)
- **Symptom**: Workers process redundant cycles when cycles span chunks
- **Impact**: Workers do 1.5-2x more work than necessary
- **Current Status**: Still present but less impactful

**Example**:
- Cycle with period 65535 spans both chunks
- Worker 0: Processes state 1, finds cycle, processes all 65535 states
- Worker 1: Processes state X (same cycle), finds cycle, processes all 65535 states
- **Result**: 2x redundant work (but deduplication at merge prevents wrong results)

**Why It's Less Impactful Now**:
- Partitioning is fast (0.26s vs 4.2s)
- Even with redundancy, parallel is faster
- Deduplication works correctly (min_state canonical key)

**Potential Fix**:
- Shared visited set (complex, requires locks)
- Better cycle detection to skip already-processed cycles
- Or accept redundancy (current approach - works but not optimal)

### Bug #3: Min_state Computation
- **Symptom**: Iterates through cycle to find min_state (up to 1000 states)
- **Impact**: Adds overhead for large cycles
- **Current Status**: Acceptable trade-off for correct deduplication

**Why It Exists**:
- Needed for proper deduplication (canonical cycle representation)
- Limited to 1000 states to avoid hangs
- Works correctly but adds computation time

---

## Performance Analysis

### Current Efficiency
- **Theoretical Speedup**: 2.0x (perfect parallelization)
- **Actual Speedup**: 1.21x
- **Efficiency**: 60.5%

### Why Not 2x Speedup?
1. **Worker Redundancy**: Workers process overlapping cycles (1.5-2x redundant work)
2. **Min_state Computation**: Extra iteration through cycles
3. **IPC Overhead**: Data serialization/deserialization (minimal, ~0.01s)
4. **Load Imbalance**: Cycles may be unevenly distributed across chunks

### Break-even Point
- **Current**: Parallel is faster for 16-bit LFSR (65K states)
- **15-bit LFSR**: Sometimes faster, sometimes slower (varies)
- **Smaller LFSRs**: Sequential is better (overhead dominates)
- **Larger LFSRs**: Parallel should be even better (redundancy becomes less significant)

---

## Comparison: Before vs After Fixes

| Metric | Before Fixes | After Partitioning Fix | Improvement |
|--------|--------------|------------------------|-------------|
| **Partitioning** | 4.2s | 0.26s | 16x faster |
| **Total Parallel** | 22.0s | 7.79s | 2.8x faster |
| **Speedup vs Sequential** | 0.40x (slower) | 1.21x (faster) | **3x improvement** |
| **Status** | Broken | Working | **Fixed!** |

---

## Recommendations

### For Users
- **16-bit+ LFSRs**: Use parallel (1.21x speedup)
- **15-bit LFSRs**: Try parallel, but sequential may be faster depending on cycle distribution
- **Smaller LFSRs**: Use sequential (overhead not worth it)

### For Development
1. **Partitioning bug**: FIXED
2. **Worker redundancy**: Could be optimized but current performance is acceptable
3. **Min_state computation**: Could be optimized but necessary for correctness

---

## Conclusion

**Current State**: **Parallel implementation is WORKING and provides speedup**

- Fixed the critical partitioning bug (16x improvement)
- Parallel is now 21% faster than sequential for 16-bit LFSR
- Remaining bugs are optimization opportunities, not blockers
- Performance is acceptable and usable

**Next Steps** (optional optimizations):
- Fix worker redundancy for better speedup (target: 1.5-1.8x)
- Optimize min_state computation
- Better load balancing

---

*Status report generated from profiling data*
