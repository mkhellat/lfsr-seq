#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LFSR synthesis and analysis algorithms.

This module provides algorithms for synthesizing LFSRs from sequences,
including the Berlekamp-Massey algorithm and linear complexity calculation.
"""

from typing import Any, List, Tuple

from lfsr.sage_imports import *


def berlekamp_massey(sequence: List[int], gf_order: int) -> Tuple[Any, int]:
    """
    Implement the Berlekamp-Massey algorithm for LFSR synthesis.

    Given a sequence of field elements, this algorithm finds the shortest
    LFSR that can generate the sequence. The algorithm returns the
    characteristic polynomial (as a list of coefficients) and the linear
    complexity (length of the LFSR).

    Args:
        sequence: List of integers representing the sequence over GF(gf_order)
        gf_order: The field order

    Returns:
        Tuple of (polynomial, linear_complexity) where:
        - polynomial: Characteristic polynomial as a SageMath polynomial
        - linear_complexity: The linear complexity (degree of the
          polynomial)

    Example:
        >>> seq = [1, 0, 1, 1, 0, 1, 0, 0, 1]
        >>> poly, complexity = berlekamp_massey(seq, 2)
        >>> # Returns the minimal LFSR that generates this sequence
    """
    if len(sequence) == 0:
        raise ValueError("Sequence cannot be empty")

    # Convert sequence to field elements
    F = GF(gf_order)
    s = [F(x) for x in sequence]

    n = len(s)
    if n == 0:
        return PolynomialRing(F, "x")(1), 0

    # Initialize
    R = PolynomialRing(F, "x")
    x = R.gen()
    C = R(1)  # Connection polynomial
    B = R(1)  # Previous connection polynomial
    L = 0  # Current length of LFSR
    m = 1  # Previous discrepancy position
    b = F(1)  # Previous discrepancy value

    for n_iter in range(n):
        # Calculate discrepancy
        d = s[n_iter]
        for i in range(1, L + 1):
            d += C[i] * s[n_iter - i]

        if d == 0:
            # No discrepancy, continue
            m += 1
        else:
            # Discrepancy found
            T = C
            # Update connection polynomial
            C = C - (d / b) * (x ** m) * B

            if 2 * L <= n_iter:
                # Update length and previous values
                L = n_iter + 1 - L
                B = T
                b = d
                m = 1
            else:
                m += 1

    # Return polynomial and linear complexity
    return C, L


def linear_complexity(sequence: List[int], gf_order: int) -> int:
    """
    Calculate the linear complexity of a sequence.

    The linear complexity is the length of the shortest LFSR that can
    generate the sequence. This uses the Berlekamp-Massey algorithm.

    Args:
        sequence: List of integers representing the sequence
        gf_order: The field order

    Returns:
        The linear complexity (non-negative integer)

    Example:
        >>> seq = [1, 0, 1, 1, 0, 1]
        >>> complexity = linear_complexity(seq, 2)
        >>> # Returns the linear complexity
    """
    _, complexity = berlekamp_massey(sequence, gf_order)
    return complexity


def extract_sequence_from_lfsr(
    state_update_matrix: Any, initial_state: Any, length: int
) -> List[int]:
    """
    Extract a sequence from an LFSR given its state update matrix.

    Args:
        state_update_matrix: The LFSR state update matrix
        initial_state: Initial state vector
        length: Length of sequence to generate

    Returns:
        List of output values (first element of each state)
    """
    sequence = []
    state = initial_state

    for _ in range(length):
        # Output is typically the first element of the state
        sequence.append(int(state[0]))
        state = state * state_update_matrix

    return sequence


def synthesize_lfsr_from_sequence(
    sequence: List[int], gf_order: int
) -> Tuple[Any, int]:
    """
    Synthesize an LFSR from a given sequence using Berlekamp-Massey.

    This is a convenience function that uses Berlekamp-Massey to find
    the LFSR and returns it in a usable form.

    Args:
        sequence: List of integers representing the sequence
        gf_order: The field order

    Returns:
        Tuple of (coefficients, length) where:
        - coefficients: List of LFSR coefficients
        - length: Length of the LFSR (linear complexity)
    """
    poly, complexity = berlekamp_massey(sequence, gf_order)

    # poly.coefficients(sparse=False) returns [a_0, a_1, ..., a_complexity]
    # (low-to-high degree), where poly = a_0 + a_1*x + ... + x^complexity.
    # Sage drops trailing zero coefficients, so a genuinely low-degree
    # result (e.g. poly == 1) can come back shorter than complexity + 1;
    # pad with trailing zeros to restore the full-length representation
    # before doing anything else.
    raw_coeffs = poly.coefficients(sparse=False)
    full_coeffs = list(raw_coeffs) + [0] * (complexity + 1 - len(raw_coeffs))

    # The connection polynomial's recurrence is
    # s_n = -a_1*s_{n-1} - ... - a_complexity*s_{n-complexity} (a_complexity
    # is always 1, the monic leading term). build_state_update_matrix
    # expects coeffs_vector[i] to be the tap weight on the i-th *oldest*
    # retained sample (index 0 = oldest), which is -a_{complexity-i} mod
    # gf_order -- i.e. drop a_0 (the constant term), negate the rest, and
    # reverse their order.
    coeffs_int = [
        (-int(a)) % gf_order for a in reversed(full_coeffs[1:complexity + 1])
    ]

    return coeffs_int, complexity

