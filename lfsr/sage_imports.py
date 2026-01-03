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
from sage.rings.finite_rings.finite_field_constructor import GF
from sage.rings.finite_rings.finite_field_base import FiniteField

# Polynomials
from sage.rings.polynomial.polynomial_ring_constructor import PolynomialRing

# Vectors and matrices
from sage.modules.free_module_element import vector
from sage.modules.free_module import VectorSpace
from sage.matrix.matrix_space import MatrixSpace
# Matrix is created via MatrixSpace, not directly imported

# Symbolic ring
from sage.symbolic.ring import SR

# Number rings (commonly used in examples and type hints)
# These are typically imported from sage.rings.all
from sage.rings.all import ZZ, QQ, RR, CC

# Integers and rationals
from sage.rings.integer import Integer
from sage.rings.rational import Rational

# Arithmetic functions
from sage.arith.misc import is_prime, gcd, primes
from sage.arith.functions import lcm
from sage.arith.misc import factor
from sage.functions.other import sqrt

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
]

