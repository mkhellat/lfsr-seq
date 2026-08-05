#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SageMath imports helper module.

This module provides a curated set of SageMath imports, avoiding deprecated
items that cause warnings. Instead of using `from sage.all import *`, modules
should use `from lfsr.sage_imports import *` to get only the needed imports
without deprecated warnings.
"""

# Import commonly used SageMath functions and classes from their specific modules
# This avoids importing deprecated items that are included in sage.all

# Finite fields
from sage.all import var
from sage.arith.functions import lcm

# Arithmetic functions
from sage.arith.misc import factor, gcd, is_prime, primes
from sage.functions.other import sqrt
from sage.matrix.constructor import matrix
from sage.matrix.matrix_space import MatrixSpace

# Functional helpers
from sage.misc.functional import basis, det
from sage.modules.free_module import VectorSpace

# Vectors and matrices
from sage.modules.free_module_element import vector

# Number rings (commonly used in examples and type hints)
# These are typically imported from sage.rings.all
from sage.rings.all import CC, QQ, RR, ZZ
from sage.rings.finite_rings.finite_field_base import FiniteField
from sage.rings.finite_rings.finite_field_constructor import GF

# Integers and rationals
from sage.rings.integer import Integer

# Polynomials
from sage.rings.polynomial.polynomial_ring_constructor import PolynomialRing
from sage.rings.rational import Rational

# Symbolic ring
from sage.symbolic.ring import SR

# Re-export everything for compatibility with `from lfsr.sage_imports import *`
__all__ = [
    'GF',
    'FiniteField',
    'PolynomialRing',
    'vector',
    'VectorSpace',
    'MatrixSpace',
    'SR',
    'ZZ',
    'QQ',
    'RR',
    'CC',
    'Integer',
    'Rational',
    'is_prime',
    'gcd',
    'lcm',
    'factor',
    'primes',
    'sqrt',
    'basis',
    'det',
    'matrix',
    'var',
]

