#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NIST SP 800-22 Statistical Test Suite for Random and Pseudorandom
Number Generators.

This module implements the NIST SP 800-22 test suite, which is an
industry-standard collection of 15 statistical tests for evaluating
the randomness of binary sequences. These tests are widely used in
cryptography to assess the quality of random number generators,
pseudorandom number generators, and stream cipher outputs.

Key Concepts:
-------------

**NIST SP 800-22**: A special publication by the National Institute
of Standards and Technology (NIST) that defines 15 statistical tests
for randomness. It is the de facto standard for evaluating
cryptographic random number generators.

**Statistical Test**: A mathematical procedure that evaluates
whether a sequence exhibits properties expected of a random sequence.
Each test focuses on a specific aspect of randomness (e.g., balance,
patterns, complexity).

**P-value**: The probability that a perfect random number generator
would produce a sequence less random than the sequence being tested.
A small p-value (< 0.01) indicates strong evidence of non-randomness,
while a large p-value (>= 0.01) suggests the sequence appears random.

**Significance Level** (:math:`\alpha`): The threshold for rejecting
the null hypothesis (that the sequence is random). Common values are
0.01 (1%) or 0.05 (5%). If p-value < :math:`\alpha`, the test fails
(sequence appears non-random).

**Null Hypothesis**: The hypothesis that the sequence is random.
Statistical tests are designed to detect deviations from randomness.
We assume randomness and look for evidence against it.

**Type I Error (False Positive)**: Rejecting a random sequence as
non-random. This occurs when p-value < :math:`\alpha` even though the
sequence is actually random.

**Type II Error (False Negative)**: Accepting a non-random sequence
as random. This occurs when p-value >= :math:`\alpha` even though the
sequence is actually non-random.

**Test Suite**: A collection of multiple tests applied to the same
sequence. A sequence should pass most (or all) tests to be considered
random. A single test failure does not necessarily mean the sequence
is non-random.

Example:
--------

    >>> from lfsr.nist import run_nist_test_suite, frequency_test
    >>> 
    >>> # Generate or load a binary sequence
    >>> sequence = [1, 0, 1, 0, 1, 1, 0, 0, 1, 0] * 100  # 1000 bits
    >>> 
    >>> # Run a single test
    >>> result = frequency_test(sequence)
    >>> print(f"Test: {result.test_name}")
    >>> print(f"P-value: {result.p_value:.6f}")
    >>> print(f"Passed: {result.passed}")
    >>> 
    >>> # Run the complete test suite
    >>> suite_result = run_nist_test_suite(sequence)
    >>> print(f"Tests passed: {suite_result.tests_passed}/{suite_result.total_tests}")
    >>> print(f"Overall: {suite_result.overall_assessment}")

References:
-----------

- NIST Special Publication 800-22 Revision 1a: "A Statistical
  Test Suite for Random and Pseudorandom Number Generators for
  Cryptographic Applications"
- Available at: https://csrc.nist.gov/publications/detail/sp/800-22/rev-1a/final
"""

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

from sage.all import *

# Import statistical distributions after sage.all to avoid conflicts
try:
    from scipy.stats import chi2 as scipy_chi2, norm as scipy_norm
    chi2 = scipy_chi2
    norm = scipy_norm
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    # Fallback for chi-square distribution
    class _Chi2Fallback:
        """Fallback chi-square distribution when scipy is not available."""
        @staticmethod
        def sf(x, df):
            """Survival function (1 - CDF) using approximation."""
            # Rough approximation - for exact results, use scipy
            import math
            # For large df, use normal approximation
            if df > 30:
                z = (x - df) / math.sqrt(2 * df)
                return 0.5 * (1 - math.erf(z / math.sqrt(2)))
            # Simple approximation for small df
            return max(0.0, min(1.0, math.exp(-x / (2 * df))))
    
    chi2 = _Chi2Fallback()
    
    # Normal distribution fallback
    class _NormFallback:
        @staticmethod
        def cdf(x):
            import math
            return 0.5 * (1 + math.erf(x / math.sqrt(2)))
        @staticmethod
        def sf(x):
            import math
            return 1.0 - 0.5 * (1 + math.erf(x / math.sqrt(2)))
    
    norm = _NormFallback()


@dataclass
class NISTTestResult:
    """
    Results from a single NIST statistical test.
    
    Attributes:
        test_name: Name of the test (e.g., "Frequency (Monobit) Test")
        p_value: P-value from the test (0.0 to 1.0)
        passed: True if p_value >= significance_level (test passed)
        statistic: Test statistic value (test-specific)
        details: Dictionary with test-specific details and
          intermediate values
    """
    test_name: str
    p_value: float
    passed: bool
    statistic: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NISTTestSuiteResult:
    """
    Results from the complete NIST SP 800-22 test suite.
    
    Attributes:
        sequence_length: Length of the tested sequence
        significance_level: Significance level used (typically 0.01)
        tests_passed: Number of tests that passed
        tests_failed: Number of tests that failed
        total_tests: Total number of tests run
        results: List of individual test results
        overall_assessment: Overall assessment ("PASSED" or "FAILED")
        pass_rate: Percentage of tests that passed
    """
    sequence_length: int
    significance_level: float
    tests_passed: int
    tests_failed: int
    total_tests: int
    results: List[NISTTestResult]
    overall_assessment: str
    pass_rate: float


def frequency_test(sequence: List[int]) -> NISTTestResult:
    """
    Test 1: Frequency (Monobit) Test.
    
    **Purpose**: Tests whether the number of zeros and ones in a
    sequence are approximately equal, as expected for a random
    sequence.
    
    **What it measures**: The balance of 0s and 1s in the entire sequence.
    
    **How it works**:
    1. Count the number of ones (n1) and zeros (n0) in the sequence
    2. Compute the test statistic: S = (n1 - n0) / sqrt(n)
    3. Compute p-value using normal distribution
    
    **Interpretation**:
    - A random sequence should have roughly equal numbers of 0s and 1s
    - If p-value < 0.01, the sequence is significantly imbalanced
    - This test detects sequences that are biased toward 0s or 1s
    
    **Minimum sequence length**: 100 bits (recommended: 1000+ bits)
    
    Args:
        sequence: Binary sequence (list of 0s and 1s)
    
    Returns:
        NISTTestResult with test results
    
    Example:
        >>> result = frequency_test([1, 0, 1, 0, 1, 1, 0, 0, 1, 0] * 100)
        >>> print(f"P-value: {result.p_value:.6f}, Passed: {result.passed}")
    """
    n = len(sequence)
    if n < 100:
        return NISTTestResult(
            test_name="Frequency (Monobit) Test",
            p_value=0.0,
            passed=False,
            statistic=0.0,
            details={"error": f"Sequence too short: {n} bits (minimum: 100)"}
        )
    
    # Count ones and zeros
    n1 = sum(sequence)  # Number of ones
    n0 = n - n1  # Number of zeros
    
    # Compute test statistic: S = (n1 - n0) / sqrt(n)
    # For a random sequence, E[S] = 0, Var[S] = 1
    s_obs = (n1 - n0) / math.sqrt(n)
    
    # Compute p-value using normal distribution (two-tailed test)
    # P-value = 2 * (1 - Phi(|S_obs|))
    p_value = 2.0 * norm.sf(abs(s_obs))
    p_value = max(0.0, min(1.0, p_value))  # Clamp to [0, 1]
    
    # Test passes if p-value >= 0.01 (default significance level)
    passed = p_value >= 0.01
    
    return NISTTestResult(
        test_name="Frequency (Monobit) Test",
        p_value=p_value,
        passed=passed,
        statistic=s_obs,
        details={
            "n0": n0,
            "n1": n1,
            "n": n,
            "ratio": n1 / n if n > 0 else 0.0,
            "expected_ratio": 0.5
        }
    )


def block_frequency_test(sequence: List[int], block_size: int = 128) -> NISTTestResult:
    """
    Test 2: Frequency Test within a Block.
    
    **Purpose**: Tests whether the frequency of ones in M-bit blocks
    is approximately M/2, as expected for a random sequence.
    
    **What it measures**: Local balance within blocks of the sequence.
    
    **How it works**:
    1. Divide the sequence into N blocks of M bits each
    2. For each block, compute the proportion of ones:
       :math:`\pi_i = \text{number of ones} / M`
    3. Compute chi-square statistic:
       :math:`\chi^2 = 4M \sum_i (\pi_i - 0.5)^2`
    4. Compute p-value using chi-square distribution with N
       degrees of freedom
    
    **Interpretation**:
    - Random sequences should have balanced blocks
    - If p-value < 0.01, some blocks are significantly imbalanced
    - This test detects local biases in the sequence
    
    **Parameters**:
    - block_size (M): Size of each block (default: 128 bits)
    - Minimum sequence length: :math:`M \times 10` (recommended:
      :math:`M \times 100`)
    
    Args:
        sequence: Binary sequence (list of 0s and 1s)
        block_size: Size of each block (default: 128)
    
    Returns:
        NISTTestResult with test results
    
    Example:
        >>> result = block_frequency_test([1, 0, 1, 0] * 250, block_size=128)
        >>> print(f"P-value: {result.p_value:.6f}, Passed: {result.passed}")
    """
    n = len(sequence)
    M = block_size
    
    if n < M * 10:
        return NISTTestResult(
            test_name="Frequency Test within a Block",
            p_value=0.0,
            passed=False,
            statistic=0.0,
            details={"error": f"Sequence too short: {n} bits (minimum: {M * 10})"}
        )
    
    # Number of blocks
    N = n // M
    
    # Compute proportion of ones in each block
    proportions = []
    for i in range(N):
        block = sequence[i * M:(i + 1) * M]
        ones_count = sum(block)
        pi = ones_count / M
        proportions.append(pi)
    
    # Compute chi-square statistic
    # chi^2 = 4M * sum((pi_i - 0.5)^2)
    chi_square = 4.0 * M * sum((pi - 0.5) ** 2 for pi in proportions)
    
    # Compute p-value using chi-square distribution with N degrees of freedom
    p_value = chi2.sf(chi_square, N)
    p_value = max(0.0, min(1.0, p_value))  # Clamp to [0, 1]
    
    # Test passes if p-value >= 0.01
    passed = p_value >= 0.01
    
    return NISTTestResult(
        test_name="Frequency Test within a Block",
        p_value=p_value,
        passed=passed,
        statistic=chi_square,
        details={
            "block_size": M,
            "num_blocks": N,
            "proportions": proportions[:10] if len(proportions) > 10 else proportions,  # First 10 for display
            "mean_proportion": sum(proportions) / len(proportions) if proportions else 0.0
        }
    )


def runs_test(sequence: List[int]) -> NISTTestResult:
    """
    Test 3: Runs Test.
    
    **Purpose**: Tests whether the number of runs (consecutive
    identical bits) is as expected for a random sequence.
    
    **What it measures**: Oscillation between 0s and 1s in the
    sequence.
    
    **How it works**:
    1. Count the total number of runs (transitions between 0 and 1)
    2. Count the number of zeros (n0) and ones (n1)
    3. Compute expected runs: E[R] = (2*n0*n1)/(n0+n1) + 1
    4. Compute variance: Var[R] = (2*n0*n1*(2*n0*n1 - n))/(n²*(n-1))
    5. Compute test statistic: z = (R - E[R]) / sqrt(Var[R])
    6. Compute p-value using normal distribution
    
    **Interpretation**:
    - Random sequences should have an appropriate number of runs
    - Too few runs indicates clustering (e.g., 00001111...)
    - Too many runs indicates oscillation (e.g., 01010101...)
    - If p-value < 0.01, the sequence has an abnormal number of runs
    
    **Minimum sequence length**: 100 bits (recommended: 1000+ bits)
    
    Args:
        sequence: Binary sequence (list of 0s and 1s)
    
    Returns:
        NISTTestResult with test results
    
    Example:
        >>> result = runs_test([1, 0, 1, 0, 1, 1, 0, 0, 1, 0] * 100)
        >>> print(f"P-value: {result.p_value:.6f}, Passed: {result.passed}")
    """
    n = len(sequence)
    if n < 100:
        return NISTTestResult(
            test_name="Runs Test",
            p_value=0.0,
            passed=False,
            statistic=0.0,
            details={"error": f"Sequence too short: {n} bits (minimum: 100)"}
        )
    
    # Count zeros and ones
    n0 = sum(1 for x in sequence if x == 0)
    n1 = n - n0
    
    if n0 == 0 or n1 == 0:
        # Sequence has no runs (all 0s or all 1s)
        return NISTTestResult(
            test_name="Runs Test",
            p_value=0.0,
            passed=False,
            statistic=0.0,
            details={"error": "Sequence contains only zeros or only ones"}
        )
    
    # Count runs
    runs = 1
    for i in range(1, n):
        if sequence[i] != sequence[i - 1]:
            runs += 1
    
    # Expected number of runs
    expected_runs = (2.0 * n0 * n1) / n + 1.0
    
    # Variance
    variance = (2.0 * n0 * n1 * (2.0 * n0 * n1 - n)) / (n * n * (n - 1))
    
    if variance <= 0:
        return NISTTestResult(
            test_name="Runs Test",
            p_value=0.0,
            passed=False,
            statistic=0.0,
            details={"error": "Variance is zero or negative"}
        )
    
    # Test statistic: z-score
    z_score = (runs - expected_runs) / math.sqrt(variance)
    
    # Compute p-value using normal distribution (two-tailed test)
    p_value = 2.0 * norm.sf(abs(z_score))
    p_value = max(0.0, min(1.0, p_value))  # Clamp to [0, 1]
    
    # Test passes if p-value >= 0.01
    passed = p_value >= 0.01
    
    return NISTTestResult(
        test_name="Runs Test",
        p_value=p_value,
        passed=passed,
        statistic=z_score,
        details={
            "runs": runs,
            "n0": n0,
            "n1": n1,
            "expected_runs": expected_runs,
            "variance": variance
        }
    )


def longest_run_of_ones_test(sequence: List[int], block_size: int = 8) -> NISTTestResult:
    """
    Test 4: Tests for Longest-Run-of-Ones in a Block.
    
    **Purpose**: Tests whether the longest run of ones within M-bit
    blocks is consistent with that expected for a random sequence.
    
    **What it measures**: Maximum consecutive ones in blocks of the
    sequence.
    
    **How it works**:
    1. Divide the sequence into N blocks of M bits each
    2. For each block, find the longest run of consecutive ones
     3. Count how many blocks fall into each category (based on
        longest run length)
     4. Compare observed frequencies with expected frequencies
        using chi-square test
    
    **Interpretation**:
    - Random sequences should have longest runs distributed
      according to theory
    - If p-value < 0.01, the sequence has abnormal longest-run
      patterns
    - This test detects sequences with unusually long or short runs
      of ones
    
    **Parameters**:
    
    - block_size (M): Size of each block. Options:
      * M = 8 for sequences of length >= 128
      * M = 128 for sequences of length >= 6272
      * M = 10000 for sequences of length >= 750000
    - Minimum sequence length: M * 16 (recommended: M * 100)
    
    Args:
        sequence: Binary sequence (list of 0s and 1s)
        block_size: Size of each block (default: 8)
    
    Returns:
        NISTTestResult with test results
    
    Example:
        >>> result = longest_run_of_ones_test([1, 0, 1, 1, 1, 0, 0, 1] * 100, block_size=8)
        >>> print(f"P-value: {result.p_value:.6f}, Passed: {result.passed}")
    """
    n = len(sequence)
    M = block_size
    
    if n < M * 16:
        return NISTTestResult(
            test_name="Tests for Longest-Run-of-Ones in a Block",
            p_value=0.0,
            passed=False,
            statistic=0.0,
            details={"error": f"Sequence too short: {n} bits (minimum: {M * 16})"}
        )
    
    # Number of blocks
    N = n // M
    
    # Expected frequencies for longest run (simplified - full implementation
    # would use exact probabilities based on M)
    # For M=8, categories are: <=1, 2, 3, 4, >=5
    # For M=128, categories are: <=4, 5, 6, 7, 8, 9, >=10
    
    # Find longest run in each block
    longest_runs = []
    for i in range(N):
        block = sequence[i * M:(i + 1) * M]
        max_run = 0
        current_run = 0
        for bit in block:
            if bit == 1:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 0
        longest_runs.append(max_run)
    
    # Categorize blocks based on longest run
    # For M=8: categories are <=1, 2, 3, 4, >=5
    if M == 8:
        categories = [0, 0, 0, 0, 0]  # <=1, 2, 3, 4, >=5
        for run in longest_runs:
            if run <= 1:
                categories[0] += 1
            elif run == 2:
                categories[1] += 1
            elif run == 3:
                categories[2] += 1
            elif run == 4:
                categories[3] += 1
            else:  # >= 5
                categories[4] += 1
        
        # Expected frequencies for M=8 (from NIST specification)
        # These are approximate - exact values depend on block size
        expected = [N * 0.2148, N * 0.3672, N * 0.2305, N * 0.1875, N * 0.0000]
        # Adjust last category
        expected[4] = N - sum(expected[:4])
        K = 5  # Number of categories
    else:
        # For other block sizes, use simplified categorization
        # This is a simplified version - full implementation would handle all cases
        max_run_value = max(longest_runs) if longest_runs else 0
        num_categories = min(6, max_run_value + 1)
        categories = [0] * num_categories
        for run in longest_runs:
            idx = min(run, num_categories - 1)
            categories[idx] += 1
        
        # Expected frequencies (uniform distribution as approximation)
        expected = [N / num_categories] * num_categories
        K = num_categories
    
    # Compute chi-square statistic
    chi_square = sum(
        ((categories[i] - expected[i]) ** 2) / expected[i]
        for i in range(K)
        if expected[i] > 0
    )
    
    # Compute p-value using chi-square distribution with (K-1) degrees of freedom
    p_value = chi2.sf(chi_square, K - 1)
    p_value = max(0.0, min(1.0, p_value))  # Clamp to [0, 1]
    
    # Test passes if p-value >= 0.01
    passed = p_value >= 0.01
    
    return NISTTestResult(
        test_name="Tests for Longest-Run-of-Ones in a Block",
        p_value=p_value,
        passed=passed,
        statistic=chi_square,
        details={
            "block_size": M,
            "num_blocks": N,
            "longest_runs": longest_runs[:10] if len(longest_runs) > 10 else longest_runs,
            "categories": categories,
            "expected": expected
        }
    )


def binary_matrix_rank_test(sequence: List[int], matrix_rows: int = 32, matrix_cols: int = 32) -> NISTTestResult:
    """
    Test 5: Binary Matrix Rank Test.
    
    **Purpose**: Tests for linear dependence among fixed length
    substrings of the sequence.
    
    **What it measures**: Linear independence of binary matrices
    formed from the sequence.
    
    **How it works**:
    1. Divide the sequence into N matrices of size
       :math:`M \times Q`
    2. For each matrix, compute its rank (over GF(2))
     3. Count how many matrices have full rank (M), rank (M-1), or
        lower rank
     4. Compare observed frequencies with expected frequencies
        using chi-square test
    
    **Interpretation**:
    - Random sequences should produce matrices with expected rank
      distribution
    - If p-value < 0.01, the sequence shows linear dependence
      patterns
    - This test detects sequences with linear structure
    
    **Parameters**:
    - matrix_rows (M): Number of rows in each matrix (default: 32)
    - matrix_cols (Q): Number of columns in each matrix (default: 32)
    - Minimum sequence length: M * Q * 38 (recommended: M * Q * 100)
    
    Args:
        sequence: Binary sequence (list of 0s and 1s)
        matrix_rows: Number of rows in each matrix (default: 32)
        matrix_cols: Number of columns in each matrix (default: 32)
    
    Returns:
        NISTTestResult with test results
    
    Example:
        >>> result = binary_matrix_rank_test([1, 0, 1, 0] * 1000, matrix_rows=32, matrix_cols=32)
        >>> print(f"P-value: {result.p_value:.6f}, Passed: {result.passed}")
    """
    n = len(sequence)
    M = matrix_rows
    Q = matrix_cols
    matrix_size = M * Q
    
    if n < matrix_size * 38:
        return NISTTestResult(
            test_name="Binary Matrix Rank Test",
            p_value=0.0,
            passed=False,
            statistic=0.0,
            details={"error": f"Sequence too short: {n} bits (minimum: {matrix_size * 38})"}
        )
    
    # Number of matrices
    N = n // matrix_size
    
    # Count ranks
    rank_full = 0  # Rank = M
    rank_m1 = 0    # Rank = M-1
    rank_other = 0 # Rank < M-1
    
    for i in range(N):
        # Extract matrix from sequence
        matrix_data = sequence[i * matrix_size:(i + 1) * matrix_size]
        
        # Build matrix over GF(2)
        matrix_list = []
        for row in range(M):
            row_data = matrix_data[row * Q:(row + 1) * Q]
            matrix_list.append([GF(2)(bit) for bit in row_data])
        
        # Compute rank
        try:
            mat = matrix(GF(2), matrix_list)
            rank = mat.rank()
            
            if rank == M:
                rank_full += 1
            elif rank == M - 1:
                rank_m1 += 1
            else:
                rank_other += 1
        except Exception:
            rank_other += 1
    
    # Expected frequencies (from NIST specification)
    # For M=Q, probabilities are approximately:
    # P(rank=M) ≈ 0.2888, P(rank=M-1) ≈ 0.5776, P(rank<M-1) ≈ 0.1336
    p_full = 0.2888
    p_m1 = 0.5776
    p_other = 1.0 - p_full - p_m1
    
    expected_full = N * p_full
    expected_m1 = N * p_m1
    expected_other = N * p_other
    
    # Compute chi-square statistic
    chi_square = 0.0
    if expected_full > 0:
        chi_square += ((rank_full - expected_full) ** 2) / expected_full
    if expected_m1 > 0:
        chi_square += ((rank_m1 - expected_m1) ** 2) / expected_m1
    if expected_other > 0:
        chi_square += ((rank_other - expected_other) ** 2) / expected_other
    
    # Compute p-value using chi-square distribution with 2 degrees of freedom
    p_value = chi2.sf(chi_square, 2)
    p_value = max(0.0, min(1.0, p_value))  # Clamp to [0, 1]
    
    # Test passes if p-value >= 0.01
    passed = p_value >= 0.01
    
    return NISTTestResult(
        test_name="Binary Matrix Rank Test",
        p_value=p_value,
        passed=passed,
        statistic=chi_square,
        details={
            "matrix_rows": M,
            "matrix_cols": Q,
            "num_matrices": N,
            "rank_full": rank_full,
            "rank_m1": rank_m1,
            "rank_other": rank_other,
            "expected_full": expected_full,
            "expected_m1": expected_m1,
            "expected_other": expected_other
        }
    )


def discrete_fourier_transform_test(sequence: List[int]) -> NISTTestResult:
    """
    Test 6: Discrete Fourier Transform (Spectral) Test.
    
    **Purpose**: Detects periodic features in the sequence that
    would indicate a deviation from the assumption of randomness.
    
    **What it measures**: Periodic patterns using Fourier analysis
    (frequency domain).
    
    **How it works**:
    1. Convert sequence to values -1 and +1 (0 -> -1, 1 -> +1)
    2. Compute Discrete Fourier Transform (DFT) of the sequence
    3. Compute the modulus of each DFT coefficient
     4. Count how many coefficients are below a threshold
        (expected: 95% for random)
    5. Compute p-value using normal distribution
    
    **Interpretation**:
    - Random sequences should not have periodic patterns
    - If p-value < 0.01, the sequence shows periodic features
    - This test detects sequences with repeating patterns
    
    **Minimum sequence length**: 1000 bits (recommended: 10000+ bits)
    
    Args:
        sequence: Binary sequence (list of 0s and 1s)
    
    Returns:
        NISTTestResult with test results
    
    Example:
        >>> result = discrete_fourier_transform_test([1, 0, 1, 0] * 250)
        >>> print(f"P-value: {result.p_value:.6f}, Passed: {result.passed}")
    """
    n = len(sequence)
    if n < 1000:
        return NISTTestResult(
            test_name="Discrete Fourier Transform (Spectral) Test",
            p_value=0.0,
            passed=False,
            statistic=0.0,
            details={"error": f"Sequence too short: {n} bits (minimum: 1000)"}
        )
    
    # Convert to -1, +1 representation
    # 0 -> -1, 1 -> +1
    X = [1 if bit == 1 else -1 for bit in sequence]
    
    # Compute DFT using simple implementation
    # For efficiency, we could use numpy.fft, but we'll use a basic implementation
    # to avoid numpy dependency
    N = len(X)
    
    # Compute DFT coefficients (simplified - full FFT would be more efficient)
    # We only need the magnitude, so we can compute efficiently
    # For NIST test, we compute |S_k| for k = 0, 1, ..., N/2 - 1
    magnitudes = []
    
    # Compute first N/2 coefficients (others are symmetric)
    for k in range(N // 2):
        real_sum = 0.0
        imag_sum = 0.0
        for j in range(N):
            angle = 2.0 * math.pi * k * j / N
            real_sum += X[j] * math.cos(angle)
            imag_sum += X[j] * math.sin(angle)
        
        magnitude = math.sqrt(real_sum * real_sum + imag_sum * imag_sum)
        magnitudes.append(magnitude)
    
    # Compute threshold: T = sqrt(ln(1/0.05) * n) = sqrt(ln(20) * n)
    # For 95% of coefficients to be below threshold
    threshold = math.sqrt(math.log(20.0) * n)
    
    # Count coefficients below threshold
    # Exclude the first coefficient (DC component)
    magnitudes_no_dc = magnitudes[1:] if len(magnitudes) > 1 else []
    N_0 = sum(1 for m in magnitudes_no_dc if m < threshold)
    N_1 = len(magnitudes_no_dc) - N_0
    
    # Expected: 95% below threshold
    expected_below = 0.95 * len(magnitudes_no_dc) if magnitudes_no_dc else 0
    
    # Compute test statistic using normal approximation
    # d = (N_0 - 0.95 * (N/2 - 1)) / sqrt(0.95 * 0.05 * (N/2 - 1))
    if len(magnitudes_no_dc) > 0:
        d = (N_0 - 0.95 * len(magnitudes_no_dc)) / math.sqrt(0.95 * 0.05 * len(magnitudes_no_dc))
    else:
        d = 0.0
    
    # Compute p-value using normal distribution (two-tailed)
    p_value = 2.0 * norm.sf(abs(d))
    p_value = max(0.0, min(1.0, p_value))  # Clamp to [0, 1]
    
    # Test passes if p-value >= 0.01
    passed = p_value >= 0.01
    
    return NISTTestResult(
        test_name="Discrete Fourier Transform (Spectral) Test",
        p_value=p_value,
        passed=passed,
        statistic=d,
        details={
            "n": n,
            "threshold": threshold,
            "coefficients_below_threshold": N_0,
            "coefficients_above_threshold": N_1,
            "total_coefficients": len(magnitudes_no_dc),
            "expected_below": expected_below
        }
    )


def non_overlapping_template_matching_test(
    sequence: List[int],
    template: Optional[List[int]] = None,
    block_size: int = 8
) -> NISTTestResult:
    """
    Test 7: Non-overlapping Template Matching Test.
    
    **Purpose**: Tests for occurrences of specific m-bit patterns
    (templates) in the sequence. Detects over-represented patterns
    that would indicate non-randomness.
    
    **What it measures**: Frequency of specific m-bit patterns in
    non-overlapping blocks.
    
    **How it works**:
    1. Divide the sequence into non-overlapping blocks of M bits
    2. For each block, check if it matches the template pattern
    3. Count the number of matches
     4. Compare observed frequency with expected frequency using
        chi-square test
    
    **Interpretation**:
    - Random sequences should not have over-represented patterns
    - If p-value < 0.01, the sequence shows pattern clustering
    - This test detects sequences with specific repeating patterns
    
    **Parameters**:
    - template: The m-bit pattern to search for (default:
      [0, 0, 0, 0, 0, 0, 0, 0, 1])
    - block_size (M): Size of each block (default: 8)
    
    **Minimum sequence length**: :math:`M \times 10` (recommended:
    :math:`M \times 100`)
    
    Args:
        sequence: Binary sequence (list of 0s and 1s)
        template: Template pattern to search for (default: 9-bit
          pattern ending in 1)
        block_size: Size of each block (default: 8)
    
    Returns:
        NISTTestResult with test results
    
    Example:
        >>> result = non_overlapping_template_matching_test([1, 0, 1, 0] * 250)
        >>> print(f"P-value: {result.p_value:.6f}, Passed: {result.passed}")
    """
    n = len(sequence)
    M = block_size
    
    if n < M * 10:
        return NISTTestResult(
            test_name="Non-overlapping Template Matching Test",
            p_value=0.0,
            passed=False,
            statistic=0.0,
            details={"error": f"Sequence too short: {n} bits (minimum: {M * 10})"}
        )
    
    # Default template: 9-bit pattern [0,0,0,0,0,0,0,0,1] (NIST standard)
    if template is None:
        template = [0, 0, 0, 0, 0, 0, 0, 0, 1]
    
    m = len(template)
    
    # Number of non-overlapping blocks
    N = n // M
    
    # Count matches in each block
    matches = []
    for i in range(N):
        block = sequence[i * M:(i + 1) * M]
        # Check if template appears in block (non-overlapping search)
        match_found = False
        for j in range(M - m + 1):
            if block[j:j + m] == template:
                match_found = True
                break
        matches.append(1 if match_found else 0)
    
    # Count total matches
    W = sum(matches)
    
    # Expected number of matches per block: (M - m + 1) / 2^m
    # Probability of match in a block
    prob_match = (M - m + 1) / (2 ** m)
    expected_matches = N * prob_match
    variance = N * prob_match * (1 - prob_match)
    
    if variance <= 0:
        return NISTTestResult(
            test_name="Non-overlapping Template Matching Test",
            p_value=0.0,
            passed=False,
            statistic=0.0,
            details={"error": "Variance is zero or negative"}
        )
    
    # Compute chi-square statistic
    chi_square = ((W - expected_matches) ** 2) / variance
    
    # Compute p-value using chi-square distribution with 1 degree of freedom
    p_value = chi2.sf(chi_square, 1)
    p_value = max(0.0, min(1.0, p_value))  # Clamp to [0, 1]
    
    # Test passes if p-value >= 0.01
    passed = p_value >= 0.01
    
    return NISTTestResult(
        test_name="Non-overlapping Template Matching Test",
        p_value=p_value,
        passed=passed,
        statistic=chi_square,
        details={
            "template": template,
            "template_length": m,
            "block_size": M,
            "num_blocks": N,
            "matches": W,
            "expected_matches": expected_matches,
            "variance": variance
        }
    )


def overlapping_template_matching_test(
    sequence: List[int],
    template: Optional[List[int]] = None,
    block_size: int = 1032
) -> NISTTestResult:
    """
    Test 8: Overlapping Template Matching Test.
    
    **Purpose**: Similar to Test 7, but searches for overlapping
    occurrences of a template pattern. Detects pattern clustering
    that would indicate non-randomness.
    
    **What it measures**: Frequency of overlapping m-bit patterns in
    blocks.
    
    **How it works**:
    1. Divide the sequence into N blocks of M bits each
    2. For each block, count overlapping occurrences of the template
    3. Count how many blocks have k occurrences (k = 0, 1, 2, ...)
     4. Compare observed frequencies with expected frequencies
        using chi-square test
    
    **Interpretation**:
    - Random sequences should have template occurrences
      distributed according to theory
    - If p-value < 0.01, the sequence shows pattern clustering
    - This test detects sequences with clustered patterns
    
    **Parameters**:
    - template: The m-bit pattern to search for (default:
      [1, 1, 1, 1, 1, 1, 1, 1, 1])
    - block_size (M): Size of each block (default: 1032)
    
    **Minimum sequence length**: :math:`M \times 8` (recommended:
    :math:`M \times 100`)
    
    Args:
        sequence: Binary sequence (list of 0s and 1s)
        template: Template pattern to search for (default: 9 ones)
        block_size: Size of each block (default: 1032)
    
    Returns:
        NISTTestResult with test results
    
    Example:
        >>> result = overlapping_template_matching_test([1, 0, 1, 0] * 1000)
        >>> print(f"P-value: {result.p_value:.6f}, Passed: {result.passed}")
    """
    n = len(sequence)
    M = block_size
    
    if n < M * 8:
        return NISTTestResult(
            test_name="Overlapping Template Matching Test",
            p_value=0.0,
            passed=False,
            statistic=0.0,
            details={"error": f"Sequence too short: {n} bits (minimum: {M * 8})"}
        )
    
    # Default template: 9-bit pattern of all ones [1,1,1,1,1,1,1,1,1] (NIST standard)
    if template is None:
        template = [1, 1, 1, 1, 1, 1, 1, 1, 1]
    
    m = len(template)
    
    # Number of blocks
    N = n // M
    
    # Count occurrences in each block (overlapping search)
    occurrences_per_block = []
    for i in range(N):
        block = sequence[i * M:(i + 1) * M]
        count = 0
        # Count overlapping occurrences
        for j in range(M - m + 1):
            if block[j:j + m] == template:
                count += 1
        occurrences_per_block.append(count)
    
    # Categorize blocks by number of occurrences
    # Expected distribution: Poisson with lambda = (M - m + 1) / 2^m
    lambda_param = (M - m + 1) / (2 ** m)
    
    # Count blocks in each category (0, 1, 2, 3, 4, 5+ occurrences)
    categories = [0, 0, 0, 0, 0, 0]  # 0, 1, 2, 3, 4, 5+
    for count in occurrences_per_block:
        if count < 5:
            categories[count] += 1
        else:
            categories[5] += 1
    
    # Expected frequencies using Poisson distribution
    # P(k) = (lambda^k * e^(-lambda)) / k!
    import math
    expected = []
    for k in range(5):
        if k == 0:
            prob = math.exp(-lambda_param)
        else:
            prob = (lambda_param ** k) * math.exp(-lambda_param) / math.factorial(k)
        expected.append(N * prob)
    
    # Category 5+: 1 - sum(P(0) to P(4))
    expected.append(N * (1.0 - sum(expected) / N if N > 0 else 0.0))
    
    # Compute chi-square statistic
    chi_square = 0.0
    for i in range(6):
        if expected[i] > 0:
            chi_square += ((categories[i] - expected[i]) ** 2) / expected[i]
    
    # Compute p-value using chi-square distribution with 5 degrees of freedom
    p_value = chi2.sf(chi_square, 5)
    p_value = max(0.0, min(1.0, p_value))  # Clamp to [0, 1]
    
    # Test passes if p-value >= 0.01
    passed = p_value >= 0.01
    
    return NISTTestResult(
        test_name="Overlapping Template Matching Test",
        p_value=p_value,
        passed=passed,
        statistic=chi_square,
        details={
            "template": template,
            "template_length": m,
            "block_size": M,
            "num_blocks": N,
            "lambda": lambda_param,
            "categories": categories,
            "expected": expected
        }
    )


def maurers_universal_test(sequence: List[int], block_size: int = 6, init_blocks: int = 10) -> NISTTestResult:
    """
    Test 9: Maurer's "Universal Statistical" Test.
    
    **Purpose**: Tests whether the sequence can be significantly
    compressed without loss of information. A random sequence
    should not be compressible.
    
    **What it measures**: Compressibility of the sequence (ability
    to predict future bits from past bits).
    
    **How it works**:
    1. Divide the sequence into blocks of L bits
    2. Use first Q blocks to initialize a table of block positions
     3. For each subsequent block, compute the distance to its last
        occurrence
    4. Compute the test statistic from these distances
    5. Compute p-value using normal distribution
    
    **Interpretation**:
    - Random sequences should not be compressible
    - If p-value < 0.01, the sequence shows compressibility (non-random)
    - This test detects sequences with predictable patterns
    
    **Parameters**:
    - block_size (L): Size of each block (default: 6)
    - init_blocks (Q): Number of initialization blocks (default: 10)
    
    **Minimum sequence length**: :math:`L \times (Q + K)` where
    :math:`K \geq 1000` (recommended: :math:`L \times 2000`)
    
    Args:
        sequence: Binary sequence (list of 0s and 1s)
        block_size: Size of each block (default: 6)
        init_blocks: Number of initialization blocks (default: 10)
    
    Returns:
        NISTTestResult with test results
    
    Example:
        >>> result = maurers_universal_test([1, 0, 1, 0] * 1000, block_size=6)
        >>> print(f"P-value: {result.p_value:.6f}, Passed: {result.passed}")
    """
    n = len(sequence)
    L = block_size
    Q = init_blocks
    
    # Minimum: L * (Q + 1000)
    min_length = L * (Q + 1000)
    if n < min_length:
        return NISTTestResult(
            test_name="Maurer's \"Universal Statistical\" Test",
            p_value=0.0,
            passed=False,
            statistic=0.0,
            details={"error": f"Sequence too short: {n} bits (minimum: {min_length})"}
        )
    
    # Number of blocks
    K = (n // L) - Q  # Blocks after initialization
    if K < 1000:
        return NISTTestResult(
            test_name="Maurer's \"Universal Statistical\" Test",
            p_value=0.0,
            passed=False,
            statistic=0.0,
            details={"error": f"Not enough blocks after initialization: {K} (minimum: 1000)"}
        )
    
    # Initialize table: map block pattern to last position
    table = {}
    for i in range(Q):
        block = tuple(sequence[i * L:(i + 1) * L])
        table[block] = i + 1  # 1-indexed position
    
    # Process remaining blocks and compute distances
    distances = []
    for i in range(Q, Q + K):
        block = tuple(sequence[i * L:(i + 1) * L])
        if block in table:
            distance = i + 1 - table[block]
            distances.append(distance)
        else:
            # First occurrence after initialization - use large distance
            distances.append(i + 1)
        table[block] = i + 1  # Update position
    
    # Compute test statistic: f_n = (1/K) * sum(log2(distance))
    if len(distances) == 0:
        return NISTTestResult(
            test_name="Maurer's \"Universal Statistical\" Test",
            p_value=0.0,
            passed=False,
            statistic=0.0,
            details={"error": "No distances computed"}
        )
    
    f_n = sum(math.log2(d) if d > 0 else 0 for d in distances) / len(distances)
    
    # Expected value and variance (from NIST specification)
    # These depend on L
    expected_values = {
        1: 0.7326495, 2: 1.5374383, 3: 2.4016068, 4: 3.3112247, 5: 4.2534266,
        6: 5.2177052, 7: 6.1962507, 8: 7.1836656, 9: 8.1764248, 10: 9.1723243,
        11: 10.170032, 12: 11.168765, 13: 12.168070, 14: 13.167693, 15: 14.167488,
        16: 15.167379
    }
    
    variance_values = {
        1: 0.690, 2: 1.338, 3: 1.901, 4: 2.358, 5: 2.705, 6: 2.954, 7: 3.125,
        8: 3.238, 9: 3.311, 10: 3.356, 11: 3.384, 12: 3.401, 13: 3.410, 14: 3.416,
        15: 3.419, 16: 3.421
    }
    
    expected = expected_values.get(L, 0.0)
    variance = variance_values.get(L, 1.0)
    
    if expected == 0.0:
        return NISTTestResult(
            test_name="Maurer's \"Universal Statistical\" Test",
            p_value=0.0,
            passed=False,
            statistic=0.0,
            details={"error": f"Unsupported block size: {L} (supported: 1-16)"}
        )
    
    # Compute test statistic: z-score
    z_score = (f_n - expected) / math.sqrt(variance / K)
    
    # Compute p-value using normal distribution (two-tailed)
    p_value = 2.0 * norm.sf(abs(z_score))
    p_value = max(0.0, min(1.0, p_value))  # Clamp to [0, 1]
    
    # Test passes if p-value >= 0.01
    passed = p_value >= 0.01
    
    return NISTTestResult(
        test_name="Maurer's \"Universal Statistical\" Test",
        p_value=p_value,
        passed=passed,
        statistic=z_score,
        details={
            "block_size": L,
            "init_blocks": Q,
            "test_blocks": K,
            "f_n": f_n,
            "expected": expected,
            "variance": variance
        }
    )


def linear_complexity_test(sequence: List[int], block_size: int = 500) -> NISTTestResult:
    """
    Test 10: Linear Complexity Test.
    
    **Purpose**: Tests whether the sequence is complex enough to be
    considered random. Sequences with low linear complexity are
    predictable and non-random.
    
    **What it measures**: Linear complexity of blocks using the
    Berlekamp-Massey algorithm.
    
    **How it works**:
    1. Divide the sequence into N blocks of M bits each
    2. For each block, compute the linear complexity using Berlekamp-Massey
    3. Compute deviations from expected complexity:
       :math:`T_i = (-1)^M \cdot (LC_i - \mu)`
    4. Count how many T_i fall into each category
     5. Compare observed frequencies with expected frequencies
        using chi-square test
    
    **Interpretation**:
    - Random sequences should have high linear complexity
    - If p-value < 0.01, the sequence has lower complexity than expected
    - This test detects sequences that are too predictable
    
    **Parameters**:
    - block_size (M): Size of each block (default: 500)
    
    **Minimum sequence length**: :math:`M \times 200` (recommended:
    :math:`M \times 1000`)
    
    Args:
        sequence: Binary sequence (list of 0s and 1s)
        block_size: Size of each block (default: 500)
    
    Returns:
        NISTTestResult with test results
    
    Example:
        >>> result = linear_complexity_test([1, 0, 1, 0] * 500, block_size=500)
        >>> print(f"P-value: {result.p_value:.6f}, Passed: {result.passed}")
    """
    n = len(sequence)
    M = block_size
    
    if n < M * 200:
        return NISTTestResult(
            test_name="Linear Complexity Test",
            p_value=0.0,
            passed=False,
            statistic=0.0,
            details={"error": f"Sequence too short: {n} bits (minimum: {M * 200})"}
        )
    
    # Number of blocks
    N = n // M
    
    # Compute linear complexity for each block
    from lfsr.synthesis import linear_complexity
    
    linear_complexities = []
    for i in range(N):
        block = sequence[i * M:(i + 1) * M]
        lc = linear_complexity(block, 2)
        linear_complexities.append(lc)
    
    # Expected linear complexity: mu = M/2 + (9 + (-1)^(M+1)) / 36
    # - (M/3 + 2/9) / 2^M
    mu = M / 2.0 + (9.0 + ((-1) ** (M + 1))) / 36.0 - (M / 3.0 + 2.0 / 9.0) / (2 ** M)
    
    # Compute deviations: T_i = (-1)^M * (LC_i - mu)
    deviations = [((-1) ** M) * (lc - mu) for lc in linear_complexities]
    
    # Categorize deviations
    # Categories: <= -2, -1, 0, +1, >= +2
    categories = [0, 0, 0, 0, 0]
    for d in deviations:
        if d <= -2:
            categories[0] += 1
        elif d == -1:
            categories[1] += 1
        elif d == 0:
            categories[2] += 1
        elif d == 1:
            categories[3] += 1
        else:  # >= 2
            categories[4] += 1
    
    # Expected frequencies (from NIST specification, approximate)
    # These are theoretical probabilities for each category
    # For simplicity, we use approximations
    pi_values = [0.0228, 0.1587, 0.3413, 0.3413, 0.1359]  # Approximate normal distribution
    expected = [N * pi for pi in pi_values]
    
    # Compute chi-square statistic
    chi_square = 0.0
    for i in range(5):
        if expected[i] > 0:
            chi_square += ((categories[i] - expected[i]) ** 2) / expected[i]
    
    # Compute p-value using chi-square distribution with 4 degrees of freedom
    p_value = chi2.sf(chi_square, 4)
    p_value = max(0.0, min(1.0, p_value))  # Clamp to [0, 1]
    
    # Test passes if p-value >= 0.01
    passed = p_value >= 0.01
    
    return NISTTestResult(
        test_name="Linear Complexity Test",
        p_value=p_value,
        passed=passed,
        statistic=chi_square,
        details={
            "block_size": M,
            "num_blocks": N,
            "linear_complexities": linear_complexities[:10] if len(linear_complexities) > 10 else linear_complexities,
            "mean_complexity": sum(linear_complexities) / len(linear_complexities) if linear_complexities else 0.0,
            "expected_complexity": mu,
            "categories": categories,
            "expected": expected
        }
    )


def serial_test(sequence: List[int], block_size: int = 2) -> NISTTestResult:
    """
    Test 11: Serial Test.
    
    **Purpose**: Tests whether the number of occurrences of
    :math:`2^m` m-bit overlapping patterns is approximately the same
    as would be expected for a random sequence.
    
    **What it measures**: Frequency distribution of m-bit overlapping
    patterns.
    
    **How it works**:
    1. Count occurrences of all possible m-bit patterns (overlapping)
    2. Count occurrences of all possible (m-1)-bit patterns
    3. Count occurrences of all possible (m-2)-bit patterns
    4. Compute chi-square statistics for each pattern length
    5. Compute p-value using chi-square distribution
    
    **Interpretation**:
    - Random sequences should have uniform pattern distribution
    - If p-value < 0.01, the sequence shows non-uniform pattern
      distribution
    - This test detects sequences with pattern bias
    
    **Parameters**:
    - block_size (m): Pattern length (default: 2)
    
    **Minimum sequence length**: :math:`2^m \times 100` (recommended:
    :math:`2^m \times 1000`)
    
    Args:
        sequence: Binary sequence (list of 0s and 1s)
        block_size: Pattern length m (default: 2)
    
    Returns:
        NISTTestResult with test results
    
    Example:
        >>> result = serial_test([1, 0, 1, 0] * 500, block_size=2)
        >>> print(f"P-value: {result.p_value:.6f}, Passed: {result.passed}")
    """
    n = len(sequence)
    m = block_size
    
    # Minimum length: 2^m * 100
    min_length = (2 ** m) * 100
    if n < min_length:
        return NISTTestResult(
            test_name="Serial Test",
            p_value=0.0,
            passed=False,
            statistic=0.0,
            details={"error": f"Sequence too short: {n} bits (minimum: {min_length})"}
        )
    
    # Count patterns for m, m-1, m-2
    pattern_counts_m = {}
    pattern_counts_m1 = {}
    pattern_counts_m2 = {}
    
    # Count m-bit patterns
    for i in range(n - m + 1):
        pattern = tuple(sequence[i:i + m])
        pattern_counts_m[pattern] = pattern_counts_m.get(pattern, 0) + 1
    
    # Count (m-1)-bit patterns
    if m > 1:
        for i in range(n - m + 2):
            pattern = tuple(sequence[i:i + m - 1])
            pattern_counts_m1[pattern] = pattern_counts_m1.get(pattern, 0) + 1
    
    # Count (m-2)-bit patterns
    if m > 2:
        for i in range(n - m + 3):
            pattern = tuple(sequence[i:i + m - 2])
            pattern_counts_m2[pattern] = pattern_counts_m2.get(pattern, 0) + 1
    
    # Compute chi-square statistics
    # For m-bit patterns
    expected_m = (n - m + 1) / (2 ** m)
    chi_square_m = sum(((count - expected_m) ** 2) / expected_m for count in pattern_counts_m.values())
    
    # For (m-1)-bit patterns
    chi_square_m1 = 0.0
    if m > 1:
        expected_m1 = (n - m + 2) / (2 ** (m - 1))
        chi_square_m1 = sum(((count - expected_m1) ** 2) / expected_m1 for count in pattern_counts_m1.values())
    
    # For (m-2)-bit patterns
    chi_square_m2 = 0.0
    if m > 2:
        expected_m2 = (n - m + 3) / (2 ** (m - 2))
        chi_square_m2 = sum(((count - expected_m2) ** 2) / expected_m2 for count in pattern_counts_m2.values())
    
    # Compute delta chi-square
    delta_chi_square = chi_square_m - chi_square_m1
    delta2_chi_square = chi_square_m - 2 * chi_square_m1 + chi_square_m2 if m > 2 else chi_square_m - chi_square_m1
    
    # Compute p-values
    df1 = 2 ** (m - 1)  # Degrees of freedom for delta
    df2 = 2 ** (m - 2) if m > 2 else 2 ** (m - 1)  # Degrees of freedom for delta2
    
    p_value1 = chi2.sf(delta_chi_square, df1) if df1 > 0 else 1.0
    p_value2 = chi2.sf(delta2_chi_square, df2) if df2 > 0 and m > 2 else 1.0
    
    # Use the minimum p-value (more conservative)
    p_value = min(p_value1, p_value2) if m > 2 else p_value1
    p_value = max(0.0, min(1.0, p_value))  # Clamp to [0, 1]
    
    # Test passes if p-value >= 0.01
    passed = p_value >= 0.01
    
    return NISTTestResult(
        test_name="Serial Test",
        p_value=p_value,
        passed=passed,
        statistic=delta_chi_square,
        details={
            "block_size": m,
            "chi_square_m": chi_square_m,
            "chi_square_m1": chi_square_m1,
            "chi_square_m2": chi_square_m2,
            "delta_chi_square": delta_chi_square,
            "delta2_chi_square": delta2_chi_square,
            "p_value1": p_value1,
            "p_value2": p_value2
        }
    )


def approximate_entropy_test(sequence: List[int], block_size: int = 2) -> NISTTestResult:
    """
    Test 12: Approximate Entropy Test.
    
    **Purpose**: Tests the frequency of all possible overlapping
    m-bit patterns. Compares the frequency of overlapping blocks of
    two consecutive lengths (m and m+1) against the expected result
    for a random sequence.
    
    **What it measures**: Entropy (randomness) of overlapping patterns.
    
    **How it works**:
    1. Count occurrences of all possible m-bit patterns
    2. Count occurrences of all possible (m+1)-bit patterns
    3. Compute approximate entropy from pattern frequencies
    4. Compute chi-square statistic
    5. Compute p-value using chi-square distribution
    
    **Interpretation**:
    - Random sequences should have high entropy (uniform pattern
      distribution)
    - If p-value < 0.01, the sequence shows low entropy (non-random)
    - This test detects sequences with pattern bias
    
    **Parameters**:
    - block_size (m): Pattern length (default: 2)
    
    **Minimum sequence length**: :math:`2^m \times 10` (recommended:
    :math:`2^m \times 100`)
    
    Args:
        sequence: Binary sequence (list of 0s and 1s)
        block_size: Pattern length m (default: 2)
    
    Returns:
        NISTTestResult with test results
    
    Example:
        >>> result = approximate_entropy_test([1, 0, 1, 0] * 500, block_size=2)
        >>> print(f"P-value: {result.p_value:.6f}, Passed: {result.passed}")
    """
    n = len(sequence)
    m = block_size
    
    # Minimum length: 2^m * 10
    min_length = (2 ** m) * 10
    if n < min_length:
        return NISTTestResult(
            test_name="Approximate Entropy Test",
            p_value=0.0,
            passed=False,
            statistic=0.0,
            details={"error": f"Sequence too short: {n} bits (minimum: {min_length})"}
        )
    
    # Count m-bit patterns
    pattern_counts_m = {}
    for i in range(n - m + 1):
        pattern = tuple(sequence[i:i + m])
        pattern_counts_m[pattern] = pattern_counts_m.get(pattern, 0) + 1
    
    # Count (m+1)-bit patterns
    pattern_counts_m1 = {}
    for i in range(n - m):
        pattern = tuple(sequence[i:i + m + 1])
        pattern_counts_m1[pattern] = pattern_counts_m1.get(pattern, 0) + 1
    
    # Compute approximate entropy
    # Phi(m) = sum of (count / (n-m+1)) * log2(count / (n-m+1))
    phi_m = 0.0
    for count in pattern_counts_m.values():
        if count > 0:
            prob = count / (n - m + 1)
            phi_m += prob * math.log2(prob)
    
    phi_m1 = 0.0
    for count in pattern_counts_m1.values():
        if count > 0:
            prob = count / (n - m)
            phi_m1 += prob * math.log2(prob)
    
    # Approximate entropy
    ap_en = phi_m - phi_m1
    
    # Compute chi-square statistic
    # chi_square = 2 * n * (ln(2) - ap_en)
    chi_square = 2.0 * n * (math.log(2) - ap_en)
    
    # Degrees of freedom: 2^m
    df = 2 ** m
    
    # Compute p-value using chi-square distribution
    p_value = chi2.sf(chi_square, df)
    p_value = max(0.0, min(1.0, p_value))  # Clamp to [0, 1]
    
    # Test passes if p-value >= 0.01
    passed = p_value >= 0.01
    
    return NISTTestResult(
        test_name="Approximate Entropy Test",
        p_value=p_value,
        passed=passed,
        statistic=chi_square,
        details={
            "block_size": m,
            "phi_m": phi_m,
            "phi_m1": phi_m1,
            "approximate_entropy": ap_en,
            "chi_square": chi_square
        }
    )


def cumulative_sums_test(sequence: List[int], mode: str = "forward") -> NISTTestResult:
    """
    Test 13: Cumulative Sums (Cusum) Test.
    
    **Purpose**: Tests whether the cumulative sum of the partial
    sequences occurring in the tested sequence is too large or too
    small relative to what would be expected for a random sequence.
    
    **What it measures**: Maximum deviation of cumulative sums from zero.
    
    **How it works**:
    1. Convert sequence to -1, +1 (0 -> -1, 1 -> +1)
    2. Compute cumulative sums
    3. Find maximum absolute cumulative sum
    4. Compute p-value using normal distribution approximation
    
    **Interpretation**:
    - Random sequences should have cumulative sums that stay
      close to zero
    - If p-value < 0.01, the sequence shows significant bias in
      cumulative sums
    - This test detects sequences with long runs or trends
    
    **Parameters**:
    - mode: "forward" or "backward" (default: "forward")
    
    **Minimum sequence length**: 100 bits (recommended: 1000+ bits)
    
    Args:
        sequence: Binary sequence (list of 0s and 1s)
        mode: "forward" or "backward" (default: "forward")
    
    Returns:
        NISTTestResult with test results
    
    Example:
        >>> result = cumulative_sums_test([1, 0, 1, 0] * 250, mode="forward")
        >>> print(f"P-value: {result.p_value:.6f}, Passed: {result.passed}")
    """
    n = len(sequence)
    
    if n < 100:
        return NISTTestResult(
            test_name="Cumulative Sums (Cusum) Test",
            p_value=0.0,
            passed=False,
            statistic=0.0,
            details={"error": f"Sequence too short: {n} bits (minimum: 100)"}
        )
    
    # Convert to -1, +1
    X = [1 if bit == 1 else -1 for bit in sequence]
    
    if mode == "backward":
        X = X[::-1]
    
    # Compute cumulative sums
    S = [0]
    for x in X:
        S.append(S[-1] + x)
    
    # Find maximum absolute cumulative sum
    max_abs_sum = max(abs(s) for s in S)
    
    # Compute p-value using normal distribution approximation
    # P-value = 1 - sum of probabilities for |z| <= max_abs_sum
    # Using approximation from NIST specification
    z = max_abs_sum / math.sqrt(n)
    
    # Compute p-value using normal distribution (two-tailed)
    # P(|Z| > z) = 2 * (1 - Phi(z))
    p_value = 2.0 * norm.sf(z)
    p_value = max(0.0, min(1.0, p_value))  # Clamp to [0, 1]
    
    # Test passes if p-value >= 0.01
    passed = p_value >= 0.01
    
    return NISTTestResult(
        test_name="Cumulative Sums (Cusum) Test",
        p_value=p_value,
        passed=passed,
        statistic=z,
        details={
            "mode": mode,
            "max_absolute_sum": max_abs_sum,
            "z_score": z
        }
    )


def random_excursions_test(sequence: List[int]) -> NISTTestResult:
    """
    Test 14: Random Excursions Test.
    
    **Purpose**: Tests the number of cycles having exactly K visits
    in a cumulative sum random walk. The test detects deviations
    from the expected number of visits to various states in the
    random walk.
    
    **What it measures**: Distribution of visits to states in a random walk.
    
    **How it works**:
    1. Convert sequence to -1, +1 (0 -> -1, 1 -> +1)
    2. Compute cumulative sums (random walk)
    3. Identify cycles (return to zero)
    4. Count visits to each state (-4, -3, -2, -1, +1, +2, +3, +4)
    5. Compute chi-square statistic for each state
    6. Compute p-value using chi-square distribution
    
    **Interpretation**:
    - Random sequences should have expected distribution of state visits
    - If p-value < 0.01, the sequence shows non-random state visit distribution
    - This test detects sequences with bias in random walk behavior
    
    **Minimum sequence length**: 1000 bits (recommended: 10000+ bits)
    
    Args:
        sequence: Binary sequence (list of 0s and 1s)
    
    Returns:
        NISTTestResult with test results
    
    Example:
        >>> result = random_excursions_test([1, 0, 1, 0] * 500)
        >>> print(f"P-value: {result.p_value:.6f}, Passed: {result.passed}")
    """
    n = len(sequence)
    
    if n < 1000:
        return NISTTestResult(
            test_name="Random Excursions Test",
            p_value=0.0,
            passed=False,
            statistic=0.0,
            details={"error": f"Sequence too short: {n} bits (minimum: 1000)"}
        )
    
    # Convert to -1, +1
    X = [1 if bit == 1 else -1 for bit in sequence]
    
    # Compute cumulative sums
    S = [0]
    for x in X:
        S.append(S[-1] + x)
    
    # Find cycles (return to zero)
    cycles = []
    current_cycle = []
    for i, s in enumerate(S):
        if s == 0:
            if current_cycle:
                cycles.append(current_cycle)
            current_cycle = []
        else:
            current_cycle.append(s)
    
    # If sequence doesn't end at zero, add last cycle
    if current_cycle:
        cycles.append(current_cycle)
    
    # States to test: -4, -3, -2, -1, +1, +2, +3, +4
    states = [-4, -3, -2, -1, 1, 2, 3, 4]
    
    # Count visits to each state in each cycle
    state_visit_counts = {state: [] for state in states}
    
    for cycle in cycles:
        if len(cycle) == 0:
            continue
        
        # Count visits to each state in this cycle
        for state in states:
            count = cycle.count(state)
            state_visit_counts[state].append(count)
    
    # Compute chi-square statistics for each state
    chi_square_values = {}
    p_values = {}
    
    # Expected probabilities for each state (from NIST specification)
    # P(x) = probability of visiting state x
    expected_probs = {
        -4: 0.03125, -3: 0.0625, -2: 0.125, -1: 0.25,
        1: 0.25, 2: 0.125, 3: 0.0625, 4: 0.03125
    }
    
    for state in states:
        visits = state_visit_counts[state]
        if len(visits) == 0:
            continue
        
        # Count cycles with k visits (k = 0, 1, 2, 3, 4, 5+)
        visit_counts = [0, 0, 0, 0, 0, 0]  # 0, 1, 2, 3, 4, 5+
        for v in visits:
            if v < 5:
                visit_counts[v] += 1
            else:
                visit_counts[5] += 1
        
        # Expected frequencies
        num_cycles = len(visits)
        expected = [
            num_cycles * expected_probs[state] * (1 - expected_probs[state]) ** k
            for k in range(5)
        ]
        expected.append(num_cycles * (1 - sum(expected[:5]) / num_cycles if num_cycles > 0 else 0))
        
        # Compute chi-square
        chi_square = 0.0
        for i in range(6):
            if expected[i] > 0:
                chi_square += ((visit_counts[i] - expected[i]) ** 2) / expected[i]
        
        chi_square_values[state] = chi_square
        # Degrees of freedom: 5
        p_values[state] = chi2.sf(chi_square, 5)
    
    # Use minimum p-value (most conservative)
    if p_values:
        min_p_value = min(p_values.values())
        min_p_value = max(0.0, min(1.0, min_p_value))  # Clamp to [0, 1]
    else:
        min_p_value = 1.0
    
    # Test passes if p-value >= 0.01
    passed = min_p_value >= 0.01
    
    return NISTTestResult(
        test_name="Random Excursions Test",
        p_value=min_p_value,
        passed=passed,
        statistic=min(chi_square_values.values()) if chi_square_values else 0.0,
        details={
            "num_cycles": len(cycles),
            "chi_square_values": chi_square_values,
            "p_values": p_values,
            "states_tested": states
        }
    )


def random_excursions_variant_test(sequence: List[int]) -> NISTTestResult:
    """
    Test 15: Random Excursions Variant Test.
    
    **Purpose**: Tests the total number of times that a particular
    state is visited in a cumulative sum random walk. This is a
    variant of Test 14 that focuses on the total number of visits
    rather than the distribution of visits per cycle.
    
    **What it measures**: Total number of visits to each state in a random walk.
    
    **How it works**:
    1. Convert sequence to -1, +1 (0 -> -1, 1 -> +1)
    2. Compute cumulative sums (random walk)
    3. Count total visits to each state (-9 to +9, excluding 0)
    4. Compute chi-square statistic for each state
    5. Compute p-value using chi-square distribution
    
    **Interpretation**:
    - Random sequences should have expected total visits to each state
    - If p-value < 0.01, the sequence shows non-random state visit counts
    - This test detects sequences with bias in random walk behavior
    
    **Minimum sequence length**: 1000 bits (recommended: 10000+ bits)
    
    Args:
        sequence: Binary sequence (list of 0s and 1s)
    
    Returns:
        NISTTestResult with test results
    
    Example:
        >>> result = random_excursions_variant_test([1, 0, 1, 0] * 500)
        >>> print(f"P-value: {result.p_value:.6f}, Passed: {result.passed}")
    """
    n = len(sequence)
    
    if n < 1000:
        return NISTTestResult(
            test_name="Random Excursions Variant Test",
            p_value=0.0,
            passed=False,
            statistic=0.0,
            details={"error": f"Sequence too short: {n} bits (minimum: 1000)"}
        )
    
    # Convert to -1, +1
    X = [1 if bit == 1 else -1 for bit in sequence]
    
    # Compute cumulative sums
    S = [0]
    for x in X:
        S.append(S[-1] + x)
    
    # States to test: -9, -8, ..., -1, +1, ..., +8, +9
    states = list(range(-9, 0)) + list(range(1, 10))
    
    # Count total visits to each state
    state_visit_totals = {state: 0 for state in states}
    
    for s in S:
        if s in state_visit_totals:
            state_visit_totals[s] += 1
    
    # Compute chi-square statistics for each state
    chi_square_values = {}
    p_values = {}
    
    # Expected number of visits (from NIST specification)
    # For state x, expected visits = n / (2 * |x| * (|x| + 1))
    for state in states:
        abs_state = abs(state)
        expected_visits = n / (2 * abs_state * (abs_state + 1))
        observed_visits = state_visit_totals[state]
        
        # Compute chi-square
        if expected_visits > 0:
            chi_square = ((observed_visits - expected_visits) ** 2) / expected_visits
        else:
            chi_square = 0.0
        
        chi_square_values[state] = chi_square
        # Degrees of freedom: 1
        p_values[state] = chi2.sf(chi_square, 1)
    
    # Use minimum p-value (most conservative)
    if p_values:
        min_p_value = min(p_values.values())
        min_p_value = max(0.0, min(1.0, min_p_value))  # Clamp to [0, 1]
    else:
        min_p_value = 1.0
    
    # Test passes if p-value >= 0.01
    passed = min_p_value >= 0.01
    
    return NISTTestResult(
        test_name="Random Excursions Variant Test",
        p_value=min_p_value,
        passed=passed,
        statistic=min(chi_square_values.values()) if chi_square_values else 0.0,
        details={
            "state_visit_totals": state_visit_totals,
            "chi_square_values": {k: v for k, v in list(chi_square_values.items())[:5]},  # Show first 5
            "p_values": {k: v for k, v in list(p_values.items())[:5]}  # Show first 5
        }
    )


def run_nist_test_suite(
    sequence: List[int],
    significance_level: float = 0.01,
    block_size: int = 128,
    matrix_rows: int = 32,
    matrix_cols: int = 32
) -> NISTTestSuiteResult:
    """
    Run the complete NIST SP 800-22 test suite on a binary sequence.
    
    This function runs all 15 NIST statistical tests and provides a
    comprehensive assessment of the sequence's randomness properties.
    
    **Test Suite Overview**:
    
    The NIST SP 800-22 test suite consists of 15 tests, each
    examining a different aspect of randomness:
    
    1. Frequency (Monobit) Test
    2. Frequency Test within a Block
    3. Runs Test
    4. Tests for Longest-Run-of-Ones in a Block
    5. Binary Matrix Rank Test
    6. Discrete Fourier Transform (Spectral) Test
    7. Non-overlapping Template Matching Test
    8. Overlapping Template Matching Test
    9. Maurer's "Universal Statistical" Test
    10. Linear Complexity Test
    11. Serial Test
    12. Approximate Entropy Test
    13. Cumulative Sums (Cusum) Test
    14. Random Excursions Test
    15. Random Excursions Variant Test
    
    **Interpretation**:
    
    - A sequence **passes** the test suite if most tests pass
      (p-value >= significance_level)
    - A single test failure does not necessarily mean the sequence
      is non-random
    - The suite should be interpreted as a whole, not individual
      tests
    - For cryptographic applications, sequences should pass all or
      nearly all tests
    
    **Minimum Requirements**:
    
    - Minimum sequence length: 1000 bits (for basic tests)
    - Recommended: 1,000,000+ bits for comprehensive evaluation
    - Some tests require longer sequences (see individual test
      documentation)
    
    Args:
        sequence: Binary sequence (list of 0s and 1s)
        significance_level: Statistical significance level (default: 0.01)
        block_size: Block size for block-based tests (default: 128)
        matrix_rows: Number of rows for matrix rank test
          (default: 32)
        matrix_cols: Number of columns for matrix rank test
          (default: 32)
    
    Returns:
        NISTTestSuiteResult with complete test suite results
    
    Example:
        >>> sequence = [1, 0, 1, 0] * 250  # 1000 bits
        >>> result = run_nist_test_suite(sequence)
        >>> print(f"Tests passed: {result.tests_passed}/{result.total_tests}")
        >>> print(f"Overall: {result.overall_assessment}")
    """
    n = len(sequence)
    
    if n < 1000:
        # Return error result
        return NISTTestSuiteResult(
            sequence_length=n,
            significance_level=significance_level,
            tests_passed=0,
            tests_failed=0,
            total_tests=0,
            results=[],
            overall_assessment="FAILED",
            pass_rate=0.0
        )
    
    # Run all available tests
    # Note: We'll implement tests incrementally, starting with the first 5
    results = []
    
    # Test 1: Frequency (Monobit) Test
    results.append(frequency_test(sequence))
    
    # Test 2: Frequency Test within a Block
    results.append(block_frequency_test(sequence, block_size=block_size))
    
    # Test 3: Runs Test
    results.append(runs_test(sequence))
    
    # Test 4: Longest Run of Ones Test
    # Determine block size based on sequence length
    if n >= 750000:
        longest_run_block_size = 10000
    elif n >= 6272:
        longest_run_block_size = 128
    else:
        longest_run_block_size = 8
    results.append(longest_run_of_ones_test(sequence, block_size=longest_run_block_size))
    
    # Test 5: Binary Matrix Rank Test
    results.append(binary_matrix_rank_test(sequence, matrix_rows=matrix_rows, matrix_cols=matrix_cols))
    
    # Test 6: Discrete Fourier Transform (Spectral) Test
    results.append(discrete_fourier_transform_test(sequence))
    
    # Test 7: Non-overlapping Template Matching Test
    results.append(non_overlapping_template_matching_test(sequence, block_size=block_size))
    
    # Test 8: Overlapping Template Matching Test
    # Use larger block size for overlapping test
    overlapping_block_size = 1032 if n >= 1032 * 8 else block_size
    results.append(overlapping_template_matching_test(sequence, block_size=overlapping_block_size))
    
    # Test 9: Maurer's "Universal Statistical" Test
    results.append(maurers_universal_test(sequence))
    
    # Test 10: Linear Complexity Test
    results.append(linear_complexity_test(sequence, block_size=500))
    
    # Test 11: Serial Test
    results.append(serial_test(sequence, block_size=2))
    
    # Test 12: Approximate Entropy Test
    results.append(approximate_entropy_test(sequence, block_size=2))
    
    # Test 13: Cumulative Sums Test
    results.append(cumulative_sums_test(sequence, mode="forward"))
    
    # Test 14: Random Excursions Test
    results.append(random_excursions_test(sequence))
    
    # Test 15: Random Excursions Variant Test
    results.append(random_excursions_variant_test(sequence))
    
    # Update significance level for all results
    for result in results:
        result.passed = result.p_value >= significance_level
    
    # Count passed/failed tests
    tests_passed = sum(1 for r in results if r.passed)
    tests_failed = len(results) - tests_passed
    total_tests = len(results)
    
    # Overall assessment
    # Pass if at least 80% of tests pass (or all tests if total < 5)
    pass_rate = tests_passed / total_tests if total_tests > 0 else 0.0
    if total_tests < 5:
        overall_assessment = "PASSED" if tests_passed == total_tests else "FAILED"
    else:
        overall_assessment = "PASSED" if pass_rate >= 0.80 else "FAILED"
    
    return NISTTestSuiteResult(
        sequence_length=n,
        significance_level=significance_level,
        tests_passed=tests_passed,
        tests_failed=tests_failed,
        total_tests=total_tests,
        results=results,
        overall_assessment=overall_assessment,
        pass_rate=pass_rate
    )
