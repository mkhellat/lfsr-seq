#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Coverage tests for lfsr.ml.anomaly_detection: statistical and
isolation-forest sequence anomaly detection, distribution anomaly
detection (bound violations, primitive-expectation violations,
frequency outliers), and the detect_all_anomalies dispatcher.

Complements the existing (light) coverage in test_ml.py."""

import builtins
import sys

import pytest

import lfsr.ml.anomaly_detection as anomdet
from lfsr.ml.anomaly_detection import (
    Anomaly,
    detect_all_anomalies,
    detect_distribution_anomalies,
    detect_sequence_anomalies,
)


def _reimport_with_blocked_import(module_name, blocked_name):
    """Force a fresh import of `module_name` with `import blocked_name`
    made to raise ImportError, to exercise the module's own `except
    ImportError: HAS_X = False` fallback branch at definition time --
    not just testing behavior with the flag pre-set to False (which
    other tests in this file already do via monkeypatch.setattr), since
    that never actually executes the except block itself. Returns the
    freshly imported module; caller is responsible for restoring
    sys.modules afterward."""
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == blocked_name:
            raise ImportError(f"simulated: {blocked_name} unavailable")
        return real_import(name, *args, **kwargs)

    if module_name in sys.modules:
        del sys.modules[module_name]

    builtins.__import__ = fake_import
    try:
        import importlib

        return importlib.import_module(module_name)
    finally:
        builtins.__import__ = real_import


class TestDetectSequenceAnomaliesStatistical:
    def test_no_anomalies_in_uniform_sequence(self):
        seq = [5] * 20
        # std == 0 -> early return, no anomalies (line ~94-95)
        anomalies = detect_sequence_anomalies(seq, method="statistical")
        assert anomalies == []

    def test_detects_outlier(self):
        seq = [1, 1, 1, 1, 1, 1, 1, 1, 1, 100]
        anomalies = detect_sequence_anomalies(seq, method="statistical")
        assert len(anomalies) == 1
        a = anomalies[0]
        assert isinstance(a, Anomaly)
        assert a.anomaly_type == "statistical_outlier"
        assert a.location == 9
        assert a.metadata["value"] == 100
        assert 0.0 < a.severity <= 1.0

    def test_no_outliers_in_normal_range(self):
        seq = [1, 2, 3, 2, 1, 2, 3, 2, 1, 2]
        anomalies = detect_sequence_anomalies(seq, method="statistical")
        assert anomalies == []

    def test_fallback_matches_numpy_path(self, monkeypatch):
        seq = [1, 1, 1, 1, 1, 1, 1, 1, 1, 100]
        anomalies_np = detect_sequence_anomalies(seq, method="statistical")

        monkeypatch.setattr(anomdet, "HAS_NUMPY", False)
        anomalies_fb = detect_sequence_anomalies(seq, method="statistical")

        assert len(anomalies_fb) == len(anomalies_np)
        assert anomalies_fb[0].location == anomalies_np[0].location
        assert anomalies_fb[0].severity == pytest.approx(anomalies_np[0].severity)


class TestDetectSequenceAnomaliesIsolationForest:
    def test_too_short_sequence_returns_empty(self):
        seq = [1, 2, 3]  # < 10
        anomalies = detect_sequence_anomalies(seq, method="isolation_forest")
        assert anomalies == []

    def test_isolation_forest_runs_and_returns_anomaly_objects(self):
        # 30 mostly-similar values plus a clear outlier block, long
        # enough to produce several sliding windows.
        seq = [1, 0] * 14 + [9, 9]
        anomalies = detect_sequence_anomalies(seq, method="isolation_forest")
        assert isinstance(anomalies, list)
        for a in anomalies:
            assert isinstance(a, Anomaly)
            assert a.anomaly_type == "isolation_forest_anomaly"
            assert a.severity == 0.7
            assert "window_start" in a.metadata
            assert "window_size" in a.metadata

    def test_isolation_forest_without_sklearn_returns_empty(self, monkeypatch):
        """method == 'isolation_forest' requires HAS_SKLEARN; when False
        the elif condition fails entirely and no anomalies (and no
        exception) result -- this is intentional silent no-op behavior,
        not a bug, but worth locking down."""
        monkeypatch.setattr(anomdet, "HAS_SKLEARN", False)
        seq = [1, 0] * 14 + [9, 9]
        anomalies = detect_sequence_anomalies(seq, method="isolation_forest")
        assert anomalies == []

    def test_unknown_method_returns_empty(self):
        seq = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        anomalies = detect_sequence_anomalies(seq, method="not_a_real_method")
        assert anomalies == []


class TestDetectDistributionAnomalies:
    def test_empty_period_dict_returns_empty(self):
        assert detect_distribution_anomalies({}, 15, is_primitive=False) == []

    def test_bound_violation_detected(self):
        period_dict = {5: 1, 20: 1}  # 20 > theoretical_max_period=15
        anomalies = detect_distribution_anomalies(period_dict, 15, is_primitive=False)
        bound_anomalies = [a for a in anomalies if a.anomaly_type == "bound_violation"]
        assert len(bound_anomalies) == 1
        a = bound_anomalies[0]
        assert a.location == 20
        assert a.severity == 1.0
        assert a.metadata["violation_amount"] == 5

    def test_no_bound_violation_when_within_range(self):
        period_dict = {5: 1, 15: 1}
        anomalies = detect_distribution_anomalies(period_dict, 15, is_primitive=False)
        assert all(a.anomaly_type != "bound_violation" for a in anomalies)

    def test_primitive_expectation_satisfied_no_violation(self):
        # 95% of sequences hit the expected max period -> within the 10%
        # tolerance, no primitive_expectation_violation anomaly.
        period_dict = {15: 95, 1: 5}
        anomalies = detect_distribution_anomalies(period_dict, 15, is_primitive=True)
        assert all(
            a.anomaly_type != "primitive_expectation_violation" for a in anomalies
        )

    def test_primitive_expectation_violation_detected(self):
        # Only half the sequences hit the expected max period.
        period_dict = {15: 5, 1: 5}
        anomalies = detect_distribution_anomalies(period_dict, 15, is_primitive=True)
        violations = [
            a for a in anomalies if a.anomaly_type == "primitive_expectation_violation"
        ]
        assert len(violations) == 1
        a = violations[0]
        assert a.metadata["sequences_with_max"] == 5
        assert a.metadata["total_sequences"] == 10
        assert a.metadata["percentage"] == pytest.approx(50.0)
        assert a.severity == pytest.approx(0.5)

    def test_primitive_expectation_missing_period_key(self):
        """If period_dict doesn't even contain theoretical_max_period as
        a key, .get(expected_period, 0) should safely default to 0
        rather than KeyError, and flag maximal severity violation."""
        period_dict = {3: 10}
        anomalies = detect_distribution_anomalies(period_dict, 15, is_primitive=True)
        violations = [
            a for a in anomalies if a.anomaly_type == "primitive_expectation_violation"
        ]
        assert len(violations) == 1
        assert violations[0].metadata["sequences_with_max"] == 0
        assert violations[0].severity == pytest.approx(1.0)

    def test_distribution_outlier_detected(self):
        # One period massively more frequent than the rest (z-score ~2.65,
        # clearly above the 2.0 threshold).
        period_dict = {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 500}
        anomalies = detect_distribution_anomalies(period_dict, 1000, is_primitive=False)
        outliers = [a for a in anomalies if a.anomaly_type == "distribution_outlier"]
        assert len(outliers) >= 1
        assert any(a.location == 8 for a in outliers)

    def test_single_period_no_distribution_outlier_check(self):
        """len(periods) <= 1 skips the distribution-outlier branch
        entirely (line ~226 guard)."""
        period_dict = {5: 3}
        anomalies = detect_distribution_anomalies(period_dict, 15, is_primitive=False)
        assert all(a.anomaly_type != "distribution_outlier" for a in anomalies)

    def test_distribution_outlier_fallback_matches_numpy(self, monkeypatch):
        period_dict = {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 500}
        anomalies_np = detect_distribution_anomalies(period_dict, 1000, is_primitive=False)

        monkeypatch.setattr(anomdet, "HAS_NUMPY", False)
        anomalies_fb = detect_distribution_anomalies(period_dict, 1000, is_primitive=False)

        outliers_np = sorted(
            (a.location, round(a.severity, 6))
            for a in anomalies_np
            if a.anomaly_type == "distribution_outlier"
        )
        outliers_fb = sorted(
            (a.location, round(a.severity, 6))
            for a in anomalies_fb
            if a.anomaly_type == "distribution_outlier"
        )
        assert outliers_fb == outliers_np


class TestDetectAllAnomalies:
    def test_empty_call_returns_empty_dict(self):
        assert detect_all_anomalies() == {}

    def test_sequence_only(self):
        result = detect_all_anomalies(sequence=[1, 1, 1, 1, 1, 1, 1, 1, 1, 100])
        assert list(result.keys()) == ["sequence_anomalies"]
        assert len(result["sequence_anomalies"]) == 1

    def test_empty_sequence_is_falsy_and_skipped(self):
        """`if sequence:` treats an empty list as falsy, so
        sequence_anomalies key is entirely absent (not an empty list)."""
        result = detect_all_anomalies(sequence=[])
        assert "sequence_anomalies" not in result

    def test_period_dict_requires_theoretical_max(self):
        """period_dict alone (without theoretical_max_period) should NOT
        produce distribution_anomalies, per the `and theoretical_max_period
        is not None` guard."""
        result = detect_all_anomalies(period_dict={1: 1, 2: 2})
        assert "distribution_anomalies" not in result

    def test_both_sequence_and_period_dict(self):
        result = detect_all_anomalies(
            sequence=[1, 1, 1, 1, 1, 1, 1, 1, 1, 100],
            period_dict={1: 1, 2: 2},
            theoretical_max_period=15,
            is_primitive=False,
        )
        assert set(result.keys()) == {"sequence_anomalies", "distribution_anomalies"}


class TestImportFallbacks:
    """Regression coverage for the module-level `except ImportError:
    HAS_NUMPY/HAS_SKLEARN = False` branches themselves (lines ~19-20,
    25-26), as opposed to just testing behavior with the flag
    pre-set to False (covered above via monkeypatch.setattr)."""

    def test_numpy_import_error_sets_has_numpy_false(self):
        try:
            fresh = _reimport_with_blocked_import("lfsr.ml.anomaly_detection", "numpy")
            assert fresh.HAS_NUMPY is False
        finally:
            # Restore the normal module for the rest of the test session.
            del sys.modules["lfsr.ml.anomaly_detection"]
            import lfsr.ml.anomaly_detection  # noqa: F401

    def test_sklearn_import_error_sets_has_sklearn_false(self):
        try:
            fresh = _reimport_with_blocked_import(
                "lfsr.ml.anomaly_detection", "sklearn.ensemble"
            )
            assert fresh.HAS_SKLEARN is False
        finally:
            del sys.modules["lfsr.ml.anomaly_detection"]
            import lfsr.ml.anomaly_detection  # noqa: F401
