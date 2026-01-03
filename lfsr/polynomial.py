#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Polynomial operations for LFSR analysis.

This module provides functions for computing characteristic polynomials
and their orders over finite fields.
"""

import textwrap
from typing import Any, Optional, TextIO, Union

from lfsr.sage_imports import *

from lfsr.constants import FACTOR_DISPLAY_WIDTH, POLYNOMIAL_DISPLAY_WIDTH
import math
from typing import List, Optional, Tuple, Dict, Any


def polynomial_order(
    polynomial: Any, state_vector_dim: int, gf_order: int
) -> Union[int, Any]:  # Returns int or oo (infinity) from SageMath
    """
    Find the order of a polynomial over the field GF(gf_order).

    The order of a polynomial P(t) is the smallest positive integer n
    such that t^n ≡ 1 (mod P(t)).

    This function uses an optimization: if the polynomial is primitive,
    the order is immediately known to be q^d - 1 without computation.

    Args:
        polynomial: The polynomial over GF(gf_order)
        state_vector_dim: Dimension of the state vector
        gf_order: The field order

    Returns:
        The order of the polynomial (or infinity if not found)
    """
    polynomial_degree = polynomial.degree()
    
    # Optimization: If polynomial is primitive, order is q^d - 1
    # This avoids expensive computation for primitive polynomials
    if polynomial_degree == state_vector_dim:
        try:
            if is_primitive_polynomial(polynomial, gf_order):
                max_order = int(gf_order) ** polynomial_degree - 1
                return max_order
        except (TypeError, ValueError, AttributeError):
            # If primitive check fails, continue with normal computation
            pass
    
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


def is_primitive_polynomial(
    polynomial: Any, gf_order: int
) -> bool:
    """
    Check if a polynomial is primitive over GF(gf_order).

    A polynomial P(t) of degree d over GF(q) is primitive if:
    1. P(t) is irreducible
    2. The order of P(t) is q^d - 1

    Primitive polynomials are important because they generate LFSRs with
    maximum period q^d - 1, which is optimal for cryptographic applications.

    Args:
        polynomial: The polynomial over GF(gf_order) to check
        gf_order: The field order

    Returns:
        True if the polynomial is primitive, False otherwise

    Example:
        >>> from lfsr.sage_imports import *
        >>> F = GF(2)
        >>> R = PolynomialRing(F, "t")
        >>> p = R("t^4 + t + 1")
        >>> is_primitive_polynomial(p, 2)
        True

    Note:
        This function uses SageMath's built-in is_primitive() method if available,
        otherwise falls back to checking irreducibility and order manually.
    """
    # Get polynomial degree
    degree = polynomial.degree()
    if degree <= 0:
        return False

    # Maximum order for a primitive polynomial of degree d over GF(q)
    max_order = int(gf_order) ** degree - 1

    # Try using SageMath's built-in is_primitive() method first
    # This is the most efficient approach
    try:
        if hasattr(polynomial, 'is_primitive'):
            result = polynomial.is_primitive()
            if result is not None:
                return bool(result)
    except (AttributeError, NotImplementedError, TypeError, ValueError):
        pass

    # Fallback: Check manually
    # Step 1: Must be irreducible
    try:
        if not polynomial.is_irreducible():
            return False
    except (AttributeError, NotImplementedError, TypeError, ValueError):
        # If we can't check irreducibility, we can't determine primitivity
        return False

    # Step 2: Order must be q^d - 1
    # Use our existing polynomial_order function
    poly_order = polynomial_order(polynomial, degree, gf_order)
    
    # Check if order equals maximum (q^d - 1)
    # Handle both integer and SageMath infinity cases
    if poly_order == oo:
        return False
    
    try:
        return int(poly_order) == max_order
    except (TypeError, ValueError):
        return False


def characteristic_polynomial(
    state_update_matrix_symbolic: Any,
    gf_order: int,
    output_file: Optional[TextIO] = None,
) -> Any:  # Returns polynomial from SageMath
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
    
    # Check if polynomial is primitive
    is_primitive = is_primitive_polynomial(A_char_poly_gf, gf_order)
    primitive_indicator = " [PRIMITIVE]" if is_primitive else ""
    
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
    
    # Add primitive polynomial indicator if applicable
    if is_primitive:
        primitive_line = " " + "\u254e" + " " * (POLYNOMIAL_DISPLAY_WIDTH + 1) + "\u254e" + primitive_indicator + " " * (18 - len(primitive_indicator)) + "\u254e"
        dump(primitive_line, "mode=all", output_file)
    
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


def compute_period_via_factorization(
    coefficients: List[int],
    field_order: int,
    state_vector_dim: Optional[int] = None
) -> Optional[int]:
    """
    Compute LFSR period using polynomial factorization.
    
    This method is more efficient than enumeration for large LFSRs. Instead
    of enumerating all states, it factors the characteristic polynomial and
    computes the period as the LCM of the orders of irreducible factors.
    
    **Mathematical Foundation**:
    
    If the characteristic polynomial factors as:
    
    P(t) = product_{i=1}^{k} f_i(t)^{e_i}
    
    where f_i(t) are irreducible factors, then the period is:
    
    period = lcm(ord(f_1(t)), ..., ord(f_k(t)))
    
    where ord(f_i(t)) is the order of the irreducible factor.
    
    **Key Terminology**:
    
    - **Polynomial Factorization**: Decomposing a polynomial into irreducible
      factors (factors that cannot be factored further over the field).
    
    - **Irreducible Factor**: A polynomial that cannot be factored into
      polynomials of lower degree over the given field.
    
    - **Order of a Polynomial**: The smallest positive integer n such that
      t^n ≡ 1 (mod P(t)) over the field.
    
    - **LCM (Least Common Multiple)**: The smallest positive integer that is
      divisible by all given integers. For example, LCM(4, 6) = 12.
    
    **Advantages**:
    
    - Much faster than enumeration for large LFSRs (degree > 15)
    - Works efficiently even when state space is huge
    - Provides theoretical insight into period structure
    
    **Limitations**:
    
    - Factorization can be expensive for very high-degree polynomials
    - May not be faster than enumeration for small degrees (< 10)
    - Requires polynomial factorization algorithms
    
    Args:
        coefficients: List of feedback polynomial coefficients [c_0, c_1, ..., c_{d-1}]
        field_order: The field order (q)
        state_vector_dim: Optional dimension (degree) of the LFSR. If None, inferred from coefficients.
    
    Returns:
        The period computed via factorization, or None if computation fails
    
    Example:
        >>> from lfsr.polynomial import compute_period_via_factorization
        >>> # LFSR with coefficients [1, 0, 0, 1] over GF(2)
        >>> period = compute_period_via_factorization([1, 0, 0, 1], 2)
        >>> print(f"Period: {period}")
        Period: 15
    
    Note:
        This function may return None if factorization fails or if the polynomial
        cannot be properly analyzed. In such cases, fall back to enumeration.
    """
    try:
        # Build characteristic polynomial from coefficients
        F = GF(field_order)
        R = PolynomialRing(F, "t")
        t = R.gen()
        
        # Characteristic polynomial: t^d + c_{d-1}*t^{d-1} + ... + c_1*t + c_0
        # Note: coefficients are in reverse order for SageMath
        if state_vector_dim is None:
            state_vector_dim = len(coefficients)
        
        d = state_vector_dim
        char_poly = t**d
        for i, coeff in enumerate(coefficients):
            char_poly += F(coeff) * t**(d - 1 - i)
        
        # Factor the polynomial
        factors = factor(char_poly)
        
        # Compute orders of irreducible factors
        orders = []
        for factor_item in list(factors):
            irreducible_factor = factor_item[0]
            # Compute order of this irreducible factor
            factor_order = polynomial_order(irreducible_factor, d, field_order)
            
            # Skip if order is infinity or invalid
            if factor_order == oo:
                continue
            
            try:
                orders.append(int(factor_order))
            except (TypeError, ValueError):
                continue
        
        # If no valid orders found, return None
        if not orders:
            return None
        
        # Compute LCM of all orders
        if len(orders) == 1:
            period = orders[0]
        else:
            # Compute LCM: LCM(a, b) = |a * b| / GCD(a, b)
            period = orders[0]
            for order in orders[1:]:
                period = abs(period * order) // math.gcd(period, order)
        
        return period
    
    except (TypeError, ValueError, AttributeError, ArithmeticError) as e:
        # If anything fails, return None to indicate fallback needed
        return None


def detect_mathematical_shortcuts(
    coefficients: List[int],
    field_order: int,
    state_vector_dim: Optional[int] = None
) -> Dict[str, Any]:
    """
    Detect special cases and recommend optimized algorithms.
    
    This function analyzes the LFSR configuration to identify special cases
    that allow for optimized computation. It returns recommendations for
    which algorithms to use.
    
    **Key Terminology**:
    
    - **Mathematical Shortcut**: An optimized algorithm for a special case
      that avoids expensive general-purpose computation.
    
    - **Primitive Polynomial Shortcut**: When a polynomial is primitive, the
      period is immediately known to be q^d - 1 without any computation.
    
    - **Irreducible Polynomial Shortcut**: When a polynomial is irreducible
      (but not necessarily primitive), factorization-based period computation
      is particularly efficient.
    
    - **Small Degree Shortcut**: For very small degrees, enumeration may be
      faster than factorization due to overhead.
    
    - **Pattern Recognition**: Detecting known polynomial patterns that have
      known properties (e.g., trinomials, pentanomials).
    
    **Special Cases Detected**:
    
    1. **Primitive Polynomials**: Period = q^d - 1 (maximum period)
    2. **Irreducible Polynomials**: Can use factorization directly
    3. **Small Degrees**: Enumeration may be faster
    4. **Known Patterns**: Polynomials matching known patterns
    
    Args:
        coefficients: List of feedback polynomial coefficients
        field_order: The field order (q)
        state_vector_dim: Optional dimension (degree) of the LFSR
    
    Returns:
        Dictionary with detected shortcuts and recommendations:
        - 'is_primitive': bool - Whether polynomial is primitive
        - 'is_irreducible': bool - Whether polynomial is irreducible
        - 'recommended_method': str - Recommended computation method
        - 'expected_period': Optional[int] - Expected period if known
        - 'shortcuts_available': List[str] - List of available shortcuts
        - 'complexity_estimate': str - Estimated computational complexity
    
    Example:
        >>> from lfsr.polynomial import detect_mathematical_shortcuts
        >>> shortcuts = detect_mathematical_shortcuts([1, 0, 0, 1], 2)
        >>> print(f"Primitive: {shortcuts['is_primitive']}")
        >>> print(f"Recommended: {shortcuts['recommended_method']}")
    """
    if state_vector_dim is None:
        state_vector_dim = len(coefficients)
    
    d = state_vector_dim
    shortcuts_available = []
    recommended_method = "enumeration"  # Default
    expected_period = None
    complexity_estimate = "O(q^d)"  # Default worst case
    
    try:
        # Build characteristic polynomial
        F = GF(field_order)
        R = PolynomialRing(F, "t")
        t = R.gen()
        
        char_poly = t**d
        for i, coeff in enumerate(coefficients):
            char_poly += F(coeff) * t**(d - 1 - i)
        
        # Check if primitive
        is_primitive = False
        try:
            is_primitive = is_primitive_polynomial(char_poly, field_order)
            if is_primitive:
                shortcuts_available.append("primitive_polynomial")
                recommended_method = "primitive_shortcut"
                expected_period = int(field_order) ** d - 1
                complexity_estimate = "O(1)"
        except (TypeError, ValueError, AttributeError):
            pass
        
        # Check if irreducible (but not primitive)
        is_irreducible = False
        if not is_primitive:
            try:
                is_irreducible = char_poly.is_irreducible()
                if is_irreducible:
                    shortcuts_available.append("irreducible_polynomial")
                    if recommended_method == "enumeration":
                        recommended_method = "factorization"
                        complexity_estimate = "O(d^3)"  # Factorization complexity
            except (AttributeError, NotImplementedError, TypeError, ValueError):
                pass
        
        # Check degree for small degree shortcut
        if d <= 10 and field_order == 2:
            shortcuts_available.append("small_degree")
            if recommended_method == "enumeration":
                complexity_estimate = "O(2^d)"  # But small constant factor
        
        # Check for known patterns (trinomials, pentanomials)
        non_zero_count = sum(1 for c in coefficients if c != 0)
        if non_zero_count == 3:  # Trinomial
            shortcuts_available.append("trinomial_pattern")
        elif non_zero_count == 5:  # Pentanomial
            shortcuts_available.append("pentanomial_pattern")
        
        # Recommend factorization for larger degrees
        if d > 15 and not is_primitive:
            if recommended_method == "enumeration":
                recommended_method = "factorization"
                complexity_estimate = "O(d^3) + O(q^d)"  # Factorization + order computation
    
    except (TypeError, ValueError, AttributeError):
        # If analysis fails, return defaults
        pass
    
    return {
        'is_primitive': is_primitive,
        'is_irreducible': is_irreducible,
        'recommended_method': recommended_method,
        'expected_period': expected_period,
        'shortcuts_available': shortcuts_available,
        'complexity_estimate': complexity_estimate
    }
