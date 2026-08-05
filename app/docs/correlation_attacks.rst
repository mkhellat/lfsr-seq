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

**Fast Correlation Attack**
   An improved correlation attack that uses iterative decoding techniques to
   recover LFSR states more efficiently than exhaustive search. The
   Meier-Staffelbach attack is the most well-known example.

**Iterative Decoding**
   A technique borrowed from error-correcting codes where candidate solutions are
   refined through multiple iterations, using correlation information to improve
   estimates of the correct state.

**Belief Propagation**
   An algorithm used in iterative decoding where beliefs about the correct state
   are propagated and updated based on observed correlations with the keystream.

**Candidate State**
   A potential initial state of the target LFSR that is tested for correlation
   with the keystream in fast correlation attacks.

**Hamming Weight**
   The number of non-zero elements in a state vector. States with low Hamming
   weight are often tested first in fast correlation attacks.

**State Recovery**
   The process of determining the initial state of an LFSR from observed
   keystream, which is the goal of fast correlation attacks.

**Distinguishing Attack**
   A cryptanalytic technique that determines whether a keystream was generated
   by a specific combination generator or is truly random. This is a weaker form
   of attack that doesn't recover the state but can detect vulnerabilities.

**Distinguisher**
   A statistical test or algorithm that can distinguish between two
   distributions (combination generator output vs. random).

**Distinguishing Statistic**
   A numerical value computed from the keystream that helps determine if it came
   from the combination generator. Common statistics include correlation
   coefficients, frequency differences, and runs differences.

**Distinguishing Advantage**
   The probability that the distinguisher correctly identifies the source minus
   the probability of random guessing. A perfect distinguisher has advantage 1.0.

Fast Correlation Attack (Meier-Staffelbach)
--------------------------------------------

The **fast correlation attack** is an improved version of the basic correlation
attack that uses iterative decoding techniques to recover LFSR states more
efficiently. The Meier-Staffelbach attack (1989) is the most well-known fast
correlation attack.

**What is a Fast Correlation Attack?**

A fast correlation attack treats the correlation attack problem as a decoding
problem. The keystream is viewed as a noisy version of the LFSR sequence, where
the correlation coefficient determines the "noise level." By using iterative
decoding techniques (similar to error-correcting codes), the attack can recover
the LFSR state more efficiently than exhaustive search.

**Key Terminology**:

- **Iterative Decoding**: A technique borrowed from error-correcting codes where
  candidate solutions are refined through multiple iterations, using information
  from correlations to improve estimates.

- **Belief Propagation**: An algorithm used in iterative decoding where beliefs
  about the correct state are propagated and updated based on observed
  correlations.

- **Candidate State**: A potential initial state of the target LFSR that is
  tested for correlation with the keystream.

- **Hamming Weight**: The number of non-zero elements in a state vector. States
  with low Hamming weight are often tested first as they may be more likely.

- **State Recovery**: The process of determining the initial state of an LFSR
  from observed keystream, which is the goal of fast correlation attacks.

**Key Advantages**:

- More efficient than exhaustive search (complexity: :math:`O(2^d / \rho^2)` in
  best case vs :math:`O(2^d)` for exhaustive search)
- Can handle weaker correlations (can work with :math:`\rho` as low as 0.1)
- Uses iterative decoding (belief propagation) to refine candidates
- Better complexity for large state spaces
- Can recover the actual LFSR state (not just detect correlation)

**Mathematical Foundation**:

The fast correlation attack views the problem as:

.. math::

   \text{keystream} = \text{LFSR sequence} + \text{noise}

where the noise level is determined by the correlation coefficient. The
correlation coefficient |rho| relates to the error probability:

.. math::

   \Pr[\text{error}] = \frac{1 - |\rho|}{2}

For |rho| = 0.3, the error probability is 0.35, meaning 35% of bits differ.

**Algorithm Overview**:

1. **Candidate Generation**: Generate candidate initial states for the target
   LFSR. Typically, states with low Hamming weight are tested first, as they may
   be more likely to produce correlated sequences.

2. **Sequence Generation**: For each candidate state, generate the
   corresponding LFSR sequence of length equal to the keystream.

3. **Correlation Computation**: Compute the correlation coefficient between the
   candidate sequence and the observed keystream.

4. **Iterative Decoding**: Use iterative decoding to refine candidates:
   - Start with the best candidate based on correlation
   - Try small variations (e.g., flipping bits)
   - If a variation improves correlation, update the candidate
   - Repeat until no improvement is found

5. **State Selection**: Select the candidate with the highest correlation as
   the recovered state.

**Algorithm Complexity**:

- **Time Complexity**: :math:`O(N \cdot n)` where :math:`N` is the number of
  candidates tested and :math:`n` is the keystream length. In practice, this
  is much better than :math:`O(2^d)` for exhaustive search.
- **Space Complexity**: :math:`O(d + n)` for storing the candidate state and
  keystream, where :math:`d` is the LFSR degree.

**When to Use**:

- Large state spaces where exhaustive search is infeasible (e.g., :math:`d > 20`)
- Weaker correlations that basic attack cannot exploit (|rho| < 0.3)
- Need for state recovery (not just detection)
- When you have sufficient keystream (typically :math:`n > 100 \cdot d`)

**Limitations**:

- Requires sufficient correlation (typically |rho| > 0.1, better if |rho| > 0.2)
- Performance depends on correlation strength (weaker correlations require
  more candidates and iterations)
- May not succeed if correlation is too weak (|rho| < 0.1)
- Requires more keystream than basic attack for reliable state recovery
- Iterative decoding may converge to local optima instead of global optimum

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

**What is a Distinguishing Attack?**

A distinguishing attack answers the question: "Can we tell if this sequence
came from our combination generator, or is it truly random?" Unlike correlation
attacks that aim to recover the LFSR state, distinguishing attacks only need to
detect that the keystream has properties consistent with the combination
generator.

**Key Terminology**:

- **Distinguisher**: A statistical test or algorithm that can distinguish
  between two distributions (in this case, combination generator output vs.
  random).

- **Distinguishing Statistic**: A numerical value computed from the keystream
  that helps determine if it came from the combination generator. Common
  statistics include correlation coefficients, frequency differences, and runs
  differences.

- **False Positive**: Incorrectly identifying a random sequence as coming from
  the combination generator.

- **False Negative**: Failing to identify a sequence from the combination
  generator as such.

- **Distinguishing Advantage**: The probability that the distinguisher correctly
  identifies the source minus the probability of random guessing (0.5 for binary
  choice).

**Why Distinguishing Attacks Matter**:

1. **Security Assessment**: If a keystream can be distinguished from random,
   the generator is vulnerable, even if full state recovery isn't possible.

2. **Weakness Detection**: Distinguishing attacks can identify weak generators
   before more sophisticated attacks are attempted.

3. **Theoretical Foundation**: Many cryptographic proofs rely on the
   indistinguishability of cipher output from random. Distinguishing attacks
   test this assumption.

4. **Practical Applications**: Used in security evaluations of stream ciphers and
   combination generators.

**Mathematical Foundation**:

A distinguisher :math:`D` takes a sequence :math:`s` and outputs 0 (random) or 1
(combination generator). The distinguishing advantage is:

.. math::

   \text{Adv}(D) = \left| \Pr[D(s_{\text{gen}}) = 1] - \Pr[D(s_{\text{rand}}) = 1] \right|

where :math:`s_{\text{gen}}` is from the combination generator and
:math:`s_{\text{rand}}` is random. A perfect distinguisher has advantage 1.0,
while a useless distinguisher has advantage 0.0.

**Methods**:

1. **Correlation-based Distinguishing**:
   
   This method tests for correlations between the keystream and individual LFSR
   sequences. If significant correlations exist, the keystream is
   distinguishable from random.
   
   **Algorithm**:
   
   - For each LFSR in the combination generator:
     - Generate a sequence from that LFSR
     - Compute correlation coefficient with keystream
   - If any correlation is significant (|rho| > threshold, p-value < 0.05), the
     keystream is distinguishable
   
   **Advantages**:
   - Directly tests the vulnerability exploited by correlation attacks
   - Can identify which LFSR is most correlated
   - Provides correlation coefficients for further analysis
   
   **Mathematical Basis**:
   
   For a truly random sequence, the correlation with any fixed sequence should
   be approximately 0. If we observe |rho| significantly different from 0,
   we can distinguish the keystream from random.
   
   The test statistic is:
   
   .. math::
   
      Z = \rho \sqrt{n}
   
   which follows a standard normal distribution under the null hypothesis of no
   correlation.

2. **Statistical Distinguishing**:
   
   This method compares statistical properties of the keystream against expected
   properties of the combination generator.
   
   **Properties Tested**:
   
   - **Frequency**: Distribution of 0s and 1s (should be balanced for good
     generators)
   - **Runs**: Number of consecutive identical bits (should match expected
     distribution)
   - **Autocorrelation**: Correlation of sequence with shifted versions
   - **Pattern Frequency**: Frequency of specific bit patterns
   
   **Algorithm**:
   
   - Generate expected sequence from combination generator
   - Compute statistical properties of both keystream and expected sequence
   - Compare properties using statistical tests (e.g., chi-square, Kolmogorov-Smirnov)
   - If properties differ significantly, the keystream is distinguishable
   
   **Advantages**:
   - Tests multiple statistical properties
   - Can detect weaknesses not visible through correlation alone
   - Provides comprehensive security assessment
   
   **Limitations**:
   - Requires generating expected sequence (may be computationally expensive)
   - May have higher false positive rate than correlation method

**When to Use**:
- Security assessment of combination generators
- Detecting weak generators before attempting full attacks
- Identifying vulnerabilities without full state recovery
- Evaluating indistinguishability properties
- Quick security checks when full cryptanalysis isn't needed

**Interpretation of Results**:

- **Distinguishable = True, Attack Successful = True**: The keystream is
  definitely distinguishable from random. The generator is vulnerable.

- **Distinguishable = False, Attack Successful = False**: The keystream appears
  random. This is good for security, but doesn't guarantee the generator is
  secure (other attacks may still work).

- **Distinguishable = True, Attack Successful = False**: Some distinguishing
  properties detected, but not statistically significant. May indicate weak
  correlation that needs more keystream to detect.

**Limitations**:
- Doesn't recover the LFSR state (only detects vulnerability)
- May have false positives/negatives depending on keystream length
- Statistical method requires generating expected sequence
- Correlation method may miss non-linear correlations

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
