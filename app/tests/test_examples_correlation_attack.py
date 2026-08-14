#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Smoke tests for lfsr.examples.correlation_attack_example.

Standalone demo/tutorial script (see src/lfsr/examples/__init__.py) --
not part of the public API, not imported by library code, not wired
into the CLI. Smoke testing only: does each ``example_*()`` function
(and ``main()``) run to completion without raising, with stdout
captured. Underlying library calls (lfsr.attacks: CombinationGenerator,
siegenthaler_correlation_attack, fast_correlation_attack,
distinguishing_attack, analyze_combining_function,
compute_correlation_coefficient) already have real test coverage
elsewhere.

BUG FOUND AND FIXED (was NOT fixed when this file was first written --
now is): ``main()`` (src/lfsr/examples/correlation_attack_example.py)
called ``example_fast_correlation_attack()`` and
``example_distinguishing_attack()``, but neither function was defined
anywhere in the module. Calling ``main()`` therefore always raised
``NameError`` after the first four examples had already run, and
``main()``'s own top-level ``try/except Exception: ...; sys.exit(1)``
converted that into ``SystemExit(1)`` on every invocation. Both
functions are now implemented (Example 5: fast_correlation_attack
against a vulnerable AND-combined generator; Example 6:
distinguishing_attack against a majority-combined generator), verified
by running the full script end-to-end (exit code 0, ~3.5s).
"""

import pytest

import lfsr.examples.correlation_attack_example as example_module


class TestIndividualExamples:
    def test_example_basic_correlation_attack_runs(self, capsys):
        example_module.example_basic_correlation_attack()
        out = capsys.readouterr().out
        assert "Basic Correlation Attack" in out

    def test_example_combining_function_analysis_runs(self, capsys):
        example_module.example_combining_function_analysis()
        out = capsys.readouterr().out
        assert "Combining Function Analysis" in out

    def test_example_correlation_computation_runs(self, capsys):
        example_module.example_correlation_computation()
        out = capsys.readouterr().out
        assert "Correlation Coefficient Computation" in out

    def test_example_vulnerable_combination_runs(self, capsys):
        example_module.example_vulnerable_combination()
        out = capsys.readouterr().out
        assert "Vulnerable Combination Generator" in out

    def test_example_fast_correlation_attack_runs(self, capsys):
        example_module.example_fast_correlation_attack()
        out = capsys.readouterr().out
        assert "Fast Correlation Attack" in out
        # Both LFSRs attacked; each prints its own result block.
        assert out.count("Recovered state") + out.count("recovery failed") == 2

    def test_example_distinguishing_attack_runs(self, capsys):
        example_module.example_distinguishing_attack()
        out = capsys.readouterr().out
        assert "Distinguishing Attack" in out
        assert "Method: correlation" in out


class TestPreviouslyUndefinedFunctionsNowExist:
    """main() used to reference two example_*() functions that were
    never defined in this module (see module docstring). Confirm they
    now exist and are real, importable, callable functions.
    """

    def test_example_fast_correlation_attack_exists(self):
        assert callable(example_module.example_fast_correlation_attack)

    def test_example_distinguishing_attack_exists(self):
        assert callable(example_module.example_distinguishing_attack)


class TestMain:
    def test_main_runs_to_completion(self, capsys):
        """main() no longer raises NameError / exits 1 -- both
        previously-missing functions are now implemented (see module
        docstring). It should return normally (no SystemExit) and
        print the full six-example sequence plus the completion banner.
        """
        example_module.main()  # must not raise / must not sys.exit

        captured = capsys.readouterr()
        assert "Basic Correlation Attack" in captured.out
        assert "Combining Function Analysis" in captured.out
        assert "Correlation Coefficient Computation" in captured.out
        assert "Vulnerable Combination Generator" in captured.out
        assert "Fast Correlation Attack" in captured.out
        assert "Distinguishing Attack" in captured.out
        assert "Examples Complete!" in captured.out
        assert captured.err == ""
