#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Statistical distribution plot visualizations.

This module provides functions to create publication-quality statistical
plots for LFSR analysis results, including period distributions, sequence
analysis, and comparison plots.
"""

from typing import Any, Dict, List, Optional, Tuple
from collections import Counter
import math

from lfsr.visualization.base import (
    VisualizationConfig,
    OutputFormat,
    HAS_MATPLOTLIB,
    HAS_PLOTLY
)


def plot_period_statistics(
    period_dict: Dict[int, int],
    theoretical_max_period: Optional[int] = None,
    is_primitive: bool = False,
    plot_type: str = "histogram",
    config: Optional[VisualizationConfig] = None,
    output_file: Optional[str] = None
) -> Any:
    """
    Create statistical plots for period distribution.
    
    This function generates publication-quality statistical plots including
    histograms, box plots, and violin plots for period distributions.
    
    **Key Terminology**:
    
    - **Histogram**: A graphical representation of data distribution using
      bars. Each bar represents a range of values and shows frequency.
    
    - **Box Plot**: A standardized way of displaying data distribution based
      on five-number summary: minimum, first quartile, median, third quartile,
      and maximum. Shows outliers and distribution shape.
    
    - **Violin Plot**: A combination of box plot and kernel density plot,
      showing both summary statistics and distribution shape.
    
    - **Publication Quality**: Visualizations suitable for research papers,
      with high resolution, proper formatting, and clear labels.
    
    Args:
        period_dict: Dictionary mapping period to count
        theoretical_max_period: Optional theoretical maximum period
        is_primitive: Whether polynomial is primitive
        plot_type: Type of plot ("histogram", "box", "violin")
        config: Optional visualization configuration
        output_file: Optional output filename
    
    Returns:
        Plot object
    """
    config = config or VisualizationConfig()
    
    periods = []
    for period, count in period_dict.items():
        periods.extend([period] * count)
    
    if plot_type == "histogram":
        return _plot_histogram(periods, theoretical_max_period, is_primitive, config, output_file)
    elif plot_type == "box":
        return _plot_box(periods, theoretical_max_period, is_primitive, config, output_file)
    elif plot_type == "violin":
        return _plot_violin(periods, theoretical_max_period, is_primitive, config, output_file)
    else:
        raise ValueError(f"Unknown plot type: {plot_type}")


def _plot_histogram(
    periods: List[int],
    theoretical_max: Optional[int],
    is_primitive: bool,
    config: VisualizationConfig,
    output_file: Optional[str]
) -> Any:
    """Create histogram plot."""
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib required for histogram plots")
    
    import matplotlib.pyplot as plt
    import numpy as np
    
    fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)
    
    # Create histogram
    n, bins, patches = ax.hist(periods, bins=min(50, len(set(periods))), alpha=0.7, edgecolor='black', linewidth=0.5)
    
    # Add theoretical maximum line
    if theoretical_max:
        ax.axvline(
            theoretical_max,
            color='red',
            linestyle='--',
            linewidth=2,
            label=f'Theoretical Maximum: {theoretical_max}'
        )
    
    # Add statistics text
    mean_period = np.mean(periods)
    median_period = np.median(periods)
    std_period = np.std(periods)
    
    stats_text = f'Mean: {mean_period:.2f}\\nMedian: {median_period:.2f}\\nStd: {std_period:.2f}'
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    title = config.title or "Period Distribution"
    if is_primitive:
        title += " (Primitive Polynomial)"
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(config.xlabel or "Period", fontsize=12)
    ax.set_ylabel(config.ylabel or "Frequency", fontsize=12)
    
    if config.show_grid:
        ax.grid(True, alpha=0.3)
    
    if config.show_legend and theoretical_max:
        ax.legend()
    
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=config.dpi, bbox_inches='tight')
    
    return fig


def _plot_box(
    periods: List[int],
    theoretical_max: Optional[int],
    is_primitive: bool,
    config: VisualizationConfig,
    output_file: Optional[str]
) -> Any:
    """Create box plot."""
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib required for box plots")
    
    import matplotlib.pyplot as plt
    import numpy as np
    
    fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)
    
    # Create box plot
    bp = ax.boxplot([periods], vert=True, patch_artist=True)
    bp['boxes'][0].set_facecolor('lightblue')
    bp['boxes'][0].set_alpha(0.7)
    
    # Add theoretical maximum line
    if theoretical_max:
        ax.axhline(
            theoretical_max,
            color='red',
            linestyle='--',
            linewidth=2,
            label=f'Theoretical Maximum: {theoretical_max}'
        )
    
    title = config.title or "Period Distribution (Box Plot)"
    if is_primitive:
        title += " (Primitive Polynomial)"
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_ylabel(config.ylabel or "Period", fontsize=12)
    ax.set_xticklabels(['Periods'])
    
    if config.show_grid:
        ax.grid(True, alpha=0.3, axis='y')
    
    if config.show_legend and theoretical_max:
        ax.legend()
    
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=config.dpi, bbox_inches='tight')
    
    return fig


def _plot_violin(
    periods: List[int],
    theoretical_max: Optional[int],
    is_primitive: bool,
    config: VisualizationConfig,
    output_file: Optional[str]
) -> Any:
    """Create violin plot."""
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib required for violin plots")
    
    import matplotlib.pyplot as plt
    import numpy as np
    
    fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)
    
    # Create violin plot
    parts = ax.violinplot([periods], positions=[1], showmeans=True, showmedians=True)
    for pc in parts['bodies']:
        pc.set_facecolor('lightblue')
        pc.set_alpha(0.7)
    
    # Add theoretical maximum line
    if theoretical_max:
        ax.axhline(
            theoretical_max,
            color='red',
            linestyle='--',
            linewidth=2,
            label=f'Theoretical Maximum: {theoretical_max}'
        )
    
    title = config.title or "Period Distribution (Violin Plot)"
    if is_primitive:
        title += " (Primitive Polynomial)"
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_ylabel(config.ylabel or "Period", fontsize=12)
    ax.set_xticklabels(['Periods'])
    
    if config.show_grid:
        ax.grid(True, alpha=0.3, axis='y')
    
    if config.show_legend and theoretical_max:
        ax.legend()
    
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=config.dpi, bbox_inches='tight')
    
    return fig


def plot_sequence_analysis(
    sequence: List[int],
    analysis_type: str = "autocorrelation",
    config: Optional[VisualizationConfig] = None,
    output_file: Optional[str] = None
) -> Any:
    """
    Create sequence analysis plots.
    
    This function generates plots for sequence properties including
    autocorrelation, frequency distribution, and runs analysis.
    
    **Key Terminology**:
    
    - **Autocorrelation**: A measure of similarity between a sequence and
      a shifted version of itself. Autocorrelation plots show how correlated
      a sequence is with itself at different lags.
    
    - **Frequency Distribution**: The distribution of different values in
      a sequence. For binary sequences, this shows the proportion of 0s and 1s.
    
    - **Runs Analysis**: Analysis of consecutive identical elements in a
      sequence. Runs plots show the distribution of run lengths.
    
    Args:
        sequence: Sequence to analyze
        analysis_type: Type of analysis ("autocorrelation", "frequency", "runs")
        config: Optional visualization configuration
        output_file: Optional output filename
    
    Returns:
        Plot object
    """
    config = config or VisualizationConfig()
    
    if analysis_type == "autocorrelation":
        return _plot_autocorrelation(sequence, config, output_file)
    elif analysis_type == "frequency":
        return _plot_frequency_distribution(sequence, config, output_file)
    elif analysis_type == "runs":
        return _plot_runs_analysis(sequence, config, output_file)
    else:
        raise ValueError(f"Unknown analysis type: {analysis_type}")


def _plot_autocorrelation(
    sequence: List[int],
    config: VisualizationConfig,
    output_file: Optional[str]
) -> Any:
    """Create autocorrelation plot."""
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib required for autocorrelation plots")
    
    import matplotlib.pyplot as plt
    import numpy as np
    
    # Compute autocorrelation
    max_lag = min(100, len(sequence) // 2)
    autocorr = []
    lags = list(range(max_lag))
    
    for lag in lags:
        if lag == 0:
            autocorr.append(1.0)
        else:
            # Simple autocorrelation computation
            corr = sum(sequence[i] == sequence[i + lag] for i in range(len(sequence) - lag))
            autocorr.append(corr / (len(sequence) - lag))
    
    fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)
    
    ax.plot(lags, autocorr, 'b-', linewidth=1.5, alpha=0.7)
    ax.axhline(y=0.5, color='r', linestyle='--', alpha=0.5, label='Expected (random)')
    ax.fill_between(lags, autocorr, 0.5, alpha=0.3)
    
    title = config.title or "Autocorrelation Analysis"
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(config.xlabel or "Lag", fontsize=12)
    ax.set_ylabel(config.ylabel or "Autocorrelation", fontsize=12)
    
    if config.show_grid:
        ax.grid(True, alpha=0.3)
    
    if config.show_legend:
        ax.legend()
    
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=config.dpi, bbox_inches='tight')
    
    return fig


def _plot_frequency_distribution(
    sequence: List[int],
    config: VisualizationConfig,
    output_file: Optional[str]
) -> Any:
    """Create frequency distribution plot."""
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib required for frequency plots")
    
    import matplotlib.pyplot as plt
    from collections import Counter
    
    freq = Counter(sequence)
    elements = list(freq.keys())
    counts = list(freq.values())
    
    fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)
    
    ax.bar(elements, counts, alpha=0.7, edgecolor='black', linewidth=0.5)
    
    title = config.title or "Frequency Distribution"
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(config.xlabel or "Element", fontsize=12)
    ax.set_ylabel(config.ylabel or "Frequency", fontsize=12)
    
    if config.show_grid:
        ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=config.dpi, bbox_inches='tight')
    
    return fig


def _plot_runs_analysis(
    sequence: List[int],
    config: VisualizationConfig,
    output_file: Optional[str]
) -> Any:
    """Create runs analysis plot."""
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib required for runs plots")
    
    import matplotlib.pyplot as plt
    from collections import Counter
    
    # Compute run lengths
    runs = []
    if sequence:
        current_run = 1
        for i in range(1, len(sequence)):
            if sequence[i] == sequence[i-1]:
                current_run += 1
            else:
                runs.append(current_run)
                current_run = 1
        runs.append(current_run)
    
    run_lengths = Counter(runs)
    lengths = sorted(run_lengths.keys())
    frequencies = [run_lengths[length] for length in lengths]
    
    fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)
    
    ax.bar(lengths, frequencies, alpha=0.7, edgecolor='black', linewidth=0.5)
    
    title = config.title or "Runs Analysis"
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(config.xlabel or "Run Length", fontsize=12)
    ax.set_ylabel(config.ylabel or "Frequency", fontsize=12)
    
    if config.show_grid:
        ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=config.dpi, bbox_inches='tight')
    
    return fig
