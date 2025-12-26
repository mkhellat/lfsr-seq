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

**Period-Only Functions** (for ``--period-only`` mode):

**Floyd's Algorithm** (``_find_period_floyd``):
   Period-only version using tortoise-and-hare method.
   Finds period in O(period) time with true O(1) space.
   Performs ~4× more operations than enumeration, making it 3-5× slower.
   Useful for educational/verification purposes.

**Brent's Algorithm** (``_find_period_brent``):
   Period-only version using powers-of-2 method.
   Finds period in O(period) time with true O(1) space.
   Similar performance characteristics to Floyd's algorithm.
   Alternative to Floyd's, useful for educational/verification purposes.

**Enumeration Method** (``_find_period_enumeration``):
   Period-only version that enumerates without storing sequence.
   Finds period in O(period) time with O(1) space.
   Faster and simpler than Floyd/Brent for typical periods.

**Period Dispatcher** (``_find_period``):
   Selects period-only algorithm based on ``algorithm`` parameter.
   Supports "floyd", "brent", "enumeration", or "auto".
   Returns only the period, not the sequence.

**Full Sequence Functions** (for normal mode):

**Floyd's Algorithm** (``_find_sequence_cycle_floyd``):
   Finds period using tortoise-and-hare, then enumerates full sequence.
   Uses O(period) space since sequence must be stored.
   Slower than enumeration due to Phase 1+2 overhead.

**Brent's Algorithm** (``_find_sequence_cycle_brent``):
   Finds period using powers-of-2, then enumerates full sequence.
   Uses O(period) space since sequence must be stored.
   Similar performance to Floyd's algorithm.

**Enumeration Method** (``_find_sequence_cycle_enumeration``):
   Enumerates all states in the cycle.
   Faster and simpler than Floyd/Brent.
   Default choice for full sequence mode.

**Main Dispatcher** (``_find_sequence_cycle``):
   Selects algorithm based on ``algorithm`` and ``period_only`` parameters.
   Supports "floyd", "brent", "enumeration", or "auto".
   * Full mode (``period_only=False``): Defaults to enumeration
   * Period-only mode (``period_only=True``): Uses period-only functions

**Performance Characteristics**:

See :doc:`../mathematical_background` for detailed performance analysis including:
* Operation count comparisons
* Time performance measurements
* Space complexity verification
* Algorithm selection guidelines

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
