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


class TestMain:
    def test_main_runs_end_to_end(self, capsys, patched_global_cache):
        m.main()
        captured = capsys.readouterr()
        assert "Optimization Techniques Examples" in captured.out
        assert "Examples Complete!" in captured.out
        assert "ERROR" not in captured.err
