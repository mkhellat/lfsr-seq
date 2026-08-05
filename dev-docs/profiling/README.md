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

The conclusions from this work are already distilled into maintained
documentation: [`dev-docs/parallel/`](../parallel/README.md) for the
polished analysis, and the root `CLAUDE.md`'s "Known limitations" section
for the current, accepted-tradeoff summary (parallel speedup peaks at
~1.21x for 16-bit LFSRs; fork overhead dominates smaller inputs). This
archive isn't required reading — it exists so the raw evidence behind
those conclusions isn't lost, and so a future investigation into parallel
performance doesn't have to start from zero.

If you're looking for the current state of parallel enumeration, start
with `dev-docs/parallel/`, not here.
