#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Anomaly detection in LFSR sequences and behavior.

This module provides anomaly detection capabilities for identifying
unusual patterns, statistical anomalies, and unexpected behavior.
"""

from typing import Any, Dict, List, Optional, Tuple
import math
from collections import Counter


class AnomalyDetector:
    """
    Anomaly detection in LFSR sequences and behavior.
    
    This class provides methods to detect anomalies in sequences and
    LFSR behavior, including statistical anomalies, unexpected patterns,
    and deviations from expected behavior.
    
    **Key Terminology**:
    
    - **Anomaly Detection**: Identifying data points or patterns that
      deviate significantly from expected behavior. Anomalies may indicate
      errors, attacks, or interesting phenomena.
    
    - **Statistical Anomaly**: A data point that is statistically unusual,
      such as values far from the mean or unexpected frequency distributions.
    
    - **Pattern Anomaly**: An unexpected pattern that doesn't match typical
      sequence structure, such as unusual repetitions or breaks in periodicity.
    
    - **Outlier**: A data point that is significantly different from other
      data points in the dataset.
    """
    
    def __init__(self, threshold: float = 2.0):
        """
        Initialize anomaly detector.
        
        Args:
            threshold: Standard deviation threshold for anomaly detection
        """
        self.threshold = threshold
    
    def detect_statistical_anomalies(
        self,
        sequence: List[int],
        field_order: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Detect statistical anomalies in sequence.
        
        This method identifies elements or subsequences that are
        statistically unusual.
        
        Args:
            sequence: Sequence to analyze
            field_order: Field order
        
        Returns:
            List of anomaly dictionaries
        """
        anomalies = []
        
        if not sequence or len(sequence) < 2:
            return anomalies
        
        # Frequency-based anomalies
        element_counts = Counter(sequence)
        expected_freq = len(sequence) / field_order
        
        for element, count in element_counts.items():
            deviation = abs(count - expected_freq)
            if deviation > self.threshold * math.sqrt(expected_freq):
                anomalies.append({
                    'type': 'frequency_anomaly',
                    'element': element,
                    'observed_count': count,
                    'expected_count': expected_freq,
                    'deviation': deviation,
                    'severity': 'high' if deviation > 2 * self.threshold * math.sqrt(expected_freq) else 'medium'
                })
        
        # Run-based anomalies
        runs = []
        current_run = 1
        for i in range(1, len(sequence)):
            if sequence[i] == sequence[i-1]:
                current_run += 1
            else:
                runs.append(current_run)
                current_run = 1
        runs.append(current_run)
        
        if runs:
            avg_run = sum(runs) / len(runs)
            std_run = math.sqrt(sum((r - avg_run) ** 2 for r in runs) / len(runs)) if len(runs) > 1 else 0.0
            
            for i, run_length in enumerate(runs):
                if run_length > avg_run + self.threshold * std_run:
                    anomalies.append({
                        'type': 'run_anomaly',
                        'position': i,
                        'run_length': run_length,
                        'expected_avg': avg_run,
                        'deviation': run_length - avg_run,
                        'severity': 'high' if run_length > avg_run + 2 * self.threshold * std_run else 'medium'
                    })
        
        return anomalies
    
    def detect_pattern_anomalies(
        self,
        sequence: List[int],
        expected_pattern: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect pattern anomalies in sequence.
        
        This method identifies unexpected patterns or breaks in expected
        patterns.
        
        Args:
            sequence: Sequence to analyze
            expected_pattern: Optional expected pattern to compare against
        
        Returns:
            List of pattern anomaly dictionaries
        """
        anomalies = []
        
        if expected_pattern:
            # Check for breaks in expected pattern
            pattern_len = len(expected_pattern)
            for i in range(len(sequence) - pattern_len + 1):
                subsequence = sequence[i:i+pattern_len]
                if subsequence != expected_pattern:
                    anomalies.append({
                        'type': 'pattern_break',
                        'position': i,
                        'expected': expected_pattern,
                        'observed': subsequence,
                        'severity': 'medium'
                    })
        
        # Detect unexpected long repetitions
        max_repetition = 1
        current_repetition = 1
        repetition_start = 0
        
        for i in range(1, len(sequence)):
            if sequence[i] == sequence[i-1]:
                current_repetition += 1
            else:
                if current_repetition > max_repetition:
                    max_repetition = current_repetition
                    repetition_start = i - current_repetition
                current_repetition = 1
        
        # Check if max repetition is anomalous
        if max_repetition > math.log2(len(sequence)) + 2:  # Heuristic threshold
            anomalies.append({
                'type': 'repetition_anomaly',
                'position': repetition_start,
                'repetition_length': max_repetition,
                'element': sequence[repetition_start] if repetition_start < len(sequence) else None,
                'severity': 'high' if max_repetition > 2 * math.log2(len(sequence)) else 'medium'
            })
        
        return anomalies
    
    def detect_period_anomalies(
        self,
        computed_period: int,
        theoretical_max_period: int,
        is_primitive: bool
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in period computation.
        
        This method identifies unexpected period values that may indicate
        errors or interesting phenomena.
        
        Args:
            computed_period: Computed period
            theoretical_max_period: Theoretical maximum period
            is_primitive: Whether polynomial is primitive
        
        Returns:
            List of period anomaly dictionaries
        """
        anomalies = []
        
        # Check primitive polynomial period
        if is_primitive and computed_period != theoretical_max_period:
            anomalies.append({
                'type': 'primitive_period_anomaly',
                'computed_period': computed_period,
                'expected_period': theoretical_max_period,
                'deviation': abs(computed_period - theoretical_max_period),
                'severity': 'high',
                'description': 'Primitive polynomial should have maximum period'
            })
        
        # Check for unusually low period
        period_ratio = computed_period / theoretical_max_period if theoretical_max_period > 0 else 0.0
        if period_ratio < 0.1 and not is_primitive:
            anomalies.append({
                'type': 'low_period_anomaly',
                'computed_period': computed_period,
                'theoretical_max': theoretical_max_period,
                'ratio': period_ratio,
                'severity': 'medium',
                'description': 'Period is unusually low compared to theoretical maximum'
            })
        
        return anomalies


def detect_anomalies(
    sequence: Optional[List[int]] = None,
    computed_period: Optional[int] = None,
    theoretical_max_period: Optional[int] = None,
    is_primitive: Optional[bool] = None,
    field_order: int = 2,
    threshold: float = 2.0
) -> Dict[str, Any]:
    """
    Detect all types of anomalies.
    
    Convenience function to detect all types of anomalies.
    
    Args:
        sequence: Optional sequence to analyze
        computed_period: Optional computed period
        theoretical_max_period: Optional theoretical maximum period
        is_primitive: Optional primitivity status
        field_order: Field order
        threshold: Anomaly detection threshold
    
    Returns:
        Dictionary with all detected anomalies
    """
    detector = AnomalyDetector(threshold=threshold)
    
    result = {
        'statistical_anomalies': [],
        'pattern_anomalies': [],
        'period_anomalies': []
    }
    
    if sequence:
        result['statistical_anomalies'] = detector.detect_statistical_anomalies(sequence, field_order)
        result['pattern_anomalies'] = detector.detect_pattern_anomalies(sequence)
    
    if computed_period is not None and theoretical_max_period is not None:
        result['period_anomalies'] = detector.detect_period_anomalies(
            computed_period,
            theoretical_max_period,
            is_primitive if is_primitive is not None else False
        )
    
    # Summary
    total_anomalies = (len(result['statistical_anomalies']) +
                      len(result['pattern_anomalies']) +
                      len(result['period_anomalies']))
    
    high_severity = sum(1 for a in (result['statistical_anomalies'] +
                                   result['pattern_anomalies'] +
                                   result['period_anomalies'])
                       if a.get('severity') == 'high')
    
    result['summary'] = {
        'total_anomalies': total_anomalies,
        'high_severity': high_severity,
        'medium_severity': total_anomalies - high_severity,
        'has_anomalies': total_anomalies > 0
    }
    
    return result
