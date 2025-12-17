#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Polynomial operations for LFSR analysis.

This module provides functions for computing characteristic polynomials
and their orders over finite fields.
"""

import textwrap
from typing import Any

from sage.all import *

from lfsr.constants import FACTOR_DISPLAY_WIDTH, POLYNOMIAL_DISPLAY_WIDTH


def polynomial_order(polynomial: Any, state_vector_dim: int, gf_order: int) -> Any:
    """
    Find the order of a polynomial over the field GF(gf_order).

    The order of a polynomial P(t) is the smallest positive integer n
    such that t^n ≡ 1 (mod P(t)).

    Args:
        polynomial: The polynomial over GF(gf_order)
        state_vector_dim: Dimension of the state vector
        gf_order: The field order

    Returns:
        The order of the polynomial (or infinity if not found)
    """
    polynomial_degree = polynomial.degree()
    state_vector_space_size = int(gf_order) ** state_vector_dim
    bi = polynomial_degree
    ei = state_vector_space_size
    for j in range(bi, ei):
        dividend = PolynomialRing(GF(gf_order), "t")(t**j)
        divisor = polynomial
        q, r = dividend.quo_rem(divisor)
        if r == 1:
            poly_order = j
            break
        elif j == state_vector_space_size:
            poly_order = oo
    return poly_order


def characteristic_polynomial(
    state_update_matrix_symbolic: Any, gf_order: int, output_file: Any = None
) -> Any:
    """
    Compute and display the characteristic polynomial of the state update matrix.

    The characteristic polynomial P(t) = det(tI - C) where C is the state update
    matrix. The order of P is equal to the order of C, and the orders of the
    factors of P (not necessarily prime factors) can be found in the sequence table.

    Args:
        state_update_matrix_symbolic: Symbolic state update matrix
        gf_order: The field order
        output_file: Optional file object for output (for formatter functions)

    Returns:
        The characteristic polynomial over GF(gf_order)
    """
    from lfsr.formatter import dump, subsection

    subsec_name = "CHARACTERISTIC POLYNOMIAL"
    subsec_desc = (
        "find char poly of the state update matrix C : "
        + "P = det(xI - C); order of P is equal to the  "
        + "order of C, and the orders of the factors of "
        + "P, not necessarily prime factors of the order "
        + "of C, could be found in the sequence table."
    )
    subsection(subsec_name, subsec_desc, output_file)

    d = state_update_matrix_symbolic.dimensions()[0]
    xI = matrix(SR, d, d, var("t"))
    A = state_update_matrix_symbolic
    ACM = xI - A
    dump(str(ACM), "mode=all", output_file)
    A_char_poly = det(ACM)
    A_char_poly_gf = PolynomialRing(GF(gf_order), "t")(A_char_poly)
    A_char_poly_l = textwrap.wrap(str(A_char_poly_gf), width=POLYNOMIAL_DISPLAY_WIDTH)
    A_char_ord_i = polynomial_order(A_char_poly_gf, d, gf_order)
    A_char_ord_s = str(A_char_ord_i)
    l1 = 13 - len(A_char_ord_s)
    t_border_1 = " " + "\u250e" + "\u2504" * 40 + "\u2530"
    t_border_2 = "\u2504" * 18 + "\u2512"
    t_border = t_border_1 + t_border_2
    dump(t_border, "mode=all", output_file)
    for term in A_char_poly_l:
        m_border_l = " " + "\u254e" + " "
        m_border_r_1 = " " * (POLYNOMIAL_DISPLAY_WIDTH - len(term) + 1) + "\u254e"
        if len(term) >= POLYNOMIAL_DISPLAY_WIDTH - 2:
            m_border_r_2 = " " * 18 + "\u254e"
        else:
            m_border_r_2 = " O : " + A_char_ord_s + " " * l1 + "\u254e"
        m_border = m_border_l + term + m_border_r_1 + m_border_r_2
        dump(m_border, "mode=all", output_file)
    b_border_1 = " " + "\u2516" + "\u2504" * 40 + "\u2538"
    b_border_2 = "\u2504" * 18 + "\u251a"
    b_border = b_border_1 + b_border_2
    dump(b_border, "mode=all", output_file)

    # Factoring char poly, determining orders of the factors
    f = factor(A_char_poly_gf)
    i = 0
    l1 = len(str(len(list(f))))
    l2 = len(A_char_ord_s)
    for item in list(f):
        i += 1
        prime_poly = item[0]
        prime_poly_power = item[1]
        factor_order = polynomial_order(prime_poly, d, gf_order)
        s1 = l1 - len(str(i))
        t_1 = "   factor " + " " * s1 + str(i) + " | "
        s2 = l2 - len(str(factor_order))
        t_2 = "O : " + " " * s2 + str(factor_order) + " | "
        i_i = t_1 + t_2
        s_i = " " * (len(i_i) + 1)
        t_p = textwrap.wrap(
            "(" + str(prime_poly) + ")^" + str(prime_poly_power),
            width=FACTOR_DISPLAY_WIDTH,
            initial_indent=i_i,
            subsequent_indent=s_i,
        )
        for t in t_p:
            dump(t, "mode=all", output_file)

    return A_char_poly_gf
