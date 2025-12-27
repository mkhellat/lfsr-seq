CLI Module
==========

The CLI module provides the command-line interface for the lfsr-seq tool, including argument parsing and main execution functions.

.. automodule:: lfsr.cli
   :members:
   :undoc-members:
   :show-inheritance: False
   :imported-members: False

Functions
---------

.. autofunction:: lfsr.cli.main
   :no-index:

Main function that performs LFSR analysis from command-line arguments or programmatic calls.

.. autofunction:: lfsr.cli.parse_args
   :no-index:

Parses command-line arguments and returns an argparse Namespace.

.. autofunction:: lfsr.cli.cli_main
   :no-index:

Entry point for the command-line interface, handles errors and calls main.

Correlation Attack CLI Functions
--------------------------------

The CLI also includes functions for correlation attack analysis:

.. automodule:: lfsr.cli_correlation
   :members:
   :undoc-members:
   :show-inheritance: False
   :imported-members: False

.. autofunction:: lfsr.cli_correlation.load_combination_generator_from_json
   :no-index:

Loads combination generator configuration from JSON file.

.. autofunction:: lfsr.cli_correlation.load_keystream_from_file
   :no-index:

Loads keystream bits from file (supports multiple formats).

.. autofunction:: lfsr.cli_correlation.perform_correlation_attack_cli
   :no-index:

Performs correlation attack from CLI with comprehensive output.

Command-Line Interface
-----------------------

The command-line interface supports the following options:

.. code-block:: text

   lfsr-seq <input_file> <gf_order> [options]
   
   Positional arguments:
     input_file            CSV file containing LFSR coefficient vectors
     gf_order              Galois field order (prime or prime power)
   
   Optional arguments:
     -h, --help            Show help message and exit
     --version             Show version and exit
     -o, --output FILE     Specify output file (default: input_file.out)
     -v, --verbose         Enable verbose output
     -q, --quiet           Enable quiet mode (suppress non-essential output)
     --no-progress         Disable progress bar display
     --format {text,json,csv,xml}
                          Output format (default: text)
     --period-only         Compute periods only (O(1) space with Floyd's)
     --algorithm {floyd,brent,enumeration,auto}
                          Cycle detection algorithm (default: auto)
     --parallel            Enable parallel processing
     --no-parallel         Disable parallel processing
     --num-workers N       Number of parallel workers
   
   Correlation attack options:
     --correlation-attack   Perform correlation attack analysis
     --lfsr-configs FILE   JSON file with combination generator config
     --keystream-file FILE File containing keystream bits
     --target-lfsr INDEX   Index of LFSR to attack (default: 0)
     --significance-level ALPHA
                          Statistical significance level (default: 0.05)

Example
~~~~~~~

.. code-block:: python

   from lfsr.cli import main
   
   # Programmatic usage
   with open("output.txt", "w") as f:
       main(
           "coefficients.csv",
           "2",
           output_file=f,
           verbose=True,
           no_progress=False,
           output_format="text"
       )
