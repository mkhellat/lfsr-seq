#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pattern detection in LFSR sequences using ML and statistical methods.

This module provides pattern detection capabilities for identifying
recurring patterns, statistical patterns, and sequence structures.
"""

from typing import Any, Dict, List, Optional, Tuple
from collections import Counter, defaultdict
import math


class PatternDetector:
    """
    Pattern detection in LFSR sequences.
    
    This class provides methods to detect various types of patterns in
    sequences, including recurring patterns, statistical patterns, and
    structural patterns.
    
    **Key Terminology**:
    
    - **Pattern Detection**: Identifying recurring or significant patterns
      in sequences. Patterns can be exact repetitions, statistical
      regularities, or structural features.
    
    - **Recurring Pattern**: A subsequence that appears multiple times
      in the sequence. For example, "101" appearing repeatedly.
    
    - **Statistical Pattern**: A pattern based on statistical properties,
      such as frequency distributions, runs, or correlations.
    
    - **Pattern Classification**: Categorizing detected patterns into types
      (periodic, random, structured, etc.).
    """
    
    def __init__(self, min_pattern_length: int = 2, max_pattern_length: int = 10):
        """
        Initialize pattern detector.
        
        Args:
            min_pattern_length: Minimum pattern length to detect
            max_pattern_length: Maximum pattern length to detect
        """
        self.min_pattern_length = min_pattern_length
        self.max_pattern_length = max_pattern_length
    
    def detect_recurring_patterns(
        self,
        sequence: List[int],
        min_occurrences: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Detect recurring patterns in sequence.
        
        This method finds subsequences that appear multiple times in the
        sequence.
        
        Args:
            sequence: Sequence to analyze
            min_occurrences: Minimum number of occurrences to consider
        
        Returns:
            List of pattern dictionaries with pattern, occurrences, positions
        """
        patterns = []
        sequence_str = ''.join(str(b) for b in sequence)
        
        for pattern_len in range(self.min_pattern_length, 
                                min(self.max_pattern_length + 1, len(sequence) // 2 + 1)):
            pattern_counts = defaultdict(list)
            
            for i in range(len(sequence) - pattern_len + 1):
                pattern = tuple(sequence[i:i+pattern_len])
                pattern_counts[pattern].append(i)
            
            for pattern, positions in pattern_counts.items():
                if len(positions) >= min_occurrences:
                    patterns.append({
                        'pattern': list(pattern),
                        'pattern_string': ''.join(str(b) for b in pattern),
                        'length': pattern_len,
                        'occurrences': len(positions),
                        'positions': positions,
                        'frequency': len(positions) / (len(sequence) - pattern_len + 1)
                    })
        
        # Sort by frequency (descending)
        patterns.sort(key=lambda x: x['frequency'], reverse=True)
        
        return patterns
    
    def detect_periodic_patterns(
        self,
        sequence: List[int],
        max_period: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect periodic patterns in sequence.
        
        This method identifies sequences that repeat with a certain period.
        
        Args:
            sequence: Sequence to analyze
            max_period: Maximum period to check (defaults to len(sequence) // 2)
        
        Returns:
            List of periodic pattern dictionaries
        """
        if max_period is None:
            max_period = len(sequence) // 2
        
        periodic_patterns = []
        
        for period in range(1, min(max_period + 1, len(sequence) // 2 + 1)):
            # Check if sequence repeats with this period
            is_periodic = True
            for i in range(period, len(sequence)):
                if sequence[i] != sequence[i % period]:
                    is_periodic = False
                    break
            
            if is_periodic:
                pattern = sequence[:period]
                periodic_patterns.append({
                    'pattern': pattern,
                    'pattern_string': ''.join(str(b) for b in pattern),
                    'period': period,
                    'repetitions': len(sequence) // period,
                    'type': 'periodic'
                })
        
        return periodic_patterns
    
    def detect_statistical_patterns(
        self,
        sequence: List[int],
        field_order: int = 2
    ) -> Dict[str, Any]:
        """
        Detect statistical patterns in sequence.
        
        This method identifies statistical regularities and anomalies.
        
        Args:
            sequence: Sequence to analyze
            field_order: Field order
        
        Returns:
            Dictionary with statistical pattern information
        """
        if not sequence:
            return {}
        
        patterns = {}
        
        # Frequency distribution
        element_counts = Counter(sequence)
        patterns['frequency_distribution'] = dict(element_counts)
        
        # Balance (for binary)
        if field_order == 2:
            ones = element_counts.get(1, 0)
            zeros = element_counts.get(0, 0)
            total = len(sequence)
            patterns['balance'] = {
                'ones': ones,
                'zeros': zeros,
                'balance_ratio': abs(ones - zeros) / total if total > 0 else 0.0,
                'is_balanced': abs(ones - zeros) <= 1
            }
        
        # Run statistics
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
            patterns['runs'] = {
                'total_runs': len(runs),
                'average_run_length': sum(runs) / len(runs),
                'max_run_length': max(runs),
                'min_run_length': min(runs)
            }
        
        # Entropy
        entropy = 0.0
        for count in element_counts.values():
            p = count / len(sequence)
            if p > 0:
                entropy -= p * math.log2(p)
        patterns['entropy'] = entropy
        patterns['max_entropy'] = math.log2(field_order)
        patterns['entropy_ratio'] = entropy / patterns['max_entropy'] if patterns['max_entropy'] > 0 else 0.0
        
        return patterns
    
    def classify_sequence(
        self,
        sequence: List[int],
        field_order: int = 2
    ) -> Dict[str, Any]:
        """
        Classify sequence based on detected patterns.
        
        This method analyzes the sequence and classifies it into categories
        based on detected patterns.
        
        Args:
            sequence: Sequence to classify
            field_order: Field order
        
        Returns:
            Dictionary with classification results
        """
        classification = {
            'length': len(sequence),
            'field_order': field_order,
            'classification': 'unknown',
            'confidence': 0.0,
            'features': {}
        }
        
        # Detect periodic patterns
        periodic = self.detect_periodic_patterns(sequence)
        if periodic:
            classification['classification'] = 'periodic'
            classification['confidence'] = 1.0
            classification['features']['period'] = periodic[0]['period']
            return classification
        
        # Detect statistical patterns
        statistical = self.detect_statistical_patterns(sequence, field_order)
        classification['features'].update(statistical)
        
        # Classify based on statistics
        if field_order == 2:
            balance = statistical.get('balance', {})
            entropy_ratio = statistical.get('entropy_ratio', 0.0)
            
            if balance.get('is_balanced', False) and entropy_ratio > 0.9:
                classification['classification'] = 'random-like'
                classification['confidence'] = 0.8
            elif entropy_ratio < 0.5:
                classification['classification'] = 'structured'
                classification['confidence'] = 0.7
            else:
                classification['classification'] = 'mixed'
                classification['confidence'] = 0.6
        
        return classification


def detect_patterns(
    sequence: List[int],
    field_order: int = 2,
    min_pattern_length: int = 2,
    max_pattern_length: int = 10
) -> Dict[str, Any]:
    """
    Detect all patterns in sequence.
    
    Convenience function to detect all types of patterns.
    
    Args:
        sequence: Sequence to analyze
        field_order: Field order
        min_pattern_length: Minimum pattern length
        max_pattern_length: Maximum pattern length
    
    Returns:
        Dictionary with all detected patterns
    """
    detector = PatternDetector(min_pattern_length, max_pattern_length)
    
    return {
        'recurring_patterns': detector.detect_recurring_patterns(sequence),
        'periodic_patterns': detector.detect_periodic_patterns(sequence),
        'statistical_patterns': detector.detect_statistical_patterns(sequence, field_order),
        'classification': detector.classify_sequence(sequence, field_order)
    }
