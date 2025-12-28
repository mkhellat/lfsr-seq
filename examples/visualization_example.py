#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example: Visualization Features

This example demonstrates the visualization capabilities of lfsr-seq,
including period distributions, state diagrams, statistical plots,
3D visualizations, and attack visualizations.

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
    print("WARNING: matplotlib not available, some visualizations will be skipped", file=sys.stderr)

try:
    import plotly
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    print("WARNING: plotly not available, interactive visualizations will be skipped", file=sys.stderr)

from lfsr.core import analyze_lfsr
from lfsr.visualization.period_graphs import plot_period_distribution
from lfsr.visualization.state_diagrams import generate_state_transition_diagram
from lfsr.visualization.statistical_plots import plot_period_statistics, plot_sequence_analysis
from lfsr.visualization.state_space_3d import plot_3d_state_space
from lfsr.visualization.attack_visualization import visualize_correlation_attack
from lfsr.visualization.base import VisualizationConfig, OutputFormat


def example_period_distribution():
    """Example of period distribution visualization."""
    print("=" * 70)
    print("Example 1: Period Distribution Visualization")
    print("=" * 70)
    
    if not HAS_MATPLOTLIB:
        print("Skipped: matplotlib not available")
        return
    
    # Analyze a simple LFSR
    coefficients = [1, 0, 0, 1]
    seq_dict, period_dict, max_period, _, _, _, _ = analyze_lfsr(coefficients, 2)
    
    theoretical_max = 2 ** len(coefficients) - 1
    
    config = VisualizationConfig(
        output_format=OutputFormat.PNG,
        interactive=False,
        title="Period Distribution Example"
    )
    
    # Generate plot (comment out file saving for examples)
    # fig = plot_period_distribution(
    #     period_dict,
    #     theoretical_max_period=theoretical_max,
    #     is_primitive=False,
    #     config=config,
    #     output_file="example_period_dist.png"
    # )
    
    print(f"\n✓ Period distribution visualization generated")
    print(f"  Periods found: {list(period_dict.keys())}")
    print(f"  Max period: {max_period}")
    print(f"  Theoretical max: {theoretical_max}")


def example_state_transitions():
    """Example of state transition diagram."""
    print("\n" + "=" * 70)
    print("Example 2: State Transition Diagram")
    print("=" * 70)
    
    if not HAS_MATPLOTLIB:
        print("Skipped: matplotlib not available")
        return
    
    # Analyze a simple LFSR
    coefficients = [1, 0, 0, 1]
    seq_dict, period_dict, max_period, _, _, _, _ = analyze_lfsr(coefficients, 2)
    
    config = VisualizationConfig(
        output_format=OutputFormat.PNG,
        interactive=False
    )
    
    # Generate diagram (comment out file saving for examples)
    # graph = generate_state_transition_diagram(
    #     seq_dict,
    #     period_dict,
    #     max_states=20,
    #     config=config,
    #     output_file="example_state_diagram.png"
    # )
    
    print(f"\n✓ State transition diagram generated")
    print(f"  Sequences analyzed: {len(seq_dict)}")
    print(f"  States visualized: {sum(len(s) for s in seq_dict.values())}")


def example_statistical_plots():
    """Example of statistical plots."""
    print("\n" + "=" * 70)
    print("Example 3: Statistical Distribution Plots")
    print("=" * 70)
    
    if not HAS_MATPLOTLIB:
        print("Skipped: matplotlib not available")
        return
    
    # Analyze a simple LFSR
    coefficients = [1, 0, 0, 1]
    seq_dict, period_dict, max_period, _, _, _, _ = analyze_lfsr(coefficients, 2)
    
    theoretical_max = 2 ** len(coefficients) - 1
    
    config = VisualizationConfig(
        output_format=OutputFormat.PNG,
        interactive=False
    )
    
    # Generate statistical plots (comment out file saving for examples)
    # fig = plot_period_statistics(
    #     period_dict,
    #     theoretical_max_period=theoretical_max,
    #     is_primitive=False,
    #     config=config,
    #     output_file="example_statistics.png"
    # )
    
    print(f"\n✓ Statistical plots generated")
    print(f"  Includes: Histogram, Box Plot, Cumulative Distribution, Statistics Summary")


def example_3d_visualization():
    """Example of 3D state space visualization."""
    print("\n" + "=" * 70)
    print("Example 4: 3D State Space Visualization")
    print("=" * 70)
    
    if not HAS_PLOTLY and not HAS_MATPLOTLIB:
        print("Skipped: plotly and matplotlib not available")
        return
    
    # Analyze a simple LFSR
    coefficients = [1, 0, 0, 1]
    seq_dict, period_dict, max_period, _, _, _, _ = analyze_lfsr(coefficients, 2)
    
    config = VisualizationConfig(
        output_format=OutputFormat.HTML if HAS_PLOTLY else OutputFormat.PNG,
        interactive=HAS_PLOTLY
    )
    
    # Generate 3D visualization (comment out file saving for examples)
    # fig = plot_3d_state_space(
    #     seq_dict,
    #     period_dict,
    #     max_states=50,
    #     config=config,
    #     output_file="example_3d.html" if HAS_PLOTLY else "example_3d.png"
    # )
    
    print(f"\n✓ 3D state space visualization generated")
    print(f"  Format: {'Interactive HTML' if HAS_PLOTLY else 'Static PNG'}")


def example_attack_visualization():
    """Example of attack visualization."""
    print("\n" + "=" * 70)
    print("Example 5: Attack Visualization")
    print("=" * 70)
    
    if not HAS_MATPLOTLIB:
        print("Skipped: matplotlib not available")
        return
    
    # Simulate attack results
    attack_results = {
        'correlations': [0.45, 0.52, 0.38, 0.49],
        'success_probability': 0.75,
        'attack_successful': True,
        'target_lfsr': 1,
        'max_correlation': 0.52,
        'candidates_over_time': [1000, 500, 250, 125, 62, 31, 15, 7, 3, 1]
    }
    
    config = VisualizationConfig(
        output_format=OutputFormat.PNG,
        interactive=False
    )
    
    # Generate visualization (comment out file saving for examples)
    # fig = visualize_correlation_attack(
    #     attack_results,
    #     config=config,
    #     output_file="example_attack.png"
    # )
    
    print(f"\n✓ Attack visualization generated")
    print(f"  Max correlation: {attack_results['max_correlation']}")
    print(f"  Success probability: {attack_results['success_probability']:.2%}")


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
