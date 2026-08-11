#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for lfsr.visualization.attack_visualization.

Covers visualize_correlation_attack() (static matplotlib + interactive
plotly) and visualize_attack_comparison() (matplotlib only).
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pytest

from lfsr.visualization import attack_visualization as av
from lfsr.visualization.base import VisualizationConfig
from lfsr.visualization.attack_visualization import (
    visualize_attack_comparison,
    visualize_correlation_attack,
)


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


FULL_RESULTS = {
    "correlations": [0.6, 0.3, 0.8],
    "success_probability": 0.75,
    "candidates_over_time": [1000, 500, 100, 10],
    "target_lfsr": 2,
    "max_correlation": 0.8,
    "attack_successful": True,
}


class TestVisualizeCorrelationAttackStatic:
    def test_returns_figure_with_four_axes(self):
        fig = visualize_correlation_attack(FULL_RESULTS)
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) == 4

    def test_raises_without_matplotlib_or_plotly(self, monkeypatch):
        monkeypatch.setattr(av, "HAS_MATPLOTLIB", False)
        monkeypatch.setattr(av, "HAS_PLOTLY", False)
        with pytest.raises(ImportError):
            visualize_correlation_attack(FULL_RESULTS)

    def test_correlation_bar_heights_match_input(self):
        fig = visualize_correlation_attack(FULL_RESULTS)
        ax1 = fig.axes[0]
        heights = [p.get_height() for p in ax1.patches]
        assert heights == pytest.approx(FULL_RESULTS["correlations"])

    def test_success_probability_barh_matches_input(self):
        fig = visualize_correlation_attack(FULL_RESULTS)
        ax2 = fig.axes[1]
        widths = [p.get_width() for p in ax2.patches]
        assert widths == pytest.approx([FULL_RESULTS["success_probability"]])

    def test_success_probability_color_reflects_threshold(self):
        results_high = dict(FULL_RESULTS, success_probability=0.9)
        results_low = dict(FULL_RESULTS, success_probability=0.1)
        fig_high = visualize_correlation_attack(results_high)
        fig_low = visualize_correlation_attack(results_low)
        color_high = fig_high.axes[1].patches[0].get_facecolor()
        color_low = fig_low.axes[1].patches[0].get_facecolor()
        assert color_high != color_low

    def test_candidates_over_time_line_matches_input(self):
        fig = visualize_correlation_attack(FULL_RESULTS)
        ax3 = fig.axes[2]
        line = ax3.get_lines()[0]
        assert list(line.get_ydata()) == FULL_RESULTS["candidates_over_time"]

    def test_summary_text_includes_all_present_fields(self):
        fig = visualize_correlation_attack(FULL_RESULTS)
        ax4 = fig.axes[3]
        text = ax4.texts[0].get_text()
        assert "Target LFSR: 2" in text
        assert "Max Correlation: 0.8000" in text
        assert "Success Probability: 75.00%" in text
        assert "Attack Successful: Yes" in text

    def test_missing_optional_keys_produce_empty_subplots_not_crash(self):
        minimal_results = {}
        fig = visualize_correlation_attack(minimal_results)
        assert isinstance(fig, plt.Figure)
        ax1, ax2, ax3, ax4 = fig.axes
        assert len(ax1.patches) == 0
        assert len(ax2.patches) == 0
        assert len(ax3.get_lines()) == 0
        # Summary text still created, just with header only
        assert ax4.texts[0].get_text().strip() == "Correlation Attack Summary"

    def test_attack_successful_false_shown_as_no(self):
        results = dict(FULL_RESULTS, attack_successful=False)
        fig = visualize_correlation_attack(results)
        text = fig.axes[3].texts[0].get_text()
        assert "Attack Successful: No" in text

    def test_saves_to_output_file(self, tmp_path):
        out = tmp_path / "corr.png"
        visualize_correlation_attack(FULL_RESULTS, output_file=str(out))
        assert out.exists()

    def test_suptitle_default_and_custom(self):
        fig_default = visualize_correlation_attack(FULL_RESULTS)
        assert fig_default._suptitle.get_text() == "Correlation Attack Analysis"
        config = VisualizationConfig(title="Custom")
        fig_custom = visualize_correlation_attack(FULL_RESULTS, config=config)
        assert fig_custom._suptitle.get_text() == "Custom"


class TestVisualizeCorrelationAttackInteractive:
    def test_returns_plotly_figure(self):
        config = VisualizationConfig(interactive=True)
        fig = visualize_correlation_attack(FULL_RESULTS, config=config)
        assert isinstance(fig, go.Figure)

    def test_correlation_trace_matches_input(self):
        config = VisualizationConfig(interactive=True)
        fig = visualize_correlation_attack(FULL_RESULTS, config=config)
        bar_trace = next(t for t in fig.data if t.name == "Correlation")
        assert list(bar_trace.y) == FULL_RESULTS["correlations"]

    def test_candidates_trace_matches_input(self):
        config = VisualizationConfig(interactive=True)
        fig = visualize_correlation_attack(FULL_RESULTS, config=config)
        candidates_trace = next(t for t in fig.data if t.name == "Candidates")
        assert list(candidates_trace.y) == FULL_RESULTS["candidates_over_time"]

    def test_saves_html_output_file(self, tmp_path):
        out = tmp_path / "corr.html"
        config = VisualizationConfig(interactive=True)
        visualize_correlation_attack(FULL_RESULTS, config=config, output_file=str(out))
        assert out.exists()


ATTACK_RESULTS_LIST = [
    {"method_name": "Correlation", "success_rate": 0.8, "execution_time": 1.5, "memory_usage": 100},
    {"method_name": "TMTO", "success_rate": 0.6, "execution_time": 3.2, "memory_usage": 500},
]


class TestVisualizeAttackComparison:
    def test_returns_figure_with_four_axes(self):
        fig = visualize_attack_comparison(ATTACK_RESULTS_LIST)
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) == 4

    def test_raises_without_matplotlib(self, monkeypatch):
        monkeypatch.setattr(av, "HAS_MATPLOTLIB", False)
        with pytest.raises(ImportError, match="matplotlib"):
            visualize_attack_comparison(ATTACK_RESULTS_LIST)

    def test_success_rate_bars_match_input(self):
        fig = visualize_attack_comparison(ATTACK_RESULTS_LIST)
        ax1 = fig.axes[0]
        heights = [p.get_height() for p in ax1.patches]
        assert heights == pytest.approx([0.8, 0.6])

    def test_execution_time_bars_match_input(self):
        fig = visualize_attack_comparison(ATTACK_RESULTS_LIST)
        ax2 = fig.axes[1]
        heights = [p.get_height() for p in ax2.patches]
        assert heights == pytest.approx([1.5, 3.2])

    def test_memory_usage_shown_when_present(self):
        fig = visualize_attack_comparison(ATTACK_RESULTS_LIST)
        ax3 = fig.axes[2]
        heights = [p.get_height() for p in ax3.patches]
        assert heights == pytest.approx([100, 500])

    def test_memory_usage_absent_shows_placeholder_text(self):
        results_no_mem = [
            {"method_name": "A", "success_rate": 0.5, "execution_time": 1.0},
        ]
        fig = visualize_attack_comparison(results_no_mem)
        ax3 = fig.axes[2]
        assert len(ax3.patches) == 0
        assert any("not available" in t.get_text() for t in ax3.texts)

    def test_method_names_default_when_missing(self):
        results = [{"success_rate": 0.5, "execution_time": 1.0}]
        fig = visualize_attack_comparison(results)
        ax1 = fig.axes[0]
        labels = [t.get_text() for t in ax1.get_xticklabels()]
        assert labels == ["Method 0"]

    def test_summary_table_has_correct_rows(self):
        fig = visualize_attack_comparison(ATTACK_RESULTS_LIST)
        ax4 = fig.axes[3]
        tables = ax4.tables
        assert len(tables) == 1
        table = tables[0]
        # 2 data rows + 1 header row = should have cells for method,success,time x 3 rows
        cell_texts = {key: cell.get_text().get_text() for key, cell in table._cells.items()}
        # header row (row index 0)
        header_texts = [cell_texts[(0, c)] for c in range(3)]
        assert header_texts == ["Method", "Success", "Time (s)"]
        row1 = [cell_texts[(1, c)] for c in range(3)]
        assert row1 == ["Correlation", "80.00%", "1.50"]

    def test_saves_to_output_file(self, tmp_path):
        out = tmp_path / "comparison.png"
        visualize_attack_comparison(ATTACK_RESULTS_LIST, output_file=str(out))
        assert out.exists()

    def test_empty_attack_list_shows_placeholder_instead_of_crashing(self):
        """Regression test (bug fixed 2026-08-11, see commit history):
        with an empty attack_results list, table_data ==
        [["Method","Success","Time (s)"]], so table_data[1:] == [] --
        matplotlib's Axes.table() does `cols = len(cellText[0])`
        unconditionally when cellText is non-None but empty, raising
        IndexError. Fixed by skipping the table entirely and showing a
        placeholder text when there are no rows to summarize, matching
        the pattern already used by the resource-usage subplot."""
        fig = visualize_attack_comparison([])
        ax4 = fig.axes[3]
        assert len(ax4.tables) == 0
        assert any("No attack results" in t.get_text() for t in ax4.texts)
