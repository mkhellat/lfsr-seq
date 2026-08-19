#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for lfsr/__init__.py.

Covers:
- The sage-dependent lazy-attribute dispatch table in __getattr__ (each
  named branch, plus the final AttributeError fallback for an unknown
  name).
- The `from lfsr._version import version as __version__` / `except
  ImportError: __version__ = "0.0.0+unknown"` fallback, which is only
  reachable in this dev environment by simulating an ImportError on
  `lfsr._version` and re-importing the package fresh (setuptools-scm
  normally generates a real _version.py, so the fallback never
  triggers naturally here).
"""

import builtins
import sys

import pytest


class TestLazyGetattr:
    """Each dispatch branch inside lfsr.__getattr__ (lines ~53-74)."""

    def test_lfsr_sequence_mapper(self):
        import lfsr

        assert callable(lfsr.lfsr_sequence_mapper)

    def test_build_state_update_matrix(self):
        import lfsr

        assert callable(lfsr.build_state_update_matrix)

    def test_compute_matrix_order(self):
        import lfsr

        assert callable(lfsr.compute_matrix_order)

    def test_validate_coefficient_vector(self):
        import lfsr

        assert callable(lfsr.validate_coefficient_vector)

    def test_validate_gf_order(self):
        import lfsr

        assert callable(lfsr.validate_gf_order)

    def test_characteristic_polynomial(self):
        import lfsr

        assert callable(lfsr.characteristic_polynomial)

    def test_polynomial_order(self):
        import lfsr

        assert callable(lfsr.polynomial_order)

    def test_lazy_attrs_are_the_real_underlying_functions(self):
        """Sanity check that the lazy dispatch doesn't just return *some*
        callable, but genuinely the same function object as importing
        the submodule directly."""
        import lfsr
        from lfsr.core import build_state_update_matrix

        assert lfsr.build_state_update_matrix is build_state_update_matrix

    def test_unknown_attribute_raises_attribute_error(self):
        import lfsr

        with pytest.raises(AttributeError, match="has no attribute 'totally_bogus_name'"):
            lfsr.totally_bogus_name


class TestVersionFallback:
    """Regression coverage for the `except ImportError: __version__ =
    "0.0.0+unknown"` branch (lines ~25-26). Simulates lfsr._version being
    unimportable by intercepting the import machinery, then re-imports
    the lfsr package fresh so its module-level try/except actually runs
    again under the simulated failure."""

    def test_version_falls_back_when_version_module_unimportable(self):
        # Snapshot every lfsr.* module currently cached so we can restore
        # them afterward -- this test forces a real re-import of the
        # `lfsr` package, which must not leak a half-initialized module
        # into the rest of the test session.
        saved_modules = {
            name: mod for name, mod in sys.modules.items()
            if name == "lfsr" or name.startswith("lfsr.")
        }

        real_import = builtins.__import__

        def blocking_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "lfsr._version":
                raise ImportError("simulated: lfsr._version unavailable")
            return real_import(name, globals, locals, fromlist, level)

        for name in list(sys.modules):
            if name == "lfsr" or name.startswith("lfsr."):
                del sys.modules[name]

        builtins.__import__ = blocking_import
        try:
            import lfsr

            assert lfsr.__version__ == "0.0.0+unknown"
        finally:
            builtins.__import__ = real_import
            for name in list(sys.modules):
                if name == "lfsr" or name.startswith("lfsr."):
                    del sys.modules[name]
            sys.modules.update(saved_modules)

    def test_real_version_module_used_when_available(self):
        """Baseline: under normal conditions (no simulated failure),
        lfsr.__version__ comes from the real generated lfsr._version
        module, not the fallback string."""
        import lfsr
        from lfsr._version import version

        assert lfsr.__version__ == version
        assert lfsr.__version__ != "0.0.0+unknown"
