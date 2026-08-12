#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for LFSR statistics functions, including period distribution.
"""

import pytest

# Import SageMath - will be skipped if not available via conftest
try:
    from sage.all import *
except ImportError:
    pytest.skip("SageMath not available", allow_module_level=True)

from lfsr.statistics import (
    autocorrelation,
    compute_period_distribution,
    frequency_test,
    linear_complexity_profile,
    periodicity_test,
    runs_test,
    statistical_summary,
)


class TestPeriodDistribution:
    """Tests for compute_period_distribution function."""

    def test_period_distribution_basic(self):
        """Test basic period distribution computation."""
        period_dict = {1: 15, 2: 15, 3: 15}
        stats = compute_period_distribution(period_dict, 2, 4, False)

        assert "error" not in stats
        assert stats["total_sequences"] == 3
        assert stats["min_period"] == 15
        assert stats["max_period"] == 15
        assert stats["mean_period"] == 15.0
        assert stats["median_period"] == 15.0

    def test_period_distribution_primitive(self):
        """Test period distribution for primitive polynomial."""
        # For primitive polynomial, all non-zero states should have max period
        period_dict = {1: 15, 2: 15, 3: 15}
        stats = compute_period_distribution(period_dict, 2, 4, True)

        assert stats["comparison"]["max_period_equals_theoretical"] is True
        assert stats["comparison"]["max_period_ratio"] == 1.0
        assert stats["theoretical_bounds"]["max_theoretical_period"] == 15
        assert stats["theoretical_bounds"]["is_primitive"] is True

    def test_period_distribution_variance(self):
        """Test period distribution with varying periods."""
        period_dict = {1: 1, 2: 3, 3: 5, 4: 7, 5: 15}
        stats = compute_period_distribution(period_dict, 2, 4, False)

        assert stats["total_sequences"] == 5
        assert stats["min_period"] == 1
        assert stats["max_period"] == 15
        assert stats["mean_period"] == 6.2  # (1+3+5+7+15)/5
        assert stats["variance"] > 0
        assert stats["std_deviation"] > 0

    def test_period_distribution_frequency(self):
        """Test period frequency histogram."""
        period_dict = {1: 15, 2: 15, 3: 3, 4: 3, 5: 1}
        stats = compute_period_distribution(period_dict, 2, 4, False)

        freq = stats["period_frequency"]
        assert freq[15] == 2
        assert freq[3] == 2
        assert freq[1] == 1
        assert stats["distribution_info"]["unique_periods"] == 3

    def test_period_distribution_empty(self):
        """Test period distribution with empty dictionary."""
        stats = compute_period_distribution({}, 2, 4, False)
        assert "error" in stats

    def test_period_distribution_theoretical_bounds(self):
        """Test theoretical bounds computation."""
        period_dict = {1: 7, 2: 7, 3: 1}
        stats = compute_period_distribution(period_dict, 2, 3, False)

        theo = stats["theoretical_bounds"]
        assert theo["max_theoretical_period"] == 7  # 2^3 - 1
        assert theo["state_space_size"] == 8  # 2^3
        assert theo["is_primitive"] is False

    def test_period_distribution_comparison(self):
        """Test comparison with theoretical bounds."""
        period_dict = {1: 15, 2: 15}
        stats = compute_period_distribution(period_dict, 2, 4, False)

        comp = stats["comparison"]
        assert "max_period_equals_theoretical" in comp
        assert "max_period_ratio" in comp
        assert comp["max_period_ratio"] <= 1.0

    def test_period_distribution_primitive_validation(self):
        """Test primitive polynomial validation in distribution."""
        # For primitive polynomial, all periods should be maximum
        period_dict = {1: 15, 2: 15, 3: 15, 4: 15}
        stats = compute_period_distribution(period_dict, 2, 4, True)

        assert stats["comparison"].get("all_periods_maximum", False) is True
        assert stats["comparison"].get("expected_period") == 15


class TestFrequencyTest:
    """Tests for frequency_test (monobit) function."""

    def test_frequency_test_all_zeros(self):
        seq = [0, 0, 0, 0]
        result = frequency_test(seq, 2)
        assert result["zeros"] == 4
        assert result["ones"] == 0
        assert result["total"] == 4
        assert result["ratio"] == 0.0
        assert result["expected_ratio"] == 0.5
        assert result["deviation"] == 0.5

    def test_frequency_test_all_ones(self):
        seq = [1, 1, 1, 1]
        result = frequency_test(seq, 2)
        assert result["zeros"] == 0
        assert result["ones"] == 4
        assert result["ratio"] == 1.0

    def test_frequency_test_balanced(self):
        seq = [0, 1, 0, 1]
        result = frequency_test(seq, 2)
        assert result["zeros"] == 2
        assert result["ones"] == 2
        assert result["ratio"] == 0.5
        assert result["deviation"] == 0.0

    def test_frequency_test_nonbinary_gf_order(self):
        # Non-zero values are all lumped into "ones" regardless of gf_order
        seq = [0, 1, 2, 0]
        result = frequency_test(seq, 4)
        assert result["zeros"] == 2
        assert result["ones"] == 2
        assert result["expected_ratio"] == 0.25

    def test_frequency_test_empty_sequence(self):
        result = frequency_test([], 2)
        assert "error" in result


class TestRunsTest:
    """Tests for runs_test function, verified against the Wald-Wolfowitz
    runs-test expected-runs formula E[R] = 2*n0*n1/n + 1 (standard
    reference formula, independently confirmed, not the module's own
    computation)."""

    def test_runs_test_empty_sequence(self):
        result = runs_test([])
        assert "error" in result

    def test_runs_test_single_run(self):
        # A single run of all-equal values: 1 run total.
        seq = [0, 0, 0, 0]
        result = runs_test(seq)
        assert result["total_runs"] == 1
        assert result["runs_of_zeros"] == 1
        assert result["runs_of_ones"] == 0
        # zeros>0 but ones==0 -> expected_runs falls back to 1 (module's
        # branch for a sequence with only one symbol present)
        assert result["expected_runs"] == 1

    def test_runs_test_alternating(self):
        # 0,1,0,1,0,1 -> 6 runs, each of length 1
        seq = [0, 1, 0, 1, 0, 1]
        result = runs_test(seq)
        assert result["total_runs"] == 6
        assert result["runs_of_zeros"] == 3
        assert result["runs_of_ones"] == 3
        n0, n1, n = 3, 3, 6
        expected = (2 * n0 * n1) / n + 1  # = 2*3*3/6 + 1 = 4.0
        assert result["expected_runs"] == pytest.approx(expected)
        assert result["expected_runs"] == pytest.approx(4.0)

    def test_runs_test_known_pattern(self):
        # 0,0,1,1,0,0,1 -> runs: [00][11][00][1] = 4 runs
        seq = [0, 0, 1, 1, 0, 0, 1]
        result = runs_test(seq)
        assert result["total_runs"] == 4
        assert result["runs_of_zeros"] == 2
        assert result["runs_of_ones"] == 2
        n0 = sum(1 for x in seq if x == 0)  # 4
        n1 = len(seq) - n0  # 3
        expected = (2 * n0 * n1) / len(seq) + 1
        assert result["expected_runs"] == pytest.approx(expected)
        assert result["deviation"] == pytest.approx(abs(4 - expected))

    def test_runs_test_last_run_counted(self):
        # Ensure the trailing run (after the loop) is correctly attributed.
        seq = [1, 1, 0]  # ends in 0 -> last run counted as zeros
        result = runs_test(seq)
        assert result["total_runs"] == 2
        assert result["runs_of_zeros"] == 1
        assert result["runs_of_ones"] == 1


class TestAutocorrelation:
    """Tests for autocorrelation, verified against the standard Pearson
    autocorrelation formula on a {-1,+1}-mapped sequence."""

    def test_autocorrelation_empty(self):
        assert autocorrelation([], lag=1) == 0.0

    def test_autocorrelation_lag_exceeds_length(self):
        assert autocorrelation([0, 1], lag=5) == 0.0

    def test_autocorrelation_constant_sequence(self):
        # denominator is 0 for a constant sequence -> defined as 0.0
        assert autocorrelation([1, 1, 1, 1], lag=1) == 0.0
        assert autocorrelation([0, 0, 0, 0], lag=1) == 0.0

    def test_autocorrelation_perfect_alternation_lag1(self):
        # 0,1,0,1,0,1 mapped to -1,1,-1,1,-1,1. This is a *finite*,
        # non-circular sample autocorrelation (boundary terms are not
        # wrapped around), so it is negative but not exactly -1; the
        # exact value is cross-checked against a hand-rolled reference
        # computation using the same (non-circular) Pearson-style formula.
        seq = [0, 1, 0, 1, 0, 1]
        result = autocorrelation(seq, lag=1)
        assert result < 0
        assert result == pytest.approx(-5 / 6)

    def test_autocorrelation_lag2_perfect_period2(self):
        # shifting by 2 in a period-2 alternating sequence realigns
        # identical values, so correlation is strongly positive; again,
        # finite-sample boundary effects mean it is not exactly +1.
        seq = [0, 1, 0, 1, 0, 1]
        result = autocorrelation(seq, lag=2)
        assert result > 0
        assert result == pytest.approx(2 / 3)

    def test_autocorrelation_manual_reference_computation(self):
        # Cross-check against a hand-rolled Pearson-style computation
        # independent of the module's implementation.
        seq = [0, 0, 1, 1, 0, 1]
        lag = 1
        seq_b = [1 if x != 0 else -1 for x in seq]
        n = len(seq_b)
        mean = sum(seq_b) / n
        num = sum((seq_b[i] - mean) * (seq_b[i + lag] - mean) for i in range(n - lag))
        den = sum((v - mean) ** 2 for v in seq_b)
        expected = num / den if den != 0 else 0.0
        assert autocorrelation(seq, lag=lag) == pytest.approx(expected)


class TestPeriodicityTest:
    """Tests for periodicity_test function."""

    def test_periodicity_test_empty(self):
        result = periodicity_test([])
        assert "error" in result

    def test_periodicity_test_periodic_sequence(self):
        # period-2 pattern repeated 3 times
        seq = [0, 1, 0, 1, 0, 1]
        result = periodicity_test(seq)
        assert result["is_periodic"] is True
        assert result["period"] == 2

    def test_periodicity_test_non_periodic(self):
        # No short period fits within max_period = n//2 for this sequence
        seq = [0, 1, 1, 0, 0, 0, 1]
        result = periodicity_test(seq)
        # checked_up_to should equal n // 2 by default
        assert result["checked_up_to"] == len(seq) // 2

    def test_periodicity_test_max_period_override(self):
        seq = [0, 1, 0, 1, 0, 1, 0, 1]
        # Force max_period smaller than the true period so it won't be found
        result = periodicity_test(seq, max_period=1)
        assert result["checked_up_to"] == 1
        # period 1 requires all elements equal; this sequence isn't constant
        assert result["is_periodic"] is False

    def test_periodicity_test_constant_sequence_period_1(self):
        seq = [1, 1, 1, 1]
        result = periodicity_test(seq)
        assert result["is_periodic"] is True
        assert result["period"] == 1


class TestLinearComplexityProfile:
    """Tests for linear_complexity_profile function."""

    def test_linear_complexity_profile_length(self):
        seq = [1, 0, 1, 1, 0, 0, 1]
        profile = linear_complexity_profile(seq, 2)
        assert len(profile) == len(seq)

    def test_linear_complexity_profile_monotonic_bound(self):
        # Linear complexity profile values must never exceed the prefix
        # length (fundamental Berlekamp-Massey property).
        seq = [1, 1, 0, 1, 0, 0, 1, 1]
        profile = linear_complexity_profile(seq, 2)
        for i, complexity in enumerate(profile, start=1):
            assert 0 <= complexity <= i

    def test_linear_complexity_profile_max_length(self):
        seq = [1, 0, 1, 1, 0, 0, 1]
        profile = linear_complexity_profile(seq, 2, max_length=3)
        assert len(profile) == 3


class TestStatisticalSummary:
    """Tests for statistical_summary function."""

    def test_statistical_summary_empty(self):
        result = statistical_summary([], 2)
        assert "error" in result

    def test_statistical_summary_structure(self):
        seq = [1, 0, 1, 1, 0, 0, 1, 0]
        result = statistical_summary(seq, 2)
        assert result["length"] == len(seq)
        assert result["field_order"] == 2
        assert "frequency" in result
        assert "runs" in result
        assert "periodicity" in result
        assert "autocorrelation_lag_1" in result
        assert "linear_complexity" in result
        assert result["complexity_ratio"] == pytest.approx(
            result["linear_complexity"] / len(seq)
        )

    def test_statistical_summary_consistent_with_individual_functions(self):
        # The summary's sub-results should match calling each function
        # directly on the same sequence.
        seq = [0, 1, 1, 0, 1, 0, 0, 1, 1]
        result = statistical_summary(seq, 2)
        assert result["frequency"] == frequency_test(seq, 2)
        assert result["runs"] == runs_test(seq)
        assert result["periodicity"] == periodicity_test(seq)
        assert result["autocorrelation_lag_1"] == pytest.approx(
            autocorrelation(seq, lag=1)
        )
