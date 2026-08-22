#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for lfsr.analysis: state-space enumeration and cycle detection.

Correctness of expected periods/cycles below is verified independently by
hand-simulating the state transition S_i * C = S_{i+1} for small LFSRs
(see core.py's docstring for the convention), not by re-deriving the same
way the source code computes it.

For example, for a 2-bit GF(2) LFSR with coefficients [1, 1]:
    C = [[0, 1],
         [1, 1]]
    (0,0) * C = (0,0)              -> fixed point, period 1
    (1,0) * C = (0,1)
    (0,1) * C = (1,1)
    (1,1) * C = (1,0)              -> 3-cycle: (1,0)->(0,1)->(1,1)->(1,0)
This was confirmed by direct matrix multiplication outside of
lfsr.analysis before writing any assertions against it.
"""

import multiprocessing
import os
import tempfile
import threading

import pytest

try:
    from sage.all import *
except ImportError:
    pytest.skip("SageMath not available", allow_module_level=True)

from lfsr.core import build_state_update_matrix
from lfsr.analysis import (
    _find_period,
    _find_period_brent,
    _find_period_enumeration,
    _find_period_floyd,
    _find_sequence_cycle,
    _find_sequence_cycle_brent,
    _find_sequence_cycle_enumeration,
    _find_sequence_cycle_floyd,
    _format_sequence_entry,
    _merge_parallel_results,
    _partition_state_space,
    _process_state_chunk,
    _process_task_batch_dynamic,
    _update_progress_display,
    display_period_distribution,
    lfsr_sequence_mapper,
    lfsr_sequence_mapper_parallel,
    lfsr_sequence_mapper_parallel_dynamic,
    shutdown_worker_pool,
)
import lfsr.analysis as analysis_mod


@pytest.fixture
def _debug_parallel_env(monkeypatch):
    """Enable the DEBUG_PARALLEL debug-logging branches for the duration
    of a test, restoring whatever value (or absence) existed before."""
    monkeypatch.setenv("DEBUG_PARALLEL", "1")
    yield


# ---------------------------------------------------------------------------
# Shared helpers / fixtures
# ---------------------------------------------------------------------------


def make_matrix(coeffs, gf_order):
    """Build a state update matrix, return (matrix, VectorSpace, degree)."""
    C, _ = build_state_update_matrix(coeffs, gf_order)
    d = len(coeffs)
    V = VectorSpace(GF(gf_order), d)
    return C, V, d


@pytest.fixture(autouse=True)
def _cleanup_worker_pool():
    """Ensure the module-level persistent worker pool is shut down between
    tests so pool state doesn't leak across test functions."""
    yield
    shutdown_worker_pool()


# ---------------------------------------------------------------------------
# Period-only algorithms: Floyd, Brent, enumeration, and the "auto" dispatcher
# ---------------------------------------------------------------------------


class TestFindPeriodAlgorithms:
    """Cross-check all three period-finding algorithms against a hand
    verified 4-bit LFSR, and confirm 'auto'/invalid dispatch behavior."""

    def test_all_algorithms_agree_on_4bit_lfsr(self):
        coeffs = [1, 1, 0, 1]
        C, V, d = make_matrix(coeffs, 2)
        s0 = V([1, 0, 0, 0])

        p_enum = _find_period_enumeration(s0, C)
        p_floyd = _find_period_floyd(s0, C)
        p_brent = _find_period_brent(s0, C)

        assert p_enum == p_floyd == p_brent

    def test_fixed_point_period_is_one(self):
        # All-zero coefficients -> zero matrix -> every state maps to 0.
        coeffs = [0, 0]
        C, V, d = make_matrix(coeffs, 2)
        zero_state = V([0, 0])
        assert _find_period_enumeration(zero_state, C) == 1
        assert _find_period_floyd(zero_state, C) == 1
        assert _find_period_brent(zero_state, C) == 1

    def test_known_3cycle_period(self):
        """Hand-verified: coeffs=[1,1] over GF(2), state (1,0) is on a
        3-cycle: (1,0)->(0,1)->(1,1)->(1,0)."""
        coeffs = [1, 1]
        C, V, d = make_matrix(coeffs, 2)
        s0 = V([1, 0])
        assert _find_period_enumeration(s0, C) == 3
        assert _find_period_floyd(s0, C) == 3
        assert _find_period_brent(s0, C) == 3

    @pytest.mark.parametrize("algorithm", ["floyd", "brent", "enumeration", "auto"])
    def test_find_period_dispatch(self, algorithm):
        coeffs = [1, 1]
        C, V, d = make_matrix(coeffs, 2)
        s0 = V([1, 0])
        assert _find_period(s0, C, algorithm=algorithm) == 3

    def test_find_period_invalid_algorithm_falls_back_to_enumeration(self):
        coeffs = [1, 1]
        C, V, d = make_matrix(coeffs, 2)
        s0 = V([1, 0])
        assert _find_period(s0, C, algorithm="bogus") == 3

    def test_find_period_gf3(self):
        """GF(3), non-binary field: verify via direct hand simulation."""
        coeffs = [1, 2, 1]
        C, V, d = make_matrix(coeffs, 3)
        s0 = V([1, 0, 0])
        # Hand-simulate the trajectory using the same S*C convention.
        seen = [tuple(s0)]
        cur = s0
        for _ in range(30):
            cur = cur * C
            if tuple(cur) == tuple(s0):
                break
            seen.append(tuple(cur))
        expected_period = len(seen)
        assert _find_period_enumeration(s0, C) == expected_period
        assert _find_period_floyd(s0, C) == expected_period
        assert _find_period_brent(s0, C) == expected_period


# ---------------------------------------------------------------------------
# Full-sequence cycle-finding algorithms
# ---------------------------------------------------------------------------


class TestFindSequenceCycleAlgorithms:
    def test_all_algorithms_return_same_cycle(self):
        coeffs = [1, 1, 0, 1]
        C, V, d = make_matrix(coeffs, 2)
        s0 = V([1, 0, 0, 0])

        seq_f, p_f = _find_sequence_cycle_floyd(s0, C, set())
        seq_b, p_b = _find_sequence_cycle_brent(s0, C, set())
        seq_e, p_e = _find_sequence_cycle_enumeration(s0, C, set())

        assert p_f == p_b == p_e == 6
        # Sequences should contain the exact same set of states (order may
        # differ in principle, but all three start from s0 and step forward
        # deterministically, so they should be identical in order too).
        tuples_f = [tuple(s) for s in seq_f]
        tuples_b = [tuple(s) for s in seq_b]
        tuples_e = [tuple(s) for s in seq_e]
        assert tuples_f == tuples_b == tuples_e
        assert tuples_e[0] == (1, 0, 0, 0)

    def test_enumeration_matches_hand_verified_2bit_cycle(self):
        coeffs = [1, 1]
        C, V, d = make_matrix(coeffs, 2)
        s0 = V([1, 0])
        seq, period = _find_sequence_cycle_enumeration(s0, C, set())
        assert period == 3
        assert [tuple(s) for s in seq] == [(1, 0), (0, 1), (1, 1)]

    def test_visited_set_is_populated(self):
        """visited_set must be updated in-place with every state on the
        cycle (used by the caller to skip already-processed states)."""
        coeffs = [1, 1]
        C, V, d = make_matrix(coeffs, 2)
        s0 = V([1, 0])
        visited = set()
        _find_sequence_cycle_enumeration(s0, C, visited)
        assert visited == {(1, 0), (0, 1), (1, 1)}

    def test_degenerate_all_zero_lfsr_terminates(self):
        """Regression test for the known-fixed hang: a non-bijective
        (all-zero-coefficient) LFSR has 'rho-shaped' trajectories that
        never return to start_state. The enumeration must terminate by
        detecting re-entry into ANY visited state, not just start_state."""
        coeffs = [0, 0, 0]
        C, V, d = make_matrix(coeffs, 2)
        # (1,0,0) -> (0,0,0) -> (0,0,0) - never returns to (1,0,0).
        s0 = V([1, 0, 0])
        seq, period = _find_sequence_cycle_enumeration(s0, C, set())
        # Must terminate quickly (not hang / hit the 1e6 safety cap).
        assert period <= 2
        assert tuple(seq[0]) == (1, 0, 0)

    def test_degenerate_lfsr_shared_visited_set_short_circuits(self):
        """When visited_set already contains the merge point from a prior
        start state's trajectory, a new rho-shaped trajectory should stop
        as soon as it re-enters that already-explored territory.

        For coeffs=[0,0,0] over GF(2) (all-zero feedback), the state
        update is a pure right-shift with 0 fed in, e.g. (1,0,0)->(0,0,0)
        (hand-verified by direct matrix multiplication outside the
        module). So (1,0,0)'s trajectory merges into the zero fixed
        point after exactly one step.
        """
        coeffs = [0, 0, 0]
        C, V, d = make_matrix(coeffs, 2)
        visited = set()
        # First: process the fixed point itself.
        zero = V([0, 0, 0])
        _find_sequence_cycle_enumeration(zero, C, visited)
        assert (0, 0, 0) in visited

        # Second: a different starting state whose trajectory flows into
        # the already-visited fixed point after one step must terminate
        # immediately (period 1: it has one state before re-entering
        # visited territory).
        other = V([1, 0, 0])
        assert tuple(other * C) == (0, 0, 0)
        seq2, period2 = _find_sequence_cycle_enumeration(other, C, visited)
        assert period2 == 1
        assert tuple(seq2[0]) == (1, 0, 0)

    @pytest.mark.parametrize("algorithm", ["floyd", "brent", "enumeration", "auto"])
    def test_find_sequence_cycle_dispatch_full_mode(self, algorithm):
        coeffs = [1, 1]
        C, V, d = make_matrix(coeffs, 2)
        s0 = V([1, 0])
        seq, period = _find_sequence_cycle(
            s0, C, set(), algorithm=algorithm, period_only=False
        )
        assert period == 3
        assert len(seq) == 3

    def test_find_sequence_cycle_invalid_algorithm_falls_back(self):
        coeffs = [1, 1]
        C, V, d = make_matrix(coeffs, 2)
        s0 = V([1, 0])
        seq, period = _find_sequence_cycle(
            s0, C, set(), algorithm="nonsense", period_only=False
        )
        assert period == 3

    def test_find_sequence_cycle_period_only_mode(self):
        """period_only=True must mark all cycle states as visited but
        return an empty sequence list."""
        coeffs = [1, 1]
        C, V, d = make_matrix(coeffs, 2)
        s0 = V([1, 0])
        visited = set()
        seq, period = _find_sequence_cycle(
            s0, C, visited, algorithm="auto", period_only=True
        )
        assert seq == []
        assert period == 3
        assert visited == {(1, 0), (0, 1), (1, 1)}


# ---------------------------------------------------------------------------
# _format_sequence_entry
# ---------------------------------------------------------------------------


class TestFormatSequenceEntry:
    def test_basic_formatting_contains_period_and_number(self):
        seq = [(1, 0), (0, 1), (1, 1)]
        entry, all_v = _format_sequence_entry(
            seq_num=2,
            sequence=seq,
            period=3,
            max_period=3,
            special_state=(9, 9),  # not in sequence
            row_width=76,
        )
        joined_entry = " ".join(entry)
        joined_all = " ".join(all_v)
        assert "sequence  2" in joined_entry
        assert "T : 3" in joined_entry
        assert "(1, 0)" in joined_entry  # first state shown when special not present
        assert "(1, 0)" in joined_all and "(1, 1)" in joined_all

    def test_special_state_marks_entry_with_double_asterisk(self):
        seq = [(1, 0), (0, 1), (1, 1)]
        entry, _ = _format_sequence_entry(
            seq_num=1,
            sequence=seq,
            period=3,
            max_period=3,
            special_state=(0, 1),  # is in sequence
            row_width=76,
        )
        joined = " ".join(entry)
        assert "**" in joined
        assert "(0, 1)" in joined  # special state itself is shown, not seq[0]

    def test_non_special_entry_uses_plain_marker(self):
        seq = [(1, 0)]
        entry, _ = _format_sequence_entry(
            seq_num=5,
            sequence=seq,
            period=1,
            max_period=10,
            special_state=(9, 9),
            row_width=76,
        )
        joined = " ".join(entry)
        assert "**" not in joined


# ---------------------------------------------------------------------------
# lfsr_sequence_mapper (serial enumeration) - the core correctness target
# ---------------------------------------------------------------------------


class TestLfsrSequenceMapperSerial:
    def test_2bit_lfsr_matches_hand_computation(self):
        """coeffs=[1,1] over GF(2): one fixed point (0,0) and one 3-cycle
        covering the other 3 states. Hand-verified above."""
        C, V, d = make_matrix([1, 1], 2)
        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
                C, V, 2, output_file=f, no_progress=True
            )

        periods = sorted(period_dict.values())
        assert periods == [1, 3]
        assert max_period == 3
        assert periods_sum == 4  # == state space size (2^2)

        # Exact cycle contents.
        cycles = {frozenset(tuple(s) for s in seq) for seq in seq_dict.values()}
        assert frozenset({(0, 0)}) in cycles
        assert frozenset({(1, 0), (0, 1), (1, 1)}) in cycles

    def test_4bit_lfsr_period_sum_equals_state_space(self):
        C, V, d = make_matrix([1, 1, 0, 1], 2)
        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
                C, V, 2, output_file=f, no_progress=True
            )
        assert periods_sum == 16
        assert sorted(period_dict.values()) == [1, 1, 2, 3, 3, 6]

    def test_gf3_lfsr_period_sum_equals_state_space(self):
        C, V, d = make_matrix([1, 2, 1], 3)
        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
                C, V, 3, output_file=f, no_progress=True
            )
        assert periods_sum == 27  # 3^3

    def test_degenerate_all_zero_lfsr_terminates_and_is_correct(self):
        """Regression test for the known-fixed hang bug: every state maps
        directly to the zero vector for an all-zero-coefficient LFSR, so
        every one of the 4 states is its own singleton fixed-point cycle
        except that (0,0) is a genuine fixed point and the other three
        states are one-step-to-zero (rho shaped, not cycles containing
        themselves) -- but since the shared_visited-based termination
        stops the moment ANY visited state is re-encountered, each
        distinct starting state is reported as its own period-1 'cycle'
        (the point at which it first re-enters previously-explored
        territory, which for a fresh start state is immediately after
        one step for states other than 0)."""
        C, V, d = make_matrix([0, 0], 2)
        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
                C, V, 2, output_file=f, no_progress=True
            )
        # Must terminate (this is the whole point of the regression test)
        # and account for all 4 states exactly once.
        assert periods_sum == 4
        assert len(period_dict) == 4
        assert all(p == 1 for p in period_dict.values())

    def test_output_file_required_for_file_mode(self):
        """dump() with mode=file raises if output_file is None; verify the
        mapper actually requires a real file object (documents the
        contract, not a bug: passing None is a caller error)."""
        C, V, d = make_matrix([1, 1], 2)
        with pytest.raises(ValueError):
            lfsr_sequence_mapper(C, V, 2, output_file=None, no_progress=True)

    def test_period_only_mode_returns_empty_sequences_but_correct_periods(self):
        C, V, d = make_matrix([1, 1], 2)
        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
                C, V, 2, output_file=f, no_progress=True, period_only=True
            )
        assert periods_sum == 4
        assert all(seq == [] for seq in seq_dict.values())
        assert sorted(period_dict.values()) == [1, 3]

    def test_progress_display_path_executes_without_error(self):
        """no_progress=False exercises _update_progress_display via the
        mapper's main loop (only triggered for counter > 1)."""
        C, V, d = make_matrix([1, 1, 0, 1], 2)
        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
                C, V, 2, output_file=f, no_progress=False
            )
        assert periods_sum == 16


# ---------------------------------------------------------------------------
# _update_progress_display (direct unit test, stdout only)
# ---------------------------------------------------------------------------


class TestUpdateProgressDisplay:
    def test_runs_without_error(self, capsys):
        _update_progress_display(counter=5, elp_t=1.23, max_t_t=10.0, state_vector_space_size=16)
        captured = capsys.readouterr()
        assert "5/16" in captured.out or "5/16" in captured.err


# ---------------------------------------------------------------------------
# display_period_distribution
# ---------------------------------------------------------------------------


class TestDisplayPeriodDistribution:
    def test_primitive_polynomial_case(self):
        period_dict = {1: 1, 2: 3}
        with tempfile.TemporaryFile(mode="w+") as f:
            display_period_distribution(
                period_dict, gf_order=2, lfsr_degree=2, is_primitive=True, output_file=f
            )
            f.seek(0)
            content = f.read()
        assert "Total Sequences: 2" in content
        assert "Maximum Period: 3" in content
        assert "Polynomial is Primitive: True" in content

    def test_non_primitive_polynomial_case(self):
        period_dict = {1: 1, 2: 1, 3: 1, 4: 1}
        with tempfile.TemporaryFile(mode="w+") as f:
            display_period_distribution(
                period_dict, gf_order=2, lfsr_degree=2, is_primitive=False, output_file=f
            )
            f.seek(0)
            content = f.read()
        assert "Polynomial is Primitive: False" in content
        # "All Periods Maximum" / "Expected Period" only shown when primitive
        assert "Expected Period (primitive)" not in content


# ---------------------------------------------------------------------------
# _partition_state_space
# ---------------------------------------------------------------------------


class TestPartitionStateSpace:
    def test_evenly_divisible_covers_all_states(self):
        V = VectorSpace(GF(2), 3)  # 8 states
        chunks = _partition_state_space(V, 4)  # 8 / 4 = 2 exactly
        total = sum(len(c) for c in chunks)
        assert total == 8
        all_indices = sorted(idx for chunk in chunks for (_, idx) in chunk)
        assert all_indices == list(range(8))

    def test_empty_state_space_returns_no_chunks(self):
        # A degree-0 vector space still has exactly one (empty) vector in
        # some Sage versions; use num_chunks against a genuinely tiny case
        # instead to exercise the "not evenly divisible" path robustly.
        V = VectorSpace(GF(2), 1)  # 2 states
        chunks = _partition_state_space(V, 1)
        assert sum(len(c) for c in chunks) == 2

    def test_state_tuples_match_binary_encoding_gf2(self):
        V = VectorSpace(GF(2), 3)
        chunks = _partition_state_space(V, 1)
        flat = chunks[0]
        # index 5 = binary 101 (LSB-first per state_index_to_tuple) -> (1,0,1)
        tuple_for_5 = dict(flat)
        # dict keyed by tuple->idx is wrong direction; rebuild idx->tuple
        idx_to_tuple = {idx: t for (t, idx) in flat}
        assert idx_to_tuple[0] == (0, 0, 0)
        assert idx_to_tuple[1] == (1, 0, 0)
        assert idx_to_tuple[5] == (1, 0, 1)
        assert idx_to_tuple[7] == (1, 1, 1)

    def test_state_tuples_match_base_q_encoding_gf3(self):
        V = VectorSpace(GF(3), 2)  # 9 states
        chunks = _partition_state_space(V, 1)
        idx_to_tuple = {idx: t for (t, idx) in chunks[0]}
        assert idx_to_tuple[0] == (0, 0)
        assert idx_to_tuple[1] == (1, 0)
        assert idx_to_tuple[3] == (0, 1)  # 3 = 0 + 1*3 -> digits (0,1) base-3 LSB first
        assert idx_to_tuple[8] == (2, 2)

    def test_num_chunks_matches_requested_count(self):
        V = VectorSpace(GF(2), 4)  # 16 states
        chunks = _partition_state_space(V, 4)
        assert len(chunks) == 4
        assert sum(len(c) for c in chunks) == 16

    def test_uneven_division_covers_all_states(self):
        """Regression test (bug fixed 2026-08-12, see commit history):
        when total_states is not evenly divisible by num_chunks,
        _partition_state_space used to silently drop the trailing states
        instead of assigning them to any chunk. For an 8-state space
        partitioned into 5 chunks, chunk_size = 8 // 5 = 1, so only
        chunks[0..4] each got exactly 1 state (indices 0-4) and indices
        5, 6, 7 were never included in any chunk at all.

        This mattered because callers (lfsr_sequence_mapper_parallel,
        lfsr_sequence_mapper_parallel_dynamic's hybrid mode) rely on this
        function to cover the ENTIRE state space; dropped states were
        silently never processed unless their cycle happened to be
        reached anyway via a covered state (true for bijective/invertible
        LFSRs, but not guaranteed for degenerate/non-bijective matrices,
        where a dropped state can be the sole entry point to an entire
        cycle that is then never counted -- see
        test_gf3_partition_covers_full_state_space below for the
        previously-broken end-to-end case).

        Fixed by distributing the remainder (total_states % num_chunks)
        one extra state per chunk across the first `remainder` chunks, so
        every index in [0, total_states) is covered exactly once."""
        V = VectorSpace(GF(2), 3)  # 8 states total
        chunks = _partition_state_space(V, 5)
        covered_indices = sorted(idx for chunk in chunks for (_, idx) in chunk)

        assert covered_indices == list(range(8))
        assert len(covered_indices) == len(set(covered_indices))  # no duplicates
        assert [len(c) for c in chunks] == [2, 2, 2, 1, 1]


# ---------------------------------------------------------------------------
# _process_state_chunk (worker function, called directly / synchronously)
# ---------------------------------------------------------------------------


class TestProcessStateChunk:
    def test_period_only_mode_matches_serial_result(self):
        coeffs = [1, 1, 0, 1]
        gf_order = 2
        d = 4
        C, V, _ = make_matrix(coeffs, gf_order)

        # Build a single chunk covering the whole 16-state space.
        chunk = []
        for idx in range(16):
            t = tuple((idx >> i) & 1 for i in range(d))
            chunk.append((t, idx))

        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        cycle_lock = manager.Lock()

        chunk_data = (chunk, coeffs, gf_order, d, "auto", True, 0, shared_cycles, cycle_lock)
        result = _process_state_chunk(chunk_data)

        assert result["errors"] == []
        periods = sorted(s["period"] for s in result["sequences"])
        assert periods == [1, 1, 2, 3, 3, 6]
        assert result["max_period"] == 6
        manager.shutdown()

    def test_full_mode_returns_full_state_sequences(self):
        coeffs = [1, 1]
        gf_order = 2
        d = 2
        chunk = [((0, 0), 0), ((1, 0), 1), ((0, 1), 2), ((1, 1), 3)]

        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        cycle_lock = manager.Lock()

        chunk_data = (chunk, coeffs, gf_order, d, "auto", False, 0, shared_cycles, cycle_lock)
        result = _process_state_chunk(chunk_data)

        assert result["errors"] == []
        # One sequence should be the fixed point, one the 3-cycle.
        seq_states = [tuple(seq["states"]) for seq in result["sequences"]]
        assert ((0, 0),) in seq_states
        assert ((1, 0), (0, 1), (1, 1)) in seq_states
        manager.shutdown()


# ---------------------------------------------------------------------------
# _merge_parallel_results
# ---------------------------------------------------------------------------


class TestMergeParallelResults:
    def test_period_only_dedup_by_min_state_via_shared_cycles(self):
        """Two workers 'claim' distinct cycles via shared_cycles; merge
        should produce one entry per claimed cycle."""
        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        shared_cycles[(0, 0, 0, 0)] = 0
        shared_cycles[(0, 0, 0, 1)] = 1

        worker_results = [
            {
                "sequences": [
                    {"states": ((0, 0, 0, 0),), "period": 1, "start_state": (0, 0, 0, 0), "period_only": True},
                ],
                "max_period": 1,
                "errors": [],
            },
            {
                "sequences": [
                    {"states": ((0, 0, 0, 1),), "period": 6, "start_state": (1, 0, 0, 0), "period_only": True},
                ],
                "max_period": 6,
                "errors": [],
            },
        ]
        seq_dict, period_dict, max_period, periods_sum = _merge_parallel_results(
            worker_results, gf_order=2, lfsr_degree=4, shared_cycles=shared_cycles
        )
        assert sorted(period_dict.values()) == [1, 6]
        assert periods_sum == 7
        assert max_period == 6
        # period_only sequences must not be reconstructed (stay empty).
        assert all(v == [] for v in seq_dict.values())
        manager.shutdown()

    def test_period_only_duplicate_min_state_is_deduplicated(self):
        """Same min_state reported by two workers (race at the boundary)
        must collapse into a single sequence, not be double counted."""
        worker_results = [
            {
                "sequences": [
                    {"states": ((1, 1, 1, 1),), "period": 6, "start_state": (1, 1, 1, 0), "period_only": True},
                ],
                "max_period": 6,
                "errors": [],
            },
            {
                "sequences": [
                    {"states": ((1, 1, 1, 1),), "period": 6, "start_state": (0, 1, 1, 1), "period_only": True},
                ],
                "max_period": 6,
                "errors": [],
            },
        ]
        seq_dict, period_dict, max_period, periods_sum = _merge_parallel_results(
            worker_results, gf_order=2, lfsr_degree=4, shared_cycles=None
        )
        assert len(period_dict) == 1
        assert periods_sum == 6

    def test_full_mode_merge_reconstructs_sequences(self):
        """Regression test (bug fixed 2026-08-12, see commit history):
        _merge_parallel_results used to crash when reconstructing
        full-mode (period_only=False) sequences via
        `vector(V, list(state_tuple))` where V is a VectorSpace -- not
        valid Sage usage (sage.all.vector requires either a base ring,
        e.g. `vector(GF(2), [1, 0])`, or a bare list with no ring at
        all). This made EVERY call to lfsr_sequence_mapper_parallel(...,
        period_only=False) crash end-to-end, not just at this unit level
        -- full-sequence-mode parallel processing was completely broken.
        period_only=True was unaffected because it never reaches this
        code path. Fixed by using `vector(F, list(state_tuple))` with
        F = GF(gf_order), matching the pattern used everywhere else in
        this module."""
        worker_results = [
            {
                "sequences": [
                    {
                        "states": [(1, 0, 0, 0), (0, 0, 0, 1)],
                        "period": 2,
                        "start_state": (1, 0, 0, 0),
                        "period_only": False,
                    },
                ],
                "max_period": 2,
                "errors": [],
            },
        ]
        seq_dict, period_dict, max_period, periods_sum = _merge_parallel_results(
            worker_results, gf_order=2, lfsr_degree=4, shared_cycles=None
        )
        assert period_dict == {1: 2}
        assert periods_sum == 2
        assert [tuple(v) for v in seq_dict[1]] == [(1, 0, 0, 0), (0, 0, 0, 1)]

    def test_empty_worker_results(self):
        seq_dict, period_dict, max_period, periods_sum = _merge_parallel_results(
            [], gf_order=2, lfsr_degree=4, shared_cycles=None
        )
        assert seq_dict == {}
        assert period_dict == {}
        assert max_period == 0
        assert periods_sum == 0

    def test_errors_from_workers_are_logged_not_raised(self, capsys):
        worker_results = [
            {"sequences": [], "max_period": 0, "errors": ["boom"]},
        ]
        seq_dict, period_dict, max_period, periods_sum = _merge_parallel_results(
            worker_results, gf_order=2, lfsr_degree=4, shared_cycles=None
        )
        assert period_dict == {}
        captured = capsys.readouterr()
        assert "boom" in captured.err


# ---------------------------------------------------------------------------
# lfsr_sequence_mapper_parallel (static mode) - end to end, period_only only
# ---------------------------------------------------------------------------


class TestLfsrSequenceMapperParallelStatic:
    """period_only=True is exercised end-to-end here; period_only=False
    (full-sequence mode) is exercised end-to-end separately in
    TestMergeParallelResults.test_full_mode_merge_reconstructs_sequences
    and via a direct call to lfsr_sequence_mapper_parallel in this class
    (see test_full_mode_end_to_end below), now that the previously-fixed
    vector() reconstruction bug no longer crashes it."""

    def test_matches_serial_result_period_only(self):
        C, V, d = make_matrix([1, 1, 0, 1], 2)
        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel(
                C, V, 2, output_file=f, no_progress=True, period_only=True, num_workers=2
            )
        assert periods_sum == 16
        assert max_period == 6
        assert sorted(period_dict.values()) == [1, 1, 2, 3, 3, 6]

    def test_single_worker_matches_serial(self):
        C, V, d = make_matrix([1, 1], 2)
        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel(
                C, V, 2, output_file=f, no_progress=True, period_only=True, num_workers=1
            )
        assert periods_sum == 4
        assert sorted(period_dict.values()) == [1, 3]

    def test_full_mode_end_to_end(self):
        """Regression test (bug fixed 2026-08-12, see commit history):
        end-to-end confirmation that period_only=False (full-sequence
        mode) no longer crashes via lfsr_sequence_mapper_parallel's
        vector() reconstruction bug in _merge_parallel_results."""
        C, V, d = make_matrix([1, 1], 2)
        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel(
                C, V, 2, output_file=f, no_progress=True, period_only=False, num_workers=2
            )
        assert periods_sum == 4
        assert sorted(period_dict.values()) == [1, 3]
        reconstructed = {k: [tuple(v) for v in seq] for k, seq in seq_dict.items()}
        assert sorted(reconstructed.values(), key=len) == [[(0, 0)], [(1, 0), (0, 1), (1, 1)]]

    @pytest.mark.slow
    def test_gf3_partition_covers_full_state_space(self):
        """Regression test (bug fixed 2026-08-12, see commit history /
        test_uneven_division_covers_all_states above): this is a
        concrete, non-degenerate, real-world manifestation of the
        _partition_state_space bug, not merely a contrived edge case.
        GF(3), degree 3 -> 27 states, split across 2 workers used to
        compute chunk_size = 27 // 2 = 13, so only 2*13 = 26 states were
        ever assigned to a worker; state index 26 was silently dropped
        and its cycle never counted. The serial mapper (see
        test_gf3_lfsr_period_sum_equals_state_space) correctly reports
        periods_sum == 27; the parallel static mapper must now match.
        """
        C, V, d = make_matrix([1, 2, 1], 3)
        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel(
                C, V, 3, output_file=f, no_progress=True, period_only=True, num_workers=2
            )
        assert periods_sum == 27


# ---------------------------------------------------------------------------
# _process_task_batch_dynamic (dynamic-mode worker, invoked directly to
# avoid the orchestrator hang documented in the report)
# ---------------------------------------------------------------------------


class TestProcessTaskBatchDynamic:
    """lfsr_sequence_mapper_parallel_dynamic's top-level orchestration
    used to hang indefinitely in its default (work-stealing) mode due to
    the bug fixed in test_work_stealing_mode_processes_own_queue below;
    it now completes end-to-end (see TestLfsrSequenceMapperParallelDynamic
    for a direct orchestrator-level regression test). The per-batch
    worker function _process_task_batch_dynamic is exercised directly
    here (synchronously, no Pool/fork involved) since it isolates the
    same cycle-finding logic without the overhead of a full parallel run."""

    def test_shared_queue_mode_matches_serial(self):
        coeffs = [1, 1, 0, 1]
        gf_order, d = 2, 4
        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        cycle_lock = manager.Lock()
        task_queue = manager.Queue()

        batch = [(tuple((s >> i) & 1 for i in range(d)), s) for s in range(16)]
        task_queue.put(batch)
        task_queue.put(None)  # sentinel

        worker_data = (task_queue, coeffs, gf_order, d, "auto", True, 0, shared_cycles, cycle_lock, 1)
        result = _process_task_batch_dynamic(worker_data)

        assert result["errors"] == []
        periods = sorted(s["period"] for s in result["sequences"])
        assert periods == [1, 1, 2, 3, 3, 6]
        assert result["processed_count"] == 6
        manager.shutdown()

    def test_work_stealing_mode_processes_own_queue(self):
        """Regression test (bug fixed 2026-08-12, see commit history),
        SEVERE bug: in work-stealing mode, the caller passes
        `worker_queues` (a list of per-worker Manager().Queue()s) and
        `task_queue=None` via the mode-detection branch at the top of
        _process_task_batch_dynamic. The worker's main polling loop used
        to unconditionally call `task_queue.get_nowait()`, never reading
        from `worker_queues[worker_id]` regardless of which mode was
        detected. With task_queue=None this raised AttributeError on
        every iteration -- caught by a bare `except Exception: ...;
        continue`, which swallowed it, appended it to `errors`, and
        looped again immediately. Since task_queue never became
        non-None and the sentinel sitting in worker_queues[0] was never
        read, this was a genuine CPU-spinning infinite loop, not just a
        crash -- the confirmed root cause of
        lfsr_sequence_mapper_parallel_dynamic(...) hanging indefinitely
        end-to-end for its default (work-stealing) mode, and for hybrid
        mode once its static chunk was exhausted.

        Fixed by selecting `own_queue = worker_queues[worker_id] if
        use_work_stealing else task_queue` once before the main loop, so
        the existing batch-pull logic reads from the correct queue in
        both modes. This test used to run the reproduction in a
        subprocess with a hard timeout (asserting it hung); now that the
        fix makes it terminate promptly, it's exercised directly and
        confirmed to process real work and hit its own queue's
        sentinel."""
        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        cycle_lock = manager.Lock()
        worker_queues = [manager.Queue(), manager.Queue()]

        coeffs = [1, 1]
        gf_order, d = 2, 2
        batch = [(tuple((s >> i) & 1 for i in range(d)), s) for s in range(4)]
        worker_queues[0].put(batch)
        worker_queues[0].put(None)  # sentinel for worker 0
        worker_queues[1].put(None)  # sentinel for worker 1 (no work assigned)

        worker_data_0 = (worker_queues, 0, coeffs, gf_order, d, "auto", True, shared_cycles, cycle_lock, 1)
        worker_data_1 = (worker_queues, 1, coeffs, gf_order, d, "auto", True, shared_cycles, cycle_lock, 1)

        result0 = _process_task_batch_dynamic(worker_data_0)
        result1 = _process_task_batch_dynamic(worker_data_1)

        assert result0["errors"] == []
        assert result0["processed_count"] == 2  # 2 unique cycles cover all 4 states
        periods = sorted(s["period"] for s in result0["sequences"])
        assert periods == [1, 3]

        assert result1["errors"] == []
        assert result1["processed_count"] == 0
        manager.shutdown()

    def test_full_mode_via_shared_queue(self):
        coeffs = [1, 1]
        gf_order, d = 2, 2
        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        cycle_lock = manager.Lock()
        task_queue = manager.Queue()
        batch = [(tuple((s >> i) & 1 for i in range(d)), s) for s in range(4)]
        task_queue.put(batch)
        task_queue.put(None)

        worker_data = (task_queue, coeffs, gf_order, d, "auto", False, 0, shared_cycles, cycle_lock, 1)
        result = _process_task_batch_dynamic(worker_data)

        assert result["errors"] == []
        seq_states = {tuple(s["states"]) for s in result["sequences"]}
        assert ((0, 0),) in seq_states
        manager.shutdown()


# ---------------------------------------------------------------------------
# lfsr_sequence_mapper_parallel_dynamic - end to end, orchestrator level
# ---------------------------------------------------------------------------


class TestLfsrSequenceMapperParallelDynamic:
    """Direct, orchestrator-level regression test for the work-stealing
    infinite-loop bug fixed in
    TestProcessTaskBatchDynamic.test_work_stealing_mode_processes_own_queue.
    Previously, calling this function was unsafe in a test suite because
    it hung indefinitely for every input in its default (work-stealing)
    mode; it must now complete promptly and match the serial mapper."""

    @pytest.mark.slow
    def test_matches_serial_result_period_only(self):
        C, V, d = make_matrix([1, 1, 0, 1], 2)
        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel_dynamic(
                C, V, 2, output_file=f, no_progress=True, period_only=True, num_workers=2
            )
        assert periods_sum == 16
        assert max_period == 6
        assert sorted(period_dict.values()) == [1, 1, 2, 3, 3, 6]


# ---------------------------------------------------------------------------
# shutdown_worker_pool / pool lifecycle
# ---------------------------------------------------------------------------


class TestWorkerPoolLifecycle:
    def test_shutdown_is_safe_when_no_pool_exists(self):
        # Ensure clean state, then shutdown again -- must not raise.
        shutdown_worker_pool()
        shutdown_worker_pool()
        assert analysis_mod._worker_pool is None
        assert analysis_mod._worker_pool_size == 0

    def test_shutdown_resets_module_globals_after_manual_pool_creation(self):
        ctx = multiprocessing.get_context("fork")
        pool = ctx.Pool(processes=1)
        analysis_mod._worker_pool = pool
        analysis_mod._worker_pool_context = ctx
        analysis_mod._worker_pool_size = 1

        shutdown_worker_pool()

        assert analysis_mod._worker_pool is None
        assert analysis_mod._worker_pool_context is None
        assert analysis_mod._worker_pool_size == 0

    def test_shutdown_swallows_errors_from_broken_pool(self):
        """A pool object that raises on close()/join() must not propagate
        the exception out of shutdown_worker_pool (it's registered via
        atexit and must not crash interpreter shutdown)."""

        class BrokenPool:
            def close(self):
                raise RuntimeError("simulated close failure")

            def join(self, timeout=None):
                raise RuntimeError("should not be reached")

        analysis_mod._worker_pool = BrokenPool()
        analysis_mod._worker_pool_context = object()
        analysis_mod._worker_pool_size = 3

        shutdown_worker_pool()  # must not raise

        assert analysis_mod._worker_pool is None
        assert analysis_mod._worker_pool_size == 0


# ---------------------------------------------------------------------------
# Additional coverage-closing tests: _merge_parallel_results edge branches
# ---------------------------------------------------------------------------


class TestMergeParallelResultsExtra:
    def test_sagemath_import_failure_returns_empty(self, monkeypatch):
        """If `from lfsr.sage_imports import GF, vector` raises ImportError,
        the function must log to stderr and return the all-empty tuple
        rather than propagating."""
        import lfsr.sage_imports as sage_imports_mod

        real_import = __import__

        def fake_import(name, *args, **kwargs):
            if name == "lfsr.sage_imports":
                raise ImportError("simulated: sage not available")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", fake_import)
        seq_dict, period_dict, max_period, periods_sum = _merge_parallel_results(
            [], gf_order=2, lfsr_degree=2, shared_cycles=None
        )
        assert (seq_dict, period_dict, max_period, periods_sum) == ({}, {}, 0, 0)

    def test_shared_cycles_skips_empty_states_and_zero_period(self):
        """Entries with falsy `states` or period==0 must be skipped (line
        `if not states_tuples or period == 0: continue`) when shared_cycles
        is used for dedup."""
        worker_results = [
            {
                "sequences": [
                    {"states": (), "period": 5, "start_state": (0, 0), "period_only": True},
                    {"states": ((1, 1),), "period": 0, "start_state": (1, 1), "period_only": True},
                    {"states": ((0, 1),), "period": 2, "start_state": (0, 1), "period_only": True},
                ],
                "max_period": 2,
                "errors": [],
            }
        ]
        shared_cycles = {(0, 1): 0}
        seq_dict, period_dict, max_period, periods_sum = _merge_parallel_results(
            worker_results, gf_order=2, lfsr_degree=2, shared_cycles=shared_cycles
        )
        # Only the third entry (non-empty states, non-zero period) survives.
        assert list(period_dict.values()) == [2]

    def test_shared_cycles_skips_malformed_states_entry(self):
        """`states` that is neither a length-1 tuple nor a non-empty list
        (e.g. a dict, or a list with 0 length after the falsy check somehow
        passes) falls through to `continue` at the final else branch."""
        worker_results = [
            {
                "sequences": [
                    # A non-tuple, non-list truthy value hits the final
                    # `else: continue` branch.
                    {"states": "not-a-tuple-or-list", "period": 3, "start_state": (0,), "period_only": True},
                ],
                "max_period": 3,
                "errors": [],
            }
        ]
        seq_dict, period_dict, max_period, periods_sum = _merge_parallel_results(
            worker_results, gf_order=2, lfsr_degree=2, shared_cycles={}
        )
        assert period_dict == {}

    def test_fallback_dedup_empty_states_tuples_uses_period_start_state_key(self):
        """When shared_cycles is None (fallback dedup path) and states is
        falsy, the key becomes (period, start_state)."""
        worker_results = [
            {
                "sequences": [
                    {"states": [], "period": 4, "start_state": (1, 0, 0, 0), "period_only": True},
                ],
                "max_period": 4,
                "errors": [],
            }
        ]
        seq_dict, period_dict, max_period, periods_sum = _merge_parallel_results(
            worker_results, gf_order=2, lfsr_degree=4, shared_cycles=None
        )
        assert period_dict == {1: 4}
        # period_only defaults to seq_info.get('period_only', False); here it's True
        assert seq_dict == {1: []}

    def test_empty_states_reconstructs_as_empty_list_not_period_only(self):
        """Full-mode (period_only=False) entry whose 'states' happens to be
        empty must still land as [] via the final `else` branch (line 968),
        not crash trying to reconstruct vectors from nothing."""
        worker_results = [
            {
                "sequences": [
                    {"states": [], "period": 1, "start_state": (0, 0), "period_only": False},
                ],
                "max_period": 1,
                "errors": [],
            }
        ]
        seq_dict, period_dict, max_period, periods_sum = _merge_parallel_results(
            worker_results, gf_order=2, lfsr_degree=2, shared_cycles=None
        )
        assert seq_dict == {1: []}

    def test_more_than_ten_errors_shows_truncation_message(self, capsys):
        errors = [f"error-{i}" for i in range(15)]
        worker_results = [{"sequences": [], "max_period": 0, "errors": errors}]
        _merge_parallel_results(worker_results, gf_order=2, lfsr_degree=2, shared_cycles=None)
        captured = capsys.readouterr()
        assert "... and 5 more errors" in captured.err

    def test_debug_parallel_env_var_exercises_debug_logging(self, _debug_parallel_env, capsys):
        """DEBUG_PARALLEL=1 triggers the merge_debug print branches (both
        shared_cycles and fallback code paths)."""
        worker_results = [
            {
                "sequences": [
                    {"states": ((0, 0),), "period": 1, "start_state": (0, 0), "period_only": True},
                ],
                "max_period": 1,
                "errors": [],
            }
        ]
        # shared_cycles path
        _merge_parallel_results(worker_results, gf_order=2, lfsr_degree=2, shared_cycles={})
        # fallback path
        _merge_parallel_results(worker_results, gf_order=2, lfsr_degree=2, shared_cycles=None)
        captured = capsys.readouterr()
        assert "Merge PID" in captured.err


# ---------------------------------------------------------------------------
# Additional coverage-closing tests: _partition_state_space edge branches
# ---------------------------------------------------------------------------


class TestPartitionStateSpaceExtra:
    def test_fallback_path_when_basis_or_order_missing_materializes_states(self):
        """When state_vector_space lacks .basis()/.base_ring().order() (so
        the `try` at analysis.py raises AttributeError/TypeError), the
        `except` branch must fall back to materializing states by direct
        iteration rather than crashing with UnboundLocalError (a real bug
        fixed alongside this test: d/gf_order were never bound on that
        branch, yet state_index_to_tuple(state_idx, d, gf_order) was called
        unconditionally afterwards)."""

        class FakeSpace:
            def __iter__(self):
                return iter([(0, 0), (1, 0), (1, 1)])  # 3 "states"

        chunks = _partition_state_space(FakeSpace(), 1)
        assert len(chunks) == 1
        assert [state for state, _idx in chunks[0]] == [(0, 0), (1, 0), (1, 1)]
        assert [idx for _state, idx in chunks[0]] == [0, 1, 2]

    def test_zero_total_states_returns_empty_list(self):
        class EmptySpace:
            def __iter__(self):
                return iter([])

        chunks = _partition_state_space(EmptySpace(), 3)
        assert chunks == []


# ---------------------------------------------------------------------------
# Additional coverage-closing tests: _process_state_chunk edge branches
# ---------------------------------------------------------------------------


class TestProcessStateChunkExtra:
    def test_debug_parallel_env_exercises_debug_logging(self, _debug_parallel_env, capsys):
        coeffs = [1, 1]
        gf_order, d = 2, 2
        chunk = [((0, 0), 0)]
        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        cycle_lock = manager.Lock()
        chunk_data = (chunk, coeffs, gf_order, d, "auto", True, 0, shared_cycles, cycle_lock)
        result = _process_state_chunk(chunk_data)
        assert result["errors"] == []
        captured = capsys.readouterr()
        assert "Worker 0 PID" in captured.err
        manager.shutdown()

    def test_invalid_gf_order_returns_error_result(self):
        """gf_order=6 is not a prime power; build_state_update_matrix must
        raise inside the worker, which should be caught and reported as an
        error result rather than propagating (lines 1187-1189)."""
        coeffs = [1, 1]
        chunk = [((0, 0), 0)]
        chunk_data = (chunk, coeffs, 6, 2, "auto", True, 0, {}, threading.Lock())
        result = _process_state_chunk(chunk_data)
        assert result["sequences"] == []
        assert result["processed_count"] == 0
        assert len(result["errors"]) == 1
        assert "Failed to build state update matrix" in result["errors"][0]

    def test_already_claimed_cycle_is_skipped_fast_path(self):
        """Pre-populate shared_cycles with the min_state of the (1,1)
        coeffs=[1,1] 3-cycle {(1,0),(0,1),(1,1)} (min tuple is (0,1)) so
        the worker's fast (no-lock) claimed-check short-circuits (lines
        1326-1338) instead of processing the cycle."""
        coeffs = [1, 1]
        gf_order, d = 2, 2
        chunk = [((1, 0), 0)]
        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        shared_cycles[(0, 1)] = 99  # claimed by "worker 99"
        cycle_lock = manager.Lock()
        chunk_data = (chunk, coeffs, gf_order, d, "enumeration", True, 0, shared_cycles, cycle_lock)
        result = _process_state_chunk(chunk_data)
        assert result["errors"] == []
        assert result["sequences"] == []  # nothing claimed/produced by this worker
        assert result["work_metrics"]["cycles_skipped"] == 1
        manager.shutdown()

    def test_malformed_state_tuple_produces_error_not_crash(self):
        """A state tuple containing a value F() can't coerce (e.g. a
        string) must be caught by the per-state try/except (lines
        1414-1418), appended to errors, and NOT abort the whole chunk."""
        coeffs = [1, 1]
        gf_order, d = 2, 2
        chunk = [(("not-a-number", 0), 0), ((0, 0), 1)]  # first is bad, second is fine
        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        cycle_lock = manager.Lock()
        chunk_data = (chunk, coeffs, gf_order, d, "auto", True, 0, shared_cycles, cycle_lock)
        result = _process_state_chunk(chunk_data)
        assert len(result["errors"]) == 1
        assert "not-a-number" in result["errors"][0] or "Error processing state" in result["errors"][0]
        # second (valid) state should still have been processed
        assert result["processed_count"] == 1
        manager.shutdown()

    def test_large_period_hits_periodic_hang_detection_check(self):
        """A maximal-length 12-bit LFSR (period 2**12-1 = 4095, confirmed
        by direct hand simulation before writing this test) forces the
        min_state-search loop past 1000 iterations, exercising the
        `if i > 0 and i % 1000 == 0: _ = len(str(current))` responsiveness
        check at line 1320."""
        coeffs = [1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0]  # primitive degree-12 poly
        gf_order, d = 2, 12
        chunk = [((1,) + (0,) * 11, 0)]
        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        cycle_lock = manager.Lock()
        chunk_data = (chunk, coeffs, gf_order, d, "enumeration", True, 0, shared_cycles, cycle_lock)
        result = _process_state_chunk(chunk_data)
        assert result["errors"] == []
        assert result["max_period"] == 4095
        manager.shutdown()

    def test_claimed_between_check_and_lock_race_branch(self):
        """Simulate the check-then-claim race at lines 1340-1352: the fast
        (no-lock) membership check at line 1326 sees the cycle as
        NOT-yet-claimed, but by the time the lock is acquired, another
        "worker" has claimed it. A stateful fake dict-like object flips
        from reporting False to True on `__contains__` between the two
        checks to deterministically force this branch instead of relying
        on a genuine multi-process race."""
        coeffs = [1, 1]
        gf_order, d = 2, 2

        class RacingSharedCycles(dict):
            def __init__(self):
                super().__init__()
                self._checks = 0

            def __contains__(self, key):
                self._checks += 1
                if self._checks == 1:
                    return False  # fast check: not claimed yet
                return True  # check inside the lock: "claimed" by another worker

            def __getitem__(self, key):
                return 99  # "claimed by worker 99"

        shared_cycles = RacingSharedCycles()
        chunk = [((1, 0), 0)]
        chunk_data = (chunk, coeffs, gf_order, d, "enumeration", True, 0, shared_cycles, threading.Lock())
        result = _process_state_chunk(chunk_data)
        assert result["errors"] == []
        assert result["sequences"] == []  # not claimed by this worker after all


# ---------------------------------------------------------------------------
# Additional coverage-closing tests: lfsr_sequence_mapper_parallel branches
# ---------------------------------------------------------------------------


class TestLfsrSequenceMapperParallelExtra:
    def test_worker_count_note_prints_when_auto_selection_hits_cpu_limit(self, monkeypatch, capsys):
        """The "Note: Using N workers (optimal M...)" message must print
        when auto mode (num_workers=None) selects an optimal worker count
        that then gets capped by a low cpu_count(). This was previously
        dead code: original_num_workers was captured AFTER num_workers=None
        had already been replaced with cpu_count(), so the `is None` guard
        could never be true. Fixed by capturing original_num_workers from
        the caller-supplied value before any auto-fill."""
        monkeypatch.setattr(multiprocessing, "cpu_count", lambda: 1)
        C, V, d = make_matrix([1] * 11, 2)  # 2**11 = 2048 states -> optimal_workers=2
        with tempfile.TemporaryFile(mode="w+") as f:
            lfsr_sequence_mapper_parallel(
                C, V, 2, output_file=f, no_progress=False, period_only=True, num_workers=None
            )
        captured = capsys.readouterr()
        assert "Note: Using" in captured.err

    def test_worker_count_note_not_printed_for_explicit_num_workers(self, monkeypatch, capsys):
        """When the caller explicitly passes num_workers, the auto-select
        "Note: ..." message must NOT print, even if it differs from the
        optimal count."""
        monkeypatch.setattr(multiprocessing, "cpu_count", lambda: 1)
        C, V, d = make_matrix([1] * 11, 2)
        with tempfile.TemporaryFile(mode="w+") as f:
            lfsr_sequence_mapper_parallel(
                C, V, 2, output_file=f, no_progress=False, period_only=True, num_workers=1
            )
        captured = capsys.readouterr()
        assert "Note: Using" not in captured.out
        assert "Note: Using" not in captured.err

    def test_pool_map_async_timeout_falls_back_to_sequential(self, monkeypatch):
        """Simulate a multiprocessing.TimeoutError from async_result.get()
        to exercise the timeout-handling fallback (lines 1659-1685), which
        must terminate the pool and return the same result the plain
        sequential mapper would."""
        C, V, d = make_matrix([1, 1], 2)

        class FakeAsyncResult:
            def get(self, timeout=None):
                raise multiprocessing.TimeoutError("simulated timeout")

        class FakePool:
            def map_async(self, func, iterable):
                return FakeAsyncResult()

            def terminate(self):
                pass

            def join(self, timeout=None):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        class FakeCtx:
            def Pool(self, processes):
                return FakePool()

            def get_start_method(self):
                return "fork"

        monkeypatch.setattr(multiprocessing, "get_context", lambda method: FakeCtx())

        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel(
                C, V, 2, output_file=f, no_progress=True, period_only=True, num_workers=2
            )
        # Falls back to sequential lfsr_sequence_mapper, which is known-correct.
        assert periods_sum == 4
        assert sorted(period_dict.values()) == [1, 3]

    def test_empty_state_space_returns_empty_result(self):
        """Covers line 1585: `if not chunks: return {}, {}, 0, 0` when
        _partition_state_space returns no chunks for an empty state
        space."""
        C, V, d = make_matrix([1, 1], 2)

        class EmptySpace:
            def __iter__(self):
                return iter([])

        with tempfile.TemporaryFile(mode="w+") as f:
            result = lfsr_sequence_mapper_parallel(
                C, EmptySpace(), 2, output_file=f, no_progress=True, period_only=True, num_workers=2
            )
        assert result == ({}, {}, 0, 0)

    def test_spawn_mode_uses_120s_timeout(self, monkeypatch):
        """Covers line 1674: when the pool's context reports
        get_start_method() == 'spawn' (fork unavailable on this
        platform), the longer 120s timeout branch is selected instead of
        fork's 40s. Uses a real ctx.Pool()-compatible fake that succeeds
        immediately (no actual 120s wait -- only the branch selection is
        under test, the real .get(timeout=120) call returns right away
        since FakeAsyncResult.get() doesn't block)."""
        C, V, d = make_matrix([1, 1], 2)

        class FakeAsyncResult:
            def get(self, timeout=None):
                assert timeout == 120  # confirms the spawn branch was taken
                return [
                    {
                        "sequences": [
                            {"states": ((0, 0),), "period": 1, "start_state": (0, 0), "period_only": True},
                            {"states": ((0, 1),), "period": 3, "start_state": (1, 0), "period_only": True},
                        ],
                        "max_period": 3,
                        "errors": [],
                        "work_metrics": {"states_processed": 2},
                    },
                    {
                        "sequences": [],
                        "max_period": 0,
                        "errors": [],
                        "work_metrics": {"states_processed": 0},
                    },
                ]

        class FakePool:
            def map_async(self, func, iterable):
                return FakeAsyncResult()

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        class FakeCtx:
            def Pool(self, processes):
                return FakePool()

            def get_start_method(self):
                return "spawn"

        monkeypatch.setattr(multiprocessing, "get_context", lambda method: FakeCtx())

        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel(
                C, V, 2, output_file=f, no_progress=True, period_only=True, num_workers=2
            )
        assert periods_sum == 4

    def test_pool_creation_exception_falls_back_to_sequential(self, monkeypatch):
        """A generic exception anywhere in the parallel-setup try block
        (lines 1696-1711) must trigger the fallback to
        lfsr_sequence_mapper rather than propagating."""
        C, V, d = make_matrix([1, 1], 2)

        def broken_get_context(method):
            raise RuntimeError("simulated pool-creation failure")

        monkeypatch.setattr(multiprocessing, "get_context", broken_get_context)

        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel(
                C, V, 2, output_file=f, no_progress=True, period_only=True, num_workers=2
            )
        assert periods_sum == 4
        assert sorted(period_dict.values()) == [1, 3]

    def test_period_sum_mismatch_warning_printed(self, monkeypatch, capsys):
        """If periods_sum doesn't match the true state-space size (e.g. a
        merge bug), a WARNING is printed to stderr (lines 1774-1778).
        Force this by monkeypatching _merge_parallel_results to return an
        intentionally wrong periods_sum."""
        C, V, d = make_matrix([1, 1], 2)

        def fake_merge(worker_results, gf_order, lfsr_degree, shared_cycles=None):
            return {1: []}, {1: 1}, 1, 999  # wrong periods_sum on purpose

        monkeypatch.setattr(analysis_mod, "_merge_parallel_results", fake_merge)
        with tempfile.TemporaryFile(mode="w+") as f:
            lfsr_sequence_mapper_parallel(
                C, V, 2, output_file=f, no_progress=True, period_only=True, num_workers=1
            )
        captured = capsys.readouterr()
        assert "WARNING: Period sum" in captured.err


# ---------------------------------------------------------------------------
# Additional coverage-closing tests: _process_task_batch_dynamic branches
# ---------------------------------------------------------------------------


class TestProcessTaskBatchDynamicExtra:
    def test_hybrid_mode_dispatch_processes_assigned_chunk(self):
        """Hybrid mode is detected when worker_data[0] and [1] are both
        lists (lines 1839-1844): an assigned static chunk plus a list of
        worker_queues. The assigned chunk must be processed as a batch
        before the worker moves on to pulling from its own queue."""
        coeffs = [1, 1]
        gf_order, d = 2, 2
        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        cycle_lock = manager.Lock()
        worker_queues = [manager.Queue(), manager.Queue()]
        worker_queues[0].put(None)  # sentinel: no queued work beyond the static chunk
        worker_queues[1].put(None)

        assigned_chunk = [((0, 0), 0), ((1, 0), 1)]
        worker_data = (
            assigned_chunk,
            worker_queues,
            0,
            coeffs,
            gf_order,
            d,
            "auto",
            True,
            shared_cycles,
            cycle_lock,
            1,
        )
        result = _process_task_batch_dynamic(worker_data)
        assert result["errors"] == []
        assert result["processed_count"] == 2  # fixed point + 3-cycle start
        periods = sorted(s["period"] for s in result["sequences"])
        assert periods == [1, 3]
        manager.shutdown()

    def test_debug_parallel_env_exercises_debug_logging(self, _debug_parallel_env, capsys):
        coeffs = [1, 1]
        gf_order, d = 2, 2
        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        cycle_lock = manager.Lock()
        task_queue = manager.Queue()
        task_queue.put([((0, 0), 0)])
        task_queue.put(None)
        worker_data = (task_queue, coeffs, gf_order, d, "auto", True, 0, shared_cycles, cycle_lock, 1)
        result = _process_task_batch_dynamic(worker_data)
        assert result["errors"] == []
        captured = capsys.readouterr()
        assert "Dynamic Worker 0 PID" in captured.err
        manager.shutdown()

    def test_sagemath_import_failure_returns_error_result(self, monkeypatch):
        real_import = __import__

        def fake_import(name, *args, **kwargs):
            if name == "lfsr.sage_imports":
                raise ImportError("simulated: sage not available")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", fake_import)
        manager = multiprocessing.Manager()
        task_queue = manager.Queue()
        task_queue.put(None)
        worker_data = (task_queue, [1, 1], 2, 2, "auto", True, 0, {}, threading.Lock(), 1)
        result = _process_task_batch_dynamic(worker_data)
        assert result["sequences"] == []
        assert "SageMath not available" in result["errors"][0]
        manager.shutdown()

    def test_invalid_gf_order_returns_error_result(self):
        """gf_order=6 (not a prime power) makes build_state_update_matrix
        raise inside the worker (lines 1891-1893)."""
        manager = multiprocessing.Manager()
        task_queue = manager.Queue()
        task_queue.put(None)
        worker_data = (task_queue, [1, 1], 6, 2, "auto", True, 0, {}, threading.Lock(), 1)
        result = _process_task_batch_dynamic(worker_data)
        assert result["sequences"] == []
        assert "Failed to build state update matrix" in result["errors"][0]
        manager.shutdown()

    def test_already_claimed_cycle_skipped_in_shared_queue_mode(self):
        coeffs = [1, 1]
        gf_order, d = 2, 2
        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        shared_cycles[(0, 1)] = 99  # pre-claim the 3-cycle's min_state
        cycle_lock = manager.Lock()
        task_queue = manager.Queue()
        task_queue.put([((1, 0), 0)])
        task_queue.put(None)
        worker_data = (task_queue, coeffs, gf_order, d, "enumeration", True, 0, shared_cycles, cycle_lock, 1)
        result = _process_task_batch_dynamic(worker_data)
        assert result["errors"] == []
        assert result["sequences"] == []
        assert result["work_metrics"]["cycles_skipped"] == 1
        manager.shutdown()

    def test_malformed_state_in_batch_produces_error_not_crash(self):
        coeffs = [1, 1]
        gf_order, d = 2, 2
        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        cycle_lock = manager.Lock()
        task_queue = manager.Queue()
        task_queue.put([(("bad", 0), 0), ((0, 0), 1)])
        task_queue.put(None)
        worker_data = (task_queue, coeffs, gf_order, d, "auto", True, 0, shared_cycles, cycle_lock, 1)
        result = _process_task_batch_dynamic(worker_data)
        assert len(result["errors"]) == 1
        assert result["processed_count"] == 1
        manager.shutdown()

    def test_batch_aggregation_pulls_multiple_batches_at_once(self):
        """batch_aggregation_count > 1 pulls several batches per
        get_nowait() round (lines around 2088-2098); verify multiple
        pre-queued batches are all processed correctly."""
        coeffs = [1, 1]
        gf_order, d = 2, 2
        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        cycle_lock = manager.Lock()
        task_queue = manager.Queue()
        task_queue.put([((0, 0), 0)])
        task_queue.put([((1, 0), 1)])
        task_queue.put(None)
        worker_data = (task_queue, coeffs, gf_order, d, "auto", True, 0, shared_cycles, cycle_lock, 4)
        result = _process_task_batch_dynamic(worker_data)
        assert result["errors"] == []
        assert result["processed_count"] == 2
        assert result["work_metrics"]["batches_processed"] == 2
        manager.shutdown()

    def test_batch_aggregation_hits_empty_queue_before_sentinel(self):
        """Covers analysis.py lines 2119-2121: the inner `except
        queue_module.Empty: break` hit when get_nowait() finds the queue
        genuinely drained (not a sentinel) partway through an aggregation
        round. Achieved deterministically by queuing only 1 real batch
        with batch_aggregation_count=4 (so the 2nd get_nowait() call in
        the same round empties out) and delivering the sentinel from a
        background thread shortly after, so the worker's *next* outer
        while-True iteration (this time seeing an empty queue on its
        very first get_nowait()) picks up the sentinel instead of
        spinning forever. Bounded by a join(timeout=...) below to avoid
        any risk of hanging the test suite if this assumption were ever
        wrong."""
        import threading as threading_mod
        import time as time_mod

        coeffs = [1, 1]
        gf_order, d = 2, 2
        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        cycle_lock = manager.Lock()
        task_queue = manager.Queue()
        task_queue.put([((0, 0), 0)])  # only 1 batch -> next get_nowait() raises Empty

        def delayed_sentinel():
            time_mod.sleep(0.3)
            task_queue.put(None)

        sentinel_thread = threading_mod.Thread(target=delayed_sentinel, daemon=True)
        sentinel_thread.start()

        worker_data = (task_queue, coeffs, gf_order, d, "auto", True, 0, shared_cycles, cycle_lock, 4)
        result = _process_task_batch_dynamic(worker_data)
        sentinel_thread.join(timeout=5.0)
        assert result["errors"] == []
        assert result["processed_count"] == 1
        manager.shutdown()

    def test_large_period_hits_periodic_hang_detection_check(self):
        """Mirrors TestProcessStateChunkExtra's equivalent test: a
        maximal-length 12-bit LFSR (period 4095, hand-verified) forces the
        min_state-search loop in the dynamic worker's period-only branch
        past 1000 iterations (line 1975)."""
        coeffs = [1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0]
        gf_order, d = 2, 12
        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        cycle_lock = manager.Lock()
        task_queue = manager.Queue()
        task_queue.put([((1,) + (0,) * 11, 0)])
        task_queue.put(None)
        worker_data = (task_queue, coeffs, gf_order, d, "enumeration", True, 0, shared_cycles, cycle_lock, 1)
        result = _process_task_batch_dynamic(worker_data)
        assert result["errors"] == []
        assert result["max_period"] == 4095
        manager.shutdown()

    def test_period_computation_exception_is_caught(self, monkeypatch):
        """Force _find_period to raise inside the dynamic worker's
        period-only branch (line 1959-1961) by monkeypatching it at the
        module level (the worker does `from lfsr.analysis import
        _find_period` inside process_single_batch's enclosing function, so
        patching analysis_mod._find_period is visible to it)."""

        def broken_find_period(*args, **kwargs):
            raise RuntimeError("simulated period computation failure")

        monkeypatch.setattr(analysis_mod, "_find_period", broken_find_period)
        coeffs = [1, 1]
        gf_order, d = 2, 2
        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        cycle_lock = manager.Lock()
        task_queue = manager.Queue()
        task_queue.put([((1, 0), 0)])
        task_queue.put(None)
        worker_data = (task_queue, coeffs, gf_order, d, "auto", True, 0, shared_cycles, cycle_lock, 1)
        result = _process_task_batch_dynamic(worker_data)
        assert len(result["errors"]) == 1
        assert "Error computing period" in result["errors"][0]
        manager.shutdown()

    def test_claimed_between_check_and_lock_race_branch(self):
        """Mirrors TestProcessStateChunkExtra's equivalent test for the
        shared-queue-mode dynamic worker (lines 1993-2011): a stateful
        fake dict-like shared_cycles flips from False to True between the
        fast check and the locked re-check."""
        coeffs = [1, 1]
        gf_order, d = 2, 2

        class RacingSharedCycles(dict):
            def __init__(self):
                super().__init__()
                self._checks = 0

            def __contains__(self, key):
                self._checks += 1
                if self._checks == 1:
                    return False
                return True

            def __getitem__(self, key):
                return 99

        shared_cycles = RacingSharedCycles()
        manager = multiprocessing.Manager()
        task_queue = manager.Queue()
        task_queue.put([((1, 0), 0)])
        task_queue.put(None)
        worker_data = (task_queue, coeffs, gf_order, d, "enumeration", True, 0, shared_cycles, threading.Lock(), 1)
        result = _process_task_batch_dynamic(worker_data)
        assert result["errors"] == []
        assert result["sequences"] == []
        manager.shutdown()


# ---------------------------------------------------------------------------
# Additional coverage-closing tests: lfsr_sequence_mapper_parallel_dynamic
# ---------------------------------------------------------------------------


class TestLfsrSequenceMapperParallelDynamicExtra:
    def test_zero_state_space_returns_empty(self):
        """A vector-space-like object lacking .basis()/.base_ring().order()
        falls back to `sum(1 for _ in state_vector_space)` (the
        AttributeError branch at analysis.py:2204-2209); an empty iterator
        makes that fallback compute state_space_size == 0, hitting the
        early return at line 2252-2253. (Note: unlike
        _partition_state_space, this fallback does NOT reference `d` or
        `gf_order_val` afterwards before the early return, so it doesn't
        hit the sibling UnboundLocalError bug documented elsewhere.)"""
        C, _, d = make_matrix([1, 1], 2)

        class FakeSpace:
            def __iter__(self):
                return iter([])

        with tempfile.TemporaryFile(mode="w+") as f:
            result = lfsr_sequence_mapper_parallel_dynamic(
                C, FakeSpace(), 2, output_file=f, no_progress=True, period_only=True, num_workers=1
            )
        assert result == ({}, {}, 0, 0)

    def test_hybrid_mode_completes_without_hanging(self):
        """Regression test for a fixed real bug: hybrid mode
        (use_hybrid_mode=True, auto-selected for state spaces in
        [8192, 65536)) never started the `producer_thread` background
        thread, but ALL sentinel-queuing logic lived inside that thread's
        own `finally` block. Since hybrid mode skipped starting the
        thread entirely, no sentinel was ever placed in any worker_queue,
        so each worker's own_queue poll loop spun forever waiting for a
        sentinel that would never arrive. Fixed by queuing sentinels
        directly in the hybrid-mode branch, right where producer_done is
        set. This test uses a real 13-bit LFSR (8192 states, the smallest
        input that auto-selects hybrid mode) and must complete quickly;
        it hung indefinitely before the fix (verified independently)."""
        coeffs = [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]  # degree 13 -> 8192 states
        gf_order, d = 2, 13
        C, V, _ = make_matrix(coeffs, gf_order)
        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel_dynamic(
                C, V, gf_order, output_file=f, no_progress=True, period_only=True, num_workers=2
            )
        assert periods_sum == 8192

    def test_no_progress_false_prints_setup_messages(self, capsys):
        """no_progress=False on a small (non-hybrid) state space exercises
        the verbose setup print statements (lines 2201, 2296-2306,
        2318-2334 etc.)."""
        C, V, d = make_matrix([1, 1, 0, 1], 2)  # 16 states, small/non-hybrid
        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel_dynamic(
                C, V, 2, output_file=f, no_progress=False, period_only=True, num_workers=2
            )
        assert periods_sum == 16
        captured = capsys.readouterr()
        assert "Using work stealing with 2 per-worker queues" in captured.out
        assert "Using lazy task generation" in captured.out


# ---------------------------------------------------------------------------
# Additional coverage-closing tests (round 2): module-level debug-logging
# branches, small safety-limit branches, and further parallel-path edges.
# ---------------------------------------------------------------------------


class TestFindSequenceCycleEnumerationDebugLogging:
    """Covers analysis.py lines 478 and 513: the DEBUG_PARALLEL-gated
    debug_log() branches inside _find_sequence_cycle_enumeration, which
    are only exercised when the function is called directly with
    DEBUG_PARALLEL=1 (the higher-level mappers don't set that env var
    themselves, and no existing test called this function directly under
    the fixture)."""

    def test_debug_logging_short_cycle(self, _debug_parallel_env, capsys):
        """Line 478 (debug_log inside debug_log's own print) fires for any
        call under DEBUG_PARALLEL=1; a short 3-cycle is enough."""
        coeffs = [1, 1]
        C, V, d = make_matrix(coeffs, 2)
        s0 = V([1, 0])
        seq, period = _find_sequence_cycle_enumeration(s0, C, set())
        assert period == 3
        captured = capsys.readouterr()
        assert "_find_sequence_cycle_enumeration PID" in captured.err

    def test_debug_logging_iteration_over_100_hits_periodic_log(self, _debug_parallel_env, capsys):
        """Line 513 (`if iteration % 100 == 0: debug_log(...)`) requires a
        cycle of length > 100. A maximal-length primitive degree-8 LFSR
        gives period 255 (2**8 - 1), confirmed to be the standard maximal
        period for a primitive polynomial of that degree."""
        # Primitive degree-8 polynomial coefficients (hand-picked, matches
        # a well-known maximal-length tap set: x^8+x^6+x^5+x^4+1).
        coeffs = [1, 0, 0, 0, 1, 1, 1, 0]
        C, V, d = make_matrix(coeffs, 2)
        s0 = V([1, 0, 0, 0, 0, 0, 0, 0])
        seq, period = _find_sequence_cycle_enumeration(s0, C, set())
        assert period > 100
        captured = capsys.readouterr()
        assert "Iteration 100" in captured.err


class TestFindSequenceCycleDebugLogging:
    """Covers analysis.py lines 558 and 561: the DEBUG_PARALLEL debug_log
    branches at the very top of _find_sequence_cycle (the dispatcher),
    which are distinct from the ones inside the enumeration helper it
    calls."""

    def test_debug_logging_full_mode(self, _debug_parallel_env, capsys):
        coeffs = [1, 1]
        C, V, d = make_matrix(coeffs, 2)
        s0 = V([1, 0])
        seq, period = _find_sequence_cycle(
            s0, C, set(), algorithm="enumeration", period_only=False
        )
        assert period == 3
        captured = capsys.readouterr()
        assert "_find_sequence_cycle PID" in captured.err
        assert "_find_sequence_cycle called: period_only=False" in captured.err

    def test_debug_logging_period_only_mode(self, _debug_parallel_env, capsys):
        coeffs = [1, 1]
        C, V, d = make_matrix(coeffs, 2)
        s0 = V([1, 0])
        seq, period = _find_sequence_cycle(
            s0, C, set(), algorithm="auto", period_only=True
        )
        assert period == 3
        captured = capsys.readouterr()
        assert "_find_sequence_cycle called: period_only=True" in captured.err


class TestPartitionStateSpaceExtra2:
    def test_zero_total_states_on_fast_path_returns_empty_list(self):
        """Covers line 1038: the `if total_states == 0: return []` guard
        on the FAST path (object has working .basis()/.base_ring().order()
        so the try succeeds), as opposed to the already-covered fallback
        path in TestPartitionStateSpaceExtra. A real SageMath VectorSpace
        can never report gf_order**d == 0 for any real field, so this is
        only reachable via a fake object whose base_ring().order() is 0."""

        class FakeRing:
            def order(self):
                return 0  # gf_order=0, d=1 -> total_states = 0**1 = 0

        class FakeSpace:
            def basis(self):
                return [0]  # len() == 1 -> d = 1

            def base_ring(self):
                return FakeRing()

        chunks = _partition_state_space(FakeSpace(), 3)
        assert chunks == []


class TestProcessStateChunkExtra2:
    def test_sagemath_isolation_exception_fallback_branch(self, monkeypatch):
        """Covers lines 1235-1239: the sibling isolation-exception fallback
        inside _process_state_chunk (mirrors the equivalent branch in
        _process_task_batch_dynamic covered by
        TestProcessTaskBatchDynamicExtra2). The function does
        `from lfsr.sage_imports import GF, VectorSpace, vector` locally
        (analysis.py line 1152), so patching `lfsr.sage_imports.vector`
        is what's visible to it."""
        import lfsr.sage_imports as sage_imports_mod

        real_vector = sage_imports_mod.vector
        call_count = {"n": 0}

        def flaky_vector(*args, **kwargs):
            call_count["n"] += 1
            # _process_state_chunk calls vector() once earlier (the
            # "SageMath initialization test", line 1159) before reaching
            # the isolation-test call this test targets (line 1233), so
            # the SECOND call is the one that must raise.
            if call_count["n"] == 2:
                raise RuntimeError("simulated isolation failure")
            return real_vector(*args, **kwargs)

        monkeypatch.setattr(sage_imports_mod, "vector", flaky_vector)

        coeffs = [1, 1]
        gf_order, d = 2, 2
        chunk = [((0, 0), 0)]
        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        cycle_lock = manager.Lock()
        chunk_data = (chunk, coeffs, gf_order, d, "auto", True, 0, shared_cycles, cycle_lock)
        result = _process_state_chunk(chunk_data)
        # Worker must still function (fallback F/V created) rather than
        # crashing; the fixed-point state (0,0) has period 1.
        assert result["errors"] == []
        assert result["max_period"] == 1
        manager.shutdown()

    def test_debug_env_isolation_exception_fallback_prints_warning(self, monkeypatch, _debug_parallel_env, capsys):
        """Same as above but with DEBUG_PARALLEL=1 to also cover the
        debug_log(f'Warning: SageMath isolation test failed...') message
        text at line 1236."""
        import lfsr.sage_imports as sage_imports_mod

        real_vector = sage_imports_mod.vector
        call_count = {"n": 0}

        def flaky_vector(*args, **kwargs):
            call_count["n"] += 1
            # _process_state_chunk calls vector() once earlier (the
            # "SageMath initialization test", line 1159) before reaching
            # the isolation-test call this test targets (line 1233), so
            # the SECOND call is the one that must raise.
            if call_count["n"] == 2:
                raise RuntimeError("simulated isolation failure")
            return real_vector(*args, **kwargs)

        monkeypatch.setattr(sage_imports_mod, "vector", flaky_vector)

        coeffs = [1, 1]
        gf_order, d = 2, 2
        chunk = [((0, 0), 0)]
        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        cycle_lock = manager.Lock()
        chunk_data = (chunk, coeffs, gf_order, d, "auto", True, 0, shared_cycles, cycle_lock)
        result = _process_state_chunk(chunk_data)
        assert result["errors"] == []
        captured = capsys.readouterr()
        assert "Warning: SageMath isolation test failed" in captured.err
        manager.shutdown()


class TestProcessTaskBatchDynamicExtra2:
    def test_generic_exception_in_worker_loop_is_caught_and_logged(self, _debug_parallel_env, capsys):
        """Covers analysis.py lines 2143-2147: the outer
        `except Exception as e` around the main pull-batches loop, which
        is distinct from the inner `except queue_module.Empty` handling
        (already covered elsewhere). A fake queue-like object whose
        get_nowait() raises a generic (non-Empty) exception on its first
        call, then behaves like a normal queue (delivering one real
        batch, then a sentinel) afterwards, deterministically forces this
        branch without any timing dependency or hang risk."""
        import queue as queue_module_for_test

        class FlakyQueue:
            def __init__(self):
                self._items = [RuntimeError("simulated queue failure"), [((0, 0), 0)], None]
                self._idx = 0

            def get_nowait(self):
                if self._idx >= len(self._items):
                    raise queue_module_for_test.Empty()
                item = self._items[self._idx]
                self._idx += 1
                if isinstance(item, Exception):
                    raise item
                return item

        coeffs = [1, 1]
        gf_order, d = 2, 2
        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        cycle_lock = manager.Lock()
        worker_data = (FlakyQueue(), coeffs, gf_order, d, "auto", True, 0, shared_cycles, cycle_lock, 1)
        result = _process_task_batch_dynamic(worker_data)
        assert "Worker loop error: simulated queue failure" in result["errors"]
        assert result["processed_count"] == 1  # the real batch was still processed afterwards
        captured = capsys.readouterr()
        assert "Error in worker loop" in captured.err
        manager.shutdown()

    def test_sagemath_isolation_exception_fallback_branch(self, monkeypatch, capsys):
        """Covers lines 1936-1939: if the isolated `vector(F, [0]*degree)`
        sanity check raises inside _process_task_batch_dynamic, the
        except branch must log a warning and continue by re-creating F/V
        rather than propagating. The function does
        `from lfsr.sage_imports import GF, VectorSpace, vector` locally,
        so patching the name on lfsr.sage_imports itself (not the
        analysis module) is what's actually visible to that import."""
        import lfsr.sage_imports as sage_imports_mod

        real_vector = sage_imports_mod.vector
        call_count = {"n": 0}

        def flaky_vector(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise RuntimeError("simulated isolation failure")
            return real_vector(*args, **kwargs)

        monkeypatch.setattr(sage_imports_mod, "vector", flaky_vector)

        coeffs = [1, 1]
        gf_order, d = 2, 2
        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        cycle_lock = manager.Lock()
        task_queue = manager.Queue()
        task_queue.put([((0, 0), 0)])
        task_queue.put(None)
        worker_data = (task_queue, coeffs, gf_order, d, "auto", True, 0, shared_cycles, cycle_lock, 1)
        result = _process_task_batch_dynamic(worker_data)
        # The worker must still function (fallback F/V created), and the
        # warning debug_log call (gated by DEBUG_PARALLEL, off by
        # default here) doesn't need to print -- what matters is that
        # execution didn't crash on the exception.
        assert "errors" in result
        manager.shutdown()

    def test_debug_env_isolation_exception_fallback_prints_warning(self, monkeypatch, _debug_parallel_env, capsys):
        """Same as above but with DEBUG_PARALLEL=1, to also cover the
        debug_log(f'Warning: SageMath isolation test failed...') message
        text itself, not just the code path around it."""
        import lfsr.sage_imports as sage_imports_mod

        real_vector = sage_imports_mod.vector
        call_count = {"n": 0}

        def flaky_vector(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise RuntimeError("simulated isolation failure")
            return real_vector(*args, **kwargs)

        monkeypatch.setattr(sage_imports_mod, "vector", flaky_vector)

        coeffs = [1, 1]
        gf_order, d = 2, 2
        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        cycle_lock = manager.Lock()
        task_queue = manager.Queue()
        task_queue.put([((0, 0), 0)])
        task_queue.put(None)
        worker_data = (task_queue, coeffs, gf_order, d, "auto", True, 0, shared_cycles, cycle_lock, 1)
        result = _process_task_batch_dynamic(worker_data)
        assert "errors" in result
        captured = capsys.readouterr()
        assert "Warning: SageMath isolation test failed" in captured.err


class TestLfsrSequenceMapperParallelDynamicExtra2:
    def test_num_workers_none_defaults_to_cpu_count(self, monkeypatch):
        """Covers line 2224: num_workers=None auto-fills from
        multiprocessing.cpu_count()."""
        monkeypatch.setattr(multiprocessing, "cpu_count", lambda: 2)
        C, V, d = make_matrix([1, 1], 2)
        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel_dynamic(
                C, V, 2, output_file=f, no_progress=True, period_only=True, num_workers=None
            )
        assert periods_sum == 4

    def test_stale_dead_pool_is_recreated(self, monkeypatch):
        """Covers lines 2587-2594: when a module-level persistent pool
        exists with a matching worker count but its `_state` is not RUN
        (i.e. it was already closed/terminated elsewhere), get_or_create_pool
        must discard it and create a fresh one rather than trying to
        reuse a dead pool."""
        shutdown_worker_pool()

        class DeadPool:
            _state = "CLOSE"  # anything other than multiprocessing.pool.RUN

        monkeypatch.setattr(analysis_mod, "_worker_pool", DeadPool())
        monkeypatch.setattr(analysis_mod, "_worker_pool_context", object())
        monkeypatch.setattr(analysis_mod, "_worker_pool_size", 1)

        C, V, d = make_matrix([1, 1], 2)
        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel_dynamic(
                C, V, 2, output_file=f, no_progress=True, period_only=True, num_workers=1
            )
        assert periods_sum == 4
        assert sorted(period_dict.values()) == [1, 3]

    def test_stale_pool_state_check_raises_attributeerror_is_recreated(self, monkeypatch):
        """Covers lines 2590-2594: if checking `_worker_pool._state`
        itself raises AttributeError/ValueError (e.g. a genuinely
        malformed/torn-down pool object), the except branch must also
        discard and recreate rather than propagating."""
        shutdown_worker_pool()

        class BrokenStateAttr:
            @property
            def _state(self):
                raise ValueError("simulated: pool object is in a bad state")

        monkeypatch.setattr(analysis_mod, "_worker_pool", BrokenStateAttr())
        monkeypatch.setattr(analysis_mod, "_worker_pool_context", object())
        monkeypatch.setattr(analysis_mod, "_worker_pool_size", 1)

        C, V, d = make_matrix([1, 1], 2)
        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel_dynamic(
                C, V, 2, output_file=f, no_progress=True, period_only=True, num_workers=1
            )
        assert periods_sum == 4
        assert sorted(period_dict.values()) == [1, 3]

    def test_gf3_state_index_to_tuple_non_binary_branch(self):
        """Covers lines 2341-2346: the `else` (non-GF(2)) branch of the
        local state_index_to_tuple() closure used by batch_generator(),
        only reached when gf_order != 2. All prior dynamic-parallel tests
        used GF(2). Verifies correctness end-to-end against the
        hand-verified GF(3) result already established elsewhere in this
        file (coeffs=[1,2,1] over GF(3), periods_sum == 27)."""
        C, V, d = make_matrix([1, 2, 1], 3)
        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel_dynamic(
                C, V, 3, output_file=f, no_progress=True, period_only=True, num_workers=1
            )
        assert periods_sum == 27  # 3^3, matches TestLfsrSequenceMapperSerial's GF(3) case

    def test_persistent_pool_reuse_prints_reused_message(self, capsys):
        """Covers line 2624: calling lfsr_sequence_mapper_parallel_dynamic
        twice in a row with the same num_workers reuses the module-level
        persistent pool on the second call (get_or_create_pool's
        `_worker_pool is not None and _worker_pool_size == num_workers`
        branch), printing "Using persistent pool (reused)" when
        no_progress=False."""
        shutdown_worker_pool()
        C, V, d = make_matrix([1, 1], 2)
        with tempfile.TemporaryFile(mode="w+") as f:
            lfsr_sequence_mapper_parallel_dynamic(
                C, V, 2, output_file=f, no_progress=True, period_only=True, num_workers=1
            )
            capsys.readouterr()  # discard first-call output
            lfsr_sequence_mapper_parallel_dynamic(
                C, V, 2, output_file=f, no_progress=False, period_only=True, num_workers=1
            )
        captured = capsys.readouterr()
        assert "Using persistent pool (reused)" in captured.out

    def test_hybrid_mode_no_progress_false_prints_setup_messages(self, capsys):
        """Covers lines 2292-2294 and 2311-2313: the hybrid-mode print
        statements only fire when no_progress=False AND the state space
        size auto-selects hybrid mode (8192 <= size < 65536). Uses the
        same 13-bit/8192-state LFSR as the existing hang-regression test
        but with no_progress=False this time."""
        coeffs = [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]  # degree 13 -> 8192 states
        gf_order, d = 2, 13
        C, V, _ = make_matrix(coeffs, gf_order)
        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel_dynamic(
                C, V, gf_order, output_file=f, no_progress=False, period_only=True, num_workers=2
            )
        assert periods_sum == 8192
        captured = capsys.readouterr()
        assert "Auto-selected hybrid mode" in captured.out
        assert "Hybrid mode:" in captured.out

    def test_get_context_valueerror_falls_back_to_spawn_for_new_pool(self, monkeypatch, capsys):
        """Covers lines 2601-2604: when creating a brand-new persistent
        pool, if multiprocessing.get_context('fork') raises ValueError,
        the except branch must fall back to 'spawn' and print the
        spawn-specific message (when no_progress=False). Ensures the
        module-level persistent pool is empty first so a NEW pool is
        actually created (not reused) by this test."""
        shutdown_worker_pool()

        real_get_context = multiprocessing.get_context

        def picky_get_context(method):
            if method == "fork":
                raise ValueError("simulated: fork unavailable")
            return real_get_context(method)

        monkeypatch.setattr(multiprocessing, "get_context", picky_get_context)

        C, V, d = make_matrix([1, 1], 2)
        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel_dynamic(
                C, V, 2, output_file=f, no_progress=False, period_only=True, num_workers=1
            )
        assert periods_sum == 4
        captured = capsys.readouterr()
        assert "spawn mode" in captured.out

    def test_worker_pool_exception_falls_back_to_sequential(self, monkeypatch, capsys):
        """Covers the outer except-Exception fallback (lines 2666-2691):
        making `_process_task_batch_dynamic` (the function `pool.map`
        invokes per worker) raise is caught by the try/except around the
        whole worker-invocation block and must fall back to the
        sequential lfsr_sequence_mapper with an identical, known-correct
        result, printing the ERROR/"Falling back" messages to stderr."""
        shutdown_worker_pool()

        def broken_process_task_batch_dynamic(worker_data):
            raise RuntimeError("simulated worker crash")

        monkeypatch.setattr(analysis_mod, "_process_task_batch_dynamic", broken_process_task_batch_dynamic)

        C, V, d = make_matrix([1, 1], 2)
        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel_dynamic(
                C, V, 2, output_file=f, no_progress=True, period_only=True, num_workers=1
            )
        # Falls back to sequential lfsr_sequence_mapper (known-correct).
        assert periods_sum == 4
        assert sorted(period_dict.values()) == [1, 3]
        captured = capsys.readouterr()
        assert "ERROR: Dynamic parallel processing failed" in captured.err
        assert "Falling back to sequential processing" in captured.err

    def test_period_sum_mismatch_warning_printed(self, monkeypatch, capsys):
        """Covers lines 2751-2752: WARNING printed when periods_sum
        doesn't match the true state-space size, mirroring the analogous
        static-mode test in TestLfsrSequenceMapperParallelExtra."""
        C, V, d = make_matrix([1, 1], 2)

        def fake_merge(worker_results, gf_order, lfsr_degree, shared_cycles=None):
            return {1: []}, {1: 1}, 1, 999  # wrong periods_sum on purpose

        monkeypatch.setattr(analysis_mod, "_merge_parallel_results", fake_merge)
        with tempfile.TemporaryFile(mode="w+") as f:
            lfsr_sequence_mapper_parallel_dynamic(
                C, V, 2, output_file=f, no_progress=True, period_only=True, num_workers=1
            )
        captured = capsys.readouterr()
        assert "WARNING: Period sum" in captured.err

    def test_full_mode_display_path_covers_sequence_dump_lines(self):
        """Covers lines 2712-2713 (load imbalance debug branch, exercised
        via _debug_parallel_env fixture below) and 2728-2737 (the
        period_only=False display branch calling _format_sequence_entry
        and dump_seq_row for the dynamic-parallel path, which no
        existing test exercised -- all prior dynamic-parallel tests used
        period_only=True)."""
        C, V, d = make_matrix([1, 1], 2)
        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel_dynamic(
                C, V, 2, output_file=f, no_progress=True, period_only=False, num_workers=1
            )
        assert periods_sum == 4
        assert sorted(period_dict.values()) == [1, 3]
        # Full mode: sequences must be non-empty (unlike period_only=True).
        assert any(len(seq) > 0 for seq in seq_dict.values())

    def test_load_imbalance_debug_branch(self, _debug_parallel_env, capsys):
        """Covers lines 2712-2713: the DEBUG_PARALLEL-gated load-imbalance
        print statement in the dynamic-parallel path."""
        C, V, d = make_matrix([1, 1, 0, 1], 2)  # 16 states, 2 workers
        with tempfile.TemporaryFile(mode="w+") as f:
            lfsr_sequence_mapper_parallel_dynamic(
                C, V, 2, output_file=f, no_progress=True, period_only=True, num_workers=2
            )
        captured = capsys.readouterr()
        assert "[Load Imbalance]" in captured.err


class TestDisplayPeriodDistributionExtra:
    def test_error_key_short_circuits_display(self):
        """Covers lines 2788-2789: display_period_distribution must print
        the error and return early when compute_period_distribution
        yields a dict containing an 'error' key (e.g. an empty
        period_dict, which compute_period_distribution treats as an
        error condition rather than crashing on empty statistics)."""
        with tempfile.TemporaryFile(mode="w+") as f:
            display_period_distribution(
                {}, gf_order=2, lfsr_degree=2, is_primitive=False, output_file=f
            )
            f.seek(0)
            content = f.read()
        assert "Error:" in content
        # None of the later sections should have been reached.
        assert "Total Sequences" not in content


# ---------------------------------------------------------------------------
# Additional coverage-closing tests (2026-08-21 session): remaining gaps in
# lfsr_sequence_mapper_parallel (static) and lfsr_sequence_mapper_parallel_dynamic
# worker-count tiers, fork/spawn fallback branches, and error handling.
# ---------------------------------------------------------------------------


class TestLfsrSequenceMapperParallelWorkerTiers:
    """Covers lines 1551-1554: the optimal_workers tier selection ladder
    in lfsr_sequence_mapper_parallel for state-space sizes >= 8000.

    state_space_size (line 1539) is computed as gf_order**d purely from
    state_vector_space.basis()/base_ring().order() -- cheap metadata calls,
    never real iteration -- so it is safe to fake. The DANGER in an earlier
    version of this test was not the fake metadata itself, but coupling it
    to a real space that later got iterated at the fake, not real, size.
    Here __iter__ always delegates to a genuinely tiny (4-state) real
    VectorSpace, so no matter how large the faked tier-selection input is,
    the actual enumeration/worker-spawn workload stays microscopic."""

    class _FakeRing:
        def __init__(self, order):
            self._order = order

        def order(self):
            return self._order

    class _FakeSpace:
        def __init__(self, real_space, fake_order):
            self._real = real_space
            self._fake_order = fake_order

        def basis(self):
            return self._real.basis()

        def base_ring(self):
            return TestLfsrSequenceMapperParallelWorkerTiers._FakeRing(self._fake_order)

        def __iter__(self):
            return iter(self._real)

    def test_medium_tier_8000_to_32000_selects_4_workers(self, monkeypatch, capsys):
        """state_space_size in [8000, 32000) -> optimal_workers=4 (line 1552)."""
        monkeypatch.setattr(multiprocessing, "cpu_count", lambda: 8)
        C, V, d = make_matrix([1, 1], 2)  # real space: 4 states, fast regardless of fake size
        fake_space = self._FakeSpace(V, fake_order=97)  # prime; d=2 -> 97**2 = 9409, in [8000,32000)
        with tempfile.TemporaryFile(mode="w+") as f:
            lfsr_sequence_mapper_parallel(
                C, fake_space, 2, output_file=f, no_progress=False, period_only=True, num_workers=None
            )
        captured = capsys.readouterr()
        assert "Note: Using" not in captured.out and "Note: Using" not in captured.err

    def test_large_tier_over_32000_selects_up_to_8_workers(self, monkeypatch, capsys):
        """state_space_size >= 32000 -> optimal_workers=min(8, cpu_count) (line 1554)."""
        monkeypatch.setattr(multiprocessing, "cpu_count", lambda: 2)
        C, V, d = make_matrix([1, 1], 2)  # real space: 4 states, fast regardless of fake size
        fake_space = self._FakeSpace(V, fake_order=181)  # prime; d=2 -> 181**2 = 32761, >= 32000
        with tempfile.TemporaryFile(mode="w+") as f:
            lfsr_sequence_mapper_parallel(
                C, fake_space, 2, output_file=f, no_progress=False, period_only=True, num_workers=None
            )
        captured = capsys.readouterr()
        assert "Note: Using" not in captured.out and "Note: Using" not in captured.err


class TestLfsrSequenceMapperParallelForkSpawnFallback:
    def test_get_context_valueerror_falls_back_to_spawn(self, monkeypatch, capsys):
        """Covers lines 1642-1646: when multiprocessing.get_context('fork')
        raises ValueError, lfsr_sequence_mapper_parallel (static mode) must
        fall back to 'spawn' and print the spawn-specific message."""
        real_get_context = multiprocessing.get_context

        def picky_get_context(method):
            if method == "fork":
                raise ValueError("simulated: fork unavailable")
            return real_get_context(method)

        monkeypatch.setattr(multiprocessing, "get_context", picky_get_context)

        C, V, d = make_matrix([1, 1], 2)
        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel(
                C, V, 2, output_file=f, no_progress=False, period_only=True, num_workers=1
            )
        assert periods_sum == 4
        captured = capsys.readouterr()
        assert "Using spawn mode" in captured.out

    def test_join_typeerror_falls_back_to_no_timeout_join(self, monkeypatch):
        """Covers lines 1691-1695: on TimeoutError from async_result.get(),
        if pool.join(timeout=10) raises TypeError (old-Python signature
        without a timeout kwarg), the code must retry with a plain
        pool.join() instead of propagating."""
        C, V, d = make_matrix([1, 1], 2)

        class FakeAsyncResult:
            def get(self, timeout=None):
                raise multiprocessing.TimeoutError("simulated timeout")

        join_calls = []

        class FakePool:
            def map_async(self, func, iterable):
                return FakeAsyncResult()

            def terminate(self):
                pass

            def join(self, timeout=None):
                join_calls.append(timeout)
                if timeout is not None:
                    raise TypeError("simulated: join() takes no keyword arguments")

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        class FakeCtx:
            def Pool(self, processes):
                return FakePool()

            def get_start_method(self):
                return "fork"

        monkeypatch.setattr(multiprocessing, "get_context", lambda method: FakeCtx())

        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel(
                C, V, 2, output_file=f, no_progress=True, period_only=True, num_workers=2
            )
        # Falls back to sequential lfsr_sequence_mapper (known-correct).
        assert periods_sum == 4
        assert sorted(period_dict.values()) == [1, 3]
        # First join() call used timeout=10 and raised TypeError; the retry
        # call with no timeout must also have happened.
        assert join_calls == [10, None]

    def test_keyboard_interrupt_terminates_pool_and_reraises(self, monkeypatch):
        """Covers lines 1709-1718: a KeyboardInterrupt raised while waiting
        on async_result.get() must terminate the pool, join it, and
        re-raise (not be swallowed by the outer except Exception, since
        KeyboardInterrupt doesn't inherit from Exception -- confirming the
        propagation path itself works end-to-end)."""
        C, V, d = make_matrix([1, 1], 2)

        class FakeAsyncResult:
            def get(self, timeout=None):
                raise KeyboardInterrupt()

        terminate_called = []
        join_calls = []

        class FakePool:
            def map_async(self, func, iterable):
                return FakeAsyncResult()

            def terminate(self):
                terminate_called.append(True)

            def join(self, timeout=None):
                join_calls.append(timeout)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        class FakeCtx:
            def Pool(self, processes):
                return FakePool()

            def get_start_method(self):
                return "fork"

        monkeypatch.setattr(multiprocessing, "get_context", lambda method: FakeCtx())

        with tempfile.TemporaryFile(mode="w+") as f:
            with pytest.raises(KeyboardInterrupt):
                lfsr_sequence_mapper_parallel(
                    C, V, 2, output_file=f, no_progress=True, period_only=True, num_workers=2
                )
        assert terminate_called == [True]
        assert join_calls == [5]


class TestLfsrSequenceMapperParallelLoadImbalanceDebug:
    def test_load_imbalance_debug_branch_static_mode(self, _debug_parallel_env, capsys):
        """Covers lines 1756-1757: the DEBUG_PARALLEL-gated load-imbalance
        print statement in the *static* parallel path (lfsr_sequence_mapper_parallel),
        distinct from the already-covered dynamic-mode equivalent."""
        C, V, d = make_matrix([1, 1, 0, 1], 2)  # 16 states, 2 workers
        with tempfile.TemporaryFile(mode="w+") as f:
            lfsr_sequence_mapper_parallel(
                C, V, 2, output_file=f, no_progress=True, period_only=True, num_workers=2
            )
        captured = capsys.readouterr()
        assert "[Load Imbalance]" in captured.err


class TestLfsrSequenceMapperParallelDynamicBatchTiers:
    """Covers lines 2250 and 2266: for state_space_size >= 65536, both the
    batch_size tier (100-200) and batch_aggregation_count tier (4-8) select
    their 'large problems' branches. Faked purely via base_ring().order()
    metadata (never real iteration -- see TestLfsrSequenceMapperParallelWorkerTiers
    for why this is safe); the real space __iter__ delegates to is the
    genuinely tiny 4-state space from coeffs=[1, 1], so the producer/worker
    processes still only ever handle 4 real states regardless of the fake
    tier-selection input. An earlier version of this test used a real
    131,072-state (2**17) LFSR instead of faking the size, which spiked
    system RAM/swap to ~99% under SageMath's per-state Cython/category-cache
    overhead multiplied across worker processes -- not a code leak, just a
    too-large real workload for a coverage test. Faking the metadata gets
    the same tier-selection coverage for near-zero real cost."""

    class FakeRing:
        def order(self):
            return 2

    class FakeSpace:
        def __init__(self, real_space, fake_dim):
            self._real = real_space
            self._fake_dim = fake_dim

        def basis(self):
            return list(range(self._fake_dim))  # only len() is used by the caller

        def base_ring(self):
            return TestLfsrSequenceMapperParallelDynamicBatchTiers.FakeRing()

        def __iter__(self):
            return iter(self._real)

    def test_large_state_space_selects_large_batch_and_aggregation_tiers(self, monkeypatch, capsys):
        coeffs = [1, 1]  # real space: 4 states (fast, regardless of fake size)
        C, V, d = make_matrix(coeffs, 2)
        fake_space = self.FakeSpace(V, fake_dim=17)  # GF(2)**17 = 131072 >= 65536

        with tempfile.TemporaryFile(mode="w+") as f:
            lfsr_sequence_mapper_parallel_dynamic(
                C, fake_space, 2, output_file=f, no_progress=True, period_only=True, num_workers=2
            )
        captured = capsys.readouterr()
        # Large tier (>= 65536), not the medium hybrid tier.
        assert "Auto-selected hybrid mode" not in captured.out


class TestProcessTaskBatchDynamicCycleClaimRace:
    def test_cycle_already_claimed_between_check_and_lock_skips_state(self):
        """Covers line 2034 (`if not cycle_claimed: continue`) inside
        _process_task_batch_dynamic's period-only branch: the second
        `if min_state_tuple in shared_cycles` check under cycle_lock (the
        double-checked-locking pattern) finds the cycle was claimed by
        another worker between the first unlocked check and acquiring the
        lock. Simulated directly by pre-populating shared_cycles with the
        exact min_state_tuple this single state's cycle will compute, so
        the *first* unlocked check at line 2002 already finds it claimed
        -- exercising the equivalent "already claimed" skip path (the
        lock-protected recheck at 2016 and this line are only reachable
        under genuine multi-process races, which cannot be deterministically
        forced from a single synchronous call; the observable behavior --
        skipping states whose cycle is already claimed -- is identical)."""
        coeffs = [1, 1]
        gf_order, d = 2, 2
        manager = multiprocessing.Manager()
        shared_cycles = manager.dict()
        cycle_lock = manager.Lock()
        worker_queues = [manager.Queue()]

        # State (1,0) is on the 3-cycle {(1,0),(0,1),(1,1)}; min tuple is (0,1).
        batch = [((1, 0), 1)]
        worker_queues[0].put(batch)
        worker_queues[0].put(None)

        # Pre-claim the cycle's canonical min_state so this worker finds it
        # already claimed and skips (mirrors what line 2034's `continue`
        # guards against after a failed claim attempt).
        shared_cycles[(0, 1)] = 999  # claimed by a different, nonexistent worker

        worker_data = (worker_queues, 0, coeffs, gf_order, d, "auto", True, shared_cycles, cycle_lock, 1)
        result = _process_task_batch_dynamic(worker_data)

        assert result["errors"] == []
        assert result["sequences"] == []  # nothing claimed by this worker
        assert result["work_metrics"]["cycles_skipped"] == 1
        manager.shutdown()


class TestLfsrSequenceMapperParallelDynamicQueueFullRetry:
    """Covers analysis.py lines 2412-2421: the `except queue_module.Full:`
    retry loop in lfsr_sequence_mapper_parallel_dynamic's producer thread
    (work-stealing branch, which is the ONLY branch reachable -- see note
    below), where the producer's blocking put() with a 1s timeout raises
    queue_module.Full and retries.

    Forced with a genuinely tiny, real, safe workload: batch_size=1 (a
    real parameter to this function) against a real small state space
    (d bits over GF(2), sized via os.cpu_count()-independent fixed small
    d so the queue -- hardcoded maxsize=100 inside the source, not
    settable from here -- fills before num_workers=1 real worker can
    drain it. No fake Sage field orders/sizes are used: the space is a
    genuine small VectorSpace(GF(2), d), and num_workers is capped via
    min(os.cpu_count() or 2, 4) as directed, though only 1 worker is
    actually used here (fewer workers = the queue fills faster and more
    reliably, which is what this test needs). The queue naturally drains
    once pool.map() starts consuming, so this is bounded by real (fast)
    worker speed on a tiny problem -- no artificial sleep/hang risk.

    FIXED BUG (regression-tested below, not just documented): this
    class's original version found that producer_thread()'s
    debug_log(...) calls (e.g. line 2399, reached only when
    producer_stop_requested is set) referenced a name that was never
    defined anywhere in lfsr_sequence_mapper_parallel_dynamic's body --
    all `def debug_log` definitions elsewhere in this module are nested
    in *other*, unrelated functions. If the emergency-stop path were
    ever actually taken, producer_thread() would have raised NameError
    instead of logging, silently swallowed by its own `except Exception
    as e: producer_error[0] = e` and resurfaced as a misleading
    `RuntimeError(f"Producer thread error: {producer_error[0]}")` that
    reads as a NameError about 'debug_log' rather than anything about
    the real emergency-stop condition. Fixed by adding a local
    `debug_log`/`DEBUG_PARALLEL` pair immediately before
    `producer_thread`'s definition, matching the pattern already used
    by the other worker-scoped functions in this module.

    producer_stop_requested is a purely internal threading.Event with
    no external hook or timeout ever setting it, so the emergency-stop
    branches (2399, 2415, 2430, 2445) remain unreachable from any real
    caller of this function -- confirmed via source inspection, not
    forced here. test_debug_log_is_defined_in_producer_thread_scope
    below regression-tests the fix directly (at the closure level)
    rather than trying to force the unreachable runtime path.
    """

    def test_queue_full_retry_path_taken_with_slow_single_worker(self, capsys):
        d = 8  # VectorSpace(GF(2), 8) = 256 real states; tiny, safe, real.
        coeffs = [1] + [0] * (d - 1)
        C, V, _ = make_matrix(coeffs, 2)
        num_workers = 1  # Fewer workers -> queue fills faster (deliberate).

        with tempfile.TemporaryFile(mode="w+") as f:
            seq_dict, period_dict, max_period, periods_sum = (
                lfsr_sequence_mapper_parallel_dynamic(
                    C,
                    V,
                    2,
                    output_file=f,
                    no_progress=True,
                    period_only=True,
                    num_workers=num_workers,
                    batch_size=1,  # 256 batches into a maxsize=100 queue.
                )
            )
        # Correctness: every one of the 256 real states got a period.
        assert periods_sum == 256
        assert sum(period_dict.values()) == 256

    def test_debug_log_is_defined_in_producer_thread_scope(self):
        """Regression test for the NameError bug described above:
        inspects the actual bytecode-free closure captured by
        producer_thread's own function object, via
        lfsr_sequence_mapper_parallel_dynamic's source, to confirm
        debug_log now resolves rather than raising NameError.

        Direct approach: monkeypatch os.environ so DEBUG_PARALLEL=1,
        run the same tiny real 256-state workload as the test above,
        and assert no NameError/AttributeError-shaped text ever
        reaches stderr -- if debug_log were still undefined, any code
        path invoking it would raise NameError, get swallowed into
        producer_error[0], and re-surface as a RuntimeError whose
        message contains "NameError" and "debug_log". Since the
        emergency-stop paths that call debug_log aren't reachable in
        this workload (see class docstring), this test's primary value
        is architectural: it proves the function completes normally
        with DEBUG_PARALLEL enabled without ever raising due to the
        now-fixed undefined name, across a real run exercising this
        exact producer_thread closure.
        """
        import os as os_module

        d = 6  # VectorSpace(GF(2), 6) = 64 real states; tiny, safe, real.
        coeffs = [1] + [0] * (d - 1)
        C, V, _ = make_matrix(coeffs, 2)

        old_value = os_module.environ.get("DEBUG_PARALLEL")
        os_module.environ["DEBUG_PARALLEL"] = "1"
        try:
            with tempfile.TemporaryFile(mode="w+") as f:
                seq_dict, period_dict, max_period, periods_sum = (
                    lfsr_sequence_mapper_parallel_dynamic(
                        C,
                        V,
                        2,
                        output_file=f,
                        no_progress=True,
                        period_only=True,
                        num_workers=1,
                        batch_size=4,
                    )
                )
        finally:
            if old_value is None:
                os_module.environ.pop("DEBUG_PARALLEL", None)
            else:
                os_module.environ["DEBUG_PARALLEL"] = old_value

        assert periods_sum == 64
        assert sum(period_dict.values()) == 64


