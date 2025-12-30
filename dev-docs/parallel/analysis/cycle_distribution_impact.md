# Impact of Cycle Distribution on Load Imbalance

## Hypothesis Confirmed 

**Question**: If we use a different 14-bit sequence with a different distribution of cycles, should we see a different imbalance distribution?

**Answer**: **YES!** The load imbalance depends on how cycles align with static chunk boundaries.

---

## Comparison: Two Different 14-Bit LFSRs

### LFSR V1: x^14 + x^5 + x^3 + x + 1
**Coefficients**: [1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0]

### LFSR V2: x^14 + x^10 + x^6 + x + 1
**Coefficients**: [1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]

---

## Load Imbalance Comparison

| Workers | LFSR V1 Imbalance | LFSR V2 Imbalance | Difference |
|---------|-------------------|-------------------|------------|
| 2 workers | 184.0% | **58.4%** | **V2 is 3.15x better!** |
| 4 workers | 400.0% | **226.5%** | **V2 is 1.77x better!** |
| 8 workers | 683.1% | **790.4%** | V1 is 1.16x better |

### Key Findings

1. **2 Workers**: V2 shows **much better** load balance (58.4% vs 184%)
 - V2: Max worker 2.02s, Min worker 0.00s, Average 1.28s
 - V1: Max worker 1.77s, Min worker 0.07s, Average 0.92s
 - **V2's cycles are better distributed across the 2 chunks**

2. **4 Workers**: V2 shows **better** load balance (226.5% vs 400%)
 - V2: Max worker 2.02s, Min worker 0.00s, Average 0.89s
 - V1: Max worker 3.99s, Min worker 0.00s, Average 1.00s
 - **V2's cycles are better distributed across the 4 chunks**

3. **8 Workers**: V2 shows **worse** load balance (790.4% vs 683%)
 - V2: Max worker 4.32s, Min worker 0.00s, Average 0.55s
 - V1: Max worker 3.88s, Min worker 0.00s, Average 0.57s
 - **With 8 workers, V2's large cycle happens to align poorly with chunk boundaries**

---

## Performance Comparison

| Workers | LFSR V1 Time | LFSR V2 Time | V1 Speedup |
|---------|--------------|--------------|------------|
| Sequential | 1.99s | **4.95s** | V1 is 2.49x faster |
| 1 worker | 1.51s | - | - |
| 2 workers | 1.93s | **3.52s** | V1 is 1.82x faster |
| 4 workers | 4.04s | **3.35s** | **V2 is 1.21x faster!** |
| 8 workers | 3.03s | **4.01s** | V1 is 1.32x faster |

### Observations

1. **Sequential Performance**: V1 is **2.49x faster** than V2
 - Different cycle structures lead to different traversal costs
 - V2's cycle structure may be less cache-friendly or have longer paths

2. **2 Workers**: V1 is faster despite worse load balance
 - V1: 1.93s (184% imbalance)
 - V2: 3.52s (58.4% imbalance)
 - **Better load balance doesn't always mean better performance** if sequential cost is higher

3. **4 Workers**: V2 is faster despite worse sequential performance!
 - V1: 4.04s (400% imbalance)
 - V2: 3.35s (226.5% imbalance)
 - **Better load balance can overcome sequential overhead** when imbalance is severe

---

## Why Different Cycle Distributions Cause Different Imbalance

### Static Threading Partitioning

Work is divided by **state indices**, not by cycle structure:
- **2 workers**: Chunk 0 = states 0-8191, Chunk 1 = states 8192-16383
- **4 workers**: Chunk 0 = states 0-4095, Chunk 1 = states 4096-8191, etc.
- **8 workers**: Chunk 0 = states 0-2047, Chunk 1 = states 2048-4095, etc.

### Cycle Alignment Matters

**LFSR V1 (x^14 + x^5 + x^3 + x + 1)**:
- Large cycle (period 16,383) likely starts in Worker 0's chunk
- Worker 0 processes all 16,383 states
- Other workers finish quickly (states already in claimed cycle)
- **Result**: Severe imbalance

**LFSR V2 (x^14 + x^10 + x^6 + x + 1)**:
- Large cycle (period 16,383) may start at a different state
- Better distribution across chunks (for 2-4 workers)
- Worker 0 still does most work, but less extreme
- **Result**: Better balance for 2-4 workers, worse for 8 workers

### The Problem with Static Threading

1. **Fixed Boundaries**: Chunks are determined by state indices, not cycle structure
2. **No Adaptability**: If a large cycle starts in Worker 0's chunk, Worker 0 must process it all
3. **Alignment Dependency**: Performance depends on "luck" - where cycles happen to start
4. **Worker Count Sensitivity**: Different worker counts create different chunk boundaries, leading to different alignment

---

## Conclusions

1. **Hypothesis Confirmed**: Different cycle distributions produce different load imbalance patterns

2. **Load Imbalance is Cycle-Dependent**:
 - V1: 184% (2w) → 400% (4w) → 683% (8w)
 - V2: 58% (2w) → 227% (4w) → 790% (8w)
 - **Pattern differs based on cycle alignment with chunk boundaries**

3. **Better Load Balance ≠ Better Performance**:
 - V2 has better balance for 2-4 workers
 - But V1 is faster overall due to better sequential performance
 - **Exception**: V2 is faster with 4 workers (3.35s vs 4.04s) because imbalance is less severe

4. **Static Threading Limitations**:
 - Performance is **unpredictable** - depends on cycle alignment
 - No way to adapt to actual work distribution
 - Different worker counts can have dramatically different performance

5. **Recommendations**:
 - **Dynamic threading** (work stealing) would eliminate this dependency
 - **Adaptive chunking** could help (start small, redistribute dynamically)
 - **Fewer workers** reduces the impact (1-2 workers for small problems)

---

## Evidence Summary

| Metric | LFSR V1 | LFSR V2 | Conclusion |
|--------|---------|---------|------------|
| Sequential time | 1.99s | 4.95s | V1 faster |
| 2 workers imbalance | 184% | 58% | V2 better balanced |
| 4 workers imbalance | 400% | 227% | V2 better balanced |
| 8 workers imbalance | 683% | 790% | V1 better balanced |
| Best 4-worker time | 4.04s | 3.35s | V2 faster (better balance wins) |

**Key Insight**: Load imbalance is **not just a function of worker count**, but also of **how cycles align with static chunk boundaries**. This confirms that static threading has inherent limitations for this problem.
