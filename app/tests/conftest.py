#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pytest configuration and fixtures for LFSR test suite.

This module provides shared fixtures and handles SageMath availability checks.
"""


import pytest

from lfsr._sage_discovery import ensure_sage_importable

# Try to make SageMath importable (this may shell out to the `sage` command
# to locate its modules if they aren't already on sys.path -- see
# lfsr._sage_discovery for why a bare `import sage` isn't reliable across
# all the ways SageMath can be installed) - if it still fails, mark all
# tests to skip.
#
# Deliberately NOT `from sage.all import *` here: sage.all exposes several
# names (e.g. `qsieve`) as sage.misc.lazy_import.LazyImport objects, whose
# __getattr__ triggers a real import as a side effect of merely being
# accessed. pytest's own fixture discovery (FixtureManager.parsefactories)
# walks every top-level name in every conftest.py module looking for
# `_pytestfixturefunction`, which -- combined with pytest's assertion-
# rewriting import hook intercepting that triggered import -- causes an
# intermittent multi-second-to-indefinite hang at session start (confirmed
# via py-spy: stuck inside AssertionRewritingHook.find_spec importing
# sage.libs.flint.qsieve_sage while pytest_sessionstart is scanning this
# module for fixtures). conftest.py doesn't need any sage.all names itself,
# only SAGEMATH_AVAILABLE below, so importing sage without star-importing
# its names into this module's (fixture-scanned) namespace avoids the
# problem entirely.
if ensure_sage_importable():
    import sage.all  # noqa: F401  (import only, deliberately not `from ... import *`)
    SAGEMATH_AVAILABLE = True
else:
    SAGEMATH_AVAILABLE = False
    # Create a dummy marker to skip tests that require SageMath
    pytestmark = pytest.mark.skip(reason="SageMath not available")


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "sagemath: mark test as requiring SageMath (deselect with '-m \"not sagemath\"')"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests that require SageMath."""
    if not SAGEMATH_AVAILABLE:
        # Skip all tests if SageMath is not available
        skip_sagemath = pytest.mark.skip(reason="SageMath not available")
        for item in items:
            item.add_marker(skip_sagemath)
    else:
        # Mark tests that import sage.all as requiring SageMath
        for item in items:
            # Check if the test file imports sage
            if hasattr(item, "module"):
                try:
                    source = item.module.__file__
                    if source:
                        with open(source, "r") as f:
                            content = f.read()
                            if "from sage.all import" in content or "import sage" in content:
                                item.add_marker(pytest.mark.sagemath)
                except (AttributeError, IOError):
                    pass

