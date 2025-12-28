"""
Machine Learning Integration for LFSR Analysis

This module provides ML-based analysis capabilities including period prediction,
pattern detection, and anomaly detection for LFSR sequences.
"""

from lfsr.ml.models import PeriodPredictor, PatternDetector, AnomalyDetector
from lfsr.ml.features import extract_polynomial_features, extract_sequence_features

__all__ = [
    "PeriodPredictor",
    "PatternDetector",
    "AnomalyDetector",
    "extract_polynomial_features",
    "extract_sequence_features",
]
