#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Smoke tests for lfsr.examples.theoretical_analysis_example.

Standalone demo script (not part of the public API, not CLI-wired --
see src/lfsr/examples/__init__.py). Wraps lfsr.theoretical,
lfsr.export_latex, lfsr.paper_generator, lfsr.theoretical_db,
lfsr.benchmarking, and lfsr.reproducibility. Per CLAUDE.md these modules
have little/no independent test coverage, so this smoke test actually
executes each example_*() function and checks it completes without
raising -- it does not assume "just a demo" implies bug-free.
"""

import io
from contextlib import redirect_stdout

import pytest

try:
    from sage.all import *  # noqa: F401,F403
except ImportError:
    pytest.skip("SageMath not available", allow_module_level=True)

from lfsr.examples import theoretical_analysis_example as tae
import lfsr.theoretical_db as theoretical_db


@pytest.fixture(autouse=True)
def _isolated_theoretical_db(tmp_path, monkeypatch):
    """Prevent example_database_comparison()'s get_database() call from
    writing into the real package tree.

    KnownResultDatabase(db_path=None) (the example calls get_database()
    with no args) defaults to writing <package_root>/data/theoretical_db.json
    -- i.e. inside src/lfsr/../data, next to the installed source -- and
    get_database() caches a module-global singleton that ignores db_path
    on every call after the first. Confirmed by directly running the
    example script: it created app/src/data/theoretical_db.json in the
    real repo tree. Reset the global and redirect KnownResultDatabase's
    default path to a pytest tmp_path so the test suite never writes into
    the source tree, and restore state afterward so tests don't leak into
    each other or the next real invocation.
    """
    monkeypatch.setattr(theoretical_db, "_global_db", None)
    monkeypatch.setattr(theoretical_db, "DEFAULT_DATA_DIR", tmp_path, raising=False)
    original_init = theoretical_db.KnownResultDatabase.__init__

    def _patched_init(self, db_path=None):
        if db_path is None:
            db_path = str(tmp_path / "theoretical_db.json")
        original_init(self, db_path=db_path)

    monkeypatch.setattr(theoretical_db.KnownResultDatabase, "__init__", _patched_init)
    yield
    monkeypatch.setattr(theoretical_db, "_global_db", None)


class TestExampleFunctionsRunCleanly:
    def test_example_irreducible_analysis(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            tae.example_irreducible_analysis()
        out = buf.getvalue()
        assert "Is irreducible" in out
        assert "Factors" in out

    def test_example_latex_export(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            tae.example_latex_export()
        out = buf.getvalue()
        assert "Polynomial LaTeX" in out
        assert "LaTeX export functionality demonstrated" in out

    def test_example_paper_generation(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            tae.example_paper_generation()
        out = buf.getvalue()
        assert "Generated research paper" in out

    def test_example_database_comparison(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            tae.example_database_comparison()
        out = buf.getvalue()
        assert "Found in database" in out
        # get_database() auto-populates standard primitive polynomials
        # (including [1, 0, 0, 1] over GF(2), degree 4 -- see
        # theoretical_db.py's get_database()/populate_standard_primitives())
        # whenever the underlying db['primitive_polynomials'] dict is
        # empty, which it always is here (fresh isolated tmp_path DB per
        # test). So this example's own hardcoded [1, 0, 0, 1] coefficients
        # ALWAYS match, hitting the "found" branch, not the "else: No
        # matching results" branch (line ~141) -- see
        # test_database_comparison_not_found_branch below for that one,
        # using coefficients deliberately absent from the seeded set.
        assert "Found in database: True" in out

    def test_database_comparison_not_found_branch(self, monkeypatch):
        """Covers the `else: print("No matching results found in
        database")` branch (line ~141), which
        test_example_database_comparison above cannot reach (see its
        comment): the example's own hardcoded [1, 0, 0, 1] coefficients
        always match get_database()'s auto-seeded standard primitives.
        Monkeypatch tae.get_database (called by example_database_comparison
        via module-global name, with no args) to return a fake db object
        whose compare_with_known() always reports not-found, letting the
        example function's own real print/branch logic execute
        unmodified against that result."""

        class _FakeDB:
            def compare_with_known(self, **kwargs):
                return {"found_in_database": False}

        monkeypatch.setattr(tae, "get_database", lambda: _FakeDB())

        buf = io.StringIO()
        with redirect_stdout(buf):
            tae.example_database_comparison()
        out = buf.getvalue()
        assert "Found in database: False" in out
        assert "No matching results found in database" in out

    def test_example_benchmarking(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            tae.example_benchmarking()
        out = buf.getvalue()
        assert "Benchmark Results" in out
        assert "enumeration" in out
        assert "factorization" in out

    def test_example_reproducibility(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            tae.example_reproducibility()
        out = buf.getvalue()
        assert "Generated reproducibility report" in out


class TestMainEndToEnd:
    def test_main_runs_all_examples_without_raising(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            tae.main()
        out = buf.getvalue()
        assert "Theoretical Analysis Features Examples" in out
        assert "Examples Complete!" in out
        assert "Example 1: Irreducible Polynomial Analysis" in out
        assert "Example 6: Reproducibility Report" in out

    def test_main_except_block_on_unexpected_error(self, monkeypatch):
        """Covers main()'s except block (lines ~219-223), unreachable
        with the script's own well-formed calls."""
        def raiser():
            raise RuntimeError("simulated failure for coverage")

        monkeypatch.setattr(tae, "example_irreducible_analysis", raiser)

        buf_out = io.StringIO()
        buf_err = io.StringIO()
        from contextlib import redirect_stderr

        with redirect_stdout(buf_out):
            with redirect_stderr(buf_err):
                with pytest.raises(SystemExit) as exc_info:
                    tae.main()
        assert exc_info.value.code == 1
        assert "ERROR: simulated failure for coverage" in buf_err.getvalue()
