#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
State transition diagram visualizations.

This module provides functions to generate state transition diagrams
showing how LFSR states transition and form cycles.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict

from lfsr.visualization.base import (
    VisualizationConfig,
    OutputFormat,
    HAS_MATPLOTLIB,
    HAS_NETWORKX
)


def generate_state_transition_diagram(
    state_sequences: Dict[int, List[Any]],
    period_dict: Dict[int, int],
    max_states: int = 50,
    config: Optional[VisualizationConfig] = None,
    output_file: Optional[str] = None
) -> Any:
    """
    Generate state transition diagram.
    
    This function creates a graph showing state transitions and cycles
    in the LFSR state space.
    
    **Key Terminology**:
    
    - **State Transition Diagram**: A graph representation showing how
      LFSR states transition from one to another. Each node represents
      a state, and each edge represents a transition.
    
    - **Cycle**: A closed path in the state transition diagram where
      states form a loop. The length of the cycle equals the period
      of the sequence starting from any state in that cycle.
    
    - **Graph Visualization**: A visual representation of a graph
      structure, typically using nodes (vertices) and edges (connections).
    
    - **Graphviz**: A tool for graph visualization that can generate
      diagrams in various formats (PNG, SVG, PDF).
    
    Args:
        state_sequences: Dictionary mapping sequence number to list of states
        period_dict: Dictionary mapping sequence number to period
        max_states: Maximum number of states to include (for large state spaces)
        config: Optional visualization configuration
        output_file: Optional output filename
    
    Returns:
        Graph object or image file
    
    Example:
        >>> from lfsr.visualization.state_diagrams import generate_state_transition_diagram
        >>> sequences = {0: [[1,0,0], [0,1,0], [0,0,1], [1,0,0]]}
        >>> periods = {0: 3}
        >>> graph = generate_state_transition_diagram(sequences, periods)
    """
    config = config or VisualizationConfig()
    
    if HAS_NETWORKX:
        return _generate_diagram_networkx(
            state_sequences, period_dict, max_states, config, output_file
        )
    elif HAS_MATPLOTLIB:
        return _generate_diagram_matplotlib(
            state_sequences, period_dict, max_states, config, output_file
        )
    else:
        raise ImportError("networkx or matplotlib required for state diagrams")


def _generate_diagram_networkx(
    state_sequences: Dict[int, List[Any]],
    period_dict: Dict[int, int],
    max_states: int,
    config: VisualizationConfig,
    output_file: Optional[str]
) -> Any:
    """Generate state transition diagram using NetworkX."""
    import networkx as nx
    import matplotlib.pyplot as plt
    
    G = nx.DiGraph()
    
    # Build graph from state sequences
    state_count = 0
    for seq_num, sequence in state_sequences.items():
        if state_count >= max_states:
            break
        
        period = period_dict.get(seq_num, len(sequence))
        
        # Add nodes and edges
        for i in range(len(sequence) - 1):
            state_str = str(sequence[i])
            next_state_str = str(sequence[i + 1])
            
            if state_str not in G:
                G.add_node(state_str)
                state_count += 1
                if state_count >= max_states:
                    break
            
            if next_state_str not in G:
                G.add_node(next_state_str)
                state_count += 1
                if state_count >= max_states:
                    break
            
            G.add_edge(state_str, next_state_str)
    
    # Create visualization
    fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)
    
    # Use spring layout for positioning
    pos = nx.spring_layout(G, k=1, iterations=50)
    
    # Draw nodes and edges
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color='lightblue', node_size=500, alpha=0.7)
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color='gray', alpha=0.5, arrows=True, arrowsize=20)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=8)
    
    ax.set_title(config.title or "State Transition Diagram", fontsize=14, fontweight='bold')
    ax.axis('off')
    
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=config.dpi, bbox_inches='tight')
    
    return fig


def _generate_diagram_matplotlib(
    state_sequences: Dict[int, List[Any]],
    period_dict: Dict[int, int],
    max_states: int,
    config: VisualizationConfig,
    output_file: Optional[str]
) -> Any:
    """Generate simplified state transition diagram using matplotlib."""
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    
    fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)
    
    # Simplified visualization: show cycles as circular arrangements
    state_count = 0
    y_offset = 0
    
    for seq_num, sequence in state_sequences.items():
        if state_count >= max_states:
            break
        
        period = period_dict.get(seq_num, len(sequence))
        if period > 1:
            # Show cycle as a circle
            cycle_states = sequence[:period]
            
            # Draw cycle
            for i, state in enumerate(cycle_states):
                angle = 2 * 3.14159 * i / period
                x = 0.5 + 0.3 * np.cos(angle)
                y = 0.5 + y_offset + 0.3 * np.sin(angle)
                
                circle = plt.Circle((x, y), 0.05, color='lightblue', alpha=0.7)
                ax.add_patch(circle)
                ax.text(x, y, str(state)[:3], ha='center', va='center', fontsize=6)
            
            y_offset += 0.8
            state_count += period
            
            if state_count >= max_states:
                break
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, y_offset + 0.5)
    ax.set_title(config.title or "State Transition Diagram (Simplified)", fontsize=14, fontweight='bold')
    ax.axis('off')
    
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=config.dpi, bbox_inches='tight')
    
    return fig


def export_to_graphviz(
    state_sequences: Dict[int, List[Any]],
    period_dict: Dict[int, int],
    output_file: str,
    max_states: int = 50
) -> None:
    """
    Export state transition diagram to Graphviz DOT format.
    
    This function generates a Graphviz DOT file that can be rendered
    using the Graphviz tools (dot, neato, etc.).
    
    Args:
        state_sequences: Dictionary mapping sequence number to list of states
        period_dict: Dictionary mapping sequence number to period
        output_file: Output DOT filename
        max_states: Maximum number of states to include
    """
    state_count = 0
    edges = []
    nodes = set()
    
    for seq_num, sequence in state_sequences.items():
        if state_count >= max_states:
            break
        
        for i in range(len(sequence) - 1):
            state_str = str(sequence[i])
            next_state_str = str(sequence[i + 1])
            
            nodes.add(state_str)
            nodes.add(next_state_str)
            edges.append((state_str, next_state_str))
            
            state_count += 1
            if state_count >= max_states:
                break
    
    # Write DOT file
    with open(output_file, 'w') as f:
        f.write("digraph StateTransitions {\n")
        f.write("  rankdir=LR;\n")
        f.write("  node [shape=circle];\n")
        
        for node in nodes:
            f.write(f'  "{node}";\n')
        
        for edge in edges:
            f.write(f'  "{edge[0]}" -> "{edge[1]}";\n')
        
        f.write("}\n")
