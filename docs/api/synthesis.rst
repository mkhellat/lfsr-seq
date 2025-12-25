Synthesis Module
================

The synthesis module provides algorithms for synthesizing LFSRs from sequences, including the Berlekamp-Massey algorithm and linear complexity calculation.

.. automodule:: lfsr.synthesis
   :members:
   :undoc-members:
   :show-inheritance:

Functions
---------

.. autofunction:: lfsr.synthesis.berlekamp_massey

Implements the Berlekamp-Massey algorithm for finding the shortest LFSR that can generate a given sequence.

.. autofunction:: lfsr.synthesis.linear_complexity

Computes the linear complexity of a sequence, which is the length of the shortest LFSR that can generate it.

.. autofunction:: lfsr.synthesis.extract_sequence_from_lfsr

Extracts a sequence from an LFSR by iterating through state transitions.

.. autofunction:: lfsr.synthesis.synthesize_lfsr_from_sequence

Convenience function that synthesizes an LFSR from a sequence using Berlekamp-Massey.

Example
~~~~~~~

.. code-block:: python

   from lfsr.synthesis import berlekamp_massey, linear_complexity
   
   # Given sequence
   sequence = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1]
   
   # Find minimal LFSR using Berlekamp-Massey
   poly, complexity = berlekamp_massey(sequence, 2)
   print(f"Characteristic polynomial: {poly}")
   print(f"Linear complexity: {complexity}")
   
   # Compute linear complexity directly
   lc = linear_complexity(sequence, 2)
   print(f"Linear complexity: {lc}")
