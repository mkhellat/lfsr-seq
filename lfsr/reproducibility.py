#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Reproducibility features for LFSR analysis.

This module provides functionality to ensure reproducibility of analysis
results through seed tracking, configuration export, and environment capture.
"""

import json
import os
import platform
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, TextIO
from pathlib import Path

try:
    import pkg_resources
    HAS_PKG_RESOURCES = True
except ImportError:
    HAS_PKG_RESOURCES = False


def generate_seed() -> int:
    """
    Generate a random seed for reproducibility.
    
    This function generates a seed that can be used to ensure reproducible
    random number generation in analysis.
    
    **Key Terminology**:
    
    - **Random Seed**: A value used to initialize a random number generator,
      ensuring that the same seed produces the same sequence of random numbers.
      This enables reproducibility of results that depend on randomness.
    
    - **Reproducibility**: The ability to reproduce research results using
      the same methods, data, and parameters. This is essential for scientific
      validity and verification.
    
    Returns:
        Random seed value
    """
    import random
    return random.randint(0, 2**31 - 1)


def capture_environment() -> Dict[str, Any]:
    """
    Capture environment information for reproducibility.
    
    This function captures system and software environment information
    needed to reproduce analysis results.
    
    **Key Terminology**:
    
    - **Environment Capture**: Recording information about the computing
      environment, including operating system, Python version, and package
      versions. This enables others to reproduce results in similar environments.
    
    - **Dependency Tracking**: Recording versions of software dependencies
      to ensure compatibility and reproducibility.
    
    Returns:
        Dictionary with environment information
    """
    env = {
        'timestamp': datetime.now().isoformat(),
        'platform': {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor()
        },
        'python': {
            'version': sys.version,
            'executable': sys.executable,
            'path': sys.path
        },
        'packages': {}
    }
    
    # Capture package versions
    if HAS_PKG_RESOURCES:
        try:
            packages = ['sage', 'numpy', 'scipy']
            for pkg_name in packages:
                try:
                    pkg = pkg_resources.get_distribution(pkg_name)
                    env['packages'][pkg_name] = pkg.version
                except pkg_resources.DistributionNotFound:
                    pass
        except Exception:
            pass
    
    return env


def export_configuration(
    analysis_config: Dict[str, Any],
    output_file: Optional[TextIO] = None
) -> str:
    """
    Export analysis configuration for reproducibility.
    
    This function exports the complete configuration used for analysis,
    enabling others to reproduce the exact same analysis.
    
    **Key Terminology**:
    
    - **Configuration Export**: Saving all parameters and settings used
      in an analysis, including input data, method choices, and options.
      This is essential for reproducibility.
    
    - **Reproducibility Report**: A document containing all information
      needed to reproduce research results, including configuration,
      environment, and execution parameters.
    
    Args:
        analysis_config: Dictionary with analysis configuration
        output_file: Optional file to write configuration to
    
    Returns:
        JSON string with configuration
    """
    config = {
        'analysis_config': analysis_config,
        'environment': capture_environment(),
        'export_timestamp': datetime.now().isoformat()
    }
    
    config_json = json.dumps(config, indent=2, ensure_ascii=False)
    
    if output_file:
        output_file.write(config_json)
        output_file.write("\n")
    
    return config_json


def generate_reproducibility_report(
    analysis_results: Dict[str, Any],
    analysis_config: Dict[str, Any],
    seed: Optional[int] = None,
    output_file: Optional[TextIO] = None
) -> str:
    """
    Generate comprehensive reproducibility report.
    
    This function generates a complete reproducibility report containing
    all information needed to reproduce the analysis.
    
    **Key Terminology**:
    
    - **Reproducibility Report**: A comprehensive document containing
      all information needed to reproduce research results, including:
      - Configuration and parameters
      - Environment information
      - Input data
      - Execution details
      - Results summary
    
    - **Scientific Reproducibility**: The ability of other researchers
      to reproduce published results using the same methods and data.
      This is a fundamental requirement for scientific validity.
    
    Args:
        analysis_results: Dictionary with analysis results
        analysis_config: Dictionary with analysis configuration
        seed: Optional random seed used
        output_file: Optional file to write report to
    
    Returns:
        Reproducibility report as string
    """
    report = {
        'report_type': 'reproducibility_report',
        'generated': datetime.now().isoformat(),
        'seed': seed,
        'configuration': analysis_config,
        'environment': capture_environment(),
        'results_summary': {
            'field_order': analysis_results.get('field_order'),
            'lfsr_degree': analysis_results.get('lfsr_degree'),
            'max_period': analysis_results.get('max_period'),
            'is_primitive': analysis_results.get('is_primitive')
        },
        'reproducibility_instructions': {
            'step1': 'Install required packages with versions specified in environment section',
            'step2': 'Load configuration from configuration section',
            'step3': 'Set random seed if provided',
            'step4': 'Run analysis with specified parameters',
            'step5': 'Compare results with results_summary section'
        }
    }
    
    report_json = json.dumps(report, indent=2, ensure_ascii=False)
    
    if output_file:
        output_file.write(report_json)
        output_file.write("\n")
    
    return report_json


def save_reproducibility_report(
    analysis_results: Dict[str, Any],
    analysis_config: Dict[str, Any],
    filename: str,
    seed: Optional[int] = None
) -> None:
    """
    Save reproducibility report to file.
    
    Convenience function to save reproducibility report directly to a file.
    
    Args:
        analysis_results: Dictionary with analysis results
        analysis_config: Dictionary with analysis configuration
        filename: Output filename
        seed: Optional random seed used
    """
    with open(filename, 'w', encoding='utf-8') as f:
        generate_reproducibility_report(
            analysis_results,
            analysis_config,
            seed,
            output_file=f
        )
