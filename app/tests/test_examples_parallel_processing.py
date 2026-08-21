#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Smoke tests for lfsr.examples.parallel_processing_example -- a
standalone demo/tutorial script (not part of the public API, not
imported by any library code, not wired into the CLI; see
src/lfsr/examples/__init__.py). It wraps lfsr.analysis's
lfsr_sequence_mapper / lfsr_sequence_mapper_parallel with intentionally
small inputs (4-bit and 6-bit LFSRs, 16 and 64 states), so these tests
are deliberately shallow: each example_*() function is invoked with
stdout captured and we assert only that it runs to completion without
raising.

This module was flagged as a specific risk area because
lfsr/analysis.py's parallel/multiprocessing machinery had 3 real bugs
(partition data loss, merge crash, work-stealing infinite loop) found
and fixed earlier in this project -- see CLAUDE.md's "Known-fixed bug
classes". This example script itself was never covered by those fixes'
tests. All 4 example_*() functions plus main() were run interactively
against this checkout, each individually timed, before writing any
assertion: all completed in well under 1 second (example_worker_scaling,
the heaviest, took ~0.3s), and none raised or hung. No bugs were found
in this module. No pytest-timeout plugin is installed in this repo (per
CLAUDE.md), so if this file is ever extended with larger inputs, wrap
the risky invocation with the outer shell `timeout` command rather than
relying on an in-process timeout.
"""

import io
import contextlib

from lfsr.examples import parallel_processing_example as m


class TestExampleFunctions:
    def test_example_basic_parallel(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m.example_basic_parallel()
        out = buf.getvalue()
        assert "Basic Parallel Processing" in out
        assert "Sequential Processing" in out
        assert "Parallel Processing (2 workers)" in out
        assert "Correctness: ✓" in out

    def test_example_worker_scaling(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m.example_worker_scaling()
        out = buf.getvalue()
        assert "Worker Count Scaling" in out
        assert "Performance by Worker Count" in out
        assert "Sequential" in out

    def test_example_period_only_mode(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m.example_period_only_mode()
        out = buf.getvalue()
        assert "Period-Only Mode" in out
        assert "Period sum: 16 (should equal state space size: 16)" in out

    def test_example_auto_detection(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m.example_auto_detection()
        out = buf.getvalue()
        assert "Automatic Parallel Detection" in out
        assert "Available CPU cores:" in out


class TestMain:
    def test_main_runs_end_to_end(self, capsys):
        m.main()
        captured = capsys.readouterr()
        assert "Parallel State Enumeration Examples" in captured.out
        assert "Examples Complete!" in captured.out
        assert "ERROR" not in captured.err

    def test_main_except_block_on_unexpected_error(self, capsys, monkeypatch):
        """Covers main()'s except block (lines ~211-215), unreachable
        with the script's own well-formed calls."""
        import pytest

        def raiser():
            raise RuntimeError("simulated failure for coverage")

        monkeypatch.setattr(m, "example_basic_parallel", raiser)

        with pytest.raises(SystemExit) as exc_info:
            m.main()
        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "ERROR: simulated failure for coverage" in err

import sys


class TestSageImportGuardParallel:
    """Regression coverage for the module-level
    `try: from sage.all import * / except ImportError: print(...);
    sys.exit(1)` guard in lfsr.examples.parallel_processing_example (source lines near the
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
        modname = "lfsr.examples.parallel_processing_example"

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
