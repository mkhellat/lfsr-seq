API Reference
==============

This section provides detailed API documentation for all modules and functions in the lfsr-seq package.

Overview
--------

The lfsr-seq package is organized into the following modules:

* **Core Module** (`lfsr.core`): State update matrix construction and matrix order computation
* **Analysis Module** (`lfsr.analysis`): Sequence mapping and period analysis
* **Polynomial Module** (`lfsr.polynomial`): Characteristic polynomial computation and analysis
* **Field Module** (`lfsr.field`): Finite field validation and coefficient validation
* **Synthesis Module** (`lfsr.synthesis`): Berlekamp-Massey algorithm and linear complexity
* **Statistics Module** (`lfsr.statistics`): Statistical tests for sequence quality
* **Export Module** (`lfsr.export`): Multi-format export (JSON, CSV, XML)
* **I/O Module** (`lfsr.io`): CSV file reading and validation
* **Formatter Module** (`lfsr.formatter`): Output formatting and display
* **CLI Module** (`lfsr.cli`): Command-line interface

Module Documentation
--------------------

.. toctree::
   :maxdepth: 2

   core
   analysis
   polynomial
   field
   synthesis
   statistics
   export
   io
   formatter
   cli

Quick Reference
---------------

Common Functions
~~~~~~~~~~~~~~~

**Core Operations**:

.. code-block:: python

   from lfsr.core import build_state_update_matrix, compute_matrix_order
   from lfsr.analysis import lfsr_sequence_mapper
   from lfsr.polynomial import characteristic_polynomial
   
   # Build state update matrix
   C, CS = build_state_update_matrix([1, 1, 0, 1], 2)
   
   # Compute matrix order
   order = compute_matrix_order(C, identity, 16)
   
   # Map sequences
   seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(C, V, 2)

**Synthesis**:

.. code-block:: python

   from lfsr.synthesis import berlekamp_massey, linear_complexity
   
   # Synthesize LFSR from sequence
   poly, complexity = berlekamp_massey(sequence, 2)
   
   # Compute linear complexity
   lc = linear_complexity(sequence, 2)

**Statistics**:

.. code-block:: python

   from lfsr.statistics import statistical_summary
   
   # Comprehensive statistical analysis
   stats = statistical_summary(sequence, 2)

