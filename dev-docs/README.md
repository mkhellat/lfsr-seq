# Development Documentation

This directory contains all development documentation, analysis reports, and implementation plans.

**Note**: This is separate from `docs/` which contains Sphinx documentation for the project.

## Recent Updates

### Parallel Processing
- **Dynamic Threading**: Implemented shared task queue model for better load balancing
- **Two Modes Available**: Static (fixed partitioning) and Dynamic (shared task queue)
- **Adaptive Batch Sizing (Phase 2.1)**: Automatic batch size optimization based on problem size
  - Small problems (<8K): 500-1000 states per batch
  - Medium problems (8K-64K): 200-500 states per batch
  - Large problems (>64K): 100-200 states per batch
  - Reduces IPC overhead for small problems, improves load balancing for large problems
  - Verified correct: All results match sequential, metrics are meaningful
- **Batch Aggregation (Phase 2.2)**: IPC overhead reduction through batch aggregation
  - Workers pull multiple batches at once (2-8 batches per operation, adaptive based on problem size)
  - Uses `get_nowait()` (non-blocking) with fallback to blocking `get()` for better CPU utilization
  - Reduces queue operations by 2-8x, provides 1.2-1.5x speedup
  - Verified correct: All results match sequential, batch aggregation working as designed
- **Lazy Task Generation (Phase 2.4)**: On-demand batch generation
  - Generator function creates batches on-demand instead of pre-generating all
  - Background producer thread populates queue as workers consume batches
  - Reduces memory usage (only active batches in memory, O(batch_size * queue_size))
  - Faster startup time (workers can start immediately, no upfront batch generation delay)
  - Better scalability for very large problems (>100K states)
  - Verified correct: All batches generated and processed correctly
- **Persistent Worker Pool (Phase 2.3)**: Worker reuse across analyses
  - Module-level pool that persists across multiple analyses
  - Pool created on first use, reused for subsequent analyses
  - Reduces process creation overhead for repeated analyses
  - Expected 2-3x speedup for multiple analyses
  - 10% speedup observed on second run (tested with 12-bit LFSR, 4 workers)
  - Automatic cleanup on program exit via atexit handler
  - Verified correct: Results match sequential across multiple analyses
- **Comprehensive Profiling**: Phase 2.1 and 2.2 profiling completed
  - Profiled 4-bit, 8-bit, 12-bit, and 14-bit LFSRs
  - Tested with 2, 4, and 8 workers
  - Tested auto and manual batch sizes
  - All results verified correct (100% match with sequential)
  - Key finding: Overhead still dominates for small problems, approaching break-even for medium problems
  - See `scripts/phase2_profiling_analysis.md` for detailed analysis
- **Memory Safety (Critical Fix)**: Fixed memory leak from unbounded queue growth
  - **Queue size limits**: All queues have maxsize=100 to prevent unbounded growth
  - **Producer backpressure**: Producer blocks when queue is full (blocking put with timeout)
  - **Emergency stop**: producer_stop_requested Event allows immediate shutdown
  - **Thread cleanup**: Improved producer thread cleanup with emergency stop mechanism
  - **Memory monitoring**: All test scripts have 4GB memory limits and emergency shutdown
  - **Test runner**: Created `scripts/test_memory_safe.py` for safe test execution
  - Prevents DDoS-like memory exhaustion from queue overflow
  - See `scripts/memory_leak_analysis.md` and `scripts/memory_leak_fixes_summary.md` for details
- **Load Balancing Analysis**: Detailed comparison of static vs dynamic modes
- **Verification**: Correctness and metrics verified for all optimizations
- See [Parallel Processing Documentation](./parallel/README.md) for details

## Quick Navigation

### Core Documentation
- **[Parallel Processing](./parallel/README.md)** - All parallel execution documentation
- **[Plans](./plans/README.md)** - Feature plans and implementation documentation
- **[Setup & Installation](./setup/README.md)** - Building and installation documentation

## Directory Structure

```
dev-docs/
├── parallel/ # Parallel processing documentation
│ ├── analysis/ # Analysis and understanding
│ ├── bugs/ # Bug reports and fixes
│ ├── performance/ # Performance profiling results
│ └── implementation/ # Implementation plans and fixes
├── plans/ # Feature and implementation plans
│ ├── parallel/ # Parallel processing plans
│ ├── features/ # Feature plans
│ ├── attacks/ # Attack method plans
│ ├── analysis/ # Analysis tool plans
│ ├── advanced/ # Advanced feature plans
│ └── status/ # Status and review documents
└── setup/ # Setup and installation docs
 ├── BUILDING.md # Building Sphinx documentation
 └── INSTALLATION_LOCATION.md # Installation location details
```

## Finding Documentation

### By Topic

**Parallel Processing:**
- [Understanding Static Threading](./parallel/analysis/static_threading_analysis.md)
- [Cycle Distribution Impact](./parallel/analysis/cycle_distribution_impact.md)
- [Dynamic Threading Feasibility](./parallel/analysis/dynamic_threading_feasibility.md)
- [14-bit Profiling Results](./parallel/performance/profiling/14bit_profiling_results.md)
- [Worker Redundancy Fix Design](./parallel/bugs/worker_redundancy_fix_design.md)

**Implementation Plans:**
- [Parallel State Enumeration Plan](./plans/parallel/parallel_state_enumeration_plan.md)
- [Period Only Mode Plan](./plans/features/period_only_mode_plan.md)
- [Optimization Techniques Plan](./plans/features/optimization_techniques_plan.md)

**Status & Reviews:**
- [Final Status](./plans/status/final_status.md)
- [Review and Improvement Plan](./plans/status/review_and_improvement_plan.md)

### By Type

**Analysis & Understanding:**
- [Parallel Analysis](./parallel/analysis/README.md)
- [Performance Investigation](./parallel/performance/investigation/README.md)

**Bug Reports & Fixes:**
- [Parallel Bugs](./parallel/bugs/README.md)
- [Implementation Fixes](./parallel/implementation/README.md)

**Profiling Results:**
- [12-bit Profiling](./parallel/performance/profiling/12bit_profiling_results.md)
- [14-bit Profiling](./parallel/performance/profiling/14bit_profiling_results.md)
- [Phase 2 Results](./parallel/performance/profiling/phase2_results.md)


## Related Documentation

- **User Documentation**: See `docs/` for Sphinx-generated user documentation
- **API Reference**: See `docs/api/` for API documentation
- **Code**: See `lfsr/` for source code
