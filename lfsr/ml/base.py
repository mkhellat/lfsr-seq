#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base classes and interfaces for ML integration.

This module provides base classes and interfaces for machine learning
models and feature extraction in LFSR analysis.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import pickle
import os
from pathlib import Path


class FeatureExtractor:
    """
    Extract features from LFSR properties for ML models.
    
    This class provides feature extraction functions that convert LFSR
    properties into numerical features suitable for machine learning models.
    
    **Key Terminology**:
    
    - **Feature Extraction**: The process of converting raw data (LFSR
      properties) into numerical features that machine learning models
      can use. Features are the input variables for ML models.
    
    - **Feature Vector**: A list of numerical values representing the
      extracted features. For example, [degree, field_order, sparsity, ...]
    
    - **Feature Engineering**: The process of selecting and transforming
      features to improve model performance. Good features are crucial
      for ML model accuracy.
    """
    
    @staticmethod
    def extract_polynomial_features(
        coefficients: List[int],
        field_order: int,
        degree: Optional[int] = None
    ) -> Dict[str, Union[int, float]]:
        """
        Extract features from polynomial coefficients.
        
        This function extracts numerical features from LFSR polynomial
        coefficients that can be used for machine learning models.
        
        **Features Extracted**:
        
        - **Degree**: Polynomial degree (d)
        - **Field Order**: Field order (q)
        - **Sparsity**: Ratio of non-zero coefficients
        - **Non-Zero Count**: Number of non-zero coefficients
        - **Coefficient Sum**: Sum of all coefficients
        - **First Coefficient**: First coefficient value
        - **Last Coefficient**: Last coefficient value
        - **Coefficient Pattern**: Pattern indicators (trinomial, pentanomial, etc.)
        
        Args:
            coefficients: List of polynomial coefficients
            field_order: Field order
            degree: Optional degree (defaults to len(coefficients))
        
        Returns:
            Dictionary of feature names to values
        """
        if degree is None:
            degree = len(coefficients)
        
        non_zero_count = sum(1 for c in coefficients if c != 0)
        sparsity = non_zero_count / degree if degree > 0 else 0.0
        coeff_sum = sum(coefficients)
        
        # Pattern detection
        is_trinomial = non_zero_count == 3
        is_pentanomial = non_zero_count == 5
        
        features = {
            'degree': degree,
            'field_order': field_order,
            'sparsity': sparsity,
            'non_zero_count': non_zero_count,
            'coefficient_sum': coeff_sum,
            'first_coefficient': coefficients[0] if coefficients else 0,
            'last_coefficient': coefficients[-1] if coefficients else 0,
            'is_trinomial': 1 if is_trinomial else 0,
            'is_pentanomial': 1 if is_pentanomial else 0,
        }
        
        return features
    
    @staticmethod
    def extract_sequence_features(
        sequence: List[int],
        field_order: int = 2
    ) -> Dict[str, Union[int, float]]:
        """
        Extract features from sequence for pattern detection.
        
        This function extracts statistical and frequency-domain features
        from LFSR sequences for pattern detection and analysis.
        
        **Features Extracted**:
        
        - **Length**: Sequence length
        - **Mean**: Mean value
        - **Variance**: Variance of values
        - **Balance**: Balance (for binary sequences)
        - **Runs**: Number of runs
        - **Autocorrelation**: First-order autocorrelation
        
        Args:
            sequence: Sequence of values
            field_order: Field order (default: 2)
        
        Returns:
            Dictionary of feature names to values
        """
        if not sequence:
            return {}
        
        length = len(sequence)
        mean = sum(sequence) / length if length > 0 else 0.0
        
        # Variance
        variance = sum((x - mean) ** 2 for x in sequence) / length if length > 0 else 0.0
        
        # Balance (for binary)
        if field_order == 2:
            ones = sum(sequence)
            zeros = length - ones
            balance = abs(ones - zeros) / length if length > 0 else 0.0
        else:
            balance = 0.0
        
        # Runs (consecutive identical values)
        runs = 1
        for i in range(1, length):
            if sequence[i] != sequence[i-1]:
                runs += 1
        
        # Autocorrelation (first-order)
        autocorr = 0.0
        if length > 1:
            autocorr = sum(
                (sequence[i] - mean) * (sequence[i+1] - mean)
                for i in range(length - 1)
            ) / (length - 1) if length > 1 else 0.0
        
        features = {
            'length': length,
            'mean': mean,
            'variance': variance,
            'balance': balance,
            'runs': runs,
            'autocorrelation': autocorr,
        }
        
        return features


class MLModel(ABC):
    """
    Abstract base class for ML models.
    
    This class defines the interface that all ML models must implement,
    providing a consistent API for training, prediction, and persistence.
    
    **Key Terminology**:
    
    - **Machine Learning Model**: A mathematical model that learns patterns
      from data and can make predictions on new data. Models are trained
      on examples and then used for inference.
    
    - **Training**: The process of teaching a model by showing it examples
      with known outcomes. The model learns patterns from these examples.
    
    - **Inference**: Using a trained model to make predictions on new,
      unseen data. This is also called prediction.
    
    - **Model Persistence**: Saving a trained model to disk so it can be
      loaded later without retraining. This enables model reuse.
    """
    
    def __init__(self, model_name: str):
        """
        Initialize ML model.
        
        Args:
            model_name: Name of the model
        """
        self.model_name = model_name
        self.model: Any = None
        self.is_trained = False
    
    @abstractmethod
    def train(self, X: List[Dict[str, Union[int, float]]], y: List[Any]) -> None:
        """
        Train the model on data.
        
        Args:
            X: List of feature dictionaries
            y: List of target values
        """
        pass
    
    @abstractmethod
    def predict(self, X: List[Dict[str, Union[int, float]]]) -> List[Any]:
        """
        Make predictions on data.
        
        Args:
            X: List of feature dictionaries
        
        Returns:
            List of predictions
        """
        pass
    
    def save(self, filepath: str) -> None:
        """
        Save model to file.
        
        Args:
            filepath: Path to save model
        """
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'model_name': self.model_name,
                'is_trained': self.is_trained
            }, f)
    
    def load(self, filepath: str) -> None:
        """
        Load model from file.
        
        Args:
            filepath: Path to load model from
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.model_name = data['model_name']
            self.is_trained = data['is_trained']
