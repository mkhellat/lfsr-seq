#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Smoke tests for lfsr.examples.tmto_attack_example.

Standalone demo script (not part of the public API, not CLI-wired --
see src/lfsr/examples/__init__.py). Wraps lfsr.tmto (HellmanTable,
RainbowTable, tmto_attack, optimize_tmto_parameters), which per CLAUDE.md
has real test coverage (98%) and had bugs fixed there previously -- this
smoke test just confirms the demo script's own glue code (small, fixed
parameters: degree-4 LFSR, 100 chains x 50 length) runs end-to-end.
Confirmed via manual run this executes in ~3.5s total, well under the
15s budget, so no timeout wrapping is needed.
"""

import io
from contextlib import redirect_stderr, redirect_stdout

import pytest

try:
    from sage.all import *  # noqa: F401,F403
except ImportError:
    pytest.skip("SageMath not available", allow_module_level=True)

from lfsr.examples import tmto_attack_example as tae


class TestExampleFunctionsRunCleanly:
    def test_example_hellman_table(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            tae.example_hellman_table()
        out = buf.getvalue()
        assert "Hellman Table" in out
        assert "Table generated" in out

    def test_example_rainbow_table(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            tae.example_rainbow_table()
        out = buf.getvalue()
        assert "Rainbow Table" in out
        assert "Table generated" in out

    def test_example_tmto_attack(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            tae.example_tmto_attack()
        out = buf.getvalue()
        assert "TMTO Attack Function" in out
        assert "Attack Results" in out

    def test_example_parameter_optimization(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            tae.example_parameter_optimization()
        out = buf.getvalue()
        assert "Optimal Parameters" in out
        assert "Chain count" in out

    def test_example_comparison(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            tae.example_comparison()
        out = buf.getvalue()
        assert "Hellman vs Rainbow Comparison" in out
        assert "Hellman Table:" in out
        assert "Rainbow Table:" in out


class TestBranchesUnreachableViaRealCalls:
    """Covers branches this script's own hardcoded demo parameters
    (100 chains x 50 length against a 16-state degree-4 LFSR -- a table
    far larger than the state space) don't reliably trigger with the
    real (non-mocked) HellmanTable/RainbowTable.lookup(), whose result
    depends on random table generation: the "not found" branches below."""

    def test_hellman_table_not_found_branch(self):
        buf = io.StringIO()
        from lfsr.tmto import HellmanTable

        class _AlwaysMissTable(HellmanTable):
            def lookup(self, target_state, lfsr_config):
                return None

        original = tae.HellmanTable
        tae.HellmanTable = _AlwaysMissTable
        try:
            with redirect_stdout(buf):
                tae.example_hellman_table()
        finally:
            tae.HellmanTable = original
        out = buf.getvalue()
        assert "State not found in table" in out
        assert "May need larger table or different target" in out

    def test_rainbow_table_not_found_branch(self):
        buf = io.StringIO()
        from lfsr.tmto import RainbowTable

        class _AlwaysMissTable(RainbowTable):
            def lookup(self, target_state, lfsr_config):
                return None

        original = tae.RainbowTable
        tae.RainbowTable = _AlwaysMissTable
        try:
            with redirect_stdout(buf):
                tae.example_rainbow_table()
        finally:
            tae.RainbowTable = original
        out = buf.getvalue()
        assert "State not found in table" in out

    def test_main_except_block_on_unexpected_error(self):
        def raiser():
            raise RuntimeError("simulated failure for coverage")

        original = tae.example_hellman_table
        tae.example_hellman_table = raiser
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        try:
            with redirect_stdout(buf_out):
                with pytest.raises(SystemExit) as exc_info:
                    with redirect_stderr(buf_err):
                        tae.main()
        finally:
            tae.example_hellman_table = original
        assert exc_info.value.code == 1
        assert "ERROR: simulated failure for coverage" in buf_err.getvalue()


class TestMainEndToEnd:
    def test_main_runs_all_examples_without_raising(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            tae.main()
        out = buf.getvalue()
        assert "Time-Memory Trade-Off Attacks Examples" in out
        assert "Examples Complete!" in out
        assert "Example 1: Hellman Table" in out
        assert "Example 5: Hellman vs Rainbow Comparison" in out
