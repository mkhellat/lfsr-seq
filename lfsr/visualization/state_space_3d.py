#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
3D state space visualizations.

This module provides functions to create 3D visualizations of LFSR state
spaces, including 3D scatter plots and projections.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from lfsr.visualization.base import (
    VisualizationConfig,
    OutputFormat,
    HAS_PLOTLY,
    HAS_MATPLOTLIB
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
    
    This function generates a 3D scatter plot showing states in the state
    space, with coloring by period or other properties.
    
    **Key Terminology**:
    
    - **3D Visualization**: A three-dimensional graphical representation
      that allows viewing data from different angles and perspectives.
    
    - **State Space**: The set of all possible states an LFSR can be in.
      For an LFSR of degree d over GF(q), the state space has q^d elements.
    
    - **Interactive 3D Plot**: A 3D plot that allows rotation, zooming,
      and panning, typically using libraries like Plotly.
    
    - **State Coloring**: Assigning colors to states based on their
      properties (e.g., period, cycle membership).
    
    Args:
        state_sequences: Dictionary mapping sequence number to list of states
        period_dict: Dictionary mapping sequence number to period
        max_states: Maximum number of states to visualize
        config: Optional visualization configuration
        output_file: Optional output filename
    
    Returns:
        Plot object (plotly figure for interactive, matplotlib for static)
    
    Example:
        >>> from lfsr.visualization.state_space_3d import plot_3d_state_space
        >>> sequences = {0: [[1,0,0], [0,1,0], [0,0,1]]}
        >>> periods = {0: 3}
        >>> fig = plot_3d_state_space(sequences, periods)
    """
    config = config or VisualizationConfig()
    
    # Extract states and periods
    states_3d = []
    periods_list = []
    state_count = 0
    
    for seq_num, sequence in state_sequences.items():
        if state_count >= max_states:
            break
        
        period = period_dict.get(seq_num, len(sequence))
        
        for state in sequence[:min(len(sequence), max_states - state_count)]:
            if len(state) >= 3:
                states_3d.append([state[0], state[1], state[2]])
                periods_list.append(period)
                state_count += 1
                if state_count >= max_states:
                    break
    
    if not states_3d:
        raise ValueError("No states with at least 3 dimensions found")
    
    states_array = np.array(states_3d)
    
    if config.interactive and HAS_PLOTLY:
        return _plot_3d_interactive(states_array, periods_list, config, output_file)
    elif HAS_MATPLOTLIB:
        return _plot_3d_static(states_array, periods_list, config, output_file)
    else:
        raise ImportError("plotly or matplotlib required for 3D visualization")


def _plot_3d_interactive(
    states: np.ndarray,
    periods: List[int],
    config: VisualizationConfig,
    output_file: Optional[str]
) -> Any:
    """Create interactive 3D plot using plotly."""
    import plotly.graph_objects as go
    
    # Create color map based on periods
    unique_periods = list(set(periods))
    color_map = {p: i for i, p in enumerate(unique_periods)}
    colors = [color_map[p] for p in periods]
    
    fig = go.Figure(data=go.Scatter3d(
        x=states[:, 0],
        y=states[:, 1],
        z=states[:, 2],
        mode='markers',
        marker=dict(
            size=5,
            color=colors,
            colorscale='Viridis',
            opacity=0.7,
            colorbar=dict(title="Period")
        ),
        text=[f"Period: {p}" for p in periods],
        hovertemplate='State: (%{x}, %{y}, %{z})<br>Period: %{text}<extra></extra>'
    ))
    
    fig.update_layout(
        title=config.title or "3D State Space Visualization",
        scene=dict(
            xaxis_title="State[0]",
            yaxis_title="State[1]",
            zaxis_title="State[2]"
        ),
        width=config.width * 80,
        height=config.height * 80
    )
    
    if output_file:
        if output_file.endswith('.html'):
            fig.write_html(output_file)
        else:
            fig.write_image(output_file)
    
    return fig


def _plot_3d_static(
    states: np.ndarray,
    periods: List[int],
    config: VisualizationConfig,
    output_file: Optional[str]
) -> Any:
    """Create static 3D plot using matplotlib."""
    from mpl_toolkits.mplot3d import Axes3D
    import matplotlib.pyplot as plt
    
    fig = plt.figure(figsize=(config.width, config.height), dpi=config.dpi)
    ax = fig.add_subplot(111, projection='3d')
    
    # Create color map based on periods
    unique_periods = list(set(periods))
    color_map = {p: i / len(unique_periods) for i, p in enumerate(unique_periods)}
    colors = [color_map[p] for p in periods]
    
    scatter = ax.scatter(
        states[:, 0],
        states[:, 1],
        states[:, 2],
        c=colors,
        cmap='viridis',
        s=20,
        alpha=0.7
    )
    
    ax.set_xlabel("State[0]", fontsize=10)
    ax.set_ylabel("State[1]", fontsize=10)
    ax.set_zlabel("State[2]", fontsize=10)
    ax.set_title(config.title or "3D State Space Visualization", fontsize=14, fontweight='bold')
    
    plt.colorbar(scatter, ax=ax, label="Period")
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=config.dpi, bbox_inches='tight')
    
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
    Create 2D projection of state space using dimensionality reduction.
    
    This function projects high-dimensional state spaces to 2D for
    visualization using methods like PCA or t-SNE.
    
    **Key Terminology**:
    
    - **Dimensionality Reduction**: Techniques for reducing the number of
      dimensions in data while preserving important structure. Common methods
      include PCA (Principal Component Analysis) and t-SNE (t-distributed
      Stochastic Neighbor Embedding).
    
    - **PCA (Principal Component Analysis)**: A linear dimensionality
      reduction technique that finds the directions of maximum variance in
      the data.
    
    - **Projection**: Mapping high-dimensional data to lower dimensions
      (e.g., 3D to 2D) for visualization.
    
    Args:
        state_sequences: Dictionary mapping sequence number to list of states
        period_dict: Dictionary mapping sequence number to period
        projection_method: Method to use ("pca" or "tsne")
        max_states: Maximum number of states to include
        config: Optional visualization configuration
        output_file: Optional output filename
    
    Returns:
        Plot object
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib required for projections")
    
    import matplotlib.pyplot as plt
    
    # Extract states
    states_list = []
    periods_list = []
    state_count = 0
    
    for seq_num, sequence in state_sequences.items():
        if state_count >= max_states:
            break
        
        period = period_dict.get(seq_num, len(sequence))
        
        for state in sequence[:min(len(sequence), max_states - state_count)]:
            states_list.append(list(state))
            periods_list.append(period)
            state_count += 1
            if state_count >= max_states:
                break
    
    if not states_list:
        raise ValueError("No states found")
    
    states_array = np.array(states_list)
    
    # Apply projection
    if projection_method.lower() == "pca":
        from sklearn.decomposition import PCA
        pca = PCA(n_components=2)
        projected = pca.fit_transform(states_array)
    elif projection_method.lower() == "tsne":
        try:
            from sklearn.manifold import TSNE
            tsne = TSNE(n_components=2, random_state=42)
            projected = tsne.fit_transform(states_array)
        except ImportError:
            raise ImportError("scikit-learn required for t-SNE projection")
    else:
        raise ValueError(f"Unknown projection method: {projection_method}")
    
    # Create plot
    config = config or VisualizationConfig()
    fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)
    
    # Color by period
    unique_periods = list(set(periods_list))
    color_map = {p: i / len(unique_periods) for i, p in enumerate(unique_periods)}
    colors = [color_map[p] for p in periods_list]
    
    scatter = ax.scatter(projected[:, 0], projected[:, 1], c=colors, cmap='viridis', s=20, alpha=0.7)
    
    ax.set_xlabel(f"{projection_method.upper()} Component 1", fontsize=10)
    ax.set_ylabel(f"{projection_method.upper()} Component 2", fontsize=10)
    ax.set_title(config.title or f"State Space Projection ({projection_method.upper()})", fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    plt.colorbar(scatter, ax=ax, label="Period")
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=config.dpi, bbox_inches='tight')
    
    return fig
