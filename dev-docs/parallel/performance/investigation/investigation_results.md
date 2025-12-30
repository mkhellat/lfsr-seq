# Parallel Execution Investigation Results

**LFSR**: 12-bit (4096 states)

---

## 1. CORRECTNESS ANALYSIS

### Results Summary

| Workers | Period Sum | Expected | Match | Status |
|---------|------------|----------|-------|--------|
| Sequential | 4096 | 4096 | ✓ | Correct |
| 1 worker | 4096 | 4096 | ✓ | **CORRECT** |
| 2 workers | 4096 | 4096 | ✓ | **CORRECT** |
| 4 workers | 12286 | 4096 | ✗ | **INCORRECT** |
| 8 workers | 24571 | 4096 | ✗ | **INCORRECT** |

### Evidence

**4 Workers Issue:**
- Sequential finds: 2 cycles (period 1, period 4095)
- 4 workers finds: 4 cycles (period 1, period 4095 × 3)
- Period sum: 1 + 4095 + 4095 + 4095 = 12286 (should be 4096)
- **Root Cause**: Same cycle (period 4095) reported 3 times with different min_states

**8 Workers Issue:**
- Sequential finds: 2 cycles (period 1, period 4095)
- 8 workers finds: 7 cycles (period 1, period 4095 × 6)
- Period sum: 1 + 4095×6 = 24571 (should be 4096)
- **Root Cause**: Same cycle (period 4095) reported 6 times with different min_states

### Conclusion

**Correctness**: 
- 1-2 workers: Results are CORRECT
- 4+ workers: Results are INCORRECT due to deduplication failure

**Problem**: The `_merge_parallel_results` function is not properly deduplicating cycles when multiple workers find the same cycle with different min_state values (due to incomplete min_state computation limited to 1000 states).

---

## 2. SPEEDUP ANALYSIS

### Performance Results

| Workers | Time (s) | Speedup | Efficiency | vs Sequential |
|---------|----------|---------|------------|---------------|
| Sequential | 1.2313 | 1.00x | - | Baseline |
| 1 worker | 0.9140 | 1.35x | 134.7% | **1.35x faster** |
| 2 workers | 0.4288 | 2.87x | 143.6% | **2.87x faster** |
| 4 workers | 0.8055 | 1.53x | 38.2% | 1.53x faster (but incorrect) |
| 8 workers | 0.7668 | 1.61x | 20.1% | 1.61x faster (but incorrect) |

### Key Findings

1. **Best Performance**: 2 workers achieve **2.87x speedup** (143.6% efficiency)
2. **1 worker**: 1.35x speedup (overhead from multiprocessing setup)
3. **4+ workers**: Slower than 2 workers despite more parallelism

---

## 3. WHY 4/8 WORKERS ARE SLOWER THAN 2 WORKERS

### Evidence from Profiling

#### 2 Workers
- **Worker execution time**: 0.7854s
- **Max worker time**: 0.5124s
- **Load imbalance**: 61.0%
- **Efficiency**: 76.6%
- **Overhead**: 0.0344s (4.2%)

#### 4 Workers
- **Worker execution time**: 0.5015s
- **Max worker time**: 0.5014s
- **Load imbalance**: 400.0% 
- **Efficiency**: 25.0% 
- **Overhead**: 0.0442s (8.1%)

#### 8 Workers
- **Worker execution time**: 0.7717s
- **Max worker time**: 0.5613s
- **Load imbalance**: 581.9% 
- **Efficiency**: 17.2% 
- **Overhead**: 0.0684s (8.1%)

### Root Causes (Evidence-Based)

#### 1. **Severe Load Imbalance** (PRIMARY CAUSE)

**Evidence**:
- 2 workers: 61% imbalance (acceptable)
- 4 workers: 400% imbalance (severe)
- 8 workers: 582% imbalance (extreme)

**What's happening**:
- Worker 0 processes 2 states, finds 2 cycles → takes 0.5014s
- Workers 1-3 process 1 state each, find 1 cycle each → take ~0.0000s (almost instant)
- **Result**: Total time = max(worker_times) = 0.5014s, but overhead adds up

**Why this happens**:
- With 4 workers, chunks are smaller (1024 states each)
- Worker 0's chunk contains the start of the large cycle (period 4095)
- Workers 1-3's chunks contain states already in cycles claimed by Worker 0
- Workers 1-3 skip most work (cycles already claimed), but Worker 0 does all the heavy lifting
- **The work is not evenly distributed**

#### 2. **Overhead Increase**

**Evidence**:
- 2 workers overhead: 0.0344s (4.2%)
- 4 workers overhead: 0.0442s (8.1%) - **28% increase**
- 8 workers overhead: 0.0684s (8.1%) - **99% increase**

**Components**:
- Pool creation: 0.0175s (4 workers) vs 0.0100s (2 workers) - **75% increase**
- More IPC overhead with more workers
- More shared memory operations

#### 3. **Lock Contention** (MINOR)

**Evidence**: Not directly measured, but:
- With 4+ workers, more workers compete for the same cycles
- Lock acquisition overhead increases
- However, this is likely minor compared to load imbalance

### Conclusion

**Why 4/8 workers are slower:**

1. **PRIMARY**: Severe load imbalance (400-582%)
 - Work is not evenly distributed
 - One worker does most of the work
 - Other workers finish quickly but don't help
 - Total time = max(worker_time) + overhead

2. **SECONDARY**: Increased overhead (28-99% increase)
 - More pool creation overhead
 - More IPC overhead
 - More shared memory operations

3. **MINOR**: Lock contention (if any)
 - Multiple workers competing for cycles
 - But cycles are claimed quickly, so minimal impact

**The fundamental issue**: With more workers, the work becomes more imbalanced because:
- Large cycles span multiple chunks
- Only one worker can claim each cycle
- Other workers in those chunks have less work to do
- Result: Poor load balancing

---

## 4. RECOMMENDATIONS

### Immediate Fixes Needed

1. **Fix Deduplication Bug** (CRITICAL)
 - `_merge_parallel_results` must properly deduplicate cycles
 - Issue: Incomplete min_state computation (limited to 1000 states) causes different min_states for same cycle
 - Solution: Use full min_state computation OR improve deduplication logic

2. **Improve Load Balancing** (PERFORMANCE)
 - Current partitioning by state index doesn't account for cycle distribution
 - Consider: Dynamic work stealing, better partitioning strategy
 - For now: 2 workers is optimal for this problem size

### Performance Recommendations

- **Use 2 workers** for 12-bit LFSR (optimal performance)
- **Use 1 worker** if overhead is a concern (still 1.35x faster than sequential)
- **Avoid 4+ workers** for small problems (load imbalance dominates)

---

## 5. SUMMARY

### Correctness
- 1-2 workers: **CORRECT**
- 4+ workers: **INCORRECT** (deduplication bug)

### Speedup
- 2 workers: **2.87x speedup** (best)
- 1 worker: **1.35x speedup**
- 4+ workers: Slower than 2 workers (load imbalance)

### Why 4/8 Workers Are Slower
1. **Severe load imbalance** (400-582%) - PRIMARY CAUSE
2. **Increased overhead** (28-99% increase) - SECONDARY
3. **Lock contention** (minor, if any)

**Evidence-based conclusion**: Load imbalance is the primary cause. With more workers, work distribution becomes worse because large cycles are claimed by one worker, leaving other workers with little to do.
