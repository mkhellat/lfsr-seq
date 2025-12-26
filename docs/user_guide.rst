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
   --period-only              Compute periods only, without storing sequences.
                              Floyd's algorithm uses true O(1) space in this mode.
                              Both algorithms achieve O(1) space, but enumeration is faster.

   --algorithm {floyd,brent,enumeration,auto}
                              Cycle detection algorithm (default: auto)
                              - enumeration: Default, faster for typical periods
                              - floyd: Tortoise-and-hare algorithm, available for
                                educational/verification purposes
                              - brent: Powers-of-2 algorithm, alternative to Floyd
                              - auto: Enumeration for full mode, floyd for period-only
                              Note: In period-only mode, all algorithms use O(1) space.
                              In full mode, all algorithms use O(period) space.

   --check-primitive          Explicitly check and report if characteristic polynomial
                              is primitive. Primitive polynomials yield maximum period
                              LFSRs (period = q^d - 1). 
                              
                              Note: Primitive polynomial detection is automatic - the tool
                              always checks and displays a [PRIMITIVE] indicator in the
                              characteristic polynomial output when a primitive polynomial
                              is detected. This flag makes the check explicit and can be
                              useful for documentation or scripting purposes.
                              
                              Example:
                                lfsr-seq coefficients.csv 2 --check-primitive

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

* **Cycle Detection Algorithms**: Three algorithms available for finding cycle periods
  * **Enumeration** (default): Simple, fast, O(1) space in period-only mode
    * Best for typical LFSR periods (< 1000)
    * 3-5× faster than Floyd/Brent for small-to-medium periods
    * True O(1) space in period-only mode
  * **Floyd's Algorithm**: Tortoise-and-hare method, available as option
    * Correctly implemented, achieves O(1) space in period-only mode
    * Does ~4× more operations, making it 3-5× slower
    * Useful for educational/verification purposes
  * **Brent's Algorithm**: Powers-of-2 method, available as option
    * Alternative to Floyd's, uses powers of 2 to find cycles
    * Similar performance characteristics to Floyd's
    * Useful for educational/verification purposes
  * **Algorithm Selection**: Use ``--algorithm`` option to choose
    * Default: Enumeration (faster, simpler)
    * Period-only mode: All achieve O(1) space, enumeration recommended
    * Use ``scripts/performance_profile.py`` for detailed analysis
  * **Performance Details**: See :doc:`mathematical_background` for comprehensive analysis
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

Primitive Polynomial Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The tool automatically detects primitive polynomials and displays a ``[PRIMITIVE]``
indicator in the characteristic polynomial output. Primitive polynomials are
important because they yield LFSRs with maximum period (q^d - 1).

Example with primitive polynomial:

.. code-block:: bash

   # Create a CSV file with coefficients for a primitive polynomial
   echo "1,0,0,1" > primitive.csv
   lfsr-seq primitive.csv 2

Output will show:
::

   ╎ t^4 + t^3 + 1                          ╎ O : 15           ╎
   ╎                                       ╎ [PRIMITIVE]      ╎

The ``[PRIMITIVE]`` indicator confirms that this polynomial is primitive and
the LFSR will have maximum period 15 (2^4 - 1) for degree 4 over GF(2).

You can explicitly request primitive checking:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --check-primitive

Note: Primitive detection is automatic - the flag makes the check explicit
and is useful for documentation or scripting purposes.

For more information on primitive polynomials and their cryptographic
significance, see the :doc:`mathematical_background` section.

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

