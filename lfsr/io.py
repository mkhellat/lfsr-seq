#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Input/Output operations for LFSR analysis.

This module handles CSV file reading, validation, and data preparation
for LFSR coefficient vectors.
"""

import sys
import os
import csv
from typing import List, Tuple


def validate_csv_file(filename: str) -> None:
    """
    Validate that CSV file exists and is readable.
    
    Args:
        filename: Path to the CSV file
        
    Raises:
        SystemExit: If validation fails with appropriate error message
    """
    if not os.path.exists(filename):
        print("ERROR: CSV file not found: %s" % filename)
        sys.exit(1)
    
    if not os.path.isfile(filename):
        print("ERROR: Path is not a file: %s" % filename)
        sys.exit(1)
    
    if not os.access(filename, os.R_OK):
        print("ERROR: CSV file is not readable: %s" % filename)
        sys.exit(1)
    
    # Check if file is empty
    if os.path.getsize(filename) == 0:
        print("ERROR: CSV file is empty: %s" % filename)
        sys.exit(1)


def read_and_validate_csv(filename: str, gf_order: int) -> List[List[str]]:
    """
    Read CSV file and validate its contents.
    
    Args:
        filename: Path to the CSV file
        gf_order: The field order for coefficient validation
        
    Returns:
        List of coefficient vectors (each vector is a list of strings)
        
    Raises:
        SystemExit: If validation fails
    """
    validate_csv_file(filename)
    
    with open(filename, mode='r') as coeffs_file:
        coeffs = csv.reader(coeffs_file)
        coeffs_list = list(coeffs)
        
        # Check if CSV is empty
        if len(coeffs_list) == 0:
            print("ERROR: CSV file contains no data: %s" % filename)
            sys.exit(1)
        
        # Check for consistent vector lengths
        if len(coeffs_list) > 1:
            first_length = len(coeffs_list[0])
            for i, row in enumerate(coeffs_list[1:], start=2):
                if len(row) != first_length:
                    print("WARNING: Coefficient vector %d has length %d, expected %d" 
                          % (i, len(row), first_length))
                    print("         All vectors should have the same length for consistency")
        
        return coeffs_list


def read_csv_coefficients(filename: str) -> List[List[str]]:
    """
    Read coefficient vectors from CSV file.
    
    Args:
        filename: Path to the CSV file
        
    Returns:
        List of coefficient vectors (each vector is a list of strings)
    """
    with open(filename, mode='r') as coeffs_file:
        coeffs = csv.reader(coeffs_file)
        return list(coeffs)

