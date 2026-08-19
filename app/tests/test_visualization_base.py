#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for lfsr.visualization.base.

Covers VisualizationConfig defaults, OutputFormat enum, BaseVisualization's
dependency-checking constructor, and check_visualization_dependencies().

matplotlib/plotly/networkx are all installed in this dev venv (added via
pip for this test session -- pyproject.toml does not declare a
visualization extras group at all, so these were not previously
installed). Tests that need "dependency X is missing" behavior monkeypatch
the module-level HAS_* flags rather than actually uninstalling packages,
since that's the only way to exercise those branches deterministically.
"""

import builtins
import importlib

import matplotlib
matplotlib.use("Agg")

import pytest

from lfsr.visualization import base as viz_base
from lfsr.visualization.base import (
    BaseVisualization,
    OutputFormat,
    VisualizationConfig,
    check_visualization_dependencies,
)


class TestOptionalDependencyImportFallbacks:
    """Covers the module-level `except ImportError:` fallback blocks for
    matplotlib (lines 20-22), plotly (28-31), and networkx (36-38).

    matplotlib/plotly/networkx are all genuinely pip-installed in this
    dev venv (see module docstring), so these branches never execute
    during a normal test run -- the only way to exercise them
    deterministically is to force the underlying `import` statements to
    raise ImportError and reload the module, exactly as
    test_reproducibility.py's TestPkgResourcesImportFallback does for
    the analogous pkg_resources case. The module is reloaded back to
    its real, correctly-imported state afterwards so it doesn't leak a
    broken state into other test files that also import
    lfsr.visualization.base.
    """

    def test_all_three_missing_sets_all_flags_false_and_none_placeholders(self):
        """NOTE: importlib.reload() re-executes the module body into the
        *same* module __dict__/object rather than creating a fresh one,
        so classes already imported elsewhere (e.g. this test file's own
        `BaseVisualization`/`ConcreteVisualization`, which close over
        that same dict for their global lookups) observe the mutated
        HAS_MATPLOTLIB/HAS_PLOTLY/HAS_NETWORKX values too -- there is no
        way to reload in true isolation without a fresh module object
        (importlib.util.module_from_spec under a throwaway sys.modules
        key), which is what this test does instead, so it cannot leak
        into any other test in this file regardless of ordering."""
        import importlib.util

        real_import = builtins.__import__
        blocked = {
            "matplotlib",
            "matplotlib.pyplot",
            "plotly.express",
            "plotly.graph_objects",
            "networkx",
        }

        def fake_import(name, *args, **kwargs):
            if name in blocked:
                raise ImportError(f"simulated missing {name}")
            return real_import(name, *args, **kwargs)

        spec = importlib.util.find_spec("lfsr.visualization.base")
        fresh_module = importlib.util.module_from_spec(spec)

        builtins.__import__ = fake_import
        try:
            spec.loader.exec_module(fresh_module)
        finally:
            builtins.__import__ = real_import

        assert fresh_module.HAS_MATPLOTLIB is False
        assert fresh_module.HAS_PLOTLY is False
        assert fresh_module.HAS_NETWORKX is False
        assert fresh_module.plt is None
        assert fresh_module.go is None
        assert fresh_module.px is None
        assert fresh_module.nx is None

        # The real, already-imported viz_base module (and this file's
        # BaseVisualization/ConcreteVisualization classes) are entirely
        # untouched since we never reloaded into their shared __dict__.
        assert viz_base.HAS_MATPLOTLIB is True
        assert viz_base.HAS_PLOTLY is True
        assert viz_base.HAS_NETWORKX is True


class TestOutputFormat:
    def test_enum_values(self):
        assert OutputFormat.PNG.value == "png"
        assert OutputFormat.SVG.value == "svg"
        assert OutputFormat.PDF.value == "pdf"
        assert OutputFormat.HTML.value == "html"
        assert OutputFormat.JSON.value == "json"


class TestVisualizationConfigDefaults:
    def test_defaults(self):
        config = VisualizationConfig()
        assert config.width == 10.0
        assert config.height == 6.0
        assert config.dpi == 300
        assert config.style == "seaborn-v0_8"
        assert config.interactive is False
        assert config.output_format == OutputFormat.PNG
        assert config.title is None
        assert config.xlabel is None
        assert config.ylabel is None
        assert config.show_grid is True
        assert config.show_legend is True

    def test_custom_values_override_defaults(self):
        config = VisualizationConfig(
            width=5.0, height=3.0, dpi=100, interactive=True,
            output_format=OutputFormat.SVG, title="My Title",
            xlabel="X", ylabel="Y", show_grid=False, show_legend=False,
        )
        assert config.width == 5.0
        assert config.height == 3.0
        assert config.dpi == 100
        assert config.interactive is True
        assert config.output_format == OutputFormat.SVG
        assert config.title == "My Title"
        assert config.xlabel == "X"
        assert config.ylabel == "Y"
        assert config.show_grid is False
        assert config.show_legend is False


class TestCheckVisualizationDependencies:
    def test_returns_dict_with_expected_keys(self):
        deps = check_visualization_dependencies()
        assert set(deps.keys()) == {"matplotlib", "plotly", "networkx"}
        assert all(isinstance(v, bool) for v in deps.values())

    def test_reflects_actually_installed_packages(self):
        """All three are pip-installed in this venv for this test run,
        so all three should report True."""
        deps = check_visualization_dependencies()
        assert deps["matplotlib"] is True
        assert deps["plotly"] is True
        assert deps["networkx"] is True


class ConcreteVisualization(BaseVisualization):
    """Minimal concrete subclass since BaseVisualization's own
    save/show/to_html are abstract (raise NotImplementedError)."""
    pass


class TestBaseVisualizationConstruction:
    def test_default_config_created_when_none_given(self):
        viz = ConcreteVisualization()
        assert isinstance(viz.config, VisualizationConfig)

    def test_explicit_config_is_used(self):
        config = VisualizationConfig(title="custom")
        viz = ConcreteVisualization(config=config)
        assert viz.config is config

    def test_construction_succeeds_when_matplotlib_available_and_png_output(self):
        # matplotlib is actually installed, so this should not raise.
        viz = ConcreteVisualization(VisualizationConfig(output_format=OutputFormat.PNG))
        assert viz.config.output_format == OutputFormat.PNG

    def test_html_output_format_does_not_require_matplotlib(self, monkeypatch):
        monkeypatch.setattr(viz_base, "HAS_MATPLOTLIB", False)
        # Should not raise even though matplotlib is "unavailable", because
        # output_format == HTML is explicitly exempted in _check_dependencies.
        viz = ConcreteVisualization(VisualizationConfig(output_format=OutputFormat.HTML))
        assert viz.config.output_format == OutputFormat.HTML

    def test_missing_matplotlib_raises_for_non_html_format(self, monkeypatch):
        monkeypatch.setattr(viz_base, "HAS_MATPLOTLIB", False)
        with pytest.raises(ImportError, match="matplotlib"):
            ConcreteVisualization(VisualizationConfig(output_format=OutputFormat.PNG))

    def test_interactive_without_plotly_raises(self, monkeypatch):
        monkeypatch.setattr(viz_base, "HAS_PLOTLY", False)
        with pytest.raises(ImportError, match="plotly"):
            ConcreteVisualization(VisualizationConfig(interactive=True))

    def test_interactive_with_plotly_available_does_not_raise(self):
        # plotly is actually installed in this venv.
        viz = ConcreteVisualization(VisualizationConfig(interactive=True))
        assert viz.config.interactive is True


class TestBaseVisualizationAbstractMethods:
    def test_save_raises_not_implemented(self):
        viz = ConcreteVisualization()
        with pytest.raises(NotImplementedError):
            viz.save("out.png")

    def test_show_raises_not_implemented(self):
        viz = ConcreteVisualization()
        with pytest.raises(NotImplementedError):
            viz.show()

    def test_to_html_raises_not_implemented(self):
        viz = ConcreteVisualization()
        with pytest.raises(NotImplementedError):
            viz.to_html()
