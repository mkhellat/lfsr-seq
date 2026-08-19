#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Smoke tests for lfsr.examples.advanced_lfsr_example.

This is a standalone demo/tutorial script (see
src/lfsr/examples/__init__.py) -- not part of the public API, not
imported by library code, not wired into the CLI. The goal here is
smoke testing only: does each ``example_*()`` function (and ``main()``)
run to completion without raising, with stdout captured. All library
functions these examples call (advanced/*, attacks.py) already have
real test coverage elsewhere per CLAUDE.md.

All 6 example functions and ``main()`` were run directly against this
repo's SageMath install before writing any assertion below; all
completed without raising (verified 2026-08-14).
"""

import lfsr.examples.advanced_lfsr_example as example_module


class TestIndividualExamples:
    def test_example_nfsr_runs(self, capsys):
        example_module.example_nfsr()
        out = capsys.readouterr().out
        assert "NFSR" in out

    def test_example_filtered_lfsr_runs(self, capsys):
        example_module.example_filtered_lfsr()
        out = capsys.readouterr().out
        assert "Filtered LFSR" in out

    def test_example_clock_controlled_lfsr_runs(self, capsys):
        example_module.example_clock_controlled_lfsr()
        out = capsys.readouterr().out
        assert "Clock-Controlled LFSR" in out

    def test_example_multi_output_lfsr_runs(self, capsys):
        example_module.example_multi_output_lfsr()
        out = capsys.readouterr().out
        assert "Multi-Output LFSR" in out

    def test_example_irregular_clocking_runs(self, capsys):
        example_module.example_irregular_clocking()
        out = capsys.readouterr().out
        assert "Irregular Clocking LFSR" in out

    def test_example_comprehensive_analysis_runs(self, capsys):
        example_module.example_comprehensive_analysis()
        out = capsys.readouterr().out
        assert "Comprehensive Analysis Results" in out


class TestMain:
    def test_main_runs_end_to_end(self, capsys):
        # main() wraps everything in try/except Exception -> sys.exit(1);
        # a clean run simply returns without raising or exiting.
        example_module.main()
        out = capsys.readouterr().out
        assert "Examples Complete!" in out

    def test_main_except_block_on_unexpected_error(self, capsys, monkeypatch):
        """Covers main()'s except block (lines ~241-245), unreachable
        with the script's own well-formed calls."""
        def raiser():
            raise RuntimeError("simulated failure for coverage")

        monkeypatch.setattr(example_module, "example_nfsr", raiser)

        import pytest

        with pytest.raises(SystemExit) as exc_info:
            example_module.main()
        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "ERROR: simulated failure for coverage" in err
