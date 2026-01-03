#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Statistical analysis tools for LFSR sequences.

This module provides statistical tests and analysis functions for
evaluating the quality and randomness properties of LFSR-generated
sequences.
"""

import math
import math
from collections import Counter
from typing import Dict, List, Optional, Tuple, Union

from lfsr.sage_imports import *


def frequency_test(sequence: List[int], gf_order: int) -> Dict[str, float]:
    """
    Perform frequency (monobit) test on a sequence.

    Tests whether the number of zeros and ones in the sequence are
    approximately equal, as expected for a random sequence.

    Args:
        sequence: List of integers representing the sequence
        gf_order: The field order (for binary sequences, use 2)

    Returns:
        Dictionary with test results:
        - 'zeros': Number of zeros
        - 'ones': Number of ones (or non-zeros)
        - 'ratio': Ratio of ones to total length
        - 'expected_ratio': Expected ratio (0.5 for binary)
    """
    n = len(sequence)
    if n == 0:
        return {"error": "Empty sequence"}

    zeros = sum(1 for x in sequence if x == 0)
    ones = n - zeros
    ratio = ones / n if n > 0 else 0.0
    expected_ratio = 1.0 / gf_order

    return {
        "zeros": zeros,
        "ones": ones,
        "total": n,
        "ratio": ratio,
        "expected_ratio": expected_ratio,
        "deviation": abs(ratio - expected_ratio),
    }


def runs_test(sequence: List[int]) -> Dict[str, any]:
    """
    Perform runs test on a binary sequence.

    Tests whether the number of runs (consecutive identical values)
    is consistent with a random sequence.

    Args:
        sequence: List of integers (typically binary: 0s and 1s)

    Returns:
        Dictionary with test results:
        - 'total_runs': Total number of runs
        - 'runs_of_zeros': Number of runs of zeros
        - 'runs_of_ones': Number of runs of ones
        - 'expected_runs': Expected number of runs for random sequence
    """
    if len(sequence) == 0:
        return {"error": "Empty sequence"}

    n = len(sequence)
    runs = 1  # Start with 1 run
    runs_of_zeros = 0
    runs_of_ones = 0

    for i in range(1, n):
        if sequence[i] != sequence[i - 1]:
            runs += 1
            if sequence[i - 1] == 0:
                runs_of_zeros += 1
            else:
                runs_of_ones += 1

    # Count the last run
    if sequence[-1] == 0:
        runs_of_zeros += 1
    else:
        runs_of_ones += 1

    # Expected number of runs for a random sequence
    # E[R] = (2*n0*n1)/(n0+n1) + 1
    zeros = sum(1 for x in sequence if x == 0)
    ones = n - zeros
    if zeros > 0 and ones > 0:
        expected_runs = (2 * zeros * ones) / n + 1
    else:
        expected_runs = 1

    return {
        "total_runs": runs,
        "runs_of_zeros": runs_of_zeros,
        "runs_of_ones": runs_of_ones,
        "expected_runs": expected_runs,
        "deviation": abs(runs - expected_runs),
    }


def autocorrelation(sequence: List[int], lag: int = 1) -> float:
    """
    Calculate autocorrelation of a sequence at a given lag.

    Args:
        sequence: List of integers representing the sequence
        lag: The lag (shift) for autocorrelation calculation

    Returns:
        Autocorrelation value (between -1 and 1)
    """
    n = len(sequence)
    if n <= lag or n == 0:
        return 0.0

    # Convert to binary-like values (-1, 1) for correlation
    seq_binary = [1 if x != 0 else -1 for x in sequence]

    # Calculate mean
    mean = sum(seq_binary) / n

    # Calculate autocorrelation
    numerator = sum((seq_binary[i] - mean) * (seq_binary[i + lag] - mean) for i in range(n - lag))
    denominator = sum((seq_binary[i] - mean) ** 2 for i in range(n))

    if denominator == 0:
        return 0.0

    return numerator / denominator


def periodicity_test(sequence: List[int], max_period: Optional[int] = None) -> Dict[str, any]:
    """
    Test for periodicity in a sequence.

    Checks if the sequence is periodic and finds the period if it exists.

    Args:
        sequence: List of integers representing the sequence
        max_period: Maximum period to check (default: len(sequence) // 2)

    Returns:
        Dictionary with test results:
        - 'is_periodic': Boolean indicating if sequence is periodic
        - 'period': Period if found, None otherwise
        - 'checked_up_to': Maximum period checked
    """
    n = len(sequence)
    if n == 0:
        return {"error": "Empty sequence"}

    if max_period is None:
        max_period = n // 2

    max_period = min(max_period, n // 2)

    for period in range(1, max_period + 1):
        is_periodic = True
        for i in range(n - period):
            if sequence[i] != sequence[i + period]:
                is_periodic = False
                break
        if is_periodic:
            return {
                "is_periodic": True,
                "period": period,
                "checked_up_to": max_period,
            }

    return {
        "is_periodic": False,
        "period": None,
        "checked_up_to": max_period,
    }


def linear_complexity_profile(
    sequence: List[int], gf_order: int, max_length: Optional[int] = None
) -> List[int]:
    """
    Calculate the linear complexity profile of a sequence.

    The linear complexity profile shows how the linear complexity
    evolves as more of the sequence is considered.

    Args:
        sequence: List of integers representing the sequence
        gf_order: The field order
        max_length: Maximum length to consider (default: full sequence)

    Returns:
        List of linear complexities for prefixes of increasing length
    """
    from lfsr.synthesis import linear_complexity

    if max_length is None:
        max_length = len(sequence)

    max_length = min(max_length, len(sequence))
    profile = []

    for length in range(1, max_length + 1):
        prefix = sequence[:length]
        complexity = linear_complexity(prefix, gf_order)
        profile.append(complexity)

    return profile


def statistical_summary(sequence: List[int], gf_order: int) -> Dict[str, any]:
    """
    Generate a comprehensive statistical summary of a sequence.

    Args:
        sequence: List of integers representing the sequence
        gf_order: The field order

    Returns:
        Dictionary containing various statistical measures
    """
    n = len(sequence)
    if n == 0:
        return {"error": "Empty sequence"}

    # Basic statistics
    freq_result = frequency_test(sequence, gf_order)
    runs_result = runs_test(sequence)
    period_result = periodicity_test(sequence)

    # Autocorrelation at lag 1
    autocorr_1 = autocorrelation(sequence, lag=1)

    # Linear complexity
    from lfsr.synthesis import linear_complexity

    complexity = linear_complexity(sequence, gf_order)

    return {
        "length": n,
        "field_order": gf_order,
        "frequency": freq_result,
        "runs": runs_result,
        "periodicity": period_result,
        "autocorrelation_lag_1": autocorr_1,
        "linear_complexity": complexity,
        "complexity_ratio": complexity / n if n > 0 else 0.0,
    }


def compute_period_distribution(
    period_dict: Dict[int, int],
    gf_order: int,
    lfsr_degree: int,
    is_primitive: bool = False,
) -> Dict[str, Union[int, float, Dict[int, int], Dict[str, Union[int, float]]]]:
    """
    Compute statistical distribution of LFSR sequence periods.
    
    This function analyzes the distribution of periods across all sequences
    in an LFSR and compares them with theoretical bounds.
    
    Args:
        period_dict: Dictionary mapping sequence numbers to periods
        gf_order: The Galois field order
        lfsr_degree: The degree of the LFSR (state vector dimension)
        is_primitive: Whether the characteristic polynomial is primitive
        
    Returns:
        Dictionary containing:
        - 'total_sequences': Total number of sequences
        - 'periods': List of all periods
        - 'min_period': Minimum period
        - 'max_period': Maximum period
        - 'mean_period': Mean (average) period
        - 'median_period': Median period
        - 'variance': Variance of periods
        - 'std_deviation': Standard deviation of periods
        - 'period_frequency': Dictionary mapping period values to their
          frequencies
        - 'theoretical_bounds': Dictionary with theoretical expectations
        - 'comparison': Comparison with theoretical bounds
    """
    if not period_dict:
        return {"error": "Empty period dictionary"}
    
    periods = list(period_dict.values())
    total_sequences = len(periods)
    
    if total_sequences == 0:
        return {"error": "No periods found"}
    
    # Basic statistics
    min_period = min(periods)
    max_period = max(periods)
    mean_period = sum(periods) / total_sequences
    
    # Median
    sorted_periods = sorted(periods)
    n = len(sorted_periods)
    if n % 2 == 0:
        median_period = (sorted_periods[n // 2 - 1] + sorted_periods[n // 2]) / 2.0
    else:
        median_period = float(sorted_periods[n // 2])
    
    # Variance and standard deviation
    variance = sum((p - mean_period) ** 2 for p in periods) / total_sequences
    std_deviation = math.sqrt(variance)
    
    # Period frequency histogram
    period_frequency = dict(Counter(periods))
    
    # Theoretical bounds
    state_space_size = int(gf_order) ** lfsr_degree
    max_theoretical_period = state_space_size - 1  # q^d - 1 (excluding zero state)
    
    theoretical_bounds = {
        "max_theoretical_period": max_theoretical_period,
        "state_space_size": state_space_size,
        "is_primitive": is_primitive,
    }
    
    # For primitive polynomials, all non-zero states should have period q^d - 1
    if is_primitive:
        expected_period = max_theoretical_period
        expected_sequences = state_space_size - 1  # All states except zero
    else:
        expected_period = None
        expected_sequences = None
    
    # Comparison with theoretical bounds
    comparison = {
        "max_period_equals_theoretical": max_period == max_theoretical_period,
        "max_period_ratio": max_period / max_theoretical_period if max_theoretical_period > 0 else 0.0,
    }
    
    if is_primitive:
        # For primitive polynomials, check if all periods are maximum
        all_max_period = all(p == max_theoretical_period for p in periods if p > 1)
        comparison["all_periods_maximum"] = all_max_period
        comparison["expected_period"] = expected_period
        comparison["expected_sequences"] = expected_sequences
        comparison["actual_sequences_with_max_period"] = period_frequency.get(max_theoretical_period, 0)
    
    # Period distribution characteristics
    unique_periods = len(period_frequency)
    distribution_info = {
        "unique_periods": unique_periods,
        "period_diversity": unique_periods / total_sequences if total_sequences > 0 else 0.0,
    }
    
    return {
        "total_sequences": total_sequences,
        "periods": periods,
        "min_period": min_period,
        "max_period": max_period,
        "mean_period": mean_period,
        "median_period": median_period,
        "variance": variance,
        "std_deviation": std_deviation,
        "period_frequency": period_frequency,
        "theoretical_bounds": theoretical_bounds,
        "comparison": comparison,
        "distribution_info": distribution_info,
    }

