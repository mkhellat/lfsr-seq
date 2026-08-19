#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Smoke tests for lfsr.examples.ml_integration_example -- a standalone
demo/tutorial script (not part of the public API, not imported by any
library code, not wired into the CLI; see
src/lfsr/examples/__init__.py). It wraps already-tested library
functions (lfsr.ml.*, lfsr.core.analyze_lfsr -- see "Complete and
verified" in the project's CLAUDE.md), so these tests are deliberately
shallow: each example_*() function is invoked with stdout captured and
we assert only that it runs to completion without raising. All 5
example_*() functions plus main() were run interactively against this
checkout before writing any assertion; none raised (scikit-learn is
installed in this environment, so the HAS_SKLEARN-gated period
prediction / model training examples ran too). No bugs were found in
this module.
"""

import io
import contextlib

import pytest

from lfsr.examples import ml_integration_example as m


class TestExampleFunctions:
    def test_example_feature_extraction(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m.example_feature_extraction()
        out = buf.getvalue()
        assert "Feature Extraction" in out
        assert "Polynomial Features" in out
        assert "Sequence Features" in out

    def test_example_pattern_detection(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m.example_pattern_detection()
        out = buf.getvalue()
        assert "Pattern Detection" in out
        assert "Detected Patterns" in out

    def test_example_anomaly_detection(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m.example_anomaly_detection()
        out = buf.getvalue()
        assert "Anomaly Detection" in out
        assert "Detected Anomalies" in out

    @pytest.mark.skipif(not m.HAS_SKLEARN, reason="scikit-learn not available")
    def test_example_period_prediction(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m.example_period_prediction()
        out = buf.getvalue()
        assert "Period Prediction" in out
        assert "Training Metrics" in out
        assert "Prediction Example" in out

    @pytest.mark.skipif(not m.HAS_SKLEARN, reason="scikit-learn not available")
    def test_example_model_training(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m.example_model_training()
        out = buf.getvalue()
        assert "Model Training" in out
        assert "Model training complete" in out


class TestMain:
    def test_main_runs_end_to_end(self, capsys):
        # main() catches Exception, prints, and sys.exit(1) on failure;
        # a clean run returns None (no SystemExit).
        m.main()
        captured = capsys.readouterr()
        assert "Machine Learning Integration Examples" in captured.out
        assert "Examples Complete!" in captured.out
        assert "ERROR" not in captured.err

    def test_main_prints_traceback_and_exits_on_exception(self, monkeypatch, capsys):
        """Regression coverage for lines 202-206: main()'s except
        Exception handler prints an ERROR message, a traceback, and
        calls sys.exit(1)."""

        def raiser():
            raise RuntimeError("forced failure for coverage")

        monkeypatch.setattr(m, "example_feature_extraction", raiser)

        with pytest.raises(SystemExit) as exc_info:
            m.main()
        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "ERROR: forced failure for coverage" in captured.err
        assert "RuntimeError" in captured.err


class TestSklearnUnavailableBranches:
    """scikit-learn is actually installed in this environment, so
    HAS_SKLEARN is True at import time. Monkeypatch the module-level
    flag to False to hit the "scikit-learn not available"/"required"
    early-return and skip branches -- doesn't touch the import-guard
    except block itself (lines 25-27, genuinely unreachable without
    uninstalling scikit-learn from this environment)."""

    def test_period_prediction_early_returns_without_sklearn(self, monkeypatch):
        monkeypatch.setattr(m, "HAS_SKLEARN", False)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m.example_period_prediction()
        out = buf.getvalue()
        assert "scikit-learn required for period prediction" in out
        assert "Training Metrics" not in out

    def test_model_training_early_returns_without_sklearn(self, monkeypatch):
        monkeypatch.setattr(m, "HAS_SKLEARN", False)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m.example_model_training()
        out = buf.getvalue()
        assert "scikit-learn required for model training" in out
        assert "Model training complete" not in out

    def test_main_prints_sklearn_note_when_unavailable(self, monkeypatch, capsys):
        monkeypatch.setattr(m, "HAS_SKLEARN", False)
        m.main()
        captured = capsys.readouterr()
        assert "Note: Some examples require scikit-learn" in captured.out
        assert "pip install scikit-learn" in captured.out
        assert "Examples Complete!" in captured.out
