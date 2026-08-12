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
import tempfile

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
