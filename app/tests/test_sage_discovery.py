#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for lfsr._sage_discovery.ensure_sage_importable.

This module has no SageMath imports of its own and is deliberately
always importable, so it doesn't need the sage-availability skip that
most of this suite's conftest.py machinery applies. Its behavior
branches on whether a bare `import sage` succeeds, and (if not)
whether shelling out to the `sage` command on PATH succeeds -- both of
which need to be simulated/mocked here since, in the real dev
environment used to run this suite, `import sage` genuinely succeeds
(so the interesting fallback/failure branches never trigger
naturally).

Every test resets the module's cache flags (_discovery_attempted,
_discovery_succeeded) before and after, since ensure_sage_importable()
is documented as memoizing its result after the first real call.
"""

import subprocess
import sys

import pytest

import lfsr._sage_discovery as sd


@pytest.fixture(autouse=True)
def _reset_discovery_cache():
    """Ensure each test starts and ends with a clean (unmemoized) cache,
    so tests don't leak state into each other or into the rest of the
    suite (other modules may call ensure_sage_importable() for real)."""
    saved_attempted = sd._discovery_attempted
    saved_succeeded = sd._discovery_succeeded
    sd._discovery_attempted = False
    sd._discovery_succeeded = False
    yield
    sd._discovery_attempted = saved_attempted
    sd._discovery_succeeded = saved_succeeded


def test_direct_import_succeeds_when_sage_already_on_sys_path():
    """The real environment: `import sage` succeeds directly (it's
    already importable, e.g. because conftest.py or an earlier test
    already made it so), so the function returns True without ever
    shelling out to the `sage` command."""
    assert "sage" in sys.modules  # true in this dev venv once sage.all was ever imported
    result = sd.ensure_sage_importable()
    assert result is True
    assert sd._discovery_succeeded is True


def test_result_is_memoized_across_calls(monkeypatch):
    """Second call must not re-run any discovery logic -- it just
    returns the cached result, even if the underlying situation
    "changes" (simulated here by making subprocess.run explode, which
    would only matter if discovery re-ran)."""
    first = sd.ensure_sage_importable()
    assert first is True

    def _boom(*args, **kwargs):
        raise AssertionError("subprocess.run should not be called on a memoized result")

    monkeypatch.setattr(subprocess, "run", _boom)
    second = sd.ensure_sage_importable()
    assert second == first


def test_falls_back_to_sage_command_when_direct_import_fails(monkeypatch):
    """When `import sage` fails directly, the function should shell out
    to the `sage` command, parse its sys.path, and retry the import.
    Simulated by blocking the direct import (removing 'sage' from
    sys.modules and injecting a stub importer that raises ImportError
    for the first attempt only) while mocking subprocess.run to report
    a sys.path that -- once inserted -- lets the second `import sage`
    attempt succeed via a fake module we plant directly into
    sys.modules keyed by a path subprocess.run "discovers"."""
    # Remove any cached real sage module so `import sage` re-executes.
    saved_sage_modules = {
        name: mod for name, mod in list(sys.modules.items())
        if name == "sage" or name.startswith("sage.")
    }
    for name in list(saved_sage_modules):
        del sys.modules[name]

    call_count = {"n": 0}
    real_import = __import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "sage" and level == 0 and not fromlist:
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise ImportError("simulated: sage not yet on sys.path")
            # Second call (after "sys.path" was patched): succeed by
            # injecting a minimal fake module.
            fake_mod = type(sys)("sage")
            sys.modules["sage"] = fake_mod
            return fake_mod
        return real_import(name, globals, locals, fromlist, level)

    class FakeCompletedProcess:
        returncode = 0
        stdout = "/fake/sage/site-packages\n"

    def fake_run(cmd, capture_output, text, timeout):
        assert cmd[0] == "sage"
        return FakeCompletedProcess()

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("builtins.__import__", fake_import)
    # os.path.isdir must say the fake path exists so it gets inserted.
    monkeypatch.setattr("os.path.isdir", lambda p: p == "/fake/sage/site-packages")

    try:
        result = sd.ensure_sage_importable()
        assert result is True
        assert "/fake/sage/site-packages" in sys.path
    finally:
        sys.path[:] = [p for p in sys.path if p != "/fake/sage/site-packages"]
        for name in list(sys.modules):
            if name == "sage" or name.startswith("sage."):
                del sys.modules[name]
        sys.modules.update(saved_sage_modules)


def test_subprocess_timeout_returns_false(monkeypatch):
    """If `sage` isn't on PATH, or hangs, or errors out at the process
    level, the function should return False rather than raising."""
    saved_sage_modules = {
        name: mod for name, mod in list(sys.modules.items())
        if name == "sage" or name.startswith("sage.")
    }
    for name in list(saved_sage_modules):
        del sys.modules[name]

    real_import = __import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "sage" and level == 0 and not fromlist:
            raise ImportError("simulated: sage not importable")
        return real_import(name, globals, locals, fromlist, level)

    def fake_run(cmd, capture_output, text, timeout):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=timeout)

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("builtins.__import__", fake_import)

    try:
        result = sd.ensure_sage_importable()
        assert result is False
    finally:
        sys.modules.update(saved_sage_modules)


def test_sage_command_nonzero_returncode_returns_false(monkeypatch):
    """If the `sage` command runs but exits with a nonzero status
    (e.g. a broken installation), the function should treat that as
    discovery failure and return False."""
    saved_sage_modules = {
        name: mod for name, mod in list(sys.modules.items())
        if name == "sage" or name.startswith("sage.")
    }
    for name in list(saved_sage_modules):
        del sys.modules[name]

    real_import = __import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "sage" and level == 0 and not fromlist:
            raise ImportError("simulated: sage not importable")
        return real_import(name, globals, locals, fromlist, level)

    class FakeCompletedProcess:
        returncode = 1
        stdout = ""

    def fake_run(cmd, capture_output, text, timeout):
        return FakeCompletedProcess()

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("builtins.__import__", fake_import)

    try:
        result = sd.ensure_sage_importable()
        assert result is False
    finally:
        sys.modules.update(saved_sage_modules)


def test_sage_command_succeeds_but_import_still_fails_returns_false(monkeypatch):
    """Edge case: the `sage` command runs successfully and reports a
    sys.path, but `import sage` still fails afterward (e.g. the
    reported paths don't actually contain a usable sage package).
    Should return False, not raise."""
    saved_sage_modules = {
        name: mod for name, mod in list(sys.modules.items())
        if name == "sage" or name.startswith("sage.")
    }
    for name in list(saved_sage_modules):
        del sys.modules[name]

    real_import = __import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "sage" and level == 0 and not fromlist:
            raise ImportError("simulated: sage still not importable")
        return real_import(name, globals, locals, fromlist, level)

    class FakeCompletedProcess:
        returncode = 0
        stdout = "/fake/still/broken/path\n"

    def fake_run(cmd, capture_output, text, timeout):
        return FakeCompletedProcess()

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("builtins.__import__", fake_import)
    monkeypatch.setattr("os.path.isdir", lambda p: p == "/fake/still/broken/path")

    try:
        result = sd.ensure_sage_importable()
        assert result is False
    finally:
        sys.path[:] = [p for p in sys.path if p != "/fake/still/broken/path"]
        sys.modules.update(saved_sage_modules)
