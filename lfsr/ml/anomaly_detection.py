#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Anomaly detection for LFSR sequences and distributions.

This module provides anomaly detection capabilities to identify unusual
patterns, outliers, and deviations from expected behavior.
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import Counter

from lfsr.ml.base import extract_sequence_features, extract_polynomial_features

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from sklearn.ensemble import IsolationForest
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


@dataclass
class Anomaly:
    """
    Detected anomaly.
    
    Attributes:
        anomaly_type: Type of anomaly
        location: Where anomaly occurs (index, period value, etc.)
        severity: Severity score (0.0 to 1.0)
        description: Human-readable description
        metadata: Additional anomaly-specific data
    """
    anomaly_type: str
    location: Any
    severity: float
    description: str
    metadata: Dict[str, Any]


def detect_sequence_anomalies(
    sequence: List[int],
    method: str = "statistical"
) -> List[Anomaly]:
    """
    Detect anomalies in a sequence.
    
    This function identifies unusual values or patterns in sequences
    that deviate from expected behavior.
    
    **Key Terminology**:
    
    - **Anomaly Detection**: The process of identifying data points or
      patterns that deviate significantly from expected behavior. In LFSR
      sequences, anomalies might indicate errors, special structure, or
      unexpected properties.
    
    - **Outlier**: A data point that is significantly different from
      other data points. Outliers can be anomalies or legitimate but
      rare events.
    
    - **Isolation Forest**: A machine learning algorithm for anomaly
      detection that isolates anomalies by randomly selecting features
      and splitting values. Anomalies are easier to isolate than normal
      points.
    
    Args:
        sequence: Sequence to analyze
        method: Detection method ("statistical" or "isolation_forest")
    
    Returns:
        List of detected anomalies
    """
    anomalies = []
    
    if method == "statistical":
        # Statistical outlier detection
        if HAS_NUMPY:
            seq_array = np.array(sequence)
            mean = np.mean(seq_array)
            std = np.std(seq_array) if len(seq_array) > 1 else 1.0
        else:
            mean = sum(sequence) / len(sequence)
            variance = sum((x - mean) ** 2 for x in sequence) / len(sequence)
            std = variance ** 0.5 if variance > 0 else 1.0
        
        if std == 0:
            return anomalies
        
        threshold = 3.0  # 3 standard deviations
        for i, value in enumerate(sequence):
            z_score = abs(value - mean) / std if std > 0 else 0.0
            if z_score > threshold:
                severity = min(z_score / (threshold * 2), 1.0)
                anomaly = Anomaly(
                    anomaly_type='statistical_outlier',
                    location=i,
                    severity=severity,
                    description=f"Value {value} at position {i} is {z_score:.2f} standard deviations from mean",
                    metadata={'value': value, 'z_score': z_score, 'mean': mean, 'std': std}
                )
                anomalies.append(anomaly)
    
    elif method == "isolation_forest" and HAS_SKLEARN:
        # Isolation Forest anomaly detection
        if len(sequence) < 10:
            return anomalies  # Need minimum samples
        
        # Extract features from sequence windows
        window_size = min(10, len(sequence) // 2)
        features = []
        positions = []
        
        for i in range(len(sequence) - window_size + 1):
            window = sequence[i:i+window_size]
            window_features = extract_sequence_features(window)
            features.append(window_features)
            positions.append(i)
        
        if not features:
            return anomalies
        
        # Train isolation forest
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        predictions = iso_forest.fit_predict(features)
        
        # Identify anomalies
        for i, pred in enumerate(predictions):
            if pred == -1:  # Anomaly
                anomaly = Anomaly(
                    anomaly_type='isolation_forest_anomaly',
                    location=positions[i],
                    severity=0.7,  # Default severity for isolation forest
                    description=f"Anomalous pattern detected at position {positions[i]}",
                    metadata={'window_start': positions[i], 'window_size': window_size}
                )
                anomalies.append(anomaly)
    
    return anomalies


def detect_distribution_anomalies(
    period_dict: Dict[int, int],
    theoretical_max_period: int,
    is_primitive: bool = False
) -> List[Anomaly]:
    """
    Detect anomalies in period distribution.
    
    This function identifies unexpected period values or distribution
    characteristics that deviate from theoretical expectations.
    
    **Key Terminology**:
    
    - **Distribution Anomaly**: An unexpected value or pattern in a
      distribution. For period distributions, anomalies might include
      periods that violate theoretical bounds or unexpected distribution
      shapes.
    
    - **Theoretical Bound**: A mathematically derived limit on possible
      values. For LFSR periods, the theoretical maximum is q^d - 1.
      Periods exceeding this bound are anomalies.
    
    Args:
        period_dict: Dictionary mapping period to count
        theoretical_max_period: Theoretical maximum period
        is_primitive: Whether polynomial is primitive
    
    Returns:
        List of detected anomalies
    """
    anomalies = []
    
    periods = list(period_dict.keys())
    if not periods:
        return anomalies
    
    max_observed = max(periods)
    min_observed = min(periods)
    
    # Check for periods exceeding theoretical maximum
    if max_observed > theoretical_max_period:
        anomaly = Anomaly(
            anomaly_type='bound_violation',
            location=max_observed,
            severity=1.0,
            description=f"Observed period {max_observed} exceeds theoretical maximum {theoretical_max_period}",
            metadata={
                'observed_period': max_observed,
                'theoretical_max': theoretical_max_period,
                'violation_amount': max_observed - theoretical_max_period
            }
        )
        anomalies.append(anomaly)
    
    # Check primitive polynomial expectations
    if is_primitive:
        # For primitive polynomials, all non-zero states should have max period
        expected_period = theoretical_max_period
        total_sequences = sum(period_dict.values())
        sequences_with_max = period_dict.get(expected_period, 0)
        
        if sequences_with_max < total_sequences * 0.9:  # Allow 10% tolerance
            severity = 1.0 - (sequences_with_max / total_sequences)
            anomaly = Anomaly(
                anomaly_type='primitive_expectation_violation',
                location=expected_period,
                severity=severity,
                description=f"Only {sequences_with_max}/{total_sequences} sequences have expected period {expected_period} for primitive polynomial",
                metadata={
                    'expected_period': expected_period,
                    'sequences_with_max': sequences_with_max,
                    'total_sequences': total_sequences,
                    'percentage': sequences_with_max / total_sequences * 100
                }
            )
            anomalies.append(anomaly)
    
    # Check for unexpected period values (statistical outliers)
    if len(periods) > 1:
        period_counts = list(period_dict.values())
        
        if HAS_NUMPY:
            mean_count = np.mean(period_counts)
            std_count = np.std(period_counts) if len(period_counts) > 1 else 1.0
        else:
            mean_count = sum(period_counts) / len(period_counts)
            variance = sum((x - mean_count) ** 2 for x in period_counts) / len(period_counts)
            std_count = variance ** 0.5 if variance > 0 else 1.0
        
        if std_count > 0:
            threshold = 2.0  # 2 standard deviations
            for period, count in period_dict.items():
                z_score = abs(count - mean_count) / std_count if std_count > 0 else 0.0
                if z_score > threshold:
                    severity = min(z_score / (threshold * 2), 1.0)
                    anomaly = Anomaly(
                        anomaly_type='distribution_outlier',
                        location=period,
                        severity=severity,
                        description=f"Period {period} has unusual frequency: {count} (z-score: {z_score:.2f})",
                        metadata={
                            'period': period,
                            'count': count,
                            'z_score': z_score,
                            'mean_count': mean_count
                        }
                    )
                    anomalies.append(anomaly)
    
    return anomalies


def detect_all_anomalies(
    sequence: Optional[List[int]] = None,
    period_dict: Optional[Dict[int, int]] = None,
    theoretical_max_period: Optional[int] = None,
    is_primitive: bool = False
) -> Dict[str, List[Anomaly]]:
    """
    Detect all types of anomalies.
    
    Convenience function that runs all anomaly detection algorithms.
    
    Args:
        sequence: Optional sequence to analyze
        period_dict: Optional period distribution
        theoretical_max_period: Optional theoretical maximum period
        is_primitive: Whether polynomial is primitive
    
    Returns:
        Dictionary mapping anomaly types to lists of anomalies
    """
    results = {}
    
    if sequence:
        results['sequence_anomalies'] = detect_sequence_anomalies(sequence)
    
    if period_dict and theoretical_max_period is not None:
        results['distribution_anomalies'] = detect_distribution_anomalies(
            period_dict, theoretical_max_period, is_primitive
        )
    
    return results
