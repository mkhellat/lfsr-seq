#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ML model training pipeline for LFSR analysis.

This module provides automated pipelines for training and evaluating
ML models on LFSR data.
"""

from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
import json

from lfsr.ml.base import FeatureExtractor
from lfsr.ml.period_prediction import PeriodPredictor, train_period_predictor
from lfsr.theoretical_db import get_database


def generate_training_data_from_database(
    max_samples: Optional[int] = None
) -> List[Tuple[List[int], int, int]]:
    """
    Generate training data from known result database.
    
    This function extracts training examples from the known result database,
    creating (coefficients, field_order, period) tuples for model training.
    
    **Key Terminology**:
    
    - **Training Data**: Examples used to train ML models. Each example
      consists of input features (LFSR configuration) and the target output
      (known period).
    
    - **Data Generation**: The process of creating training examples from
      known results. This is essential for supervised learning where the
      model learns from labeled examples.
    
    - **Supervised Learning**: A type of ML where the model learns from
      examples with known outcomes. The model learns to predict outcomes
      for new, unseen inputs.
    
    Args:
        max_samples: Maximum number of samples to generate (None = all)
    
    Returns:
        List of (coefficients, field_order, period) tuples
    """
    db = get_database()
    training_data = []
    
    # Extract from primitive polynomials
    for key, poly_data in db.db['primitive_polynomials'].items():
        training_data.append((
            poly_data['coefficients'],
            poly_data['field_order'],
            poly_data['order']
        ))
    
    # Extract from polynomial orders
    for key, order_data in db.db['polynomial_orders'].items():
        training_data.append((
            order_data['coefficients'],
            order_data['field_order'],
            order_data['order']
        ))
    
    # Limit samples if requested
    if max_samples is not None and len(training_data) > max_samples:
        training_data = training_data[:max_samples]
    
    return training_data


def generate_synthetic_training_data(
    field_order: int = 2,
    min_degree: int = 2,
    max_degree: int = 10,
    num_samples: int = 100
) -> List[Tuple[List[int], int, int]]:
    """
    Generate synthetic training data by computing periods.
    
    This function generates training data by creating random LFSR
    configurations and computing their periods through analysis.
    
    **Key Terminology**:
    
    - **Synthetic Data**: Artificially generated data used for training.
      In this case, we generate random LFSR configurations and compute
      their periods to create training examples.
    
    - **Data Augmentation**: Techniques to increase the amount of training
      data, which can improve model performance. Synthetic data generation
      is a form of data augmentation.
    
    Args:
        field_order: Field order for generated LFSRs
        min_degree: Minimum LFSR degree
        max_degree: Maximum LFSR degree
        num_samples: Number of samples to generate
    
    Returns:
        List of (coefficients, field_order, period) tuples
    """
    import random
    from lfsr.core import compute_period_enumeration
    
    training_data = []
    
    for _ in range(num_samples):
        degree = random.randint(min_degree, max_degree)
        
        # Generate random coefficients
        coefficients = [random.randint(0, field_order - 1) for _ in range(degree)]
        
        # Ensure at least one non-zero coefficient
        if all(c == 0 for c in coefficients):
            coefficients[0] = 1
        
        # Compute period
        try:
            period = compute_period_enumeration(coefficients, field_order)
            if period is not None:
                training_data.append((coefficients, field_order, period))
        except Exception:
            # Skip if computation fails
            continue
    
    return training_data


def train_and_evaluate_model(
    training_data: List[Tuple[List[int], int, int]],
    model_type: str = "random_forest",
    test_split: float = 0.2
) -> Tuple[PeriodPredictor, Dict[str, Any]]:
    """
    Train and evaluate a period prediction model.
    
    This function trains a model and provides comprehensive evaluation
    metrics to assess its performance.
    
    **Key Terminology**:
    
    - **Model Evaluation**: The process of assessing how well a trained
      model performs on new, unseen data. Common metrics include mean
      absolute error (MAE) and R² score.
    
    - **Test Split**: The portion of data reserved for testing the model
      after training. This ensures the model is evaluated on data it hasn't
      seen during training.
    
    - **Overfitting**: When a model learns the training data too well
      but fails to generalize to new data. Evaluation on test data helps
      detect overfitting.
    
    Args:
        training_data: List of (coefficients, field_order, period) tuples
        model_type: Type of model to train
        test_split: Fraction of data to use for testing
    
    Returns:
        Tuple of (trained model, evaluation metrics)
    """
    # Train model
    model = train_period_predictor(training_data, model_type=model_type)
    
    # Extract features for evaluation
    X = []
    y = []
    for coefficients, field_order, period in training_data:
        features = FeatureExtractor.extract_polynomial_features(
            coefficients, field_order
        )
        X.append(features)
        y.append(float(period))
    
    # Train returns metrics
    metrics = model.train(X, y)
    
    return model, metrics


def save_training_pipeline(
    model: PeriodPredictor,
    training_data: List[Tuple[List[int], int, int]],
    metrics: Dict[str, Any],
    filepath: str
) -> None:
    """
    Save complete training pipeline information.
    
    This function saves the model, training data, and metrics for
    later use and reproducibility.
    
    Args:
        model: Trained model
        training_data: Training data used
        metrics: Evaluation metrics
        filepath: Path to save pipeline
    """
    pipeline_data = {
        'model_type': model.model_type,
        'training_samples': len(training_data),
        'metrics': metrics,
        'training_data': [
            {
                'coefficients': list(coeffs),
                'field_order': field_order,
                'period': period
            }
            for coeffs, field_order, period in training_data
        ]
    }
    
    # Save model separately
    model_path = Path(filepath).with_suffix('.model')
    model.save(str(model_path))
    
    # Save pipeline metadata
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(pipeline_data, f, indent=2)


def load_training_pipeline(filepath: str) -> Tuple[PeriodPredictor, Dict[str, Any]]:
    """
    Load training pipeline from file.
    
    Args:
        filepath: Path to pipeline file
    
    Returns:
        Tuple of (loaded model, pipeline metadata)
    """
    # Load metadata
    with open(filepath, 'r', encoding='utf-8') as f:
        pipeline_data = json.load(f)
    
    # Load model
    model_path = Path(filepath).with_suffix('.model')
    model = PeriodPredictor(model_type=pipeline_data['model_type'])
    model.load(str(model_path))
    
    return model, pipeline_data
