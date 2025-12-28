#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Anomaly detection in LFSR sequences and properties.

This module provides anomaly detection capabilities for identifying
unusual patterns, outliers, and anomalies in LFSR analysis results.
"""

from typing import Any, Dict, List, Optional
import warnings

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    warnings.warn("scikit-learn not available. Anomaly detection will be limited.")

from lfsr.ml.base import FeatureExtractor


class AnomalyDetector:
    """
    Detect anomalies in LFSR sequences and properties.
    
    This class provides anomaly detection using isolation forests and
    statistical methods to identify unusual patterns or outliers.
    
    **Key Terminology**:
    
    - **Anomaly Detection**: Identifying data points that deviate
      significantly from expected patterns. Anomalies can indicate errors,
      interesting cases, or security issues.
    
    - **Isolation Forest**: A machine learning algorithm that isolates
      anomalies by randomly partitioning data. Anomalies are easier to
      isolate and require fewer partitions.
    
    - **Outlier**: A data point that is significantly different from
      other data points. Outliers can be anomalies or just unusual cases.
    
    - **Anomaly Score**: A numerical value indicating how anomalous
      a data point is. Higher scores indicate more anomalous points.
    """
    
    def __init__(self, contamination: float = 0.1):
        """
        Initialize anomaly detector.
        
        Args:
            contamination: Expected proportion of anomalies (0.0 to 0.5)
        """
        self.contamination = contamination
        self.scaler = StandardScaler() if HAS_SKLEARN else None
        self.model: Any = None
    
    def detect_anomalies(
        self,
        sequences: List[List[int]],
        field_order: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in sequences.
        
        This function analyzes multiple sequences to identify anomalous ones.
        
        Args:
            sequences: List of sequences to analyze
            field_order: Field order
        
        Returns:
            List of anomaly detection results
        """
        if not HAS_SKLEARN:
            return self._statistical_anomaly_detection(sequences)
        
        if not sequences:
            return []
        
        # Extract features from each sequence
        features = []
        for seq in sequences:
            feat = FeatureExtractor.extract_sequence_features(seq, field_order)
            features.append(list(feat.values()))
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Detect anomalies
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=42
        )
        predictions = self.model.fit_predict(features_scaled)
        scores = self.model.score_samples(features_scaled)
        
        # Format results
        results = []
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            results.append({
                'sequence_index': i,
                'is_anomaly': pred == -1,
                'anomaly_score': float(score),
                'sequence_length': len(sequences[i])
            })
        
        return results
    
    def detect_property_anomalies(
        self,
        properties: List[Dict[str, Union[int, float]]]
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in LFSR properties.
        
        This function analyzes polynomial properties to identify anomalies.
        
        Args:
            properties: List of property dictionaries
        
        Returns:
            List of anomaly detection results
        """
        if not HAS_SKLEARN:
            return self._statistical_property_anomalies(properties)
        
        if not properties:
            return []
        
        # Convert to feature arrays
        feature_names = sorted(properties[0].keys())
        features = [
            [float(p.get(name, 0)) for name in feature_names]
            for p in properties
        ]
        
        # Scale
        features_scaled = self.scaler.fit_transform(features)
        
        # Detect
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=42
        )
        predictions = self.model.fit_predict(features_scaled)
        scores = self.model.score_samples(features_scaled)
        
        # Format results
        results = []
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            results.append({
                'property_index': i,
                'is_anomaly': pred == -1,
                'anomaly_score': float(score),
                'properties': properties[i]
            })
        
        return results
    
    def _statistical_anomaly_detection(
        self,
        sequences: List[List[int]]
    ) -> List[Dict[str, Any]]:
        """Statistical anomaly detection (fallback)."""
        if not sequences:
            return []
        
        # Extract features
        features = []
        for seq in sequences:
            feat = FeatureExtractor.extract_sequence_features(seq, 2)
            features.append(feat)
        
        # Simple statistical outlier detection
        lengths = [f['length'] for f in features]
        means = [f['mean'] for f in features]
        
        length_mean = sum(lengths) / len(lengths) if lengths else 0
        length_std = (
            (sum((l - length_mean) ** 2 for l in lengths) / len(lengths)) ** 0.5
            if lengths else 0
        )
        
        results = []
        for i, (length, mean) in enumerate(zip(lengths, means)):
            # Simple z-score based detection
            z_score = abs((length - length_mean) / length_std) if length_std > 0 else 0
            is_anomaly = z_score > 2.0  # 2 standard deviations
            
            results.append({
                'sequence_index': i,
                'is_anomaly': is_anomaly,
                'anomaly_score': z_score,
                'sequence_length': length
            })
        
        return results
    
    def _statistical_property_anomalies(
        self,
        properties: List[Dict[str, Union[int, float]]]
    ) -> List[Dict[str, Any]]:
        """Statistical property anomaly detection (fallback)."""
        if not properties:
            return []
        
        # Simple outlier detection based on degree
        degrees = [p.get('degree', 0) for p in properties]
        degree_mean = sum(degrees) / len(degrees) if degrees else 0
        degree_std = (
            (sum((d - degree_mean) ** 2 for d in degrees) / len(degrees)) ** 0.5
            if degrees else 0
        )
        
        results = []
        for i, prop in enumerate(properties):
            degree = prop.get('degree', 0)
            z_score = abs((degree - degree_mean) / degree_std) if degree_std > 0 else 0
            is_anomaly = z_score > 2.0
            
            results.append({
                'property_index': i,
                'is_anomaly': is_anomaly,
                'anomaly_score': z_score,
                'properties': prop
            })
        
        return results


def detect_anomalies(
    sequences: List[List[int]],
    field_order: int = 2,
    contamination: float = 0.1
) -> List[Dict[str, Any]]:
    """
    Detect anomalies in sequences.
    
    Convenience function for anomaly detection.
    
    Args:
        sequences: List of sequences to analyze
        field_order: Field order
        contamination: Expected proportion of anomalies
    
    Returns:
        List of anomaly detection results
    """
    detector = AnomalyDetector(contamination=contamination)
    return detector.detect_anomalies(sequences, field_order)
