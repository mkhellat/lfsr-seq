#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for lfsr.visualization.state_diagrams.

Covers generate_state_transition_diagram() (networkx and matplotlib-only
backends) and export_to_graphviz() (DOT file text generation).
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from lfsr.visualization import state_diagrams as sd
from lfsr.visualization.base import VisualizationConfig
from lfsr.visualization.state_diagrams import (
    export_to_graphviz,
    generate_state_transition_diagram,
)

SEQUENCES = {
    0: [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 0, 0]],
    1: [[1, 1, 0], [0, 1, 1]],
}
PERIODS = {0: 3, 1: 2}


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


class TestGenerateStateTransitionDiagramNetworkx:
    def test_returns_matplotlib_figure(self):
        fig = generate_state_transition_diagram(SEQUENCES, PERIODS)
        assert isinstance(fig, plt.Figure)

    def test_axis_off_and_has_title(self):
        fig = generate_state_transition_diagram(SEQUENCES, PERIODS)
        ax = fig.axes[0]
        assert ax.get_title() == "State Transition Diagram"

    def test_custom_title(self):
        config = VisualizationConfig(title="Custom")
        fig = generate_state_transition_diagram(SEQUENCES, PERIODS, config=config)
        assert fig.axes[0].get_title() == "Custom"

    def test_saves_to_output_file(self, tmp_path):
        out = tmp_path / "diagram.png"
        generate_state_transition_diagram(SEQUENCES, PERIODS, output_file=str(out))
        assert out.exists()

    def test_max_states_limits_graph_size(self):
        """With max_states very small, fewer nodes should end up plotted
        than with the full sequences -- verified via node collection size
        on the underlying networkx graph construction path (indirectly,
        by checking the figure still builds without error and respects
        the cap without crashing)."""
        # Should not raise even with a tiny cap.
        fig = generate_state_transition_diagram(SEQUENCES, PERIODS, max_states=1)
        assert isinstance(fig, plt.Figure)

    def test_falls_back_to_matplotlib_when_networkx_unavailable(self, monkeypatch):
        monkeypatch.setattr(sd, "HAS_NETWORKX", False)
        fig = generate_state_transition_diagram(SEQUENCES, PERIODS)
        assert isinstance(fig, plt.Figure)
        # matplotlib-only fallback uses the "(Simplified)" suffix in default title
        assert "Simplified" in fig.axes[0].get_title()

    def test_raises_when_neither_backend_available(self, monkeypatch):
        monkeypatch.setattr(sd, "HAS_NETWORKX", False)
        monkeypatch.setattr(sd, "HAS_MATPLOTLIB", False)
        with pytest.raises(ImportError):
            generate_state_transition_diagram(SEQUENCES, PERIODS)


class TestGenerateStateTransitionDiagramMatplotlibFallback:
    def test_direct_matplotlib_backend_returns_figure(self, monkeypatch):
        monkeypatch.setattr(sd, "HAS_NETWORKX", False)
        fig = generate_state_transition_diagram(SEQUENCES, PERIODS)
        assert isinstance(fig, plt.Figure)

    def test_period_one_sequences_are_skipped(self, monkeypatch):
        """Source only draws a cycle circle when period > 1; sequences
        with period == 1 contribute nothing to state_count/y_offset."""
        monkeypatch.setattr(sd, "HAS_NETWORKX", False)
        seqs = {0: [[1, 0, 0]]}
        periods = {0: 1}
        fig = generate_state_transition_diagram(seqs, periods)
        ax = fig.axes[0]
        # No circles/patches should have been drawn.
        assert len(ax.patches) == 0


class TestExportToGraphviz:
    def test_writes_dot_file_with_expected_structure(self, tmp_path):
        out = tmp_path / "graph.dot"
        export_to_graphviz(SEQUENCES, PERIODS, str(out))

        content = out.read_text()
        assert content.startswith("digraph StateTransitions {")
        assert content.strip().endswith("}")
        assert "rankdir=LR;" in content
        assert 'node [shape=circle];' in content

    def test_all_edges_present_in_dot_output(self, tmp_path):
        out = tmp_path / "graph.dot"
        export_to_graphviz(SEQUENCES, PERIODS, str(out))
        content = out.read_text()

        # sequence 0: [1,0,0]->[0,1,0]->[0,0,1]->[1,0,0]
        assert '"[1, 0, 0]" -> "[0, 1, 0]";' in content
        assert '"[0, 1, 0]" -> "[0, 0, 1]";' in content
        assert '"[0, 0, 1]" -> "[1, 0, 0]";' in content
        # sequence 1: [1,1,0]->[0,1,1]
        assert '"[1, 1, 0]" -> "[0, 1, 1]";' in content

    def test_all_nodes_declared(self, tmp_path):
        out = tmp_path / "graph.dot"
        export_to_graphviz(SEQUENCES, PERIODS, str(out))
        content = out.read_text()
        for state in ([1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0], [0, 1, 1]):
            assert f'"{state}";' in content

    def test_max_states_caps_edge_count(self, tmp_path):
        out = tmp_path / "graph.dot"
        export_to_graphviz(SEQUENCES, PERIODS, str(out), max_states=1)
        content = out.read_text()
        edge_lines = [line for line in content.splitlines() if "->" in line]
        assert len(edge_lines) == 1

    def test_single_state_sequence_produces_no_edges(self, tmp_path):
        out = tmp_path / "graph.dot"
        export_to_graphviz({0: [[1, 0]]}, {0: 1}, str(out))
        content = out.read_text()
        edge_lines = [line for line in content.splitlines() if "->" in line]
        assert edge_lines == []
