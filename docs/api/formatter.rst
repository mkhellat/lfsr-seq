Formatter Module
=================

The formatter module provides functions for formatting and displaying LFSR analysis results in a human-readable format.

.. automodule:: lfsr.formatter
   :members:
   :undoc-members:
   :show-inheritance:

Functions
---------

.. autofunction:: lfsr.formatter.dump

Writes text to output file and/or console based on mode.

.. autofunction:: lfsr.formatter.intro

Prints the introduction header with tool information.

.. autofunction:: lfsr.formatter.section

Prints a section header with title and description.

.. autofunction:: lfsr.formatter.subsection

Prints a subsection header with title and description.

.. autofunction:: lfsr.formatter.dump_seq_row

Formats and displays a sequence row in a table format.

Example
~~~~~~~

.. code-block:: python

   from lfsr.formatter import intro, section, subsection, dump
   
   # Print introduction
   with open("output.txt", "w") as f:
       intro("LFSR Tool", "1.0", "input.csv", "2", f)
       
       # Print section
       section("ANALYSIS RESULTS", "Complete LFSR analysis", f)
       
       # Print subsection
       subsection("SEQUENCES", "All state sequences", f)
       
       # Dump content
       dump("Sequence 1: [1, 0, 1, 1]", "mode=all", f)
