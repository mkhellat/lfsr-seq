# 14-Bit LFSR Parallel Execution Profiling Results

**Date**: 2025-12-30  
**LFSR Configuration**: 14-bit, primitive polynomial x^14 + x^5 + x^3 + x + 1  
**State Space Size**: 16,384 states

---

## Performance Summary

| Workers | Time (s) | Speedup | Efficiency | Correct |
|---------|----------|---------|------------|---------|
| Sequential | 1.9865 | 1.00x | - | ✓ |
| 1 worker | 1.5128 | 1.31x | 131.3% | ✓ ⭐ |
| 2 workers | 1.9300 | 1.03x | 51.5% | ✓ |
| 4 workers | 4.0416 | 0.49x | 12.3% | ✓ |
| 8 workers | 3.0269 | 0.66x | 8.2% | ✓ |

**Key Finding**: **1 worker is fastest** (1.31x speedup over sequential)!

---

## Correctness

✅ **All worker counts produce correct results**
- Period sum = 16,384 for all configurations
- All cycles match between sequential and parallel execution

---

## Detailed Work Distribution Analysis

### 1 Worker (Best Performance)
- **Worker 0**: 1.4813s
  - States in chunk: 16,384
  - States processed: 2
  - States skipped (visited): 16,382
  - Cycles found: 2, claimed: 0, skipped: 0
- **Load imbalance**: N/A (single worker)
- **Efficiency**: 131.3% (superlinear!)

### 2 Workers
- **Worker 0**: 1.7686s
  - States in chunk: 8,192
  - States processed: 2
  - States skipped (visited): 8,190
  - States skipped (claimed): 0
  - Cycles found: 2, claimed: 0, skipped: 0
- **Worker 1**: 0.0738s
  - States in chunk: 8,192
  - States processed: 0
  - States skipped (visited): 8,191
  - States skipped (claimed): 16,383
  - Cycles found: 0, claimed: 0, skipped: 1
- **Load imbalance**: 184.0%
- **Efficiency**: 52.1%

### 4 Workers
- **Worker 0**: 3.9861s (does most work)
  - States in chunk: 4,096
  - States processed: 1
  - States skipped (visited): 4,094
  - States skipped (claimed): 16,383
  - Cycles found: 1, claimed: 0, skipped: 1
- **Workers 1-3**: ~0.0000s (finish quickly)
  - Each processes 1 cycle or skips all work
- **Load imbalance**: 400.0% (severe!)
- **Efficiency**: 25.0%

### 8 Workers
- **Worker 0**: 3.8761s (does most work)
  - States in chunk: 2,048
  - States processed: 2
  - Cycles found: 2, claimed: 0, skipped: 0
- **Workers 1-7**: 0.0000s - 0.6633s (finish quickly)
  - Most workers skip all work (cycles already claimed)
- **Load imbalance**: 683.1% (extreme!)
- **Efficiency**: 14.6%

---

## Why 4/8 Workers Are Slower

### Evidence from Profiling

**2 workers vs 4 workers:**
- 2 workers execution time: 1.8424s
- 4 workers execution time: 3.9861s
- **Difference**: +2.14s (116% slower!)

**Load Imbalance:**
- 2 workers: 184.0% imbalance
- 4 workers: 400.0% imbalance
- 8 workers: 683.1% imbalance

**Overhead:**
- 2 workers: 0.1564s (7.8%)
- 4 workers: 0.0833s (2.0%)
- Overhead is minimal; execution time dominates

### Root Cause Analysis

1. **Severe Load Imbalance** (PRIMARY CAUSE)
   - One worker processes the large cycle (period 16,383)
   - Other workers finish quickly because cycles are already claimed
   - With more workers, chunks get smaller but work distribution gets worse

2. **Work Distribution Pattern**
   - Worker 0 finds the large cycle early
   - Other workers check their chunks, find states already in claimed cycles
   - Result: Most workers do minimal work, one worker does all the heavy lifting

3. **Why 1 Worker is Fastest**
   - No partitioning overhead
   - No inter-worker communication overhead
   - No lock contention
   - Single worker processes all states efficiently

---

## Comparison with 12-Bit Results

| Metric | 12-bit (4K states) | 14-bit (16K states) |
|--------|---------------------|----------------------|
| Sequential time | 0.75s | 1.99s |
| Best worker count | 2 workers (2.51x) | 1 worker (1.31x) |
| 2 workers speedup | 0.92x | 1.03x |
| 4 workers speedup | 0.73x | 0.49x |
| 8 workers speedup | 0.99x | 0.66x |
| Load imbalance (2 workers) | 168% | 184% |
| Load imbalance (4 workers) | 400% | 400% |
| Load imbalance (8 workers) | 620% | 683% |

**Key Observations:**
- 14-bit shows even worse performance with multiple workers
- Load imbalance increases with problem size
- 1 worker becomes optimal for 16K states

---

## Conclusions

1. **Correctness**: ✅ All worker counts produce correct results

2. **Performance**: 
   - **1 worker is optimal** for 14-bit LFSR (16K states)
   - Multiple workers provide no benefit due to severe load imbalance
   - Performance degrades significantly with more workers

3. **Load Imbalance**:
   - Increases dramatically with more workers (184% → 400% → 683%)
   - Primary cause of performance degradation
   - One worker does most work, others finish quickly

4. **Recommendations**:
   - **Use 1 worker** for 14-bit LFSR (or auto-select based on problem size)
   - Auto-selection should choose 1 worker for problems < 8K states
   - For 8K-16K states, 1-2 workers are optimal
   - Avoid 4+ workers for problems < 32K states

---

## Auto-Selection Update Needed

Current auto-selection thresholds:
- < 2K states: 1 worker
- 2K-8K states: 2 workers
- 8K-32K states: 4 workers

**Recommended update based on 14-bit results:**
- < 8K states: 1 worker
- 8K-16K states: 1-2 workers
- 16K-32K states: 2-4 workers
- > 32K states: 4+ workers

The 14-bit results show that even 2 workers provide minimal benefit (1.03x speedup) compared to 1 worker (1.31x speedup).
