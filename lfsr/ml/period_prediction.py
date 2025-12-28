#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Period prediction using machine learning models.

This module provides ML-based period prediction from polynomial features.
"""

from typing import Any, Dict, List, Optional, Tuple
import json
import os
from pathlib import Path

from lfsr.ml.features import extract_polynomial_features, get_feature_vector


class PeriodPredictor:
    """
    Machine learning model for predicting LFSR period from polynomial features.
    
    This class provides period prediction using trained ML models. It supports
    multiple model types and can be trained on known LFSR results.
    
    **Key Terminology**:
    
    - **Period Prediction**: Using machine learning to predict the period of
      an LFSR from its polynomial structure, without performing expensive
      computation. This can provide quick estimates for large LFSRs.
    
    - **Machine Learning Model**: A mathematical model trained on data to make
      predictions. Common types include linear regression, decision trees, and
      neural networks.
    
    - **Training Data**: Known examples (polynomial features → period) used to
      train the model. More training data generally leads to better predictions.
    
    - **Feature Vector**: Numerical representation of polynomial properties
      used as input to the model.
    """
    
    def __init__(self, model_type: str = "linear"):
        """
        Initialize period predictor.
        
        Args:
            model_type: Type of model ("linear", "polynomial", "simple")
        """
        self.model_type = model_type
        self.model = None
        self.feature_names = None
        self.is_trained = False
    
    def train(
        self,
        training_data: List[Tuple[Dict[str, float], int]]
    ) -> None:
        """
        Train the period prediction model.
        
        This method trains the model on provided training data consisting
        of (features, period) pairs.
        
        Args:
            training_data: List of (features_dict, period) tuples
        """
        if not training_data:
            raise ValueError("Training data cannot be empty")
        
        # Extract feature vectors and periods
        X = []
        y = []
        
        # Determine feature names from first example
        if training_data:
            self.feature_names = sorted(training_data[0][0].keys())
        
        for features, period in training_data:
            feature_vec = get_feature_vector(features, self.feature_names)
            X.append(feature_vec)
            y.append(float(period))
        
        # Train simple linear model (can be extended to use scikit-learn, etc.)
        if self.model_type == "linear" or self.model_type == "simple":
            self._train_linear_model(X, y)
        else:
            # For now, default to linear
            self._train_linear_model(X, y)
        
        self.is_trained = True
    
    def _train_linear_model(self, X: List[List[float]], y: List[float]) -> None:
        """
        Train a simple linear regression model.
        
        This implements a basic linear model: period ≈ sum(weight_i * feature_i)
        
        Args:
            X: Feature vectors
            y: Target periods
        """
        if not X or not y:
            return
        
        num_features = len(X[0])
        
        # Simple approach: use theoretical max as baseline, adjust based on features
        # This is a placeholder - in production, use proper ML library
        self.model = {
            'type': 'linear',
            'baseline': sum(y) / len(y) if y else 0.0,
            'feature_weights': [0.0] * num_features
        }
        
        # Simple heuristic: weight features based on correlation with period
        # (This is simplified - proper ML would use gradient descent, etc.)
        for i in range(num_features):
            feature_values = [x[i] for x in X]
            # Simple correlation estimate
            if len(feature_values) > 1:
                mean_feat = sum(feature_values) / len(feature_values)
                mean_period = sum(y) / len(y)
                
                numerator = sum((feature_values[j] - mean_feat) * (y[j] - mean_period)
                               for j in range(len(feature_values)))
                denominator = sum((feature_values[j] - mean_feat) ** 2
                                for j in range(len(feature_values)))
                
                if denominator > 0:
                    self.model['feature_weights'][i] = numerator / denominator
                else:
                    self.model['feature_weights'][i] = 0.0
    
    def predict(self, features: Dict[str, float]) -> float:
        """
        Predict period from polynomial features.
        
        Args:
            features: Dictionary of polynomial features
        
        Returns:
            Predicted period
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        feature_vec = get_feature_vector(features, self.feature_names)
        
        if self.model and self.model['type'] == 'linear':
            # Linear prediction
            prediction = self.model['baseline']
            for i, weight in enumerate(self.model['feature_weights']):
                if i < len(feature_vec):
                    prediction += weight * feature_vec[i]
            return max(1.0, prediction)  # Ensure positive period
        else:
            # Fallback to theoretical max
            return features.get('theoretical_max_period', 1.0)
    
    def save(self, filepath: str) -> None:
        """Save model to file."""
        model_data = {
            'model_type': self.model_type,
            'model': self.model,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(model_data, f, indent=2)
    
    def load(self, filepath: str) -> None:
        """Load model from file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            model_data = json.load(f)
        
        self.model_type = model_data.get('model_type', 'linear')
        self.model = model_data.get('model')
        self.feature_names = model_data.get('feature_names')
        self.is_trained = model_data.get('is_trained', False)


def train_period_predictor(
    training_data: List[Tuple[Dict[str, float], int]],
    model_type: str = "linear"
) -> PeriodPredictor:
    """
    Train a period prediction model.
    
    Convenience function to create and train a period predictor.
    
    Args:
        training_data: List of (features_dict, period) tuples
        model_type: Type of model to train
    
    Returns:
        Trained PeriodPredictor instance
    """
    predictor = PeriodPredictor(model_type=model_type)
    predictor.train(training_data)
    return predictor
