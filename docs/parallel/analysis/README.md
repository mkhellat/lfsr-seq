# Parallel Execution Analysis

## Overview

This directory contains analysis documents that explain how parallel execution works and why it behaves the way it does.

## Documents

### [static_threading_analysis.md](./static_threading_analysis.md)
**Why we use static threading and what it means**

Explains that our implementation uses static threading (fixed chunk assignment) and why this causes load imbalance. Confirms that work is partitioned before execution and workers get predetermined chunks.

### [cycle_distribution_impact.md](./cycle_distribution_impact.md)
**How cycle distribution affects load balance**

Shows that different LFSRs with different cycle distributions produce different load imbalance patterns. Confirms that load imbalance depends on how cycles align with static chunk boundaries.

### [dynamic_threading_feasibility.md](./dynamic_threading_feasibility.md)
**Can we migrate to dynamic threading?**

Comprehensive analysis of whether we can migrate from static to dynamic threading (work stealing). Includes feasibility analysis, implementation approaches, performance estimates, and recommendations.
