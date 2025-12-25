CLI Module
==========

The CLI module provides the command-line interface for the lfsr-seq tool, including argument parsing and main execution functions.

.. automodule:: lfsr.cli
   :members:
   :undoc-members:
   :show-inheritance: False
   :imported-members: False
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
