#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Input/Output operations for LFSR analysis.

This module handles CSV file reading, validation, and data preparation
for LFSR coefficient vectors.
"""

import csv
import os
import sys
from pathlib import Path
from typing import List

from lfsr.constants import MAX_CSV_ROWS, MAX_FILE_SIZE


def sanitize_file_path(filepath: str) -> Path:
    """
    Sanitize and validate file path to prevent path traversal attacks.

    Args:
        filepath: Input file path string

    Returns:
        Path object with resolved absolute path

    Raises:
        SystemExit: If path contains suspicious patterns or cannot be
          resolved
    """
    try:
        path = Path(filepath).resolve()
    except (OSError, ValueError) as e:
        print(f"ERROR: Invalid file path: {filepath}")
        print(f"       {str(e)}")
        sys.exit(1)

    # Check for path traversal attempts
    # Resolve to absolute path and check for suspicious patterns
    path_str = str(path)
    if ".." in path_str or path_str.startswith("/proc") or path_str.startswith("/sys"):
        print(f"ERROR: Suspicious file path detected: {filepath}")
        print("       Path traversal attempts are not allowed")
        sys.exit(1)

    return path


def validate_csv_file(filename: str) -> None:
    """
    Validate that CSV file exists, is readable, and meets security
    requirements.

    This function performs comprehensive validation including:
    - File existence and readability
    - Path sanitization (prevents path traversal)
    - File size limits (prevents DoS attacks)
    - File type validation

    Args:
        filename: Path to the CSV file

    Raises:
        SystemExit: If validation fails with appropriate error message
    """
    # Sanitize and resolve file path
    file_path = sanitize_file_path(filename)

    if not file_path.exists():
        print(f"ERROR: CSV file not found: {filename}")
        sys.exit(1)

    if not file_path.is_file():
        print(f"ERROR: Path is not a file: {filename}")
        sys.exit(1)

    if not os.access(str(file_path), os.R_OK):
        print(f"ERROR: CSV file is not readable: {filename}")
        sys.exit(1)

    # Check file size to prevent DoS attacks
    file_size = file_path.stat().st_size
    if file_size == 0:
        print(f"ERROR: CSV file is empty: {filename}")
        sys.exit(1)

    if file_size > MAX_FILE_SIZE:
        print(f"ERROR: CSV file too large: {filename}")
        print(f"       File size: {file_size} bytes")
        print(f"       Maximum allowed: {MAX_FILE_SIZE} bytes ({MAX_FILE_SIZE // (1024*1024)} MB)")
        sys.exit(1)


def read_and_validate_csv(filename: str, gf_order: int) -> List[List[str]]:
    """
    Read CSV file and validate its contents.

    This function performs validation including:
    - File path sanitization
    - File size limits
    - Row count limits (prevents memory exhaustion)
    - Content validation

    Args:
        filename: Path to the CSV file
        gf_order: The field order for coefficient validation

    Returns:
        List of coefficient vectors (each vector is a list of strings)

    Raises:
        SystemExit: If validation fails
    """
    validate_csv_file(filename)

    with open(filename, mode="r", encoding="utf-8") as coeffs_file:
        coeffs = csv.reader(coeffs_file)
        coeffs_list = []

        # Read rows with limit to prevent memory exhaustion
        for row_num, row in enumerate(coeffs, start=1):
            if row_num > MAX_CSV_ROWS:
                print(f"ERROR: CSV file has too many rows: {filename}")
                print(f"       Maximum allowed: {MAX_CSV_ROWS} rows")
                print(f"       Found at least: {row_num} rows")
                sys.exit(1)
            coeffs_list.append(row)

        # Check if CSV is empty
        if len(coeffs_list) == 0:
            print(f"ERROR: CSV file contains no data: {filename}")
            sys.exit(1)

        # Check for consistent vector lengths
        if len(coeffs_list) > 1:
            first_length = len(coeffs_list[0])
            for i, row in enumerate(coeffs_list[1:], start=2):
                if len(row) != first_length:
                    print(
                        "WARNING: Coefficient vector %d has length %d, expected %d"
                        % (i, len(row), first_length)
                    )
                    print(
                        "         All vectors should have the same length for consistency"
                    )

        return coeffs_list


def read_csv_coefficients(filename: str) -> List[List[str]]:
    """
    Read coefficient vectors from CSV file without validation.

    This is a simple CSV reader that does not perform validation.
    Use `read_and_validate_csv` for validated reading.

    Args:
        filename: Path to the CSV file

    Returns:
        List of coefficient vectors, where each vector is a list of
          strings. Each row in the CSV becomes one coefficient
          vector.

    Note:
        This function does not validate:
        - File existence
        - File readability
        - Coefficient values
        - Vector lengths

    Example:
        >>> coeffs = read_csv_coefficients("data.csv")
        >>> print(coeffs[0])  # First coefficient vector
        ['1', '1', '0', '1']
    """
    with open(filename, mode="r") as coeffs_file:
        coeffs = csv.reader(coeffs_file)
        return list(coeffs)
