Analysis Module
===============

The analysis module provides functions for analyzing LFSR sequences, computing periods, and categorizing state vectors.

.. automodule:: lfsr.analysis
   :members:
   :undoc-members:
   :show-inheritance:

Functions
---------

.. autofunction:: lfsr.analysis.lfsr_sequence_mapper

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
