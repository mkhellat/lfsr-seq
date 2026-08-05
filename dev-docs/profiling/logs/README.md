# Profiling Logs and Raw Results

Captured output from running the scripts in [`../scripts/`](../scripts/)
and [`../investigations/`](../investigations/) (see [`../README.md`](../README.md)
for context). Historical raw data, not maintained or regenerated.

- `*.log` — captured stdout from profiling runs. Note: `comprehensive_profiling_output.log`,
  `profiling_12bit.log`, and `profiling_output.log` are empty (0 bytes) in
  this archive — likely the run was redirected to file but never completed,
  or captured before output was flushed. Kept as-is rather than removed,
  since an empty log is still evidence a run was attempted at that name.
- `*.json` — structured profiling results, mostly from 12/14/16-bit parallel
  enumeration runs, often in `_v1`/`_v2` and `_imbalance`/`_fixed` pairs
  (before/after variants of a specific fix or tuning pass).

The interpreted conclusions from this raw data live in
[`../reports/`](../reports/) and, in polished form, in `dev-docs/parallel/`.
