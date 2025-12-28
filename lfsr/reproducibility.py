#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Reproducibility features for LFSR analysis.

This module provides features to ensure research reproducibility, including
seed tracking, configuration export, and reproducibility reports.
"""

import json
import random
import sys
import platform
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

try:
    import sage
    SAGE_VERSION = sage.__version__
except ImportError:
    SAGE_VERSION = "not available"

try:
    import numpy
    NUMPY_VERSION = numpy.__version__
except ImportError:
    NUMPY_VERSION = "not available"


@dataclass
class ReproducibilityConfig:
    """
    Configuration for reproducible analysis.
    
    Attributes:
        random_seed: Random seed used
        python_version: Python version
        platform: Platform information
        dependencies: Dependency versions
        analysis_parameters: Analysis configuration
        timestamp: When analysis was performed
    """
    random_seed: Optional[int] = None
    python_version: str = ""
    platform: str = ""
    dependencies: Dict[str, str] = None
    analysis_parameters: Dict[str, Any] = None
    timestamp: str = ""


class ReproducibilityManager:
    """
    Manager for reproducibility features.
    
    This class provides functionality to ensure research reproducibility by
    tracking random seeds, configuration, and environment information.
    
    **Key Terminology**:
    
    - **Reproducibility**: The ability to reproduce research results using
      the same methods, data, and configuration. This is essential for
      scientific validity and verification.
    
    - **Random Seed**: A value used to initialize a random number generator,
      ensuring that random operations produce the same sequence of values.
      Tracking seeds enables reproducible random behavior.
    
    - **Configuration Export**: Saving all analysis parameters and settings
      to enable exact reproduction of results. This includes coefficients,
      field order, methods used, and other parameters.
    
    - **Environment Capture**: Recording system and dependency information
      (Python version, library versions, platform) to ensure compatibility
      when reproducing results.
    
    - **Reproducibility Report**: A document containing all information
      needed to reproduce research results, including configuration, seeds,
      and environment details.
    
    **Usage**:
    
        >>> manager = ReproducibilityManager()
        >>> manager.set_seed(42)
        >>> config = manager.capture_configuration(
        ...     coefficients=[1, 0, 0, 1],
        ...     field_order=2
        ... )
        >>> manager.export_config("config.json")
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize reproducibility manager.
        
        Args:
            seed: Optional random seed to set
        """
        self.seed = seed
        self.config: Optional[ReproducibilityConfig] = None
        
        if seed is not None:
            self.set_seed(seed)
    
    def set_seed(self, seed: int) -> None:
        """
        Set random seed for reproducibility.
        
        Args:
            seed: Random seed value
        """
        self.seed = seed
        random.seed(seed)
        
        # Also set numpy seed if available
        try:
            import numpy as np
            np.random.seed(seed)
        except ImportError:
            pass
    
    def get_seed(self) -> Optional[int]:
        """
        Get current random seed.
        
        Returns:
            Current seed or None
        """
        return self.seed
    
    def capture_environment(self) -> Dict[str, str]:
        """
        Capture environment information.
        
        Returns:
            Dictionary with environment details
        """
        return {
            'python_version': sys.version,
            'platform': platform.platform(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor(),
            'sage_version': SAGE_VERSION,
            'numpy_version': NUMPY_VERSION
        }
    
    def capture_configuration(
        self,
        analysis_parameters: Dict[str, Any],
        additional_info: Optional[Dict[str, Any]] = None
    ) -> ReproducibilityConfig:
        """
        Capture complete configuration for reproducibility.
        
        Args:
            analysis_parameters: Analysis parameters (coefficients, field_order, etc.)
            additional_info: Optional additional information
        
        Returns:
            ReproducibilityConfig with all captured information
        """
        env = self.capture_environment()
        
        dependencies = {
            'sage': SAGE_VERSION,
            'numpy': NUMPY_VERSION
        }
        
        if additional_info:
            dependencies.update(additional_info)
        
        self.config = ReproducibilityConfig(
            random_seed=self.seed,
            python_version=sys.version.split()[0],
            platform=platform.platform(),
            dependencies=dependencies,
            analysis_parameters=analysis_parameters,
            timestamp=datetime.now().isoformat()
        )
        
        return self.config
    
    def export_config(self, filename: str) -> None:
        """
        Export configuration to file.
        
        Args:
            filename: Output filename (JSON format)
        """
        if self.config is None:
            raise ValueError("No configuration captured. Call capture_configuration() first.")
        
        data = asdict(self.config)
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_config(self, filename: str) -> ReproducibilityConfig:
        """
        Load configuration from file.
        
        Args:
            filename: Input filename (JSON format)
        
        Returns:
            ReproducibilityConfig loaded from file
        """
        with open(filename, 'r') as f:
            data = json.load(f)
        
        self.config = ReproducibilityConfig(**data)
        
        # Restore seed if present
        if self.config.random_seed is not None:
            self.set_seed(self.config.random_seed)
        
        return self.config
    
    def generate_reproducibility_report(
        self,
        results_summary: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate reproducibility report.
        
        Args:
            results_summary: Optional summary of analysis results
        
        Returns:
            Reproducibility report as string
        """
        if self.config is None:
            return "No configuration available. Capture configuration first."
        
        report = []
        report.append("=" * 70)
        report.append("REPRODUCIBILITY REPORT")
        report.append("=" * 70)
        report.append("")
        report.append(f"Generated: {self.config.timestamp}")
        report.append("")
        
        report.append("Environment Information:")
        report.append("-" * 70)
        report.append(f"Python Version: {self.config.python_version}")
        report.append(f"Platform: {self.config.platform}")
        report.append("")
        
        report.append("Dependencies:")
        report.append("-" * 70)
        for dep, version in self.config.dependencies.items():
            report.append(f"  {dep}: {version}")
        report.append("")
        
        report.append("Random Seed:")
        report.append("-" * 70)
        if self.config.random_seed is not None:
            report.append(f"  Seed: {self.config.random_seed}")
            report.append("  Note: Set this seed before running analysis for reproducibility")
        else:
            report.append("  No seed set (non-deterministic)")
        report.append("")
        
        report.append("Analysis Parameters:")
        report.append("-" * 70)
        for key, value in self.config.analysis_parameters.items():
            report.append(f"  {key}: {value}")
        report.append("")
        
        if results_summary:
            report.append("Results Summary:")
            report.append("-" * 70)
            for key, value in results_summary.items():
                report.append(f"  {key}: {value}")
            report.append("")
        
        report.append("Reproducibility Instructions:")
        report.append("-" * 70)
        report.append("1. Ensure same Python version and dependencies")
        report.append("2. Set random seed if used in analysis")
        report.append("3. Use same analysis parameters")
        report.append("4. Run analysis with same configuration")
        report.append("")
        
        return "\n".join(report)
    
    def save_reproducibility_report(
        self,
        filename: str,
        results_summary: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Save reproducibility report to file.
        
        Args:
            filename: Output filename
            results_summary: Optional summary of analysis results
        """
        report = self.generate_reproducibility_report(results_summary)
        
        with open(filename, 'w') as f:
            f.write(report)
