# Phase 2.1 & 2.2 Performance Profiling Report

Generated: 2025-12-31T22:23:40.047489

## Summary

- Total configurations tested: 4
- All results correct: ✓ Yes

## Small Problems

### 4-bit (16 states)

- Sequential: 0.068s

- Dynamic 2w (auto): 0.068s (0.99x speedup)
- Dynamic 4w (auto): 0.082s (0.83x speedup)

### 8-bit (256 states)

- Sequential: 0.023s

- Dynamic 2w (auto): 0.100s (0.23x speedup)
- Dynamic 4w (auto): 0.111s (0.21x speedup)

### 12-bit (4,096 states)

- Sequential: 0.555s

- Dynamic 2w (auto): 1.248s (0.44x speedup)
- Dynamic 4w (auto): 0.975s (0.57x speedup)

## Medium Problems

### 14-bit (16,384 states)

- Sequential: 2.085s

- Dynamic 2w (auto): 2.280s (0.91x speedup)
- Dynamic 4w (auto): 3.840s (0.54x speedup)
- Dynamic 8w (auto): 6.689s (0.31x speedup)
