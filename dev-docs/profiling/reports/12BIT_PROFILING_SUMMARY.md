# 12-bit LFSR Profiling Summary

## Configurations Tested

1. **12-bit-v1**: x^12 + x^6 + x^4 + x + 1 (2 cycles total)
2. **12-bit-v2**: x^12 + x^7 + x^6 + x^2 + 1 (8 cycles total)

## Correctness

✅ **All tests pass** - Both static and dynamic parallel modes produce correct results matching sequential execution.

## Performance Results

### 12-bit-v1 (2 cycles)

| Workers | Mode    | Time (s) | Speedup | Correct | Work Distribution | Imbalance |
|---------|---------|----------|---------|---------|-------------------|-----------|
| 1       | Static  | 0.633    | 0.85x   | ✓       | [2]               | 0.0%      |
| 1       | Dynamic | 0.706    | 0.77x   | ✓       | [2]               | 0.0%      |
| 2       | Static  | 0.620    | 0.87x   | ✓       | [1, 1]            | 0.0%      |
| 2       | Dynamic | 0.547    | 0.99x   | ✓       | [1, 1]            | 0.0%      |
| 4       | Static  | 0.979    | 0.55x   | ✓       | [1, 1, 0, 0]      | 100.0%    |
| 4       | Dynamic | 1.062    | 0.51x   | ✓       | [2, 0, 0, 0]      | 300.0%    |
| 8       | Static  | 0.710    | 0.76x   | ✓       | [1, 1, 0, 0, 0, 0, 0, 0] | 300.0% |
| 8       | Dynamic | 1.849    | 0.29x   | ✓       | [0, 0, 0, 0, 1, 0, 1, 0] | 300.0% |

**Sequential baseline**: 0.541s

### 12-bit-v2 (8 cycles)

| Workers | Mode    | Time (s) | Speedup | Correct | Work Distribution | Imbalance |
|---------|---------|----------|---------|---------|-------------------|-----------|
| 1       | Static  | 0.603    | 0.99x   | ✓       | [8]               | 0.0%      |
| 1       | Dynamic | 0.588    | 1.01x   | ✓       | [8]               | 0.0%      |
| 2       | Static  | 0.649    | 0.92x   | ✓       | [1, 7]            | 75.0%     |
| 2       | Dynamic | 0.711    | 0.84x   | ✓       | [1, 7]            | 75.0%     |
| 4       | Static  | 1.187    | 0.50x   | ✓       | [1, 0, 7, 0]      | 250.0%    |
| 4       | Dynamic | 1.200    | 0.50x   | ✓       | [0, 8, 0, 0]      | 300.0%    |
| 8       | Static  | 0.689    | 0.87x   | ✓       | [1, 6, 0, 0, 0, 1, 0, 0] | 500.0% |
| 8       | Dynamic | 1.592    | 0.37x   | ✓       | [2, 0, 2, 4, 0, 0, 0, 0] | 300.0% |

**Sequential baseline**: 0.597s

## Key Observations

1. **Correctness**: All parallel executions produce correct results matching sequential.

2. **Load Imbalance**:
   - **12-bit-v1**: Perfect balance (0%) for 1w and 2w since there are exactly 2 cycles. Severe imbalance (100-300%) for 4w/8w because only 2 cycles exist, so many workers get 0 cycles.
   - **12-bit-v2**: Moderate imbalance (75%) for 2w, severe (250-500%) for 4w/8w. The 8 cycles are not evenly distributed across workers.

3. **Performance**:
   - Parallel overhead often outweighs benefits for 12-bit LFSRs
   - Best performance: Sequential or 1 worker
   - Dynamic mode shows similar or worse performance than static for 12-bit

4. **Static vs Dynamic**:
   - Both show similar load imbalance patterns
   - Dynamic does not significantly improve load balancing for 12-bit
   - IPC overhead in dynamic mode may contribute to slower performance

## Next Steps

- Profile 14-bit LFSRs (2 configurations)
- Profile 16-bit LFSRs (2 configurations)
- Compare load imbalance patterns across different bit sizes
