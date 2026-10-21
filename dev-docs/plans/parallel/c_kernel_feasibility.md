# C Kernel for the State-Transition Hot Loop: Feasibility Scoping

**Status**: Scoping document — measurements only, no implementation yet.
**Date**: 2026-10-21

## Why this document exists

`CLAUDE.md`'s "Known limitations" section documents that parallel speedup
peaks at ~1.21x for 16-bit LFSRs and that fork overhead dominates for
smaller inputs. Separately, `dev-docs/profiling/` holds an extensive
historical profiling archive, but it is explicitly self-flagged as
unreliable (`PROFILING_EVALUATION.md`'s header note: single-run,
high-variance, two runs even recorded `"correct": false`), and
`CLAUDE.md` itself says no speedup multiplier should be reused without a
fresh, checked-in, multi-run benchmark.

This document does not reuse any number from that archive. It measures,
fresh, whether replacing the per-state Sage-object arithmetic with a
tight C (or C-equivalent) inner loop is likely to be worth the added
build/packaging complexity of a compiled extension module.

## What was measured

A degree-16 GF(2) LFSR, 20,000 sequential state transitions, run on this
host (`.venv/bin/python`, same Sage install the test suite uses). Three
variants of the same operation:

1. **Sage vector × matrix** — what `analysis.py`'s hot loop
   (`_find_sequence_cycle_floyd`/`_find_period_enumeration`/
   `_process_state_chunk`, etc.) actually does today: `state = state *
   state_update_matrix` where `state` is a Sage `Vector_mod2_dense` and
   the matrix is a Sage `Matrix` over `GF(2)`.
2. **Plain-Python int bitmask shift+xor** — the same GF(2) LFSR step
   expressed as a machine-integer bit operation, i.e. what a C kernel's
   inner loop would actually compute, minus any FFI/array-marshalling
   cost (so this is an upper bound on C's advantage, not a real C
   measurement).
3. **Numpy uint8 batched roll+xor** — the same step vectorized over a
   batch of states at once, as a cheaper intermediate step short of a
   full compiled extension.

Script: kept in this session's scratchpad
(`profile_c_kernel_case.py`); not checked into the repo since it's a
one-off scoping measurement, not a maintained benchmark. Re-run it
yourself if you want to reproduce before trusting these numbers on a
different host.

### Results (this host, single run — treat as directional, not final)

| Variant | Time / state | Ratio vs. Sage |
|---|---|---|
| Sage `vector * matrix` | 23.61 µs | 1.0x (baseline) |
| Plain-Python int bitops | 0.08 µs | **288x faster** |
| Numpy uint8 batched | 0.05 µs | **446x faster** |

A second measurement added the per-state bookkeeping the real hot loop
also does — `tuple(state)` + `set.add(...)` for the visited-state
tracking:

| Operation | Time / state |
|---|---|
| Sage transition alone | 23.61 µs |
| Sage transition + `tuple()` + `set.add()` | 41.21 µs |

So the visited-set bookkeeping alone roughly **doubles** the per-state
cost on top of the matrix multiply — both are Sage/Python-object-touching
operations a C kernel would also eliminate, by using a raw machine
integer as the state representation and a bitset or flat array (indexed
by state value) instead of a Python `tuple`+`set`.

### Sanity-checking against the (unreliable) historical data

The self-flagged-unreliable `profile_report_16bit.md` recorded 13.251s
sequential time for a full 16-bit (65,536-state) enumeration — 0.202
ms/state overall. `65536 states × 23.61 µs/state ≈ 1.55s` for pure
transition cost alone (not the 0.202ms/state **total**, which includes
cycle/period bookkeeping, dict construction, etc.). That's a plausible
fraction of the old total and is directionally consistent, which is
reassuring, but this cross-check is not load-bearing — the fresh numbers
above stand on their own regardless of what the old archive says.

## Where a C kernel would and wouldn't help

**Would help — the per-state inner loop:**
- State transition (`_find_sequence_cycle_floyd`/`_brent`/`_enumeration`,
  `_process_state_chunk`'s worker-side loop in `analysis.py`): currently
  one Sage vector-matrix multiply per state, repeated once per state in
  the entire state space (up to millions for larger LFSR degrees).
- Visited-state tracking: currently `tuple(sage_vector)` +
  Python `set` membership, repeated at the same frequency.
- This is exactly the "simple arithmetic over GF(2)/GF(q), repeated
  millions of times" pattern that C (or even just representing state as
  a Python `int` with bit ops, no compiled extension at all) is suited
  for. For GF(2) specifically, a degree-d LFSR state fits in a single
  machine word for any realistic d (≤64), so the *plain-Python-int*
  variant above (288x) is itself a viable, zero-new-dependency
  intermediate step — not only the full C-extension option.

**Would not help — anything Sage-object-shaped:**
- `matrix.characteristic_polynomial()`, polynomial factorization
  (`polynomial.py`), Berlekamp-Massey over Sage polynomial rings
  (`synthesis.py`) — these call into Sage's own (already-compiled,
  often Cython/GMP-backed) number theory internals. Reimplementing
  these in a hand-rolled C kernel means re-deriving a chunk of Sage's
  own math library; not worth it.
- Extending this approach to GF(q) for q > 2 (non-binary LFSRs) is more
  work than the GF(2) case — a state is no longer a single bitmask, and
  the transition is a real modular matrix-vector product — but still
  far cheaper in C/numpy than in Sage, since the arithmetic is small
  fixed-width integers mod a small prime (or prime power via a lookup
  table for the extension field case), not Sage's general-purpose exact
  arithmetic machinery.

## What this does NOT yet establish

Being explicit about the gap between "the inner loop is slow" and "a C
kernel is worth building":

1. **No end-to-end measurement yet.** The 23.61 µs/state Sage cost is
   one contributor to total wall time, not all of it (dict building,
   progress display, I/O, pool/IPC overhead, polynomial-side work all
   still cost something once a C kernel removes the transition cost).
   Need to profile a full `lfsr_sequence_mapper_parallel_dynamic` run
   with the transition+bookkeeping swapped for the C/int equivalent to
   see the real end-to-end speedup, not just the isolated micro-op
   ratio.
2. **No multi-core scaling data for a C kernel specifically.** The
   existing `CLAUDE.md`-documented 1.21x parallel ceiling is a
   consequence of fork/IPC overhead not paying for itself when
   per-task work is cheap in wall-clock terms relative to overhead. If
   a C kernel makes each worker's **share** of work finish 100-400x
   faster, that could go either direction: workers finish fast enough
   that fork/pool overhead dominates even more (parallelism pays off
   *less*), or batches can be sized far larger for the same wall time
   budget, making the existing dynamic/hybrid worker-stealing logic
   actually effective at a problem size where it previously wasn't.
   This needs a real measurement with workers actually running the
   faster kernel, not an assumption either way.
3. **No decision yet on implementation mechanism.** Options, roughly in
   order of increasing complexity and payoff ceiling:
   - **(a)** Keep pure Python, just change the state representation
     from Sage vectors to Python `int` + bit ops for the GF(2) case
     (the 288x number above, zero new dependencies, smallest risk,
     doesn't require a build step).
   - **(b)** `numpy`-vectorize the batch (446x for the batched case
     above; numpy is already a dependency per `pyproject.toml`).
   - **(c)** A real C extension (via `ctypes`/`cffi` against a small
     hand-written `.so`, or a Cython module) for the hottest loop,
     with Python/Sage still orchestrating everything else.
   (a) and (b) need no new build infrastructure at all and should be
   tried first; a full C extension's packaging cost (new compiled
   dependency, platform wheels, `pyproject.toml` build-backend changes)
   is only worth paying if (a)/(b) don't close enough of the gap on a
   real end-to-end run.

## Recommended next step

Before writing any C: prototype option (a) — swap the GF(2) path's
state representation to a plain Python `int` bitmask inside
`_find_sequence_cycle_enumeration`/`_find_period_enumeration` and the
worker-side loop in `_process_state_chunk`, behind a code path that only
activates for `gf_order == 2` (the common case; GF(q>2) keeps using the
existing Sage path unchanged) — then re-run a real sequential vs.
parallel end-to-end benchmark (multiple runs, checked-in script,
reported with variance, consistent with the project's existing
"no unverifiable speedup figures" rule) to see the actual wall-clock
gain before deciding whether a compiled C extension is justified at
all.
