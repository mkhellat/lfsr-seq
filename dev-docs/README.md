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
- **Batch Aggregation (Phase 2.2)**: IPC overhead reduction through batch aggregation
  - Workers pull multiple batches at once (2-8 batches per operation)
  - Non-blocking operations with fallback for better CPU utilization
  - Reduces queue operations by 2-8x, provides 1.2-1.5x speedup
- **Comprehensive Profiling**: 12-bit, 14-bit, and 16-bit LFSR profiling results available
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
