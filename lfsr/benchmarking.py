#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Benchmarking framework for LFSR analysis methods.

This module provides functionality to benchmark analysis methods for
performance and accuracy comparisons.
"""

import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from lfsr.sage_imports import *


@dataclass
class BenchmarkResult:
    """
    Results from a single benchmark run.
    
    Attributes:
        method_name: Name of the method being benchmarked
        execution_time: Execution time in seconds
        memory_usage: Memory usage (if available)
        result_correct: Whether result matches expected value
        result_value: The computed result value
        expected_value: Expected result value (if known)
        parameters: Parameters used for the benchmark
    """
    method_name: str
    execution_time: float
    memory_usage: Optional[float] = None
    result_correct: Optional[bool] = None
    result_value: Any = None
    expected_value: Any = None
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkSuite:
    """
    Collection of benchmark results.
    
    Attributes:
        suite_name: Name of the benchmark suite
        results: List of benchmark results
        total_time: Total execution time
        average_time: Average execution time per benchmark
    """
    suite_name: str
    results: List[BenchmarkResult] = field(default_factory=list)
    total_time: float = 0.0
    average_time: float = 0.0


def benchmark_polynomial_order(
    polynomial: Any,
    field_order: int,
    state_vector_dim: int,
    expected_order: Optional[int] = None
) -> BenchmarkResult:
    """
    Benchmark polynomial order computation.
    
    This function benchmarks the polynomial order computation method,
    measuring execution time and verifying correctness if expected value is provided.
    
    **Key Terminology**:
    
    - **Benchmarking**: The process of measuring and comparing the performance
      of different methods or algorithms. This helps identify the most efficient
      approach for a given problem.
    
    - **Performance Metrics**: Quantitative measures of performance, such as
      execution time, memory usage, or computational complexity.
    
    - **Accuracy Verification**: Checking that computed results match expected
      values, ensuring correctness of the implementation.
    
    Args:
        polynomial: Polynomial to analyze
        field_order: Field order
        state_vector_dim: State vector dimension
        expected_order: Optional expected order for verification
    
    Returns:
        BenchmarkResult with timing and correctness information
    """
    from lfsr.polynomial import polynomial_order
    
    start_time = time.time()
    computed_order = polynomial_order(polynomial, state_vector_dim, field_order)
    execution_time = time.time() - start_time
    
    result_correct = None
    if expected_order is not None:
        if computed_order != oo:
            result_correct = int(computed_order) == expected_order
        else:
            result_correct = False
    
    return BenchmarkResult(
        method_name="polynomial_order",
        execution_time=execution_time,
        result_correct=result_correct,
        result_value=int(computed_order) if computed_order != oo else None,
        expected_value=expected_order,
        parameters={
            'field_order': field_order,
            'degree': polynomial.degree(),
            'state_vector_dim': state_vector_dim
        }
    )


def benchmark_period_computation(
    coefficients: List[int],
    field_order: int,
    method: str = "enumeration",
    expected_period: Optional[int] = None
) -> BenchmarkResult:
    """
    Benchmark period computation methods.
    
    This function benchmarks different period computation methods (enumeration,
    factorization) and compares their performance.
    
    Args:
        coefficients: LFSR coefficients
        field_order: Field order
        method: Method to use ("enumeration" or "factorization")
        expected_period: Optional expected period for verification
    
    Returns:
        BenchmarkResult with timing and correctness information
    """
    from lfsr.core import compute_period_enumeration
    from lfsr.polynomial import compute_period_via_factorization
    
    start_time = time.time()
    
    if method == "enumeration":
        computed_period = compute_period_enumeration(coefficients, field_order)
    elif method == "factorization":
        computed_period = compute_period_via_factorization(coefficients, field_order)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    execution_time = time.time() - start_time
    
    result_correct = None
    if expected_period is not None:
        result_correct = computed_period == expected_period
    
    return BenchmarkResult(
        method_name=f"period_computation_{method}",
        execution_time=execution_time,
        result_correct=result_correct,
        result_value=computed_period,
        expected_value=expected_period,
        parameters={
            'coefficients': coefficients,
            'field_order': field_order,
            'method': method
        }
    )


def run_benchmark_suite(
    test_cases: List[Dict[str, Any]],
    suite_name: str = "LFSR Analysis Benchmarks"
) -> BenchmarkSuite:
    """
    Run a suite of benchmarks.
    
    This function runs multiple benchmarks and aggregates the results
    for comparison and analysis.
    
    Args:
        test_cases: List of test case dictionaries with benchmark parameters
        suite_name: Name of the benchmark suite
    
    Returns:
        BenchmarkSuite with aggregated results
    """
    suite = BenchmarkSuite(suite_name=suite_name)
    total_time = 0.0
    
    for test_case in test_cases:
        benchmark_type = test_case.get('type', 'polynomial_order')
        
        if benchmark_type == 'polynomial_order':
            from lfsr.sage_imports import PolynomialRing, GF
            F = GF(test_case['field_order'])
            R = PolynomialRing(F, "t")
            poly = R(test_case['polynomial'])
            result = benchmark_polynomial_order(
                poly,
                test_case['field_order'],
                test_case.get('state_vector_dim', poly.degree()),
                test_case.get('expected_order')
            )
        elif benchmark_type == 'period_computation':
            result = benchmark_period_computation(
                test_case['coefficients'],
                test_case['field_order'],
                test_case.get('method', 'enumeration'),
                test_case.get('expected_period')
            )
        else:
            continue
        
        suite.results.append(result)
        total_time += result.execution_time
    
    suite.total_time = total_time
    suite.average_time = total_time / len(suite.results) if suite.results else 0.0
    
    return suite


def compare_methods(
    coefficients: List[int],
    field_order: int,
    expected_period: Optional[int] = None
) -> Dict[str, BenchmarkResult]:
    """
    Compare different period computation methods.
    
    This function runs multiple methods on the same input and compares
    their performance and accuracy.
    
    Args:
        coefficients: LFSR coefficients
        field_order: Field order
        expected_period: Optional expected period for verification
    
    Returns:
        Dictionary mapping method names to benchmark results
    """
    results = {}
    
    # Benchmark enumeration
    enum_result = benchmark_period_computation(
        coefficients, field_order, "enumeration", expected_period
    )
    results['enumeration'] = enum_result
    
    # Benchmark factorization
    try:
        factor_result = benchmark_period_computation(
            coefficients, field_order, "factorization", expected_period
        )
        results['factorization'] = factor_result
    except Exception:
        # Factorization may fail for some polynomials
        pass
    
    return results
