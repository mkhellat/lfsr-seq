Examples
========

Basic LFSR Analysis
-------------------

Analyze a simple 4-bit LFSR over GF(2):

.. code-block:: bash

   echo "1,1,0,1" > test.csv
   lfsr-seq test.csv 2

This will generate ``test.csv.out`` with:
- State update matrix
- All state sequences and their periods
- Characteristic polynomial and its order

Multiple LFSR Configurations
----------------------------

Analyze multiple LFSR configurations:

.. code-block:: bash

   cat > lfsrs.csv << EOF
   1,1,0,1
   1,0,1,1
   1,1,1,0,1
   EOF
   lfsr-seq lfsrs.csv 2

Each row will be analyzed separately.

Non-Binary Fields
-----------------

Analyze LFSR over GF(3):

.. code-block:: bash

   echo "1,2,1" > gf3.csv
   lfsr-seq gf3.csv 3

Export to JSON
~~~~~~~~~~~~~~

Export results in JSON format:

.. code-block:: bash

   lfsr-seq strange.csv 2 --format json --output results.json

The JSON file will contain structured data suitable for programmatic processing.

Parallel Processing
-------------------

Use parallel processing for faster analysis of larger LFSRs:

.. code-block:: bash

   # Enable parallel processing explicitly
   lfsr-seq coefficients.csv 2 --parallel --period-only

   # Use specific number of workers
   lfsr-seq coefficients.csv 2 --parallel --num-workers 4 --period-only

   # Auto-detection (enabled for large state spaces)
   lfsr-seq large_lfsr.csv 2 --period-only

**Note**: Parallel processing requires ``--period-only`` mode. The tool automatically
forces period-only mode when parallel is enabled, displaying a warning.

Python API Usage
----------------

Use the library programmatically:

.. code-block:: python

   from lfsr.cli import main
   from lfsr.synthesis import berlekamp_massey, linear_complexity
   from lfsr.statistics import statistical_summary
   from lfsr.core import build_state_update_matrix, compute_matrix_order
   from lfsr.polynomial import characteristic_polynomial, polynomial_order
   from lfsr.field import validate_gf_order, validate_coefficient_vector

   # Analyze LFSR from CSV file
   with open("output.txt", "w") as f:
       main("coefficients.csv", "2", output_file=f)

   # Synthesize LFSR from sequence using Berlekamp-Massey
   sequence = [1, 0, 1, 1, 0, 1, 0, 0, 1]
   poly, complexity = berlekamp_massey(sequence, 2)
   print(f"Linear complexity: {complexity}")

   # Calculate linear complexity directly
   complexity = linear_complexity(sequence, 2)
   print(f"Linear complexity: {complexity}")

   # Statistical analysis
   stats = statistical_summary(sequence, 2)
   print(f"Frequency ratio: {stats['frequency']['ratio']}")
   print(f"Total runs: {stats['runs']['total_runs']}")

   # Build state update matrix
   coeffs = [1, 1, 0, 1]
   C, CS = build_state_update_matrix(coeffs, 2)
   order = compute_matrix_order(C, CS)
   print(f"Matrix order (period): {order}")

   # Characteristic polynomial
   char_poly = characteristic_polynomial(coeffs, 2)
   poly_order = polynomial_order(char_poly, 2)
   print(f"Polynomial order: {poly_order}")

   # Field validation
   gf_order = validate_gf_order("4")  # Returns 4
   validate_coefficient_vector([1, 2, 3], 4)  # Validates coefficients for GF(4)

Correlation Attacks
-------------------

Perform correlation attacks on combination generators:

.. code-block:: python

   from lfsr.attacks import (
       CombinationGenerator,
       LFSRConfig,
       siegenthaler_correlation_attack
   )
   
   # Define a majority function
   def majority(a, b, c):
       return 1 if (a + b + c) >= 2 else 0
   
   # Create combination generator
   gen = CombinationGenerator(
       lfsrs=[
           LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4),
           LFSRConfig(coefficients=[1, 1, 0, 1], field_order=2, degree=4),
           LFSRConfig(coefficients=[1, 0, 1, 1], field_order=2, degree=4)
       ],
       combining_function=majority,
       function_name='majority'
   )
   
   # Generate keystream
   keystream = gen.generate_keystream(length=1000)
   
   # Attack the first LFSR
   result = siegenthaler_correlation_attack(
       combination_generator=gen,
       keystream=keystream,
       target_lfsr_index=0
   )
   
   if result.attack_successful:
       print(f"Attack succeeded! Correlation: {result.correlation_coefficient:.4f}")
   else:
       print("No significant correlation detected")

Analyze Combining Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Analyze the security properties of combining functions:

.. code-block:: python

   from lfsr.attacks import analyze_combining_function
   
   def majority(a, b, c):
       return 1 if (a + b + c) >= 2 else 0
   
   analysis = analyze_combining_function(majority, num_inputs=3)
   print(f"Balanced: {analysis['balanced']}")
   print(f"Bias: {analysis['bias']}")
   print(f"Correlation immunity order: {analysis['correlation_immunity']}")

**Fast Correlation Attack**:

.. code-block:: python

   from lfsr.attacks import fast_correlation_attack
   
   # Perform fast correlation attack
   result = fast_correlation_attack(
       combination_generator=gen,
       keystream=keystream,
       target_lfsr_index=0,
       max_candidates=1000
   )
   
   if result.attack_successful:
       print(f"Recovered state: {result.recovered_state}")

**Distinguishing Attack**:

.. code-block:: python

   from lfsr.attacks import distinguishing_attack
   
   # Test if keystream is distinguishable
   result = distinguishing_attack(
       combination_generator=gen,
       keystream=keystream,
       method="correlation"
   )
   
   if result.distinguishable:
       print("Keystream is distinguishable from random!")

For complete examples, see ``examples/correlation_attack_example.py``.

Optimization Techniques
-----------------------

**Period Computation via Factorization**:

.. code-block:: python

   from lfsr.polynomial import compute_period_via_factorization
   
   # Compute period using factorization (faster for large LFSRs)
   period = compute_period_via_factorization([1, 0, 0, 1], 2)
   print(f"Period: {period}")

**Mathematical Shortcut Detection**:

.. code-block:: python

   from lfsr.polynomial import detect_mathematical_shortcuts
   
   # Detect special cases and get recommendations
   shortcuts = detect_mathematical_shortcuts([1, 0, 0, 1], 2)
   
   if shortcuts['is_primitive']:
       print(f"Primitive polynomial! Period = {shortcuts['expected_period']}")
   print(f"Recommended method: {shortcuts['recommended_method']}")
   print(f"Complexity: {shortcuts['complexity_estimate']}")

**Result Caching**:

.. code-block:: python

   from lfsr.optimization import ResultCache, get_global_cache
   
   # Use global cache
   cache = get_global_cache()
   
   # Generate cache key
   key = cache.generate_key([1, 0, 0, 1], 2, "period")
   
   # Check cache before computing
   if key in cache:
       period = cache.get(key)
       print(f"Cached period: {period}")
   else:
       period = compute_period_via_factorization([1, 0, 0, 1], 2)
       cache.set(key, period)
       print(f"Computed period: {period}")
   
   # Get cache statistics
   stats = cache.get_stats()
   print(f"Cache hit rate: {stats['hit_rate']:.2%}")

For complete examples, see ``examples/optimization_example.py``.

Algebraic Attacks
-----------------

**Algebraic Immunity Computation**:

.. code-block:: python

   from lfsr.attacks import compute_algebraic_immunity
   
   def filtering_function(x0, x1, x2, x3):
       return x0 & x1  # Example filtering function
   
   result = compute_algebraic_immunity(filtering_function, 4)
   print(f"Algebraic immunity: {result['algebraic_immunity']}")
   print(f"Optimal: {result['optimal']}")

**Gröbner Basis Attack**:

.. code-block:: python

   from lfsr.attacks import LFSRConfig, groebner_basis_attack
   
   lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
   keystream = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
   
   result = groebner_basis_attack(lfsr, keystream)
   if result.attack_successful:
       print(f"Recovered state: {result.recovered_state}")

**Cube Attack**:

.. code-block:: python

   from lfsr.attacks import LFSRConfig, cube_attack
   
   lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
   keystream = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
   
   result = cube_attack(lfsr, keystream, max_cube_size=5)
   if result.attack_successful:
       print(f"Cubes found: {result.cubes_found}")
       print(f"Recovered bits: {result.recovered_bits}")

For complete examples, see ``examples/algebraic_attack_example.py`` (to be created).

NIST SP 800-22 Test Suite
--------------------------

Run NIST statistical tests on binary sequences:

.. code-block:: python

   from lfsr.nist import run_nist_test_suite, frequency_test
   
   # Generate or load a binary sequence
   sequence = [1, 0, 1, 0, 1, 1, 0, 0, 1, 0] * 100  # 1000 bits
   
   # Run a single test
   result = frequency_test(sequence)
   print(f"P-value: {result.p_value:.6f}")
   print(f"Passed: {result.passed}")
   
   # Run the complete test suite
   suite_result = run_nist_test_suite(sequence)
   print(f"Tests passed: {suite_result.tests_passed}/{suite_result.total_tests}")
   print(f"Overall: {suite_result.overall_assessment}")

For complete examples, see ``examples/nist_test_example.py``.

NIST SP 800-22 Statistical Tests
-----------------------------------

Run NIST statistical tests on binary sequences:

.. code-block:: python

   from lfsr.nist import run_nist_test_suite, frequency_test
   
   # Generate or load a binary sequence
   sequence = [1, 0, 1, 0, 1, 1, 0, 0, 1, 0] * 100  # 1000 bits
   
   # Run a single test
   result = frequency_test(sequence)
   print(f"P-value: {result.p_value:.6f}, Passed: {result.passed}")
   
   # Run the complete test suite
   suite_result = run_nist_test_suite(sequence)
   print(f"Tests passed: {suite_result.tests_passed}/{suite_result.total_tests}")
   print(f"Overall: {suite_result.overall_assessment}")

For complete examples, see ``examples/nist_test_example.py``.

NIST SP 800-22 Test Suite
-------------------------

Run NIST statistical tests on binary sequences:

.. code-block:: python

   from lfsr.nist import run_nist_test_suite, frequency_test
   
   # Generate or load a binary sequence
   sequence = [1, 0, 1, 0, 1, 1, 0, 0, 1, 0] * 100  # 1000 bits
   
   # Run a single test
   result = frequency_test(sequence)
   print(f"P-value: {result.p_value:.6f}, Passed: {result.passed}")
   
   # Run the complete test suite
   suite_result = run_nist_test_suite(sequence)
   print(f"Tests passed: {suite_result.tests_passed}/{suite_result.total_tests}")
   print(f"Overall: {suite_result.overall_assessment}")

For complete examples, see ``examples/nist_test_example.py``.

Parallel Processing API
------------------------

Use parallel processing programmatically:

.. code-block:: python

   from sage.all import *
   from lfsr.analysis import lfsr_sequence_mapper_parallel
   from lfsr.core import build_state_update_matrix

   # Build state update matrix
   coeffs = [1, 0, 0, 1]
   C, CS = build_state_update_matrix(coeffs, 2)
   V = VectorSpace(GF(2), 4)

   # Parallel processing with 2 workers
   seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel(
       C, V, 2, output_file=None, no_progress=True,
       period_only=True, num_workers=2
   )

   print(f"Found {len(seq_dict)} sequences")
   print(f"Maximum period: {max_period}")
   print(f"Period sum: {periods_sum} (should equal state space size)")

   # Compare with sequential
   from lfsr.analysis import lfsr_sequence_mapper
   seq_dict_seq, period_dict_seq, max_period_seq, periods_sum_seq = lfsr_sequence_mapper(
       C, V, 2, output_file=None, no_progress=True, period_only=True
   )

   # Verify correctness
   assert max_period == max_period_seq
   assert periods_sum == 16  # State space size for 4-bit LFSR

