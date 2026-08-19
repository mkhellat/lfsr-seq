#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Coverage tests for lfsr.ml.pattern_detection: repeating-subsequence
detection, statistical-anomaly windows, periodicity indicators
(autocorrelation), the Pattern.description property, and the
detect_all_patterns dispatcher. Complements the existing light coverage
in test_ml.py."""

import builtins
import sys

import pytest

import lfsr.ml.pattern_detection as patdet
from lfsr.ml.pattern_detection import (
    Pattern,
    detect_all_patterns,
    detect_periodicity_indicators,
    detect_repeating_subsequences,
    detect_statistical_anomalies,
)


def _reimport_with_blocked_import(module_name, blocked_name):
    """Force a fresh import of `module_name` with `import blocked_name`
    made to raise ImportError, to exercise the module's own `except
    ImportError: HAS_NUMPY = False` fallback branch at definition time.
    Mirrors the identical helper in test_ml_anomaly_detection.py /
    test_ml_period_prediction.py."""
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


class TestPatternDescription:
    def test_description_property(self):
        p = Pattern(
            pattern_type="repeating_subsequence",
            pattern_data=[1, 0],
            start_position=2,
            end_position=3,
            confidence=0.8,
        )
        assert p.description == "repeating_subsequence at [2:3]: [1, 0]"


class TestDetectRepeatingSubsequences:
    def test_detects_repeating_pattern(self):
        seq = [1, 0] * 6
        patterns = detect_repeating_subsequences(seq, min_length=2, max_length=4)
        assert len(patterns) > 0
        assert all(p.pattern_type == "repeating_subsequence" for p in patterns)
        # Sorted descending by confidence.
        confidences = [p.confidence for p in patterns]
        assert confidences == sorted(confidences, reverse=True)

    def test_no_repeats_in_strictly_increasing_sequence(self):
        seq = list(range(20))
        patterns = detect_repeating_subsequences(seq, min_length=2, max_length=5)
        assert patterns == []

    def test_short_sequence_no_crash(self):
        # n // 2 + 1 bounds the loop; very short sequences should just
        # produce no patterns rather than erroring.
        patterns = detect_repeating_subsequences([1, 2], min_length=2, max_length=10)
        assert patterns == []

    def test_confidence_bounded_at_one(self):
        seq = [7] * 20  # maximal repetition
        patterns = detect_repeating_subsequences(seq, min_length=2, max_length=3)
        assert all(p.confidence <= 1.0 for p in patterns)


class TestDetectStatisticalAnomalies:
    def test_sequence_shorter_than_window_returns_empty(self):
        patterns = detect_statistical_anomalies([1, 2, 3], window_size=100)
        assert patterns == []

    def test_zero_variance_returns_empty(self):
        seq = [5] * 200
        patterns = detect_statistical_anomalies(seq, window_size=50)
        assert patterns == []

    def test_detects_anomalous_window(self):
        # Long run of 0/1 noise-like values, then a block of a very
        # different constant value -- that window's mean should deviate
        # enough to cross the z-score threshold.
        seq = [0, 1] * 100 + [9] * 60 + [0, 1] * 100
        patterns = detect_statistical_anomalies(seq, window_size=50, threshold=2.0)
        assert len(patterns) > 0
        for p in patterns:
            assert p.pattern_type == "statistical_anomaly"
            assert "z_score" in p.pattern_data
            assert "window_mean" in p.pattern_data
            assert "overall_mean" in p.pattern_data
            assert 0.0 < p.confidence <= 1.0

    def test_fallback_matches_numpy_path(self, monkeypatch):
        seq = [0, 1] * 100 + [9] * 60 + [0, 1] * 100
        patterns_np = detect_statistical_anomalies(seq, window_size=50, threshold=2.0)

        monkeypatch.setattr(patdet, "HAS_NUMPY", False)
        patterns_fb = detect_statistical_anomalies(seq, window_size=50, threshold=2.0)

        assert len(patterns_fb) == len(patterns_np)
        starts_np = sorted(p.start_position for p in patterns_np)
        starts_fb = sorted(p.start_position for p in patterns_fb)
        assert starts_fb == starts_np


class TestDetectPeriodicityIndicators:
    def test_too_short_sequence_returns_empty(self):
        assert detect_periodicity_indicators([1], max_period=10) == []
        assert detect_periodicity_indicators([], max_period=10) == []

    def test_detects_period_two(self):
        seq = [1, 0] * 30
        patterns = detect_periodicity_indicators(seq, max_period=10)
        assert len(patterns) > 0
        best = patterns[0]
        assert best.pattern_type == "periodicity_indicator"
        assert best.pattern_data["suggested_period"] == 2
        assert best.pattern_data["autocorrelation"] == pytest.approx(1.0)
        assert best.confidence == pytest.approx(1.0)
        # Sorted descending by confidence.
        confidences = [p.confidence for p in patterns]
        assert confidences == sorted(confidences, reverse=True)

    def test_random_like_sequence_below_threshold(self):
        # An alternating-but-aperiodic-ish sequence unlikely to have
        # strong autocorrelation at any lag under a low max_period.
        seq = [0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0]
        patterns = detect_periodicity_indicators(seq, max_period=3)
        # Every reported pattern (if any) must exceed the 0.7 threshold;
        # this mainly exercises the "may legitimately be empty" path.
        assert all(p.confidence > 0.7 for p in patterns)

    def test_max_period_capped_by_sequence_length(self):
        seq = [1, 0, 1, 0]
        # max_period larger than len(seq) should not error; loop bounded
        # by min(max_period + 1, n).
        patterns = detect_periodicity_indicators(seq, max_period=1000)
        assert isinstance(patterns, list)


class TestDetectAllPatterns:
    def test_all_keys_present_by_default(self):
        seq = [0, 1, 0, 1, 1, 0, 1, 1, 1, 0] * 5
        result = detect_all_patterns(seq)
        assert set(result.keys()) == {
            "repeating_subsequences",
            "statistical_anomalies",
            "periodicity_indicators",
        }

    def test_only_repeating_selected(self):
        seq = [0, 1, 0, 1, 1, 0, 1, 1, 1, 0] * 5
        result = detect_all_patterns(
            seq, include_repeating=True, include_anomalies=False, include_periodicity=False
        )
        assert set(result.keys()) == {"repeating_subsequences"}

    def test_only_anomalies_selected(self):
        seq = [0, 1, 0, 1, 1, 0, 1, 1, 1, 0] * 5
        result = detect_all_patterns(
            seq, include_repeating=False, include_anomalies=True, include_periodicity=False
        )
        assert set(result.keys()) == {"statistical_anomalies"}

    def test_none_selected_returns_empty_dict(self):
        seq = [0, 1, 0, 1, 1, 0, 1, 1, 1, 0] * 5
        result = detect_all_patterns(
            seq, include_repeating=False, include_anomalies=False, include_periodicity=False
        )
        assert result == {}


class TestImportFallback:
    """Regression coverage for the module-level `except ImportError:
    HAS_NUMPY = False` branch itself (lines ~19-20), as opposed to just
    testing behavior with the flag pre-set to False. Mirrors the
    equivalent test class in test_ml_anomaly_detection.py."""

    def test_numpy_import_error_sets_has_numpy_false(self):
        try:
            fresh = _reimport_with_blocked_import(
                "lfsr.ml.pattern_detection", "numpy"
            )
            assert fresh.HAS_NUMPY is False
        finally:
            del sys.modules["lfsr.ml.pattern_detection"]
            import lfsr.ml.pattern_detection  # noqa: F401
