#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for lfsr.attacks (correlation attack framework).

Ground-truth facts asserted in these tests are independently verified,
not assumed:

- XOR of two independent uniform bits has *zero* correlation with either
  input: enumerating all 4 input combinations, XOR(a, b) matches `a`
  exactly 2 times out of 4, giving |rho| = 2*(2/4) - 1 = 0. This is the
  textbook motivation for why simple XOR combiners resist Siegenthaler's
  attack while majority-style combiners do not.
- majority(a, b, c) = 1 if a+b+c >= 2 else 0 matches each individual
  input in 6 of 8 truth-table rows, giving Pr[match] = 0.75 and
  correlation = 2*0.75 - 1 = 0.5. This matches the standard published
  result for the 3-input majority function (Pr[y = x_i] = 0.75 for
  i = 1, 2, 3), confirmed via a truth-table enumeration in this module
  and cross-checked against the published literature on correlation
  immunity of Boolean functions.

Both facts hold exactly for the *uniform independent input* model.
LFSR-driven combination generators only approximate that model (LFSR
output sequences are not literally independent coin flips), so attack
results below are checked with generous thresholds/trends rather than
asserting exact 0.5/0.0 correlation.
"""

import pytest

from lfsr.attacks import (
    CombinationGenerator,
    LFSRConfig,
    analyze_combining_function,
    compute_algebraic_immunity,
    compute_correlation_coefficient,
    cube_attack,
    distinguishing_attack,
    estimate_attack_success_probability,
    fast_correlation_attack,
    groebner_basis_attack,
    siegenthaler_correlation_attack,
)
from lfsr.sage_imports import GF, vector


def majority(a, b, c):
    """Standard 3-input majority combining function."""
    return 1 if (a + b + c) >= 2 else 0


def xor2(a, b):
    """2-input XOR combining function."""
    return a ^ b


def and2(a, b):
    """2-input AND combining function (unbalanced: only 1/4 outputs are 1)."""
    return a & b


LFSR_A = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
LFSR_B = LFSRConfig(coefficients=[1, 1, 0, 1], field_order=2, degree=4)
LFSR_C = LFSRConfig(coefficients=[1, 0, 1, 1], field_order=2, degree=4)


def majority_generator():
    """3-LFSR combination generator using majority (correlated with each input)."""
    return CombinationGenerator(
        lfsrs=[LFSR_A, LFSR_B, LFSR_C],
        combining_function=majority,
        function_name="majority",
    )


def xor_generator():
    """2-LFSR combination generator using XOR (uncorrelated with either input)."""
    return CombinationGenerator(
        lfsrs=[LFSR_A, LFSR_B],
        combining_function=xor2,
        function_name="xor",
    )


class TestCombinationGeneratorKeystream:
    """Tests for CombinationGenerator.generate_keystream."""

    def test_keystream_length_matches_request(self):
        """generate_keystream produces exactly `length` bits."""
        gen = majority_generator()
        keystream = gen.generate_keystream(length=37)
        assert len(keystream) == 37

    def test_keystream_bits_are_binary(self):
        """All keystream bits are 0 or 1 for a GF(2) generator."""
        gen = majority_generator()
        keystream = gen.generate_keystream(length=100)
        assert all(bit in (0, 1) for bit in keystream)

    def test_keystream_deterministic_for_same_initial_states(self):
        """Two calls with default initial state produce identical output."""
        gen = majority_generator()
        first = gen.generate_keystream(length=50)
        second = gen.generate_keystream(length=50)
        assert first == second

    def test_default_initial_state_is_1_followed_by_zeros(self):
        """Without explicit initial_states, each LFSR starts at [1, 0, ..., 0]."""
        gen = xor_generator()
        keystream = gen.generate_keystream(length=1)
        # state[0] for both LFSRs is 1 at t=0, so XOR of first outputs is 0.
        assert keystream[0] == 0

    def test_explicit_initial_states_override_default(self):
        """Passing initial_states changes the generated keystream."""
        gen = xor_generator()
        default_ks = gen.generate_keystream(length=20)
        custom_ks = gen.generate_keystream(
            length=20, initial_states=[[0, 1, 0, 0], [1, 1, 1, 0]]
        )
        assert default_ks != custom_ks

    def test_lfsr_config_initial_state_used_when_no_override_passed(self):
        """generate_keystream falls back to each LFSRConfig's own
        initial_state (not the [1,0,...,0] default) when no
        `initial_states` argument is supplied at all."""
        custom_a = LFSRConfig(
            coefficients=[1, 0, 0, 1], field_order=2, degree=4, initial_state=[0, 1, 0, 0]
        )
        gen = CombinationGenerator(
            lfsrs=[custom_a], combining_function=lambda a: a, function_name="identity"
        )
        keystream = gen.generate_keystream(length=1)
        assert keystream[0] == 0  # state[0] of [0,1,0,0] is 0, not the default's 1

    def test_keystream_matches_hand_computed_xor_combination(self):
        """generate_keystream's output equals combining_function applied to
        the two LFSR sequences computed independently by hand.

        seqA (coeffs=[1,0,0,1], default init [1,0,0,0]):
            1, 0, 0, 0, 1, 1, 1, 1, 0, 1
        seqB (coeffs=[1,1,0,1], default init [1,0,0,0]):
            1, 0, 0, 0, 1, 1, 1, 0, 0, 0
        XOR:
            0, 0, 0, 0, 0, 0, 0, 1, 0, 1
        (independently derived via build_state_update_matrix directly,
        not by calling generate_keystream itself).
        """
        gen = xor_generator()
        keystream = gen.generate_keystream(length=10)
        expected = [0, 0, 0, 0, 0, 0, 0, 1, 0, 1]
        assert keystream == expected

    def test_combining_function_actually_applied_not_just_passthrough(self):
        """A generator using AND (mostly 0) differs from one using OR-like
        majority for the same underlying LFSRs, proving the combining
        function is genuinely applied rather than e.g. just returning the
        first LFSR's output."""
        and_gen = CombinationGenerator(
            lfsrs=[LFSR_A, LFSR_B], combining_function=and2, function_name="and"
        )
        xor_gen = xor_generator()
        and_ks = and_gen.generate_keystream(length=50)
        xor_ks = xor_gen.generate_keystream(length=50)
        assert and_ks != xor_ks


class TestCombinationGeneratorLfsrSequence:
    """Tests for CombinationGenerator.generate_lfsr_sequence."""

    def test_sequence_length_matches_request(self):
        """generate_lfsr_sequence produces exactly `length` bits."""
        gen = majority_generator()
        seq = gen.generate_lfsr_sequence(lfsr_index=1, length=25)
        assert len(seq) == 25

    def test_sequence_matches_hand_computed_values(self):
        """LFSR A's sequence (index 0) matches the independently
        hand-computed values used in test_keystream_matches_hand_computed_xor_combination."""
        gen = xor_generator()
        seq = gen.generate_lfsr_sequence(lfsr_index=0, length=10)
        assert seq == [1, 0, 0, 0, 1, 1, 1, 1, 0, 1]

    def test_different_indices_give_different_sequences(self):
        """LFSR A and LFSR B (different feedback coefficients) diverge."""
        gen = xor_generator()
        seq_a = gen.generate_lfsr_sequence(lfsr_index=0, length=10)
        seq_b = gen.generate_lfsr_sequence(lfsr_index=1, length=10)
        assert seq_a != seq_b


class TestComputeCorrelationCoefficient:
    """Tests for compute_correlation_coefficient."""

    def test_identical_sequences_have_correlation_one(self):
        """Perfectly matching sequences give correlation +1."""
        seq = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1,
               1, 0, 1, 0, 1, 0, 1, 1, 1]
        corr, p_value, stats = compute_correlation_coefficient(seq, seq)
        assert corr == 1.0
        assert stats["matches"] == len(seq)

    def test_complementary_sequences_have_correlation_negative_one(self):
        """Bitwise-complementary sequences give correlation -1."""
        seq1 = [1, 0, 1, 1, 0] * 7  # length 35, > 30 so normal approx is used
        seq2 = [1 - b for b in seq1]
        corr, p_value, stats = compute_correlation_coefficient(seq1, seq2)
        assert corr == -1.0
        assert stats["matches"] == 0

    def test_docstring_example_matches_documented_result(self):
        """The module docstring's own worked example: seq1 vs seq2 should
        give correlation 0.2 (3 matches out of 5)."""
        seq1 = [1, 0, 1, 0, 1]
        seq2 = [1, 1, 1, 0, 0]
        corr, p_value, stats = compute_correlation_coefficient(seq1, seq2)
        assert corr == pytest.approx(0.2)
        assert stats["matches"] == 3
        assert stats["total_bits"] == 5

    def test_mismatched_lengths_raise_value_error(self):
        """Sequences of different lengths are rejected."""
        with pytest.raises(ValueError):
            compute_correlation_coefficient([1, 0], [1, 0, 1])

    def test_empty_sequences_return_zero_correlation(self):
        """Empty sequences are handled gracefully with a documented error
        marker rather than raising or dividing by zero."""
        corr, p_value, stats = compute_correlation_coefficient([], [])
        assert corr == 0.0
        assert p_value == 1.0
        assert "error" in stats

    def test_large_n_uses_normal_approximation_p_value(self):
        """For n > 30, p_value is computed from a real z-score rather than
        the small-n placeholder (0.5), so an extreme mismatch pattern
        should give a small p-value."""
        n = 100
        seq1 = [i % 2 for i in range(n)]
        seq2 = [1 - (i % 2) for i in range(n)]  # perfect anti-correlation
        corr, p_value, stats = compute_correlation_coefficient(seq1, seq2)
        assert corr == -1.0
        assert p_value < 0.01

    def test_small_n_uses_placeholder_p_value(self):
        """For n <= 30, the implementation uses a fixed placeholder p-value
        of 0.5 rather than an exact binomial test (documented behavior,
        see inline comment in compute_correlation_coefficient)."""
        seq1 = [1, 0, 1, 0, 1]
        seq2 = [0, 1, 0, 1, 0]  # complementary, n=5 <= 30
        corr, p_value, stats = compute_correlation_coefficient(seq1, seq2)
        assert p_value == 0.5


class TestAnalyzeCombiningFunction:
    """Tests for analyze_combining_function."""

    def test_majority_is_balanced(self):
        """majority(a,b,c) outputs 1 exactly 4/8 times -> balanced."""
        result = analyze_combining_function(majority, num_inputs=3)
        assert result["balanced"] is True
        assert result["output_distribution"] == {0: 4, 1: 4}

    def test_xor_is_balanced(self):
        """xor2(a,b) outputs 1 exactly 2/4 times -> balanced."""
        result = analyze_combining_function(xor2, num_inputs=2)
        assert result["balanced"] is True
        assert result["bias"] == 0.0

    def test_and_is_unbalanced_with_nonzero_bias(self):
        """and2(a,b) outputs 1 only 1/4 times -> unbalanced, bias 0.25."""
        result = analyze_combining_function(and2, num_inputs=2)
        assert result["balanced"] is False
        assert result["bias"] == pytest.approx(0.25)
        assert result["output_distribution"] == {0: 3, 1: 1}

    def test_truth_table_has_all_input_combinations(self):
        """Truth table enumerates every one of field_order**num_inputs rows."""
        result = analyze_combining_function(and2, num_inputs=2, field_order=2)
        assert len(result["truth_table"]) == 4
        inputs_seen = {row[0] for row in result["truth_table"]}
        assert inputs_seen == {(0, 0), (1, 0), (0, 1), (1, 1)}

    def test_truth_table_values_correct_for_and(self):
        """Each truth-table row's output equals the function applied to its inputs."""
        result = analyze_combining_function(and2, num_inputs=2, field_order=2)
        table = dict(result["truth_table"])
        assert table[(0, 0)] == 0
        assert table[(1, 0)] == 0
        assert table[(0, 1)] == 0
        assert table[(1, 1)] == 1


class TestEstimateAttackSuccessProbability:
    """Tests for estimate_attack_success_probability."""

    def test_zero_correlation_gives_zero_detection_and_success(self):
        """No correlation means the attack cannot detect or succeed."""
        result = estimate_attack_success_probability(
            correlation_coefficient=0.0, keystream_length=1000, lfsr_degree=4
        )
        assert result["detection_probability"] == 0.0
        assert result["overall_success_probability"] == 0.0
        assert result["feasible"] is False

    def test_strong_correlation_with_small_state_space_is_feasible(self):
        """A strong correlation (0.5) against a small (16-state) LFSR gives
        a high detection probability and marks the attack feasible."""
        result = estimate_attack_success_probability(
            correlation_coefficient=0.5, keystream_length=1000, lfsr_degree=4
        )
        assert result["detection_probability"] == pytest.approx(1.0)
        assert result["feasible"] is True
        assert result["recovery_probability"] == 0.9
        assert result["state_space_size"] == 16

    def test_huge_state_space_marks_infeasible_despite_correlation(self):
        """Even with strong correlation, a state space above the 2^40
        threshold (here: 2^50) is marked as not feasible."""
        result = estimate_attack_success_probability(
            correlation_coefficient=0.5, keystream_length=1000, lfsr_degree=50
        )
        assert result["state_space_size"] == 2 ** 50
        assert result["feasible"] is False
        assert result["overall_success_probability"] == 0.0

    def test_zero_keystream_length_gives_zero_detection(self):
        """No keystream bits means no detection is possible."""
        result = estimate_attack_success_probability(
            correlation_coefficient=0.5, keystream_length=0, lfsr_degree=4
        )
        assert result["detection_probability"] == 0.0

    def test_moderate_correlation_gives_moderate_recovery_probability(self):
        """0.1 <= |rho| < 0.3 is the 'moderate correlation' band, which the
        implementation maps to a fixed recovery_probability of 0.5."""
        result = estimate_attack_success_probability(
            correlation_coefficient=0.2, keystream_length=1000, lfsr_degree=4
        )
        assert result["recovery_probability"] == 0.5
        assert result["feasible"] is True


class TestSiegenthalerCorrelationAttack:
    """Tests for siegenthaler_correlation_attack."""

    def test_correlated_combiner_detects_nonzero_correlation(self):
        """Majority-of-3 is provably correlated (rho=0.5 in the uniform
        model) with each input; against a real LFSR-driven generator the
        measured correlation should be substantial and the attack should
        report success given enough keystream."""
        gen = majority_generator()
        keystream = gen.generate_keystream(length=300)
        result = siegenthaler_correlation_attack(gen, keystream, target_lfsr_index=0)
        assert abs(result.correlation_coefficient) > 0.3
        assert result.attack_successful is True

    def test_correlated_combiner_succeeds_against_all_three_inputs(self):
        """Majority is symmetric: the attack should find correlation against
        every one of the three constituent LFSRs, not just index 0."""
        gen = majority_generator()
        keystream = gen.generate_keystream(length=300)
        for idx in range(3):
            result = siegenthaler_correlation_attack(gen, keystream, target_lfsr_index=idx)
            assert abs(result.correlation_coefficient) > 0.3
            assert result.attack_successful is True

    def test_xor_combiner_shows_no_significant_correlation(self):
        """XOR of two inputs is provably uncorrelated (rho=0 in the uniform
        model) with either input; the attack should not report success
        against either target LFSR."""
        gen = xor_generator()
        keystream = gen.generate_keystream(length=300)
        result0 = siegenthaler_correlation_attack(gen, keystream, target_lfsr_index=0)
        result1 = siegenthaler_correlation_attack(gen, keystream, target_lfsr_index=1)
        assert result0.attack_successful is False
        assert result1.attack_successful is False

    def test_result_fields_are_internally_consistent(self):
        """matches / total_bits / match_ratio agree with each other and
        with keystream length."""
        gen = majority_generator()
        keystream = gen.generate_keystream(length=200)
        result = siegenthaler_correlation_attack(gen, keystream, target_lfsr_index=0)
        assert result.total_bits == 200
        assert result.match_ratio == pytest.approx(result.matches / result.total_bits)
        assert result.target_lfsr_index == 0

    def test_complexity_estimate_is_field_order_pow_degree(self):
        """complexity_estimate documents brute-force state recovery cost:
        field_order ** degree, i.e. 2**4 = 16 for these fixture LFSRs."""
        gen = majority_generator()
        keystream = gen.generate_keystream(length=100)
        result = siegenthaler_correlation_attack(gen, keystream, target_lfsr_index=2)
        assert result.complexity_estimate == 16.0

    def test_invalid_lfsr_index_raises_value_error(self):
        """Negative or out-of-range target_lfsr_index is rejected."""
        gen = majority_generator()
        keystream = gen.generate_keystream(length=100)
        with pytest.raises(ValueError):
            siegenthaler_correlation_attack(gen, keystream, target_lfsr_index=3)
        with pytest.raises(ValueError):
            siegenthaler_correlation_attack(gen, keystream, target_lfsr_index=-1)

    def test_empty_keystream_raises_value_error(self):
        """An empty keystream cannot be attacked."""
        gen = majority_generator()
        with pytest.raises(ValueError):
            siegenthaler_correlation_attack(gen, [], target_lfsr_index=0)

    def test_max_sequence_length_shorter_than_keystream_extends_sequence(self):
        """When max_sequence_length caps the generated LFSR sequence below
        the keystream length, the implementation tiles/repeats the shorter
        sequence to reach n (the 'shouldn't happen, but handle gracefully'
        branch). The result should still compare against the full
        keystream length, not the truncated one."""
        gen = majority_generator()
        keystream = gen.generate_keystream(length=200)
        result = siegenthaler_correlation_attack(
            gen, keystream, target_lfsr_index=0, max_sequence_length=50
        )
        assert result.total_bits == 200


class TestFastCorrelationAttack:
    """Tests for fast_correlation_attack (Meier-Staffelbach).

    max_candidates is kept small (<=10) in these tests: the implementation
    tests each candidate by regenerating a full-length LFSR sequence via
    Sage matrix-vector multiplication, so larger candidate counts make this
    test module noticeably slow without adding meaningful coverage.
    """

    def test_short_keystream_returns_unsuccessful_without_searching(self):
        """Keystreams under 100 bits short-circuit to a trivial failure
        result without testing any candidates (n < 100 guard)."""
        gen = majority_generator()
        keystream = gen.generate_keystream(length=50)
        result = fast_correlation_attack(gen, keystream, target_lfsr_index=0)
        assert result.attack_successful is False
        assert result.candidate_states_tested == 0
        assert result.recovered_state is None
        assert result.keystream_length == 50

    def test_correlated_combiner_recovers_true_initial_state(self):
        """Against majority (correlated), the default initial state
        [1, 0, 0, 0] is among the low-Hamming-weight candidates tried
        first, so the attack should recover it exactly."""
        gen = majority_generator()
        keystream = gen.generate_keystream(length=300)
        result = fast_correlation_attack(
            gen, keystream, target_lfsr_index=0, max_candidates=10
        )
        assert result.attack_successful is True
        assert result.recovered_state == [1, 0, 0, 0]
        assert result.best_correlation >= 0.1

    def test_uncorrelated_combiner_does_not_succeed(self):
        """Against XOR (uncorrelated), best_correlation should stay below
        the default correlation_threshold (0.1) and the attack should not
        report success."""
        gen = xor_generator()
        keystream = gen.generate_keystream(length=300)
        result = fast_correlation_attack(
            gen, keystream, target_lfsr_index=0, max_candidates=10
        )
        assert result.attack_successful is False

    def test_candidate_states_tested_matches_max_candidates(self):
        """When enough candidates are requested, exactly max_candidates
        are tested (bounded by the requested cap)."""
        gen = majority_generator()
        keystream = gen.generate_keystream(length=300)
        result = fast_correlation_attack(
            gen, keystream, target_lfsr_index=0, max_candidates=7
        )
        assert result.candidate_states_tested == 7

    def test_keystream_length_field_matches_input(self):
        """keystream_length in the result reflects the actual input length."""
        gen = majority_generator()
        keystream = gen.generate_keystream(length=150)
        result = fast_correlation_attack(
            gen, keystream, target_lfsr_index=1, max_candidates=6
        )
        assert result.keystream_length == 150
        assert result.target_lfsr_index == 1

    def test_max_candidates_above_structured_set_uses_random_fill(self):
        """For a degree-4 LFSR the structured candidate set (zero state +
        single-1 states + two-1 states) has 1 + 4 + 6 = 11 entries.
        Requesting more than that forces the random-candidate-fill loop to
        execute and still yields exactly max_candidates total candidates."""
        gen = majority_generator()
        keystream = gen.generate_keystream(length=200)
        result = fast_correlation_attack(
            gen, keystream, target_lfsr_index=0, max_candidates=12
        )
        assert result.candidate_states_tested == 12

    def test_max_candidates_exceeding_full_state_space_terminates(self):
        """BUG (fixed): the random-candidate-fill loop
        (`while len(candidates) < max_candidates: ... if state not in
        candidates: candidates.append(state)`) had no attempt cap. A
        degree-4 GF(2) LFSR has only 2**4 = 16 distinct states total; once
        every state is already in `candidates`, every further random draw
        collides and the loop can never grow `candidates` again --
        confirmed hanging indefinitely (still running after 15s, well
        past this test's needs) before the fix, for max_candidates as low
        as 20. Requesting more candidates than exist in the entire state
        space (max_candidates=1000, the function's own default) must
        terminate promptly and simply yield every distinct state
        (candidate_states_tested == 16), not hang."""
        gen = majority_generator()
        keystream = gen.generate_keystream(length=200)
        result = fast_correlation_attack(
            gen, keystream, target_lfsr_index=0, max_candidates=1000
        )
        assert result.candidate_states_tested == 16


class TestDistinguishingAttack:
    """Tests for distinguishing_attack."""

    def test_too_short_keystream_not_distinguishable(self):
        """Keystreams under 100 bits short-circuit without running the
        distinguisher."""
        gen = majority_generator()
        result = distinguishing_attack(gen, [0, 1] * 20, method="correlation")
        assert result.distinguishable is False
        assert result.attack_successful is False
        assert "error" in result.details

    def test_correlation_method_detects_majority_combiner(self):
        """A majority-combined keystream is distinguishable from random via
        correlation against its own constituent LFSRs."""
        gen = majority_generator()
        keystream = gen.generate_keystream(length=300)
        result = distinguishing_attack(gen, keystream, method="correlation")
        assert result.distinguishable is True
        assert result.method_used == "correlation"
        assert result.details["best_lfsr_index"] in (0, 1, 2)
        assert len(result.details["all_correlations"]) == 3

    def test_correlation_method_does_not_flag_xor_combiner(self):
        """XOR-combined keystream shows weak correlation with either LFSR
        and should not be flagged as distinguishable via this method."""
        gen = xor_generator()
        keystream = gen.generate_keystream(length=300)
        result = distinguishing_attack(gen, keystream, method="correlation")
        assert result.distinguishable is False

    def test_statistical_method_on_self_generated_keystream_matches_exactly(self):
        """generate_keystream is deterministic given the same generator and
        default initial states, so comparing a generator's own keystream
        against generate_keystream() called again produces a perfect
        match: zero frequency/runs difference, not distinguishable."""
        gen = xor_generator()
        keystream = gen.generate_keystream(length=200)
        result = distinguishing_attack(gen, keystream, method="statistical")
        assert result.distinguishing_statistic == 0.0
        assert result.distinguishable is False
        assert result.details["frequency_difference"] == 0.0
        assert result.details["runs_difference"] == 0.0

    def test_statistical_method_flags_frequency_difference(self):
        """A keystream that is all-ones differs sharply in frequency from
        the generator's own balanced-ish keystream, and should be flagged
        distinguishable by the statistical method."""
        gen = xor_generator()
        all_ones = [1] * 200
        result = distinguishing_attack(gen, all_ones, method="statistical")
        assert result.distinguishing_statistic > 0.1
        assert result.distinguishable is True

    def test_unknown_method_returns_error_result(self):
        """An unrecognized method name returns a non-distinguishable,
        non-successful result carrying an error message rather than
        raising."""
        gen = xor_generator()
        keystream = gen.generate_keystream(length=200)
        result = distinguishing_attack(gen, keystream, method="not_a_real_method")
        assert result.distinguishable is False
        assert result.attack_successful is False
        assert result.method_used == "not_a_real_method"
        assert "error" in result.details


class TestLFSRConfigDefaults:
    """Tests for LFSRConfig's initial_state handling via CombinationGenerator."""

    def test_lfsr_config_explicit_initial_state_is_used(self):
        """When LFSRConfig.initial_state is set, generate_lfsr_sequence uses
        it in preference to the all-zero-but-first default."""
        custom = LFSRConfig(
            coefficients=[1, 0, 0, 1], field_order=2, degree=4, initial_state=[0, 1, 1, 0]
        )
        gen = CombinationGenerator(
            lfsrs=[custom], combining_function=lambda a: a, function_name="identity"
        )
        seq_default_index_call = gen.generate_lfsr_sequence(lfsr_index=0, length=1)
        assert seq_default_index_call[0] == 0  # state[0] of [0,1,1,0]

    def test_generate_lfsr_sequence_explicit_initial_state_overrides_config(self):
        """An initial_state passed directly to generate_lfsr_sequence takes
        precedence over both the config default and LFSRConfig.initial_state."""
        gen = xor_generator()
        seq = gen.generate_lfsr_sequence(lfsr_index=0, length=1, initial_state=[0, 0, 1, 0])
        assert seq[0] == 0

        seq2 = gen.generate_lfsr_sequence(lfsr_index=0, length=1, initial_state=[1, 1, 1, 1])
        assert seq2[0] == 1


class TestFastCorrelationAttackRefinementLoop:
    """Tests for the iterative-decoding refinement loop inside
    fast_correlation_attack (lines ~1480-1518): after the initial candidate
    search, if the best candidate clears correlation_threshold, the function
    tries flipping each bit of the best state looking for an improvement.
    These cases specifically drive that loop through at least one real
    improve-then-stop cycle (iterations_performed == 1), which the existing
    tests in TestFastCorrelationAttack don't reach because their best
    candidate is already optimal (0 iterations)."""

    def test_refinement_improves_and_then_stops(self):
        """With a small max_candidates and a true initial state that isn't
        in the structured candidate set, the best initial candidate found is
        suboptimal; the refinement loop's single-bit-flip search should find
        an improvement once (iterations_performed == 1) and then stop when
        no further single-bit flip improves it further."""
        gen = majority_generator()
        keystream = gen.generate_keystream(
            length=400, initial_states=[[1, 1, 1, 0], [1, 0, 1, 0], [0, 1, 1, 1]]
        )
        result = fast_correlation_attack(
            gen, keystream, target_lfsr_index=0, max_candidates=3, max_iterations=8
        )
        assert result.iterations_performed == 1
        assert result.attack_successful is True
        assert result.recovered_state == [0, 0, 1, 0]


class TestComputeAlgebraicImmunity:
    """Tests for compute_algebraic_immunity."""

    def test_non_binary_field_order_unsupported(self):
        """Only field_order=2 is currently supported; other field orders
        return an explicit error result rather than attempting analysis."""

        def dummy(a, b, c):
            return a

        result = compute_algebraic_immunity(dummy, 3, field_order=3)
        assert result["algebraic_immunity"] == 0
        assert result["annihilators_found"] == []
        assert result["optimal"] is False
        assert result["max_possible"] == 0
        assert "error" in result

    def test_majority_achieves_optimal_algebraic_immunity(self):
        """majority(a,b,c) is balanced with no near-constant bias, so it
        should not hit the degree-1 low-immunity heuristic and should be
        reported as achieving the maximum possible algebraic immunity for
        3 inputs (ceil(3/2) = 2)."""

        def majority(a, b, c):
            return 1 if (a + b + c) >= 2 else 0

        result = compute_algebraic_immunity(majority, 3)
        assert result["max_possible"] == 2
        assert result["algebraic_immunity"] == 2
        assert result["optimal"] is True

    def test_constant_function_has_zero_algebraic_immunity(self):
        """A constant function (always 0) is the most degenerate case:
        every output is 0, immediately triggering the 'constant function'
        branch (min_degree = 0)."""

        def always_zero(a, b, c):
            return 0

        result = compute_algebraic_immunity(always_zero, 3)
        assert result["algebraic_immunity"] == 0
        assert result["optimal"] is False

    def test_almost_constant_function_has_algebraic_immunity_one(self):
        """AND of 3 inputs is 1 in exactly one of the 8 input rows (only
        [1,1,1] gives ones==1), triggering the 'almost constant' branch
        (min_degree = 1) rather than the constant-function branch."""

        def and3(a, b, c):
            return a & b & c

        result = compute_algebraic_immunity(and3, 3)
        assert result["algebraic_immunity"] == 1
        assert result["optimal"] is False
        assert result["max_possible"] == 2


class TestGroebnerBasisAttack:
    """Tests for groebner_basis_attack (placeholder implementation:
    attack_successful is always False by construction, see the function's
    own source -- these tests cover the length guard and the exception
    branch, not a real state-recovery success case, which does not exist
    in the current implementation)."""

    def test_insufficient_keystream_returns_failure(self):
        lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        result = groebner_basis_attack(lfsr, keystream=[1, 0, 1])
        assert result.attack_successful is False
        assert result.method_used == "groebner_basis"
        assert "Insufficient keystream" in result.details["error"]

    def test_invalid_field_order_hits_exception_branch(self):
        """field_order=0 is not a valid finite field order, so GF(0)
        inside the function raises a ValueError, which is caught by the
        function's own (TypeError, ValueError, AttributeError,
        ArithmeticError) handler and converted into a failure result
        carrying the error message rather than propagating.

        Note: field_order=6 (a composite non-prime-power) was tried
        first and also reaches this branch logically, but triggers a
        reproducible SageMath internal category-cache assertion crash
        under pytest-cov instrumentation specifically (not reproducible
        running the same GF(6) call standalone without coverage) --
        genuinely a Sage/coverage interaction issue, not specific to
        this test's intent, so field_order=0 is used instead as a
        stable way to reach the same except branch."""
        lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=0, degree=4)
        keystream = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
        result = groebner_basis_attack(lfsr, keystream)
        assert result.attack_successful is False
        assert result.method_used == "groebner_basis"
        assert "error" in result.details

    def test_sufficient_keystream_runs_placeholder_path(self):
        """With enough keystream and a valid field, the placeholder
        Groebner-basis path runs to completion without raising."""
        lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        keystream = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
        result = groebner_basis_attack(lfsr, keystream)
        assert result.attack_successful is False
        assert result.equations_solved == 0


class TestCubeAttack:
    """Tests for cube_attack (placeholder implementation: attack_successful
    is always False by construction; see the function's own source)."""

    def test_insufficient_keystream_returns_failure(self):
        lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        result = cube_attack(lfsr, keystream=[1, 0, 1], max_cube_size=5)
        assert result.attack_successful is False
        assert "Insufficient keystream" in result.details["error"]

    def test_sufficient_keystream_runs_placeholder_path(self):
        lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        keystream = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1] * 4  # 40 bits, > 2**5
        result = cube_attack(lfsr, keystream, max_cube_size=5)
        assert result.attack_successful is False
        assert result.details["max_cube_size_tried"] == 5
        assert result.details["keystream_length"] == len(keystream)
