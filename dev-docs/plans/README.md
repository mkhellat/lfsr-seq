# Implementation Plans

## Overview

This directory contains all feature plans and implementation documentation, organized by category.

## Structure

- **[parallel/](./parallel/README.md)** - Parallel processing plans
- **[features/](./features/README.md)** - Feature implementation plans
- **[attacks/](./attacks/README.md)** - Attack method plans
- **[analysis/](./analysis/README.md)** - Analysis tool plans
- **[advanced/](./advanced/README.md)** - Advanced feature plans
- **[status/](./status/README.md)** - Status and review documents

## Quick Navigation

### Completed
- [Parallel Enumeration Complete](./parallel/parallel_enumeration_complete.md)
- [Parallel Fork Migration Complete](./parallel/parallel_fork_migration_complete.md)

### In Progress
- [Parallel Optimization Options](./parallel/parallel_optimization_options.md)

### Planned (at time of writing — all five below are now implemented)
- [Period Only Mode Plan](./features/period_only_mode_plan.md) — implemented (`--period-only` flag)
- [Optimization Techniques Plan](./features/optimization_techniques_plan.md) — implemented (`app/src/lfsr/optimization.py`)
- [Correlation Attack Framework](./attacks/correlation_attack_framework_plan.md) — implemented (`app/src/lfsr/cli_correlation.py`, `app/src/lfsr/attacks.py`)
- [Fast Correlation Attack](./attacks/fast_correlation_attack_plan.md) — implemented (`--fast-correlation-attack`)
- [Theoretical Analysis Plan](./analysis/theoretical_analysis_plan.md) — implemented (`app/src/lfsr/theoretical.py`, `app/src/lfsr/theoretical_db.py`)

### Status & Reviews
- [Final Status](./status/final_status.md)
- [Review and Improvement Plan](./status/review_and_improvement_plan.md)
- [Phase 1 Implementation Documentation](./status/phase1_implementation_documentation.md)

## Related Documentation

- [Main Documentation Index](../README.md)
- [Parallel Processing Docs](../parallel/README.md)
- [Setup Documentation](../setup/README.md)
