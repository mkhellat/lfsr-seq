# Performance Investigation Reports

## Overview

Investigation reports analyzing parallel execution correctness, performance, and overhead.

## Documents

### [investigation_results.md](./investigation_results.md)
**Correctness and performance investigation**

Detailed investigation answering three questions:
1. Are parallel results correct? (Yes - all workers match sequential)
2. What is the speedup? (2 workers: 2.51x best)
3. Why are 4/8 workers slower? (Severe load imbalance: 267-620%)

### [performance_analysis.md](./performance_analysis.md)
**General performance analysis**

Analysis of parallel execution performance, including timing breakdown, overhead analysis, and performance bottlenecks.

### [parallel_overhead_analysis.md](./parallel_overhead_analysis.md)
**Parallel execution overhead analysis**

Detailed analysis of overhead in parallel execution, including process creation, IPC, and synchronization costs.
