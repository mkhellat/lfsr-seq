#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Coverage tests for lfsr.ml.period_prediction: model_type dispatch
(random_forest / gradient_boosting / invalid), the no-sklearn error
paths, save/load round trips (including the pickle fallback branch),
and create_period_prediction_model. Complements the round-trip tests
already in test_ml.py."""

import json

import pytest

import lfsr.ml.period_prediction as periodpred
from lfsr.ml.base import extract_polynomial_features
from lfsr.ml.period_prediction import (
    PeriodPredictionModel,
    create_period_prediction_model,
)


def _sample_xy():
    X = [
        extract_polynomial_features([1, 0, 0, 1], 2, 4),
        extract_polynomial_features([1, 1, 0, 1], 2, 4),
        extract_polynomial_features([1, 0, 1, 1], 2, 4),
        extract_polynomial_features([1, 1, 1, 1], 2, 4),
    ]
    y = [15.0, 6.0, 6.0, 1.0]
    return X, y


class TestModelTypeDispatch:
    def test_gradient_boosting_model_type(self):
        model = PeriodPredictionModel(model_type="gradient_boosting")
        X, y = _sample_xy()
        metrics = model.train(X, y)
        assert model.is_trained
        assert "mse" in metrics
        predictions = model.predict(X)
        assert len(predictions) == len(X)

    def test_unknown_model_type_raises(self):
        with pytest.raises(ValueError, match="Unknown model type"):
            PeriodPredictionModel(model_type="not_a_real_model")

    def test_default_config_feature_names(self):
        model = PeriodPredictionModel(model_type="random_forest")
        assert model.config.feature_names == [
            'degree', 'field_order', 'num_coeffs', 'nonzero_count',
            'sparsity', 'is_trinomial', 'is_pentanomial',
            'coeff_sum', 'coeff_mean', 'is_irreducible', 'is_primitive'
        ]
        assert model.config.model_type == "random_forest"

    def test_custom_config_is_preserved(self):
        from lfsr.ml.base import MLModelConfig

        config = MLModelConfig(
            model_type="random_forest", model_params={"n_estimators": 5}, feature_names=["a"]
        )
        model = PeriodPredictionModel(model_type="random_forest", config=config)
        assert model.config is config


class TestNoSklearn:
    def test_model_is_none_without_sklearn(self, monkeypatch):
        monkeypatch.setattr(periodpred, "HAS_SKLEARN", False)
        model = PeriodPredictionModel(model_type="random_forest")
        assert model.model is None

    def test_train_without_sklearn_raises_importerror(self, monkeypatch):
        monkeypatch.setattr(periodpred, "HAS_SKLEARN", False)
        model = PeriodPredictionModel(model_type="random_forest")
        X, y = _sample_xy()
        with pytest.raises(ImportError, match="scikit-learn"):
            model.train(X, y)

    def test_train_with_uninitialized_model_raises_valueerror(self, monkeypatch):
        """If HAS_SKLEARN is True (so train() doesn't raise ImportError)
        but self.model is somehow None, train() should raise ValueError
        (line ~110)."""
        model = PeriodPredictionModel(model_type="random_forest")
        model.model = None
        X, y = _sample_xy()
        with pytest.raises(ValueError, match="Model not initialized"):
            model.train(X, y)

    def test_predict_with_uninitialized_model_raises_valueerror(self):
        model = PeriodPredictionModel(model_type="random_forest")
        model.is_trained = True  # bypass the "must be trained" check
        model.model = None
        with pytest.raises(ValueError, match="Model not initialized"):
            model.predict([[1.0] * 11])


class TestTrainFallbackWithoutNumpy:
    def test_train_metrics_fallback_matches_numpy(self, monkeypatch):
        X, y = _sample_xy()

        model_np = PeriodPredictionModel(model_type="random_forest")
        metrics_np = model_np.train(X, y)

        monkeypatch.setattr(periodpred, "HAS_NUMPY", False)
        model_fb = PeriodPredictionModel(model_type="random_forest")
        metrics_fb = model_fb.train(X, y)

        assert metrics_fb["mse"] == pytest.approx(metrics_np["mse"], rel=1e-6)
        assert metrics_fb["rmse"] == pytest.approx(metrics_np["rmse"], rel=1e-6)
        assert metrics_fb["r2_score"] == pytest.approx(metrics_np["r2_score"], rel=1e-6)
        assert metrics_fb["training_samples"] == len(X)

    def test_predict_fallback_without_numpy(self, monkeypatch):
        X, y = _sample_xy()
        model = PeriodPredictionModel(model_type="random_forest")
        model.train(X, y)

        monkeypatch.setattr(periodpred, "HAS_NUMPY", False)
        predictions = model.predict(X)
        assert len(predictions) == len(X)
        assert all(isinstance(p, float) for p in predictions)


class TestSaveLoad:
    def test_save_before_train_raises(self, tmp_path):
        model = PeriodPredictionModel(model_type="random_forest")
        with pytest.raises(ValueError, match="must be trained"):
            model.save_model(str(tmp_path / "model"))

    def test_save_creates_config_json_with_expected_fields(self, tmp_path):
        model = PeriodPredictionModel(model_type="random_forest")
        X, y = _sample_xy()
        model.train(X, y)

        save_path = str(tmp_path / "nested" / "dir" / "model")
        model.save_model(save_path)

        config_file = tmp_path / "nested" / "dir" / "model.config.json"
        assert config_file.exists()
        with open(config_file) as f:
            config_dict = json.load(f)
        assert config_dict["model_type"] == "random_forest"
        assert config_dict["is_trained"] is True
        assert config_dict["config"]["feature_names"] == model.config.feature_names

    def test_save_load_pickle_fallback_when_joblib_missing(self, tmp_path, monkeypatch):
        """save_model/load_model prefer joblib but fall back to pickle
        (ImportError branch) if joblib isn't importable. Simulate that by
        forcing `import joblib` to fail inside the module."""
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "joblib":
                raise ImportError("simulated: joblib not installed")
            return real_import(name, *args, **kwargs)

        model = PeriodPredictionModel(model_type="random_forest")
        X, y = _sample_xy()
        model.train(X, y)

        save_path = str(tmp_path / "model")
        monkeypatch.setattr(builtins, "__import__", fake_import)
        model.save_model(save_path)
        monkeypatch.undo()

        assert (tmp_path / "model.model").exists()

        loaded = PeriodPredictionModel(model_type="random_forest")
        monkeypatch.setattr(builtins, "__import__", fake_import)
        loaded.load_model(save_path)
        monkeypatch.undo()

        assert loaded.is_trained
        assert loaded.predict(X) == model.predict(X)


class TestPredictPeriodConvenience:
    def test_predict_period_returns_float(self):
        model = PeriodPredictionModel(model_type="random_forest")
        X, y = _sample_xy()
        model.train(X, y)
        result = model.predict_period([1, 0, 0, 1], 2, degree=4)
        assert isinstance(result, float)

    def test_predict_period_default_degree(self):
        model = PeriodPredictionModel(model_type="random_forest")
        X, y = _sample_xy()
        model.train(X, y)
        result = model.predict_period([1, 0, 0, 1], 2)
        assert isinstance(result, float)


class TestCreatePeriodPredictionModel:
    def test_default_type(self):
        model = create_period_prediction_model()
        assert model.model_type == "random_forest"
        assert isinstance(model, PeriodPredictionModel)

    def test_explicit_type(self):
        model = create_period_prediction_model(model_type="gradient_boosting")
        assert model.model_type == "gradient_boosting"
