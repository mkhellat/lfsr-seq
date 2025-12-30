# Performance Profiling Results

## Overview

Detailed profiling results for specific LFSR sizes and configurations.

## Documents

### [14bit_profiling_results.md](./14bit_profiling_results.md)
**14-bit LFSR (16,384 states) profiling results**

Complete profiling of 14-bit LFSR with primitive polynomial x^14 + x^5 + x^3 + x + 1. Shows that 1 worker is optimal (1.31x speedup), with severe load imbalance for 4+ workers (400-683%).

### [12bit_profiling_results.md](./12bit_profiling_results.md)
**12-bit LFSR (4,096 states) profiling results**

Profiling results for 12-bit LFSR showing 2 workers achieve 2.51x speedup, with load imbalance increasing from 168% (2w) to 620% (8w).

### [phase2_results.md](./phase2_results.md)
**Phase 2 load balancing improvements**

Results from Phase 2 improvements including work distribution profiling and auto-selection of optimal worker count. Shows load imbalance evidence and performance results.

### [final_results.md](./final_results.md)
**Final results summary**

Complete summary of Phase 1 (correctness fix) and Phase 2 (load balancing) results, with performance comparison and conclusions.
