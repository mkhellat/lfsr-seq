Polynomial Module
==================

The polynomial module provides functions for working with characteristic polynomials, computing polynomial orders, and analyzing polynomial properties.

.. automodule:: lfsr.polynomial
   :members:
   :undoc-members:
   :show-inheritance: False
   :imported-members: False

Functions
---------

.. autofunction:: lfsr.polynomial.characteristic_polynomial
   :no-index:

Computes the characteristic polynomial of the state update matrix using the determinant of (xI - C).

.. autofunction:: lfsr.polynomial.polynomial_order
   :no-index:

Computes the order of a polynomial over a finite field, which is the smallest positive integer n such that the polynomial divides x^n - 1.

.. autofunction:: lfsr.polynomial.is_primitive_polynomial
   :no-index:

Checks if a polynomial is primitive over a finite field. A primitive polynomial of degree d over GF(q) is irreducible and has order q^d - 1, which yields LFSRs with maximum period.

.. autofunction:: lfsr.polynomial.compute_period_via_factorization
   :no-index:

Compute LFSR period using polynomial factorization instead of enumeration. More efficient for large LFSRs (degree > 15). Factors the characteristic polynomial and computes the LCM of irreducible factor orders.

.. autofunction:: lfsr.polynomial.detect_mathematical_shortcuts
   :no-index:

Detect special cases and recommend optimized algorithms. Identifies primitive polynomials, irreducible polynomials, small degree cases, and known patterns (trinomials, pentanomials).

Example
~~~~~~~

.. code-block:: python

   from sage.all import *
   from lfsr.core import build_state_update_matrix
   from lfsr.polynomial import characteristic_polynomial, polynomial_order
   
   # Build state update matrix
   coeffs = [1, 1, 0, 1]
   C, CS = build_state_update_matrix(coeffs, 2)
   
   # Compute characteristic polynomial
   char_poly = characteristic_polynomial(CS, 2)
   print(f"Characteristic polynomial: {char_poly}")
   
   # Compute polynomial order
   order = polynomial_order(char_poly, len(coeffs), 2)
   print(f"Polynomial order: {order}")
   
   # Check if polynomial is primitive
   from lfsr.polynomial import is_primitive_polynomial
   is_prim = is_primitive_polynomial(char_poly, 2)
   print(f"Is primitive: {is_prim}")
   
   # Period computation via factorization (optimization)
   from lfsr.polynomial import compute_period_via_factorization
   period = compute_period_via_factorization(coeffs, 2)
   print(f"Period (via factorization): {period}")
   
   # Detect mathematical shortcuts
   from lfsr.polynomial import detect_mathematical_shortcuts
   shortcuts = detect_mathematical_shortcuts(coeffs, 2)
   print(f"Primitive: {shortcuts['is_primitive']}")
   print(f"Recommended method: {shortcuts['recommended_method']}")
