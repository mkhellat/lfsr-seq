#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Core LFSR mathematics and state update operations.

This module provides functions for building state update matrices and
computing matrix orders.
"""

from typing import List, Any, Optional, TextIO, Tuple
from sage.all import *


def build_state_update_matrix(
    coeffs_vector: List[int], gf_order: int
) -> Tuple[Any, Any]:
    """
    Build the LFSR state update matrix from coefficient vector.

    The state update matrix C follows the convention: S_i * C = S_i+1
    where S_i is the current state vector and S_i+1 is the next state.

    Args:
        coeffs_vector: List of coefficients (as integers) for the LFSR
        gf_order: The field order

    Returns:
        Tuple of (C, CS) where:
        - C: State update matrix over GF(gf_order)
        - CS: Symbolic state update matrix over SR (for characteristic polynomial)
    """
    d = len(coeffs_vector)
    M = MatrixSpace(GF(gf_order), d, d)
    I = M.identity_matrix()
    C = M.matrix()
    MS = MatrixSpace(SR, d)
    CS = MS.matrix()

    for i in range(d):
        row = []
        if i > 0:
            row = [0 for k in range(i - 1)]
            row.append(1)
        for j in range(d - 1 - i):
            row.append(0)
        row.append(coeffs_vector[i])
        C[i] = row
        CS[i] = row

    return C, CS


def compute_matrix_order(
    state_update_matrix: Any,
    identity_matrix: Any,
    state_vector_space_size: int,
    output_file: Optional[TextIO] = None,
) -> Optional[int]:
    """
    Compute the order of the state update matrix.

    The order of matrix C is the smallest positive integer n such that C^n = I,
    where I is the identity matrix.

    Args:
        state_update_matrix: The state update matrix C
        identity_matrix: The identity matrix I
        state_vector_space_size: Size of the state vector space (gf_order^d)
        output_file: Optional file object for output

    Returns:
        The order of the matrix, or None if not found within the search space
    """
    from lfsr.formatter import subsection, dump

    CE = identity_matrix * state_update_matrix
    for j in range(state_vector_space_size - 1):
        if CE == identity_matrix:
            subsection(
                "STATE UPDATE MATRIX ORDER",
                "exponent of the state update "
                + "matrix analogous to the "
                + "IDENTITY matrix :",
                output_file,
            )
            order = j + 1
            dump("  ** O(C) = " + str(order) + " **", "mode=all", output_file)
            return order
        else:
            CE = CE * state_update_matrix

    return None
