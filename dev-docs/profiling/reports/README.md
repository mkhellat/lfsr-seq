# Profiling Reports

Write-ups produced while interpreting the data in [`../logs/`](../logs/)
and running the scripts in [`../scripts/`](../scripts/) and
[`../investigations/`](../investigations/). See [`../README.md`](../README.md)
for how this archive relates to the maintained `dev-docs/parallel/` docs.

| Report | Topic |
|---|---|
| `12BIT_PROFILING_SUMMARY.md` | Summary of 12-bit parallel enumeration profiling |
| `memory_leak_analysis.md` | Investigation of a suspected memory leak |
| `memory_leak_fixes_summary.md` | Fixes applied following the memory leak analysis |
| `phase_2_2_summary.md` / `phase_2_3_summary.md` / `phase_2_4_summary.md` | Phase 2.x implementation summaries |
| `phase2_profiling_analysis.md` / `phase2_profiling_report.md` | Phase 2 profiling analysis and report |
| `phase_3_1_summary.md` / `phase_3_2_summary.md` | Phase 3.x implementation summaries |
| `profile_report_16bit.md` | 16-bit LFSR profiling report |
| `PROFILING_EVALUATION.md` | Comprehensive evaluation across profiling runs (already annotated with an "Update" note pointing at superseding conclusions) |
| `verify_adaptive_batch.md` | Verification notes for adaptive batch sizing |

Several of these already carry their own `> **Update**: ...` annotations
from an earlier documentation audit, marking specific claims as superseded
by later work — those annotations remain accurate after this move and were
not re-verified again here.
