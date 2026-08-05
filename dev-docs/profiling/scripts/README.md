# Profiling Scripts

Standalone scripts written to measure specific performance questions during
the parallel-enumeration work (see [`../README.md`](../README.md)). These
are historical artifacts, not maintained tooling — none of them are run by
`make`, CI, or the test suite, and none are guaranteed to run unmodified
against the current `app/`-relocated package layout.

| Script | What it measured |
|---|---|
| `analyze_floyd_overhead.py` | Overhead of Floyd's cycle-detection algorithm |
| `benchmark_static_vs_dynamic.py` | Static vs. dynamic worker-thread partitioning |
| `benchmark_strange_csv.py` | Benchmark against the repo's `strange.csv` fixture |
| `detailed_performance_analysis.py` | Fine-grained timing breakdown of enumeration |
| `parallel_performance_profile.py` | General parallel-mode profiling |
| `performance_profile.py` | General (non-parallel-specific) profiling |
| `profile_12bit_parallel.py` | 12-bit LFSR parallel enumeration profiling |
| `profile_14bit_parallel.py` / `_v2.py` | 14-bit LFSR parallel enumeration profiling (two iterations) |
| `profile_16bit.py` | 16-bit LFSR enumeration profiling |
| `profile_phase2_optimizations.py` | Phase 2 optimization impact measurement |

If you need to re-run one of these against the current codebase, expect to
update its imports/paths for the `src/` and `app/` layout moves first.
