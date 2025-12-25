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
