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
