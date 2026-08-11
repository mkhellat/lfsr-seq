#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for lfsr.visualization's package __init__.

The __init__.py itself contains no logic beyond re-exporting names from
its submodules and declaring __all__; these tests verify every name in
__all__ actually resolves to the correct object (i.e. no stale/renamed
export) and that __all__ doesn't omit or over-declare anything.
"""

import matplotlib
matplotlib.use("Agg")

import lfsr.visualization as viz
from lfsr.visualization import (
    attack_visualization,
    base,
    period_graphs,
    state_diagrams,
    state_space_3d,
    statistical_plots,
)


EXPECTED_SOURCE_MODULE = {
    "BaseVisualization": base,
    "VisualizationConfig": base,
    "OutputFormat": base,
    "check_visualization_dependencies": base,
    "plot_period_distribution": period_graphs,
    "plot_period_vs_state": period_graphs,
    "generate_state_transition_diagram": state_diagrams,
    "export_to_graphviz": state_diagrams,
    "plot_period_statistics": statistical_plots,
    "plot_sequence_analysis": statistical_plots,
    "plot_3d_state_space": state_space_3d,
    "plot_state_space_projection": state_space_3d,
    "visualize_correlation_attack": attack_visualization,
    "visualize_attack_comparison": attack_visualization,
}


class TestPackageExports:
    def test_all_matches_expected_name_set(self):
        assert set(viz.__all__) == set(EXPECTED_SOURCE_MODULE.keys())

    def test_no_duplicate_names_in_all(self):
        assert len(viz.__all__) == len(set(viz.__all__))

    def test_every_exported_name_is_identical_object_to_source_module(self):
        for name, source_module in EXPECTED_SOURCE_MODULE.items():
            assert hasattr(viz, name), f"{name} missing from lfsr.visualization"
            assert getattr(viz, name) is getattr(source_module, name), (
                f"lfsr.visualization.{name} is not the same object as "
                f"{source_module.__name__}.{name}"
            )

    def test_all_names_are_importable_directly_from_package(self):
        from lfsr.visualization import (
            BaseVisualization,
            OutputFormat,
            VisualizationConfig,
            check_visualization_dependencies,
            export_to_graphviz,
            generate_state_transition_diagram,
            plot_3d_state_space,
            plot_period_distribution,
            plot_period_statistics,
            plot_period_vs_state,
            plot_sequence_analysis,
            plot_state_space_projection,
            visualize_attack_comparison,
            visualize_correlation_attack,
        )
        # Import succeeding is the assertion; nothing further needed.
        assert BaseVisualization is base.BaseVisualization
        assert OutputFormat is base.OutputFormat
