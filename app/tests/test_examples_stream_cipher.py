#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Smoke tests for lfsr.examples.stream_cipher_example.

This is a standalone demo script (not part of the public API, not
CLI-wired -- see src/lfsr/examples/__init__.py). Each example_*() function
prints a demo section wrapping already-tested cipher classes
(lfsr.ciphers.*) and lfsr.ciphers.comparison. The goal here is smoke
testing: does each function run to completion without raising, when
stdout is captured -- not deep unit testing of cipher internals.
"""

import io
from contextlib import redirect_stdout

import pytest

try:
    from sage.all import *  # noqa: F401,F403
except ImportError:
    pytest.skip("SageMath not available", allow_module_level=True)

from lfsr.examples import stream_cipher_example as sce


class TestExampleFunctionsRunCleanly:
    """Each example_*() should run to completion without raising."""

    def test_example_a5_1(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            sce.example_a5_1()
        out = buf.getvalue()
        assert "A5/1" in out
        assert "Keystream Generation" in out

    def test_example_e0(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            sce.example_e0()
        out = buf.getvalue()
        assert "E0" in out

    def test_example_trivium(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            sce.example_trivium()
        out = buf.getvalue()
        assert "Trivium" in out

    def test_example_grain(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            sce.example_grain()
        out = buf.getvalue()
        assert "Grain-128" in out
        assert "Grain-128a" in out

    def test_example_lili128(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            sce.example_lili128()
        out = buf.getvalue()
        assert "LILI-128" in out

    def test_example_comparison(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            sce.example_comparison()
        out = buf.getvalue()
        assert "Comparing" in out
        assert "Full Comparison Report" in out

    def test_example_comprehensive_analysis(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            sce.example_comprehensive_analysis()
        out = buf.getvalue()
        assert "Comprehensive Analysis Results" in out
        assert "Security assessment" in out


class TestMainEndToEnd:
    def test_main_runs_all_examples_without_raising(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            sce.main()
        out = buf.getvalue()
        assert "Stream Cipher Analysis Examples" in out
        assert "Examples Complete!" in out
        # sanity: every example section actually ran, in order
        assert "Example 1: A5/1" in out
        assert "Example 7: Comprehensive Analysis" in out

    def test_main_except_block_on_unexpected_error(self, monkeypatch):
        """Covers main()'s except block (lines ~228-232), unreachable
        with the script's own well-formed calls."""
        def raiser():
            raise RuntimeError("simulated failure for coverage")

        monkeypatch.setattr(sce, "example_a5_1", raiser)

        buf_out = io.StringIO()
        buf_err = io.StringIO()
        from contextlib import redirect_stderr

        with redirect_stdout(buf_out):
            with redirect_stderr(buf_err):
                with pytest.raises(SystemExit) as exc_info:
                    sce.main()
        assert exc_info.value.code == 1
        assert "ERROR: simulated failure for coverage" in buf_err.getvalue()
