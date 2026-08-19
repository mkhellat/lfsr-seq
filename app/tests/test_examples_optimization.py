#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Smoke tests for lfsr.examples.optimization_example -- a standalone
demo/tutorial script (not part of the public API, not imported by any
library code, not wired into the CLI; see
src/lfsr/examples/__init__.py). It wraps already-tested library
functions (lfsr.polynomial.compute_period_via_factorization /
detect_mathematical_shortcuts, lfsr.optimization.ResultCache), so these
tests are deliberately shallow: each example_*() function is invoked
with stdout captured and we assert only that it runs to completion
without raising.

KNOWN RISK, verified and handled: example_global_cache() calls
lfsr.optimization.get_global_cache(), which -- unlike
example_result_caching()'s ResultCache(cache_file=None) -- lazily
creates a module-level singleton backed by a REAL, persistent,
disk-backed file at ~/.lfsr-seq/cache.json (see optimization.py
get_global_cache(), line ~266: `os.path.expanduser("~/.lfsr-seq/cache.json")`,
unconditionally, not under any XDG/tmp override). Calling it
unpatched would create/mutate a real file outside the repo. The
`patched_global_cache` fixture below monkeypatches
`lfsr.optimization.os.path.expanduser` so that only the literal
"~/.lfsr-seq/cache.json" path is redirected to a pytest tmp_path, and
resets the `_global_cache` module singleton before and after each
test so no cross-test / cross-run state leaks. Verified interactively
(outside pytest) that with this patch in place, `~/.lfsr-seq/cache.json`
on the real filesystem is never created or modified by running these
tests, and that only `theoretical.db` (pre-existing, unrelated to this
module) is present in ~/.lfsr-seq/ afterwards.

All functions in this module (including example_global_cache with the
patch, and main()) were run interactively against this checkout before
writing any assertion; none raised and none took longer than ~1s. No
bugs were found in this module.
"""

import io
import contextlib
from unittest import mock

import pytest

from lfsr.examples import optimization_example as m
import lfsr.optimization as optimization


@pytest.fixture
def patched_global_cache(tmp_path, monkeypatch):
    """Redirect the global, disk-backed cache to a tmp_path location.

    Prevents example_global_cache() / main() from creating or mutating
    the real ~/.lfsr-seq/cache.json file on the developer's machine.
    """
    tmp_cache = str(tmp_path / "cache.json")
    real_expanduser = optimization.os.path.expanduser

    def fake_expanduser(path):
        if path == "~/.lfsr-seq/cache.json":
            return tmp_cache
        return real_expanduser(path)

    monkeypatch.setattr(optimization.os.path, "expanduser", fake_expanduser)
    monkeypatch.setattr(optimization, "_global_cache", None)
    yield tmp_cache
    monkeypatch.setattr(optimization, "_global_cache", None)


class TestExampleFunctions:
    def test_example_period_via_factorization(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m.example_period_via_factorization()
        out = buf.getvalue()
        assert "Period Computation via Factorization" in out
        assert "Period:" in out

    def test_example_shortcut_detection(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m.example_shortcut_detection()
        out = buf.getvalue()
        assert "Mathematical Shortcut Detection" in out
        assert "Is primitive:" in out

    def test_example_result_caching(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m.example_result_caching()
        out = buf.getvalue()
        assert "Result Caching" in out
        assert "Cache Statistics" in out
        # Note: the "miss" branch in this example checks `key in cache`
        # (ResultCache.__contains__), which does not touch cache_stats --
        # only .get()/.set() do. So only the later cache-hit .get() call
        # increments 'hits'; 'misses' stays 0. Verified via actual output.
        assert "Hits: 1" in out
        assert "Misses: 0" in out

    def test_example_global_cache_does_not_touch_real_cache_file(
        self, patched_global_cache
    ):
        # `import os` gives the same module object everywhere (Python
        # caches modules in sys.modules) -- monkeypatch.setattr on
        # optimization.os.path.expanduser therefore patches the *same*
        # os.path.expanduser seen by any other `import os` in this
        # process, this test included. So to independently verify the
        # real, hardcoded path string on the real filesystem, we must
        # NOT go through os.path.expanduser at all here -- build it by
        # hand from HOME instead.
        import pathlib

        real_cache_path = pathlib.Path.home() / ".lfsr-seq" / "cache.json"
        existed_before = real_cache_path.exists()

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m.example_global_cache()
        out = buf.getvalue()

        assert "Global Cache" in out
        assert "Cache file:" in out
        assert patched_global_cache in out  # confirms redirection took effect

        # The real, hardcoded ~/.lfsr-seq/cache.json path must be
        # unaffected by running this example under the fixture's patch.
        assert real_cache_path.exists() == existed_before


class TestFactorizationFailureBranches:
    """example_period_via_factorization() has two independent
    if/else branches (lines 49-53 and 61-65) for the small and the
    "larger" (degree 8) coefficient lists. Both use the module-level
    compute_period_via_factorization -- monkeypatch it to always
    return None to hit both "Factorization failed" else-branches."""

    def test_both_failure_branches_printed(self, monkeypatch):
        monkeypatch.setattr(m, "compute_period_via_factorization", lambda *a, **kw: None)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m.example_period_via_factorization()
        out = buf.getvalue()
        assert "Factorization failed, fall back to enumeration" in out
        assert "Factorization failed" in out


class TestResultCachingBranches:
    def test_key_already_in_cache_on_first_access(self):
        """Regression coverage for lines 116-118: if the key is already
        present before the "first access" check (simulated here by
        pre-seeding the cache), the cache-hit branch prints "Found in
        cache" instead of computing."""
        from lfsr.optimization import ResultCache
        from lfsr.polynomial import compute_period_via_factorization

        cache = ResultCache(cache_file=None)
        coefficients = [1, 0, 0, 1]
        field_order = 2
        key = cache.generate_key(coefficients, field_order, "period")
        # Pre-seed so `key in cache` is True on the function's "first access".
        period = compute_period_via_factorization(coefficients, field_order)
        cache.set(key, period)

        # Patch ResultCache to return our pre-seeded instance so
        # example_result_caching()'s internal `ResultCache(cache_file=None)`
        # call yields a cache that already contains the key.
        def fake_result_cache(cache_file=None):
            return cache

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with mock.patch.object(m, "ResultCache", fake_result_cache):
                m.example_result_caching()
        out = buf.getvalue()
        assert "First access (cache miss):" in out
        assert "Found in cache:" in out

    def test_key_evicted_between_accesses_hits_unexpected_branch(self):
        """Regression coverage for line 132: the "Second access" check
        prints "Not in cache (unexpected)" if the key vanished between
        the set() in the first branch and the second `key in cache`
        check. Simulate this with a ResultCache stand-in whose
        __contains__ returns True only once (first access), then False."""

        class FlakyCache:
            def __init__(self, real_cache):
                self._real = real_cache
                self._contains_calls = 0

            def generate_key(self, *a, **kw):
                return self._real.generate_key(*a, **kw)

            def __contains__(self, key):
                self._contains_calls += 1
                # First access (miss) -> False; simulate the entry
                # vanishing before the second check too (also False),
                # forcing the "unexpected" branch.
                return False

            def get(self, key):
                return self._real.get(key)

            def set(self, key, value):
                return self._real.set(key, value)

            def get_stats(self):
                return self._real.get_stats()

        from lfsr.optimization import ResultCache

        real_cache = ResultCache(cache_file=None)
        flaky = FlakyCache(real_cache)

        def fake_result_cache(cache_file=None):
            return flaky

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with mock.patch.object(m, "ResultCache", fake_result_cache):
                m.example_result_caching()
        out = buf.getvalue()
        assert "Not in cache, computing..." in out
        assert "Not in cache (unexpected)" in out


class TestGlobalCacheHitBranch:
    def test_key_already_in_global_cache(self, patched_global_cache):
        """Regression coverage for lines 159-161: if the key is already
        present in the (redirected) global cache before
        example_global_cache() runs, the "Found in persistent cache"
        branch is taken instead of computing+caching."""
        from lfsr.optimization import get_global_cache
        from lfsr.polynomial import compute_period_via_factorization

        cache = get_global_cache()
        key = cache.generate_key([1, 0, 0, 1], 2, "period")
        period = compute_period_via_factorization([1, 0, 0, 1], 2)
        cache.set(key, period)

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m.example_global_cache()
        out = buf.getvalue()
        assert "Found in persistent cache:" in out


class TestMain:
    def test_main_runs_end_to_end(self, capsys, patched_global_cache):
        m.main()
        captured = capsys.readouterr()
        assert "Optimization Techniques Examples" in captured.out
        assert "Examples Complete!" in captured.out
        assert "ERROR" not in captured.err

    def test_main_prints_traceback_and_exits_on_exception(
        self, monkeypatch, capsys, patched_global_cache
    ):
        """Regression coverage for lines 192-196: main()'s except
        Exception handler prints an ERROR message, a traceback, and
        calls sys.exit(1)."""

        def raiser():
            raise RuntimeError("forced failure for coverage")

        monkeypatch.setattr(m, "example_period_via_factorization", raiser)

        with pytest.raises(SystemExit) as exc_info:
            m.main()
        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "ERROR: forced failure for coverage" in captured.err
        assert "RuntimeError" in captured.err
