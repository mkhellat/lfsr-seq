# Development Documentation

This directory contains all development documentation, analysis reports, and implementation plans.

**Note**: This is separate from `docs/` which contains Sphinx documentation for the project.

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

## Recent Updates

- Organized documentation structure into `dev-docs/`
- Added 14-bit profiling results
- Added dynamic threading feasibility analysis
- Moved setup documentation from `docs/`

## Related Documentation

- **User Documentation**: See `docs/` for Sphinx-generated user documentation
- **API Reference**: See `docs/api/` for API documentation
- **Code**: See `lfsr/` for source code
