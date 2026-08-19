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

import builtins
import io
import os
import sys
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


class TestImportGuards:
    """Regression coverage for the module-level `except ImportError:
    HAS_MATPLOTLIB/HAS_PLOTLY = False` branches themselves (lines
    ~27-29, ~34-36), as opposed to just testing behavior with the flags
    pre-set to False (covered below via monkeypatch.setattr). The
    sage.all import guard (lines 19-21) is NOT covered here: blocking
    `sage.all` itself would break every downstream import this test
    module and the wider test session depend on, unlike
    matplotlib/plotly which are optional, independently-blockable
    imports."""

    def test_matplotlib_import_error_sets_has_matplotlib_false(self, capsys):
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "matplotlib":
                raise ImportError("simulated: matplotlib unavailable")
            return real_import(name, *args, **kwargs)

        module_name = "lfsr.examples.visualization_example"
        if module_name in sys.modules:
            del sys.modules[module_name]

        builtins.__import__ = fake_import
        try:
            import importlib

            fresh = importlib.import_module(module_name)
        finally:
            builtins.__import__ = real_import

        try:
            assert fresh.HAS_MATPLOTLIB is False
            captured = capsys.readouterr()
            assert "matplotlib not available" in (captured.err + captured.out)
        finally:
            del sys.modules[module_name]
            importlib.import_module(module_name)

    def test_plotly_import_error_sets_has_plotly_false(self, capsys):
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "plotly":
                raise ImportError("simulated: plotly unavailable")
            return real_import(name, *args, **kwargs)

        module_name = "lfsr.examples.visualization_example"
        if module_name in sys.modules:
            del sys.modules[module_name]

        builtins.__import__ = fake_import
        try:
            import importlib

            fresh = importlib.import_module(module_name)
        finally:
            builtins.__import__ = real_import

        try:
            assert fresh.HAS_PLOTLY is False
            captured = capsys.readouterr()
            assert "plotly not available" in (captured.err + captured.out)
        finally:
            del sys.modules[module_name]
            importlib.import_module(module_name)


class TestFlagGatedElseBranches:
    """matplotlib and plotly are both actually installed in this
    environment, so HAS_MATPLOTLIB/HAS_PLOTLY are True at import time and
    the "not available, skipping" else-branches in each example_*()
    function are never naturally exercised. Monkeypatch the module-level
    flags to False to hit those branches directly."""

    def test_period_distribution_skips_without_matplotlib(self, monkeypatch):
        monkeypatch.setattr(ve, "HAS_MATPLOTLIB", False)
        buf = io.StringIO()
        with redirect_stdout(buf):
            ve.example_period_distribution()
        assert "matplotlib not available, skipping visualization" in buf.getvalue()

    def test_state_transitions_skips_without_matplotlib(self, monkeypatch):
        monkeypatch.setattr(ve, "HAS_MATPLOTLIB", False)
        buf = io.StringIO()
        with redirect_stdout(buf):
            ve.example_state_transitions()
        assert "matplotlib not available, skipping visualization" in buf.getvalue()

    def test_statistical_plots_skips_without_matplotlib(self, monkeypatch):
        monkeypatch.setattr(ve, "HAS_MATPLOTLIB", False)
        buf = io.StringIO()
        with redirect_stdout(buf):
            ve.example_statistical_plots()
        assert "matplotlib not available, skipping visualization" in buf.getvalue()

    def test_3d_visualization_skips_without_plotly(self, monkeypatch):
        monkeypatch.setattr(ve, "HAS_PLOTLY", False)
        buf = io.StringIO()
        with redirect_stdout(buf):
            ve.example_3d_visualization()
        assert "plotly not available, skipping 3D visualization" in buf.getvalue()

    def test_attack_visualization_skips_without_matplotlib(self, monkeypatch):
        monkeypatch.setattr(ve, "HAS_MATPLOTLIB", False)
        buf = io.StringIO()
        with redirect_stdout(buf):
            ve.example_attack_visualization()
        assert "matplotlib not available, skipping visualization" in buf.getvalue()


class TestMainErrorHandling:
    def test_main_prints_traceback_and_exits_on_exception(self, monkeypatch, capsys):
        """Regression coverage for lines 221-225: main()'s except Exception
        block prints an ERROR message to stderr, a traceback, and calls
        sys.exit(1). Force example_period_distribution (the first call
        inside main()'s try block) to raise so the handler fires."""

        def raiser():
            raise RuntimeError("forced failure for coverage")

        monkeypatch.setattr(ve, "example_period_distribution", raiser)

        with pytest.raises(SystemExit) as exc_info:
            ve.main()
        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "ERROR: forced failure for coverage" in captured.err
        assert "RuntimeError" in captured.err  # traceback.print_exc() output


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
