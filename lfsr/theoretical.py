#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Theoretical analysis functions for LFSR sequences.

This module provides comprehensive theoretical analysis capabilities, including
irreducible polynomial analysis, theoretical comparisons, and research-oriented
features.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
import math

from lfsr.sage_imports import *


@dataclass
class IrreduciblePolynomialAnalysis:
    """
    Results from irreducible polynomial analysis.
    
    This class contains comprehensive analysis results for irreducible
    polynomials, including factorization, factor orders, and theoretical
    properties.
    
    Attributes:
        polynomial: The polynomial being analyzed
        is_irreducible: Whether the polynomial is irreducible
        factors: List of irreducible factors with multiplicities
        factor_orders: Orders of each irreducible factor
        polynomial_order: Order of the full polynomial
        lcm_of_orders: LCM of factor orders (should equal polynomial order)
        has_primitive_factors: Whether any factors are primitive
        primitive_factors: List of primitive factors
        degree_distribution: Distribution of factor degrees
        theoretical_period: Theoretical maximum period
    """
    polynomial: Any
    is_irreducible: bool
    factors: List[Tuple[Any, int]] = field(default_factory=list)
    factor_orders: List[int] = field(default_factory=list)
    polynomial_order: Optional[int] = None
    lcm_of_orders: Optional[int] = None
    has_primitive_factors: bool = False
    primitive_factors: List[Any] = field(default_factory=list)
    degree_distribution: Dict[int, int] = field(default_factory=dict)
    theoretical_period: Optional[int] = None
    field_order: int = 2
    polynomial_degree: int = 0


def analyze_irreducible_properties(
    polynomial: Any,
    field_order: int,
    state_vector_dim: Optional[int] = None
) -> IrreduciblePolynomialAnalysis:
    """
    Perform comprehensive analysis of irreducible polynomial properties.
    
    This function analyzes a polynomial to determine:
    - Whether it is irreducible
    - Its factorization into irreducible factors
    - Orders of each factor
    - Relationship between factor orders and polynomial order
    - Primitive factor detection
    - Degree distribution of factors
    
    **Key Terminology**:
    
    - **Irreducible Polynomial**: A polynomial that cannot be factored into
      polynomials of lower degree over the given field. For example, over GF(2),
      t^2 + t + 1 is irreducible, but t^2 + 1 = (t+1)^2 is not.
    
    - **Polynomial Factorization**: Decomposing a polynomial into irreducible
      factors. For example, t^4 + t^3 + t + 1 = (t+1)(t^3 + t + 1) over GF(2).
    
    - **Factor Order**: The order of an irreducible factor f(t) is the smallest
      positive integer n such that t^n ≡ 1 (mod f(t)). This determines the
      period contribution of that factor.
    
    - **Polynomial Order**: The order of the full polynomial P(t) is the smallest
      positive integer n such that t^n ≡ 1 (mod P(t)). For a polynomial with
      factors f_i(t), the order is LCM(ord(f_1), ..., ord(f_k)).
    
    - **Primitive Factor**: An irreducible factor whose order equals q^d - 1,
      where d is the degree of the factor and q is the field order. Primitive
      factors generate maximum-period sequences.
    
    - **LCM (Least Common Multiple)**: The smallest positive integer divisible
      by all given integers. For example, LCM(3, 4) = 12.
    
    **Mathematical Foundation**:
    
    For a polynomial P(t) over GF(q) that factors as:
    
    P(t) = product_{i=1}^{k} f_i(t)^{e_i}
    
    where f_i(t) are irreducible factors, the order of P(t) is:
    
    ord(P(t)) = lcm(ord(f_1(t)), ..., ord(f_k(t)))
    
    This relationship is fundamental to understanding LFSR period structure.
    
    Args:
        polynomial: The polynomial to analyze (SageMath polynomial)
        field_order: The field order (q)
        state_vector_dim: Optional state vector dimension (defaults to polynomial degree)
    
    Returns:
        IrreduciblePolynomialAnalysis with comprehensive results
    
    Example:
        >>> from sage.all import *
        >>> F = GF(2)
        >>> R = PolynomialRing(F, "t")
        >>> p = R("t^4 + t^3 + t + 1")
        >>> analysis = analyze_irreducible_properties(p, 2)
        >>> print(f"Is irreducible: {analysis.is_irreducible}")
        >>> print(f"Number of factors: {len(analysis.factors)}")
    """
    degree = polynomial.degree()
    if state_vector_dim is None:
        state_vector_dim = degree
    
    # Check irreducibility
    is_irreducible = polynomial.is_irreducible()
    
    # Factor the polynomial
    factors_list = []
    factor_orders_list = []
    primitive_factors_list = []
    degree_dist = {}
    
    if is_irreducible:
        # Single irreducible factor
        factor_order = polynomial_order(polynomial, state_vector_dim, field_order)
        factors_list = [(polynomial, 1)]
        factor_orders_list = [int(factor_order) if factor_order != oo else None]
        
        # Check if primitive
        max_order = int(field_order) ** degree - 1
        if factor_order == max_order:
            primitive_factors_list = [polynomial]
        
        degree_dist[degree] = 1
    else:
        # Factor into irreducible factors
        factorization = factor(polynomial)
        
        for factor_item in list(factorization):
            factor_poly = factor_item[0]
            multiplicity = factor_item[1]
            factor_deg = factor_poly.degree()
            
            factors_list.append((factor_poly, multiplicity))
            
            # Compute order of this factor
            factor_order = _polynomial_order_helper(factor_poly, factor_deg, field_order)
            if factor_order != oo:
                factor_orders_list.append(int(factor_order))
            else:
                factor_orders_list.append(None)
            
            # Check if primitive
            max_order = int(field_order) ** factor_deg - 1
            if factor_order == max_order:
                primitive_factors_list.append(factor_poly)
            
            # Track degree distribution
            degree_dist[factor_deg] = degree_dist.get(factor_deg, 0) + multiplicity
    
    # Compute polynomial order
    poly_order = _polynomial_order_helper(polynomial, state_vector_dim, field_order)
    poly_order_int = int(poly_order) if poly_order != oo else None
    
    # Compute LCM of factor orders
    valid_orders = [o for o in factor_orders_list if o is not None]
    if valid_orders:
        if len(valid_orders) > 1:
            lcm_orders = math.lcm(*valid_orders)
        else:
            lcm_orders = valid_orders[0]
    else:
        lcm_orders = None
    
    # Theoretical maximum period
    theoretical_period = int(field_order) ** state_vector_dim - 1
    
    return IrreduciblePolynomialAnalysis(
        polynomial=polynomial,
        is_irreducible=is_irreducible,
        factors=factors_list,
        factor_orders=factor_orders_list,
        polynomial_order=poly_order_int,
        lcm_of_orders=lcm_orders,
        has_primitive_factors=len(primitive_factors_list) > 0,
        primitive_factors=primitive_factors_list,
        degree_distribution=degree_dist,
        theoretical_period=theoretical_period,
        field_order=field_order,
        polynomial_degree=degree
    )


def compare_with_theoretical_bounds(
    computed_period: int,
    theoretical_max_period: int,
    is_primitive: bool,
    polynomial_order: Optional[int] = None
) -> Dict[str, Any]:
    """
    Compare computed results with theoretical predictions.
    
    This function verifies that computed results match theoretical expectations,
    which is crucial for validating analysis correctness.
    
    **Key Terminology**:
    
    - **Theoretical Maximum Period**: The maximum possible period for an LFSR
      of degree d over GF(q), which is q^d - 1. This is achieved if and only
      if the characteristic polynomial is primitive.
    
    - **Primitive Polynomial**: A polynomial P(t) of degree d over GF(q) is
      primitive if it is irreducible and has order q^d - 1. Primitive polynomials
      generate LFSRs with maximum period.
    
    - **Period Verification**: Checking that the computed period matches the
      theoretical prediction based on polynomial properties.
    
    **Theoretical Predictions**:
    
    1. **Primitive Polynomials**: If P(t) is primitive, all non-zero states
       should have period q^d - 1.
    
    2. **Irreducible Polynomials**: If P(t) is irreducible (but not primitive),
       the period should equal the order of P(t), which divides q^d - 1.
    
    3. **Composite Polynomials**: If P(t) factors, the period should equal the
       LCM of the orders of irreducible factors.
    
    Args:
        computed_period: The period computed from analysis
        theoretical_max_period: The theoretical maximum period (q^d - 1)
        is_primitive: Whether the polynomial is primitive
        polynomial_order: Optional polynomial order (if known)
    
    Returns:
        Dictionary with comparison results and verification status
    """
    comparison = {
        'computed_period': computed_period,
        'theoretical_max_period': theoretical_max_period,
        'is_primitive': is_primitive,
        'period_equals_max': computed_period == theoretical_max_period,
        'period_ratio': computed_period / theoretical_max_period if theoretical_max_period > 0 else 0.0,
        'verification_status': 'unknown'
    }
    
    if is_primitive:
        # For primitive polynomials, period should equal q^d - 1
        if computed_period == theoretical_max_period:
            comparison['verification_status'] = 'verified'
            comparison['verification_message'] = 'Period matches theoretical maximum for primitive polynomial'
        else:
            comparison['verification_status'] = 'mismatch'
            comparison['verification_message'] = f'Period {computed_period} does not match expected {theoretical_max_period} for primitive polynomial'
    elif polynomial_order is not None:
        # For non-primitive polynomials, period should equal polynomial order
        if computed_period == polynomial_order:
            comparison['verification_status'] = 'verified'
            comparison['verification_message'] = 'Period matches polynomial order'
        else:
            comparison['verification_status'] = 'mismatch'
            comparison['verification_message'] = f'Period {computed_period} does not match polynomial order {polynomial_order}'
    else:
        # Cannot verify without polynomial order
        comparison['verification_status'] = 'unverified'
        comparison['verification_message'] = 'Cannot verify: polynomial order not provided'
    
    return comparison


def _polynomial_order_helper(
    polynomial: Any,
    state_vector_dim: int,
    gf_order: int
) -> Union[int, Any]:
    """
    Find the order of a polynomial over the field GF(gf_order).
    
    This is a helper function that uses the polynomial's parent ring
    to compute the order.
    
    Args:
        polynomial: The polynomial over GF(gf_order)
        state_vector_dim: Dimension of the state vector
        gf_order: The field order
    
    Returns:
        The order of the polynomial (or infinity if not found)
    """
    # Get the parent ring of the polynomial
    R = polynomial.parent()
    t = R.gen()
    
    state_vector_space_size = int(gf_order) ** state_vector_dim
    polynomial_degree = polynomial.degree()
    
    bi = polynomial_degree
    ei = state_vector_space_size
    
    for j in range(bi, ei):
        dividend = t**j
        q, r = dividend.quo_rem(polynomial)
        if r == 1:
            return j
        elif j == state_vector_space_size - 1:
            return oo
    
    return oo
