#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for lfsr.visualization.state_space_3d.

Covers plot_3d_state_space() (matplotlib 3D + plotly Scatter3d) and
plot_state_space_projection() (PCA/t-SNE via scikit-learn, matplotlib
only).
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import pytest

from lfsr.visualization import state_space_3d as ss3d
from lfsr.visualization.base import VisualizationConfig
from lfsr.visualization.state_space_3d import (
    plot_3d_state_space,
    plot_state_space_projection,
)

SEQUENCES_3D = {
    0: [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
    1: [[1, 1, 0], [0, 1, 1], [1, 0, 1]],
}
PERIODS_3D = {0: 3, 1: 3}


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


class TestPlot3DStateSpaceStatic:
    def test_returns_matplotlib_figure(self):
        fig = plot_3d_state_space(SEQUENCES_3D, PERIODS_3D)
        assert isinstance(fig, plt.Figure)

    def test_scatter_point_count_matches_input_states(self):
        fig = plot_3d_state_space(SEQUENCES_3D, PERIODS_3D)
        ax = fig.axes[0]
        # scatter collection holds all points
        collection = ax.collections[0]
        n_points = collection._offsets3d[0].shape[0]
        total_states = sum(len(seq) for seq in SEQUENCES_3D.values())
        assert n_points == total_states

    def test_scatter_coordinates_match_first_three_dims(self):
        fig = plot_3d_state_space(SEQUENCES_3D, PERIODS_3D)
        ax = fig.axes[0]
        collection = ax.collections[0]
        xs, ys, zs = collection._offsets3d
        all_states = SEQUENCES_3D[0] + SEQUENCES_3D[1]
        expected_x = sorted(s[0] for s in all_states)
        assert sorted(xs.tolist()) == expected_x

    def test_states_with_fewer_than_3_dims_are_skipped(self):
        seqs = {0: [[1, 0], [0, 1]]}  # only 2D states
        with pytest.raises(ValueError, match="at least 3 dimensions"):
            plot_3d_state_space(seqs, {0: 2})

    def test_max_states_caps_point_count(self):
        fig = plot_3d_state_space(SEQUENCES_3D, PERIODS_3D, max_states=2)
        ax = fig.axes[0]
        collection = ax.collections[0]
        n_points = collection._offsets3d[0].shape[0]
        assert n_points == 2

    def test_axis_labels(self):
        fig = plot_3d_state_space(SEQUENCES_3D, PERIODS_3D)
        ax = fig.axes[0]
        assert ax.get_xlabel() == "State[0]"
        assert ax.get_ylabel() == "State[1]"
        assert ax.get_zlabel() == "State[2]"

    def test_default_and_custom_title(self):
        fig_default = plot_3d_state_space(SEQUENCES_3D, PERIODS_3D)
        assert fig_default.axes[0].get_title() == "3D State Space Visualization"

        config = VisualizationConfig(title="Custom 3D")
        fig_custom = plot_3d_state_space(SEQUENCES_3D, PERIODS_3D, config=config)
        assert fig_custom.axes[0].get_title() == "Custom 3D"

    def test_saves_to_output_file(self, tmp_path):
        out = tmp_path / "3d.png"
        plot_3d_state_space(SEQUENCES_3D, PERIODS_3D, output_file=str(out))
        assert out.exists()

    def test_raises_when_neither_backend_available(self, monkeypatch):
        monkeypatch.setattr(ss3d, "HAS_MATPLOTLIB", False)
        monkeypatch.setattr(ss3d, "HAS_PLOTLY", False)
        with pytest.raises(ImportError):
            plot_3d_state_space(SEQUENCES_3D, PERIODS_3D)


class TestPlot3DStateSpaceInteractive:
    def test_returns_plotly_figure(self):
        config = VisualizationConfig(interactive=True)
        fig = plot_3d_state_space(SEQUENCES_3D, PERIODS_3D, config=config)
        assert isinstance(fig, go.Figure)

    def test_scatter3d_trace_point_count(self):
        config = VisualizationConfig(interactive=True)
        fig = plot_3d_state_space(SEQUENCES_3D, PERIODS_3D, config=config)
        trace = fig.data[0]
        total_states = sum(len(seq) for seq in SEQUENCES_3D.values())
        assert len(trace.x) == total_states

    def test_saves_html_output(self, tmp_path):
        out = tmp_path / "3d.html"
        config = VisualizationConfig(interactive=True)
        plot_3d_state_space(SEQUENCES_3D, PERIODS_3D, config=config, output_file=str(out))
        assert out.exists()


class TestPlotStateSpaceProjectionPCA:
    def test_returns_matplotlib_figure(self):
        fig = plot_state_space_projection(SEQUENCES_3D, PERIODS_3D, projection_method="pca")
        assert isinstance(fig, plt.Figure)

    def test_raises_without_matplotlib(self, monkeypatch):
        monkeypatch.setattr(ss3d, "HAS_MATPLOTLIB", False)
        with pytest.raises(ImportError, match="matplotlib"):
            plot_state_space_projection(SEQUENCES_3D, PERIODS_3D)

    def test_scatter_point_count_matches_states(self):
        fig = plot_state_space_projection(SEQUENCES_3D, PERIODS_3D, projection_method="pca")
        ax = fig.axes[0]
        offsets = ax.collections[0].get_offsets()
        total_states = sum(len(seq) for seq in SEQUENCES_3D.values())
        assert offsets.shape[0] == total_states

    def test_pca_projection_matches_independent_sklearn_call(self):
        """Cross-check the actual PCA output (not just 'a plot appeared')
        against an independently-run sklearn.decomposition.PCA on the same
        input data, since PCA output depends on component sign convention
        that could silently differ if the module wrapped it incorrectly."""
        from sklearn.decomposition import PCA

        states_array = np.array(SEQUENCES_3D[0] + SEQUENCES_3D[1])
        expected = PCA(n_components=2).fit_transform(states_array)

        fig = plot_state_space_projection(SEQUENCES_3D, PERIODS_3D, projection_method="pca")
        ax = fig.axes[0]
        offsets = ax.collections[0].get_offsets()

        assert offsets.shape == expected.shape
        assert np.allclose(np.asarray(offsets), expected)

    def test_unknown_projection_method_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown projection method"):
            plot_state_space_projection(SEQUENCES_3D, PERIODS_3D, projection_method="magic")

    def test_no_states_raises_value_error(self):
        with pytest.raises(ValueError, match="No states found"):
            plot_state_space_projection({}, {})

    def test_axis_labels_reflect_method_name(self):
        fig = plot_state_space_projection(SEQUENCES_3D, PERIODS_3D, projection_method="pca")
        ax = fig.axes[0]
        assert ax.get_xlabel() == "PCA Component 1"
        assert ax.get_ylabel() == "PCA Component 2"

    def test_default_and_custom_title(self):
        fig_default = plot_state_space_projection(SEQUENCES_3D, PERIODS_3D)
        assert "PCA" in fig_default.axes[0].get_title()

        config = VisualizationConfig(title="Custom Proj")
        fig_custom = plot_state_space_projection(SEQUENCES_3D, PERIODS_3D, config=config)
        assert fig_custom.axes[0].get_title() == "Custom Proj"

    def test_saves_to_output_file(self, tmp_path):
        out = tmp_path / "proj.png"
        plot_state_space_projection(SEQUENCES_3D, PERIODS_3D, output_file=str(out))
        assert out.exists()

    def test_max_states_caps_point_count(self):
        fig = plot_state_space_projection(SEQUENCES_3D, PERIODS_3D, max_states=2)
        ax = fig.axes[0]
        offsets = ax.collections[0].get_offsets()
        assert offsets.shape[0] == 2


class TestPlotStateSpaceProjectionTSNE:
    def test_tsne_returns_figure(self):
        # sklearn's TSNE defaults perplexity=30, which requires
        # n_samples > perplexity, so use a larger synthetic sample set.
        sequences = {
            0: [[i, i + 1, i + 2] for i in range(40)],
        }
        periods = {0: 40}
        fig = plot_state_space_projection(sequences, periods, projection_method="tsne")
        assert isinstance(fig, plt.Figure)

    def test_tsne_missing_sklearn_raises_import_error(self, monkeypatch):
        import sys
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "sklearn.manifold" or name.startswith("sklearn.manifold"):
                raise ImportError("no sklearn.manifold")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        sequences = {0: [[1, 2, 3], [4, 5, 6], [7, 8, 9]]}
        with pytest.raises(ImportError, match="scikit-learn required"):
            plot_state_space_projection(sequences, {0: 3}, projection_method="tsne")

    def test_method_name_case_insensitive(self):
        fig_upper = plot_state_space_projection(SEQUENCES_3D, PERIODS_3D, projection_method="PCA")
        assert isinstance(fig_upper, plt.Figure)
