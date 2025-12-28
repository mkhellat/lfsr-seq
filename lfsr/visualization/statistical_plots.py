#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Statistical distribution plot visualizations.

This module provides functions to create publication-quality statistical
plots for LFSR analysis results.
"""

from typing import Any, Dict, List, Optional, Tuple
from collections import Counter

from lfsr.visualization.base import (
    VisualizationConfig,
    OutputFormat,
    HAS_MATPLOTLIB
)


def plot_period_statistics(
    period_dict: Dict[int, int],
    theoretical_max_period: Optional[int] = None,
    is_primitive: bool = False,
    config: Optional[VisualizationConfig] = None,
    output_file: Optional[str] = None
) -> Any:
    """
    Create publication-quality statistical plots for period distribution.
    
    This function generates multiple statistical visualizations including
    histograms, box plots, and violin plots for period distributions.
    
    **Key Terminology**:
    
    - **Histogram**: A graphical representation of data distribution using
      bars. Each bar represents a range of values and shows frequency.
    
    - **Box Plot**: A standardized way of displaying data distribution based
      on five-number summary: minimum, first quartile, median, third quartile,
      and maximum. Also shows outliers.
    
    - **Violin Plot**: A combination of box plot and kernel density plot,
      showing the distribution shape and summary statistics.
    
    - **Publication Quality**: Visualizations suitable for research papers,
      with high resolution, proper formatting, and clear labels.
    
    Args:
        period_dict: Dictionary mapping period to count
        theoretical_max_period: Optional theoretical maximum period
        is_primitive: Whether polynomial is primitive
        config: Optional visualization configuration
        output_file: Optional output filename
    
    Returns:
        Matplotlib figure with subplots
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib is required for statistical plots")
    
    import matplotlib.pyplot as plt
    import numpy as np
    
    config = config or VisualizationConfig()
    
    # Extract periods and counts
    periods = list(period_dict.keys())
    counts = list(period_dict.values())
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(config.width, config.height), dpi=config.dpi)
    fig.suptitle(config.title or "Period Distribution Statistics", fontsize=16, fontweight='bold')
    
    # 1. Histogram
    ax1 = axes[0, 0]
    ax1.bar(periods, counts, alpha=0.7, edgecolor='black', linewidth=0.5)
    if theoretical_max_period:
        ax1.axvline(theoretical_max_period, color='red', linestyle='--', linewidth=2, label='Theoretical Max')
    ax1.set_xlabel("Period", fontsize=10)
    ax1.set_ylabel("Frequency", fontsize=10)
    ax1.set_title("Histogram", fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    if theoretical_max_period:
        ax1.legend()
    
    # 2. Box Plot
    ax2 = axes[0, 1]
    # Create data for box plot (repeat periods by their counts)
    period_data = []
    for period, count in zip(periods, counts):
        period_data.extend([period] * count)
    ax2.boxplot(period_data, vert=True)
    if theoretical_max_period:
        ax2.axhline(theoretical_max_period, color='red', linestyle='--', linewidth=2, label='Theoretical Max')
    ax2.set_ylabel("Period", fontsize=10)
    ax2.set_title("Box Plot", fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    if theoretical_max_period:
        ax2.legend()
    
    # 3. Cumulative Distribution
    ax3 = axes[1, 0]
    sorted_periods = sorted(periods)
    cumulative_counts = []
    total = sum(counts)
    cumsum = 0
    for period in sorted_periods:
        cumsum += period_dict[period]
        cumulative_counts.append(cumsum / total)
    ax3.plot(sorted_periods, cumulative_counts, marker='o', linestyle='-', linewidth=2)
    ax3.set_xlabel("Period", fontsize=10)
    ax3.set_ylabel("Cumulative Probability", fontsize=10)
    ax3.set_title("Cumulative Distribution", fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0, 1.1)
    
    # 4. Statistics Summary
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    # Calculate statistics
    mean_period = np.average(period_data) if period_data else 0
    median_period = np.median(period_data) if period_data else 0
    max_period = max(periods) if periods else 0
    min_period = min(periods) if periods else 0
    std_period = np.std(period_data) if period_data else 0
    
    stats_text = f"Period Statistics\n\n"
    stats_text += f"Mean: {mean_period:.2f}\n"
    stats_text += f"Median: {median_period:.2f}\n"
    stats_text += f"Std Dev: {std_period:.2f}\n"
    stats_text += f"Min: {min_period}\n"
    stats_text += f"Max: {max_period}\n"
    if theoretical_max_period:
        stats_text += f"\nTheoretical Max: {theoretical_max_period}\n"
        stats_text += f"Ratio: {max_period/theoretical_max_period:.2%}\n"
    stats_text += f"\nPrimitive: {'Yes' if is_primitive else 'No'}\n"
    stats_text += f"Total Sequences: {sum(counts)}\n"
    
    ax4.text(0.1, 0.5, stats_text, fontsize=11, family='monospace', verticalalignment='center')
    
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=config.dpi, bbox_inches='tight')
    
    return fig


def plot_sequence_analysis(
    sequence: List[int],
    config: Optional[VisualizationConfig] = None,
    output_file: Optional[str] = None
) -> Any:
    """
    Create plots for sequence analysis (autocorrelation, frequency, etc.).
    
    This function generates visualizations for sequence properties including
    autocorrelation, frequency distribution, and runs analysis.
    
    Args:
        sequence: Binary sequence to analyze
        config: Optional visualization configuration
        output_file: Optional output filename
    
    Returns:
        Matplotlib figure with subplots
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib is required for sequence plots")
    
    import matplotlib.pyplot as plt
    import numpy as np
    
    config = config or VisualizationConfig()
    
    fig, axes = plt.subplots(2, 2, figsize=(config.width, config.height), dpi=config.dpi)
    fig.suptitle(config.title or "Sequence Analysis", fontsize=16, fontweight='bold')
    
    # 1. Sequence plot (first 100 bits)
    ax1 = axes[0, 0]
    plot_length = min(100, len(sequence))
    ax1.plot(range(plot_length), sequence[:plot_length], marker='o', markersize=2, linewidth=0.5)
    ax1.set_xlabel("Position", fontsize=10)
    ax1.set_ylabel("Bit Value", fontsize=10)
    ax1.set_title(f"Sequence (first {plot_length} bits)", fontsize=12, fontweight='bold')
    ax1.set_ylim(-0.1, 1.1)
    ax1.grid(True, alpha=0.3)
    
    # 2. Frequency distribution
    ax2 = axes[0, 1]
    freq = Counter(sequence)
    zeros = freq.get(0, 0)
    ones = freq.get(1, 0)
    total = len(sequence)
    ax2.bar(['0', '1'], [zeros/total, ones/total], alpha=0.7, color=['blue', 'orange'])
    ax2.set_ylabel("Frequency", fontsize=10)
    ax2.set_title("Bit Frequency", fontsize=12, fontweight='bold')
    ax2.set_ylim(0, 1)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. Autocorrelation (simplified)
    ax3 = axes[1, 0]
    max_lag = min(20, len(sequence) // 2)
    autocorr = []
    for lag in range(max_lag):
        corr = sum(sequence[i] == sequence[i+lag] for i in range(len(sequence)-lag)) / (len(sequence)-lag)
        autocorr.append(corr)
    ax3.plot(range(max_lag), autocorr, marker='o', linewidth=2)
    ax3.axhline(0.5, color='red', linestyle='--', linewidth=1, label='Expected (0.5)')
    ax3.set_xlabel("Lag", fontsize=10)
    ax3.set_ylabel("Autocorrelation", fontsize=10)
    ax3.set_title("Autocorrelation", fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # 4. Runs analysis
    ax4 = axes[1, 1]
    runs = []
    current_run = 1
    for i in range(1, min(100, len(sequence))):
        if sequence[i] == sequence[i-1]:
            current_run += 1
        else:
            runs.append(current_run)
            current_run = 1
    runs.append(current_run)
    
    run_freq = Counter(runs)
    run_lengths = sorted(run_freq.keys())
    run_counts = [run_freq[r] for r in run_lengths]
    
    ax4.bar(run_lengths, run_counts, alpha=0.7, edgecolor='black', linewidth=0.5)
    ax4.set_xlabel("Run Length", fontsize=10)
    ax4.set_ylabel("Frequency", fontsize=10)
    ax4.set_title("Run Length Distribution", fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=config.dpi, bbox_inches='tight')
    
    return fig
