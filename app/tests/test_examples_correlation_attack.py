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


class TestBranchesUnreachableViaRealCalls:
    """Covers branches this script's own hardcoded demo inputs may not
    reliably trigger with the real (non-mocked) library functions."""

    def test_fast_correlation_attack_failure_branch(self, capsys, monkeypatch):
        """Covers the `else: print('State recovery failed')` branch
        (line ~265) in example_fast_correlation_attack(), which depends
        on fast_correlation_attack's real (probabilistic) success/
        failure outcome for this script's hardcoded AND-combined
        generator -- not guaranteed to hit the failure branch on every
        run (test_example_fast_correlation_attack_runs above only
        asserts the union of both outcomes across 2 LFSRs). Monkeypatch
        fast_correlation_attack to force attack_successful=False
        deterministically, isolating this script's print/branch logic."""
        from dataclasses import dataclass, field
        from typing import Any, Dict, List, Optional

        @dataclass
        class _FakeResult:
            target_lfsr_index: int
            recovered_state: Optional[List[int]]
            correlation_coefficient: float
            attack_successful: bool
            iterations_performed: int
            candidate_states_tested: int
            best_correlation: float
            complexity_estimate: float
            keystream_length: int

        def fake_fast_correlation_attack(gen, keystream, target_lfsr_index):
            return _FakeResult(
                target_lfsr_index=target_lfsr_index,
                recovered_state=None,
                correlation_coefficient=0.01,
                attack_successful=False,
                iterations_performed=5,
                candidate_states_tested=100,
                best_correlation=0.02,
                complexity_estimate=999.0,
                keystream_length=2000,
            )

        monkeypatch.setattr(
            example_module, "fast_correlation_attack", fake_fast_correlation_attack
        )
        example_module.example_fast_correlation_attack()
        out = capsys.readouterr().out
        assert "State recovery failed" in out

    def test_main_except_block_on_unexpected_error(self, capsys, monkeypatch):
        def raiser():
            raise RuntimeError("simulated failure for coverage")

        monkeypatch.setattr(
            example_module, "example_basic_correlation_attack", raiser
        )
        with pytest.raises(SystemExit) as exc_info:
            example_module.main()
        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "ERROR: simulated failure for coverage" in err


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

import sys


class TestSageImportGuardCorrelation:
    """Regression coverage for the module-level
    `try: from sage.all import * / except ImportError: print(...);
    sys.exit(1)` guard in lfsr.examples.correlation_attack_example (source lines near the
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
        modname = "lfsr.examples.correlation_attack_example"

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
