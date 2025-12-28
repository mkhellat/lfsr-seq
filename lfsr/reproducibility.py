#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Reproducibility features for LFSR analysis.

This module provides features to ensure research reproducibility, including
seed tracking, configuration export, and environment capture.
"""

import json
import random
import sys
import platform
from typing import Any, Dict, List, Optional, TextIO
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import hashlib

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
    Configuration for reproducibility tracking.
    
    Attributes:
        random_seed: Random seed used for analysis
        python_version: Python version
        platform: Platform information
        dependencies: Dictionary of dependency versions
        analysis_parameters: Analysis configuration parameters
        timestamp: When analysis was performed
        git_commit: Git commit hash (if available)
    """
    random_seed: Optional[int] = None
    python_version: str = field(default_factory=lambda: sys.version)
    platform: str = field(default_factory=lambda: platform.platform())
    dependencies: Dict[str, str] = field(default_factory=dict)
    analysis_parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    git_commit: Optional[str] = None


class ReproducibilityTracker:
    """
    Tracks reproducibility information for analysis runs.
    
    This class provides comprehensive tracking of all information needed to
    reproduce analysis results, including random seeds, configuration parameters,
    environment information, and dependency versions.
    
    **Key Terminology**:
    
    - **Reproducibility**: The ability to reproduce research results using the
      same methods, data, and environment. This is essential for scientific
      validity and peer review.
    
    - **Random Seed**: A value used to initialize a pseudorandom number generator,
      ensuring that random operations produce the same sequence of values when
      the same seed is used. This is crucial for reproducibility.
    
    - **Configuration Export**: Saving all analysis parameters and settings
      so that the exact same analysis can be rerun later.
    
    - **Environment Capture**: Recording information about the computing
      environment, including software versions, operating system, and hardware
      specifications.
    
    - **Reproducibility Report**: A document containing all information needed
      to reproduce research results, including configuration, environment, and
      execution parameters.
    
    Example:
        >>> tracker = ReproducibilityTracker()
        >>> tracker.set_seed(42)
        >>> tracker.add_parameter("field_order", 2)
        >>> config = tracker.get_config()
        >>> report = tracker.generate_report()
    """
    
    def __init__(self):
        """Initialize reproducibility tracker."""
        self.config = ReproducibilityConfig()
        self.config.dependencies = {
            'python': sys.version.split()[0],
            'sage': SAGE_VERSION,
            'numpy': NUMPY_VERSION
        }
        self._try_get_git_commit()
    
    def _try_get_git_commit(self):
        """Try to get current git commit hash."""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.config.git_commit = result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass
    
    def set_seed(self, seed: Optional[int] = None):
        """
        Set random seed for reproducibility.
        
        Args:
            seed: Random seed (if None, generates a new seed)
        """
        if seed is None:
            seed = random.randint(0, 2**31 - 1)
        
        self.config.random_seed = seed
        random.seed(seed)
        
        # Also set SageMath random seed if available
        try:
            from sage.all import set_random_seed
            set_random_seed(seed)
        except (ImportError, AttributeError):
            pass
    
    def get_seed(self) -> Optional[int]:
        """
        Get current random seed.
        
        Returns:
            Current random seed
        """
        return self.config.random_seed
    
    def add_parameter(self, name: str, value: Any):
        """
        Add analysis parameter.
        
        Args:
            name: Parameter name
            value: Parameter value
        """
        self.config.analysis_parameters[name] = value
    
    def add_parameters(self, parameters: Dict[str, Any]):
        """
        Add multiple analysis parameters.
        
        Args:
            parameters: Dictionary of parameters
        """
        self.config.analysis_parameters.update(parameters)
    
    def get_config(self) -> ReproducibilityConfig:
        """
        Get current reproducibility configuration.
        
        Returns:
            ReproducibilityConfig object
        """
        return self.config
    
    def export_config(self, filename: str):
        """
        Export configuration to JSON file.
        
        Args:
            filename: Output filename
        """
        config_dict = asdict(self.config)
        
        # Convert non-serializable values
        def convert_value(v):
            if isinstance(v, (dict, list, str, int, float, bool, type(None))):
                return v
            return str(v)
        
        def convert_dict(d):
            if isinstance(d, dict):
                return {k: convert_value(v) for k, v in d.items()}
            return convert_value(d)
        
        config_dict = convert_dict(config_dict)
        
        with open(filename, 'w') as f:
            json.dump(config_dict, f, indent=2, default=str)
    
    def load_config(self, filename: str) -> ReproducibilityConfig:
        """
        Load configuration from JSON file.
        
        Args:
            filename: Input filename
        
        Returns:
            Loaded ReproducibilityConfig
        """
        with open(filename, 'r') as f:
            config_dict = json.load(f)
        
        self.config = ReproducibilityConfig(**config_dict)
        return self.config
    
    def generate_report(self, output_file: Optional[TextIO] = None) -> str:
        """
        Generate reproducibility report.
        
        Args:
            output_file: Optional file to write report to
        
        Returns:
            Report as string
        """
        report_lines = []
        
        report_lines.append("=" * 70)
        report_lines.append("Reproducibility Report")
        report_lines.append("=" * 70)
        report_lines.append("")
        
        report_lines.append("Timestamp:")
        report_lines.append(f"  {self.config.timestamp}")
        report_lines.append("")
        
        if self.config.random_seed is not None:
            report_lines.append("Random Seed:")
            report_lines.append(f"  {self.config.random_seed}")
            report_lines.append("")
        
        report_lines.append("Environment:")
        report_lines.append(f"  Platform: {self.config.platform}")
        report_lines.append(f"  Python: {self.config.python_version}")
        report_lines.append("")
        
        report_lines.append("Dependencies:")
        for dep, version in self.config.dependencies.items():
            report_lines.append(f"  {dep}: {version}")
        report_lines.append("")
        
        if self.config.git_commit:
            report_lines.append("Git Commit:")
            report_lines.append(f"  {self.config.git_commit}")
            report_lines.append("")
        
        if self.config.analysis_parameters:
            report_lines.append("Analysis Parameters:")
            for param, value in self.config.analysis_parameters.items():
                report_lines.append(f"  {param}: {value}")
            report_lines.append("")
        
        report_lines.append("=" * 70)
        
        report = "\n".join(report_lines)
        
        if output_file:
            output_file.write(report)
            output_file.write("\n")
        
        return report
    
    def generate_latex_report(self) -> str:
        """
        Generate LaTeX-formatted reproducibility report.
        
        Returns:
            LaTeX code as string
        """
        latex_lines = []
        
        latex_lines.append("\\section{Reproducibility Information}")
        latex_lines.append("")
        
        latex_lines.append("\\subsection{Environment}")
        latex_lines.append("\\begin{itemize}")
        latex_lines.append(f"\\item Platform: {self.config.platform}")
        latex_lines.append(f"\\item Python: {self.config.python_version}")
        for dep, version in self.config.dependencies.items():
            latex_lines.append(f"\\item {dep}: {version}")
        latex_lines.append("\\end{itemize}")
        latex_lines.append("")
        
        if self.config.random_seed is not None:
            latex_lines.append("\\subsection{Random Seed}")
            latex_lines.append(f"The random seed used was: {self.config.random_seed}")
            latex_lines.append("")
        
        if self.config.analysis_parameters:
            latex_lines.append("\\subsection{Analysis Parameters}")
            latex_lines.append("\\begin{itemize}")
            for param, value in self.config.analysis_parameters.items():
                latex_lines.append(f"\\item {param}: {value}")
            latex_lines.append("\\end{itemize}")
            latex_lines.append("")
        
        if self.config.git_commit:
            latex_lines.append("\\subsection{Version Information}")
            latex_lines.append(f"Git commit: \\texttt{{{self.config.git_commit}}}")
            latex_lines.append("")
        
        return "\n".join(latex_lines)
    
    def compute_config_hash(self) -> str:
        """
        Compute hash of configuration for verification.
        
        Returns:
            SHA256 hash of configuration
        """
        config_str = json.dumps(asdict(self.config), sort_keys=True, default=str)
        return hashlib.sha256(config_str.encode()).hexdigest()
