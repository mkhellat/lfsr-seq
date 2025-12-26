User Guide
==========

Basic Usage
-----------

The basic command-line usage is:

.. code-block:: bash

   lfsr-seq <input_file> <gf_order> [options]

**Example:**
.. code-block:: bash

   lfsr-seq strange.csv 2

This will:
- Read LFSR coefficients from ``strange.csv``
- Analyze sequences over GF(2)
- Generate output in ``strange.csv.out``

Command-Line Options
--------------------

Positional Arguments:
   input_file                 CSV file containing LFSR coefficient vectors
   gf_order                   Galois field order (prime or prime power)

Optional Arguments:

   -h, --help                 Show help message and exit
   --version                  Show version and exit
   -o, --output FILE          Specify output file (default: input_file.out)
   -v, --verbose              Enable verbose output
   -q, --quiet                Enable quiet mode (suppress non-essential output)
   --no-progress              Disable progress bar display
   --format {text,json,csv,xml}
                              Output format (default: text)

Input Format
------------

The CSV file should contain one or more rows of LFSR coefficients.
Each row represents a different LFSR configuration:

.. code-block:: text

   1,1,1,0,0,0,0,0,1,1
   1,1,1,0,0,0,0,0,1,1,0,1,1,1,0
   1,1,1,0,0,0,0,0,1,1,0,1,1,1,1

Each coefficient should be in the range [0, GF_order-1].

Output Formats
--------------

The tool supports multiple output formats for different use cases:

Text Format (Default)
~~~~~~~~~~~~~~~~~~~~~

Human-readable text output with formatted tables and sections. This is the default format
and provides the most readable output for manual inspection.

JSON Format
~~~~~~~~~~~

Structured JSON output suitable for programmatic processing:

.. code-block:: bash

   lfsr-seq strange.csv 2 --format json --output results.json

The JSON format includes:
- Metadata (timestamp, GF order, coefficients, LFSR degree)
- Characteristic polynomial and its order
- All state sequences with their periods
- Statistical analysis results

CSV Format
~~~~~~~~~~

Tabular CSV output suitable for spreadsheet applications:

.. code-block:: bash

   lfsr-seq strange.csv 2 --format csv --output results.csv

XML Format
~~~~~~~~~~

Structured XML output for XML-based workflows:

.. code-block:: bash

   lfsr-seq strange.csv 2 --format xml --output results.xml

Output Contents
---------------

The tool generates comprehensive output including:

* **State Update Matrix**: The companion matrix representing LFSR state transitions
* **Matrix Order**: The period of state transitions (order of the matrix)
* **State Sequences**: All possible state sequences with their periods
* **Characteristic Polynomial**: The characteristic polynomial of the LFSR
* **Polynomial Order**: The order of the characteristic polynomial
* **Polynomial Factorization**: Factorization of the characteristic polynomial with factor orders
* **Sequence Analysis**: Detailed analysis of each state sequence

Output is written to both:
* **Console**: Summary information (unless ``--quiet`` is used)
* **Output File**: Complete detailed analysis

Security Features
-----------------

The tool includes several security features:

* **Path Traversal Protection**: Prevents access to files outside the intended directory
* **File Size Limits**: Maximum file size of 10 MB
* **Row Limits**: Maximum of 10,000 CSV rows per file
* **Input Validation**: Comprehensive validation of field orders and coefficients
* **Sanitization**: Input sanitization to prevent injection attacks

These limits can be adjusted in ``lfsr/constants.py`` if needed for specific use cases.

Performance Features
--------------------

The tool implements several performance optimizations:

* **Cycle Detection**: Floyd's (tortoise-and-hare) algorithm is implemented but currently disabled
  * **Current Method**: Enumeration (works correctly, used until Floyd's algorithm bug is fixed)
  * **Future**: Floyd's algorithm will provide O(1) space vs O(period) for enumeration
  * **Scalability**: Once enabled, will support analysis of LFSRs with very large periods (>10^6 states)
* **Optimized State Tracking**: Set-based visited state tracking for O(1) membership testing
* **Efficient Algorithms**: Mathematical optimizations for period computation and sequence analysis

For detailed mathematical background on cycle detection algorithms, see the :doc:`mathematical_background` section.

Examples
--------

Basic Analysis
~~~~~~~~~~~~~~

Analyze LFSR over GF(2):

.. code-block:: bash

   lfsr-seq coefficients.csv 2

This will:
- Read LFSR coefficients from ``coefficients.csv``
- Analyze sequences over GF(2)
- Generate output in ``coefficients.csv.out``

Verbose Output
~~~~~~~~~~~~~~

Show detailed information about processing:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --verbose

Quiet Mode
~~~~~~~~~~

Suppress non-essential output (no progress bar):

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --quiet

Custom Output File
~~~~~~~~~~~~~~~~~~

Specify a custom output file:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --output my_results.txt

JSON Export
~~~~~~~~~~~

Export results in JSON format:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --format json --output results.json

CSV Export
~~~~~~~~~~

Export results in CSV format:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --format csv --output results.csv

XML Export
~~~~~~~~~~

Export results in XML format:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --format xml --output results.xml

Non-Binary Fields
~~~~~~~~~~~~~~~~~

Analyze LFSR over GF(3):

.. code-block:: bash

   lfsr-seq coefficients.csv 3

Analyze LFSR over GF(4) = GF(2²):

.. code-block:: bash

   lfsr-seq coefficients.csv 4

