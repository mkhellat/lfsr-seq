NIST Module
===========

The NIST module provides the NIST SP 800-22 Statistical Test Suite for evaluating
the randomness of binary sequences.

.. automodule:: lfsr.nist
   :members:
   :undoc-members:
   :show-inheritance:

Classes
-------

NISTTestResult
~~~~~~~~~~~~~~

.. autoclass:: lfsr.nist.NISTTestResult
   :members:
   :no-index:

Represents results from a single NIST statistical test.

**Attributes**:
- ``test_name``: Name of the test
- ``p_value``: P-value from the test (0.0 to 1.0)
- ``passed``: True if test passed (p_value >= significance_level)
- ``statistic``: Test statistic value
- ``details``: Dictionary with test-specific details

**Example**:

.. code-block:: python

   from lfsr.nist import frequency_test
   
   result = frequency_test([1, 0] * 500)
   print(f"Test: {result.test_name}")
   print(f"P-value: {result.p_value:.6f}")
   print(f"Passed: {result.passed}")

NISTTestSuiteResult
~~~~~~~~~~~~~~~~~~~

.. autoclass:: lfsr.nist.NISTTestSuiteResult
   :members:
   :no-index:

Represents results from the complete NIST test suite.

**Attributes**:
- ``sequence_length``: Length of tested sequence
- ``significance_level``: Significance level used
- ``tests_passed``: Number of tests that passed
- ``tests_failed``: Number of tests that failed
- ``total_tests``: Total number of tests run
- ``results``: List of individual test results
- ``overall_assessment``: "PASSED" or "FAILED"
- ``pass_rate``: Percentage of tests that passed

**Example**:

.. code-block:: python

   from lfsr.nist import run_nist_test_suite
   
   sequence = [1, 0] * 500
   suite_result = run_nist_test_suite(sequence)
   print(f"Tests passed: {suite_result.tests_passed}/{suite_result.total_tests}")
   print(f"Overall: {suite_result.overall_assessment}")

Functions
---------

frequency_test
~~~~~~~~~~~~~~

.. autofunction:: lfsr.nist.frequency_test
   :no-index:

Test 1: Frequency (Monobit) Test.

Tests whether the number of zeros and ones in a sequence are approximately equal.

**Parameters**:
- ``sequence``: Binary sequence (list of 0s and 1s)

**Returns**:
NISTTestResult with test results

**Example**:

.. code-block:: python

   from lfsr.nist import frequency_test
   
   result = frequency_test([1, 0] * 500)
   print(f"P-value: {result.p_value:.6f}, Passed: {result.passed}")

block_frequency_test
~~~~~~~~~~~~~~~~~~~~

.. autofunction:: lfsr.nist.block_frequency_test
   :no-index:

Test 2: Frequency Test within a Block.

Tests whether the frequency of ones in M-bit blocks is approximately M/2.

**Parameters**:
- ``sequence``: Binary sequence (list of 0s and 1s)
- ``block_size``: Size of each block (default: 128)

**Returns**:
NISTTestResult with test results

**Example**:

.. code-block:: python

   from lfsr.nist import block_frequency_test
   
   result = block_frequency_test([1, 0] * 500, block_size=128)
   print(f"P-value: {result.p_value:.6f}, Passed: {result.passed}")

runs_test
~~~~~~~~~

.. autofunction:: lfsr.nist.runs_test
   :no-index:

Test 3: Runs Test.

Tests whether the number of runs (consecutive identical bits) is as expected.

**Parameters**:
- ``sequence``: Binary sequence (list of 0s and 1s)

**Returns**:
NISTTestResult with test results

**Example**:

.. code-block:: python

   from lfsr.nist import runs_test
   
   result = runs_test([1, 0] * 500)
   print(f"P-value: {result.p_value:.6f}, Passed: {result.passed}")

longest_run_of_ones_test
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: lfsr.nist.longest_run_of_ones_test
   :no-index:

Test 4: Tests for Longest-Run-of-Ones in a Block.

Tests whether the longest run of ones within M-bit blocks is consistent with randomness.

**Parameters**:
- ``sequence``: Binary sequence (list of 0s and 1s)
- ``block_size``: Size of each block (default: 8)

**Returns**:
NISTTestResult with test results

**Example**:

.. code-block:: python

   from lfsr.nist import longest_run_of_ones_test
   
   result = longest_run_of_ones_test([1, 0] * 500, block_size=8)
   print(f"P-value: {result.p_value:.6f}, Passed: {result.passed}")

binary_matrix_rank_test
~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: lfsr.nist.binary_matrix_rank_test
   :no-index:

Test 5: Binary Matrix Rank Test.

Tests for linear dependence among fixed length substrings of the sequence.

**Parameters**:
- ``sequence``: Binary sequence (list of 0s and 1s)
- ``matrix_rows``: Number of rows in each matrix (default: 32)
- ``matrix_cols``: Number of columns in each matrix (default: 32)

**Returns**:
NISTTestResult with test results

**Example**:

.. code-block:: python

   from lfsr.nist import binary_matrix_rank_test
   
   result = binary_matrix_rank_test([1, 0] * 1000, matrix_rows=32, matrix_cols=32)
   print(f"P-value: {result.p_value:.6f}, Passed: {result.passed}")

discrete_fourier_transform_test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: lfsr.nist.discrete_fourier_transform_test
   :no-index:

Test 6: Discrete Fourier Transform (Spectral) Test.

Detects periodic features using Fourier analysis.

**Parameters**:
- ``sequence``: Binary sequence (list of 0s and 1s)

**Returns**:
NISTTestResult with test results

non_overlapping_template_matching_test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: lfsr.nist.non_overlapping_template_matching_test
   :no-index:

Test 7: Non-overlapping Template Matching Test.

Tests for occurrences of specific m-bit patterns in non-overlapping blocks.

**Parameters**:
- ``sequence``: Binary sequence (list of 0s and 1s)
- ``template``: Template pattern to search for (optional)
- ``block_size``: Size of each block (default: 8)

**Returns**:
NISTTestResult with test results

overlapping_template_matching_test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: lfsr.nist.overlapping_template_matching_test
   :no-index:

Test 8: Overlapping Template Matching Test.

Tests for overlapping occurrences of template patterns.

**Parameters**:
- ``sequence``: Binary sequence (list of 0s and 1s)
- ``template``: Template pattern to search for (optional)
- ``block_size``: Size of each block (default: 1032)

**Returns**:
NISTTestResult with test results

maurers_universal_test
~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: lfsr.nist.maurers_universal_test
   :no-index:

Test 9: Maurer's "Universal Statistical" Test.

Tests whether the sequence can be significantly compressed.

**Parameters**:
- ``sequence``: Binary sequence (list of 0s and 1s)
- ``block_size``: Size of each block (default: 6)
- ``init_blocks``: Number of initialization blocks (default: 10)

**Returns**:
NISTTestResult with test results

linear_complexity_test
~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: lfsr.nist.linear_complexity_test
   :no-index:

Test 10: Linear Complexity Test.

Tests whether the sequence has sufficient linear complexity.

**Parameters**:
- ``sequence``: Binary sequence (list of 0s and 1s)
- ``block_size``: Size of each block (default: 500)

**Returns**:
NISTTestResult with test results

run_nist_test_suite
~~~~~~~~~~~~~~~~~~~

.. autofunction:: lfsr.nist.run_nist_test_suite
   :no-index:

Run the complete NIST SP 800-22 test suite on a binary sequence.

**Parameters**:
- ``sequence``: Binary sequence (list of 0s and 1s)
- ``significance_level``: Statistical significance level (default: 0.01)
- ``block_size``: Block size for block-based tests (default: 128)
- ``matrix_rows``: Number of rows for matrix rank test (default: 32)
- ``matrix_cols``: Number of columns for matrix rank test (default: 32)

**Returns**:
NISTTestSuiteResult with complete test suite results

**Example**:

.. code-block:: python

   from lfsr.nist import run_nist_test_suite
   
   sequence = [1, 0] * 500
   result = run_nist_test_suite(sequence)
   print(f"Tests passed: {result.tests_passed}/{result.total_tests}")
   print(f"Overall: {result.overall_assessment}")

Important Notes
---------------

**Sequence Requirements**:
- Sequences must be binary (contain only 0s and 1s)
- Minimum length varies by test (typically 100-1000 bits)
- Longer sequences provide more reliable results

**P-value Interpretation**:
- p-value ≥ 0.01: Test passes (sequence appears random)
- p-value < 0.01: Test fails (sequence appears non-random)
- A single test failure does not necessarily mean the sequence is non-random

**Test Suite Interpretation**:
- Consider the overall pattern of results, not individual tests
- A sequence should pass most or all tests to be considered random
- For cryptographic applications, sequences should pass all tests

**Statistical Distributions**:
- The module uses scipy.stats if available for accurate p-value computation
- Falls back to approximations if scipy is not available
- Results are more accurate with scipy installed

See Also
--------

* :doc:`../nist_sp800_22` for detailed introduction and theory
* :doc:`../mathematical_background` for mathematical foundations
* :doc:`../user_guide` for usage examples
* `NIST SP 800-22 <https://csrc.nist.gov/publications/detail/sp/800-22/rev-1a/final>`_ for official specification
