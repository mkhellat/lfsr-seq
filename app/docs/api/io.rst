I/O Module
==========

The I/O module provides functions for reading and validating CSV files containing LFSR coefficient vectors, with security features like path sanitization and file size limits.

.. automodule:: lfsr.io
   :members:
   :undoc-members:
   :show-inheritance: False
   :imported-members: False

Functions
---------

.. autofunction:: lfsr.io.sanitize_file_path
   :no-index:

Sanitizes file paths to prevent directory traversal attacks.

.. autofunction:: lfsr.io.validate_csv_file
   :no-index:

Validates that a CSV file exists, is readable, and meets size constraints.

.. autofunction:: lfsr.io.read_and_validate_csv
   :no-index:

Reads and validates CSV file containing coefficient vectors, with comprehensive validation.

.. autofunction:: lfsr.io.read_csv_coefficients
   :no-index:

Simple CSV reader without validation (for internal use).

Example
~~~~~~~

.. code-block:: python

   from lfsr.io import read_and_validate_csv
   
   # Read and validate CSV file
   coeffs_list = read_and_validate_csv("coefficients.csv", 2)
   
   # Process each coefficient vector
   for i, coeffs in enumerate(coeffs_list, 1):
       print(f"LFSR {i}: {coeffs}")
