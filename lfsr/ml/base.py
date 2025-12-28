#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base classes and interfaces for ML integration.

This module provides base classes and interfaces for machine learning
models and feature extraction in LFSR analysis.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import json
import pickle
from pathlib import Path


class FeatureExtractor:
    """
    Extract features from LFSR properties for ML models.
    
    This class provides methods to extract numerical features from LFSR
    configurations and analysis results for use in machine learning models.
    
    **Key Terminology**:
    
    - **Feature Extraction**: The process of converting raw data (LFSR
      properties) into numerical features that machine learning models
      can use. Features are the input variables for ML models.
    
    - **Feature Vector**: A list of numerical values representing the
      extracted features. For example, [degree, field_order, num_taps, ...]
    
    - **Feature Engineering**: The process of selecting and transforming
      features to improve ML model performance.
    """
    
    @staticmethod
    def extract_polynomial_features(
        coefficients: List[int],
        field_order: int,
        degree: Optional[int] = None
    ) -> List[float]:
        """
        Extract features from polynomial coefficients.
        
        Features extracted:
        - Degree
        - Field order
        - Number of non-zero coefficients (taps)
        - Coefficient density
        - Position of first/last non-zero coefficient
        - Sum of coefficients
        
        Args:
            coefficients: Polynomial coefficients
            field_order: Field order
            degree: Optional degree (defaults to len(coefficients))
        
        Returns:
            List of feature values
        """
        if degree is None:
            degree = len(coefficients)
        
        # Count non-zero coefficients (taps)
        num_taps = sum(1 for c in coefficients if c != 0)
        
        # Coefficient density
        density = num_taps / degree if degree > 0 else 0.0
        
        # Position of first non-zero coefficient
        first_tap = next((i for i, c in enumerate(coefficients) if c != 0), -1)
        
        # Position of last non-zero coefficient
        last_tap = next((i for i, c in enumerate(reversed(coefficients)) if c != 0), -1)
        if last_tap >= 0:
            last_tap = degree - 1 - last_tap
        
        # Sum of coefficients
        coeff_sum = sum(coefficients)
        
        return [
            float(degree),
            float(field_order),
            float(num_taps),
            density,
            float(first_tap) if first_tap >= 0 else 0.0,
            float(last_tap) if last_tap >= 0 else float(degree - 1),
            float(coeff_sum)
        ]
    
    @staticmethod
    def extract_sequence_features(
        sequence: List[int],
        max_length: int = 1000
    ) -> List[float]:
        """
        Extract features from sequence.
        
        Features extracted:
        - Sequence length (truncated to max_length)
        - Mean value
        - Variance
        - Number of unique values
        - Run length statistics
        
        Args:
            sequence: Sequence of values
            max_length: Maximum length to consider
        
        Returns:
            List of feature values
        """
        seq = sequence[:max_length]
        
        if not seq:
            return [0.0] * 10
        
        # Basic statistics
        mean_val = sum(seq) / len(seq)
        variance = sum((x - mean_val) ** 2 for x in seq) / len(seq) if len(seq) > 1 else 0.0
        unique_count = len(set(seq))
        unique_ratio = unique_count / len(seq) if seq else 0.0
        
        # Run length statistics (for binary sequences)
        if all(x in [0, 1] for x in seq):
            runs = []
            current_run = 1
            for i in range(1, len(seq)):
                if seq[i] == seq[i-1]:
                    current_run += 1
                else:
                    runs.append(current_run)
                    current_run = 1
            runs.append(current_run)
            
            avg_run_length = sum(runs) / len(runs) if runs else 0.0
            max_run_length = max(runs) if runs else 0.0
        else:
            avg_run_length = 0.0
            max_run_length = 0.0
        
        return [
            float(len(seq)),
            mean_val,
            variance,
            float(unique_count),
            unique_ratio,
            avg_run_length,
            max_run_length,
            float(seq[0]) if seq else 0.0,
            float(seq[-1]) if seq else 0.0,
            float(sum(seq[:10]))  # Sum of first 10 elements
        ]


class MLModel(ABC):
    """
    Abstract base class for ML models.
    
    This class defines the interface that all ML models must implement,
    providing a consistent API for training, prediction, and persistence.
    
    **Key Terminology**:
    
    - **Machine Learning Model**: A mathematical model that learns patterns
      from data and can make predictions on new data. Examples include
      linear regression, neural networks, and decision trees.
    
    - **Training**: The process of teaching an ML model by showing it
      examples (training data) with known outcomes. The model learns
      patterns from these examples.
    
    - **Prediction**: Using a trained ML model to make predictions on new,
      unseen data. The model applies learned patterns to predict outcomes.
    
    - **Model Persistence**: Saving a trained model to disk so it can be
      loaded and used later without retraining.
    """
    
    def __init__(self, model_name: str):
        """
        Initialize ML model.
        
        Args:
            model_name: Name identifier for the model
        """
        self.model_name = model_name
        self.model = None
        self.is_trained = False
    
    @abstractmethod
    def train(self, X: List[List[float]], y: List[float]) -> None:
        """
        Train the model on data.
        
        Args:
            X: Feature vectors (list of feature lists)
            y: Target values (list of floats)
        """
        pass
    
    @abstractmethod
    def predict(self, X: List[List[float]]) -> List[float]:
        """
        Make predictions on new data.
        
        Args:
            X: Feature vectors (list of feature lists)
        
        Returns:
            List of predicted values
        """
        pass
    
    def save(self, filepath: str) -> None:
        """
        Save model to file.
        
        Args:
            filepath: Path to save model
        """
        model_data = {
            'model_name': self.model_name,
            'is_trained': self.is_trained,
            'model': self._serialize_model()
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load(self, filepath: str) -> None:
        """
        Load model from file.
        
        Args:
            filepath: Path to load model from
        """
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model_name = model_data['model_name']
        self.is_trained = model_data['is_trained']
        self._deserialize_model(model_data['model'])
    
    @abstractmethod
    def _serialize_model(self) -> Any:
        """Serialize model for storage."""
        pass
    
    @abstractmethod
    def _deserialize_model(self, data: Any) -> None:
        """Deserialize model from storage."""
        pass
