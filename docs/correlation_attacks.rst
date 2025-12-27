Correlation Attacks
===================

This section provides a comprehensive introduction to correlation attacks, a
fundamental cryptanalytic technique for analyzing combination generators and
stream ciphers. The documentation is designed to be accessible to beginners
while providing sufficient depth for researchers.

Introduction
------------

**What is a Correlation Attack?**

A **correlation attack** is a cryptanalytic technique that exploits statistical
correlations between the output of a combination generator (the keystream) and
the outputs of individual LFSRs. When multiple LFSRs are combined using a
non-linear function, the output may be statistically correlated with individual
LFSR outputs, even if the combining function appears secure.

**Why are Correlation Attacks Important?**

1. **Real-World Relevance**: Many stream ciphers use combination generators
   (e.g., A5/1 used in GSM, E0 used in Bluetooth)

2. **Theoretical Foundation**: Understanding correlation attacks is fundamental
   to stream cipher security analysis

3. **Research Tool**: Enables analysis of combination generator security and
   helps identify vulnerabilities

4. **Educational Value**: Demonstrates practical cryptanalysis techniques and
   the importance of correlation immunity

**When are Correlation Attacks Applicable?**

Correlation attacks are applicable when:
- Multiple LFSRs are combined with a non-linear function
- The combining function is not correlation immune (or has low correlation immunity)
- An attacker can observe a sufficient amount of keystream
- The attacker knows the structure of the combination generator

Key Concepts
------------

Combination Generator
~~~~~~~~~~~~~~~~~~~~~~

A **combination generator** is a stream cipher design where multiple LFSRs are
combined using a non-linear function. The output (keystream) is the result of
applying this function to the LFSR outputs.

**Example**: Three LFSRs combined with a majority function:

- LFSR1 output: 1
- LFSR2 output: 0
- LFSR3 output: 1
- Majority(1, 0, 1) = 1 (keystream output)

**Components**:
- **Multiple LFSRs**: Typically 2-5 LFSRs with different feedback polynomials
- **Combining Function**: A non-linear function that takes LFSR outputs as input
- **Keystream**: The output of the combining function

**Common Combining Functions**:
- **XOR**: Linear function (vulnerable to linear algebra attacks)
- **Majority**: Non-linear, correlation immune of order 1
- **AND/OR**: Non-linear but not correlation immune
- **Custom Functions**: Designed for specific security properties

Correlation Coefficient
~~~~~~~~~~~~~~~~~~~~~~~~~

The **correlation coefficient** (denoted |rho|, "rho") measures the linear relationship
between two binary sequences. It ranges from -1 to +1:

- **+1**: Perfect positive correlation (sequences are identical)
- **0**: No correlation (sequences are independent)
- **-1**: Perfect negative correlation (sequences are complements)

**Mathematical Definition**:

For binary sequences, the correlation coefficient is computed as:

.. math::

   \rho = 2 \cdot \Pr[X = Y] - 1

where :math:`\Pr[X = Y]` is the probability that corresponding bits match.

**Interpretation**:
- A correlation coefficient close to 0 indicates no relationship
- A positive correlation (|rho| > 0) means sequences tend to match
- A negative correlation (|rho| < 0) means sequences tend to be complements
- A significant correlation (|rho| > threshold) indicates a vulnerability

**Statistical Significance**:

The correlation coefficient alone is not sufficient; we must also test for
statistical significance. A **p-value** measures the probability that the observed
correlation is due to chance. A small p-value (typically < 0.05) indicates that
the correlation is statistically significant.

Correlation Immunity
~~~~~~~~~~~~~~~~~~~~

**Correlation immunity** is a security property of combining functions. A
function is **correlation immune of order m** if the output is statistically
independent of any m input LFSRs.

**Example**: The majority function of 3 inputs is correlation immune of order 1
(but not order 2). This means:
- The output is independent of any single input
- But the output may be correlated with pairs of inputs

**Why it Matters**:
- Higher correlation immunity makes correlation attacks harder
- Functions with low correlation immunity are vulnerable to correlation attacks
- Designing correlation-immune functions is an active area of research

Siegenthaler's Attack
---------------------

**Siegenthaler's correlation attack** (named after its inventor, Thomas
Siegenthaler) is the fundamental correlation attack technique. It works as follows:

**Algorithm**:

1. **Generate LFSR Sequence**: Generate a sequence from the target LFSR
   (the LFSR we want to attack)

2. **Compute Correlation**: Measure the correlation coefficient between this
   sequence and the observed keystream

3. **Statistical Test**: Determine if the correlation is statistically
   significant (using p-value)

4. **Recover State**: If correlation is significant, use it to recover the
   LFSR state (typically through exhaustive search or more advanced techniques)

**Success Condition**:

The attack succeeds when:
- The correlation coefficient is significantly different from 0
- The p-value is below a significance threshold (typically 0.05)
- Sufficient keystream is available

**Attack Complexity**:

The computational complexity is roughly :math:`O(2^d)` where :math:`d` is the
degree of the target LFSR. This is because we need to search through all
possible initial states.

**Attack Success Probability**:

The probability that a correlation attack will succeed depends on two factors:

1. **Detection Probability**: The probability of detecting the correlation
   (statistical power). This depends on:
   - The correlation coefficient strength (|rho|)
   - The amount of keystream available (n)
   - The statistical significance level (α)

2. **Recovery Probability**: The probability of recovering the LFSR state
   (computational feasibility). This depends on:
   - The state space size (:math:`q^d`)
   - Whether the correlation is strong enough to distinguish the correct state

The overall success probability is the product of these two factors. For
practical attacks, the state space should be less than :math:`2^{40}` and the
correlation coefficient should be at least 0.1 for reasonable success probability.

**Limitations**:

- Requires knowledge of the LFSR structure (feedback polynomial)
- Needs sufficient keystream (typically thousands of bits)
- Only works if correlation exists (function is not correlation immune)
- Computational complexity grows exponentially with LFSR degree

Mathematical Background
-----------------------

Correlation Coefficient Computation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The correlation coefficient between two binary sequences :math:`X = (x_1, x_2, \ldots, x_n)`
and :math:`Y = (y_1, y_2, \ldots, y_n)` is computed as:

.. math::

   \rho = \frac{2 \cdot M - n}{n}

where :math:`M` is the number of matching bits (positions where :math:`x_i = y_i`).

**Statistical Test**:

To test if the correlation is significant, we use a binomial test. Under the null
hypothesis (no correlation), we expect :math:`M \approx n/2`. For large :math:`n`,
we can use a normal approximation:

.. math::

   Z = \frac{M - n/2}{\sqrt{n/4}}

The p-value is then computed from the standard normal distribution.

Combining Function Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Analyzing a combining function involves:

1. **Truth Table**: Enumerate all possible input combinations and their outputs
2. **Output Distribution**: Check if outputs are balanced (equal 0s and 1s)
3. **Bias**: Measure deviation from uniform distribution
4. **Correlation Immunity**: Determine the maximum order of correlation immunity

**Example**: Majority function of 3 inputs:

+-------+-------+-------+----------+
| Input1| Input2| Input3| Output   |
+=======+=======+=======+==========+
|   0   |   0   |   0   |    0     |
|   0   |   0   |   1   |    0     |
|   0   |   1   |   0   |    0     |
|   0   |   1   |   1   |    1     |
|   1   |   0   |   0   |    0     |
|   1   |   0   |   1   |    1     |
|   1   |   1   |   0   |    1     |
|   1   |   1   |   1   |    1     |
+-------+-------+-------+----------+

Output distribution: 4 zeros, 4 ones (balanced)
Correlation immunity: Order 1 (output independent of any single input)

API Reference
-------------

The correlation attack framework is implemented in the :mod:`lfsr.attacks` module.
See :doc:`api/attacks` for complete API documentation.

Command-Line Usage
------------------

Correlation attacks can be performed from the command line using the
``--correlation-attack`` option:

**Basic Usage**:

.. code-block:: bash

   lfsr-seq dummy.csv 2 --correlation-attack --lfsr-configs config.json

**Attack Specific LFSR**:

.. code-block:: bash

   lfsr-seq dummy.csv 2 --correlation-attack --lfsr-configs config.json \
       --target-lfsr 0 --significance-level 0.01

**Use Pre-computed Keystream**:

.. code-block:: bash

   lfsr-seq dummy.csv 2 --correlation-attack --lfsr-configs config.json \
       --keystream-file keystream.txt

**Configuration File Format**:

The ``--lfsr-configs`` file must be JSON with this structure:

.. code-block:: json

   {
       "lfsrs": [
           {
               "coefficients": [1, 0, 0, 1],
               "field_order": 2,
               "degree": 4,
               "initial_state": [1, 0, 0, 0]
           },
           {
               "coefficients": [1, 1, 0, 1],
               "field_order": 2,
               "degree": 4
           }
       ],
       "combining_function": {
           "type": "majority",
           "num_inputs": 2
       }
   }

**Supported Combining Function Types**:
- ``majority``: Majority function (returns 1 if majority of inputs are 1)
- ``xor``: XOR (exclusive OR) function
- ``and``: AND function
- ``or``: OR function
- ``custom``: Custom function (requires ``code`` field with Python function definition)

**CLI Options**:
- ``--correlation-attack``: Enable correlation attack mode
- ``--lfsr-configs CONFIG_FILE``: JSON file with combination generator configuration
- ``--keystream-file KEYSTREAM_FILE``: Optional file containing keystream bits
- ``--target-lfsr INDEX``: Index of LFSR to attack (0-based, default: 0)
- ``--significance-level ALPHA``: Statistical significance level (default: 0.05)
- ``--fast-correlation-attack``: Use fast correlation attack (Meier-Staffelbach) instead of basic attack
- ``--max-candidates N``: Maximum candidate states to test in fast attack (default: 1000)
- ``--distinguishing-attack``: Perform distinguishing attack
- ``--distinguishing-method METHOD``: Method for distinguishing: "correlation" or "statistical" (default: correlation)

See ``examples/combination_generator_config.json`` for a complete example configuration.

Python API Usage
----------------

Here's a simple example demonstrating a correlation attack using the Python API:

.. code-block:: python

   from lfsr.attacks import (
       CombinationGenerator,
       LFSRConfig,
       siegenthaler_correlation_attack
   )
   
   # Define a majority function
   def majority(a, b, c):
       return 1 if (a + b + c) >= 2 else 0
   
   # Create combination generator with 3 LFSRs
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
   
   # Check results
   if result.attack_successful:
       print(f"Attack succeeded!")
       print(f"Correlation coefficient: {result.correlation_coefficient:.4f}")
   
   # Fast correlation attack example
   from lfsr.attacks import fast_correlation_attack
   
   fast_result = fast_correlation_attack(
       combination_generator=gen,
       keystream=keystream,
       target_lfsr_index=0,
       max_candidates=1000
   )
   
   if fast_result.attack_successful:
       print(f"State recovered: {fast_result.recovered_state}")
   
   # Distinguishing attack example
   from lfsr.attacks import distinguishing_attack
   
   dist_result = distinguishing_attack(
       combination_generator=gen,
       keystream=keystream,
       method="correlation"
   )
   
   if dist_result.distinguishable:
       print("Keystream is distinguishable from random!")
       print(f"P-value: {result.p_value:.4f}")
   else:
       print("Attack failed - no significant correlation detected")

Glossary
--------

**Combination Generator**
   A stream cipher design where multiple LFSRs are combined using a
   non-linear function to produce the keystream.

**Correlation Attack**
   A cryptanalytic technique that exploits statistical correlations between
   the keystream and individual LFSR outputs.

**Correlation Coefficient**
   A measure of linear relationship between two sequences, ranging from -1
   to +1. A value near 0 indicates no correlation.

**Correlation Immunity**
   A security property of combining functions. A function is correlation
   immune of order m if the output is statistically independent of any m
   inputs.

**Keystream**
   The output sequence of a stream cipher, used to encrypt plaintext.

**LFSR (Linear Feedback Shift Register)**
   A shift register whose input is a linear function of its previous state.

**P-value**
   The probability that an observed result is due to chance. A small p-value
   (< 0.05) indicates statistical significance.

**Siegenthaler's Attack**
   The fundamental correlation attack technique, named after its inventor.

**Statistical Significance**
   A result is statistically significant if it is unlikely to have occurred by
   chance alone, typically measured using p-values.

Fast Correlation Attack (Meier-Staffelbach)
--------------------------------------------

The **fast correlation attack** is an improved version of the basic correlation
attack that uses iterative decoding techniques to recover LFSR states more
efficiently. The Meier-Staffelbach attack (1989) is the most well-known fast
correlation attack.

**Key Advantages**:
- More efficient than exhaustive search
- Can handle weaker correlations
- Uses iterative decoding (belief propagation)
- Better complexity for large state spaces

**Algorithm Overview**:
1. Generate candidate initial states for the target LFSR
2. For each candidate, generate the corresponding LFSR sequence
3. Compute correlation with keystream
4. Use iterative decoding to refine candidates
5. Select the best candidate based on correlation

**When to Use**:
- Large state spaces where exhaustive search is infeasible
- Weaker correlations that basic attack cannot exploit
- Need for state recovery (not just detection)

**Limitations**:
- Requires sufficient correlation (typically |rho| > 0.1)
- Performance depends on correlation strength
- May not succeed if correlation is too weak

**CLI Usage**:

.. code-block:: bash

   # Use fast correlation attack
   lfsr-seq dummy.csv 2 --correlation-attack --lfsr-configs config.json \
       --fast-correlation-attack --max-candidates 2000

**Python API Usage**:

.. code-block:: python

   from lfsr.attacks import fast_correlation_attack
   
   result = fast_correlation_attack(
       combination_generator=gen,
       keystream=keystream,
       target_lfsr_index=0,
       max_candidates=1000,
       correlation_threshold=0.1
   )
   
   if result.attack_successful:
       print(f"Recovered state: {result.recovered_state}")

Distinguishing Attacks
----------------------

A **distinguishing attack** determines whether a keystream was generated by a
specific combination generator or is truly random. This is a weaker form of
attack that doesn't recover the state but can detect vulnerabilities.

**Applications**:
- Detect if a generator is being used
- Identify weak generators
- Security assessment
- Vulnerability detection

**Methods**:

1. **Correlation-based**: Tests for correlations between keystream and
   individual LFSR sequences. If correlations exist, the keystream is
   distinguishable from random.

2. **Statistical**: Tests statistical properties of the keystream against
   expected properties of the combination generator.

**When to Use**:
- Security assessment of combination generators
- Detecting weak generators
- Identifying vulnerabilities without full state recovery

**CLI Usage**:

.. code-block:: bash

   # Perform distinguishing attack
   lfsr-seq dummy.csv 2 --correlation-attack --lfsr-configs config.json \
       --distinguishing-attack --distinguishing-method correlation

**Python API Usage**:

.. code-block:: python

   from lfsr.attacks import distinguishing_attack
   
   result = distinguishing_attack(
       combination_generator=gen,
       keystream=keystream,
       method="correlation"
   )
   
   if result.distinguishable:
       print("Keystream is distinguishable from random!")

Further Reading
---------------

- Siegenthaler, T. (1984). "Correlation-immunity of nonlinear combining
  functions for cryptographic applications"

- Meier, W., & Staffelbach, O. (1989). "Fast correlation attacks on certain
  stream ciphers"

- Rueppel, R. A. (1986). "Analysis and Design of Stream Ciphers"

- Menezes, A. J., et al. (1996). "Handbook of Applied Cryptography"
