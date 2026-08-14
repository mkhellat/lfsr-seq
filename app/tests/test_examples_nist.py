#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Smoke tests for lfsr.examples.nist_test_example.

Standalone demo/tutorial script (see src/lfsr/examples/__init__.py) --
not part of the public API, not imported by library code, not wired
into the CLI. Smoke testing only: does each ``example_*()`` function
(and ``main()``) run to completion without raising, with stdout
captured. Underlying library calls (lfsr.nist: the NIST SP 800-22
suite) already have real, verified test coverage elsewhere (93%
coverage per CLAUDE.md, several real bugs already found and fixed
there in a prior session).

All 5 example functions and ``main()`` were run directly against this
repo's SageMath install before writing any assertion below; all
completed without raising (verified 2026-08-14).

``example_all_tests()`` wraps each of its 15 individual NIST test calls
in its own try/except that prints "ERROR" instead of raising, so a
plain "did not raise" assertion on that function alone would not catch
a silently-failing sub-test. Its captured stdout was checked directly
for any "ERROR" line before writing the test below; none was found --
all 15 sub-tests in that function's demo sequence genuinely passed.
"""

import lfsr.examples.nist_test_example as example_module


class TestIndividualExamples:
    def test_example_single_test_runs(self, capsys):
        example_module.example_single_test()
        out = capsys.readouterr().out
        assert "Frequency (Monobit) Test" in out

    def test_example_test_suite_runs(self, capsys):
        example_module.example_test_suite()
        out = capsys.readouterr().out
        assert "Test Suite Results" in out

    def test_example_all_tests_runs_with_no_internal_errors(self, capsys):
        # This function catches per-test exceptions internally and
        # prints "ERROR" instead of raising -- explicitly assert none
        # of the 15 individual NIST tests silently failed.
        example_module.example_all_tests()
        out = capsys.readouterr().out
        assert "All Individual Tests" in out
        assert "ERROR" not in out

    def test_example_interpretation_runs(self, capsys):
        example_module.example_interpretation()
        out = capsys.readouterr().out
        assert "Interpreting Test Results" in out

    def test_example_significance_levels_runs(self, capsys):
        example_module.example_significance_levels()
        out = capsys.readouterr().out
        assert "Effect of Significance Levels" in out


class TestMain:
    def test_main_runs_end_to_end(self, capsys):
        example_module.main()
        out = capsys.readouterr().out
        assert "Examples Complete!" in out
