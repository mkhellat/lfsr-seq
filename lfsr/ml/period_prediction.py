#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Period prediction models using machine learning.

This module provides ML-based period prediction for LFSRs, learning to
predict periods from polynomial structure features.
"""

from typing import Any, Dict, List, Optional
import json
import os
from pathlib import Path

from lfsr.ml.base import BaseMLModel, MLModelConfig, extract_polynomial_features

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.model_selection import train_test_split
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


class PeriodPredictionModel(BaseMLModel):
    """
    ML model for predicting LFSR periods from polynomial structure.
    
    This model learns to predict the period of an LFSR from features
    extracted from its characteristic polynomial.
    
    **Key Terminology**:
    
    - **Period Prediction**: Using machine learning to predict the period
      of an LFSR from its polynomial structure, without computing the period
      directly. This can be faster than enumeration for large LFSRs.
    
    - **Supervised Learning**: A type of machine learning where the model
      learns from labeled examples (input-output pairs). For period prediction,
      examples are (polynomial features, actual period) pairs.
    
    - **Regression**: A type of machine learning task where the goal is to
      predict a continuous numerical value (like period) rather than a category.
      Period prediction is a regression problem.
    
    - **Random Forest**: An ensemble ML method that combines multiple decision
      trees to make predictions. It's interpretable and works well for
      structured data like polynomial features.
    
    - **Gradient Boosting**: An ensemble ML method that builds models
      sequentially, each correcting the errors of the previous ones. Often
      more accurate than random forests but less interpretable.
    """
    
    def __init__(self, model_type: str = "random_forest", config: Optional[MLModelConfig] = None):
        """
        Initialize period prediction model.
        
        Args:
            model_type: Type of model ("random_forest" or "gradient_boosting")
            config: Optional model configuration
        """
        if config is None:
            feature_names = [
                'degree', 'field_order', 'num_coeffs', 'nonzero_count',
                'sparsity', 'is_trinomial', 'is_pentanomial',
                'coeff_sum', 'coeff_mean'
            ]
            config = MLModelConfig(
                model_type=model_type,
                model_params={},
                feature_names=feature_names
            )
        
        super().__init__(config)
        self.model_type = model_type
        
        if HAS_SKLEARN:
            if model_type == "random_forest":
                self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            elif model_type == "gradient_boosting":
                self.model = GradientBoostingRegressor(n_estimators=100, random_state=42)
            else:
                raise ValueError(f"Unknown model type: {model_type}")
        else:
            self.model = None
    
    def train(self, X: List[List[float]], y: List[float]) -> Dict[str, Any]:
        """
        Train the period prediction model.
        
        Args:
            X: Feature vectors (list of feature lists)
            y: Target periods (list of floats)
        
        Returns:
            Dictionary with training metrics
        """
        if not HAS_SKLEARN:
            raise ImportError("scikit-learn is required for ML model training")
        
        if not self.model:
            raise ValueError("Model not initialized")
        
        # Convert to numpy arrays if available
        if HAS_NUMPY:
            X_array = np.array(X)
            y_array = np.array(y)
        else:
            X_array = X
            y_array = y
        
        # Train model
        self.model.fit(X_array, y_array)
        self.is_trained = True
        
        # Evaluate on training data
        predictions = self.model.predict(X_array)
        
        if HAS_NUMPY:
            mse = np.mean((y_array - predictions) ** 2)
            rmse = np.sqrt(mse)
            r2 = 1 - (np.sum((y_array - predictions) ** 2) / 
                     np.sum((y_array - np.mean(y_array)) ** 2))
        else:
            n = len(y)
            mse = sum((y[i] - predictions[i]) ** 2 for i in range(n)) / n
            rmse = mse ** 0.5
            y_mean = sum(y) / n
            ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
            ss_res = sum((y[i] - predictions[i]) ** 2 for i in range(n))
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        return {
            'mse': float(mse),
            'rmse': float(rmse),
            'r2_score': float(r2),
            'training_samples': len(X)
        }
    
    def predict(self, X: List[List[float]]) -> List[float]:
        """
        Predict periods from polynomial features.
        
        Args:
            X: Feature vectors (list of feature lists)
        
        Returns:
            List of predicted periods
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        if not self.model:
            raise ValueError("Model not initialized")
        
        if HAS_NUMPY:
            X_array = np.array(X)
            predictions = self.model.predict(X_array)
            return [float(p) for p in predictions]
        else:
            predictions = self.model.predict(X)
            return [float(p) for p in predictions]
    
    def predict_period(
        self,
        coefficients: List[int],
        field_order: int,
        degree: Optional[int] = None
    ) -> float:
        """
        Predict period directly from polynomial coefficients.
        
        Convenience method that extracts features and makes prediction.
        
        Args:
            coefficients: Polynomial coefficients
            field_order: Field order
            degree: Optional polynomial degree
        
        Returns:
            Predicted period
        """
        features = extract_polynomial_features(coefficients, field_order, degree)
        predictions = self.predict([features])
        return predictions[0]
    
    def save_model(self, filepath: str) -> None:
        """
        Save trained model to file.
        
        Args:
            filepath: Path to save model
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before saving")
        
        model_dir = Path(filepath).parent
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Save model using joblib if available, otherwise pickle
        try:
            import joblib
            joblib.dump(self.model, filepath + '.model')
        except ImportError:
            import pickle
            with open(filepath + '.model', 'wb') as f:
                pickle.dump(self.model, f)
        
        # Save configuration
        config_dict = {
            'model_type': self.model_type,
            'config': {
                'model_type': self.config.model_type,
                'model_params': self.config.model_params,
                'feature_names': self.config.feature_names,
                'model_version': self.config.model_version
            },
            'is_trained': self.is_trained
        }
        
        with open(filepath + '.config.json', 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    def load_model(self, filepath: str) -> None:
        """
        Load trained model from file.
        
        Args:
            filepath: Path to load model from
        """
        # Load configuration
        with open(filepath + '.config.json', 'r') as f:
            config_dict = json.load(f)
        
        self.model_type = config_dict['model_type']
        self.config = MLModelConfig(**config_dict['config'])
        self.is_trained = config_dict['is_trained']
        
        # Load model
        try:
            import joblib
            self.model = joblib.load(filepath + '.model')
        except ImportError:
            import pickle
            with open(filepath + '.model', 'rb') as f:
                self.model = pickle.load(f)


def create_period_prediction_model(
    model_type: str = "random_forest"
) -> PeriodPredictionModel:
    """
    Create a new period prediction model.
    
    Args:
        model_type: Type of model ("random_forest" or "gradient_boosting")
    
    Returns:
        PeriodPredictionModel instance
    """
    return PeriodPredictionModel(model_type=model_type)
