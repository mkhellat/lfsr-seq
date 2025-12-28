"""
Machine Learning Integration for LFSR Analysis

This module provides ML-based analysis capabilities including period prediction,
pattern detection, and anomaly detection.
"""

from lfsr.ml.base import MLModel, FeatureExtractor
from lfsr.ml.period_prediction import PeriodPredictor, train_period_predictor
from lfsr.ml.pattern_detection import PatternDetector, detect_patterns
from lfsr.ml.anomaly_detection import AnomalyDetector, detect_anomalies

__all__ = [
    "MLModel",
    "FeatureExtractor",
    "PeriodPredictor",
    "train_period_predictor",
    "PatternDetector",
    "detect_patterns",
    "AnomalyDetector",
    "detect_anomalies",
]
