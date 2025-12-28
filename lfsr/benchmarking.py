#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Benchmarking framework for LFSR analysis.

This module provides benchmarking capabilities for comparing performance,
accuracy, and results across different analysis methods and configurations.
"""

import time
import json
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from sage.all import *


@dataclass
class BenchmarkResult:
    """
    Result from a single benchmark run.
    
    Attributes:
        method: Analysis method used
        configuration: Configuration parameters
        execution_time: Execution time in seconds
        memory_usage: Memory usage in bytes (optional)
        result_accuracy: Accuracy metric (optional)
        result_value: Actual result value
        error_message: Error message if benchmark failed
        timestamp: When benchmark was run
    """
    method: str
    configuration: Dict[str, Any]
    execution_time: float
    memory_usage: Optional[int] = None
    result_accuracy: Optional[float] = None
    result_value: Optional[Any] = None
    error_message: Optional[str] = None
    timestamp: str = ""


class BenchmarkSuite:
    """
    Benchmarking framework for LFSR analysis.
    
    This class provides a framework for benchmarking different analysis
    methods, comparing performance, and tracking results over time.
    
    **Key Terminology**:
    
    - **Benchmarking**: The process of measuring and comparing the performance
      of different methods or configurations. Benchmarks help identify the most
      efficient approaches and track performance over time.
    
    - **Performance Metrics**: Quantitative measures of performance, such as
      execution time, memory usage, and computational complexity. These metrics
      help evaluate and compare different methods.
    
    - **Regression Testing**: Testing to ensure that changes don't degrade
      performance. Benchmarking helps detect performance regressions.
    
    - **Accuracy Benchmark**: Comparing computed results with known correct
      results to verify accuracy. This ensures methods produce correct results.
    
    **Usage**:
    
        >>> suite = BenchmarkSuite()
        >>> result = suite.benchmark_period_computation(
        ...     coefficients=[1, 0, 0, 1],
        ...     field_order=2,
        ...     method="enumeration"
        ... )
        >>> suite.save_results("benchmark_results.json")
    """
    
    def __init__(self):
        """Initialize benchmark suite."""
        self.results: List[BenchmarkResult] = []
    
    def benchmark_period_computation(
        self,
        coefficients: List[int],
        field_order: int,
        method: str = "enumeration",
        state_vector_dim: Optional[int] = None
    ) -> BenchmarkResult:
        """
        Benchmark period computation method.
        
        Args:
            coefficients: LFSR coefficients
            field_order: Field order
            method: Method to use ("enumeration", "factorization", etc.)
            state_vector_dim: Optional state vector dimension
        
        Returns:
            BenchmarkResult with execution time and result
        """
        from lfsr.core import find_sequence_cycle
        from lfsr.polynomial import compute_period_via_factorization
        
        config = {
            'coefficients': coefficients,
            'field_order': field_order,
            'method': method,
            'state_vector_dim': state_vector_dim
        }
        
        start_time = time.time()
        error_message = None
        result_value = None
        
        try:
            if method == "enumeration":
                # Use enumeration method
                if state_vector_dim is None:
                    state_vector_dim = len(coefficients)
                # Simple benchmark: compute period for first non-zero state
                initial_state = [1] + [0] * (state_vector_dim - 1)
                cycle_result = find_sequence_cycle(
                    coefficients,
                    field_order,
                    initial_state,
                    method="enumeration"
                )
                result_value = cycle_result.get('period')
            elif method == "factorization":
                # Use factorization method
                result_value = compute_period_via_factorization(
                    coefficients,
                    field_order,
                    state_vector_dim
                )
            else:
                error_message = f"Unknown method: {method}"
        except Exception as e:
            error_message = str(e)
        
        execution_time = time.time() - start_time
        
        return BenchmarkResult(
            method=method,
            configuration=config,
            execution_time=execution_time,
            result_value=result_value,
            error_message=error_message,
            timestamp=datetime.now().isoformat()
        )
    
    def benchmark_polynomial_analysis(
        self,
        coefficients: List[int],
        field_order: int
    ) -> BenchmarkResult:
        """
        Benchmark polynomial analysis operations.
        
        Args:
            coefficients: LFSR coefficients
            field_order: Field order
        
        Returns:
            BenchmarkResult with execution time
        """
        from lfsr.polynomial import (
            compute_characteristic_polynomial,
            is_primitive_polynomial,
            polynomial_order
        )
        
        config = {
            'coefficients': coefficients,
            'field_order': field_order
        }
        
        start_time = time.time()
        error_message = None
        result_value = None
        
        try:
            char_poly = compute_characteristic_polynomial(coefficients, field_order)
            is_primitive = is_primitive_polynomial(char_poly, field_order)
            order = polynomial_order(char_poly, len(coefficients), field_order)
            
            result_value = {
                'is_primitive': is_primitive,
                'order': int(order) if order != oo else None
            }
        except Exception as e:
            error_message = str(e)
        
        execution_time = time.time() - start_time
        
        return BenchmarkResult(
            method="polynomial_analysis",
            configuration=config,
            execution_time=execution_time,
            result_value=result_value,
            error_message=error_message,
            timestamp=datetime.now().isoformat()
        )
    
    def compare_methods(
        self,
        coefficients: List[int],
        field_order: int,
        methods: List[str]
    ) -> Dict[str, Any]:
        """
        Compare multiple methods on the same configuration.
        
        Args:
            coefficients: LFSR coefficients
            field_order: Field order
            methods: List of methods to compare
        
        Returns:
            Dictionary with comparison results
        """
        results = {}
        
        for method in methods:
            result = self.benchmark_period_computation(
                coefficients,
                field_order,
                method=method
            )
            results[method] = result
            self.results.append(result)
        
        # Find fastest method
        valid_results = {
            k: v for k, v in results.items()
            if v.error_message is None
        }
        
        if valid_results:
            fastest = min(valid_results.items(), key=lambda x: x[1].execution_time)
            comparison = {
                'methods_tested': list(results.keys()),
                'fastest_method': fastest[0],
                'fastest_time': fastest[1].execution_time,
                'results': {k: asdict(v) for k, v in results.items()},
                'all_succeeded': all(r.error_message is None for r in results.values())
            }
        else:
            comparison = {
                'methods_tested': list(results.keys()),
                'fastest_method': None,
                'fastest_time': None,
                'results': {k: asdict(v) for k, v in results.items()},
                'all_succeeded': False
            }
        
        return comparison
    
    def save_results(self, filename: str) -> None:
        """
        Save benchmark results to file.
        
        Args:
            filename: Output filename (JSON format)
        """
        data = {
            'benchmark_results': [asdict(r) for r in self.results],
            'total_runs': len(self.results),
            'generated_at': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_results(self, filename: str) -> None:
        """
        Load benchmark results from file.
        
        Args:
            filename: Input filename (JSON format)
        """
        with open(filename, 'r') as f:
            data = json.load(f)
        
        self.results = [
            BenchmarkResult(**r) for r in data.get('benchmark_results', [])
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about benchmark results.
        
        Returns:
            Dictionary with statistics
        """
        if not self.results:
            return {'total_runs': 0}
        
        valid_results = [r for r in self.results if r.error_message is None]
        
        if not valid_results:
            return {
                'total_runs': len(self.results),
                'successful_runs': 0,
                'failed_runs': len(self.results)
            }
        
        execution_times = [r.execution_time for r in valid_results]
        
        return {
            'total_runs': len(self.results),
            'successful_runs': len(valid_results),
            'failed_runs': len(self.results) - len(valid_results),
            'avg_execution_time': sum(execution_times) / len(execution_times),
            'min_execution_time': min(execution_times),
            'max_execution_time': max(execution_times),
            'methods_used': list(set(r.method for r in self.results))
        }
