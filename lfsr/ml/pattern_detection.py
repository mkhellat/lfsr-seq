#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pattern detection in LFSR sequences using machine learning.

This module provides ML-based pattern detection algorithms for identifying
patterns, recurring structures, and anomalies in LFSR sequences.
"""

from typing import Any, Dict, List, Optional, Tuple
import warnings

try:
    from sklearn.cluster import KMeans, DBSCAN
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    warnings.warn("scikit-learn not available. Pattern detection will be limited.")

from lfsr.ml.base import FeatureExtractor


class PatternDetector:
    """
    Detect patterns in LFSR sequences using machine learning.
    
    This class provides pattern detection capabilities using clustering
    and classification algorithms to identify recurring patterns in sequences.
    
    **Key Terminology**:
    
    - **Pattern Detection**: Identifying recurring structures or sequences
      of values in LFSR output. Patterns can indicate structure or weaknesses.
    
    - **Clustering**: A machine learning technique that groups similar
      data points together. Used here to identify similar sequence segments.
    
    - **Sequence Segmentation**: Breaking a sequence into smaller segments
      for pattern analysis. This enables detection of local patterns.
    
    - **Pattern Classification**: Categorizing detected patterns into
      types (periodic, random, structured, etc.).
    """
    
    def __init__(self, method: str = "kmeans"):
        """
        Initialize pattern detector.
        
        Args:
            method: Detection method ("kmeans" or "dbscan")
        """
        self.method = method
        self.scaler = StandardScaler() if HAS_SKLEARN else None
        self.model: Any = None
    
    def detect_patterns(
        self,
        sequence: List[int],
        window_size: int = 10,
        n_patterns: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Detect patterns in sequence.
        
        This function analyzes a sequence to identify recurring patterns
        using sliding windows and clustering.
        
        Args:
            sequence: Sequence to analyze
            window_size: Size of sliding window
            n_patterns: Number of patterns to identify
        
        Returns:
            List of detected patterns with metadata
        """
        if not HAS_SKLEARN:
            return self._simple_pattern_detection(sequence, window_size)
        
        if len(sequence) < window_size:
            return []
        
        # Extract windows
        windows = []
        for i in range(len(sequence) - window_size + 1):
            window = sequence[i:i+window_size]
            windows.append(window)
        
        # Scale features
        windows_scaled = self.scaler.fit_transform(windows)
        
        # Cluster
        if self.method == "kmeans":
            self.model = KMeans(n_clusters=n_patterns, random_state=42, n_init=10)
            clusters = self.model.fit_predict(windows_scaled)
        elif self.method == "dbscan":
            self.model = DBSCAN(eps=0.5, min_samples=2)
            clusters = self.model.fit_predict(windows_scaled)
        else:
            raise ValueError(f"Unknown method: {self.method}")
        
        # Analyze clusters
        patterns = []
        for cluster_id in set(clusters):
            if cluster_id == -1:  # Noise in DBSCAN
                continue
            
            cluster_windows = [windows[i] for i, c in enumerate(clusters) if c == cluster_id]
            if not cluster_windows:
                continue
            
            # Compute representative pattern (mean)
            pattern = [
                sum(w[i] for w in cluster_windows) / len(cluster_windows)
                for i in range(window_size)
            ]
            
            patterns.append({
                'pattern_id': cluster_id,
                'pattern': pattern,
                'frequency': len(cluster_windows),
                'window_size': window_size
            })
        
        return sorted(patterns, key=lambda p: p['frequency'], reverse=True)
    
    def _simple_pattern_detection(
        self,
        sequence: List[int],
        window_size: int
    ) -> List[Dict[str, Any]]:
        """
        Simple pattern detection without ML (fallback).
        
        Detects exact repeating patterns.
        """
        patterns = []
        seen = {}
        
        for i in range(len(sequence) - window_size + 1):
            window = tuple(sequence[i:i+window_size])
            if window in seen:
                seen[window].append(i)
            else:
                seen[window] = [i]
        
        # Find repeating patterns
        for window, positions in seen.items():
            if len(positions) > 1:
                patterns.append({
                    'pattern_id': len(patterns),
                    'pattern': list(window),
                    'frequency': len(positions),
                    'window_size': window_size,
                    'positions': positions[:5]  # First 5 occurrences
                })
        
        return sorted(patterns, key=lambda p: p['frequency'], reverse=True)


def detect_patterns(
    sequence: List[int],
    window_size: int = 10,
    method: str = "kmeans",
    n_patterns: int = 5
) -> List[Dict[str, Any]]:
    """
    Detect patterns in sequence.
    
    Convenience function for pattern detection.
    
    Args:
        sequence: Sequence to analyze
        window_size: Size of sliding window
        method: Detection method
        n_patterns: Number of patterns to identify
    
    Returns:
        List of detected patterns
    """
    detector = PatternDetector(method=method)
    return detector.detect_patterns(sequence, window_size, n_patterns)
