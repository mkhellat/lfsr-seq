Field Module
=============

The field module provides validation functions for finite field orders and coefficient vectors.

.. automodule:: lfsr.field
   :members:
   :undoc-members:
   :show-inheritance: False
   :imported-members: False

Functions
---------

.. autofunction:: lfsr.field.validate_gf_order
   :no-index:

Validates that a field order string represents a valid finite field order (prime or prime power).

.. autofunction:: lfsr.field.validate_coefficient
   :no-index:

Validates that a coefficient value is within the valid range for the given field order.

.. autofunction:: lfsr.field.validate_coefficient_vector
   :no-index:

Validates an entire coefficient vector, checking that all coefficients are valid for the field order.

Example
~~~~~~~

.. code-block:: python

   from lfsr.field import validate_gf_order, validate_coefficient_vector
   
   # Validate field order
   gf_order = validate_gf_order("2")  # Returns 2
   gf_order = validate_gf_order("4")  # Returns 4 (GF(2^2))
   
   # Validate coefficient vector
   coeffs = ["1", "1", "0", "1"]
   validate_coefficient_vector(coeffs, 2, 1)  # Validates for GF(2)
