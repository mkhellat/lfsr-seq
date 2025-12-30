# Parallel Processing Documentation

## Overview

This directory contains all documentation related to parallel execution of LFSR sequence analysis.

## Structure

- **[analysis/](./analysis/README.md)** - Analysis of parallel execution behavior
- **[bugs/](./bugs/README.md)** - Bug reports, fixes, and design documents
- **[performance/](./performance/README.md)** - Performance profiling and benchmarking
- **[implementation/](./implementation/README.md)** - Implementation plans and fixes

## Quick Navigation

### Understanding Parallel Execution
- [Static Threading Analysis](./analysis/static_threading_analysis.md) - Why we use static threading
- [Cycle Distribution Impact](./analysis/cycle_distribution_impact.md) - How cycle distribution affects load balance
- [Dynamic Threading Feasibility](./analysis/dynamic_threading_feasibility.md) - Can we migrate to dynamic threading?

### Performance Results
- [14-bit Profiling Results](./performance/profiling/14bit_profiling_results.md) - Complete 14-bit LFSR profiling
- [12-bit Profiling Results](./performance/profiling/12bit_profiling_results.md) - 12-bit LFSR profiling
- [Phase 2 Results](./performance/profiling/phase2_results.md) - Load balancing improvements
- [Final Results](./performance/profiling/final_results.md) - Complete fix summary

### Bug Fixes
- [Worker Redundancy Logic Flaws](./bugs/worker_redundancy_logic_flaws.md) - Identified flaws in redundancy logic
- [Worker Redundancy Fix Design](./bugs/worker_redundancy_fix_design.md) - Design for fixing redundancy
- [Parallel Bugs and Fixes](./bugs/parallel_bugs_and_fixes.md) - Summary of all bugs and fixes
- [Parallel Worker Hang Analysis](./bugs/parallel_worker_hang_analysis.md) - Analysis of worker hang issues

### Implementation
- [Fix Action Plan](./implementation/fix_action_plan.md) - Action plan for fixing parallel issues
- [Worker Redundancy Fix Plan](./implementation/worker_redundancy_fix_plan.md) - Plan for fixing redundancy
- [Current Parallel Status](./implementation/current_parallel_status.md) - Current status of parallel execution

## Related Documentation

- [Main Documentation Index](../README.md)
- [Parallel Plans](../plans/parallel/README.md)
- [Setup Documentation](../setup/README.md)
