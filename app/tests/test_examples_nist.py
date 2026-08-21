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


class TestBranchesUnreachableViaRealCalls:
    def test_example_all_tests_prints_error_line_on_sub_test_exception(
        self, capsys, monkeypatch
    ):
        """Covers the `except Exception as e: print(... 'ERROR' ...)`
        branch (lines ~147-148) inside example_all_tests()'s per-test
        loop -- never taken with the script's own well-formed 1000-bit
        demo sequence (see module docstring: verified no "ERROR" line
        appears). Monkeypatch frequency_test (referenced by module-
        global name inside example_all_tests()'s own `tests` list of
        lambdas) to raise, forcing the except branch deterministically."""
        def raiser(seq):
            raise RuntimeError("simulated failure for coverage")

        monkeypatch.setattr(example_module, "frequency_test", raiser)
        example_module.example_all_tests()
        out = capsys.readouterr().out
        assert "ERROR" in out

    def test_main_except_block_on_unexpected_error(self, capsys, monkeypatch):
        def raiser():
            raise RuntimeError("simulated failure for coverage")

        monkeypatch.setattr(example_module, "example_single_test", raiser)
        import pytest

        with pytest.raises(SystemExit) as exc_info:
            example_module.main()
        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "ERROR: simulated failure for coverage" in err

import sys


class TestSageImportGuardNist:
    """Regression coverage for the module-level
    `try: from sage.all import * / except ImportError: print(...);
    sys.exit(1)` guard in lfsr.examples.nist_test_example (source lines near the
    top of the file). SageMath IS importable in this environment, so
    this branch is never hit by a normal import; force it by blocking
    only `sage.all` imports whose caller is this specific example
    module (a plain global block on "sage.all" would also break
    lfsr.cli/lfsr.sage_imports, which import it eagerly at package-init
    time via `import lfsr`)."""

    def test_missing_sage_all_prints_error_and_exits(self, capsys):
        import builtins
        import importlib

        import pytest

        real_import = builtins.__import__
        modname = "lfsr.examples.nist_test_example"

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            caller = (globals or {}).get("__name__", "")
            if name == "sage.all" and caller == modname:
                raise ImportError("simulated: sage.all unavailable")
            return real_import(name, globals, locals, fromlist, level)

        if modname in sys.modules:
            del sys.modules[modname]

        builtins.__import__ = fake_import
        try:
            with pytest.raises(SystemExit) as exc_info:
                importlib.import_module(modname)
            assert exc_info.value.code == 1
        finally:
            builtins.__import__ = real_import
            if modname in sys.modules:
                del sys.modules[modname]
            importlib.import_module(modname)

        captured = capsys.readouterr()
        assert "SageMath is required" in captured.err
