# Investigation Scripts

One-off scripts written to investigate specific correctness or behavior
questions during the parallel-enumeration work (see
[`../README.md`](../README.md)). Historical artifacts, not maintained
tooling or tests.

**Important**: several of these are named `test_*.py`, matching pytest's
default discovery pattern, but they are **not** part of the pytest suite —
they were standalone manual-run scripts. The actual, maintained test suite
lives in `app/tests/` and is what `make test` / CI run.

| Script | What it investigated |
|---|---|
| `debug_worker_behavior.py` | Worker process behavior during enumeration |
| `investigate_parallel_correctness.py` | Whether parallel results matched serial results |
| `investigate_parallel_overhead.py` | Where parallel-mode overhead came from |
| `test_8bit_parallel.py` | 8-bit LFSR parallel enumeration correctness |
| `test_adaptive_batch_correctness.py` | Adaptive batch-sizing correctness |
| `test_adaptive_batch_sizing.py` | Adaptive batch-sizing behavior/tuning |
| `test_all_modes_performance.py` | Performance comparison across all enumeration modes |
| `test_batch_aggregation_correctness.py` | Batch result aggregation correctness |
| `test_fork_with_sagemath.py` | Fork-mode multiprocessing compatibility with SageMath |
| `test_hybrid_mode_correctness.py` | Hybrid (static+dynamic) mode correctness |
| `test_large_periods.py` | Behavior with large-period LFSRs |
| `test_lazy_generation_correctness.py` | Lazy task-generation correctness |
| `test_memory_safe.py` | Memory safety under parallel enumeration |
| `test_persistent_pool.py` | Persistent worker pool behavior |
| `test_work_stealing_correctness.py` | Work-stealing scheduler correctness |
