#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Additional coverage tests for lfsr.ml.base: BaseMLModel.evaluate (both
the numpy+sklearn path and the pure-Python fallback path), and the
extract_sequence_features fallback branches. Complements test_ml.py's
existing feature-extraction / char-poly-correctness tests."""

import builtins
import importlib
import sys

import pytest

import lfsr.ml.base as mlbase
from lfsr.ml.base import (
    BaseMLModel,
    MLModelConfig,
    extract_polynomial_features,
    extract_sequence_features,
)


def _reimport_with_blocked_import(module_name, blocked_name):
    """See tests/test_ml_anomaly_detection.py for the rationale: forces
    a fresh import of `module_name` with `import blocked_name` made to
    raise ImportError, to exercise the module's own `except ImportError:
    HAS_X = False` fallback branch at definition time."""
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == blocked_name:
            raise ImportError(f"simulated: {blocked_name} unavailable")
        return real_import(name, *args, **kwargs)

    if module_name in sys.modules:
        del sys.modules[module_name]

    builtins.__import__ = fake_import
    try:
        return importlib.import_module(module_name)
    finally:
        builtins.__import__ = real_import


class DummyModel(BaseMLModel):
    """Minimal concrete BaseMLModel: predict() returns fixed offsets from
    training targets stored on train(), just enough to exercise
    evaluate()'s numeric paths without needing a real ML backend."""

    def train(self, X, y):
        self.is_trained = True
        self._y = list(y)
        return {}

    def predict(self, X):
        # Return the stored y with a deterministic error rather than a
        # perfect echo, so mse/r2 aren't trivially 0/1.
        return [v + 1.0 for v in self._y[: len(X)]]

    def save_model(self, filepath):
        pass

    def load_model(self, filepath):
        pass


class TestMLModelConfig:
    def test_default_version(self):
        config = MLModelConfig(model_type="x", model_params={}, feature_names=["a"])
        assert config.model_version == "1.0"

    def test_explicit_version(self):
        config = MLModelConfig(
            model_type="x", model_params={}, feature_names=["a"], model_version="2.0"
        )
        assert config.model_version == "2.0"


class TestBaseMLModelEvaluate:
    def test_evaluate_before_train_raises(self):
        model = DummyModel()
        with pytest.raises(ValueError):
            model.evaluate([[1.0]], [1.0])

    def test_evaluate_numpy_sklearn_path(self):
        model = DummyModel()
        X = [[0.0], [1.0], [2.0], [3.0]]
        y = [10.0, 20.0, 30.0, 40.0]
        model.train(X, y)

        metrics = model.evaluate(X, y)
        assert set(metrics.keys()) == {"mse", "rmse", "r2_score"}
        # predictions are y+1 exactly, so mse == 1.0, rmse == 1.0
        assert metrics["mse"] == pytest.approx(1.0)
        assert metrics["rmse"] == pytest.approx(1.0)

    def test_evaluate_fallback_path_matches_numpy_path(self, monkeypatch):
        """With HAS_NUMPY/HAS_SKLEARN forced off, the pure-Python fallback
        formulas in evaluate() (lines ~159-174) must produce the same
        mse/rmse/r2 as the numpy+sklearn path for identical input."""
        X = [[0.0], [1.0], [2.0], [3.0]]
        y = [10.0, 20.0, 30.0, 40.0]

        model_np = DummyModel()
        model_np.train(X, y)
        metrics_np = model_np.evaluate(X, y)

        monkeypatch.setattr(mlbase, "HAS_NUMPY", False)
        monkeypatch.setattr(mlbase, "HAS_SKLEARN", False)

        model_fb = DummyModel()
        model_fb.train(X, y)
        metrics_fb = model_fb.evaluate(X, y)

        assert metrics_fb["mse"] == pytest.approx(metrics_np["mse"])
        assert metrics_fb["rmse"] == pytest.approx(metrics_np["rmse"])
        assert metrics_fb["r2_score"] == pytest.approx(metrics_np["r2_score"])

    def test_evaluate_fallback_zero_variance_r2(self, monkeypatch):
        """When all y values are identical, ss_tot == 0 in the fallback
        branch; the code guards this with `if ss_tot > 0 else 0.0`
        (line ~168) rather than dividing by zero."""
        monkeypatch.setattr(mlbase, "HAS_NUMPY", False)
        monkeypatch.setattr(mlbase, "HAS_SKLEARN", False)

        model = DummyModel()
        X = [[0.0], [1.0]]
        y = [5.0, 5.0]
        model.train(X, y)
        metrics = model.evaluate(X, y)
        assert metrics["r2_score"] == 0.0


class TestExtractPolynomialFeaturesNonTrivial:
    def test_non_palindromic_gf7_case(self):
        """A non-trivial, non-palindromic GF(7) case (field_order > 5,
        never exercised by the existing GF(2)/GF(3)/GF(5) tests in
        test_ml.py) to further confirm the char-poly reconstruction fix
        (ring([(-c) % field_order for c in coefficients] + [1])) holds
        generally and not just for the small field orders already
        checked elsewhere."""
        from lfsr.core import build_state_update_matrix
        from lfsr.polynomial import is_primitive_polynomial

        coeffs = [3, 0, 5, 1]  # deliberately non-palindromic
        gf_order = 7
        C, _ = build_state_update_matrix(coeffs, gf_order)
        actual_charpoly = C.characteristic_polynomial()

        features = extract_polynomial_features(coeffs, gf_order, len(coeffs))
        is_irreducible, is_primitive = features[-2], features[-1]

        assert bool(is_irreducible) == actual_charpoly.is_irreducible()
        if actual_charpoly.is_irreducible():
            assert bool(is_primitive) == is_primitive_polynomial(actual_charpoly, gf_order)


class TestExtractPolynomialFeaturesDegreeDefault:
    def test_degree_defaults_to_len_coefficients(self):
        features = extract_polynomial_features([1, 0, 1], 2)
        assert features[0] == 3.0

    def test_exception_path_leaves_flags_zero(self):
        """An invalid field_order (e.g. 4, not prime/prime-power-safe for
        GF()) should be swallowed by the broad except and leave
        is_irreducible/is_primitive at their 0.0 default (lines ~278-279)."""
        features = extract_polynomial_features([1, 1, 1], 1, 3)
        is_irreducible, is_primitive = features[-2], features[-1]
        assert is_irreducible == 0.0
        assert is_primitive == 0.0


class TestExtractSequenceFeaturesFallback:
    def test_fallback_matches_numpy_path(self, monkeypatch):
        seq = [1, 3, 2, 8, 5, 7, 2, 4, 9, 1]

        features_np = extract_sequence_features(seq)

        monkeypatch.setattr(mlbase, "HAS_NUMPY", False)
        features_fb = extract_sequence_features(seq)

        assert len(features_fb) == len(features_np)
        for a, b in zip(features_fb, features_np):
            assert a == pytest.approx(b)

    def test_fallback_single_element_sequence_std_zero(self, monkeypatch):
        """len(seq) == 1: std/autocorr fallback branches (lines ~324, 337)
        should produce 0.0 rather than raising."""
        monkeypatch.setattr(mlbase, "HAS_NUMPY", False)
        features = extract_sequence_features([5])
        # [len, unique, mean, std, min, max, autocorr, balance]
        assert features[0] == 1.0
        assert features[3] == 0.0  # std fallback for len==1

    def test_binary_sequence_balance_feature(self):
        # All-ones binary sequence: perfectly imbalanced -> balance == 1.0
        features = extract_sequence_features([1, 1, 1, 1])
        assert features[-1] == 1.0

    def test_balanced_binary_sequence(self):
        features = extract_sequence_features([0, 1, 0, 1])
        assert features[-1] == 0.0

    def test_non_binary_sequence_balance_feature_is_zero(self):
        """Non-binary values skip the balance branch entirely (line 345),
        appending 0.0 rather than computing anything."""
        features = extract_sequence_features([2, 4, 6, 8])
        assert features[-1] == 0.0

    def test_truncates_to_max_length(self):
        seq = list(range(20))
        features = extract_sequence_features(seq, max_length=5)
        assert features[0] == 5.0


class TestImportFallbacks:
    """Regression coverage for the module-level `except ImportError:
    HAS_NUMPY/HAS_SKLEARN = False` branches themselves (lines ~18-19,
    24-25)."""

    def test_numpy_import_error_sets_has_numpy_false(self):
        try:
            fresh = _reimport_with_blocked_import("lfsr.ml.base", "numpy")
            assert fresh.HAS_NUMPY is False
        finally:
            del sys.modules["lfsr.ml.base"]
            import lfsr.ml.base  # noqa: F401

    def test_sklearn_import_error_sets_has_sklearn_false(self):
        try:
            fresh = _reimport_with_blocked_import("lfsr.ml.base", "sklearn.metrics")
            assert fresh.HAS_SKLEARN is False
        finally:
            del sys.modules["lfsr.ml.base"]
            import lfsr.ml.base  # noqa: F401
