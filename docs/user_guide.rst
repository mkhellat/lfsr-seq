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

.. code-block:: text

   -o, --output OUTPUT_FILE    Specify output file (default: INPUT_FILE.out)
   -v, --verbose               Enable verbose output
   -q, --quiet                 Enable quiet mode
   --no-progress               Disable progress bar
   --format {text,json,csv,xml} Output format (default: text)
   --version                   Show version and exit
   -h, --help                  Show help message

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

Text Format (Default)
~~~~~~~~~~~~~~~~~~~~~

Human-readable text output with formatted tables and sections.

JSON Format
~~~~~~~~~~~

Structured JSON output suitable for programmatic processing:

.. code-block:: bash

   lfsr-seq strange.csv 2 --format json --output results.json

CSV Format
~~~~~~~~~~

Tabular CSV output:

.. code-block:: bash

   lfsr-seq strange.csv 2 --format csv --output results.csv

XML Format
~~~~~~~~~~

Structured XML output:

.. code-block:: bash

   lfsr-seq strange.csv 2 --format xml --output results.xml

Examples
--------

Basic Analysis
~~~~~~~~~~~~~~

.. code-block:: bash

   lfsr-seq coefficients.csv 2

Verbose Output
~~~~~~~~~~~~~~

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --verbose

Quiet Mode
~~~~~~~~~~

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --quiet

Custom Output File
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --output my_results.txt

JSON Export
~~~~~~~~~~~

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --format json --output results.json

