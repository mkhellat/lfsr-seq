#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base classes and interfaces for ML-based LFSR analysis.

This module provides the foundation for ML integration, including base
classes, feature extraction, and model interfaces.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import os
from pathlib import Path

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, r2_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


@dataclass
class MLModelConfig:
    """
    Configuration for ML models.
    
    Attributes:
        model_type: Type of model (e.g., 'random_forest', 'gradient_boosting')
        model_params: Model-specific parameters
        feature_names: Names of features used
        model_version: Version of the model
    """
    model_type: str
    model_params: Dict[str, Any]
    feature_names: List[str]
    model_version: str = "1.0"


class BaseMLModel(ABC):
    """
    Base class for ML models in LFSR analysis.
    
    This abstract base class defines the interface that all ML models
    must implement, providing a consistent API for prediction and training.
    
    **Key Terminology**:
    
    - **Machine Learning Model**: A mathematical model that learns patterns
      from data to make predictions. In this context, models learn from
      LFSR configurations and sequences to predict properties like periods.
    
    - **Feature Extraction**: The process of converting raw data (polynomial
      coefficients, sequences) into numerical features that ML models can use.
      For example, extracting polynomial degree, field order, coefficient patterns.
    
    - **Training**: The process of teaching an ML model by showing it examples
      of input-output pairs. The model learns patterns from these examples.
    
    - **Prediction**: Using a trained model to make predictions on new,
      unseen data. For example, predicting the period of an LFSR from its
      polynomial structure.
    
    - **Model Persistence**: Saving trained models to disk so they can be
      loaded and used later without retraining.
    """
    
    def __init__(self, config: Optional[MLModelConfig] = None):
        """
        Initialize ML model.
        
        Args:
            config: Optional model configuration
        """
        self.config = config
        self.model = None
        self.is_trained = False
    
    @abstractmethod
    def train(self, X: List[List[float]], y: List[float]) -> Dict[str, Any]:
        """
        Train the model on provided data.
        
        Args:
            X: Feature vectors (list of feature lists)
            y: Target values (list of floats)
        
        Returns:
            Dictionary with training metrics
        """
        pass
    
    @abstractmethod
    def predict(self, X: List[List[float]]) -> List[float]:
        """
        Make predictions on new data.
        
        Args:
            X: Feature vectors (list of feature lists)
        
        Returns:
            List of predictions
        """
        pass
    
    @abstractmethod
    def save_model(self, filepath: str) -> None:
        """
        Save trained model to file.
        
        Args:
            filepath: Path to save model
        """
        pass
    
    @abstractmethod
    def load_model(self, filepath: str) -> None:
        """
        Load trained model from file.
        
        Args:
            filepath: Path to load model from
        """
        pass
    
    def evaluate(self, X: List[List[float]], y: List[float]) -> Dict[str, float]:
        """
        Evaluate model performance on test data.
        
        Args:
            X: Feature vectors
            y: True target values
        
        Returns:
            Dictionary with evaluation metrics
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        predictions = self.predict(X)
        
        if HAS_NUMPY and HAS_SKLEARN:
            y_array = np.array(y)
            pred_array = np.array(predictions)
            
            mse = mean_squared_error(y_array, pred_array)
            r2 = r2_score(y_array, pred_array)
            
            return {
                'mse': float(mse),
                'rmse': float(np.sqrt(mse)),
                'r2_score': float(r2)
            }
        else:
            # Fallback calculation without sklearn
            n = len(y)
            mse = sum((y[i] - predictions[i]) ** 2 for i in range(n)) / n
            rmse = mse ** 0.5
            
            y_mean = sum(y) / n
            ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
            ss_res = sum((y[i] - predictions[i]) ** 2 for i in range(n))
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
            
            return {
                'mse': mse,
                'rmse': rmse,
                'r2_score': r2
            }


def extract_polynomial_features(
    coefficients: List[int],
    field_order: int,
    degree: Optional[int] = None
) -> List[float]:
    """
    Extract features from polynomial structure for ML models.
    
    This function converts polynomial structure into numerical features
    that ML models can use for prediction.
    
    **Key Terminology**:
    
    - **Feature Extraction**: Converting raw data into numerical features.
      For polynomials, this includes degree, field order, coefficient patterns.
    
    - **Feature Vector**: A list of numerical values representing the
      characteristics of an object. For example, [4, 2, 3, 0.75] might
      represent [degree, field_order, nonzero_coeffs, sparsity].
    
    - **Sparsity**: The proportion of zero coefficients. A sparse polynomial
      has many zero coefficients, while a dense polynomial has few zeros.
    
    Args:
        coefficients: Polynomial coefficients
        field_order: Field order
        degree: Optional polynomial degree (defaults to len(coefficients))
    
    Returns:
        List of feature values
    """
    if degree is None:
        degree = len(coefficients)
    
    # Basic features
    features = [
        float(degree),
        float(field_order),
        float(len(coefficients))
    ]
    
    # Coefficient pattern features
    nonzero_count = sum(1 for c in coefficients if c != 0)
    sparsity = 1.0 - (nonzero_count / len(coefficients)) if coefficients else 0.0
    
    features.append(float(nonzero_count))
    features.append(sparsity)
    
    # Pattern detection
    is_trinomial = (nonzero_count == 3)
    is_pentanomial = (nonzero_count == 5)
    
    features.append(1.0 if is_trinomial else 0.0)
    features.append(1.0 if is_pentanomial else 0.0)
    
    # Coefficient distribution
    if coefficients:
        coeff_sum = sum(coefficients)
        coeff_mean = coeff_sum / len(coefficients)
        features.append(float(coeff_sum))
        features.append(coeff_mean)
    else:
        features.extend([0.0, 0.0])
    
    return features


def extract_sequence_features(
    sequence: List[int],
    max_length: int = 1000
) -> List[float]:
    """
    Extract features from sequence for ML models.
    
    Args:
        sequence: Sequence of values
        max_length: Maximum length to analyze
    
    Returns:
        List of feature values
    """
    seq = sequence[:max_length]
    
    if not seq:
        return [0.0] * 10
    
    features = [
        float(len(seq)),
        float(len(set(seq)))  # Unique values
    ]
    
    # Statistical features
    if HAS_NUMPY:
        seq_array = np.array(seq)
        features.extend([
            float(np.mean(seq_array)),
            float(np.std(seq_array)) if len(seq_array) > 1 else 0.0,
            float(np.min(seq_array)),
            float(np.max(seq_array))
        ])
    else:
        # Fallback without numpy
        features.extend([
            float(sum(seq) / len(seq)),
            float((sum((x - sum(seq)/len(seq))**2 for x in seq) / len(seq))**0.5) if len(seq) > 1 else 0.0,
            float(min(seq)),
            float(max(seq))
        ])
    
    # Pattern features
    if len(seq) >= 2:
        # Autocorrelation at lag 1
        mean_val = sum(seq) / len(seq)
        autocorr = sum((seq[i] - mean_val) * (seq[i+1] - mean_val) 
                      for i in range(len(seq)-1)) / (len(seq) - 1) if len(seq) > 1 else 0.0
        features.append(autocorr)
    else:
        features.append(0.0)
    
    # Balance (for binary sequences)
    if all(x in [0, 1] for x in seq):
        ones = sum(seq)
        balance = abs(ones - (len(seq) - ones)) / len(seq) if seq else 0.0
        features.append(balance)
    else:
        features.append(0.0)
    
    return features
