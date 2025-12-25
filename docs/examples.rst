Examples
========

Basic LFSR Analysis
-------------------

Analyze a simple 4-bit LFSR over GF(2):

.. code-block:: bash

   echo "1,1,0,1" > test.csv
   lfsr-seq test.csv 2

This will generate ``test.csv.out`` with:
- State update matrix
- All state sequences and their periods
- Characteristic polynomial and its order

Multiple LFSR Configurations
----------------------------

Analyze multiple LFSR configurations:

.. code-block:: bash

   cat > lfsrs.csv << EOF
   1,1,0,1
   1,0,1,1
   1,1,1,0,1
   EOF
   lfsr-seq lfsrs.csv 2

Each row will be analyzed separately.

Non-Binary Fields
-----------------

Analyze LFSR over GF(3):

.. code-block:: bash

   echo "1,2,1" > gf3.csv
   lfsr-seq gf3.csv 3

Export to JSON
~~~~~~~~~~~~~~

Export results in JSON format:

.. code-block:: bash

   lfsr-seq strange.csv 2 --format json --output results.json

The JSON file will contain structured data suitable for programmatic processing.

Python API Usage
----------------

Use the library programmatically:

.. code-block:: python

   from lfsr.cli import main
   from lfsr.synthesis import berlekamp_massey, linear_complexity
   from lfsr.statistics import statistical_summary
   from lfsr.core import build_state_update_matrix, compute_matrix_order
   from lfsr.polynomial import characteristic_polynomial, polynomial_order
   from lfsr.field import validate_gf_order, validate_coefficient_vector

   # Analyze LFSR from CSV file
   with open("output.txt", "w") as f:
       main("coefficients.csv", "2", output_file=f)

   # Synthesize LFSR from sequence using Berlekamp-Massey
   sequence = [1, 0, 1, 1, 0, 1, 0, 0, 1]
   poly, complexity = berlekamp_massey(sequence, 2)
   print(f"Linear complexity: {complexity}")

   # Calculate linear complexity directly
   complexity = linear_complexity(sequence, 2)
   print(f"Linear complexity: {complexity}")

   # Statistical analysis
   stats = statistical_summary(sequence, 2)
   print(f"Frequency ratio: {stats['frequency']['ratio']}")
   print(f"Total runs: {stats['runs']['total_runs']}")

   # Build state update matrix
   coeffs = [1, 1, 0, 1]
   C, CS = build_state_update_matrix(coeffs, 2)
   order = compute_matrix_order(C, CS)
   print(f"Matrix order (period): {order}")

   # Characteristic polynomial
   char_poly = characteristic_polynomial(coeffs, 2)
   poly_order = polynomial_order(char_poly, 2)
   print(f"Polynomial order: {poly_order}")

   # Field validation
   gf_order = validate_gf_order("4")  # Returns 4
   validate_coefficient_vector([1, 2, 3], 4)  # Validates coefficients for GF(4)

