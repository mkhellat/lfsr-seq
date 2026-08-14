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
from contextlib import redirect_stdout

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
