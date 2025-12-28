#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ML model training pipeline for LFSR analysis.

This module provides automated training pipelines for ML models,
including data collection, feature engineering, and model evaluation.
"""

from typing import Any, Dict, List, Optional, Tuple
import json
import os
from pathlib import Path
from datetime import datetime

from lfsr.ml.features import extract_polynomial_features
from lfsr.ml.period_prediction import PeriodPredictor, train_period_predictor
from lfsr.theoretical_db import get_database


class TrainingPipeline:
    """
    Automated training pipeline for ML models.
    
    This class provides functionality to collect training data, engineer
    features, train models, and evaluate performance.
    
    **Key Terminology**:
    
    - **Training Pipeline**: An automated process for collecting data,
      preparing features, training models, and evaluating performance.
      This enables continuous improvement of ML models.
    
    - **Feature Engineering**: The process of creating and selecting
      features that are most useful for ML models. Good features are
      crucial for model performance.
    
    - **Model Evaluation**: Assessing the performance of trained models
      using metrics like accuracy, mean squared error, etc. This helps
      select the best model.
    
    - **Cross-Validation**: A technique for evaluating models by splitting
      data into training and validation sets multiple times to get more
      reliable performance estimates.
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize training pipeline.
        
        Args:
            data_dir: Directory for storing training data and models
        """
        if data_dir is None:
            data_dir = str(Path(__file__).parent.parent.parent / "data" / "ml_training")
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.training_data_file = self.data_dir / "training_data.json"
        self.models_dir = self.data_dir / "models"
        self.models_dir.mkdir(exist_ok=True)
    
    def collect_training_data_from_database(self) -> List[Tuple[Dict[str, float], int]]:
        """
        Collect training data from known result database.
        
        This method extracts training examples from the known result
        database, converting them to (features, period) pairs.
        
        Returns:
            List of (features_dict, period) tuples
        """
        training_data = []
        db = get_database()
        
        # Collect from primitive polynomials
        for key, poly_data in db.db['primitive_polynomials'].items():
            coeffs = poly_data['coefficients']
            field_order = poly_data['field_order']
            degree = poly_data['degree']
            order = poly_data['order']
            
            # Create polynomial and extract features
            try:
                from sage.all import GF, PolynomialRing
                F = GF(field_order)
                R = PolynomialRing(F, "t")
                poly_str = " + ".join([f"t^{i}" if i > 0 else "1" 
                                      for i, c in enumerate(coeffs) if c != 0])
                if not poly_str:
                    poly_str = "1"
                poly = R(poly_str)
                
                features = extract_polynomial_features(poly, coeffs, field_order, degree)
                training_data.append((features, order))
            except Exception:
                # Skip if polynomial creation fails
                continue
        
        # Collect from polynomial orders
        for key, order_data in db.db['polynomial_orders'].items():
            coeffs = order_data['coefficients']
            field_order = order_data['field_order']
            degree = order_data['degree']
            order = order_data['order']
            
            try:
                from sage.all import GF, PolynomialRing
                F = GF(field_order)
                R = PolynomialRing(F, "t")
                poly_str = " + ".join([f"t^{i}" if i > 0 else "1" 
                                      for i, c in enumerate(coeffs) if c != 0])
                if not poly_str:
                    poly_str = "1"
                poly = R(poly_str)
                
                features = extract_polynomial_features(poly, coeffs, field_order, degree)
                training_data.append((features, order))
            except Exception:
                continue
        
        return training_data
    
    def save_training_data(self, training_data: List[Tuple[Dict[str, float], int]]) -> None:
        """Save training data to file."""
        data_to_save = [
            {
                'features': features,
                'period': period
            }
            for features, period in training_data
        ]
        
        with open(self.training_data_file, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2)
    
    def load_training_data(self) -> List[Tuple[Dict[str, float], int]]:
        """Load training data from file."""
        if not self.training_data_file.exists():
            return []
        
        with open(self.training_data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return [(item['features'], item['period']) for item in data]
    
    def train_period_predictor_model(
        self,
        training_data: Optional[List[Tuple[Dict[str, float], int]]] = None,
        model_type: str = "linear",
        save_model: bool = True
    ) -> Tuple[PeriodPredictor, Dict[str, Any]]:
        """
        Train a period prediction model.
        
        Args:
            training_data: Optional training data (if None, collects from database)
            model_type: Type of model to train
            save_model: Whether to save the trained model
        
        Returns:
            Tuple of (trained model, evaluation metrics)
        """
        if training_data is None:
            training_data = self.collect_training_data_from_database()
        
        if not training_data:
            raise ValueError("No training data available")
        
        # Split into training and validation (80/20)
        split_idx = int(0.8 * len(training_data))
        train_data = training_data[:split_idx]
        val_data = training_data[split_idx:]
        
        # Train model
        predictor = train_period_predictor(train_data, model_type=model_type)
        
        # Evaluate on validation set
        errors = []
        for features, true_period in val_data:
            predicted = predictor.predict(features)
            error = abs(predicted - true_period)
            errors.append(error)
        
        metrics = {
            'mean_absolute_error': sum(errors) / len(errors) if errors else 0.0,
            'max_error': max(errors) if errors else 0.0,
            'min_error': min(errors) if errors else 0.0,
            'training_samples': len(train_data),
            'validation_samples': len(val_data),
            'model_type': model_type,
            'trained_at': datetime.now().isoformat()
        }
        
        # Save model
        if save_model:
            model_file = self.models_dir / f"period_predictor_{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            predictor.save(str(model_file))
            metrics['model_file'] = str(model_file)
        
        return predictor, metrics
    
    def evaluate_model(
        self,
        model: PeriodPredictor,
        test_data: List[Tuple[Dict[str, float], int]]
    ) -> Dict[str, Any]:
        """
        Evaluate a trained model on test data.
        
        Args:
            model: Trained model to evaluate
            test_data: Test data as (features, period) tuples
        
        Returns:
            Dictionary with evaluation metrics
        """
        errors = []
        relative_errors = []
        
        for features, true_period in test_data:
            predicted = model.predict(features)
            error = abs(predicted - true_period)
            errors.append(error)
            
            if true_period > 0:
                rel_error = error / true_period
                relative_errors.append(rel_error)
        
        metrics = {
            'mean_absolute_error': sum(errors) / len(errors) if errors else 0.0,
            'max_error': max(errors) if errors else 0.0,
            'min_error': min(errors) if errors else 0.0,
            'mean_relative_error': sum(relative_errors) / len(relative_errors) if relative_errors else 0.0,
            'max_relative_error': max(relative_errors) if relative_errors else 0.0,
            'test_samples': len(test_data)
        }
        
        return metrics


def train_models_from_database(
    model_type: str = "linear",
    save_models: bool = True
) -> Tuple[PeriodPredictor, Dict[str, Any]]:
    """
    Train ML models from known result database.
    
    Convenience function to train models using the known result database.
    
    Args:
        model_type: Type of model to train
        save_models: Whether to save trained models
    
    Returns:
        Tuple of (trained model, evaluation metrics)
    """
    pipeline = TrainingPipeline()
    return pipeline.train_period_predictor_model(
        training_data=None,
        model_type=model_type,
        save_model=save_models
    )
