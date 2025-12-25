Statistics Module
==================

The statistics module provides statistical tests and analysis functions for evaluating the quality and randomness properties of LFSR-generated sequences.

.. automodule:: lfsr.statistics
   :members:
   :undoc-members:
   :show-inheritance:

Functions
---------

.. autofunction:: lfsr.statistics.frequency_test

Performs frequency (monobit) test on a sequence to check if zeros and ones are approximately equal.

.. autofunction:: lfsr.statistics.runs_test

Performs runs test on a binary sequence to check if the number of runs is consistent with randomness.

.. autofunction:: lfsr.statistics.autocorrelation

Computes the autocorrelation of a sequence at a given lag.

.. autofunction:: lfsr.statistics.periodicity_test

Tests for periodic patterns in a sequence.

.. autofunction:: lfsr.statistics.linear_complexity_profile

Computes the linear complexity profile of a sequence, showing how complexity evolves.

.. autofunction:: lfsr.statistics.statistical_summary

Provides a comprehensive statistical summary of a sequence, including multiple tests.

Example
~~~~~~~

.. code-block:: python

   from lfsr.statistics import (
       frequency_test,
       runs_test,
       autocorrelation,
       statistical_summary
   )
   
   # Generate or load a sequence
   sequence = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1]
   
   # Frequency test
   freq_result = frequency_test(sequence, 2)
   print(f"Frequency ratio: {freq_result['ratio']}")
   
   # Runs test
   runs_result = runs_test(sequence)
   print(f"Total runs: {runs_result['total_runs']}")
   
   # Autocorrelation
   autocorr = autocorrelation(sequence, lag=1)
   print(f"Autocorrelation (lag=1): {autocorr}")
   
   # Comprehensive summary
   summary = statistical_summary(sequence, 2)
   print(summary)
