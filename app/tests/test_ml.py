#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Regression tests for the lfsr.ml package (feature extraction, period
prediction training/evaluation, pattern detection, anomaly detection)."""

import pytest

from lfsr.ml.anomaly_detection import detect_all_anomalies
from lfsr.ml.base import extract_polynomial_features, extract_sequence_features
from lfsr.ml.pattern_detection import detect_all_patterns
from lfsr.ml.period_prediction import PeriodPredictionModel
from lfsr.ml.training import evaluate_model_performance, train_period_prediction_model


class TestExtractPolynomialFeatures:
    def test_returns_expected_length(self):
        features = extract_polynomial_features([1, 0, 1, 1], 2, 4)
        assert len(features) == 11

    def test_all_values_are_floats(self):
        features = extract_polynomial_features([1, 0, 1, 1], 2, 4)
        assert all(isinstance(v, float) for v in features)

    def test_empty_coefficients(self):
        features = extract_polynomial_features([], 2, 0)
        assert len(features) == 11

    def test_primitive_polynomial_flagged(self):
        # coeffs [1,0,0,1] over GF(2) -> characteristic polynomial
        # x^4+x^3+1 (verified via build_state_update_matrix(...)
        # .characteristic_polynomial()), a well-known primitive
        # polynomial over GF(2)
        features = extract_polynomial_features([1, 0, 0, 1], 2, 4)
        is_irreducible, is_primitive = features[-2], features[-1]
        assert is_irreducible == 1.0
        assert is_primitive == 1.0

    def test_reducible_polynomial_not_flagged_primitive(self):
        # coeffs [1,0,0,0] over GF(2) -> x^4+1 = (x+1)^4, reducible,
        # hence not primitive
        features = extract_polynomial_features([1, 0, 0, 0], 2, 4)
        is_irreducible, is_primitive = features[-2], features[-1]
        assert is_irreducible == 0.0
        assert is_primitive == 0.0

    def test_gf3_characteristic_polynomial_matches_matrix(self):
        """extract_polynomial_features' internal char-poly construction
        must match build_state_update_matrix's actual
        characteristic_polynomial() for field orders > 2, where an
        earlier version of this function's polynomial construction
        (`ring([1] + coefficients[::-1])`, no negation, wrong order)
        was silently wrong -- invisible for GF(2) with palindromic
        coefficient vectors (negation mod 2 is a no-op), but wrong for
        every GF(3)/GF(5)/... case."""
        from lfsr.core import build_state_update_matrix

        coeffs = [1, 2, 1]
        gf_order = 3
        C, _ = build_state_update_matrix(coeffs, gf_order)
        actual_charpoly = C.characteristic_polynomial()

        features = extract_polynomial_features(coeffs, gf_order, len(coeffs))
        is_irreducible, is_primitive = features[-2], features[-1]

        assert bool(is_irreducible) == actual_charpoly.is_irreducible()
        if actual_charpoly.is_irreducible():
            from lfsr.polynomial import is_primitive_polynomial

            assert bool(is_primitive) == is_primitive_polynomial(actual_charpoly, gf_order)

    def test_gf5_characteristic_polynomial_matches_matrix(self):
        """Same cross-check as test_gf3_..., for GF(5)."""
        from lfsr.core import build_state_update_matrix

        coeffs = [1, 3, 2, 1]
        gf_order = 5
        C, _ = build_state_update_matrix(coeffs, gf_order)
        actual_charpoly = C.characteristic_polynomial()

        features = extract_polynomial_features(coeffs, gf_order, len(coeffs))
        is_irreducible, is_primitive = features[-2], features[-1]

        assert bool(is_irreducible) == actual_charpoly.is_irreducible()
        if actual_charpoly.is_irreducible():
            from lfsr.polynomial import is_primitive_polynomial

            assert bool(is_primitive) == is_primitive_polynomial(actual_charpoly, gf_order)


class TestExtractSequenceFeatures:
    def test_returns_nonempty_features(self):
        features = extract_sequence_features([0, 1, 0, 1, 1, 0, 1, 1, 1, 0])
        assert len(features) > 0

    def test_empty_sequence(self):
        features = extract_sequence_features([])
        assert features == [0.0] * 10


class TestPeriodPredictionModel:
    def test_train_and_predict_round_trip(self):
        model = PeriodPredictionModel(model_type="random_forest")
        X = [
            extract_polynomial_features([1, 0, 0, 1], 2, 4),
            extract_polynomial_features([1, 1, 0, 1], 2, 4),
            extract_polynomial_features([1, 0, 1, 1], 2, 4),
            extract_polynomial_features([1, 1, 1, 1], 2, 4),
        ]
        y = [15.0, 6.0, 6.0, 1.0]
        metrics = model.train(X, y)
        assert model.is_trained
        assert "mse" in metrics and "r2_score" in metrics

        predictions = model.predict(X)
        assert len(predictions) == len(X)

    def test_predict_before_train_raises(self):
        model = PeriodPredictionModel(model_type="random_forest")
        with pytest.raises(ValueError):
            model.predict([[1.0] * 11])

    def test_save_and_load_round_trip(self, tmp_path):
        model = PeriodPredictionModel(model_type="random_forest")
        X = [
            extract_polynomial_features([1, 0, 0, 1], 2, 4),
            extract_polynomial_features([1, 1, 0, 1], 2, 4),
            extract_polynomial_features([1, 0, 1, 1], 2, 4),
        ]
        y = [15.0, 6.0, 6.0]
        model.train(X, y)

        save_path = str(tmp_path / "model")
        model.save_model(save_path)

        loaded = PeriodPredictionModel(model_type="random_forest")
        loaded.load_model(save_path)
        assert loaded.is_trained
        assert loaded.predict(X) == model.predict(X)

    def test_predict_period_convenience_method(self):
        model = PeriodPredictionModel(model_type="random_forest")
        X = [
            extract_polynomial_features([1, 0, 0, 1], 2, 4),
            extract_polynomial_features([1, 1, 0, 1], 2, 4),
            extract_polynomial_features([1, 0, 1, 1], 2, 4),
        ]
        y = [15.0, 6.0, 6.0]
        model.train(X, y)

        prediction = model.predict_period([1, 0, 0, 1], 2, degree=4)
        assert isinstance(prediction, float)


class TestGenerateTrainingData:
    def test_analyze_lfsr_exception_is_skipped(self, monkeypatch):
        """Covers the `except Exception: continue` branch in
        generate_training_data (lines ~108-110): if analyze_lfsr raises
        for a given candidate, that sample is silently skipped rather
        than propagating, and the function still returns whatever
        samples succeeded. Monkeypatches lfsr.ml.training.analyze_lfsr
        (imported by name into training's namespace) to always raise,
        isolating this behavior from analyze_lfsr's real success/failure
        conditions (covered elsewhere)."""
        import lfsr.ml.training as training

        def always_raises(coefficients, field_order):
            raise RuntimeError("simulated analyze_lfsr failure")

        monkeypatch.setattr(training, "analyze_lfsr", always_raises)

        X, y = training.generate_training_data(
            num_samples=5, max_degree=4, field_order=2
        )
        assert X == []
        assert y == []


class TestTrainingPipeline:
    @pytest.mark.slow
    def test_train_period_prediction_model(self):
        model = train_period_prediction_model(
            model_type="random_forest",
            num_samples=10,
            max_degree=6,
            field_order=2,
            save_path=None
        )
        assert model.is_trained

    @pytest.mark.slow
    def test_train_gradient_boosting_model(self):
        model = train_period_prediction_model(
            model_type="gradient_boosting",
            num_samples=10,
            max_degree=6,
            field_order=2,
            save_path=None
        )
        assert model.is_trained

    @pytest.mark.slow
    def test_evaluate_model_performance(self):
        model = train_period_prediction_model(
            model_type="random_forest",
            num_samples=10,
            max_degree=6,
            field_order=2,
            save_path=None
        )
        metrics = evaluate_model_performance(
            model, test_samples=5, max_degree=6, field_order=2
        )
        assert "mse" in metrics and "rmse" in metrics and "r2_score" in metrics


class TestPatternDetection:
    def test_detect_all_patterns_returns_expected_keys(self):
        sequence = [0, 1, 0, 1, 1, 0, 1, 1, 1, 0] * 5
        patterns = detect_all_patterns(sequence)
        assert set(patterns.keys()) == {
            "repeating_subsequences", "statistical_anomalies", "periodicity_indicators"
        }

    def test_detect_all_patterns_partial_selection(self):
        sequence = [0, 1, 0, 1, 1, 0, 1, 1, 1, 0] * 5
        patterns = detect_all_patterns(
            sequence, include_repeating=False, include_anomalies=False, include_periodicity=True
        )
        assert set(patterns.keys()) == {"periodicity_indicators"}


class TestAnomalyDetection:
    def test_detect_all_anomalies_with_sequence_only(self):
        sequence = [0, 1, 0, 1, 1, 0, 1, 1, 1, 0] * 5
        anomalies = detect_all_anomalies(sequence=sequence)
        assert "sequence_anomalies" in anomalies

    def test_detect_all_anomalies_with_period_dict(self):
        period_dict = {1: 1, 2: 2, 3: 3}
        anomalies = detect_all_anomalies(
            period_dict=period_dict, theoretical_max_period=15, is_primitive=False
        )
        assert "distribution_anomalies" in anomalies

    def test_detect_all_anomalies_empty_input(self):
        anomalies = detect_all_anomalies()
        assert anomalies == {}
