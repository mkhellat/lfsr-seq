#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ML model training pipeline for LFSR analysis.

This module provides automated pipelines for training ML models on LFSR data,
including data generation, preprocessing, training, and evaluation.
"""

from typing import Any, Dict, List, Optional
import json
from pathlib import Path

from lfsr.ml.period_prediction import PeriodPredictor, train_period_predictor
from lfsr.ml.base import FeatureExtractor


def generate_training_data(
    coefficients_list: List[List[int]],
    field_order: int,
    periods: List[int]
) -> List[Dict[str, Any]]:
    """
    Generate training data from LFSR analysis results.
    
    This function converts LFSR analysis results into training data format
    for machine learning models.
    
    **Key Terminology**:
    
    - **Training Data**: Examples with known outcomes used to train ML models.
      Each example has input features (polynomial properties) and target
      (actual period).
    
    - **Data Generation**: Creating training examples from existing analysis
      results. This enables model training without manual data collection.
    
    Args:
        coefficients_list: List of coefficient lists
        field_order: Field order
        periods: List of corresponding periods
    
    Returns:
        List of training data dictionaries
    """
    if len(coefficients_list) != len(periods):
        raise ValueError("Coefficients and periods must have same length")
    
    training_data = []
    for coeffs, period in zip(coefficients_list, periods):
        training_data.append({
            'coefficients': coeffs,
            'field_order': field_order,
            'degree': len(coeffs),
            'period': period
        })
    
    return training_data


def train_period_predictor_pipeline(
    training_data: List[Dict[str, Any]],
    model_type: str = "random_forest",
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Complete training pipeline for period predictor.
    
    This function provides a complete pipeline for training period prediction
    models, including data preparation, training, evaluation, and saving.
    
    **Key Terminology**:
    
    - **Training Pipeline**: An automated sequence of steps for training
      ML models, including data preparation, model training, evaluation,
      and persistence.
    
    - **Model Evaluation**: Assessing model performance using metrics like
      mean absolute error and R² score. This helps determine if the model
      is ready for use.
    
    Args:
        training_data: List of training data dictionaries
        model_type: Type of model to train
        output_dir: Optional directory to save model
    
    Returns:
        Dictionary with training results and metrics
    """
    # Train model
    predictor = train_period_predictor(training_data, model_type=model_type)
    
    # Extract features and targets for metrics
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
    
    # Get training metrics (already computed during training)
    # We'll recompute for reporting
    from lfsr.ml.period_prediction import HAS_SKLEARN
    if HAS_SKLEARN:
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_absolute_error, r2_score
        
        X_array = predictor._features_to_array(X)
        X_train, X_test, y_train, y_test = train_test_split(
            X_array, y, test_size=0.2, random_state=42
        )
        
        y_pred_train = predictor.model.predict(X_train)
        y_pred_test = predictor.model.predict(X_test)
        
        metrics = {
            'train_mae': mean_absolute_error(y_train, y_pred_train),
            'test_mae': mean_absolute_error(y_test, y_pred_test),
            'train_r2': r2_score(y_train, y_pred_train),
            'test_r2': r2_score(y_test, y_pred_test),
        }
    else:
        metrics = {}
    
    # Save model if output directory provided
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        model_path = output_path / f"period_predictor_{model_type}.pkl"
        predictor.save(str(model_path))
        
        # Save metadata
        metadata = {
            'model_type': model_type,
            'training_samples': len(training_data),
            'metrics': metrics,
            'feature_names': sorted(X[0].keys()) if X else []
        }
        metadata_path = output_path / f"period_predictor_{model_type}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    return {
        'predictor': predictor,
        'metrics': metrics,
        'model_path': str(output_path / f"period_predictor_{model_type}.pkl") if output_dir else None
    }
