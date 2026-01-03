#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Attack visualization functions.

This module provides functions to visualize cryptanalytic attacks,
including correlation attacks, algebraic attacks, and attack progress.
"""

from typing import Any, Dict, List, Optional, Tuple

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
      correlation attack results, showing how correlation coefficients
      vary and how the attack progresses.
    
    - **Correlation Coefficient**: A measure of linear relationship between
      two variables, ranging from -1 to 1. In correlation attacks, this
      measures the correlation between keystream and LFSR output.
    
    - **Attack Progress**: Visualization showing how the attack progresses
      over time, including success probability and candidate reduction.
    
    Args:
        correlation_results: Dictionary with correlation attack results
        config: Optional visualization configuration
        output_file: Optional output filename
    
    Returns:
        Plot object
    """
    config = config or VisualizationConfig()
    
    if config.interactive and HAS_PLOTLY:
        return _visualize_correlation_interactive(correlation_results, config, output_file)
    elif HAS_MATPLOTLIB:
        return _visualize_correlation_static(correlation_results, config, output_file)
    else:
        raise ImportError("matplotlib or plotly required for visualization")


def _visualize_correlation_static(
    results: Dict[str, Any],
    config: VisualizationConfig,
    output_file: Optional[str]
) -> Any:
    """Create static correlation attack visualization."""
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(2, 2, figsize=(config.width, config.height), dpi=config.dpi)
    fig.suptitle(config.title or "Correlation Attack Analysis", fontsize=16, fontweight='bold')
    
    # 1. Correlation coefficients
    ax1 = axes[0, 0]
    if 'correlations' in results:
        correlations = results['correlations']
        lfsr_indices = range(len(correlations))
        ax1.bar(lfsr_indices, correlations, alpha=0.7, edgecolor='black', linewidth=0.5)
        ax1.axhline(0.5, color='red', linestyle='--', linewidth=1, label='Threshold (0.5)')
        ax1.set_xlabel("LFSR Index", fontsize=10)
        ax1.set_ylabel("Correlation Coefficient", fontsize=10)
        ax1.set_title("Correlation Coefficients", fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
    
    # 2. Success probability
    ax2 = axes[0, 1]
    if 'success_probability' in results:
        prob = results['success_probability']
        ax2.barh(['Attack'], [prob], alpha=0.7, color='green' if prob > 0.5 else 'orange')
        ax2.set_xlabel("Success Probability", fontsize=10)
        ax2.set_title("Attack Success Probability", fontsize=12, fontweight='bold')
        ax2.set_xlim(0, 1)
        ax2.grid(True, alpha=0.3, axis='x')
    
    # 3. Candidate reduction (if available)
    ax3 = axes[1, 0]
    if 'candidates_over_time' in results:
        candidates = results['candidates_over_time']
        iterations = range(len(candidates))
        ax3.plot(iterations, candidates, marker='o', linewidth=2)
        ax3.set_xlabel("Iteration", fontsize=10)
        ax3.set_ylabel("Number of Candidates", fontsize=10)
        ax3.set_title("Candidate Reduction", fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3)
    
    # 4. Attack summary
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    summary_text = "Correlation Attack Summary\n\n"
    if 'target_lfsr' in results:
        summary_text += f"Target LFSR: {results['target_lfsr']}\n"
    if 'max_correlation' in results:
        summary_text += f"Max Correlation: {results['max_correlation']:.4f}\n"
    if 'success_probability' in results:
        summary_text += f"Success Probability: {results['success_probability']:.2%}\n"
    if 'attack_successful' in results:
        summary_text += f"Attack Successful: {'Yes' if results['attack_successful'] else 'No'}\n"
    
    ax4.text(0.1, 0.5, summary_text, fontsize=11, family='monospace', verticalalignment='center')
    
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=config.dpi, bbox_inches='tight')
    
    return fig


def _visualize_correlation_interactive(
    results: Dict[str, Any],
    config: VisualizationConfig,
    output_file: Optional[str]
) -> Any:
    """Create interactive correlation attack visualization."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Correlation Coefficients", "Success Probability", "Candidate Reduction", "Summary"),
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "scatter"}, {"type": "table"}]]
    )
    
    # Correlation coefficients
    if 'correlations' in results:
        correlations = results['correlations']
        fig.add_trace(
            go.Bar(x=list(range(len(correlations))), y=correlations, name="Correlation"),
            row=1, col=1
        )
        fig.add_hline(y=0.5, line_dash="dash", line_color="red", row=1, col=1)
    
    # Success probability
    if 'success_probability' in results:
        prob = results['success_probability']
        fig.add_trace(
            go.Bar(x=['Attack'], y=[prob], name="Success", marker_color='green' if prob > 0.5 else 'orange'),
            row=1, col=2
        )
    
    # Candidate reduction
    if 'candidates_over_time' in results:
        candidates = results['candidates_over_time']
        fig.add_trace(
            go.Scatter(x=list(range(len(candidates))), y=candidates, mode='lines+markers', name="Candidates"),
            row=2, col=1
        )
    
    fig.update_layout(
        title=config.title or "Correlation Attack Analysis",
        height=config.height * 80,
        showlegend=False
    )
    
    if output_file:
        if output_file.endswith('.html'):
            fig.write_html(output_file)
        else:
            fig.write_image(output_file)
    
    return fig


def visualize_attack_comparison(
    attack_results: List[Dict[str, Any]],
    config: Optional[VisualizationConfig] = None,
    output_file: Optional[str] = None
) -> Any:
    """
    Compare multiple attack methods visually.
    
    This function creates side-by-side comparisons of different attack
    methods, showing performance, success rates, and resource usage.
    
    Args:
        attack_results: List of attack result dictionaries
        config: Optional visualization configuration
        output_file: Optional output filename
    
    Returns:
        Plot object
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib required for attack comparison")
    
    import matplotlib.pyplot as plt
    
    config = config or VisualizationConfig()
    
    fig, axes = plt.subplots(2, 2, figsize=(config.width, config.height), dpi=config.dpi)
    fig.suptitle(config.title or "Attack Method Comparison", fontsize=16, fontweight='bold')
    
    attack_names = [r.get('method_name', f"Method {i}") for i, r in enumerate(attack_results)]
    
    # 1. Success rates
    ax1 = axes[0, 0]
    success_rates = [r.get('success_rate', 0) for r in attack_results]
    ax1.bar(attack_names, success_rates, alpha=0.7, edgecolor='black', linewidth=0.5)
    ax1.set_ylabel("Success Rate", fontsize=10)
    ax1.set_title("Success Rates", fontsize=12, fontweight='bold')
    ax1.set_ylim(0, 1)
    ax1.grid(True, alpha=0.3, axis='y')
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 2. Execution times
    ax2 = axes[0, 1]
    execution_times = [r.get('execution_time', 0) for r in attack_results]
    ax2.bar(attack_names, execution_times, alpha=0.7, edgecolor='black', linewidth=0.5, color='orange')
    ax2.set_ylabel("Execution Time (seconds)", fontsize=10)
    ax2.set_title("Performance", fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 3. Resource usage (if available)
    ax3 = axes[1, 0]
    if any('memory_usage' in r for r in attack_results):
        memory_usage = [r.get('memory_usage', 0) for r in attack_results]
        ax3.bar(attack_names, memory_usage, alpha=0.7, edgecolor='black', linewidth=0.5, color='green')
        ax3.set_ylabel("Memory Usage (MB)", fontsize=10)
        ax3.set_title("Resource Usage", fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='y')
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
    else:
        ax3.axis('off')
        ax3.text(0.5, 0.5, "Resource usage data not available", ha='center', va='center')
    
    # 4. Summary table
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    table_data = [["Method", "Success", "Time (s)"]]
    for i, result in enumerate(attack_results):
        table_data.append([
            attack_names[i],
            f"{result.get('success_rate', 0):.2%}",
            f"{result.get('execution_time', 0):.2f}"
        ])
    
    table = ax4.table(cellText=table_data[1:], colLabels=table_data[0], cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=config.dpi, bbox_inches='tight')
    
    return fig
