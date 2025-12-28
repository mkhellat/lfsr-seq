#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Anomaly detection in LFSR sequences and analysis results.

This module provides ML-based anomaly detection to identify unusual
patterns, outliers, and potential errors in LFSR analysis.
"""

from typing import List, Dict, Any, Optional
import math
from statistics import mean, stdev

from lfsr.ml.base import FeatureExtractor

# Try to import scikit-learn, but make it optional
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


class AnomalyDetector:
    """
    Detect anomalies in LFSR sequences and analysis results.
    
    This class provides methods to identify anomalies, outliers, and
    unusual patterns that may indicate errors or interesting properties.
    
    **Key Terminology**:
    
    - **Anomaly Detection**: The process of identifying data points or
      patterns that deviate significantly from expected behavior. In LFSR
      analysis, anomalies might indicate errors, security weaknesses, or
      interesting mathematical properties.
    
    - **Outlier**: A data point that is significantly different from
      other data points. For example, a period that is much larger or
      smaller than expected.
    
    - **Statistical Anomaly**: A value that falls outside the expected
      statistical distribution, typically defined as values beyond a
      certain number of standard deviations from the mean.
    
    - **Isolation Forest**: A machine learning algorithm for anomaly
      detection that isolates anomalies by randomly selecting features
      and splitting values. Anomalies are easier to isolate than normal
      points.
    """
    
    def __init__(self, method: str = "statistical"):
        """
        Initialize anomaly detector.
        
        Args:
            method: Detection method ("statistical" or "isolation_forest")
        """
        self.method = method
        self.model = None
        self.scaler = None
        
        if method == "isolation_forest":
            if not HAS_SKLEARN:
                raise ImportError(
                    "scikit-learn is required for isolation forest. "
                    "Install with: pip install scikit-learn"
                )
            self.model = IsolationForest(contamination=0.1, random_state=42)
            self.scaler = StandardScaler()
    
    def detect_sequence_anomalies(
        self,
        sequence: List[int],
        threshold: float = 3.0
    ) -> Dict[str, Any]:
        """
        Detect anomalies in sequence values.
        
        This method identifies values in the sequence that are unusual
        compared to the sequence's statistical properties.
        
        Args:
            sequence: Sequence to analyze
            threshold: Number of standard deviations for statistical method
        
        Returns:
            Dictionary with anomaly information
        """
        if not sequence:
            return {'anomalies': [], 'anomaly_count': 0}
        
        if self.method == "statistical":
            return self._detect_statistical_anomalies(sequence, threshold)
        elif self.method == "isolation_forest":
            return self._detect_ml_anomalies(sequence)
        else:
            raise ValueError(f"Unknown method: {self.method}")
    
    def _detect_statistical_anomalies(
        self,
        sequence: List[int],
        threshold: float
    ) -> Dict[str, Any]:
        """Detect anomalies using statistical methods."""
        if len(sequence) < 2:
            return {'anomalies': [], 'anomaly_count': 0}
        
        seq_mean = mean(sequence)
        seq_stdev = stdev(sequence) if len(sequence) > 1 else 0.0
        
        if seq_stdev == 0:
            return {'anomalies': [], 'anomaly_count': 0}
        
        anomalies = []
        for i, value in enumerate(sequence):
            z_score = abs((value - seq_mean) / seq_stdev) if seq_stdev > 0 else 0.0
            if z_score > threshold:
                anomalies.append({
                    'index': i,
                    'value': value,
                    'z_score': z_score
                })
        
        return {
            'anomalies': anomalies,
            'anomaly_count': len(anomalies),
            'mean': seq_mean,
            'stdev': seq_stdev,
            'threshold': threshold
        }
    
    def _detect_ml_anomalies(
        self,
        sequence: List[int]
    ) -> Dict[str, Any]:
        """Detect anomalies using isolation forest."""
        if not HAS_SKLEARN:
            raise ImportError("scikit-learn is required for ML anomaly detection")
        
        # Extract features from sequence windows
        window_size = min(10, len(sequence))
        features = []
        indices = []
        
        for i in range(len(sequence) - window_size + 1):
            window = sequence[i:i+window_size]
            window_features = FeatureExtractor.extract_sequence_features(window)
            features.append(window_features)
            indices.append(i)
        
        if not features:
            return {'anomalies': [], 'anomaly_count': 0}
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Detect anomalies
        predictions = self.model.fit_predict(features_scaled)
        
        anomalies = []
        for i, pred in enumerate(predictions):
            if pred == -1:  # Anomaly
                anomalies.append({
                    'index': indices[i],
                    'window': sequence[indices[i]:indices[i]+window_size],
                    'score': float(self.model.score_samples([features_scaled[i]])[0])
                })
        
        return {
            'anomalies': anomalies,
            'anomaly_count': len(anomalies),
            'method': 'isolation_forest'
        }
    
    def detect_period_anomalies(
        self,
        periods: List[int],
        expected_period: Optional[int] = None,
        threshold: float = 3.0
    ) -> Dict[str, Any]:
        """
        Detect anomalies in period distribution.
        
        This method identifies periods that are unusual compared to
        the expected or observed distribution.
        
        Args:
            periods: List of periods
            expected_period: Optional expected period value
            threshold: Number of standard deviations for statistical method
        
        Returns:
            Dictionary with anomaly information
        """
        if not periods:
            return {'anomalies': [], 'anomaly_count': 0}
        
        period_mean = mean(periods)
        period_stdev = stdev(periods) if len(periods) > 1 else 0.0
        
        anomalies = []
        for i, period in enumerate(periods):
            is_anomaly = False
            
            # Check against expected period
            if expected_period is not None:
                if abs(period - expected_period) > threshold * period_stdev:
                    is_anomaly = True
            
            # Check against distribution
            if period_stdev > 0:
                z_score = abs((period - period_mean) / period_stdev)
                if z_score > threshold:
                    is_anomaly = True
            
            if is_anomaly:
                anomalies.append({
                    'index': i,
                    'period': period,
                    'deviation_from_mean': period - period_mean,
                    'z_score': abs((period - period_mean) / period_stdev) if period_stdev > 0 else 0.0
                })
        
        return {
            'anomalies': anomalies,
            'anomaly_count': len(anomalies),
            'mean_period': period_mean,
            'stdev_period': period_stdev,
            'expected_period': expected_period
        }


def detect_anomalies(
    sequence: Optional[List[int]] = None,
    periods: Optional[List[int]] = None,
    method: str = "statistical",
    threshold: float = 3.0
) -> Dict[str, Any]:
    """
    Comprehensive anomaly detection.
    
    This function performs anomaly detection on sequences and/or periods,
    returning comprehensive results.
    
    Args:
        sequence: Optional sequence to analyze
        periods: Optional list of periods to analyze
        method: Detection method ("statistical" or "isolation_forest")
        threshold: Threshold for statistical method
    
    Returns:
        Dictionary with all anomaly detection results
    """
    detector = AnomalyDetector(method=method)
    results = {}
    
    if sequence is not None:
        results['sequence_anomalies'] = detector.detect_sequence_anomalies(
            sequence, threshold
        )
    
    if periods is not None:
        results['period_anomalies'] = detector.detect_period_anomalies(
            periods, threshold=threshold
        )
    
    return results
