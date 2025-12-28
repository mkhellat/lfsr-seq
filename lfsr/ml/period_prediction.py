#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Period prediction using machine learning.

This module provides ML-based period prediction models that predict LFSR
periods from polynomial structure without full enumeration.
"""

from typing import Any, Dict, List, Optional, Union
import warnings

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    warnings.warn("scikit-learn not available. ML features will be limited.")

from lfsr.ml.base import MLModel, FeatureExtractor


class PeriodPredictor(MLModel):
    """
    ML model for predicting LFSR periods from polynomial structure.
    
    This class provides period prediction using machine learning models
    trained on polynomial features. It can predict periods without
    performing full state enumeration.
    
    **Key Terminology**:
    
    - **Period Prediction**: Using machine learning to predict the period
      of an LFSR from its polynomial structure, without computing the
      actual period through enumeration or factorization.
    
    - **Regression Model**: A machine learning model that predicts
      continuous numerical values (like period) rather than categories.
      Examples include Random Forest and Gradient Boosting.
    
    - **Feature-Based Prediction**: Making predictions based on extracted
      features (polynomial properties) rather than the raw polynomial itself.
      This enables generalization to unseen polynomials.
    
    **Mathematical Foundation**:
    
    The model learns a function:
    
    .. math::
    
       P = f(\\text{degree}, \\text{field\_order}, \\text{sparsity}, \\ldots)
    
    where P is the predicted period and f is learned from training data.
    """
    
    def __init__(self, model_type: str = "random_forest"):
        """
        Initialize period predictor.
        
        Args:
            model_type: Type of model ("random_forest" or "gradient_boosting")
        """
        super().__init__(f"period_predictor_{model_type}")
        self.model_type = model_type
        
        if not HAS_SKLEARN:
            self.model = None
            return
        
        if model_type == "random_forest":
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        elif model_type == "gradient_boosting":
            self.model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def _features_to_array(self, X: List[Dict[str, Union[int, float]]]) -> List[List[float]]:
        """Convert feature dictionaries to arrays."""
        if not X:
            return []
        
        # Get feature names from first example
        feature_names = sorted(X[0].keys())
        
        # Convert to arrays
        arrays = []
        for x in X:
            array = [float(x.get(name, 0)) for name in feature_names]
            arrays.append(array)
        
        return arrays
    
    def train(
        self,
        X: List[Dict[str, Union[int, float]]],
        y: List[int],
        test_size: float = 0.2
    ) -> Dict[str, float]:
        """
        Train the period prediction model.
        
        Args:
            X: List of feature dictionaries
            y: List of actual periods
            test_size: Fraction of data to use for testing
        
        Returns:
            Dictionary with training metrics
        """
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn is required for training")
        
        if not X or not y:
            raise ValueError("Training data cannot be empty")
        
        # Convert features to arrays
        X_array = self._features_to_array(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_array, y, test_size=test_size, random_state=42
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Evaluate
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        metrics = {
            'train_mae': mean_absolute_error(y_train, y_pred_train),
            'test_mae': mean_absolute_error(y_test, y_pred_test),
            'train_r2': r2_score(y_train, y_pred_train),
            'test_r2': r2_score(y_test, y_pred_test),
        }
        
        return metrics
    
    def predict(self, X: List[Dict[str, Union[int, float]]]) -> List[float]:
        """
        Predict periods from features.
        
        Args:
            X: List of feature dictionaries
        
        Returns:
            List of predicted periods
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before prediction")
        
        if not HAS_SKLEARN:
            raise RuntimeError("scikit-learn is required for prediction")
        
        X_array = self._features_to_array(X)
        predictions = self.model.predict(X_array)
        return [float(p) for p in predictions]
    
    def predict_single(
        self,
        coefficients: List[int],
        field_order: int,
        degree: Optional[int] = None
    ) -> float:
        """
        Predict period for a single polynomial.
        
        Convenience method for single predictions.
        
        Args:
            coefficients: Polynomial coefficients
            field_order: Field order
            degree: Optional degree
        
        Returns:
            Predicted period
        """
        features = FeatureExtractor.extract_polynomial_features(
            coefficients, field_order, degree
        )
        predictions = self.predict([features])
        return predictions[0]


def train_period_predictor(
    training_data: List[Dict[str, Any]],
    model_type: str = "random_forest"
) -> PeriodPredictor:
    """
    Train a period predictor on provided data.
    
    This function creates and trains a period prediction model on
    provided training data.
    
    **Key Terminology**:
    
    - **Training Data**: Examples with known outcomes used to teach
      the model. Each example has features (polynomial properties) and
      a target (actual period).
    
    - **Model Training**: The process of teaching the model by showing
      it many examples. The model learns patterns that map features to
      periods.
    
    Args:
        training_data: List of dictionaries with 'coefficients', 'field_order',
            'degree', and 'period' keys
        model_type: Type of model to train
    
    Returns:
        Trained PeriodPredictor
    """
    if not HAS_SKLEARN:
        raise RuntimeError("scikit-learn is required for training")
    
    # Extract features and targets
    X = []
    y = []
    
    for data in training_data:
        features = FeatureExtractor.extract_polynomial_features(
            data['coefficients'],
            data['field_order'],
            data.get('degree')
        )
        X.append(features)
        y.append(data['period'])
    
    # Create and train model
    predictor = PeriodPredictor(model_type=model_type)
    metrics = predictor.train(X, y)
    
    return predictor
