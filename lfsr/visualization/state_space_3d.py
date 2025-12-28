#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
3D state space visualizations.

This module provides functions to create 3D visualizations of LFSR state
spaces, including 3D scatter plots and projections.
"""

from typing import Any, Dict, List, Optional, Tuple
import math

from lfsr.visualization.base import (
    VisualizationConfig,
    OutputFormat,
    HAS_PLOTLY
)


def plot_3d_state_space(
    state_sequences: Dict[int, List[Any]],
    period_dict: Dict[int, int],
    max_states: int = 100,
    config: Optional[VisualizationConfig] = None,
    output_file: Optional[str] = None
) -> Any:
    """
    Create 3D visualization of state space.
    
    This function generates interactive 3D scatter plots showing states
    in the LFSR state space, with coloring by period or other properties.
    
    **Key Terminology**:
    
    - **3D Visualization**: A three-dimensional graphical representation
      that allows viewing data from different angles and perspectives.
      Useful for understanding spatial relationships in high-dimensional data.
    
    - **State Space**: The set of all possible states an LFSR can be in.
      For an LFSR of degree d over GF(q), the state space has q^d elements.
    
    - **Interactive 3D Plot**: A 3D plot that allows user interaction such
      as rotation, zooming, and panning. Typically implemented using Plotly.
    
    - **State Coloring**: Assigning colors to states based on their properties
      (e.g., period, cycle membership) to highlight patterns and relationships.
    
    Args:
        state_sequences: Dictionary mapping sequence number to list of states
        period_dict: Dictionary mapping sequence number to period
        max_states: Maximum number of states to visualize
        config: Optional visualization configuration
        output_file: Optional output filename (should be HTML for interactive)
    
    Returns:
        Plotly figure object
    """
    if not HAS_PLOTLY:
        raise ImportError("plotly required for 3D visualizations. Install with: pip install plotly")
    
    import plotly.graph_objects as go
    import numpy as np
    
    config = config or VisualizationConfig()
    
    # Collect states and their properties
    states_3d = []
    periods = []
    colors = []
    
    state_count = 0
    for seq_num, sequence in state_sequences.items():
        if state_count >= max_states:
            break
        
        period = period_dict.get(seq_num, len(sequence))
        
        for i, state in enumerate(sequence[:min(period, max_states - state_count)]):
            # Convert state to 3D coordinates
            # For binary states, use first 3 bits as coordinates
            if isinstance(state, (list, tuple)) and len(state) >= 3:
                x, y, z = state[0], state[1], state[2]
            else:
                # Fallback: use state index and period
                x, y, z = i % 10, (i // 10) % 10, period % 10
            
            states_3d.append((x, y, z))
            periods.append(period)
            colors.append(period)  # Color by period
            state_count += 1
            
            if state_count >= max_states:
                break
    
    if not states_3d:
        raise ValueError("No states to visualize")
    
    x_coords = [s[0] for s in states_3d]
    y_coords = [s[1] for s in states_3d]
    z_coords = [s[2] for s in states_3d]
    
    # Create 3D scatter plot
    fig = go.Figure(data=go.Scatter3d(
        x=x_coords,
        y=y_coords,
        z=z_coords,
        mode='markers',
        marker=dict(
            size=5,
            color=colors,
            colorscale='Viridis',
            opacity=0.7,
            colorbar=dict(title="Period")
        ),
        text=[f"Period: {p}" for p in periods],
        hovertemplate='X: %{x}<br>Y: %{y}<br>Z: %{z}<br>%{text}<extra></extra>'
    ))
    
    title = config.title or "3D State Space Visualization"
    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
        ),
        width=config.width * 80,
        height=config.height * 80
    )
    
    if output_file:
        if output_file.endswith('.html'):
            fig.write_html(output_file)
        else:
            # For non-HTML, plotly needs kaleido for static export
            try:
                fig.write_image(output_file)
            except Exception:
                # Fallback: save as HTML
                fig.write_html(output_file.replace('.png', '.html').replace('.pdf', '.html'))
    
    return fig


def plot_state_space_projection(
    state_sequences: Dict[int, List[Any]],
    period_dict: Dict[int, int],
    projection_method: str = "pca",
    max_states: int = 100,
    config: Optional[VisualizationConfig] = None,
    output_file: Optional[str] = None
) -> Any:
    """
    Create 2D projection of state space.
    
    This function projects high-dimensional state spaces to 2D for visualization
    using dimensionality reduction techniques.
    
    **Key Terminology**:
    
    - **Dimensionality Reduction**: Techniques for reducing the number of
      features (dimensions) in data while preserving important information.
      Common methods include PCA and t-SNE.
    
    - **PCA (Principal Component Analysis)**: A linear dimensionality reduction
      technique that finds the directions of maximum variance in data.
    
    - **t-SNE (t-Distributed Stochastic Neighbor Embedding)**: A non-linear
      dimensionality reduction technique that preserves local structure.
    
    - **Projection**: Mapping high-dimensional data to lower dimensions for
      visualization while attempting to preserve relationships.
    
    Args:
        state_sequences: Dictionary mapping sequence number to list of states
        period_dict: Dictionary mapping sequence number to period
        projection_method: Projection method ("pca", "tsne", "simple")
        max_states: Maximum number of states to project
        config: Optional visualization configuration
        output_file: Optional output filename
    
    Returns:
        Plot object
    """
    config = config or VisualizationConfig()
    
    # Collect states
    states = []
    periods = []
    
    state_count = 0
    for seq_num, sequence in state_sequences.items():
        if state_count >= max_states:
            break
        
        period = period_dict.get(seq_num, len(sequence))
        
        for state in sequence[:min(period, max_states - state_count)]:
            if isinstance(state, (list, tuple)):
                states.append(list(state))
            else:
                states.append([state])
            periods.append(period)
            state_count += 1
            
            if state_count >= max_states:
                break
    
    if not states:
        raise ValueError("No states to project")
    
    if projection_method == "pca":
        return _project_pca(states, periods, config, output_file)
    elif projection_method == "simple":
        return _project_simple(states, periods, config, output_file)
    else:
        raise ValueError(f"Unknown projection method: {projection_method}")


def _project_pca(
    states: List[List[int]],
    periods: List[int],
    config: VisualizationConfig,
    output_file: Optional[str]
) -> Any:
    """Project using PCA."""
    try:
        from sklearn.decomposition import PCA
        import numpy as np
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("sklearn and numpy required for PCA projection")
    
    # Convert to numpy array
    max_len = max(len(s) for s in states)
    states_padded = [s + [0] * (max_len - len(s)) for s in states]
    X = np.array(states_padded)
    
    # Apply PCA
    if X.shape[1] < 2:
        # Not enough dimensions, use simple projection
        return _project_simple(states, periods, config, output_file)
    
    pca = PCA(n_components=2)
    X_projected = pca.fit_transform(X)
    
    # Create plot
    fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)
    
    scatter = ax.scatter(X_projected[:, 0], X_projected[:, 1], c=periods, cmap='viridis', alpha=0.6, s=20)
    plt.colorbar(scatter, ax=ax, label='Period')
    
    title = config.title or "State Space Projection (PCA)"
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(config.xlabel or "First Principal Component", fontsize=12)
    ax.set_ylabel(config.ylabel or "Second Principal Component", fontsize=12)
    
    if config.show_grid:
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=config.dpi, bbox_inches='tight')
    
    return fig


def _project_simple(
    states: List[List[int]],
    periods: List[int],
    config: VisualizationConfig,
    output_file: Optional[str]
) -> Any:
    """Simple 2D projection using first two dimensions."""
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib required for projections")
    
    import matplotlib.pyplot as plt
    import numpy as np
    
    # Extract first two dimensions
    x_coords = [s[0] if len(s) > 0 else 0 for s in states]
    y_coords = [s[1] if len(s) > 1 else 0 for s in states]
    
    fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)
    
    scatter = ax.scatter(x_coords, y_coords, c=periods, cmap='viridis', alpha=0.6, s=20)
    plt.colorbar(scatter, ax=ax, label='Period')
    
    title = config.title or "State Space Projection (Simple)"
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(config.xlabel or "First Dimension", fontsize=12)
    ax.set_ylabel(config.ylabel or "Second Dimension", fontsize=12)
    
    if config.show_grid:
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=config.dpi, bbox_inches='tight')
    
    return fig
