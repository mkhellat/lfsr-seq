#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for lfsr.visualization.statistical_plots.

Covers plot_period_statistics() (2x2 subplot: histogram, box plot,
cumulative distribution, stats text) and plot_sequence_analysis() (2x2
subplot: sequence trace, bit frequency, autocorrelation, run lengths).
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from lfsr.visualization import statistical_plots as sp
from lfsr.visualization.base import VisualizationConfig
from lfsr.visualization.statistical_plots import (
    plot_period_statistics,
    plot_sequence_analysis,
)


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


class TestPlotPeriodStatistics:
    def test_returns_figure_with_four_axes(self):
        fig = plot_period_statistics({1: 1, 3: 2, 15: 9})
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) == 4

    def test_raises_without_matplotlib(self, monkeypatch):
        monkeypatch.setattr(sp, "HAS_MATPLOTLIB", False)
        with pytest.raises(ImportError, match="matplotlib"):
            plot_period_statistics({1: 1})

    def test_histogram_bar_heights_match_counts(self):
        period_dict = {1: 5, 3: 2, 15: 9}
        fig = plot_period_statistics(period_dict)
        ax1 = fig.axes[0]
        heights = sorted(p.get_height() for p in ax1.patches)
        assert heights == sorted(period_dict.values())

    def test_boxplot_uses_period_values_repeated_by_count(self):
        """The box plot's underlying data is periods repeated `count`
        times each; verify median matches an independently-computed
        median of the expanded dataset."""
        period_dict = {1: 1, 3: 1, 15: 2}  # expanded: [1, 3, 15, 15]
        expanded = [1, 3, 15, 15]
        expected_median = float(np.median(expanded))

        fig = plot_period_statistics(period_dict)
        ax2 = fig.axes[1]
        # boxplot median line's y-data (constant y across the box width)
        median_lines = ax2.lines
        # matplotlib boxplot draws several Line2D objects; the median line
        # is identifiable as the one whose y-values are both equal to the
        # true median.
        found = False
        for line in median_lines:
            ydata = line.get_ydata()
            if len(ydata) and abs(ydata[0] - expected_median) < 1e-9 and ydata[0] == ydata[-1]:
                found = True
                break
        assert found, f"expected a boxplot line at median={expected_median}"

    def test_cumulative_distribution_matches_manual_computation(self):
        period_dict = {1: 1, 3: 2, 15: 1}  # total = 4
        fig = plot_period_statistics(period_dict)
        ax3 = fig.axes[2]
        line = ax3.get_lines()[0]
        x_data = list(line.get_xdata())
        y_data = list(line.get_ydata())

        assert x_data == [1, 3, 15]
        # cumulative: 1/4, (1+2)/4, (1+2+1)/4
        expected_y = [1 / 4, 3 / 4, 4 / 4]
        assert y_data == pytest.approx(expected_y)

    def test_stats_text_contains_correct_mean_and_max(self):
        period_dict = {1: 1, 3: 1, 15: 1}  # expanded [1,3,15], mean=6.33..
        fig = plot_period_statistics(period_dict)
        ax4 = fig.axes[3]
        texts = [t.get_text() for t in ax4.texts]
        assert len(texts) == 1
        stats_text = texts[0]

        expanded = [1, 3, 15]
        expected_mean = np.mean(expanded)
        assert f"Mean: {expected_mean:.2f}" in stats_text
        assert "Max: 15" in stats_text
        assert "Min: 1" in stats_text

    def test_stats_text_includes_theoretical_ratio_when_provided(self):
        period_dict = {1: 1, 15: 1}
        fig = plot_period_statistics(period_dict, theoretical_max_period=15)
        ax4 = fig.axes[3]
        stats_text = ax4.texts[0].get_text()
        assert "Theoretical Max: 15" in stats_text
        assert "Ratio: 100.00%" in stats_text

    def test_stats_text_primitive_flag_reflected(self):
        fig_prim = plot_period_statistics({1: 1}, is_primitive=True)
        fig_not = plot_period_statistics({1: 1}, is_primitive=False)
        assert "Primitive: Yes" in fig_prim.axes[3].texts[0].get_text()
        assert "Primitive: No" in fig_not.axes[3].texts[0].get_text()

    def test_saves_to_output_file(self, tmp_path):
        out = tmp_path / "stats.png"
        plot_period_statistics({1: 1, 3: 2}, output_file=str(out))
        assert out.exists()

    def test_suptitle_default_and_custom(self):
        fig_default = plot_period_statistics({1: 1})
        assert fig_default._suptitle.get_text() == "Period Distribution Statistics"

        config = VisualizationConfig(title="My Stats")
        fig_custom = plot_period_statistics({1: 1}, config=config)
        assert fig_custom._suptitle.get_text() == "My Stats"


class TestPlotSequenceAnalysis:
    def test_returns_figure_with_four_axes(self):
        sequence = [0, 1, 1, 0, 1, 0, 0, 1] * 10
        fig = plot_sequence_analysis(sequence)
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) == 4

    def test_raises_without_matplotlib(self, monkeypatch):
        monkeypatch.setattr(sp, "HAS_MATPLOTLIB", False)
        with pytest.raises(ImportError, match="matplotlib"):
            plot_sequence_analysis([0, 1, 0, 1])

    def test_sequence_plot_shows_first_100_bits_only(self):
        sequence = [i % 2 for i in range(250)]
        fig = plot_sequence_analysis(sequence)
        ax1 = fig.axes[0]
        line = ax1.get_lines()[0]
        assert len(line.get_xdata()) == 100
        assert list(line.get_ydata()) == sequence[:100]

    def test_sequence_plot_shorter_than_100_shows_all(self):
        sequence = [0, 1, 0, 1, 1]
        fig = plot_sequence_analysis(sequence)
        ax1 = fig.axes[0]
        line = ax1.get_lines()[0]
        assert list(line.get_ydata()) == sequence

    def test_bit_frequency_matches_manual_count(self):
        sequence = [0, 0, 0, 1, 1, 1, 1]  # 3 zeros, 4 ones, total 7
        fig = plot_sequence_analysis(sequence)
        ax2 = fig.axes[1]
        heights = [p.get_height() for p in ax2.patches]
        assert heights == pytest.approx([3 / 7, 4 / 7])

    def test_bit_frequency_all_zeros_sequence(self):
        sequence = [0, 0, 0, 0]
        fig = plot_sequence_analysis(sequence)
        ax2 = fig.axes[1]
        heights = [p.get_height() for p in ax2.patches]
        assert heights == pytest.approx([1.0, 0.0])

    def test_autocorrelation_lag_zero_is_always_one(self):
        """At lag 0, sequence[i] == sequence[i] trivially, so autocorr[0]
        must equal 1.0 for any non-empty sequence."""
        sequence = [0, 1, 1, 0, 1, 0, 1, 1, 0, 0]
        fig = plot_sequence_analysis(sequence)
        ax3 = fig.axes[2]
        line = ax3.get_lines()[0]
        assert line.get_ydata()[0] == pytest.approx(1.0)

    def test_autocorrelation_max_lag_capped_at_20_and_half_length(self):
        long_seq = [i % 2 for i in range(200)]
        fig = plot_sequence_analysis(long_seq)
        ax3 = fig.axes[2]
        line = ax3.get_lines()[0]
        assert len(line.get_xdata()) == 20  # min(20, 200//2) == 20

        short_seq = [0, 1, 0, 1, 1, 0]  # len=6, max_lag=3
        fig2 = plot_sequence_analysis(short_seq)
        ax3b = fig2.axes[2]
        line2 = ax3b.get_lines()[0]
        assert len(line2.get_xdata()) == 3

    def test_autocorrelation_manual_verification(self):
        """Verify autocorr value at lag=1 against an independent manual
        computation for a small fixed sequence."""
        sequence = [1, 1, 0, 1, 0]
        # lag=1: compare sequence[i] to sequence[i+1] for i in 0..3
        # pairs: (1,1)T (1,0)F (0,1)F (1,0)F -> 1/4 matches
        expected_lag1 = sum(
            sequence[i] == sequence[i + 1] for i in range(len(sequence) - 1)
        ) / (len(sequence) - 1)

        fig = plot_sequence_analysis(sequence)
        ax3 = fig.axes[2]
        line = ax3.get_lines()[0]
        assert line.get_ydata()[1] == pytest.approx(expected_lag1)

    def test_run_length_distribution_matches_manual_computation(self):
        # sequence: 0,0,1,1,1,0 -> runs: [2,3,1]
        sequence = [0, 0, 1, 1, 1, 0]
        fig = plot_sequence_analysis(sequence)
        ax4 = fig.axes[3]

        run_lengths = sorted(p.get_x() + p.get_width() / 2 for p in ax4.patches)
        assert run_lengths == [1.0, 2.0, 3.0]
        # run length 1 occurs once, 2 occurs once, 3 occurs once
        heights = {
            round(p.get_x() + p.get_width() / 2): p.get_height() for p in ax4.patches
        }
        assert heights == {1: 1, 2: 1, 3: 1}

    def test_run_length_distribution_repeated_run_lengths(self):
        # sequence: 0,1,0,1 -> runs: [1,1,1,1] (all single-bit runs)
        sequence = [0, 1, 0, 1]
        fig = plot_sequence_analysis(sequence)
        ax4 = fig.axes[3]
        assert len(ax4.patches) == 1  # only run-length "1" appears
        assert ax4.patches[0].get_height() == 4

    def test_single_element_sequence_does_not_crash(self):
        """Edge case: a sequence of length 1 has no lag>=1 pairs and the
        run-length loop's range(1, min(100,1)) is empty, but current_run
        still gets appended once at the end -- should not raise."""
        fig = plot_sequence_analysis([1])
        assert isinstance(fig, plt.Figure)
        ax4 = fig.axes[3]
        assert len(ax4.patches) == 1
        assert ax4.patches[0].get_height() == 1

    def test_saves_to_output_file(self, tmp_path):
        out = tmp_path / "seq.png"
        plot_sequence_analysis([0, 1, 0, 1, 1, 0], output_file=str(out))
        assert out.exists()

    def test_suptitle_default_and_custom(self):
        fig_default = plot_sequence_analysis([0, 1])
        assert fig_default._suptitle.get_text() == "Sequence Analysis"

        config = VisualizationConfig(title="Custom Seq")
        fig_custom = plot_sequence_analysis([0, 1], config=config)
        assert fig_custom._suptitle.get_text() == "Custom Seq"
