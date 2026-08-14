#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Smoke tests for lfsr.examples.visualization_example.

Standalone demo script (not part of the public API, not CLI-wired --
see src/lfsr/examples/__init__.py). Notably, despite the module docstring
promising "period distribution plots, state transition diagrams,
statistical plots, 3D visualizations, and attack visualizations", every
actual call into lfsr.visualization.* (plot_period_distribution,
generate_state_transition_diagram, plot_period_statistics,
plot_3d_state_space, visualize_correlation_attack) is commented out in
the source -- confirmed by reading src/lfsr/examples/visualization_example.py
and by a manual `python3 -m lfsr.examples.visualization_example` run that
produced no image/HTML files anywhere under the repo. The script only
prints text and constructs VisualizationConfig objects. The example module
itself already calls `matplotlib.use('Agg')` at import time (non-interactive
backend), so no GUI window risk; the test file still calls matplotlib.use
before that import as defense in depth in case the source ever adds a real
plotting call, and asserts no stray image files land in the cwd afterward.
"""

import io
import os
from contextlib import redirect_stdout

import pytest

try:
    from sage.all import *  # noqa: F401,F403
except ImportError:
    pytest.skip("SageMath not available", allow_module_level=True)

import matplotlib

matplotlib.use("Agg")

from lfsr.examples import visualization_example as ve  # noqa: E402


IMAGE_EXTENSIONS = (".png", ".svg", ".html", ".pdf", ".jpg", ".jpeg")


def _stray_image_files(directory):
    """List image/output files directly in `directory` (non-recursive)."""
    try:
        return [f for f in os.listdir(directory) if f.lower().endswith(IMAGE_EXTENSIONS)]
    except OSError:
        return []


class TestExampleFunctionsRunCleanly:
    def test_example_period_distribution(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        buf = io.StringIO()
        with redirect_stdout(buf):
            ve.example_period_distribution()
        out = buf.getvalue()
        assert "Period Distribution Visualization" in out
        assert _stray_image_files(tmp_path) == []

    def test_example_state_transitions(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        buf = io.StringIO()
        with redirect_stdout(buf):
            ve.example_state_transitions()
        out = buf.getvalue()
        assert "State Transition Diagram" in out
        assert _stray_image_files(tmp_path) == []

    def test_example_statistical_plots(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        buf = io.StringIO()
        with redirect_stdout(buf):
            ve.example_statistical_plots()
        out = buf.getvalue()
        assert "Statistical Distribution Plots" in out
        assert _stray_image_files(tmp_path) == []

    def test_example_3d_visualization(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        buf = io.StringIO()
        with redirect_stdout(buf):
            ve.example_3d_visualization()
        out = buf.getvalue()
        assert "3D State Space Visualization" in out
        assert _stray_image_files(tmp_path) == []

    def test_example_attack_visualization(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        buf = io.StringIO()
        with redirect_stdout(buf):
            ve.example_attack_visualization()
        out = buf.getvalue()
        assert "Attack Visualization" in out
        assert _stray_image_files(tmp_path) == []


class TestMainEndToEnd:
    def test_main_runs_all_examples_without_raising(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        buf = io.StringIO()
        with redirect_stdout(buf):
            ve.main()
        out = buf.getvalue()
        assert "Visualization Features Examples" in out
        assert "Examples Complete!" in out
        assert "Example 1: Period Distribution Visualization" in out
        assert "Example 5: Attack Visualization" in out
        assert _stray_image_files(tmp_path) == []
