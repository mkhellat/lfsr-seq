#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Feature extraction for ML models.

This module provides functions to extract features from LFSR polynomials
and sequences for use in machine learning models.
"""

from typing import Any, Dict, List, Optional

import numpy as np

try:
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


def extract_polynomial_features(
    coefficients: List[int],
    field_order: int,
    polynomial: Optional[Any] = None
) -> Dict[str, float]:
    """
    Extract features from polynomial for ML models.
    
    This function extracts numerical features from polynomial coefficients
    and properties that can be used to train ML models for period prediction.
    
    **Key Terminology**:
    
    - **Feature Extraction**: The process of converting raw data (polynomial
      coefficients) into numerical features that machine learning models can
      use. Features should be informative and relevant to the prediction task.
    
    - **Polynomial Features**: Numerical characteristics of polynomials such
      as degree, sparsity, coefficient distribution, etc. These features help
      ML models learn relationships between polynomial structure and period.
    
    - **Feature Vector**: A list of numerical values representing the features
      of a single data point. ML models use feature vectors as input.
    
    **Features Extracted**:
    
    1. **Degree**: Polynomial degree (d)
    2. **Sparsity**: Ratio of non-zero coefficients
    3. **Coefficient Sum**: Sum of all coefficients
    4. **Non-Zero Count**: Number of non-zero coefficients
    5. **Field Order**: Field order (q)
    6. **State Space Size**: q^d
    7. **Theoretical Max Period**: q^d - 1
    
    Args:
        coefficients: List of polynomial coefficients
        field_order: Field order (q)
        polynomial: Optional SageMath polynomial (for additional features)
    
    Returns:
        Dictionary of feature names to values
    """
    degree = len(coefficients)
    non_zero_count = sum(1 for c in coefficients if c != 0)
    sparsity = non_zero_count / degree if degree > 0 else 0.0
    coefficient_sum = sum(coefficients)
    
    state_space_size = int(field_order) ** degree
    theoretical_max_period = state_space_size - 1
    
    features = {
        'degree': float(degree),
        'sparsity': sparsity,
        'coefficient_sum': float(coefficient_sum),
        'non_zero_count': float(non_zero_count),
        'field_order': float(field_order),
        'state_space_size': float(state_space_size),
        'theoretical_max_period': float(theoretical_max_period)
    }
    
    # Additional features if polynomial provided
    if polynomial is not None:
        try:
            # Check if irreducible
            is_irreducible = polynomial.is_irreducible()
            features['is_irreducible'] = 1.0 if is_irreducible else 0.0
            
            # Check if primitive (if possible)
            try:
                from lfsr.polynomial import is_primitive_polynomial
                is_primitive = is_primitive_polynomial(polynomial, field_order)
                features['is_primitive'] = 1.0 if is_primitive else 0.0
            except Exception:
                features['is_primitive'] = 0.0
        except Exception:
            features['is_irreducible'] = 0.0
            features['is_primitive'] = 0.0
    
    return features


def extract_sequence_features(
    sequence: List[int],
    window_size: int = 100
) -> Dict[str, float]:
    """
    Extract features from sequence for pattern detection.
    
    This function extracts statistical and pattern features from LFSR sequences
    for use in pattern detection and anomaly detection models.
    
    **Key Terminology**:
    
    - **Sequence Features**: Numerical characteristics of sequences such as
      frequency distribution, runs, autocorrelation, etc. These features help
      identify patterns and anomalies in sequences.
    
    - **Statistical Features**: Features derived from statistical analysis of
      the sequence, such as mean, variance, entropy, etc.
    
    - **Pattern Features**: Features that capture recurring patterns or
      structures in the sequence.
    
    **Features Extracted**:
    
    1. **Length**: Sequence length
    2. **Mean**: Average value
    3. **Variance**: Variance of values
    4. **Entropy**: Information entropy
    5. **Runs**: Number of runs (consecutive identical values)
    6. **Balance**: Balance between 0s and 1s (for binary)
    
    Args:
        sequence: List of sequence elements
        window_size: Size of window for windowed features
    
    Returns:
        Dictionary of feature names to values
    """
    if not sequence:
        return {}
    
    seq_array = np.array(sequence)
    length = len(sequence)
    
    features = {
        'length': float(length),
        'mean': float(np.mean(seq_array)),
        'variance': float(np.var(seq_array)),
        'std': float(np.std(seq_array))
    }
    
    # Entropy (for binary sequences)
    if set(sequence).issubset({0, 1}):
        ones = sum(sequence)
        zeros = length - ones
        if ones > 0 and zeros > 0:
            p1 = ones / length
            p0 = zeros / length
            entropy = -(p1 * np.log2(p1) + p0 * np.log2(p0))
            features['entropy'] = float(entropy)
            features['balance'] = abs(ones - zeros) / length
        else:
            features['entropy'] = 0.0
            features['balance'] = 1.0
    
    # Runs count
    runs = 1
    for i in range(1, length):
        if sequence[i] != sequence[i-1]:
            runs += 1
    features['runs'] = float(runs)
    features['runs_per_length'] = runs / length if length > 0 else 0.0
    
    return features


def features_to_vector(features: Dict[str, float], feature_order: Optional[List[str]] = None) -> np.ndarray:
    """
    Convert feature dictionary to numpy array.
    
    Args:
        features: Dictionary of feature names to values
        feature_order: Optional list specifying feature order
    
    Returns:
        Numpy array of feature values
    """
    if feature_order is None:
        feature_order = sorted(features.keys())
    
    return np.array([features.get(name, 0.0) for name in feature_order])
