"""
lfsr - Linear Feedback Shift Register Analysis Package

This package provides tools for analyzing Linear Feedback Shift
Register sequences, computing periods, and determining characteristic
polynomials over finite fields.

Main Components:
- core: LFSR core mathematics and state update operations
- analysis: Sequence analysis and period calculation
- polynomial: Polynomial operations and characteristic polynomial
  calculation
- field: Finite field operations and validation
- io: Input/output handling
- formatter: Output formatting utilities
- cli: Command-line interface

Example:
    >>> from lfsr.cli import main
    >>> main("coefficients.csv", "2", output_file=open("output.txt", "w"))
"""

__version__ = "0.2.0"
__author__ = "Mohammadreza Khellat"

# Import non-sage-dependent modules at top level
from lfsr.cli import cli_main, main
from lfsr.constants import (
    DISPLAY_WIDTH,
    FACTOR_DISPLAY_WIDTH,
    INTRO_HEADER_WIDTH,
    LABEL_PADDING_WIDTH,
    MAX_PRIME_POWER_LIMIT,
    MIN_GF_ORDER,
    PLATFORM_INDENT,
    POLYNOMIAL_DISPLAY_WIDTH,
    PROGRESS_BAR_WIDTH,
    TABLE_ROW_WIDTH,
    TEXT_INDENT,
    TEXT_WRAP_WIDTH,
)
from lfsr.formatter import dump, dump_seq_row, intro, section, subsection
from lfsr.io import read_and_validate_csv, validate_csv_file

# Sage-dependent imports are lazy-loaded to avoid requiring sage for --help
# These will be imported on first access via __getattr__
def __getattr__(name: str):
    """Lazy import for sage-dependent modules."""
    if name == "lfsr_sequence_mapper":
        from lfsr.analysis import lfsr_sequence_mapper
        return lfsr_sequence_mapper
    elif name == "build_state_update_matrix":
        from lfsr.core import build_state_update_matrix
        return build_state_update_matrix
    elif name == "compute_matrix_order":
        from lfsr.core import compute_matrix_order
        return compute_matrix_order
    elif name == "validate_coefficient_vector":
        from lfsr.field import validate_coefficient_vector
        return validate_coefficient_vector
    elif name == "validate_gf_order":
        from lfsr.field import validate_gf_order
        return validate_gf_order
    elif name == "characteristic_polynomial":
        from lfsr.polynomial import characteristic_polynomial
        return characteristic_polynomial
    elif name == "polynomial_order":
        from lfsr.polynomial import polynomial_order
        return polynomial_order
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # CLI
    "main",
    "cli_main",
    # Core
    "build_state_update_matrix",
    "compute_matrix_order",
    # Analysis
    "lfsr_sequence_mapper",
    # Polynomial
    "characteristic_polynomial",
    "polynomial_order",
    # Field
    "validate_gf_order",
    "validate_coefficient_vector",
    # I/O
    "read_and_validate_csv",
    "validate_csv_file",
    # Formatter
    "dump",
    "intro",
    "section",
    "subsection",
    "dump_seq_row",
    # Constants
    "DISPLAY_WIDTH",
    "INTRO_HEADER_WIDTH",
    "LABEL_PADDING_WIDTH",
    "PLATFORM_INDENT",
    "TABLE_ROW_WIDTH",
    "PROGRESS_BAR_WIDTH",
    "POLYNOMIAL_DISPLAY_WIDTH",
    "FACTOR_DISPLAY_WIDTH",
    "MAX_PRIME_POWER_LIMIT",
    "MIN_GF_ORDER",
    "TEXT_WRAP_WIDTH",
    "TEXT_INDENT",
]
