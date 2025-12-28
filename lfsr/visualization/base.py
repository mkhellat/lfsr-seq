#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base classes and utilities for LFSR visualization.

This module provides base classes and common utilities for creating
visualizations of LFSR analysis results.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import os

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    plt = None

try:
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    go = None
    px = None

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    nx = None


class OutputFormat(Enum):
    """Supported output formats for visualizations."""
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    HTML = "html"
    JSON = "json"


@dataclass
class VisualizationConfig:
    """
    Configuration for visualizations.
    
    Attributes:
        width: Figure width in inches
        height: Figure height in inches
        dpi: Resolution for raster formats
        style: Matplotlib style name
        interactive: Whether to create interactive plots
        output_format: Output format (PNG, SVG, PDF, HTML)
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        show_grid: Whether to show grid
        show_legend: Whether to show legend
    """
    width: float = 10.0
    height: float = 6.0
    dpi: int = 300
    style: str = "seaborn-v0_8"
    interactive: bool = False
    output_format: OutputFormat = OutputFormat.PNG
    title: Optional[str] = None
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None
    show_grid: bool = True
    show_legend: bool = True


class BaseVisualization:
    """
    Base class for LFSR visualizations.
    
    This class provides common functionality for all visualization types,
    including configuration, export, and common utilities.
    
    **Key Terminology**:
    
    - **Visualization**: A graphical representation of data or analysis results.
      Visualizations help understand patterns, relationships, and properties
      that may not be obvious from raw data.
    
    - **Static Plot**: A non-interactive image file (PNG, SVG, PDF) that can be
      included in documents or presentations.
    
    - **Interactive Plot**: A plot that allows user interaction (zooming, panning,
      tooltips) typically in HTML format using libraries like Plotly.
    
    - **Publication Quality**: Visualizations suitable for inclusion in research
      papers, with high resolution, proper formatting, and clear labels.
    """
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        """
        Initialize visualization.
        
        Args:
            config: Optional visualization configuration
        """
        self.config = config or VisualizationConfig()
        self._check_dependencies()
    
    def _check_dependencies(self) -> None:
        """Check if required dependencies are available."""
        if not HAS_MATPLOTLIB and self.config.output_format != OutputFormat.HTML:
            raise ImportError(
                "matplotlib is required for static plot generation. "
                "Install with: pip install matplotlib"
            )
        
        if not HAS_PLOTLY and self.config.interactive:
            raise ImportError(
                "plotly is required for interactive plots. "
                "Install with: pip install plotly"
            )
    
    def save(self, filename: str) -> None:
        """
        Save visualization to file.
        
        Args:
            filename: Output filename
        """
        raise NotImplementedError("Subclasses must implement save()")
    
    def show(self) -> None:
        """Display visualization (if in interactive environment)."""
        raise NotImplementedError("Subclasses must implement show()")
    
    def to_html(self) -> str:
        """
        Convert visualization to HTML string.
        
        Returns:
            HTML string representation
        """
        raise NotImplementedError("Subclasses must implement to_html()")


def check_visualization_dependencies() -> Dict[str, bool]:
    """
    Check which visualization dependencies are available.
    
    Returns:
        Dictionary mapping library names to availability status
    """
    return {
        'matplotlib': HAS_MATPLOTLIB,
        'plotly': HAS_PLOTLY,
        'networkx': HAS_NETWORKX
    }
