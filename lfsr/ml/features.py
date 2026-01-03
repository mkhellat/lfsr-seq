#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Feature extraction for machine learning models.

This module provides functions to extract features from LFSR polynomials
and sequences for use in machine learning models.
"""

from typing import Any, Dict, List, Optional
import math

from lfsr.sage_imports import *


def extract_polynomial_features(
    polynomial: Any,
    coefficients: List[int],
    field_order: int,
    degree: Optional[int] = None
) -> Dict[str, float]:
    """
    Extract features from polynomial for ML models.
    
    This function extracts numerical features from a polynomial that can be
    used as input to machine learning models for period prediction and other
    tasks.
    
    **Key Terminology**:
    
    - **Feature Extraction**: The process of converting raw data (polynomials,
      sequences) into numerical features that machine learning models can use.
      Features should capture relevant properties of the data.
    
    - **Polynomial Features**: Numerical properties of polynomials, such as
      degree, number of non-zero coefficients, sparsity, etc. These features
      help ML models learn relationships between polynomial structure and
      period.
    
    - **Feature Vector**: A list of numerical values representing the features
      of a data point. ML models take feature vectors as input.
    
    **Features Extracted**:
    
    1. **Degree**: Polynomial degree (d)
    2. **Field Order**: Field order (q)
    3. **Coefficient Count**: Number of non-zero coefficients
    4. **Sparsity**: Ratio of non-zero to total coefficients
    5. **Coefficient Sum**: Sum of all coefficients
    6. **Coefficient Variance**: Variance of coefficients
    7. **Leading Coefficient**: Value of leading coefficient
    8. **Constant Term**: Value of constant term
    9. **Theoretical Maximum Period**: q^d - 1
    
    Args:
        polynomial: SageMath polynomial
        coefficients: List of polynomial coefficients
        field_order: Field order (q)
        degree: Optional polynomial degree (defaults to polynomial.degree())
    
    Returns:
        Dictionary mapping feature names to numerical values
    """
    if degree is None:
        degree = polynomial.degree()
    
    # Basic properties
    features = {
        'degree': float(degree),
        'field_order': float(field_order),
        'theoretical_max_period': float(field_order ** degree - 1)
    }
    
    # Coefficient statistics
    non_zero_count = sum(1 for c in coefficients if c != 0)
    total_coeffs = len(coefficients)
    sparsity = non_zero_count / total_coeffs if total_coeffs > 0 else 0.0
    
    features['coefficient_count'] = float(non_zero_count)
    features['sparsity'] = sparsity
    features['coefficient_sum'] = float(sum(coefficients))
    
    # Coefficient variance
    if total_coeffs > 1:
        mean_coeff = sum(coefficients) / total_coeffs
        variance = sum((c - mean_coeff) ** 2 for c in coefficients) / total_coeffs
        features['coefficient_variance'] = variance
    else:
        features['coefficient_variance'] = 0.0
    
    # Leading and constant terms
    features['leading_coefficient'] = float(coefficients[0] if coefficients else 0)
    features['constant_term'] = float(coefficients[-1] if coefficients else 0)
    
    # Polynomial properties
    try:
        is_irreducible = polynomial.is_irreducible()
        features['is_irreducible'] = 1.0 if is_irreducible else 0.0
    except (AttributeError, NotImplementedError):
        features['is_irreducible'] = 0.0
    
    # Try primitive check (may fail for some polynomials)
    try:
        from lfsr.polynomial import is_primitive_polynomial
        is_primitive = is_primitive_polynomial(polynomial, field_order)
        features['is_primitive'] = 1.0 if is_primitive else 0.0
    except (TypeError, ValueError, AttributeError):
        features['is_primitive'] = 0.0
    
    return features


def extract_sequence_features(
    sequence: List[int],
    field_order: int = 2
) -> Dict[str, float]:
    """
    Extract features from sequence for ML models.
    
    This function extracts numerical features from a sequence that can be
    used for pattern detection and anomaly detection.
    
    **Key Terminology**:
    
    - **Sequence Features**: Numerical properties of sequences, such as
      frequency distribution, runs, autocorrelation, etc. These features
      help ML models detect patterns and anomalies.
    
    - **Statistical Features**: Features based on statistical properties
      of the sequence, such as mean, variance, entropy, etc.
    
    Args:
        sequence: Sequence of field elements
        field_order: Field order (q)
    
    Returns:
        Dictionary mapping feature names to numerical values
    """
    if not sequence:
        return {}
    
    length = len(sequence)
    features = {
        'length': float(length),
        'field_order': float(field_order)
    }
    
    # Frequency distribution
    element_counts = {}
    for element in sequence:
        element_counts[element] = element_counts.get(element, 0) + 1
    
    # Frequency features
    max_freq = max(element_counts.values()) if element_counts else 0
    min_freq = min(element_counts.values()) if element_counts else 0
    features['max_frequency'] = float(max_freq)
    features['min_frequency'] = float(min_freq)
    features['frequency_range'] = float(max_freq - min_freq)
    
    # Balance (for binary sequences)
    if field_order == 2:
        ones = element_counts.get(1, 0)
        zeros = element_counts.get(0, 0)
        balance = abs(ones - zeros) / length if length > 0 else 0.0
        features['balance'] = balance
        features['ones_ratio'] = ones / length if length > 0 else 0.0
    
    # Runs (consecutive identical elements)
    runs = 1
    for i in range(1, length):
        if sequence[i] != sequence[i-1]:
            runs += 1
    features['runs'] = float(runs)
    features['average_run_length'] = length / runs if runs > 0 else 0.0
    
    # Entropy (Shannon entropy)
    entropy = 0.0
    for count in element_counts.values():
        if count > 0:
            p = count / length
            entropy -= p * math.log2(p)
    features['entropy'] = entropy
    
    # Autocorrelation (simple first-order)
    if length > 1:
        autocorr = sum(1 for i in range(length - 1) if sequence[i] == sequence[i+1])
        features['autocorrelation'] = autocorr / (length - 1) if length > 1 else 0.0
    else:
        features['autocorrelation'] = 0.0
    
    return features


def get_feature_vector(features: Dict[str, float], feature_names: Optional[List[str]] = None) -> List[float]:
    """
    Convert feature dictionary to feature vector.
    
    This function converts a feature dictionary into a list of numerical
    values in a consistent order for ML models.
    
    Args:
        features: Dictionary of features
        feature_names: Optional list of feature names in desired order
                      (defaults to sorted keys)
    
    Returns:
        List of feature values
    """
    if feature_names is None:
        feature_names = sorted(features.keys())
    
    return [features.get(name, 0.0) for name in feature_names]
