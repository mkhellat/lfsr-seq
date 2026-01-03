#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Finite field operations and validation for LFSR analysis.

This module provides functions for validating and working with finite fields
(Galois fields) used in LFSR analysis.
"""

import sys

from sage.all import *

from lfsr.constants import MAX_PRIME_POWER_LIMIT, MIN_GF_ORDER


def validate_gf_order(gf_order_str: str) -> int:
    """
    Validate that GF_order is a valid prime or prime power.

    Args:
        gf_order_str: String representation of the field order

    Returns:
        Validated integer field order

    Raises:
        SystemExit: If validation fails with appropriate error message
    """
    try:
        gf_order = int(gf_order_str)
    except ValueError:
        print("ERROR: GF_order must be an integer, got: %s" % gf_order_str)
        sys.exit(1)

    if gf_order < MIN_GF_ORDER:
        print("ERROR: GF_order must be at least %d, got: %d" % (MIN_GF_ORDER, gf_order))
        sys.exit(1)

    # Check if it's a prime
    if is_prime(gf_order):
        return gf_order

    # Check if it's a prime power (p^n where p is prime and n > 1)
    # For now, we'll support small prime powers
    # A more complete check would factor gf_order and verify it's p^n
    if gf_order <= MAX_PRIME_POWER_LIMIT:
        # Try to find if it's a prime power
        for p in primes(2, int(sqrt(gf_order)) + 1):
            n = 1
            power = p
            while power < gf_order:
                power = power * p
                n += 1
            if power == gf_order:
                return gf_order

    print("ERROR: GF_order must be a prime or prime power, got: %d"
          % gf_order)
    print("       Supported: primes and small prime powers (p^n where p"
          " is prime)")
    sys.exit(1)


def validate_coefficient(
    coeff_str: str, gf_order: int, vector_num: int, position: int
) -> int:
    """
    Validate a single coefficient value.

    Args:
        coeff_str: String representation of the coefficient
        gf_order: The field order
        vector_num: The coefficient vector number (for error messages)
        position: The position in the vector (for error messages)

    Returns:
        Validated integer coefficient

    Raises:
        SystemExit: If validation fails with appropriate error message
    """
    try:
        coeff = int(coeff_str)
    except ValueError:
        print(
            "ERROR: Invalid coefficient in vector %d, position %d: %s"
            % (vector_num, position, coeff_str)
        )
        print("       Coefficients must be integers")
        sys.exit(1)

    if coeff < 0 or coeff >= gf_order:
        print(
            "ERROR: Coefficient out of range in vector %d, position %d: %d"
            % (vector_num, position, coeff)
        )
        print("       Coefficients must be in range [0, %d)" % gf_order)
        sys.exit(1)

    return coeff


def validate_coefficient_vector(
    coeffs_vector: list, gf_order: int, vector_num: int
) -> None:
    """
    Validate an entire coefficient vector.

    Args:
        coeffs_vector: List of coefficient strings
        gf_order: The field order
        vector_num: The vector number (for error messages)

    Raises:
        SystemExit: If validation fails with appropriate error message
    """
    if len(coeffs_vector) == 0:
        print("ERROR: Coefficient vector %d is empty" % vector_num)
        sys.exit(1)

    # Validate each coefficient
    for i, coeff_str in enumerate(coeffs_vector):
        validate_coefficient(coeff_str, gf_order, vector_num, i)
