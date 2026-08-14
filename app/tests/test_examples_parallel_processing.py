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
