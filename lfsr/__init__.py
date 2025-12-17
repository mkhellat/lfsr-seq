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
    >>> from lfsr.cli import main
    >>> main("coefficients.csv", "2", output_file=open("output.txt", "w"))
"""

__version__ = "0.2.0"
__author__ = "Mohammadreza Khellat"

# Export main functions
from lfsr.analysis import lfsr_sequence_mapper
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
from lfsr.core import build_state_update_matrix, compute_matrix_order
from lfsr.field import validate_coefficient_vector, validate_gf_order
from lfsr.formatter import dump, dump_seq_row, intro, section, subsection
from lfsr.io import read_and_validate_csv, validate_csv_file
from lfsr.polynomial import characteristic_polynomial, polynomial_order

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
