#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Interactive period graph visualizations.

This module provides functions to create interactive and static visualizations
of LFSR period distributions and period-related analysis.
"""

from typing import Any, Dict, List, Optional, Tuple
from collections import Counter

from lfsr.visualization.base import (
    BaseVisualization,
    VisualizationConfig,
    OutputFormat,
    HAS_MATPLOTLIB,
    HAS_PLOTLY
)


def plot_period_distribution(
    period_dict: Dict[int, int],
    theoretical_max_period: Optional[int] = None,
    is_primitive: bool = False,
    config: Optional[VisualizationConfig] = None,
    output_file: Optional[str] = None
) -> Any:
    """
    Create period distribution visualization.
    
    This function generates a histogram showing the distribution of periods
    across all initial states, with optional comparison to theoretical bounds.
    
    **Key Terminology**:
    
    - **Period Distribution**: The distribution of periods across all possible
      initial states of an LFSR. This shows how many sequences have each
      possible period.
    
    - **Histogram**: A graphical representation of data distribution using
      bars. Each bar represents a range of values and shows how many data
      points fall within that range.
    
    - **Theoretical Maximum Period**: The maximum possible period for an LFSR
      of degree d over GF(q), which is q^d - 1. This is achieved if and only
      if the characteristic polynomial is primitive.
    
    - **Interactive Plot**: A plot that allows user interaction such as
      zooming, panning, and viewing detailed information on hover.
    
    Args:
        period_dict: Dictionary mapping period to count
        theoretical_max_period: Optional theoretical maximum period
        is_primitive: Whether polynomial is primitive
        config: Optional visualization configuration
        output_file: Optional output filename
    
    Returns:
        Plot object (matplotlib figure or plotly figure)
    
    Example:
        >>> from lfsr.visualization.period_graphs import plot_period_distribution
        >>> period_dict = {1: 1, 3: 2, 6: 4, 12: 8}
        >>> fig = plot_period_distribution(period_dict, theoretical_max_period=15)
        >>> fig.savefig("period_distribution.png")
    """
    config = config or VisualizationConfig()
    
    periods = list(period_dict.keys())
    counts = list(period_dict.values())
    total_sequences = sum(counts)
    
    if config.interactive and HAS_PLOTLY:
        return _plot_period_distribution_interactive(
            periods, counts, theoretical_max_period, is_primitive, config, output_file
        )
    elif HAS_MATPLOTLIB:
        return _plot_period_distribution_static(
            periods, counts, theoretical_max_period, is_primitive, config, output_file
        )
    else:
        raise ImportError("matplotlib or plotly required for visualization")


def _plot_period_distribution_static(
    periods: List[int],
    counts: List[int],
    theoretical_max: Optional[int],
    is_primitive: bool,
    config: VisualizationConfig,
    output_file: Optional[str]
) -> Any:
    """Create static period distribution plot using matplotlib."""
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)
    
    # Create histogram
    ax.bar(periods, counts, alpha=0.7, edgecolor='black', linewidth=0.5)
    
    # Add theoretical maximum line if provided
    if theoretical_max:
        ax.axvline(
            theoretical_max,
            color='red',
            linestyle='--',
            linewidth=2,
            label=f'Theoretical Maximum: {theoretical_max}'
        )
    
    # Labels and title
    if config.title:
        ax.set_title(config.title, fontsize=14, fontweight='bold')
    else:
        title = "Period Distribution"
        if is_primitive:
            title += " (Primitive Polynomial)"
        ax.set_title(title, fontsize=14, fontweight='bold')
    
    ax.set_xlabel(config.xlabel or "Period", fontsize=12)
    ax.set_ylabel(config.ylabel or "Number of Sequences", fontsize=12)
    
    if config.show_grid:
        ax.grid(True, alpha=0.3)
    
    if config.show_legend and theoretical_max:
        ax.legend()
    
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=config.dpi, bbox_inches='tight')
    
    return fig


def _plot_period_distribution_interactive(
    periods: List[int],
    counts: List[int],
    theoretical_max: Optional[int],
    is_primitive: bool,
    config: VisualizationConfig,
    output_file: Optional[str]
) -> Any:
    """Create interactive period distribution plot using plotly."""
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Add histogram bars
    fig.add_trace(go.Bar(
        x=periods,
        y=counts,
        name="Period Distribution",
        marker_color='steelblue',
        opacity=0.7,
        hovertemplate='Period: %{x}<br>Count: %{y}<extra></extra>'
    ))
    
    # Add theoretical maximum line if provided
    if theoretical_max:
        fig.add_vline(
            x=theoretical_max,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Theoretical Maximum: {theoretical_max}",
            annotation_position="top"
        )
    
    # Update layout
    title = config.title or "Period Distribution"
    if is_primitive:
        title += " (Primitive Polynomial)"
    
    fig.update_layout(
        title=title,
        xaxis_title=config.xlabel or "Period",
        yaxis_title=config.ylabel or "Number of Sequences",
        showlegend=config.show_legend,
        width=config.width * 80,  # Convert inches to pixels
        height=config.height * 80,
        hovermode='closest'
    )
    
    if output_file:
        if output_file.endswith('.html'):
            fig.write_html(output_file)
        else:
            fig.write_image(output_file)
    
    return fig


def plot_period_vs_state(
    state_period_pairs: List[Tuple[Any, int]],
    config: Optional[VisualizationConfig] = None,
    output_file: Optional[str] = None
) -> Any:
    """
    Create scatter plot of period vs initial state.
    
    This function visualizes how period varies with initial state, helping
    identify patterns in period distribution.
    
    Args:
        state_period_pairs: List of (state, period) tuples
        config: Optional visualization configuration
        output_file: Optional output filename
    
    Returns:
        Plot object
    """
    config = config or VisualizationConfig()
    
    if len(state_period_pairs) == 0:
        raise ValueError("No state-period pairs provided")
    
    # Extract states and periods
    states = [str(state) for state, _ in state_period_pairs]
    periods = [period for _, period in state_period_pairs]
    
    if config.interactive and HAS_PLOTLY:
        return _plot_period_vs_state_interactive(states, periods, config, output_file)
    elif HAS_MATPLOTLIB:
        return _plot_period_vs_state_static(states, periods, config, output_file)
    else:
        raise ImportError("matplotlib or plotly required for visualization")


def _plot_period_vs_state_static(
    states: List[str],
    periods: List[int],
    config: VisualizationConfig,
    output_file: Optional[str]
) -> Any:
    """Create static scatter plot using matplotlib."""
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)
    
    # Create scatter plot
    x_indices = range(len(states))
    ax.scatter(x_indices, periods, alpha=0.6, s=20)
    
    # Labels and title
    ax.set_title(config.title or "Period vs Initial State", fontsize=14, fontweight='bold')
    ax.set_xlabel(config.xlabel or "State Index", fontsize=12)
    ax.set_ylabel(config.ylabel or "Period", fontsize=12)
    
    if config.show_grid:
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=config.dpi, bbox_inches='tight')
    
    return fig


def _plot_period_vs_state_interactive(
    states: List[str],
    periods: List[int],
    config: VisualizationConfig,
    output_file: Optional[str]
) -> Any:
    """Create interactive scatter plot using plotly."""
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=list(range(len(states))),
        y=periods,
        mode='markers',
        name="Period",
        marker=dict(size=5, opacity=0.6),
        hovertemplate='State: %{text}<br>Period: %{y}<extra></extra>',
        text=states
    ))
    
    fig.update_layout(
        title=config.title or "Period vs Initial State",
        xaxis_title=config.xlabel or "State Index",
        yaxis_title=config.ylabel or "Period",
        showlegend=config.show_legend,
        width=config.width * 80,
        height=config.height * 80,
        hovermode='closest'
    )
    
    if output_file:
        if output_file.endswith('.html'):
            fig.write_html(output_file)
        else:
            fig.write_image(output_file)
    
    return fig
