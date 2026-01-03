#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Core LFSR mathematics and state update operations.

This module provides functions for building state update matrices and
computing matrix orders.
"""

from typing import Any, List, Optional, TextIO, Tuple

from sage.all import *


def build_state_update_matrix(
    coeffs_vector: List[int], gf_order: int
) -> Tuple[Any, Any]:
    """Build the LFSR state update matrix from coefficient vector.

    The state update matrix C follows the convention: S_i * C = S_i+1
    where S_i is the current state vector and S_i+1 is the next state.

    The matrix is constructed as a companion matrix where:

    - The first d-1 rows form an identity-like structure with 1s on the
      subdiagonal
    - The last row contains the LFSR coefficients

    Args:
        coeffs_vector: List of coefficients (as integers) for the LFSR.
            The length determines the dimension of the state space.
        gf_order: The field order for the finite field GF(gf_order).

    Returns:
        Tuple of (C, CS) where:
        - C: State update matrix over GF(gf_order), used for state
          transitions
        - CS: Symbolic state update matrix over SR (SageMath symbolic
          ring), used for characteristic polynomial computation

    Example:
        >>> coeffs = [1, 1, 0, 1]
        >>> C, CS = build_state_update_matrix(coeffs, 2)
        >>> # C is a 4x4 matrix over GF(2)
    """
    d = len(coeffs_vector)
    M = MatrixSpace(GF(gf_order), d, d)
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
    where I is the identity matrix. This represents the period of the LFSR
    state transitions.

    The algorithm computes successive powers of C until C^n = I, or until
    the maximum possible order (state_vector_space_size - 1) is reached.

    Args:
        state_update_matrix: The state update matrix C over GF(gf_order)
        identity_matrix: The identity matrix I of the same dimension
        state_vector_space_size: Size of the state vector space
          (gf_order^d). This is the maximum possible order.
        output_file: Optional file object for formatted output.
            If provided, the order is written to the file.

    Returns:
        The order of the matrix (smallest n such that C^n = I), or None
        if the order is not found within the search space [1,
        state_vector_space_size-1].

    Note:
        The order is always at most state_vector_space_size - 1 by the
        pigeonhole principle. If None is returned, it indicates an error
        in the computation or an extremely large order.

    Example:
        >>> C = build_state_update_matrix([1, 1, 0, 1], 2)[0]
        >>> I = MatrixSpace(GF(2), 4, 4).identity_matrix()
        >>> order = compute_matrix_order(C, I, 16)
        >>> # Returns the period of the LFSR
    """
    from lfsr.formatter import dump, subsection

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
