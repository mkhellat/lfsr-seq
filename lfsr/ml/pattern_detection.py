#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pattern detection in LFSR sequences using machine learning.

This module provides ML-based pattern detection capabilities for identifying
patterns, cycles, and anomalies in LFSR-generated sequences.
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

from lfsr.ml.base import FeatureExtractor

# Try to import scikit-learn, but make it optional
try:
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


class PatternDetector:
    """
    Detect patterns in LFSR sequences.
    
    This class provides methods to detect various patterns in sequences,
    including recurring patterns, cycles, and statistical anomalies.
    
    **Key Terminology**:
    
    - **Pattern Detection**: The process of identifying recurring structures
      or sequences in data. In LFSR sequences, patterns might include
      repeating subsequences, cycles, or statistical regularities.
    
    - **Sequence Pattern**: A recurring subsequence that appears multiple
      times in a sequence. For example, in [0,1,0,1,0,1,...], the pattern
      [0,1] repeats.
    
    - **Cycle Detection**: Identifying when a sequence starts repeating,
      indicating the beginning of a cycle. This is related to period detection.
    
    - **Statistical Pattern**: Regularities in the statistical properties
      of a sequence, such as frequency distributions or autocorrelation.
    """
    
    def __init__(self):
        """Initialize pattern detector."""
        self.scaler = StandardScaler() if HAS_SKLEARN else None
    
    def detect_recurring_patterns(
        self,
        sequence: List[int],
        min_pattern_length: int = 2,
        max_pattern_length: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Detect recurring patterns in sequence.
        
        This method identifies subsequences that repeat multiple times
        in the sequence.
        
        **Key Terminology**:
        
        - **Recurring Pattern**: A subsequence that appears multiple times
          in a sequence. For example, if [0,1,0,1] appears 3 times, it's
          a recurring pattern.
        
        - **Pattern Frequency**: The number of times a pattern appears
          in the sequence.
        
        Args:
            sequence: Sequence to analyze
            min_pattern_length: Minimum pattern length to consider
            max_pattern_length: Maximum pattern length to consider
        
        Returns:
            List of dictionaries with pattern information
        """
        patterns = []
        seq_str = ''.join(str(x) for x in sequence)
        
        for length in range(min_pattern_length, min(max_pattern_length + 1, len(sequence) // 2 + 1)):
            pattern_counts = {}
            
            # Slide window through sequence
            for i in range(len(sequence) - length + 1):
                pattern = tuple(sequence[i:i+length])
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
            
            # Find patterns that appear multiple times
            for pattern, count in pattern_counts.items():
                if count > 1:
                    patterns.append({
                        'pattern': list(pattern),
                        'length': length,
                        'frequency': count,
                        'pattern_str': ''.join(str(x) for x in pattern)
                    })
        
        # Sort by frequency (descending)
        patterns.sort(key=lambda x: x['frequency'], reverse=True)
        
        return patterns
    
    def detect_cycles(
        self,
        sequence: List[int],
        max_cycle_length: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Detect cycles in sequence using Floyd's cycle detection.
        
        This method detects if the sequence contains a cycle and identifies
        the cycle start and length.
        
        **Key Terminology**:
        
        - **Cycle**: A repeating subsequence in a sequence. Once a cycle
          starts, the sequence repeats indefinitely. For LFSRs, the cycle
          length equals the period.
        
        - **Cycle Detection**: Algorithms to identify cycles without
          storing the entire sequence. Floyd's algorithm uses two pointers
          moving at different speeds.
        
        Args:
            sequence: Sequence to analyze
            max_cycle_length: Maximum cycle length to consider (None = no limit)
        
        Returns:
            Dictionary with cycle information, or None if no cycle detected
        """
        if len(sequence) < 2:
            return None
        
        # Floyd's cycle detection
        slow = 0
        fast = 1
        
        # Find meeting point
        while fast < len(sequence) and sequence[slow] != sequence[fast]:
            slow = (slow + 1) % len(sequence)
            fast = (fast + 2) % len(sequence)
        
        if fast >= len(sequence) or sequence[slow] != sequence[fast]:
            return None
        
        # Find cycle start
        slow = 0
        while sequence[slow] != sequence[fast]:
            slow += 1
            fast += 1
            if fast >= len(sequence):
                return None
        
        # Find cycle length
        cycle_start = slow
        cycle_length = 1
        ptr = slow + 1
        
        while ptr < len(sequence) and sequence[ptr] != sequence[cycle_start]:
            cycle_length += 1
            ptr += 1
        
        if ptr >= len(sequence):
            return None
        
        return {
            'has_cycle': True,
            'cycle_start': cycle_start,
            'cycle_length': cycle_length,
            'cycle_pattern': sequence[cycle_start:cycle_start + cycle_length]
        }
    
    def analyze_statistical_patterns(
        self,
        sequence: List[int]
    ) -> Dict[str, Any]:
        """
        Analyze statistical patterns in sequence.
        
        This method computes statistical properties that reveal patterns
        in the sequence distribution.
        
        **Key Terminology**:
        
        - **Statistical Pattern**: Regularities in the distribution or
          statistical properties of sequence values. Examples include
          frequency distributions, autocorrelation, and run lengths.
        
        - **Frequency Distribution**: How often each value appears in
          the sequence. A uniform distribution indicates good randomness.
        
        Args:
            sequence: Sequence to analyze
        
        Returns:
            Dictionary with statistical pattern information
        """
        if not sequence:
            return {}
        
        # Frequency distribution
        freq_dist = Counter(sequence)
        unique_values = len(freq_dist)
        max_freq = max(freq_dist.values()) if freq_dist else 0
        min_freq = min(freq_dist.values()) if freq_dist else 0
        
        # For binary sequences, check balance
        is_binary = all(x in [0, 1] for x in sequence)
        balance = None
        if is_binary:
            ones = freq_dist.get(1, 0)
            zeros = freq_dist.get(0, 0)
            total = len(sequence)
            balance = abs(ones - zeros) / total if total > 0 else 0.0
        
        # Run length statistics
        run_lengths = []
        if len(sequence) > 1:
            current_run = 1
            for i in range(1, len(sequence)):
                if sequence[i] == sequence[i-1]:
                    current_run += 1
                else:
                    run_lengths.append(current_run)
                    current_run = 1
            run_lengths.append(current_run)
        
        avg_run_length = sum(run_lengths) / len(run_lengths) if run_lengths else 0.0
        max_run_length = max(run_lengths) if run_lengths else 0.0
        
        return {
            'unique_values': unique_values,
            'max_frequency': max_freq,
            'min_frequency': min_freq,
            'is_binary': is_binary,
            'balance': balance,
            'average_run_length': avg_run_length,
            'max_run_length': max_run_length,
            'total_runs': len(run_lengths)
        }


def detect_patterns(
    sequence: List[int],
    include_recurring: bool = True,
    include_cycles: bool = True,
    include_statistical: bool = True
) -> Dict[str, Any]:
    """
    Comprehensive pattern detection in sequence.
    
    This function performs multiple types of pattern detection and
    returns comprehensive results.
    
    Args:
        sequence: Sequence to analyze
        include_recurring: Whether to detect recurring patterns
        include_cycles: Whether to detect cycles
        include_statistical: Whether to analyze statistical patterns
    
    Returns:
        Dictionary with all pattern detection results
    """
    detector = PatternDetector()
    results = {}
    
    if include_recurring:
        results['recurring_patterns'] = detector.detect_recurring_patterns(sequence)
    
    if include_cycles:
        results['cycle'] = detector.detect_cycles(sequence)
    
    if include_statistical:
        results['statistical'] = detector.analyze_statistical_patterns(sequence)
    
    return results
