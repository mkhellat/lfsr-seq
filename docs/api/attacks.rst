Attacks Module
==============

The attacks module provides correlation attack implementations for analyzing
combination generators and stream ciphers.

.. automodule:: lfsr.attacks
   :members:
   :undoc-members:
   :show-inheritance:

Classes
-------

LFSRConfig
~~~~~~~~~~

.. autoclass:: lfsr.attacks.LFSRConfig
   :members:
   :no-index:

Represents the configuration for a single LFSR in a combination generator.

**Attributes**:
- ``coefficients``: List of feedback polynomial coefficients
- ``field_order``: Field order (q), typically 2 for binary
- ``degree``: Degree of the LFSR (length of state vector)
- ``initial_state``: Optional initial state vector

**Example**:

.. code-block:: python

   from lfsr.attacks import LFSRConfig
   
   lfsr = LFSRConfig(
       coefficients=[1, 0, 0, 1],
       field_order=2,
       degree=4
   )

CombinationGenerator
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: lfsr.attacks.CombinationGenerator
   :members:
   :no-index:

Represents a combination generator with multiple LFSRs.

**Attributes**:
- ``lfsrs``: List of LFSR configurations
- ``combining_function``: Function that combines LFSR outputs
- ``function_name``: Human-readable name of the combining function

**Example**:

.. code-block:: python

   from lfsr.attacks import CombinationGenerator, LFSRConfig
   
   def xor_combiner(a, b):
       return a ^ b
   
   gen = CombinationGenerator(
       lfsrs=[
           LFSRConfig([1, 0, 0, 1], 2, 4),
           LFSRConfig([1, 1, 0, 1], 2, 4)
       ],
       combining_function=xor_combiner,
       function_name='xor'
   )

CorrelationAttackResult
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: lfsr.attacks.CorrelationAttackResult
   :members:
   :no-index:

Results from a correlation attack.

**Attributes**:
- ``target_lfsr_index``: Index of the LFSR that was attacked
- ``correlation_coefficient``: Measured correlation (range: -1 to +1)
- ``p_value``: Statistical significance (probability correlation is due to chance)
- ``attack_successful``: Whether the attack succeeded
- ``success_probability``: Estimated probability that attack will succeed
- ``required_keystream_bits``: Estimated keystream bits needed
- ``complexity_estimate``: Estimated computational complexity
- ``matches``: Number of matching bits
- ``total_bits``: Total bits compared
- ``match_ratio``: Ratio of matches to total bits

FastCorrelationAttackResult
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: lfsr.attacks.FastCorrelationAttackResult
   :members:
   :no-index:

Results from a fast correlation attack (Meier-Staffelbach).

**Attributes**:
- ``target_lfsr_index``: Index of the LFSR that was attacked
- ``recovered_state``: Recovered initial state (if successful)
- ``correlation_coefficient``: Measured correlation coefficient
- ``attack_successful``: Whether the attack successfully recovered the state
- ``iterations_performed``: Number of iterative decoding iterations
- ``candidate_states_tested``: Number of candidate states evaluated
- ``best_correlation``: Best correlation found among candidates
- ``complexity_estimate``: Estimated computational complexity
- ``keystream_length``: Length of keystream used

DistinguishingAttackResult
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: lfsr.attacks.DistinguishingAttackResult
   :members:
   :no-index:

Results from a distinguishing attack.

**Attributes**:
- ``distinguishable``: Whether the keystream can be distinguished from random
- ``distinguishing_statistic``: Value of the distinguishing statistic
- ``p_value``: Statistical significance
- ``attack_successful``: Whether distinction was successful
- ``method_used``: Method used for distinguishing (e.g., "correlation", "statistical")
- ``details``: Additional details about the attack

Functions
---------

compute_correlation_coefficient
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: lfsr.attacks.compute_correlation_coefficient
   :no-index:

Compute correlation coefficient between two binary sequences.

**Parameters**:
- ``sequence1``: First binary sequence
- ``sequence2``: Second binary sequence (must be same length)

**Returns**:
Tuple of (correlation_coefficient, p_value, detailed_stats)

**Example**:

.. code-block:: python

   from lfsr.attacks import compute_correlation_coefficient
   
   seq1 = [1, 0, 1, 0, 1]
   seq2 = [1, 1, 1, 0, 0]
   rho, p, stats = compute_correlation_coefficient(seq1, seq2)
   print(f"Correlation: {rho:.3f}, p-value: {p:.3f}")

siegenthaler_correlation_attack
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: lfsr.attacks.siegenthaler_correlation_attack
   :no-index:

Perform Siegenthaler's basic correlation attack.

**Parameters**:
- ``combination_generator``: The combination generator being attacked
- ``keystream``: Observed keystream bits
- ``target_lfsr_index``: Index of LFSR to attack (0-based)
- ``significance_level``: Statistical significance level (default: 0.05)
- ``max_sequence_length``: Maximum length of LFSR sequence to generate

**Returns**:
CorrelationAttackResult with attack results

**Example**:

.. code-block:: python

   from lfsr.attacks import (
       CombinationGenerator,
       LFSRConfig,
       siegenthaler_correlation_attack
   )
   
   def majority(a, b, c):
       return 1 if (a + b + c) >= 2 else 0
   
   gen = CombinationGenerator(
       lfsrs=[
           LFSRConfig([1, 0, 0, 1], 2, 4),
           LFSRConfig([1, 1, 0, 1], 2, 4),
           LFSRConfig([1, 0, 1, 1], 2, 4)
       ],
       combining_function=majority,
       function_name='majority'
   )
   
   keystream = gen.generate_keystream(1000)
   result = siegenthaler_correlation_attack(gen, keystream, target_lfsr_index=0)
   
   if result.attack_successful:
       print(f"Attack succeeded! Correlation: {result.correlation_coefficient:.4f}")

fast_correlation_attack
~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: lfsr.attacks.fast_correlation_attack
   :no-index:

Perform Meier-Staffelbach fast correlation attack.

**Parameters**:
- ``combination_generator``: The combination generator being attacked
- ``keystream``: Observed keystream bits
- ``target_lfsr_index``: Index of LFSR to attack (0-based)
- ``max_candidates``: Maximum number of candidate states to test (default: 1000)
- ``max_iterations``: Maximum iterations for iterative decoding (default: 10)
- ``correlation_threshold``: Minimum correlation to consider (default: 0.1)
- ``significance_level``: Statistical significance level (default: 0.05)

**Returns**:
FastCorrelationAttackResult with attack results

**Example**:

.. code-block:: python

   from lfsr.attacks import fast_correlation_attack
   
   result = fast_correlation_attack(
       combination_generator=gen,
       keystream=keystream,
       target_lfsr_index=0,
       max_candidates=1000
   )
   
   if result.attack_successful:
       print(f"Recovered state: {result.recovered_state}")

distinguishing_attack
~~~~~~~~~~~~~~~~~~~~

.. autofunction:: lfsr.attacks.distinguishing_attack
   :no-index:

Perform a distinguishing attack on a combination generator.

**Parameters**:
- ``combination_generator``: The combination generator to test against
- ``keystream``: Observed keystream bits
- ``method``: Distinguishing method ("correlation" or "statistical", default: "correlation")
- ``significance_level``: Statistical significance level (default: 0.05)

**Returns**:
DistinguishingAttackResult with attack results

**Example**:

.. code-block:: python

   from lfsr.attacks import distinguishing_attack
   
   result = distinguishing_attack(
       combination_generator=gen,
       keystream=keystream,
       method="correlation"
   )
   
   if result.distinguishable:
       print("Keystream is distinguishable from random!")

analyze_combining_function
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: lfsr.attacks.analyze_combining_function
   :no-index:

estimate_attack_success_probability
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: lfsr.attacks.estimate_attack_success_probability
   :no-index:

Estimate the probability that a correlation attack will succeed.

**Parameters**:
- ``correlation_coefficient``: Measured correlation coefficient
- ``keystream_length``: Number of keystream bits available
- ``lfsr_degree``: Degree of the target LFSR
- ``field_order``: Field order (default: 2)
- ``significance_level``: Statistical significance level (default: 0.05)
- ``target_success_probability``: Target success probability (default: 0.95)

**Returns**:
Dictionary with detection probability, recovery probability, overall
success probability, required keystream bits, and feasibility.

**Example**:

.. code-block:: python

   from lfsr.attacks import estimate_attack_success_probability
   
   result = estimate_attack_success_probability(
       correlation_coefficient=0.3,
       keystream_length=1000,
       lfsr_degree=10,
       field_order=2
   )
   
   print(f"Success probability: {result['overall_success_probability']:.2%}")
   print(f"Feasible: {result['feasible']}")

Analyze correlation properties of a combining function.

**Parameters**:
- ``function``: The combining function (takes num_inputs arguments)
- ``num_inputs``: Number of inputs to the function
- ``field_order``: Field order (default: 2 for binary)

**Returns**:
Dictionary with analysis results:
- ``correlation_immunity``: Maximum order of correlation immunity
- ``bias``: Output bias (deviation from uniform)
- ``truth_table``: Truth table of the function
- ``balanced``: Whether function is balanced

**Example**:

.. code-block:: python

   from lfsr.attacks import analyze_combining_function
   
   def majority(a, b, c):
       return 1 if (a + b + c) >= 2 else 0
   
   analysis = analyze_combining_function(majority, num_inputs=3)
   print(f"Correlation immunity: {analysis['correlation_immunity']}")
   print(f"Balanced: {analysis['balanced']}")

Important Notes
---------------

**Period-Only Mode**: Correlation attacks work with keystream sequences and do
not require full LFSR state enumeration, making them efficient for analysis.

**Statistical Significance**: Always check the p-value when interpreting
correlation results. A correlation coefficient alone is not sufficient.

**Attack Complexity**: The computational complexity of recovering the LFSR state
is roughly :math:`O(2^d)` where :math:`d` is the LFSR degree. For large degrees,
this becomes infeasible.

**Correlation Immunity**: Functions with high correlation immunity are more
resistant to correlation attacks. Always analyze the combining function before
designing a combination generator.

See Also
--------

* :doc:`../correlation_attacks` for detailed introduction and theory
* :doc:`../mathematical_background` for mathematical foundations
* :doc:`../user_guide` for usage examples
