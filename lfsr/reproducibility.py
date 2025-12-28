#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Reproducibility features for LFSR analysis.

This module provides features to ensure research reproducibility, including
seed tracking, configuration export, and environment capture.
"""

import json
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO
import hashlib
import random

from sage.all import *


def generate_reproducibility_seed() -> int:
    """
    Generate a reproducibility seed for deterministic execution.
    
    This function generates a seed that can be used to ensure reproducible
    results in analysis that involves randomness.
    
    **Key Terminology**:
    
    - **Reproducibility Seed**: A value used to initialize random number
      generators, ensuring that random operations produce the same sequence
      of values when the same seed is used.
    
    - **Deterministic Execution**: Execution that produces the same results
      when given the same inputs and seed, enabling exact reproduction of
      results.
    
    - **Research Reproducibility**: The ability to reproduce research results
      using the same methods, data, and configuration. This is essential for
      scientific validity.
    
    Returns:
        Integer seed value
    """
    # Generate seed from current timestamp (for uniqueness)
    # In practice, users should set a specific seed for reproducibility
    return int(datetime.now().timestamp() * 1000000) % (2**31)


def set_reproducibility_seed(seed: int) -> None:
    """
    Set seed for reproducible random number generation.
    
    Args:
        seed: Seed value to use
    """
    random.seed(seed)
    # SageMath uses Python's random, so this should be sufficient
    # Additional SageMath-specific seeding if needed


def capture_environment() -> Dict[str, Any]:
    """
    Capture environment information for reproducibility.
    
    This function captures system and software environment information
    needed to reproduce analysis results.
    
    **Key Terminology**:
    
    - **Environment Capture**: Recording system information, software versions,
      and configuration that might affect results.
    
    - **System Information**: Details about the computing environment including
      operating system, CPU, memory, and software versions.
    
    - **Dependency Tracking**: Recording versions of software libraries and
      dependencies used in the analysis.
    
    Returns:
        Dictionary with environment information
    """
    try:
        import sage
        sage_version = sage.__version__
    except (ImportError, AttributeError):
        sage_version = "unknown"
    
    try:
        import numpy
        numpy_version = numpy.__version__
    except (ImportError, AttributeError):
        numpy_version = "not installed"
    
    environment = {
        'timestamp': datetime.now().isoformat(),
        'python_version': sys.version,
        'platform': platform.platform(),
        'processor': platform.processor(),
        'system': platform.system(),
        'sage_version': sage_version,
        'numpy_version': numpy_version,
        'python_executable': sys.executable
    }
    
    return environment


def export_configuration(
    analysis_config: Dict[str, Any],
    output_file: Optional[TextIO] = None
) -> str:
    """
    Export complete analysis configuration for reproducibility.
    
    This function exports all configuration parameters needed to reproduce
    an analysis, including coefficients, field order, methods, and options.
    
    **Key Terminology**:
    
    - **Configuration Export**: Saving all parameters and settings used in
      an analysis to enable exact reproduction.
    
    - **Analysis Configuration**: All parameters, options, and settings that
      affect the results of an analysis.
    
    - **Reproducibility Report**: A document containing all information needed
      to reproduce research results.
    
    Args:
        analysis_config: Dictionary with analysis configuration
        output_file: Optional file to write configuration to
    
    Returns:
        JSON string with configuration
    """
    config = {
        'timestamp': datetime.now().isoformat(),
        'configuration': analysis_config,
        'environment': capture_environment()
    }
    
    config_json = json.dumps(config, indent=2)
    
    if output_file:
        output_file.write(config_json)
        output_file.write("\n")
    
    return config_json


def generate_reproducibility_report(
    analysis_config: Dict[str, Any],
    analysis_results: Dict[str, Any],
    seed: Optional[int] = None,
    output_file: Optional[TextIO] = None
) -> str:
    """
    Generate comprehensive reproducibility report.
    
    This function generates a complete reproducibility report including
    configuration, environment, results, and verification information.
    
    **Key Terminology**:
    
    - **Reproducibility Report**: A comprehensive document containing all
      information needed to reproduce research results, including configuration,
      environment, methods, and results.
    
    - **Research Reproducibility**: The ability to reproduce research results
      using the same methods, data, and configuration. Essential for scientific
      validity and peer review.
    
    - **Verification Information**: Data that can be used to verify that
      reproduced results match the original results.
    
    Args:
        analysis_config: Analysis configuration
        analysis_results: Analysis results
        seed: Optional seed used for reproducibility
        output_file: Optional file to write report to
    
    Returns:
        JSON string with reproducibility report
    """
    report = {
        'report_type': 'reproducibility_report',
        'timestamp': datetime.now().isoformat(),
        'seed': seed,
        'configuration': analysis_config,
        'environment': capture_environment(),
        'results': analysis_results,
        'reproducibility_notes': [
            'This report contains all information needed to reproduce the analysis.',
            'Use the same configuration, environment, and seed to reproduce results.',
            'Verify results match by comparing result hashes or values.'
        ]
    }
    
    # Compute result hash for verification
    results_str = json.dumps(analysis_results, sort_keys=True)
    result_hash = hashlib.sha256(results_str.encode()).hexdigest()
    report['result_hash'] = result_hash
    
    report_json = json.dumps(report, indent=2)
    
    if output_file:
        output_file.write(report_json)
        output_file.write("\n")
    
    return report_json


def load_configuration(
    config_file: str
) -> Dict[str, Any]:
    """
    Load analysis configuration from file.
    
    Args:
        config_file: Path to configuration file
    
    Returns:
        Dictionary with configuration
    """
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    return config.get('configuration', config)


def verify_reproducibility(
    original_results: Dict[str, Any],
    reproduced_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify that reproduced results match original results.
    
    This function compares original and reproduced results to verify
    that reproduction was successful.
    
    **Key Terminology**:
    
    - **Result Verification**: Comparing reproduced results with original
      results to ensure they match exactly.
    
    - **Reproducibility Verification**: Confirming that reproduced results
      match the original results, validating the reproducibility process.
    
    Args:
        original_results: Original analysis results
        reproduced_results: Reproduced analysis results
    
    Returns:
        Dictionary with verification status and details
    """
    # Compute hashes for comparison
    original_str = json.dumps(original_results, sort_keys=True)
    reproduced_str = json.dumps(reproduced_results, sort_keys=True)
    
    original_hash = hashlib.sha256(original_str.encode()).hexdigest()
    reproduced_hash = hashlib.sha256(reproduced_str.encode()).hexdigest()
    
    matches = original_hash == reproduced_hash
    
    verification = {
        'verified': matches,
        'original_hash': original_hash,
        'reproduced_hash': reproduced_hash,
        'message': 'Results match exactly' if matches else 'Results do not match'
    }
    
    # Detailed comparison if hashes don't match
    if not matches:
        verification['differences'] = _compare_results(
            original_results, reproduced_results
        )
    
    return verification


def _compare_results(
    original: Dict[str, Any],
    reproduced: Dict[str, Any],
    path: str = ""
) -> List[str]:
    """
    Compare two result dictionaries and find differences.
    
    Args:
        original: Original results
        reproduced: Reproduced results
        path: Current path in nested structure
    
    Returns:
        List of difference descriptions
    """
    differences = []
    
    # Check keys
    original_keys = set(original.keys())
    reproduced_keys = set(reproduced.keys())
    
    missing = original_keys - reproduced_keys
    extra = reproduced_keys - original_keys
    
    for key in missing:
        differences.append(f"Missing key: {path}.{key}" if path else f"Missing key: {key}")
    
    for key in extra:
        differences.append(f"Extra key: {path}.{key}" if path else f"Extra key: {key}")
    
    # Compare common keys
    for key in original_keys & reproduced_keys:
        current_path = f"{path}.{key}" if path else key
        orig_val = original[key]
        repro_val = reproduced[key]
        
        if isinstance(orig_val, dict) and isinstance(repro_val, dict):
            differences.extend(_compare_results(orig_val, repro_val, current_path))
        elif orig_val != repro_val:
            differences.append(f"Value mismatch at {current_path}: {orig_val} != {repro_val}")
    
    return differences
