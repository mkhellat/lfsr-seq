#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Attack visualization functions.

This module provides functions to visualize attack processes and results,
including correlation attacks, algebraic attacks, and attack comparisons.
"""

from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

from lfsr.visualization.base import (
    VisualizationConfig,
    OutputFormat,
    HAS_MATPLOTLIB,
    HAS_PLOTLY
)


def visualize_correlation_attack(
    correlation_results: Dict[str, Any],
    config: Optional[VisualizationConfig] = None,
    output_file: Optional[str] = None
) -> Any:
    """
    Visualize correlation attack results.
    
    This function creates visualizations showing correlation coefficients,
    attack progress, and success probabilities.
    
    **Key Terminology**:
    
    - **Correlation Attack Visualization**: Graphical representation of
      correlation attack results, showing correlation coefficients, attack
      progress, and success indicators.
    
    - **Correlation Coefficient**: A measure of linear relationship between
      two sequences, ranging from -1 to 1. Values close to ±1 indicate
      strong correlation.
    
    - **Attack Progress**: Visualization of how an attack progresses over
      time, showing metrics like candidates tested, success rate, etc.
    
    - **Success Probability Curve**: A plot showing the probability of
      attack success as a function of various parameters (e.g., keystream
      length, correlation threshold).
    
    Args:
        correlation_results: Dictionary containing correlation attack results
        config: Optional visualization configuration
        output_file: Optional output filename
    
    Returns:
        Plot object or list of plot objects
    """
    config = config or VisualizationConfig()
    
    plots = []
    
    # Correlation coefficient plot
    if 'correlations' in correlation_results:
        corr_plot = _plot_correlation_coefficients(
            correlation_results['correlations'],
            config,
            output_file
        )
        plots.append(corr_plot)
    
    # Attack progress plot
    if 'progress' in correlation_results:
        progress_plot = _plot_attack_progress(
            correlation_results['progress'],
            config,
            output_file
        )
        plots.append(progress_plot)
    
    # Success probability plot
    if 'success_probability' in correlation_results:
        prob_plot = _plot_success_probability(
            correlation_results['success_probability'],
            config,
            output_file
        )
        plots.append(prob_plot)
    
    return plots[0] if len(plots) == 1 else plots


def _plot_correlation_coefficients(
    correlations: Dict[str, float],
    config: VisualizationConfig,
    output_file: Optional[str]
) -> Any:
    """Plot correlation coefficients."""
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib required for correlation plots")
    
    import matplotlib.pyplot as plt
    
    lfsr_names = list(correlations.keys())
    corr_values = list(correlations.values())
    
    fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)
    
    colors = ['red' if abs(c) > 0.5 else 'blue' for c in corr_values]
    bars = ax.bar(range(len(lfsr_names)), corr_values, color=colors, alpha=0.7, edgecolor='black')
    
    # Add threshold lines
    ax.axhline(y=0.5, color='red', linestyle='--', alpha=0.5, label='High Correlation Threshold')
    ax.axhline(y=-0.5, color='red', linestyle='--', alpha=0.5)
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    ax.set_xticks(range(len(lfsr_names)))
    ax.set_xticklabels(lfsr_names, rotation=45, ha='right')
    ax.set_ylim(-1.1, 1.1)
    
    title = config.title or "Correlation Coefficients"
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_ylabel(config.ylabel or "Correlation Coefficient", fontsize=12)
    
    if config.show_grid:
        ax.grid(True, alpha=0.3, axis='y')
    
    if config.show_legend:
        ax.legend()
    
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=config.dpi, bbox_inches='tight')
    
    return fig


def _plot_attack_progress(
    progress: Dict[str, List[Any]],
    config: VisualizationConfig,
    output_file: Optional[str]
) -> Any:
    """Plot attack progress over time."""
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib required for progress plots")
    
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)
    
    # Plot different metrics
    if 'iterations' in progress and 'candidates_tested' in progress:
        iterations = progress['iterations']
        candidates = progress['candidates_tested']
        ax.plot(iterations, candidates, 'b-', linewidth=2, label='Candidates Tested')
    
    if 'iterations' in progress and 'success_rate' in progress:
        iterations = progress['iterations']
        success = progress['success_rate']
        ax2 = ax.twinx()
        ax2.plot(iterations, success, 'r-', linewidth=2, label='Success Rate', alpha=0.7)
        ax2.set_ylabel('Success Rate', color='r', fontsize=12)
        ax2.tick_params(axis='y', labelcolor='r')
    
    title = config.title or "Attack Progress"
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(config.xlabel or "Iteration", fontsize=12)
    ax.set_ylabel(config.ylabel or "Candidates Tested", fontsize=12)
    
    if config.show_grid:
        ax.grid(True, alpha=0.3)
    
    if config.show_legend:
        ax.legend(loc='upper left')
        if 'ax2' in locals():
            ax2.legend(loc='upper right')
    
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=config.dpi, bbox_inches='tight')
    
    return fig


def _plot_success_probability(
    success_data: Dict[str, Any],
    config: VisualizationConfig,
    output_file: Optional[str]
) -> Any:
    """Plot success probability curves."""
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib required for probability plots")
    
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)
    
    if 'parameter' in success_data and 'probability' in success_data:
        param = success_data['parameter']
        prob = success_data['probability']
        ax.plot(param, prob, 'b-', linewidth=2, marker='o', markersize=4)
    
    title = config.title or "Attack Success Probability"
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(config.xlabel or "Parameter", fontsize=12)
    ax.set_ylabel(config.ylabel or "Success Probability", fontsize=12)
    ax.set_ylim(0, 1.1)
    
    if config.show_grid:
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=config.dpi, bbox_inches='tight')
    
    return fig


def visualize_attack_comparison(
    attack_results: Dict[str, Dict[str, Any]],
    config: Optional[VisualizationConfig] = None,
    output_file: Optional[str] = None
) -> Any:
    """
    Visualize comparison of different attack methods.
    
    This function creates side-by-side comparisons of multiple attack
    methods, showing performance metrics and success rates.
    
    Args:
        attack_results: Dictionary mapping attack names to results
        config: Optional visualization configuration
        output_file: Optional output filename
    
    Returns:
        Plot object
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib required for comparison plots")
    
    import matplotlib.pyplot as plt
    
    config = config or VisualizationConfig()
    
    attack_names = list(attack_results.keys())
    
    # Extract metrics
    execution_times = []
    success_rates = []
    
    for name in attack_names:
        results = attack_results[name]
        execution_times.append(results.get('execution_time', 0))
        success_rates.append(results.get('success_rate', 0))
    
    # Create comparison plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(config.width * 1.5, config.height), dpi=config.dpi)
    
    # Execution time comparison
    ax1.bar(attack_names, execution_times, alpha=0.7, color='steelblue', edgecolor='black')
    ax1.set_title("Execution Time Comparison", fontsize=12, fontweight='bold')
    ax1.set_ylabel("Time (seconds)", fontsize=10)
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Success rate comparison
    ax2.bar(attack_names, success_rates, alpha=0.7, color='green', edgecolor='black')
    ax2.set_title("Success Rate Comparison", fontsize=12, fontweight='bold')
    ax2.set_ylabel("Success Rate", fontsize=10)
    ax2.set_ylim(0, 1.1)
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3, axis='y')
    
    fig.suptitle(config.title or "Attack Method Comparison", fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=config.dpi, bbox_inches='tight')
    
    return fig
