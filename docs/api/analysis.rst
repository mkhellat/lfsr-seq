Analysis Module
===============

The analysis module provides functions for analyzing LFSR sequences, computing periods, and categorizing state vectors.

.. automodule:: lfsr.analysis
   :members:
   :undoc-members:
   :show-inheritance: False
   :imported-members: False

Cycle Detection Algorithms
--------------------------

The module implements efficient cycle detection algorithms for finding sequence periods:

**Floyd's Algorithm** (``_find_sequence_cycle_floyd``):
   Memory-efficient cycle detection using the tortoise-and-hare method.
   Finds period in O(period) time with O(1) extra space.

**Enumeration Method** (``_find_sequence_cycle_enumeration``):
   Fallback method that enumerates all states in the cycle.
   Used when full sequence is needed or Floyd's algorithm hits limits.

The main function ``_find_sequence_cycle`` automatically selects the appropriate algorithm.

Functions
---------

.. autofunction:: lfsr.analysis.lfsr_sequence_mapper
   :no-index:

This is the main function for mapping all possible state vectors to their sequences and periods. It enumerates the entire state space and identifies all cycles.

Example
~~~~~~~

.. code-block:: python

   from sage.all import *
   from lfsr.core import build_state_update_matrix
   from lfsr.analysis import lfsr_sequence_mapper
   
   # Build state update matrix
   coeffs = [1, 1, 0, 1]
   C, CS = build_state_update_matrix(coeffs, 2)
   
   # Create vector space
   V = VectorSpace(GF(2), 4)
   
   # Map sequences
   seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
       C, V, 2, output_file=None, no_progress=False
   )
   
   print(f"Found {len(seq_dict)} sequences")
   print(f"Maximum period: {max_period}")
