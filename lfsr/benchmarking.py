#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Benchmarking framework for LFSR analysis.

This module provides benchmarking capabilities for comparing performance,
accuracy, and results across different analysis methods.
"""

import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json

from sage.all import *


@dataclass
class BenchmarkResult:
    """
    Result from a single benchmark run.
    
    Attributes:
        method: Method name (e.g., "enumeration", "factorization")
        coefficients: LFSR coefficients
        field_order: Field order
        degree: LFSR degree
        execution_time: Execution time in seconds
        memory_usage: Memory usage in bytes (optional)
        result: Analysis result
        accuracy: Accuracy metric (optional)
        error: Error message if benchmark failed
    """
    method: str
    coefficients: List[int]
    field_order: int
    degree: int
    execution_time: float
    memory_usage: Optional[int] = None
    result: Optional[Any] = None
    accuracy: Optional[float] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class BenchmarkSuite:
    """
    Collection of benchmark results.
    
    Attributes:
        name: Suite name
        description: Suite description
        results: List of benchmark results
        metadata: Additional metadata
    """
    name: str
    description: str
    results: List[BenchmarkResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


def benchmark_period_computation(
    coefficients: List[int],
    field_order: int,
    methods: Optional[List[str]] = None
) -> List[BenchmarkResult]:
    """
    Benchmark period computation using different methods.
    
    This function compares performance and accuracy of different period
    computation methods (enumeration, factorization, etc.).
    
    **Key Terminology**:
    
    - **Benchmarking**: The process of measuring and comparing performance
      or accuracy of different methods or implementations.
    
    - **Performance Benchmark**: Measuring execution time, memory usage,
      or other resource consumption metrics.
    
    - **Accuracy Benchmark**: Comparing results to verify correctness
      and measure accuracy differences between methods.
    
    - **Method Comparison**: Comparing different algorithms or approaches
      to solve the same problem, evaluating trade-offs.
    
    Args:
        coefficients: LFSR coefficients
        field_order: Field order
        methods: List of methods to benchmark (default: ["enumeration", "factorization"])
    
    Returns:
        List of BenchmarkResult objects
    """
    if methods is None:
        methods = ["enumeration", "factorization"]
    
    results = []
    degree = len(coefficients)
    
    for method in methods:
        start_time = time.time()
        error = None
        result = None
        
        try:
            if method == "enumeration":
                from lfsr.core import find_sequence_cycle_enumeration
                # Use a sample initial state
                initial_state = [1] + [0] * (degree - 1)
                period, _ = find_sequence_cycle_enumeration(
                    coefficients, field_order, initial_state
                )
                result = period
            
            elif method == "factorization":
                from lfsr.polynomial import compute_period_via_factorization
                result = compute_period_via_factorization(
                    coefficients, field_order, degree
                )
            
            execution_time = time.time() - start_time
            
        except Exception as e:
            execution_time = time.time() - start_time
            error = str(e)
        
        benchmark_result = BenchmarkResult(
            method=method,
            coefficients=coefficients,
            field_order=field_order,
            degree=degree,
            execution_time=execution_time,
            result=result,
            error=error
        )
        
        results.append(benchmark_result)
    
    # Compute accuracy by comparing results
    valid_results = [r for r in results if r.result is not None and r.error is None]
    if len(valid_results) > 1:
        # All results should match
        reference = valid_results[0].result
        for r in valid_results[1:]:
            if r.result == reference:
                r.accuracy = 1.0
            else:
                r.accuracy = 0.0
    
    return results


def benchmark_polynomial_analysis(
    coefficients: List[int],
    field_order: int
) -> BenchmarkResult:
    """
    Benchmark polynomial analysis operations.
    
    This function measures performance of polynomial analysis including
    order computation, primitivity checking, and factorization.
    
    Args:
        coefficients: LFSR coefficients
        field_order: Field order
    
    Returns:
        BenchmarkResult for polynomial analysis
    """
    from lfsr.polynomial import (
        compute_characteristic_polynomial,
        polynomial_order,
        is_primitive_polynomial
    )
    
    start_time = time.time()
    error = None
    result = {}
    
    try:
        char_poly = compute_characteristic_polynomial(coefficients, field_order)
        degree = len(coefficients)
        
        poly_order = polynomial_order(char_poly, degree, field_order)
        is_primitive = is_primitive_polynomial(char_poly, field_order)
        
        result = {
            'order': int(poly_order) if poly_order != oo else None,
            'is_primitive': is_primitive
        }
        
        execution_time = time.time() - start_time
        
    except Exception as e:
        execution_time = time.time() - start_time
        error = str(e)
    
    return BenchmarkResult(
        method="polynomial_analysis",
        coefficients=coefficients,
        field_order=field_order,
        degree=len(coefficients),
        execution_time=execution_time,
        result=result,
        error=error
    )


def compare_benchmark_results(
    results: List[BenchmarkResult]
) -> Dict[str, Any]:
    """
    Compare benchmark results and generate comparison report.
    
    This function analyzes benchmark results to identify the fastest method,
    accuracy differences, and performance trade-offs.
    
    **Key Terminology**:
    
    - **Performance Comparison**: Analyzing execution times to identify
      the fastest or most efficient method.
    
    - **Trade-off Analysis**: Evaluating the balance between different
      metrics (e.g., speed vs. accuracy, memory vs. time).
    
    - **Benchmark Report**: Summary of benchmark results with comparisons
      and recommendations.
    
    Args:
        results: List of benchmark results to compare
    
    Returns:
        Dictionary with comparison analysis
    """
    valid_results = [r for r in results if r.error is None]
    
    if not valid_results:
        return {
            'status': 'error',
            'message': 'No valid benchmark results to compare'
        }
    
    # Find fastest method
    fastest = min(valid_results, key=lambda r: r.execution_time)
    
    # Find slowest method
    slowest = max(valid_results, key=lambda r: r.execution_time)
    
    # Check if results match
    results_match = True
    if len(valid_results) > 1:
        reference_result = valid_results[0].result
        for r in valid_results[1:]:
            if r.result != reference_result:
                results_match = False
                break
    
    comparison = {
        'status': 'success',
        'total_methods': len(results),
        'valid_methods': len(valid_results),
        'fastest_method': fastest.method,
        'fastest_time': fastest.execution_time,
        'slowest_method': slowest.method,
        'slowest_time': slowest.execution_time,
        'speedup': slowest.execution_time / fastest.execution_time if fastest.execution_time > 0 else None,
        'results_match': results_match,
        'method_details': [
            {
                'method': r.method,
                'time': r.execution_time,
                'result': r.result,
                'accuracy': r.accuracy
            }
            for r in valid_results
        ]
    }
    
    return comparison


def save_benchmark_suite(
    suite: BenchmarkSuite,
    filename: str
) -> None:
    """
    Save benchmark suite to JSON file.
    
    Args:
        suite: BenchmarkSuite to save
        filename: Output filename
    """
    data = {
        'name': suite.name,
        'description': suite.description,
        'timestamp': suite.timestamp,
        'metadata': suite.metadata,
        'results': [asdict(r) for r in suite.results]
    }
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)


def load_benchmark_suite(
    filename: str
) -> BenchmarkSuite:
    """
    Load benchmark suite from JSON file.
    
    Args:
        filename: Input filename
    
    Returns:
        BenchmarkSuite object
    """
    with open(filename, 'r') as f:
        data = json.load(f)
    
    results = [
        BenchmarkResult(**r) for r in data['results']
    ]
    
    return BenchmarkSuite(
        name=data['name'],
        description=data['description'],
        results=results,
        metadata=data.get('metadata', {}),
        timestamp=data.get('timestamp', '')
    )
