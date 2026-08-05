# Profiling Archive

Raw material from the parallel-enumeration performance work described in
[`dev-docs/parallel/`](../parallel/README.md). This directory is a historical
record, not living documentation or a maintained toolset — nothing here is
run by `make`, CI, or the test suite.

- [`scripts/`](scripts/) — standalone profiling/benchmarking scripts
  (`profile_*.py`, `benchmark_*.py`, `performance_profile.py`,
  `analyze_floyd_overhead.py`). Each was written to answer a specific
  performance question at the time; several assume a working directory or
  Python environment from before the `src/` and `app/` layout migrations
  and are not guaranteed to run as-is today.
- [`investigations/`](investigations/) — one-off correctness/behavior
  investigation scripts (`investigate_*.py`, `debug_*.py`, and a handful of
  `test_*.py` files that are standalone scripts, **not** pytest tests —
  the real pytest suite lives in `app/tests/`).
- [`logs/`](logs/) — captured stdout/output logs (`*.log`) and structured
  profiling results (`*.json`) from specific runs of the scripts above.
- [`reports/`](reports/) — write-ups and summaries produced while
  interpreting the profiling/investigation data (phase summaries, memory
  leak analysis, `PROFILING_EVALUATION.md`).

## Why this is kept

This archive isn't required reading — it exists so the raw evidence
behind past parallel-enumeration work isn't lost, and so a future
investigation doesn't have to start from zero.

**A critical note on the numbers in this archive**: the profiling scripts
here measured each configuration exactly once (no repetition, no warmup,
fixed run order), with 40-60% variance observed between identical reruns
minutes apart — well above the effects being reported. The raw JSON data
in [`logs/`](logs/) shows parallel enumeration *slower* than sequential
across most measured configurations, worsening as worker count increases
(e.g. 16-bit LFSRs: roughly 0.87x at 2 workers, 0.54x at 4, 0.31x at 8).
Every specific speedup multiplier that was ever quoted elsewhere in this
project's docs based on this material (fork-vs-spawn, batch aggregation,
persistent pool reuse, load balancing, overall large-LFSR speedup) has
since been stripped from those docs as unreproducible. Treat every number
in this archive as unverified; the qualitative, honestly-supported
takeaway is that parallel enumeration currently provides no reliable
speedup at the problem sizes tested here, most likely due to fork/IPC
overhead dominating cheap per-state work.

If you're looking for the current state of parallel enumeration, start
with `dev-docs/parallel/`, not here — and be skeptical of any multiplier
you find in either location unless it comes with a repeatable, multi-run
benchmark attached.
