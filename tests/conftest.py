#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pytest configuration and fixtures for LFSR test suite.

This module provides shared fixtures and handles SageMath availability checks.
"""

import pytest
import sys

# Try to import SageMath - if it fails, mark all tests to skip
try:
    from sage.all import *
    SAGEMATH_AVAILABLE = True
except ImportError:
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

