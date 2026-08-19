#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for lfsr.visualization.period_graphs.

Covers plot_period_distribution() and plot_period_vs_state(), both static
(matplotlib) and interactive (plotly) code paths. Assertions check figure
structure (axes count, bar heights/x-positions, line data, labels/titles)
rather than pixel comparison.
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pytest

from lfsr.visualization import period_graphs as pg
from lfsr.visualization.base import VisualizationConfig
from lfsr.visualization.period_graphs import (
    plot_period_distribution,
    plot_period_vs_state,
)


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


class TestPlotPeriodDistributionStatic:
    def test_returns_matplotlib_figure(self):
        fig = plot_period_distribution({1: 1, 3: 2, 6: 4, 12: 8})
        assert isinstance(fig, plt.Figure)

    def test_bar_heights_match_counts(self):
        period_dict = {1: 5, 3: 2, 15: 9}
        fig = plot_period_distribution(period_dict)
        ax = fig.axes[0]
        patches = ax.patches
        assert len(patches) == len(period_dict)
        heights = sorted(p.get_height() for p in patches)
        assert heights == sorted(period_dict.values())

    def test_bar_x_positions_match_periods(self):
        period_dict = {1: 5, 3: 2, 15: 9}
        fig = plot_period_distribution(period_dict)
        ax = fig.axes[0]
        x_positions = sorted(p.get_x() + p.get_width() / 2 for p in ax.patches)
        assert x_positions == sorted(float(p) for p in period_dict)

    def test_theoretical_max_line_added_when_provided(self):
        fig = plot_period_distribution({1: 1, 15: 15}, theoretical_max_period=15)
        ax = fig.axes[0]
        # axvline creates a Line2D; verify one exists at x=15.
        vlines = [line for line in ax.get_lines() if len(set(line.get_xdata())) == 1]
        assert any(line.get_xdata()[0] == 15 for line in vlines)
        assert ax.get_legend() is not None

    def test_no_theoretical_max_no_vline_no_legend(self):
        fig = plot_period_distribution({1: 1, 15: 15})
        ax = fig.axes[0]
        assert len(ax.get_lines()) == 0
        assert ax.get_legend() is None

    def test_default_title_includes_primitive_when_flagged(self):
        fig = plot_period_distribution({1: 1}, is_primitive=True)
        ax = fig.axes[0]
        assert "Primitive" in ax.get_title()

    def test_default_title_excludes_primitive_when_not_flagged(self):
        fig = plot_period_distribution({1: 1}, is_primitive=False)
        ax = fig.axes[0]
        assert "Primitive" not in ax.get_title()
        assert ax.get_title() == "Period Distribution"

    def test_custom_title_used_verbatim(self):
        config = VisualizationConfig(title="Custom Title")
        fig = plot_period_distribution({1: 1}, is_primitive=True, config=config)
        assert fig.axes[0].get_title() == "Custom Title"

    def test_default_axis_labels(self):
        fig = plot_period_distribution({1: 1})
        ax = fig.axes[0]
        assert ax.get_xlabel() == "Period"
        assert ax.get_ylabel() == "Number of Sequences"

    def test_custom_axis_labels(self):
        config = VisualizationConfig(xlabel="P", ylabel="N")
        fig = plot_period_distribution({1: 1}, config=config)
        ax = fig.axes[0]
        assert ax.get_xlabel() == "P"
        assert ax.get_ylabel() == "N"

    def test_saves_to_output_file(self, tmp_path):
        out = tmp_path / "dist.png"
        plot_period_distribution({1: 1, 3: 2}, output_file=str(out))
        assert out.exists()
        assert out.stat().st_size > 0

    def test_grid_toggle(self):
        fig_on = plot_period_distribution({1: 1}, config=VisualizationConfig(show_grid=True))
        fig_off = plot_period_distribution({1: 1}, config=VisualizationConfig(show_grid=False))
        assert any(line.get_visible() for line in fig_on.axes[0].get_xgridlines())
        assert not any(line.get_visible() for line in fig_off.axes[0].get_xgridlines())


class TestPlotPeriodDistributionInteractive:
    def test_returns_plotly_figure(self):
        config = VisualizationConfig(interactive=True)
        fig = plot_period_distribution({1: 1, 3: 2}, config=config)
        assert isinstance(fig, go.Figure)

    def test_bar_trace_data_matches_input(self):
        period_dict = {1: 5, 3: 2, 15: 9}
        config = VisualizationConfig(interactive=True)
        fig = plot_period_distribution(period_dict, config=config)
        bar_trace = fig.data[0]
        assert list(bar_trace.x) == list(period_dict.keys())
        assert list(bar_trace.y) == list(period_dict.values())

    def test_theoretical_max_vline_shape_added(self):
        config = VisualizationConfig(interactive=True)
        fig = plot_period_distribution({1: 1, 15: 15}, theoretical_max_period=15, config=config)
        # add_vline creates a shape on the layout
        assert len(fig.layout.shapes) >= 1

    def test_title_includes_primitive(self):
        config = VisualizationConfig(interactive=True)
        fig = plot_period_distribution({1: 1}, is_primitive=True, config=config)
        assert "Primitive" in fig.layout.title.text

    def test_saves_html_output_file(self, tmp_path):
        out = tmp_path / "dist.html"
        config = VisualizationConfig(interactive=True)
        plot_period_distribution({1: 1, 3: 2}, config=config, output_file=str(out))
        assert out.exists()
        assert "plotly" in out.read_text().lower()

    def test_saves_non_html_output_file_via_write_image(self, tmp_path, monkeypatch):
        """Covers the `else: fig.write_image(output_file)` branch (line
        ~187), taken when output_file doesn't end in '.html'. Real
        static image export requires the optional "kaleido" package
        (not installed in this venv), so monkeypatch go.Figure.write_image
        with a stub that records the call, isolating this
        branch-selection logic from kaleido's actual availability."""
        calls = []
        monkeypatch.setattr(
            go.Figure, "write_image", lambda self, path: calls.append(path)
        )
        out = tmp_path / "dist.png"
        config = VisualizationConfig(interactive=True)
        plot_period_distribution({1: 1, 3: 2}, config=config, output_file=str(out))
        assert calls == [str(out)]


class TestPlotPeriodDistributionDispatch:
    """Covers plot_period_distribution's top-level backend-selection
    else branch (line ~80): `raise ImportError(...)` when neither
    plotly nor matplotlib is available."""

    def test_raises_when_neither_backend_available(self, monkeypatch):
        monkeypatch.setattr(pg, "HAS_PLOTLY", False)
        monkeypatch.setattr(pg, "HAS_MATPLOTLIB", False)
        with pytest.raises(ImportError, match="matplotlib or plotly"):
            plot_period_distribution({1: 1, 3: 2})


class TestPlotPeriodVsStateStatic:
    def test_returns_matplotlib_figure(self):
        pairs = [([1, 0, 0], 3), ([0, 1, 0], 7), ([1, 1, 0], 1)]
        fig = plot_period_vs_state(pairs)
        assert isinstance(fig, plt.Figure)

    def test_scatter_points_match_periods(self):
        pairs = [([1, 0, 0], 3), ([0, 1, 0], 7), ([1, 1, 0], 1)]
        fig = plot_period_vs_state(pairs)
        ax = fig.axes[0]
        collection = ax.collections[0]
        offsets = collection.get_offsets()
        y_values = sorted(offsets[:, 1].tolist())
        assert y_values == sorted(p for _, p in pairs)

    def test_x_indices_are_sequential(self):
        pairs = [([1], 1), ([2], 2), ([3], 3), ([4], 4)]
        fig = plot_period_vs_state(pairs)
        ax = fig.axes[0]
        offsets = ax.collections[0].get_offsets()
        x_values = sorted(offsets[:, 0].tolist())
        assert x_values == [0.0, 1.0, 2.0, 3.0]

    def test_empty_pairs_raises_value_error(self):
        with pytest.raises(ValueError, match="No state-period pairs"):
            plot_period_vs_state([])

    def test_default_title_and_labels(self):
        fig = plot_period_vs_state([([1], 1)])
        ax = fig.axes[0]
        assert ax.get_title() == "Period vs Initial State"
        assert ax.get_xlabel() == "State Index"
        assert ax.get_ylabel() == "Period"

    def test_saves_to_output_file(self, tmp_path):
        out = tmp_path / "scatter.png"
        plot_period_vs_state([([1, 0], 3), ([0, 1], 5)], output_file=str(out))
        assert out.exists()


class TestPlotPeriodVsStateInteractive:
    def test_returns_plotly_figure(self):
        config = VisualizationConfig(interactive=True)
        pairs = [([1, 0], 3), ([0, 1], 5)]
        fig = plot_period_vs_state(pairs, config=config)
        assert isinstance(fig, go.Figure)

    def test_scatter_trace_matches_periods(self):
        config = VisualizationConfig(interactive=True)
        pairs = [([1, 0], 3), ([0, 1], 5), ([1, 1], 7)]
        fig = plot_period_vs_state(pairs, config=config)
        trace = fig.data[0]
        assert list(trace.y) == [3, 5, 7]
        assert trace.mode == "markers"

    def test_empty_pairs_raises_before_dispatch(self):
        config = VisualizationConfig(interactive=True)
        with pytest.raises(ValueError):
            plot_period_vs_state([], config=config)

    def test_saves_non_html_output_file_via_write_image(self, tmp_path, monkeypatch):
        """Covers the `else: fig.write_image(output_file)` branch (line
        ~294) for plot_period_vs_state's interactive backend, mirroring
        the equivalent test for plot_period_distribution above."""
        calls = []
        monkeypatch.setattr(
            go.Figure, "write_image", lambda self, path: calls.append(path)
        )
        out = tmp_path / "scatter.png"
        config = VisualizationConfig(interactive=True)
        pairs = [([1, 0], 3), ([0, 1], 5)]
        plot_period_vs_state(pairs, config=config, output_file=str(out))
        assert calls == [str(out)]


class TestPlotPeriodVsStateDispatch:
    """Covers plot_period_vs_state's top-level backend-selection else
    branch (line ~225): `raise ImportError(...)` when neither plotly
    nor matplotlib is available."""

    def test_raises_when_neither_backend_available(self, monkeypatch):
        monkeypatch.setattr(pg, "HAS_PLOTLY", False)
        monkeypatch.setattr(pg, "HAS_MATPLOTLIB", False)
        with pytest.raises(ImportError, match="matplotlib or plotly"):
            plot_period_vs_state([([1, 0], 3), ([0, 1], 5)])
