#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Period prediction using machine learning.

This module provides ML-based period prediction models that can predict
LFSR period from polynomial structure without full enumeration.
"""

from typing import List, Optional, Tuple, Dict, Any
import math

from lfsr.ml.base import MLModel, FeatureExtractor

# Try to import scikit-learn, but make it optional
try:
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


class PeriodPredictor(MLModel):
    """
    ML model for predicting LFSR period from polynomial features.
    
    This class provides period prediction using machine learning models
    trained on known LFSR configurations and their periods.
    
    **Key Terminology**:
    
    - **Period Prediction**: Using machine learning to predict the period
      of an LFSR from its polynomial structure without performing full
      enumeration. This can be much faster than enumeration for large LFSRs.
    
    - **Regression Model**: A type of ML model that predicts continuous
      numerical values (like period) rather than discrete categories.
      Examples include linear regression and random forests.
    
    - **Feature Engineering**: Selecting and transforming polynomial
      properties into numerical features that help the model make accurate
      predictions.
    
    - **Training Data**: Examples of LFSR configurations with known periods
      used to train the prediction model. The model learns patterns from
      these examples.
    """
    
    def __init__(self, model_type: str = "random_forest"):
        """
        Initialize period predictor.
        
        Args:
            model_type: Type of model ("linear" or "random_forest")
        """
        super().__init__(f"period_predictor_{model_type}")
        self.model_type = model_type
        self.scaler = None
        
        if not HAS_SKLEARN:
            raise ImportError(
                "scikit-learn is required for period prediction. "
                "Install with: pip install scikit-learn"
            )
        
        if model_type == "linear":
            self.model = LinearRegression()
        elif model_type == "random_forest":
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        self.scaler = StandardScaler()
    
    def train(
        self,
        X: List[List[float]],
        y: List[float]
    ) -> Dict[str, float]:
        """
        Train the period prediction model.
        
        This method trains the model on feature vectors (X) and known
        periods (y), then evaluates the model's performance.
        
        Args:
            X: Feature vectors (list of feature lists)
            y: Known periods (list of floats)
        
        Returns:
            Dictionary with training metrics (MAE, R² score)
        """
        if not HAS_SKLEARN:
            raise ImportError("scikit-learn is required for training")
        
        # Split data for evaluation
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        return {
            'mean_absolute_error': mae,
            'r2_score': r2,
            'training_samples': len(X_train),
            'test_samples': len(X_test)
        }
    
    def predict(self, X: List[List[float]]) -> List[float]:
        """
        Predict periods from feature vectors.
        
        Args:
            X: Feature vectors (list of feature lists)
        
        Returns:
            List of predicted periods
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        if not HAS_SKLEARN:
            raise ImportError("scikit-learn is required for prediction")
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Predict
        predictions = self.model.predict(X_scaled)
        
        # Ensure non-negative predictions
        return [max(0.0, float(p)) for p in predictions]
    
    def predict_period(
        self,
        coefficients: List[int],
        field_order: int,
        degree: Optional[int] = None
    ) -> float:
        """
        Predict period from polynomial coefficients.
        
        Convenience method that extracts features and predicts in one call.
        
        Args:
            coefficients: Polynomial coefficients
            field_order: Field order
            degree: Optional degree (defaults to len(coefficients))
        
        Returns:
            Predicted period
        """
        features = FeatureExtractor.extract_polynomial_features(
            coefficients, field_order, degree
        )
        predictions = self.predict([features])
        return predictions[0]
    
    def _serialize_model(self) -> Any:
        """Serialize model for storage."""
        return {
            'model_type': self.model_type,
            'model': self.model,
            'scaler': self.scaler
        }
    
    def _deserialize_model(self, data: Any) -> None:
        """Deserialize model from storage."""
        self.model_type = data['model_type']
        self.model = data['model']
        self.scaler = data['scaler']


def train_period_predictor(
    training_data: List[Tuple[List[int], int, int]],
    model_type: str = "random_forest"
) -> PeriodPredictor:
    """
    Train a period prediction model from training data.
    
    This function creates and trains a period prediction model using
    provided training data consisting of (coefficients, field_order, period)
    tuples.
    
    **Key Terminology**:
    
    - **Training Data**: Examples used to train the ML model. Each example
      consists of an LFSR configuration (coefficients, field order) and
      its known period.
    
    - **Model Training**: The process of teaching the model by showing it
      many examples. The model learns patterns that relate polynomial
      features to periods.
    
    Args:
        training_data: List of (coefficients, field_order, period) tuples
        model_type: Type of model to train ("linear" or "random_forest")
    
    Returns:
        Trained PeriodPredictor model
    
    Example:
        >>> training_data = [
        ...     ([1, 0, 0, 1], 2, 15),  # coefficients, field_order, period
        ...     ([1, 1], 2, 3),
        ... ]
        >>> model = train_period_predictor(training_data)
        >>> predicted = model.predict_period([1, 0, 0, 1], 2)
    """
    if not HAS_SKLEARN:
        raise ImportError(
            "scikit-learn is required for training. "
            "Install with: pip install scikit-learn"
        )
    
    # Extract features and targets
    X = []
    y = []
    
    for coefficients, field_order, period in training_data:
        features = FeatureExtractor.extract_polynomial_features(
            coefficients, field_order
        )
        X.append(features)
        y.append(float(period))
    
    # Create and train model
    predictor = PeriodPredictor(model_type=model_type)
    metrics = predictor.train(X, y)
    
    return predictor
