#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example: Machine Learning Integration Features

This example demonstrates ML-based analysis capabilities, including period
prediction, pattern detection, anomaly detection, and model training.

Example Usage:
    python3 examples/ml_integration_example.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import SageMath
try:
    from sage.all import *
except ImportError:
    print("ERROR: SageMath is required for this example", file=sys.stderr)
    sys.exit(1)

try:
    from sklearn.ensemble import RandomForestRegressor
    HAS_SKLEARN = True
except ImportError:
    print("WARNING: scikit-learn not available. Some ML features may not work.", file=sys.stderr)
    HAS_SKLEARN = False

from lfsr.ml.period_prediction import PeriodPredictionModel, create_period_prediction_model
from lfsr.ml.pattern_detection import detect_all_patterns
from lfsr.ml.anomaly_detection import detect_all_anomalies
from lfsr.ml.training import generate_training_data, train_period_prediction_model
from lfsr.ml.base import extract_polynomial_features
from lfsr.core import analyze_lfsr


def example_period_prediction():
    """Example of period prediction."""
    print("=" * 70)
    print("Example 1: Period Prediction")
    print("=" * 70)
    
    if not HAS_SKLEARN:
        print("\n⚠️  scikit-learn required for period prediction")
        return
    
    # Generate training data and train model
    print("\nTraining period prediction model...")
    X, y = generate_training_data(num_samples=50, max_degree=8, field_order=2)
    
    model = create_period_prediction_model("random_forest")
    metrics = model.train(X, y)
    
    print(f"\nTraining Metrics:")
    print(f"  MSE: {metrics['mse']:.2f}")
    print(f"  RMSE: {metrics['rmse']:.2f}")
    print(f"  R² Score: {metrics['r2_score']:.4f}")
    
    # Predict period for a new polynomial
    coefficients = [1, 0, 0, 1]
    predicted = model.predict_period(coefficients, field_order=2)
    
    # Compare with actual period
    _, _, actual_period, _, _, _, _ = analyze_lfsr(coefficients, 2)
    
    print(f"\nPrediction Example:")
    print(f"  Coefficients: {coefficients}")
    print(f"  Predicted period: {predicted:.2f}")
    print(f"  Actual period: {actual_period}")
    print(f"  Error: {abs(predicted - actual_period):.2f}")


def example_pattern_detection():
    """Example of pattern detection."""
    print("\n" + "=" * 70)
    print("Example 2: Pattern Detection")
    print("=" * 70)
    
    # Generate a sequence with patterns
    sequence = [1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1]
    
    print(f"\nAnalyzing sequence: {sequence[:20]}...")
    
    patterns = detect_all_patterns(sequence)
    
    print(f"\nDetected Patterns:")
    for pattern_type, pattern_list in patterns.items():
        print(f"\n  {pattern_type}: {len(pattern_list)} patterns")
        for i, pattern in enumerate(pattern_list[:3]):  # Show top 3
            print(f"    Pattern {i+1}: {pattern.description}")
            print(f"      Confidence: {pattern.confidence:.2f}")
            print(f"      Position: {pattern.start_position}-{pattern.end_position}")


def example_anomaly_detection():
    """Example of anomaly detection."""
    print("\n" + "=" * 70)
    print("Example 3: Anomaly Detection")
    print("=" * 70)
    
    # Create sequence with anomaly
    sequence = [0] * 50 + [1] * 50 + [0] * 50 + [99] + [0] * 50  # 99 is an anomaly
    
    print(f"\nAnalyzing sequence (length: {len(sequence)})...")
    
    anomalies = detect_all_anomalies(
        sequence=sequence,
        period_dict={5: 10, 6: 8, 7: 12, 20: 1},  # 20 is unusual
        theoretical_max_period=15,
        is_primitive=False
    )
    
    print(f"\nDetected Anomalies:")
    for anomaly_type, anomaly_list in anomalies.items():
        print(f"\n  {anomaly_type}: {len(anomaly_list)} anomalies")
        for i, anomaly in enumerate(anomaly_list[:3]):  # Show top 3
            print(f"    Anomaly {i+1}: {anomaly.description}")
            print(f"      Severity: {anomaly.severity:.2f}")
            print(f"      Location: {anomaly.location}")


def example_model_training():
    """Example of model training."""
    print("\n" + "=" * 70)
    print("Example 4: Model Training")
    print("=" * 70)
    
    if not HAS_SKLEARN:
        print("\n⚠️  scikit-learn required for model training")
        return
    
    print("\nTraining period prediction model...")
    print("(This may take a moment)")
    
    model = train_period_prediction_model(
        model_type="random_forest",
        num_samples=50,  # Small for example
        max_degree=8,
        field_order=2,
        save_path=None  # Don't save in example
    )
    
    print("\n✓ Model training complete!")
    print("  Model can now be used for period prediction")


def example_feature_extraction():
    """Example of feature extraction."""
    print("\n" + "=" * 70)
    print("Example 5: Feature Extraction")
    print("=" * 70)
    
    from lfsr.ml.base import extract_polynomial_features, extract_sequence_features
    
    # Polynomial features
    coefficients = [1, 0, 0, 1, 0, 1]
    features = extract_polynomial_features(coefficients, field_order=2, degree=6)
    
    print(f"\nPolynomial Features:")
    print(f"  Coefficients: {coefficients}")
    print(f"  Features: {features}")
    print(f"  Feature names: degree, field_order, num_coeffs, nonzero_count,")
    print(f"                  sparsity, is_trinomial, is_pentanomial,")
    print(f"                  coeff_sum, coeff_mean")
    
    # Sequence features
    sequence = [1, 0, 1, 0, 1, 1, 0, 1, 0, 1]
    seq_features = extract_sequence_features(sequence)
    
    print(f"\nSequence Features:")
    print(f"  Sequence: {sequence}")
    print(f"  Features: {seq_features[:5]}...")  # Show first 5


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("Machine Learning Integration Examples")
    print("=" * 70)
    print("\nThis script demonstrates ML-based analysis capabilities.")
    
    try:
        example_feature_extraction()
        example_pattern_detection()
        example_anomaly_detection()
        
        if HAS_SKLEARN:
            example_period_prediction()
            example_model_training()
        else:
            print("\n" + "=" * 70)
            print("Note: Some examples require scikit-learn")
            print("Install with: pip install scikit-learn")
        
        print("\n" + "=" * 70)
        print("Examples Complete!")
        print("=" * 70)
        print("\nFor more information, see:")
        print("  - ML Integration Guide: docs/ml_integration.rst")
        print("  - API Documentation: docs/api/ml.rst")
        
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
