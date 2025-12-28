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
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

from sage.all import *


@dataclass
class BenchmarkResult:
    """
    Result from a single benchmark run.
    
    Attributes:
        method: Method name being benchmarked
        configuration: Configuration parameters
        execution_time: Execution time in seconds
        memory_usage: Memory usage (if available)
        result: The computed result
        accuracy: Accuracy metric (if applicable)
        success: Whether benchmark succeeded
        error: Error message if failed
        timestamp: When benchmark was run
    """
    method: str
    configuration: Dict[str, Any]
    execution_time: float
    memory_usage: Optional[float] = None
    result: Any = None
    accuracy: Optional[float] = None
    success: bool = True
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


class BenchmarkFramework:
    """
    Framework for benchmarking LFSR analysis methods.
    
    This class provides a comprehensive benchmarking framework for comparing
    different analysis methods, measuring performance, and tracking accuracy.
    
    **Key Terminology**:
    
    - **Benchmarking**: The process of measuring and comparing the performance
      of different methods or implementations. This includes execution time,
      memory usage, and accuracy metrics.
    
    - **Performance Benchmark**: Measurement of how fast a method executes,
      typically measured in seconds or operations per second.
    
    - **Accuracy Benchmark**: Measurement of how correct a method's results are,
      typically compared against known correct results or theoretical predictions.
    
    - **Regression Testing**: Running benchmarks to detect performance or
      accuracy regressions when code changes are made.
    
    **Benchmark Types**:
    
    1. **Performance Benchmarks**: Measure execution time and resource usage
    2. **Accuracy Benchmarks**: Compare results with known correct values
    3. **Scalability Benchmarks**: Measure performance across different input sizes
    4. **Method Comparison**: Compare different methods on the same inputs
    
    Example:
        >>> framework = BenchmarkFramework()
        >>> result = framework.benchmark_method(
        ...     "enumeration",
        ...     {"coefficients": [1, 0, 0, 1], "field_order": 2},
        ...     lambda: compute_period_enumeration([1, 0, 0, 1], 2)
        ... )
        >>> print(f"Execution time: {result.execution_time:.4f}s")
    """
    
    def __init__(self):
        """Initialize benchmarking framework."""
        self.suites: Dict[str, BenchmarkSuite] = {}
    
    def benchmark_method(
        self,
        method_name: str,
        configuration: Dict[str, Any],
        function: callable,
        expected_result: Optional[Any] = None,
        accuracy_function: Optional[callable] = None
    ) -> BenchmarkResult:
        """
        Benchmark a single method execution.
        
        Args:
            method_name: Name of the method being benchmarked
            configuration: Configuration parameters
            function: Function to benchmark (should be callable with no args)
            expected_result: Expected result for accuracy checking
            accuracy_function: Function to compute accuracy (takes computed, expected)
        
        Returns:
            BenchmarkResult with execution metrics
        """
        start_time = time.time()
        result = None
        error = None
        success = True
        
        try:
            result = function()
            execution_time = time.time() - start_time
        except Exception as e:
            execution_time = time.time() - start_time
            error = str(e)
            success = False
        
        # Compute accuracy if applicable
        accuracy = None
        if success and expected_result is not None and result is not None:
            if accuracy_function:
                accuracy = accuracy_function(result, expected_result)
            elif result == expected_result:
                accuracy = 1.0
            else:
                accuracy = 0.0
        
        return BenchmarkResult(
            method=method_name,
            configuration=configuration,
            execution_time=execution_time,
            result=result,
            accuracy=accuracy,
            success=success,
            error=error
        )
    
    def compare_methods(
        self,
        methods: List[Tuple[str, Dict[str, Any], callable]],
        expected_result: Optional[Any] = None
    ) -> List[BenchmarkResult]:
        """
        Compare multiple methods on the same configuration.
        
        Args:
            methods: List of (method_name, configuration, function) tuples
            expected_result: Expected result for accuracy checking
        
        Returns:
            List of benchmark results for each method
        """
        results = []
        
        for method_name, config, function in methods:
            result = self.benchmark_method(
                method_name,
                config,
                function,
                expected_result
            )
            results.append(result)
        
        return results
    
    def create_suite(
        self,
        name: str,
        description: str = ""
    ) -> BenchmarkSuite:
        """
        Create a new benchmark suite.
        
        Args:
            name: Suite name
            description: Suite description
        
        Returns:
            Created BenchmarkSuite
        """
        suite = BenchmarkSuite(name=name, description=description)
        self.suites[name] = suite
        return suite
    
    def add_to_suite(
        self,
        suite_name: str,
        result: BenchmarkResult
    ) -> None:
        """
        Add benchmark result to a suite.
        
        Args:
            suite_name: Name of the suite
            result: Benchmark result to add
        """
        if suite_name not in self.suites:
            self.create_suite(suite_name)
        
        self.suites[suite_name].results.append(result)
    
    def get_suite_summary(
        self,
        suite_name: str
    ) -> Dict[str, Any]:
        """
        Get summary statistics for a benchmark suite.
        
        Args:
            suite_name: Name of the suite
        
        Returns:
            Dictionary with summary statistics
        """
        if suite_name not in self.suites:
            return {}
        
        suite = self.suites[suite_name]
        results = suite.results
        
        if not results:
            return {'count': 0}
        
        successful = [r for r in results if r.success]
        times = [r.execution_time for r in successful]
        accuracies = [r.accuracy for r in successful if r.accuracy is not None]
        
        summary = {
            'suite_name': suite_name,
            'total_runs': len(results),
            'successful_runs': len(successful),
            'failed_runs': len(results) - len(successful),
            'avg_time': sum(times) / len(times) if times else 0.0,
            'min_time': min(times) if times else 0.0,
            'max_time': max(times) if times else 0.0,
            'avg_accuracy': sum(accuracies) / len(accuracies) if accuracies else None,
        }
        
        return summary
    
    def export_suite(
        self,
        suite_name: str,
        filename: str
    ) -> None:
        """
        Export benchmark suite to JSON file.
        
        Args:
            suite_name: Name of the suite
            filename: Output filename
        """
        if suite_name not in self.suites:
            raise ValueError(f"Suite '{suite_name}' not found")
        
        suite = self.suites[suite_name]
        
        # Convert to serializable format
        data = {
            'name': suite.name,
            'description': suite.description,
            'metadata': suite.metadata,
            'results': [asdict(r) for r in suite.results],
            'summary': self.get_suite_summary(suite_name)
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def load_suite(
        self,
        filename: str
    ) -> BenchmarkSuite:
        """
        Load benchmark suite from JSON file.
        
        Args:
            filename: Input filename
        
        Returns:
            Loaded BenchmarkSuite
        """
        with open(filename, 'r') as f:
            data = json.load(f)
        
        suite = BenchmarkSuite(
            name=data['name'],
            description=data.get('description', ''),
            metadata=data.get('metadata', {})
        )
        
        for r_data in data.get('results', []):
            result = BenchmarkResult(**r_data)
            suite.results.append(result)
        
        self.suites[suite.name] = suite
        return suite
