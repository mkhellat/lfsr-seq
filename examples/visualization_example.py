#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example: Visualization Features

This example demonstrates the visualization capabilities, including period
distribution plots, state transition diagrams, statistical plots, 3D
visualizations, and attack visualizations.

Example Usage:
    python3 examples/visualization_example.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import SageMath
try:
    from sage.all import *
except ImportError:
    print("ERROR: SageMath is required for this example", file=sys.stderr)
    sys.exit(1)

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("WARNING: matplotlib not available, some visualizations will be skipped")

try:
    import plotly
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    print("WARNING: plotly not available, interactive visualizations will be skipped")

from lfsr.core import analyze_lfsr
from lfsr.visualization import (
    plot_period_distribution,
    generate_state_transition_diagram,
    plot_period_statistics,
    plot_3d_state_space,
    visualize_correlation_attack,
    VisualizationConfig,
    OutputFormat
)


def example_period_distribution():
    """Example of period distribution visualization."""
    print("=" * 70)
    print("Example 1: Period Distribution Visualization")
    print("=" * 70)
    
    # Analyze a simple LFSR
    coefficients = [1, 0, 0, 1]
    seq_dict, period_dict, max_period, _, _, _, _ = analyze_lfsr(coefficients, 2)
    
    theoretical_max = 2 ** len(coefficients) - 1
    
    print(f"\nPeriod distribution: {period_dict}")
    print(f"Maximum period: {max_period}")
    print(f"Theoretical maximum: {theoretical_max}")
    
    if HAS_MATPLOTLIB:
        config = VisualizationConfig(
            title="Period Distribution Example",
            output_format=OutputFormat.PNG
        )
        # Note: Commented out to avoid creating files in examples
        # fig = plot_period_distribution(
        #     period_dict,
        #     theoretical_max_period=theoretical_max,
        #     is_primitive=False,
        #     config=config,
        #     output_file="period_dist_example.png"
        # )
        print("\n✓ Period distribution visualization functionality demonstrated")
        print("  (File creation commented out to avoid creating files in examples)")
    else:
        print("\n⚠ matplotlib not available, skipping visualization")


def example_state_transitions():
    """Example of state transition diagram."""
    print("\n" + "=" * 70)
    print("Example 2: State Transition Diagram")
    print("=" * 70)
    
    coefficients = [1, 0, 0, 1]
    seq_dict, period_dict, _, _, _, _, _ = analyze_lfsr(coefficients, 2)
    
    print(f"\nNumber of sequences: {len(seq_dict)}")
    print(f"Periods: {list(period_dict.values())}")
    
    if HAS_MATPLOTLIB:
        config = VisualizationConfig(
            title="State Transition Diagram Example",
            output_format=OutputFormat.PNG
        )
        # Note: Commented out to avoid creating files in examples
        # graph = generate_state_transition_diagram(
        #     seq_dict,
        #     period_dict,
        #     max_states=20,
        #     config=config,
        #     output_file="transitions_example.png"
        # )
        print("\n✓ State transition diagram functionality demonstrated")
        print("  (File creation commented out to avoid creating files in examples)")
    else:
        print("\n⚠ matplotlib not available, skipping visualization")


def example_statistical_plots():
    """Example of statistical plots."""
    print("\n" + "=" * 70)
    print("Example 3: Statistical Distribution Plots")
    print("=" * 70)
    
    coefficients = [1, 0, 0, 1]
    seq_dict, period_dict, max_period, _, _, _, _ = analyze_lfsr(coefficients, 2)
    theoretical_max = 2 ** len(coefficients) - 1
    
    if HAS_MATPLOTLIB:
        config = VisualizationConfig(
            title="Period Statistics Example",
            output_format=OutputFormat.PNG
        )
        # Note: Commented out to avoid creating files in examples
        # fig = plot_period_statistics(
        #     period_dict,
        #     theoretical_max_period=theoretical_max,
        #     is_primitive=False,
        #     config=config,
        #     output_file="stats_example.png"
        # )
        print("\n✓ Statistical plots functionality demonstrated")
        print("  (File creation commented out to avoid creating files in examples)")
    else:
        print("\n⚠ matplotlib not available, skipping visualization")


def example_3d_visualization():
    """Example of 3D state space visualization."""
    print("\n" + "=" * 70)
    print("Example 4: 3D State Space Visualization")
    print("=" * 70)
    
    coefficients = [1, 0, 0, 1]
    seq_dict, period_dict, _, _, _, _, _ = analyze_lfsr(coefficients, 2)
    
    if HAS_PLOTLY:
        config = VisualizationConfig(
            title="3D State Space Example",
            interactive=True,
            output_format=OutputFormat.HTML
        )
        # Note: Commented out to avoid creating files in examples
        # fig = plot_3d_state_space(
        #     seq_dict,
        #     period_dict,
        #     max_states=50,
        #     config=config,
        #     output_file="state_space_3d_example.html"
        # )
        print("\n✓ 3D state space visualization functionality demonstrated")
        print("  (File creation commented out to avoid creating files in examples)")
    else:
        print("\n⚠ plotly not available, skipping 3D visualization")


def example_attack_visualization():
    """Example of attack visualization."""
    print("\n" + "=" * 70)
    print("Example 5: Attack Visualization")
    print("=" * 70)
    
    # Simulated attack results
    attack_results = {
        'correlations': [0.5, 0.3, 0.7, 0.2],
        'success_probability': 0.75,
        'attack_successful': True,
        'iterations': 100
    }
    
    if HAS_MATPLOTLIB:
        config = VisualizationConfig(
            title="Correlation Attack Visualization",
            output_format=OutputFormat.PNG
        )
        # Note: Commented out to avoid creating files in examples
        # fig = visualize_correlation_attack(
        #     attack_results,
        #     config=config,
        #     output_file="attack_viz_example.png"
        # )
        print("\n✓ Attack visualization functionality demonstrated")
        print("  (File creation commented out to avoid creating files in examples)")
    else:
        print("\n⚠ matplotlib not available, skipping visualization")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("Visualization Features Examples")
    print("=" * 70)
    print("\nThis script demonstrates visualization capabilities.")
    
    try:
        example_period_distribution()
        example_state_transitions()
        example_statistical_plots()
        example_3d_visualization()
        example_attack_visualization()
        
        print("\n" + "=" * 70)
        print("Examples Complete!")
        print("=" * 70)
        print("\nFor more information, see:")
        print("  - Visualization Guide: docs/visualization.rst")
        print("  - API Documentation: docs/api/visualization.rst")
        
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
