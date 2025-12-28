#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ML model training pipeline for LFSR analysis.

This module provides automated training pipelines for ML models using
known results and generated datasets.
"""

from typing import Any, Dict, List, Optional, Tuple
import json
import os
from pathlib import Path

try:
    import numpy as np
    from sklearn.model_selection import GridSearchCV
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

from lfsr.ml.models import PeriodPredictor
from lfsr.ml.features import extract_polynomial_features
from lfsr.theoretical_db import get_database


def generate_training_dataset(
    max_degree: int = 10,
    field_order: int = 2,
    num_samples: Optional[int] = None
) -> List[Tuple[Dict[str, float], int]]:
    """
    Generate training dataset from known results and computed periods.
    
    This function generates a training dataset by extracting features from
    known polynomials and their periods, suitable for training period
    prediction models.
    
    **Key Terminology**:
    
    - **Training Dataset**: A collection of examples (polynomial features
      and their corresponding periods) used to train machine learning models.
      The model learns patterns from this data.
    
    - **Feature-Label Pairs**: Each training example consists of features
      (polynomial properties) and a label (the period). The model learns
      to predict labels from features.
    
    - **Dataset Generation**: Creating training data from known results,
      computed periods, or synthetic examples. Good datasets are diverse
      and representative of the problem space.
    
    Args:
        max_degree: Maximum polynomial degree to include
        field_order: Field order
        num_samples: Optional limit on number of samples
    
    Returns:
        List of (features_dict, period) tuples
    """
    if not HAS_SKLEARN:
        raise ImportError("scikit-learn and numpy are required for training")
    
    dataset = []
    
    # Get known results from database
    db = get_database()
    
    # Add known primitive polynomials
    for key, poly_data in db.db['primitive_polynomials'].items():
        if poly_data['degree'] <= max_degree and poly_data['field_order'] == field_order:
            features = extract_polynomial_features(
                poly_data['coefficients'],
                poly_data['field_order']
            )
            dataset.append((features, poly_data['order']))
    
    # Add known polynomial orders
    for key, order_data in db.db['polynomial_orders'].items():
        if order_data['degree'] <= max_degree and order_data['field_order'] == field_order:
            features = extract_polynomial_features(
                order_data['coefficients'],
                order_data['field_order']
            )
            dataset.append((features, order_data['order']))
    
    # Limit dataset size if requested
    if num_samples and len(dataset) > num_samples:
        import random
        dataset = random.sample(dataset, num_samples)
    
    return dataset


def train_period_predictor(
    training_data: Optional[List[Tuple[Dict[str, float], int]]] = None,
    model_type: str = "random_forest",
    max_degree: int = 10,
    field_order: int = 2,
    hyperparameter_tuning: bool = False
) -> Tuple[PeriodPredictor, Dict[str, float]]:
    """
    Train a period prediction model.
    
    This function trains a period prediction model using either provided
    training data or automatically generated data from known results.
    
    **Key Terminology**:
    
    - **Model Training**: The process of teaching a machine learning model
      to make predictions by showing it examples. The model adjusts its
      parameters to minimize prediction error.
    
    - **Hyperparameter Tuning**: Optimizing model settings (like number of
      trees in a random forest) to improve performance. This is done using
      techniques like grid search.
    
    - **Training Metrics**: Quantitative measures of model performance during
      training, such as mean squared error (MSE) and R² score. These help
      evaluate how well the model learned.
    
    Args:
        training_data: Optional training data (if None, generates automatically)
        model_type: Type of model to train
        max_degree: Maximum degree for dataset generation
        field_order: Field order
        hyperparameter_tuning: Whether to perform hyperparameter tuning
    
    Returns:
        Tuple of (trained model, training metrics)
    """
    if not HAS_SKLEARN:
        raise ImportError("scikit-learn is required for training")
    
    # Generate training data if not provided
    if training_data is None:
        training_data = generate_training_dataset(max_degree, field_order)
    
    if not training_data:
        raise ValueError("No training data available")
    
    # Create and train model
    predictor = PeriodPredictor(model_type=model_type)
    
    # Hyperparameter tuning if requested
    if hyperparameter_tuning and model_type == "random_forest":
        # Extract features and labels
        X = []
        y = []
        feature_order = None
        
        for features_dict, period in training_data:
            if feature_order is None:
                feature_order = sorted(features_dict.keys())
            from lfsr.ml.features import features_to_vector
            feature_vector = features_to_vector(features_dict, feature_order)
            X.append(feature_vector)
            y.append(float(period))
        
        X = np.array(X)
        y = np.array(y)
        
        # Grid search for hyperparameters
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [None, 10, 20]
        }
        base_model = PeriodPredictor(model_type=model_type)
        base_model._create_model()
        grid_search = GridSearchCV(
            base_model.model,
            param_grid,
            cv=5,
            scoring='neg_mean_squared_error'
        )
        grid_search.fit(X, y)
        predictor.model = grid_search.best_estimator_
        predictor.feature_order = feature_order
        predictor.is_trained = True
        
        # Evaluate
        from sklearn.metrics import mean_squared_error, r2_score
        y_pred = predictor.model.predict(X)
        metrics = {
            'train_mse': float(mean_squared_error(y, y_pred)),
            'train_r2': float(r2_score(y, y_pred)),
            'best_params': grid_search.best_params_
        }
    else:
        metrics = predictor.train(training_data)
    
    return predictor, metrics


def save_training_results(
    model: PeriodPredictor,
    metrics: Dict[str, float],
    filepath: str
) -> None:
    """
    Save trained model and training results.
    
    Args:
        model: Trained model
        metrics: Training metrics
        filepath: Path to save model (without extension)
    """
    # Save model
    model.save(f"{filepath}.pkl")
    
    # Save metrics
    with open(f"{filepath}_metrics.json", 'w') as f:
        json.dump(metrics, f, indent=2)


def load_trained_model(filepath: str) -> PeriodPredictor:
    """
    Load a trained model from file.
    
    Args:
        filepath: Path to model file
    
    Returns:
        Loaded PeriodPredictor model
    """
    predictor = PeriodPredictor()
    predictor.load(filepath)
    return predictor
