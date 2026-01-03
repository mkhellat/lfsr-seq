"""
Visualization module for LFSR analysis results.

This module provides visualization capabilities for LFSR analysis,
including interactive period graphs, state transition diagrams,
statistical plots, 3D visualizations, and attack visualizations.
"""

from lfsr.visualization.base import (
    BaseVisualization,
    VisualizationConfig,
    OutputFormat,
    check_visualization_dependencies
)

from lfsr.visualization.period_graphs import (
    plot_period_distribution,
    plot_period_vs_state
)

from lfsr.visualization.state_diagrams import (
    generate_state_transition_diagram,
    export_to_graphviz
)

from lfsr.visualization.statistical_plots import (
    plot_period_statistics,
    plot_sequence_analysis
)

from lfsr.visualization.state_space_3d import (
    plot_3d_state_space,
    plot_state_space_projection
)

from lfsr.visualization.attack_visualization import (
    visualize_correlation_attack,
    visualize_attack_comparison
)

__all__ = [
    "BaseVisualization",
    "VisualizationConfig",
    "OutputFormat",
    "check_visualization_dependencies",
    "plot_period_distribution",
    "plot_period_vs_state",
    "generate_state_transition_diagram",
    "export_to_graphviz",
    "plot_period_statistics",
    "plot_sequence_analysis",
    "plot_3d_state_space",
    "plot_state_space_projection",
    "visualize_correlation_attack",
    "visualize_attack_comparison",
]
