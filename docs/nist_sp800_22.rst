NIST SP 800-22 Statistical Test Suite
======================================

This section provides a comprehensive introduction to the NIST SP 800-22 Statistical
Test Suite, an industry-standard collection of tests for evaluating the randomness
of binary sequences. The documentation is designed to be accessible to beginners
while providing sufficient depth for researchers.

Introduction
------------

**What is NIST SP 800-22?**

**NIST SP 800-22** (Special Publication 800-22) is a statistical test suite developed
by the National Institute of Standards and Technology (NIST) for testing the randomness
of binary sequences. It is the de facto standard for evaluating:

- Random number generators (RNGs)
- Pseudorandom number generators (PRNGs)
- Stream cipher outputs
- Cryptographic hash function outputs
- Any binary sequence that should appear random

**Why is NIST SP 800-22 Important?**

1. **Industry Standard**: Widely accepted and used in cryptographic evaluation
2. **Comprehensive**: 15 different statistical tests covering various aspects of randomness
3. **Research Credibility**: Results from NIST tests are recognized in academic research
4. **Regulatory Compliance**: Required for many cryptographic certifications (FIPS 140-2, Common Criteria)
5. **Educational Value**: Demonstrates proper statistical testing methodology

**When to Use NIST SP 800-22?**

Use the NIST test suite when you need to:
- Evaluate the quality of a random number generator
- Assess the randomness of stream cipher outputs
- Verify that a sequence exhibits properties expected of random data
- Meet regulatory or certification requirements
- Conduct research on randomness properties

Key Concepts
------------

Statistical Test
~~~~~~~~~~~~~~~~

A **statistical test** is a mathematical procedure that evaluates whether a sequence
exhibits properties expected of a random sequence. Each test focuses on a specific
aspect of randomness (e.g., balance, patterns, complexity).

**How it works**:
1. Compute a test statistic from the sequence
2. Compare the statistic to what would be expected from a random sequence
3. Calculate a p-value indicating how likely the observed statistic is
4. Make a decision: pass (appears random) or fail (appears non-random)

**Example**: The frequency test checks if a sequence has roughly equal numbers of 0s
and 1s, which is expected for a random sequence.

P-value
~~~~~~~

The **p-value** is the probability that a perfect random number generator would produce
a sequence less random than the sequence being tested.

**Interpretation**:
- **Large p-value (≥ 0.01)**: The sequence appears random (test passes)
- **Small p-value (< 0.01)**: Strong evidence of non-randomness (test fails)

**Important Notes**:
- A p-value does NOT tell you the probability that the sequence is random
- A p-value tells you the probability of observing this result IF the sequence were random
- Multiple tests should be considered together, not individually

**Example**: If p-value = 0.05, this means there's a 5% chance that a random sequence
would produce a result this extreme. This is borderline - the test might pass or fail
depending on the significance level.

Significance Level (α)
~~~~~~~~~~~~~~~~~~~~~~~

The **significance level** (denoted α, "alpha") is the threshold for rejecting the null
hypothesis (that the sequence is random). Common values are:

- **α = 0.01 (1%)**: Strict threshold - only 1% of random sequences would fail
- **α = 0.05 (5%)**: More lenient threshold - 5% of random sequences would fail

**Decision Rule**:
- If p-value ≥ α: Test **passes** (sequence appears random)
- If p-value < α: Test **fails** (sequence appears non-random)

**Trade-offs**:
- Lower α (e.g., 0.01): Fewer false positives, but more false negatives
- Higher α (e.g., 0.05): More false positives, but fewer false negatives

Null Hypothesis
~~~~~~~~~~~~~~~

The **null hypothesis** (denoted H₀) is the hypothesis that the sequence is random.
Statistical tests are designed to detect deviations from randomness.

**Testing Process**:
1. Assume the sequence is random (null hypothesis)
2. Compute test statistic
3. Calculate p-value (probability of observing this statistic if sequence were random)
4. If p-value is very small, reject null hypothesis (sequence appears non-random)

**Example**: For the frequency test, the null hypothesis is "the sequence has equal
numbers of 0s and 1s." The test checks if the observed imbalance is too large to be
due to chance.

Type I and Type II Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Type I Error (False Positive)**: Rejecting a random sequence as non-random.
- Occurs when p-value < α even though the sequence is actually random
- Probability of Type I error = α (the significance level)
- Example: A good RNG fails a test due to bad luck

**Type II Error (False Negative)**: Accepting a non-random sequence as random.
- Occurs when p-value ≥ α even though the sequence is actually non-random
- Harder to control - depends on how non-random the sequence is
- Example: A biased RNG passes a test due to insufficient data

**Balancing Errors**:
- Lower α reduces Type I errors but increases Type II errors
- More data (longer sequences) reduces both types of errors

Test Suite
~~~~~~~~~~

A **test suite** is a collection of multiple tests applied to the same sequence.
A sequence should pass most (or all) tests to be considered random.

**Why Multiple Tests?**
- Different tests detect different types of non-randomness
- A single test might miss certain patterns
- Multiple tests provide comprehensive evaluation

**Interpretation**:
- **All tests pass**: Strong evidence the sequence is random
- **Most tests pass**: Sequence appears mostly random (may have minor issues)
- **Many tests fail**: Strong evidence the sequence is non-random

**Note**: A single test failure does not necessarily mean the sequence is non-random.
Consider the overall pattern of results.

The 15 NIST Tests
------------------

Test 1: Frequency (Monobit) Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests whether the number of zeros and ones in a sequence are approximately
equal, as expected for a random sequence.

**What it measures**: The balance of 0s and 1s in the entire sequence.

**How it works**:
1. Count the number of ones (n₁) and zeros (n₀) in the sequence
2. Compute the test statistic: :math:`S = \frac{n_1 - n_0}{\sqrt{n}}`
3. Compute p-value using normal distribution

**Interpretation**:
- Random sequences should have roughly equal numbers of 0s and 1s
- If p-value < 0.01, the sequence is significantly imbalanced
- This test detects sequences that are biased toward 0s or 1s

**Minimum sequence length**: 100 bits (recommended: 1000+ bits)

Test 2: Frequency Test within a Block
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests whether the frequency of ones in M-bit blocks is approximately M/2,
as expected for a random sequence.

**What it measures**: Local balance within blocks of the sequence.

**How it works**:
1. Divide the sequence into N blocks of M bits each
2. For each block, compute the proportion of ones: :math:`\pi_i = \frac{\text{ones}}{M}`
3. Compute chi-square statistic: :math:`\chi^2 = 4M \sum_{i=1}^{N} (\pi_i - 0.5)^2`
4. Compute p-value using chi-square distribution

**Interpretation**:
- Random sequences should have balanced blocks
- If p-value < 0.01, some blocks are significantly imbalanced
- This test detects local biases in the sequence

**Parameters**:
- Block size (M): Typically 128 bits
- Minimum sequence length: M × 10 (recommended: M × 100)

Test 3: Runs Test
~~~~~~~~~~~~~~~~~

**Purpose**: Tests whether the number of runs (consecutive identical bits) is as expected
for a random sequence.

**What it measures**: Oscillation between 0s and 1s in the sequence.

**How it works**:
1. Count the total number of runs (transitions between 0 and 1)
2. Count the number of zeros (n₀) and ones (n₁)
3. Compute expected runs: :math:`E[R] = \frac{2n_0 n_1}{n_0 + n_1} + 1`
4. Compute variance and z-score
5. Compute p-value using normal distribution

**Interpretation**:
- Random sequences should have an appropriate number of runs
- Too few runs indicates clustering (e.g., 00001111...)
- Too many runs indicates oscillation (e.g., 01010101...)
- If p-value < 0.01, the sequence has an abnormal number of runs

**Minimum sequence length**: 100 bits (recommended: 1000+ bits)

Test 4: Tests for Longest-Run-of-Ones in a Block
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests whether the longest run of ones within M-bit blocks is consistent
with that expected for a random sequence.

**What it measures**: Maximum consecutive ones in blocks of the sequence.

**How it works**:
1. Divide the sequence into N blocks of M bits each
2. For each block, find the longest run of consecutive ones
3. Count how many blocks fall into each category (based on longest run length)
4. Compare observed frequencies with expected frequencies using chi-square test

**Interpretation**:
- Random sequences should have longest runs distributed according to theory
- If p-value < 0.01, the sequence has abnormal longest-run patterns
- This test detects sequences with unusually long or short runs of ones

**Parameters**:
- Block size depends on sequence length:
  - M = 8 for sequences ≥ 128 bits
  - M = 128 for sequences ≥ 6272 bits
  - M = 10000 for sequences ≥ 750000 bits

Test 5: Binary Matrix Rank Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests for linear dependence among fixed length substrings of the sequence.

**What it measures**: Linear independence of binary matrices formed from the sequence.

**How it works**:
1. Divide the sequence into N matrices of size M×Q
2. For each matrix, compute its rank over GF(2)
3. Count how many matrices have full rank (M), rank (M-1), or lower rank
4. Compare observed frequencies with expected frequencies using chi-square test

**Interpretation**:
- Random sequences should produce matrices with expected rank distribution
- If p-value < 0.01, the sequence shows linear dependence patterns
- This test detects sequences with linear structure

**Parameters**:
- Matrix size: Typically 32×32
- Minimum sequence length: M × Q × 38 (recommended: M × Q × 100)

Test 6: Discrete Fourier Transform (Spectral) Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Detects periodic features in the sequence that would indicate
a deviation from the assumption of randomness.

**What it measures**: Periodic patterns using Fourier analysis (frequency domain).

**How it works**:
1. Convert sequence to values -1 and +1 (0 → -1, 1 → +1)
2. Compute Discrete Fourier Transform (DFT) of the sequence
3. Compute the modulus of each DFT coefficient
4. Count how many coefficients are below a threshold (expected: 95% for random)
5. Compute p-value using normal distribution

**Interpretation**:
- Random sequences should not have periodic patterns
- If p-value < 0.01, the sequence shows periodic features
- This test detects sequences with repeating patterns

**Minimum sequence length**: 1000 bits (recommended: 10000+ bits)

Test 7: Non-overlapping Template Matching Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests for occurrences of specific m-bit patterns (templates) in
the sequence. Detects over-represented patterns that would indicate non-randomness.

**What it measures**: Frequency of specific m-bit patterns in non-overlapping blocks.

**How it works**:
1. Divide the sequence into non-overlapping blocks of M bits
2. For each block, check if it matches the template pattern
3. Count the number of matches
4. Compare observed frequency with expected frequency using chi-square test

**Interpretation**:
- Random sequences should not have over-represented patterns
- If p-value < 0.01, the sequence shows pattern clustering
- This test detects sequences with specific repeating patterns

**Parameters**:
- Template: The m-bit pattern to search for (default: 9-bit pattern)
- Block size (M): Typically 8 bits

Test 8: Overlapping Template Matching Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Similar to Test 7, but searches for overlapping occurrences of
a template pattern. Detects pattern clustering that would indicate non-randomness.

**What it measures**: Frequency of overlapping m-bit patterns in blocks.

**How it works**:
1. Divide the sequence into N blocks of M bits each
2. For each block, count overlapping occurrences of the template
3. Count how many blocks have k occurrences (k = 0, 1, 2, ...)
4. Compare observed frequencies with expected frequencies using chi-square test

**Interpretation**:
- Random sequences should have template occurrences distributed according to theory
- If p-value < 0.01, the sequence shows pattern clustering
- This test detects sequences with clustered patterns

**Parameters**:
- Template: The m-bit pattern to search for (default: 9 ones)
- Block size (M): Typically 1032 bits

Test 9: Maurer's "Universal Statistical" Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests whether the sequence can be significantly compressed without
loss of information. A random sequence should not be compressible.

**What it measures**: Compressibility of the sequence (ability to predict future
bits from past bits).

**How it works**:
1. Divide the sequence into blocks of L bits
2. Use first Q blocks to initialize a table of block positions
3. For each subsequent block, compute the distance to its last occurrence
4. Compute the test statistic from these distances
5. Compute p-value using normal distribution

**Interpretation**:
- Random sequences should not be compressible
- If p-value < 0.01, the sequence shows compressibility (non-random)
- This test detects sequences with predictable patterns

**Parameters**:
- Block size (L): Typically 6 bits
- Initialization blocks (Q): Typically 10 blocks

Test 10: Linear Complexity Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests whether the sequence is complex enough to be considered random.
Sequences with low linear complexity are predictable and non-random.

**What it measures**: Linear complexity of blocks using the Berlekamp-Massey algorithm.

**How it works**:
1. Divide the sequence into N blocks of M bits each
2. For each block, compute the linear complexity using Berlekamp-Massey
3. Compute deviations from expected complexity
4. Compare observed distribution with expected distribution using chi-square test

**Interpretation**:
- Random sequences should have high linear complexity
- If p-value < 0.01, the sequence has lower complexity than expected
- This test detects sequences that are too predictable

**Parameters**:
- Block size (M): Typically 500 bits

Test 11: Serial Test
~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests whether the number of occurrences of 2^m m-bit overlapping
patterns is approximately the same as would be expected for a random sequence.

**What it measures**: Frequency distribution of m-bit overlapping patterns.

**How it works**:
1. Count occurrences of all possible m-bit patterns (overlapping)
2. Count occurrences of all possible (m-1)-bit patterns
3. Count occurrences of all possible (m-2)-bit patterns
4. Compute chi-square statistics for each pattern length
5. Compute p-value using chi-square distribution

**Interpretation**:
- Random sequences should have uniform pattern distribution
- If p-value < 0.01, the sequence shows non-uniform pattern distribution
- This test detects sequences with pattern bias

**Parameters**:
- Pattern length (m): Typically 2 bits

**Minimum sequence length**: 2^m × 100 bits

Test 12: Approximate Entropy Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests the frequency of all possible overlapping m-bit patterns.
Compares the frequency of overlapping blocks of two consecutive lengths (m and m+1)
against the expected result for a random sequence.

**What it measures**: Entropy (randomness) of overlapping patterns.

**How it works**:
1. Count occurrences of all possible m-bit patterns
2. Count occurrences of all possible (m+1)-bit patterns
3. Compute approximate entropy from pattern frequencies
4. Compute chi-square statistic
5. Compute p-value using chi-square distribution

**Interpretation**:
- Random sequences should have high entropy (uniform pattern distribution)
- If p-value < 0.01, the sequence shows low entropy (non-random)
- This test detects sequences with pattern bias

**Parameters**:
- Pattern length (m): Typically 2 bits

**Minimum sequence length**: 2^m × 10 bits

Test 13: Cumulative Sums (Cusum) Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests whether the cumulative sum of the partial sequences occurring
in the tested sequence is too large or too small relative to what would be
expected for a random sequence.

**What it measures**: Maximum deviation of cumulative sums from zero.

**How it works**:
1. Convert sequence to -1, +1 (0 → -1, 1 → +1)
2. Compute cumulative sums
3. Find maximum absolute cumulative sum
4. Compute p-value using normal distribution approximation

**Interpretation**:
- Random sequences should have cumulative sums that stay close to zero
- If p-value < 0.01, the sequence shows significant bias in cumulative sums
- This test detects sequences with long runs or trends

**Parameters**:
- Mode: "forward" or "backward" (default: "forward")

**Minimum sequence length**: 100 bits

Test 14: Random Excursions Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests the number of cycles having exactly K visits in a cumulative
sum random walk. The test detects deviations from the expected number of visits
to various states in the random walk.

**What it measures**: Distribution of visits to states in a random walk.

**How it works**:
1. Convert sequence to -1, +1 (0 → -1, 1 → +1)
2. Compute cumulative sums (random walk)
3. Identify cycles (return to zero)
4. Count visits to each state (-4, -3, -2, -1, +1, +2, +3, +4)
5. Compute chi-square statistic for each state
6. Compute p-value using chi-square distribution

**Interpretation**:
- Random sequences should have expected distribution of state visits
- If p-value < 0.01, the sequence shows non-random state visit distribution
- This test detects sequences with bias in random walk behavior

**Minimum sequence length**: 1000 bits (recommended: 10000+ bits)

Test 15: Random Excursions Variant Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests the total number of times that a particular state is visited
in a cumulative sum random walk. This is a variant of Test 14 that focuses
on the total number of visits rather than the distribution of visits per cycle.

**What it measures**: Total number of visits to each state in a random walk.

**How it works**:
1. Convert sequence to -1, +1 (0 → -1, 1 → +1)
2. Compute cumulative sums (random walk)
3. Count total visits to each state (-9 to +9, excluding 0)
4. Compute chi-square statistic for each state
5. Compute p-value using chi-square distribution

**Interpretation**:
- Random sequences should have expected total visits to each state
- If p-value < 0.01, the sequence shows non-random state visit counts
- This test detects sequences with bias in random walk behavior

**Minimum sequence length**: 1000 bits (recommended: 10000+ bits)

Mathematical Background
-----------------------

P-value Computation
~~~~~~~~~~~~~~~~~~~~

For most NIST tests, p-values are computed using standard statistical distributions:

**Normal Distribution**: Used for tests with z-scores (e.g., frequency test, runs test)
- Two-tailed test: :math:`p = 2 \times (1 - \Phi(|z|))`
- One-tailed test: :math:`p = 1 - \Phi(z)` or :math:`p = \Phi(z)`

**Chi-square Distribution**: Used for tests comparing observed vs expected frequencies
- :math:`p = 1 - F_{\chi^2}(\chi^2, \text{df})` where F is the chi-square CDF

**Special Distributions**: Some tests use specialized distributions (e.g., rank test)

Statistical Significance
~~~~~~~~~~~~~~~~~~~~~~~~

A test **passes** if:
- p-value ≥ significance_level (typically 0.01)

A test **fails** if:
- p-value < significance_level

**Note**: A single test failure does not necessarily mean the sequence is non-random.
The suite should be interpreted as a whole, not individual tests.

API Reference
-------------

The NIST test suite is implemented in the :mod:`lfsr.nist` module.
See :doc:`api/nist` for complete API documentation.

Quick Start Example
-------------------

Here's a simple example demonstrating NIST testing:

.. code-block:: python

   from lfsr.nist import run_nist_test_suite, frequency_test
   
   # Generate or load a binary sequence
   sequence = [1, 0, 1, 0, 1, 1, 0, 0, 1, 0] * 100  # 1000 bits
   
   # Run a single test
   result = frequency_test(sequence)
   print(f"Test: {result.test_name}")
   print(f"P-value: {result.p_value:.6f}")
   print(f"Passed: {result.passed}")
   
   # Run the complete test suite (first 5 tests)
   suite_result = run_nist_test_suite(sequence)
   print(f"Tests passed: {suite_result.tests_passed}/{suite_result.total_tests}")
   print(f"Overall: {suite_result.overall_assessment}")

Glossary
--------

**Binary Sequence**
   A sequence of bits (0s and 1s) that should appear random.

**Chi-square Distribution**
   A statistical distribution used for testing whether observed frequencies
   match expected frequencies. Denoted :math:`\chi^2`.

**Cryptographic Randomness**
   Randomness properties required for cryptographic applications, including
   unpredictability and statistical randomness.

**Degrees of Freedom (df)**
   A parameter of statistical distributions (e.g., chi-square) that determines
   the shape of the distribution. Often related to the number of independent
   observations or categories.

**Expected Value (E[X])**
   The theoretical average value of a random variable. For a random binary
   sequence, we expect equal numbers of 0s and 1s.

**False Negative**
   See Type II Error.

**False Positive**
   See Type I Error.

**Frequency**
   The number of times a particular value (e.g., 0 or 1) appears in a sequence.

**GF(2)**
   The Galois field of order 2, also known as the binary field. Arithmetic
   operations are performed modulo 2.

**Hypothesis Testing**
   A statistical procedure for making decisions about whether data supports
   a particular hypothesis (e.g., "the sequence is random").

**Matrix Rank**
   The maximum number of linearly independent rows (or columns) in a matrix.
   Over GF(2), rank indicates linear independence in binary space.

**Normal Distribution**
   A bell-shaped probability distribution, also called Gaussian distribution.
   Denoted N(μ, σ²) where μ is the mean and σ² is the variance.

**Null Hypothesis**
   The hypothesis that the sequence is random. Tests are designed to detect
   deviations from this hypothesis.

**P-value**
   The probability that a perfect random number generator would produce a
   sequence less random than the sequence being tested.

**Pseudorandom Number Generator (PRNG)**
   An algorithm that generates sequences that appear random but are actually
   deterministic. Used in cryptography and simulations.

**Random Number Generator (RNG)**
   A device or algorithm that generates truly random sequences from physical
   processes (e.g., thermal noise, radioactive decay).

**Rank (Matrix)**
   See Matrix Rank.

**Run**
   A sequence of consecutive identical bits (e.g., "000" is a run of zeros
   of length 3).

**Significance Level (α)**
   The threshold for rejecting the null hypothesis. Common values are 0.01
   (1%) or 0.05 (5%).

**Statistical Test**
   A mathematical procedure that evaluates whether a sequence exhibits properties
   expected of a random sequence.

**Test Statistic**
   A numerical value computed from the sequence that is used to make a decision
   about randomness.

**Type I Error**
   Rejecting a random sequence as non-random (false positive). Probability
   equals the significance level α.

**Type II Error**
   Accepting a non-random sequence as random (false negative). Probability
   depends on how non-random the sequence is.

**Variance**
   A measure of how spread out values are. For a random variable X, variance
   is :math:`\text{Var}(X) = E[(X - E[X])^2]`.

**Z-score**
   A standardized value indicating how many standard deviations an observation
   is from the mean. :math:`z = \frac{X - \mu}{\sigma}`.

Further Reading
---------------

**Primary Reference**:
- NIST Special Publication 800-22 Revision 1a: "A Statistical Test Suite for Random
  and Pseudorandom Number Generators for Cryptographic Applications"
- Available at: https://csrc.nist.gov/publications/detail/sp/800-22/rev-1a/final

**Statistical Theory**:
- Casella, G., & Berger, R. L. (2002). "Statistical Inference"
- Wasserman, L. (2004). "All of Statistics: A Concise Course in Statistical Inference"

**Cryptography**:
- Menezes, A. J., et al. (1996). "Handbook of Applied Cryptography"
- Stinson, D. R. (2005). "Cryptography: Theory and Practice"

**Random Number Generation**:
- Knuth, D. E. (1997). "The Art of Computer Programming, Volume 2: Seminumerical Algorithms"
