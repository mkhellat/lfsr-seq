"""
lfsr - Linear Feedback Shift Register Analysis Package

This package provides tools for analyzing Linear Feedback Shift Register sequences,
computing periods, and determining characteristic polynomials over finite fields.

Main Components:
- core: LFSR core mathematics and state update operations
- analysis: Sequence analysis and period calculation
- polynomial: Polynomial operations and characteristic polynomial calculation
- field: Finite field operations and validation
- io: Input/output handling
- formatter: Output formatting utilities
- cli: Command-line interface

Example:
    >>> from lfsr import LFSR
    >>> lfsr = LFSR([1, 1, 1, 0], gf_order=2)
    >>> sequences = lfsr.analyze_sequences()
"""

__version__ = "0.2.0"
__author__ = "Mohammadreza Khellat"

# Package will be populated during refactoring
__all__ = []

