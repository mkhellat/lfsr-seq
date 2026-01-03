#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Training pipeline for ML models.

This module provides functionality to generate training data and train
ML models for LFSR analysis tasks.
"""

from typing import Any, Dict, List, Optional, Tuple
import random
from pathlib import Path

from lfsr.sage_imports import *

from lfsr.ml.base import extract_polynomial_features
from lfsr.ml.period_prediction import PeriodPredictionModel
from lfsr.core import analyze_lfsr
from lfsr.polynomial import is_primitive_polynomial


def generate_training_data(
    num_samples: int = 100,
    max_degree: int = 10,
    field_order: int = 2,
    include_primitive: bool = True
) -> Tuple[List[List[float]], List[float]]:
    """
    Generate training data for period prediction models.
    
    This function generates synthetic LFSR configurations and computes
    their periods to create training data for ML models.
    
    **Key Terminology**:
    
    - **Training Data**: A collection of input-output pairs used to
      train machine learning models. For period prediction, this consists
      of (polynomial features, actual period) pairs.
    
    - **Synthetic Data**: Artificially generated data used for training
      when real data is limited. Synthetic LFSR configurations are
      generated with known properties.
    
    - **Feature Vector**: The input part of a training example, containing
      numerical features extracted from the polynomial structure.
    
    - **Target Value**: The output part of a training example, the value
      we want to predict. For period prediction, this is the actual period.
    
    Args:
        num_samples: Number of training samples to generate
        max_degree: Maximum polynomial degree
        field_order: Field order
        include_primitive: Whether to include primitive polynomials
    
    Returns:
        Tuple of (feature vectors, target periods)
    """
    X = []
    y = []
    
    F = GF(field_order)
    R = PolynomialRing(F, "t")
    
    generated = set()
    
    for _ in range(num_samples):
        # Generate random degree
        degree = random.randint(2, max_degree)
        
        # Generate random coefficients
        while True:
            coefficients = [random.randint(0, field_order - 1) for _ in range(degree)]
            coefficients[0] = 1  # Ensure monic polynomial
            
            # Create polynomial
            poly_str = "t^" + str(degree)
            for i in range(1, degree):
                if coefficients[i] != 0:
                    poly_str += f" + {coefficients[i]}*t^{degree-i}"
            if coefficients[degree-1] != 0:
                poly_str += f" + {coefficients[degree-1]}"
            
            try:
                poly = R(poly_str)
                poly_key = str(poly)
                
                if poly_key not in generated:
                    generated.add(poly_key)
                    break
            except:
                continue
        
        # Compute period
        try:
            seq_dict, period_dict, max_period, _, _, _, _ = analyze_lfsr(
                coefficients, field_order
            )
            
            # Extract features
            features = extract_polynomial_features(coefficients, field_order, degree)
            X.append(features)
            y.append(float(max_period))
        except Exception:
            # Skip if analysis fails
            continue
    
    return X, y


def train_period_prediction_model(
    model_type: str = "random_forest",
    num_samples: int = 100,
    max_degree: int = 10,
    field_order: int = 2,
    save_path: Optional[str] = None
) -> PeriodPredictionModel:
    """
    Train a period prediction model.
    
    This function generates training data and trains a period prediction
    model, optionally saving it to disk.
    
    Args:
        model_type: Type of model ("random_forest" or "gradient_boosting")
        num_samples: Number of training samples
        max_degree: Maximum polynomial degree for training
        field_order: Field order
        save_path: Optional path to save trained model
    
    Returns:
        Trained PeriodPredictionModel
    """
    print(f"Generating {num_samples} training samples...")
    X, y = generate_training_data(num_samples, max_degree, field_order)
    
    print(f"Generated {len(X)} training samples")
    print(f"Training {model_type} model...")
    
    model = PeriodPredictionModel(model_type=model_type)
    metrics = model.train(X, y)
    
    print(f"Training complete!")
    print(f"  MSE: {metrics['mse']:.2f}")
    print(f"  RMSE: {metrics['rmse']:.2f}")
    print(f"  R² Score: {metrics['r2_score']:.4f}")
    
    if save_path:
        print(f"Saving model to {save_path}...")
        model.save_model(save_path)
        print("Model saved!")
    
    return model


def evaluate_model_performance(
    model: PeriodPredictionModel,
    test_samples: int = 50,
    max_degree: int = 10,
    field_order: int = 2
) -> Dict[str, float]:
    """
    Evaluate model performance on test data.
    
    Args:
        model: Trained model to evaluate
        test_samples: Number of test samples
        max_degree: Maximum polynomial degree
        field_order: Field order
    
    Returns:
        Dictionary with evaluation metrics
    """
    print(f"Generating {test_samples} test samples...")
    X_test, y_test = generate_training_data(test_samples, max_degree, field_order)
    
    print("Evaluating model...")
    metrics = model.evaluate(X_test, y_test)
    
    print(f"Test Performance:")
    print(f"  MSE: {metrics['mse']:.2f}")
    print(f"  RMSE: {metrics['rmse']:.2f}")
    print(f"  R² Score: {metrics['r2_score']:.4f}")
    
    return metrics
