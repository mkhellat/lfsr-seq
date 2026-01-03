#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Machine learning models for LFSR analysis.

This module provides ML models for period prediction, pattern detection,
and anomaly detection.
"""

from typing import Any, Dict, List, Optional, Tuple
import pickle
import os

import numpy as np

try:
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, r2_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

from lfsr.ml.features import extract_polynomial_features, features_to_vector


class PeriodPredictor:
    """
    Machine learning model for predicting LFSR period from polynomial structure.
    
    This class provides period prediction using trained ML models. The model
    learns relationships between polynomial features and period, enabling
    fast period estimation without full enumeration.
    
    **Key Terminology**:
    
    - **Period Prediction**: Using machine learning to estimate LFSR period
      from polynomial structure without computing the full period. This can
      be much faster than enumeration for large LFSRs.
    
    - **Regression Model**: A machine learning model that predicts
      continuous values (like period) from input features. Common types
      include linear regression, random forests, and neural networks.
    
    - **Feature Engineering**: The process of selecting and transforming
      input data (polynomial coefficients) into features that help the
      model make accurate predictions.
    
    - **Model Training**: The process of teaching a machine learning model
      to make predictions by showing it examples of polynomial features and
      their corresponding periods.
    """
    
    def __init__(self, model_type: str = "random_forest"):
        """
        Initialize period predictor.
        
        Args:
            model_type: Type of model ("linear", "ridge", "random_forest")
        """
        if not HAS_SKLEARN:
            raise ImportError("scikit-learn is required for ML features. Install with: pip install scikit-learn")
        
        self.model_type = model_type
        self.model = None
        self.feature_order = None
        self.is_trained = False
    
    def _create_model(self):
        """Create model instance based on model_type."""
        if self.model_type == "linear":
            self.model = LinearRegression()
        elif self.model_type == "ridge":
            self.model = Ridge(alpha=1.0)
        elif self.model_type == "random_forest":
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def train(
        self,
        training_data: List[Tuple[Dict[str, float], int]],
        test_size: float = 0.2
    ) -> Dict[str, float]:
        """
        Train the period prediction model.
        
        Args:
            training_data: List of (features_dict, period) tuples
            test_size: Fraction of data to use for testing
        
        Returns:
            Dictionary with training metrics (MSE, R²)
        """
        if not training_data:
            raise ValueError("Training data cannot be empty")
        
        # Extract features and labels
        X = []
        y = []
        feature_order = None
        
        for features_dict, period in training_data:
            if feature_order is None:
                feature_order = sorted(features_dict.keys())
            feature_vector = features_to_vector(features_dict, feature_order)
            X.append(feature_vector)
            y.append(float(period))
        
        X = np.array(X)
        y = np.array(y)
        self.feature_order = feature_order
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        # Create and train model
        self._create_model()
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Evaluate
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        metrics = {
            'train_mse': float(mean_squared_error(y_train, y_pred_train)),
            'test_mse': float(mean_squared_error(y_test, y_pred_test)),
            'train_r2': float(r2_score(y_train, y_pred_train)),
            'test_r2': float(r2_score(y_test, y_pred_test))
        }
        
        return metrics
    
    def predict(
        self,
        coefficients: List[int],
        field_order: int,
        polynomial: Optional[Any] = None
    ) -> float:
        """
        Predict period from polynomial.
        
        Args:
            coefficients: Polynomial coefficients
            field_order: Field order
            polynomial: Optional SageMath polynomial
        
        Returns:
            Predicted period
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        features = extract_polynomial_features(coefficients, field_order, polynomial)
        feature_vector = features_to_vector(features, self.feature_order)
        
        prediction = self.model.predict([feature_vector])[0]
        return float(prediction)
    
    def save(self, filepath: str) -> None:
        """Save model to file."""
        model_data = {
            'model_type': self.model_type,
            'model': self.model,
            'feature_order': self.feature_order,
            'is_trained': self.is_trained
        }
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load(self, filepath: str) -> None:
        """Load model from file."""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model_type = model_data['model_type']
        self.model = model_data['model']
        self.feature_order = model_data['feature_order']
        self.is_trained = model_data['is_trained']


class PatternDetector:
    """
    Pattern detection in LFSR sequences using ML.
    
    This class provides pattern detection capabilities for identifying
    recurring patterns, statistical anomalies, and structural features
    in LFSR sequences.
    """
    
    def __init__(self):
        """Initialize pattern detector."""
        pass
    
    def detect_patterns(self, sequence: List[int], min_pattern_length: int = 2) -> List[Dict[str, Any]]:
        """
        Detect patterns in sequence.
        
        Args:
            sequence: Sequence to analyze
            min_pattern_length: Minimum pattern length to detect
        
        Returns:
            List of detected patterns with positions and frequencies
        """
        patterns = []
        sequence_str = ''.join(map(str, sequence))
        
        # Simple pattern detection: find repeating substrings
        for length in range(min_pattern_length, len(sequence) // 2):
            for i in range(len(sequence) - length):
                pattern = sequence_str[i:i+length]
                count = sequence_str.count(pattern)
                if count > 1:
                    patterns.append({
                        'pattern': pattern,
                        'length': length,
                        'frequency': count,
                        'first_position': i
                    })
        
        # Remove duplicates
        seen = set()
        unique_patterns = []
        for p in patterns:
            key = (p['pattern'], p['length'])
            if key not in seen:
                seen.add(key)
                unique_patterns.append(p)
        
        return unique_patterns


class AnomalyDetector:
    """
    Anomaly detection in LFSR sequences and analysis results.
    
    This class provides anomaly detection capabilities for identifying
    unusual patterns, outliers, and unexpected results in LFSR analysis.
    """
    
    def __init__(self, threshold: float = 2.0):
        """
        Initialize anomaly detector.
        
        Args:
            threshold: Standard deviation threshold for anomaly detection
        """
        self.threshold = threshold
    
    def detect_anomalies(
        self,
        values: List[float],
        method: str = "zscore"
    ) -> List[Tuple[int, float]]:
        """
        Detect anomalies in a list of values.
        
        Args:
            values: List of values to analyze
            method: Detection method ("zscore", "iqr")
        
        Returns:
            List of (index, value) tuples for anomalies
        """
        if not values:
            return []
        
        values_array = np.array(values)
        anomalies = []
        
        if method == "zscore":
            mean = np.mean(values_array)
            std = np.std(values_array)
            if std > 0:
                z_scores = np.abs((values_array - mean) / std)
                for i, z_score in enumerate(z_scores):
                    if z_score > self.threshold:
                        anomalies.append((i, float(values_array[i])))
        
        elif method == "iqr":
            q1 = np.percentile(values_array, 25)
            q3 = np.percentile(values_array, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            for i, value in enumerate(values_array):
                if value < lower_bound or value > upper_bound:
                    anomalies.append((i, float(value)))
        
        return anomalies
