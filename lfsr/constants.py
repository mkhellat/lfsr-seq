#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Constants used throughout the LFSR analysis package.

This module defines named constants to replace magic numbers and improve
code maintainability.
"""

# Display formatting constants
DISPLAY_WIDTH = 60  # Standard display width for sections, tables, etc.
INTRO_HEADER_WIDTH = 62  # Width of introduction header border
LABEL_PADDING_WIDTH = 26  # Padding width for labels in intro section
PLATFORM_INDENT = 29  # Indent for platform text wrapping

# Table and sequence display constants
TABLE_ROW_WIDTH = 60  # Width of sequence table rows
PROGRESS_BAR_WIDTH = 60  # Width of progress bar display

# Polynomial display constants
POLYNOMIAL_DISPLAY_WIDTH = 38  # Width for polynomial term wrapping
FACTOR_DISPLAY_WIDTH = 55  # Width for factor display wrapping

# Field validation constants
MAX_PRIME_POWER_LIMIT = 1000  # Maximum prime power to check during validation
MIN_GF_ORDER = 2  # Minimum valid Galois field order

# Text wrapping constants
TEXT_WRAP_WIDTH = 60  # Standard text wrapping width
TEXT_INDENT = 2  # Standard text indent for wrapped lines
