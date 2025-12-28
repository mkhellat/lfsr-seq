#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pattern detection algorithms for LFSR sequences.

This module provides algorithms to detect patterns in sequences and
state transitions, including repeating subsequences, statistical anomalies,
and periodicity indicators.
"""

from typing import Any, Dict, List, Optional, Tuple
from collections import Counter, defaultdict
from dataclasses import dataclass

from lfsr.ml.base import extract_sequence_features

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


@dataclass
class Pattern:
    """
    Detected pattern in a sequence.
    
    Attributes:
        pattern_type: Type of pattern (e.g., 'repeating', 'anomaly')
        pattern_data: Pattern-specific data
        start_position: Start position in sequence
        end_position: End position in sequence
        confidence: Confidence score (0.0 to 1.0)
    """
    pattern_type: str
    pattern_data: Any
    start_position: int
    end_position: int
    confidence: float


def detect_repeating_subsequences(
    sequence: List[int],
    min_length: int = 2,
    max_length: int = 10
) -> List[Pattern]:
    """
    Detect repeating subsequences in a sequence.
    
    This function identifies subsequences that appear multiple times,
    which can indicate periodicity or structure in the sequence.
    
    **Key Terminology**:
    
    - **Repeating Subsequence**: A subsequence that appears multiple times
      in a sequence. For example, in [1, 0, 1, 0, 1, 0], the subsequence
      [1, 0] repeats three times.
    
    - **Periodicity Indicator**: A pattern that suggests the sequence
      has a periodic structure. Repeating subsequences are strong
      periodicity indicators.
    
    Args:
        sequence: Sequence to analyze
        min_length: Minimum subsequence length to consider
        max_length: Maximum subsequence length to consider
    
    Returns:
        List of detected patterns
    """
    patterns = []
    n = len(sequence)
    
    for length in range(min_length, min(max_length + 1, n // 2 + 1)):
        subsequence_counts = defaultdict(list)
        
        # Find all subsequences of this length
        for i in range(n - length + 1):
            subseq = tuple(sequence[i:i+length])
            subsequence_counts[subseq].append(i)
        
        # Find repeating subsequences
        for subseq, positions in subsequence_counts.items():
            if len(positions) > 1:
                # Calculate confidence based on frequency
                frequency = len(positions) / (n - length + 1)
                confidence = min(frequency * 2, 1.0)  # Normalize to [0, 1]
                
                pattern = Pattern(
                    pattern_type='repeating_subsequence',
                    pattern_data=list(subseq),
                    start_position=positions[0],
                    end_position=positions[0] + length - 1,
                    confidence=confidence
                )
                patterns.append(pattern)
    
    # Sort by confidence (highest first)
    patterns.sort(key=lambda p: p.confidence, reverse=True)
    
    return patterns


def detect_statistical_anomalies(
    sequence: List[int],
    window_size: int = 100,
    threshold: float = 2.0
) -> List[Pattern]:
    """
    Detect statistical anomalies in a sequence.
    
    This function identifies windows where statistical properties deviate
    significantly from the overall sequence statistics.
    
    **Key Terminology**:
    
    - **Statistical Anomaly**: A region of a sequence where statistical
      properties (mean, variance, distribution) differ significantly from
      the overall sequence. This can indicate errors or special structure.
    
    - **Z-score**: A measure of how many standard deviations a value is
      from the mean. High z-scores indicate anomalies.
    
    Args:
        sequence: Sequence to analyze
        window_size: Size of sliding window
        threshold: Z-score threshold for anomaly detection
    
    Returns:
        List of detected anomaly patterns
    """
    patterns = []
    n = len(sequence)
    
    if n < window_size:
        return patterns
    
    # Compute overall statistics
    if HAS_NUMPY:
        seq_array = np.array(sequence)
        overall_mean = np.mean(seq_array)
        overall_std = np.std(seq_array) if len(seq_array) > 1 else 1.0
    else:
        overall_mean = sum(sequence) / len(sequence)
        variance = sum((x - overall_mean) ** 2 for x in sequence) / len(sequence)
        overall_std = variance ** 0.5 if variance > 0 else 1.0
    
    if overall_std == 0:
        return patterns  # No variation, no anomalies
    
    # Slide window and detect anomalies
    for i in range(n - window_size + 1):
        window = sequence[i:i+window_size]
        
        if HAS_NUMPY:
            window_array = np.array(window)
            window_mean = np.mean(window_array)
            window_std = np.std(window_array) if len(window_array) > 1 else 0.0
        else:
            window_mean = sum(window) / len(window)
            window_variance = sum((x - window_mean) ** 2 for x in window) / len(window)
            window_std = window_variance ** 0.5 if window_variance > 0 else 0.0
        
        # Calculate z-score for mean deviation
        z_score = abs(window_mean - overall_mean) / overall_std if overall_std > 0 else 0.0
        
        if z_score > threshold:
            confidence = min(z_score / (threshold * 2), 1.0)
            
            pattern = Pattern(
                pattern_type='statistical_anomaly',
                pattern_data={
                    'window_mean': window_mean,
                    'overall_mean': overall_mean,
                    'z_score': z_score
                },
                start_position=i,
                end_position=i + window_size - 1,
                confidence=confidence
            )
            patterns.append(pattern)
    
    return patterns


def detect_periodicity_indicators(
    sequence: List[int],
    max_period: int = 100
) -> List[Pattern]:
    """
    Detect periodicity indicators in a sequence.
    
    This function identifies patterns that suggest the sequence has
    periodic structure.
    
    **Key Terminology**:
    
    - **Periodicity**: The property of a sequence repeating after a
      fixed number of elements. For example, [1, 0, 1, 0, 1, 0] has
      period 2.
    
    - **Autocorrelation**: A measure of how similar a sequence is to
      a shifted version of itself. High autocorrelation at a particular
      lag indicates periodicity.
    
    Args:
        sequence: Sequence to analyze
        max_period: Maximum period to check
    
    Returns:
        List of detected periodicity patterns
    """
    patterns = []
    n = len(sequence)
    
    if n < 2:
        return patterns
    
    # Compute autocorrelation for different lags
    for lag in range(1, min(max_period + 1, n)):
        if lag >= n:
            break
        
        # Compute autocorrelation at this lag
        matches = sum(1 for i in range(n - lag) if sequence[i] == sequence[i + lag])
        autocorr = matches / (n - lag) if (n - lag) > 0 else 0.0
        
        # High autocorrelation suggests periodicity
        if autocorr > 0.7:  # Threshold for periodicity
            confidence = autocorr
            
            pattern = Pattern(
                pattern_type='periodicity_indicator',
                pattern_data={
                    'suggested_period': lag,
                    'autocorrelation': autocorr
                },
                start_position=0,
                end_position=n - 1,
                confidence=confidence
            )
            patterns.append(pattern)
    
    # Sort by confidence
    patterns.sort(key=lambda p: p.confidence, reverse=True)
    
    return patterns


def detect_all_patterns(
    sequence: List[int],
    include_repeating: bool = True,
    include_anomalies: bool = True,
    include_periodicity: bool = True
) -> Dict[str, List[Pattern]]:
    """
    Detect all types of patterns in a sequence.
    
    Convenience function that runs all pattern detection algorithms.
    
    Args:
        sequence: Sequence to analyze
        include_repeating: Whether to detect repeating subsequences
        include_anomalies: Whether to detect statistical anomalies
        include_periodicity: Whether to detect periodicity indicators
    
    Returns:
        Dictionary mapping pattern types to lists of patterns
    """
    results = {}
    
    if include_repeating:
        results['repeating_subsequences'] = detect_repeating_subsequences(sequence)
    
    if include_anomalies:
        results['statistical_anomalies'] = detect_statistical_anomalies(sequence)
    
    if include_periodicity:
        results['periodicity_indicators'] = detect_periodicity_indicators(sequence)
    
    return results
