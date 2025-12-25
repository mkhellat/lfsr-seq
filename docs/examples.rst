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

   # Analyze LFSR
   with open("output.txt", "w") as f:
       main("coefficients.csv", "2", output_file=f)

   # Synthesize LFSR from sequence
   sequence = [1, 0, 1, 1, 0, 1, 0, 0, 1]
   poly, complexity = berlekamp_massey(sequence, 2)
   print(f"Linear complexity: {complexity}")

   # Statistical analysis
   stats = statistical_summary(sequence, 2)
   print(stats)

