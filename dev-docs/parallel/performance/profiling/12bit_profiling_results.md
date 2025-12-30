# 12-Bit LFSR Parallel Execution Profiling Report
**LFSR**: 12-bit, primitive polynomial x^12 + x^6 + x^4 + x + 1
**Total States**: 4095
**Algorithm**: enumeration
**Period-Only Mode**: True

## Executive Summary

| Workers | Time (s) | Speedup | Efficiency | Correct | No Redundancy |
|---------|----------|--------|-----------|---------|---------------|
| Sequential | 0.5294 | 1.00x | - | ✓ | ✓ |
| 1 | 0.3487 | 1.52x | 151.8% | ✗ | ✓ |
| 2 | 0.3631 | 1.46x | 72.9% | ✗ | ✓ |
| 4 | 0.5900 | 0.90x | 22.4% | ✗ | ✓ |
| 8 | 0.9106 | 0.58x | 7.3% | ✗ | ✓ |

## Performance Breakdown

### 1 Workers

**Total Time**: 0.3487s
**Speedup**: 1.52x
**Efficiency**: 151.8%

**Time Breakdown**:

| Stage | Time (s) | Percentage |
|-------|----------|------------|
| Partitioning | 0.0070 | 2.0% |
| Prepare Data | 0.0249 | 7.2% |
| Pool Creation | 0.0073 | 2.1% |
| Submit Tasks | 0.0000 | 0.0% |
| Worker Execution | 0.3014 | 86.4% |
| Merging | 0.0000 | 0.0% |

**Per-Worker Statistics**:

| Worker | States Processed | Sequences Found | Max Period | Errors |
|--------|------------------|-----------------|------------|--------|
| 0 | 2 | 2 | 4095 | 0 |

### 2 Workers

**Total Time**: 0.3631s
**Speedup**: 1.46x
**Efficiency**: 72.9%

**Time Breakdown**:

| Stage | Time (s) | Percentage |
|-------|----------|------------|
| Partitioning | 0.0076 | 2.1% |
| Prepare Data | 0.0095 | 2.6% |
| Pool Creation | 0.0114 | 3.1% |
| Submit Tasks | 0.0001 | 0.0% |
| Worker Execution | 0.3280 | 90.3% |
| Merging | 0.0000 | 0.0% |

**Per-Worker Statistics**:

| Worker | States Processed | Sequences Found | Max Period | Errors |
|--------|------------------|-----------------|------------|--------|
| 0 | 2 | 2 | 4095 | 0 |
| 1 | 0 | 0 | 0 | 0 |

### 4 Workers

**Total Time**: 0.5900s
**Speedup**: 0.90x
**Efficiency**: 22.4%

**Time Breakdown**:

| Stage | Time (s) | Percentage |
|-------|----------|------------|
| Partitioning | 0.0082 | 1.4% |
| Prepare Data | 0.0091 | 1.5% |
| Pool Creation | 0.0180 | 3.1% |
| Submit Tasks | 0.0001 | 0.0% |
| Worker Execution | 0.5431 | 92.1% |
| Merging | 0.0000 | 0.0% |

**Per-Worker Statistics**:

| Worker | States Processed | Sequences Found | Max Period | Errors |
|--------|------------------|-----------------|------------|--------|
| 0 | 2 | 2 | 4095 | 0 |
| 1 | 1 | 1 | 4095 | 0 |
| 2 | 0 | 0 | 0 | 0 |
| 3 | 1 | 1 | 4095 | 0 |

### 8 Workers

**Total Time**: 0.9106s
**Speedup**: 0.58x
**Efficiency**: 7.3%

**Time Breakdown**:

| Stage | Time (s) | Percentage |
|-------|----------|------------|
| Partitioning | 0.0149 | 1.6% |
| Prepare Data | 0.0133 | 1.5% |
| Pool Creation | 0.0505 | 5.5% |
| Submit Tasks | 0.0001 | 0.0% |
| Worker Execution | 0.8186 | 89.9% |
| Merging | 0.0000 | 0.0% |

**Per-Worker Statistics**:

| Worker | States Processed | Sequences Found | Max Period | Errors |
|--------|------------------|-----------------|------------|--------|
| 0 | 1 | 1 | 1 | 0 |
| 1 | 1 | 1 | 4095 | 0 |
| 2 | 1 | 1 | 4095 | 0 |
| 3 | 1 | 1 | 4095 | 0 |
| 4 | 1 | 1 | 4095 | 0 |
| 5 | 1 | 1 | 4095 | 0 |
| 6 | 1 | 1 | 4095 | 0 |
| 7 | 0 | 0 | 0 | 0 |

## Correctness Analysis

### 1 Workers

✗ **FAIL**: Mismatch detected

- Extra cycles: 2

### 2 Workers

✗ **FAIL**: Mismatch detected

- Extra cycles: 2

### 4 Workers

✗ **FAIL**: Mismatch detected

- Extra cycles: 4

### 8 Workers

✗ **FAIL**: Mismatch detected

- Extra cycles: 7

## Redundancy Analysis

### 1 Workers

✓ **No redundancy detected**: Each cycle processed by exactly one worker

### 2 Workers

✓ **No redundancy detected**: Each cycle processed by exactly one worker

### 4 Workers

✓ **No redundancy detected**: Each cycle processed by exactly one worker

### 8 Workers

✓ **No redundancy detected**: Each cycle processed by exactly one worker

## Recommendations

- **Optimal worker count**: 1 workers (speedup: 1.52x)
- **Correctness issues**: Results don't match sequential execution
