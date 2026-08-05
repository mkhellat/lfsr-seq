NIST SP 800-22 Statistical Test Suite
======================================

This section provides a comprehensive theoretical treatment of the NIST SP 800-22
Statistical Test Suite, an industry-standard collection of tests for evaluating
the randomness of binary sequences. The documentation is designed to be accessible
to beginners while providing sufficient depth for researchers and developers. We
begin with intuitive explanations and gradually build to rigorous mathematical
formulations.

Introduction
------------

**What is NIST SP 800-22?**

**NIST SP 800-22** (Special Publication 800-22) is a statistical test suite
developed by the National Institute of Standards and Technology (NIST) for
testing the randomness of binary sequences. It is the de facto standard for
evaluating:

- Random number generators (RNGs)
- Pseudorandom number generators (PRNGs)
- Stream cipher outputs
- Cryptographic hash function outputs
- Any binary sequence that should appear random

**Historical Context and Motivation**

The NIST SP 800-22 test suite was developed in response to the need for
standardized methods to evaluate the quality of random and pseudorandom number
generators used in cryptographic applications. The original publication (SP
800-22) was released in 2001, with Revision 1a published in 2010, incorporating
corrections and improvements based on years of use and research.

The development of the test suite was motivated by several factors:

1. **Cryptographic Security**: Cryptographic systems rely on high-quality random
   number generation. Weak randomness can lead to security vulnerabilities.

2. **Standardization**: Prior to NIST SP 800-22, there was no widely accepted
   standard for evaluating randomness, leading to inconsistent evaluation
   methods.

3. **Regulatory Requirements**: Cryptographic certifications (e.g., FIPS 140-2,
   Common Criteria) require evidence of randomness quality, necessitating
   standardized tests.

4. **Research Needs**: Academic and industrial research on random number
   generation requires reproducible, standardized evaluation methods.

The test suite draws on decades of research in statistical testing, probability
theory, and cryptanalysis. It incorporates tests based on classical statistical
methods (e.g., chi-square tests, normal approximations) as well as specialized
tests designed specifically for binary sequences (e.g., linear complexity test,
matrix rank test).

**Why is NIST SP 800-22 Important?**

1. **Industry Standard**: Widely accepted and used in cryptographic evaluation,
   making it the de facto standard for randomness testing.

2. **Comprehensive Coverage**: 15 different statistical tests covering
   various aspects of randomness, including balance, patterns, complexity, and
   distribution properties.

3. **Research Credibility**: Results from NIST tests are recognized and
   accepted in academic research, providing credibility to randomness evaluations.

4. **Regulatory Compliance**: Required for many cryptographic certifications
   (FIPS 140-2, Common Criteria), making it essential for commercial
   cryptographic products.

5. **Educational Value**: Demonstrates proper statistical testing methodology
   and provides a framework for understanding randomness properties.

6. **Theoretical Foundation**: Each test is based on solid statistical theory,
   providing theoretical guarantees about test behavior.

**When to Use NIST SP 800-22?**

Use the NIST test suite when you need to:

- Evaluate the quality of a random number generator for cryptographic use
- Assess the randomness of stream cipher outputs or pseudorandom sequences
- Verify that a sequence exhibits properties expected of random data
- Meet regulatory or certification requirements for cryptographic systems
- Conduct research on randomness properties and statistical analysis
- Compare different random number generation methods

**Key Concepts**:

- **Statistical Test**: A mathematical procedure that evaluates whether a
  sequence exhibits properties expected of a random sequence. Each test focuses
  on a specific aspect of randomness.

- **P-value**: The probability that a perfect random number generator would
  produce a sequence less random than the sequence being tested. Small p-values
  indicate evidence of non-randomness.

- **Significance Level**: The threshold for rejecting the null hypothesis
  (that the sequence is random). Common values are :math:`\alpha = 0.01` or
  :math:`\alpha = 0.05`.

- **Null Hypothesis**: The hypothesis that the sequence is random. Tests are
  designed to detect deviations from randomness.

- **Type I and Type II Errors**: Type I errors (false positives) occur when
  random sequences are rejected, while Type II errors (false negatives) occur
  when non-random sequences are accepted.

Notation and Terminology
--------------------------

This section uses the following notation, consistent with the rest of the
documentation:

**Sequences**:

* :math:`s = s_0, s_1, s_2, \ldots, s_{n-1}` denotes a binary sequence of
  length :math:`n`
* :math:`n` denotes the length of the sequence
* :math:`n_0` denotes the number of zeros in the sequence
* :math:`n_1` denotes the number of ones in the sequence

**Statistical Distributions**:

* :math:`N(\mu, \sigma^2)` denotes a normal distribution with mean :math:`\mu`
  and variance :math:`\sigma^2`
* :math:`\chi^2_k` denotes a chi-square distribution with :math:`k` degrees of
  freedom
* :math:`\Phi(z)` denotes the cumulative distribution function (CDF) of the
  standard normal distribution
* :math:`F_{\chi^2}(x, k)` denotes the CDF of a chi-square distribution with
  :math:`k` degrees of freedom

**Test Statistics**:

* :math:`S` denotes a test statistic
* :math:`z` denotes a z-score (standardized value)
* :math:`\chi^2` denotes a chi-square statistic
* :math:`p` denotes a p-value

**Hypothesis Testing**:

* :math:`H_0` denotes the null hypothesis (sequence is random)
* :math:`H_1` denotes the alternative hypothesis (sequence is non-random)
* :math:`\alpha` denotes the significance level (typically :math:`0.01` or
  :math:`0.05`)

**Probability and Expectation**:

* :math:`P(A)` denotes the probability of event :math:`A`
* :math:`E[X]` denotes the expected value of random variable :math:`X`
* :math:`\text{Var}(X)` denotes the variance of random variable :math:`X`

**Other Symbols**:

* :math:`M` denotes block size (for block-based tests)
* :math:`N` denotes the number of blocks
* :math:`m` denotes pattern length (for pattern-based tests)
* :math:`\pi` denotes proportion (e.g., proportion of ones in a block)

Key Concepts
------------

Statistical Test
~~~~~~~~~~~~~~~~

A **statistical test** is a mathematical procedure that evaluates whether a
sequence exhibits properties expected of a random sequence. Each test focuses on
a specific aspect of randomness (e.g., balance, patterns, complexity).

**Mathematical Foundation**:

A statistical test can be formalized as:

1. **Null Hypothesis** :math:`H_0`: The sequence is random
2. **Alternative Hypothesis** :math:`H_1`: The sequence is non-random
3. **Test Statistic** :math:`S`: A function of the sequence that measures a
   specific property
4. **Distribution Under** :math:`H_0`: The distribution of :math:`S` when
   :math:`H_0` is true
5. **Decision Rule**: Reject :math:`H_0` if :math:`S` is in the critical region

**How it works**:

1. Compute a test statistic :math:`S` from the sequence
2. Determine the distribution of :math:`S` under the null hypothesis (that
   the sequence is random)
3. Calculate a p-value :math:`p = P(S \geq s_{\text{obs}} | H_0)`, where
   :math:`s_{\text{obs}}` is the observed statistic
4. Make a decision: reject :math:`H_0` (sequence appears non-random) if
   :math:`p < \alpha`, or fail to reject :math:`H_0` (sequence appears random)
   if :math:`p \geq \alpha`

**Example**: The frequency test checks if a sequence has roughly equal numbers
of :math:`0` s and :math:`1` s, which is expected for a random sequence. The
test statistic measures the deviation from this expectation.

P-value
~~~~~~~

The **p-value** is the probability that a perfect random number generator would
produce a sequence less random than the sequence being tested.

**Mathematical Definition**:

For a test statistic :math:`S` with observed value :math:`s_{\text{obs}}`, the
p-value is:

.. math::

   p = P(S \geq s_{\text{obs}} | H_0)

or for two-tailed tests:

.. math::

   p = 2 \times P(|S| \geq |s_{\text{obs}}| | H_0)

**Interpretation**:

- **Large p-value** (:math:`\geq \alpha`, typically :math:`\geq 0.01`): The
  sequence appears random (test passes). The observed statistic is consistent
  with what would be expected from a random sequence.

- **Small p-value** (:math:`< \alpha`, typically :math:`< 0.01`): Strong
  evidence of non-randomness (test fails). The observed statistic is unlikely
  to occur if the sequence were random.

**Important Notes**:

- A p-value does NOT tell you the probability that the sequence is random
- A p-value tells you the probability of observing this result IF the sequence
  were random
- Multiple tests should be considered together, not individually
- A single test failure does not necessarily mean the sequence is non-random

**Example**: If p-value :math:`= 0.05`, this means there's a :math:`5\%` chance
that a random sequence would produce a result this extreme. This is borderline
- the test might pass or fail depending on the significance level.

Significance Level (α)
~~~~~~~~~~~~~~~~~~~~~~~

The **significance level** (denoted :math:`\alpha`, "alpha") is the threshold for
rejecting the null hypothesis (that the sequence is random). Common values are:

- **:math:`\alpha = 0.01`** (:math:`1\%`): Strict threshold - only :math:`1\%`
  of random sequences would fail
- **:math:`\alpha = 0.05`** (:math:`5\%`): More lenient threshold - :math:`5\%`
  of random sequences would fail

**Decision Rule**:

- If p-value :math:`\geq \alpha`: Test **passes** (sequence appears random)
- If p-value :math:`< \alpha`: Test **fails** (sequence appears non-random)

**Mathematical Foundation**:

The significance level :math:`\alpha` controls the Type I error rate:

.. math::

   P(\text{reject } H_0 | H_0 \text{ is true}) = \alpha

**Trade-offs**:

- Lower :math:`\alpha` (e.g., :math:`0.01`): Fewer false positives, but more
  false negatives
- Higher :math:`\alpha` (e.g., :math:`0.05`): More false positives, but fewer
  false negatives

Null Hypothesis
~~~~~~~~~~~~~~~

The **null hypothesis** (denoted :math:`H_0`) is the hypothesis that the
sequence is random. Statistical tests are designed to detect deviations from
randomness.

**Mathematical Formulation**:

For most NIST tests, the null hypothesis can be stated as:

.. math::

   H_0: \text{The sequence is random}

with specific properties depending on the test. For example:

- **Frequency Test**: :math:`H_0: n_0 = n_1` (equal numbers of zeros and ones)
- **Runs Test**: :math:`H_0`: Number of runs follows expected distribution
- **Pattern Tests**: :math:`H_0`: Patterns occur with expected frequency

**Testing Process**:

1. Assume the sequence is random (null hypothesis :math:`H_0`)
2. Compute test statistic :math:`S`
3. Calculate p-value (probability of observing :math:`S` if :math:`H_0` were true)
4. If p-value is very small, reject null hypothesis (sequence appears non-random)

**Example**: For the frequency test, the null hypothesis is "the sequence has
equal numbers of :math:`0` s and :math:`1` s." The test checks if the observed
imbalance is too large to be due to chance.

Type I and Type II Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Type I Error (False Positive)**: Rejecting a random sequence as non-random.

- Occurs when p-value :math:`< \alpha` even though the sequence is actually
  random
- Probability of Type I error :math:`= \alpha` (the significance level)
- Example: A good RNG fails a test due to bad luck

**Type II Error (False Negative)**: Accepting a non-random sequence as random.

- Occurs when p-value :math:`\geq \alpha` even though the sequence is actually
  non-random
- Harder to control - depends on how non-random the sequence is
- Example: A biased RNG passes a test due to insufficient data

**Mathematical Formulation**:

- **Type I Error Rate**: :math:`P(\text{reject } H_0 | H_0 \text{ is true}) = \alpha`
- **Type II Error Rate**: :math:`P(\text{accept } H_0 | H_1 \text{ is true}) = \beta`

**Balancing Errors**:

- Lower :math:`\alpha` reduces Type I errors but increases Type II errors
- More data (longer sequences) reduces both types of errors
- The power of a test is :math:`1 - \beta`, the probability of correctly
  rejecting :math:`H_0` when :math:`H_1` is true

Test Suite
~~~~~~~~~~

A **test suite** is a collection of multiple tests applied to the same sequence.
A sequence should pass most (or all) tests to be considered random.

**Why Multiple Tests?**

- Different tests detect different types of non-randomness
- A single test might miss certain patterns or properties
- Multiple tests provide comprehensive evaluation
- Reduces the impact of Type I errors (false positives)

**Interpretation**:

- **All tests pass**: Strong evidence the sequence is random
- **Most tests pass**: Sequence appears mostly random (may have minor issues)
- **Many tests fail**: Strong evidence the sequence is non-random

**Note**: A single test failure does not necessarily mean the sequence is
non-random. Consider the overall pattern of results. For cryptographic
applications, sequences should pass all or nearly all tests.

The 15 NIST Tests
------------------

Test 1: Frequency (Monobit) Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests whether the number of zeros and ones in a sequence are
approximately equal, as expected for a random sequence.

**What it measures**: The balance of :math:`0` s and :math:`1` s in the entire
sequence.

**Mathematical Foundation**:

For a random binary sequence of length :math:`n`, we expect:
- :math:`E[n_0] = E[n_1] = n/2`
- The test statistic is:

.. math::

   S = \frac{n_1 - n_0}{\sqrt{n}}

Under the null hypothesis (random sequence), :math:`S` follows approximately a
standard normal distribution :math:`N(0, 1)` for large :math:`n` (by the Central
Limit Theorem).

**How it works**:

1. Count the number of ones (:math:`n_1`) and zeros (:math:`n_0`) in the sequence
2. Compute the test statistic: :math:`S = \frac{n_1 - n_0}{\sqrt{n}}`
3. Compute p-value using normal distribution: :math:`p = 2(1 - \Phi(|S|))`
4. Decision: Pass if :math:`p \geq \alpha`, fail if :math:`p < \alpha`

**Interpretation**:

- Random sequences should have roughly equal numbers of :math:`0` s and :math:`1` s
- If p-value :math:`< 0.01`, the sequence is significantly imbalanced
- This test detects sequences that are biased toward :math:`0` s or :math:`1` s

**Minimum sequence length**: :math:`100` bits (recommended: :math:`1000+` bits)

Test 2: Frequency Test within a Block
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests whether the frequency of ones in :math:`M`-bit blocks is
approximately :math:`M/2`, as expected for a random sequence.

**What it measures**: Local balance within blocks of the sequence.

**Mathematical Foundation**:

For a random sequence, each :math:`M`-bit block should have approximately
:math:`M/2` ones. The proportion of ones in block :math:`i` is:

.. math::

   \pi_i = \frac{\text{ones in block } i}{M}

Under the null hypothesis, :math:`\pi_i` should be approximately :math:`0.5` for
each block. The test uses a chi-square statistic:

.. math::

   \chi^2 = 4M \sum_{i=1}^{N} (\pi_i - 0.5)^2

where :math:`N` is the number of blocks. Under :math:`H_0`, this statistic
follows a chi-square distribution with :math:`N` degrees of freedom.

**How it works**:

1. Divide the sequence into :math:`N` blocks of :math:`M` bits each
2. For each block, compute the proportion of ones: :math:`\pi_i = \frac{\text{ones}}{M}`
3. Compute chi-square statistic: :math:`\chi^2 = 4M \sum_{i=1}^{N} (\pi_i - 0.5)^2`
4. Compute p-value using chi-square distribution: :math:`p = 1 - F_{\chi^2}(\chi^2, N)`
5. Decision: Pass if :math:`p \geq \alpha`, fail if :math:`p < \alpha`

**Interpretation**:

- Random sequences should have balanced blocks
- If p-value :math:`< 0.01`, some blocks are significantly imbalanced
- This test detects local biases in the sequence

**Parameters**:

- Block size (:math:`M`): Typically :math:`128` bits
- Minimum sequence length: :math:`M \times 10` (recommended: :math:`M \times 100`)

Test 3: Runs Test
~~~~~~~~~~~~~~~~~

**Purpose**: Tests whether the number of runs (consecutive identical bits) is as
expected for a random sequence.

**What it measures**: Oscillation between :math:`0` s and :math:`1` s in the
sequence.

**Mathematical Foundation**:

A **run** is a sequence of consecutive identical bits. For a random sequence of
length :math:`n` with :math:`n_0` zeros and :math:`n_1` ones, the expected
number of runs is:

.. math::

   E[R] = \frac{2n_0 n_1}{n_0 + n_1} + 1

The variance is:

.. math::

   \text{Var}(R) = \frac{2n_0 n_1(2n_0 n_1 - n_0 - n_1)}{(n_0 + n_1)^2(n_0 + n_1 - 1)}

The z-score is:

.. math::

   z = \frac{R - E[R]}{\sqrt{\text{Var}(R)}}

Under :math:`H_0`, :math:`z` follows approximately a standard normal distribution
:math:`N(0, 1)`.

**How it works**:

1. Count the total number of runs :math:`R` (transitions between :math:`0` and
   :math:`1`)
2. Count the number of zeros (:math:`n_0`) and ones (:math:`n_1`)
3. Compute expected runs: :math:`E[R] = \frac{2n_0 n_1}{n_0 + n_1} + 1`
4. Compute variance and z-score: :math:`z = \frac{R - E[R]}{\sqrt{\text{Var}(R)}}`
5. Compute p-value using normal distribution: :math:`p = 2(1 - \Phi(|z|))`
6. Decision: Pass if :math:`p \geq \alpha`, fail if :math:`p < \alpha`

**Interpretation**:

- Random sequences should have an appropriate number of runs
- Too few runs indicates clustering (e.g., :math:`00001111\ldots`)
- Too many runs indicates oscillation (e.g., :math:`01010101\ldots`)
- If p-value :math:`< 0.01`, the sequence has an abnormal number of runs

**Minimum sequence length**: :math:`100` bits (recommended: :math:`1000+` bits)

Test 4: Tests for Longest-Run-of-Ones in a Block
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests whether the longest run of ones within :math:`M`-bit blocks
is consistent with that expected for a random sequence.

**What it measures**: Maximum consecutive ones in blocks of the sequence.

**Mathematical Foundation**:

For a random :math:`M`-bit block, the probability distribution of the longest
run of ones follows a known distribution. The test compares observed
frequencies with expected frequencies using a chi-square test.

**How it works**:

1. Divide the sequence into :math:`N` blocks of :math:`M` bits each
2. For each block, find the longest run of consecutive ones
3. Count how many blocks fall into each category (based on longest run length)
4. Compare observed frequencies with expected frequencies using chi-square test
5. Compute p-value using chi-square distribution
6. Decision: Pass if :math:`p \geq \alpha`, fail if :math:`p < \alpha`

**Interpretation**:

- Random sequences should have longest runs distributed according to theory
- If p-value :math:`< 0.01`, the sequence has abnormal longest-run patterns
- This test detects sequences with unusually long or short runs of ones

**Parameters**:

Block size depends on sequence length:

- :math:`M = 8` for sequences :math:`\geq 128` bits
- :math:`M = 128` for sequences :math:`\geq 6272` bits
- :math:`M = 10000` for sequences :math:`\geq 750000` bits

Test 5: Binary Matrix Rank Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests for linear dependence among fixed length substrings of the
sequence.

**What it measures**: Linear independence of binary matrices formed from the
sequence.

**Mathematical Foundation**:

The test constructs :math:`M \times Q` binary matrices from the sequence and
computes their rank over :math:`\text{GF}(2)`. For a random sequence, the
expected proportion of full-rank matrices is approximately:

.. math::

   P(\text{rank} = M) \approx \prod_{i=0}^{M-1} (1 - 2^{i-Q})

The test uses a chi-square statistic to compare observed rank frequencies with
expected frequencies.

**How it works**:

1. Divide the sequence into :math:`N` matrices of size :math:`M \times Q`
2. For each matrix, compute its rank over :math:`\text{GF}(2)`
3. Count how many matrices have full rank (:math:`M`), rank (:math:`M-1`), or
   lower rank
4. Compare observed frequencies with expected frequencies using chi-square test
5. Compute p-value using chi-square distribution
6. Decision: Pass if :math:`p \geq \alpha`, fail if :math:`p < \alpha`

**Interpretation**:

- Random sequences should produce matrices with expected rank distribution
- If p-value :math:`< 0.01`, the sequence shows linear dependence patterns
- This test detects sequences with linear structure

**Parameters**:

- Matrix size: Typically :math:`32 \times 32`
- Minimum sequence length: :math:`M \times Q \times 38` (recommended: :math:`M \times Q \times 100`)

Test 6: Discrete Fourier Transform (Spectral) Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Detects periodic features in the sequence that would indicate a
deviation from the assumption of randomness.

**What it measures**: Periodic patterns using Fourier analysis (frequency domain).

**Mathematical Foundation**:

The test converts the sequence to values :math:`-1` and :math:`+1` (:math:`0
\rightarrow -1`, :math:`1 \rightarrow +1`) and computes the Discrete Fourier
Transform (DFT):

.. math::

   X(k) = \sum_{j=0}^{n-1} x_j e^{-2\pi i j k / n}

where :math:`x_j \in \{-1, +1\}`. For a random sequence, the modulus
:math:`|X(k)|` should be below a threshold :math:`T` for approximately
:math:`95\%` of coefficients. The test counts how many coefficients are below
:math:`T` and compares with the expected :math:`95\%`.

**How it works**:

1. Convert sequence to values :math:`-1` and :math:`+1` (:math:`0 \rightarrow -1`,
   :math:`1 \rightarrow +1`)
2. Compute Discrete Fourier Transform (DFT) of the sequence
3. Compute the modulus :math:`|X(k)|` of each DFT coefficient
4. Count how many coefficients are below threshold :math:`T` (expected:
   :math:`95\%` for random)
5. Compute p-value using normal distribution approximation
6. Decision: Pass if :math:`p \geq \alpha`, fail if :math:`p < \alpha`

**Interpretation**:

- Random sequences should not have periodic patterns
- If p-value :math:`< 0.01`, the sequence shows periodic features
- This test detects sequences with repeating patterns

**Minimum sequence length**: :math:`1000` bits (recommended: :math:`10000+` bits)

Test 7: Non-overlapping Template Matching Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests for occurrences of specific :math:`m`-bit patterns
(templates) in the sequence. Detects over-represented patterns that would
indicate non-randomness.

**What it measures**: Frequency of specific :math:`m`-bit patterns in
non-overlapping blocks.

**Mathematical Foundation**:

For a random sequence, the expected number of occurrences of an :math:`m`-bit
pattern in :math:`N` non-overlapping blocks of :math:`M` bits is:

.. math::

   E[\text{matches}] = \frac{N(M - m + 1)}{2^m}

The test uses a chi-square statistic to compare observed frequency with expected
frequency.

**How it works**:

1. Divide the sequence into non-overlapping blocks of :math:`M` bits
2. For each block, check if it matches the template pattern
3. Count the number of matches
4. Compare observed frequency with expected frequency using chi-square test
5. Compute p-value using chi-square distribution
6. Decision: Pass if :math:`p \geq \alpha`, fail if :math:`p < \alpha`

**Interpretation**:

- Random sequences should not have over-represented patterns
- If p-value :math:`< 0.01`, the sequence shows pattern clustering
- This test detects sequences with specific repeating patterns

**Parameters**:

- Template: The :math:`m`-bit pattern to search for (default: :math:`9`-bit pattern)
- Block size (:math:`M`): Typically :math:`8` bits

Test 8: Overlapping Template Matching Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Similar to Test 7, but searches for overlapping occurrences of a
template pattern. Detects pattern clustering that would indicate non-randomness.

**What it measures**: Frequency of overlapping :math:`m`-bit patterns in blocks.

**Mathematical Foundation**:

For overlapping patterns, the expected number of occurrences in a block of
:math:`M` bits is:

.. math::

   E[\text{occurrences}] = \frac{M - m + 1}{2^m}

The test counts how many blocks have :math:`k` occurrences (:math:`k = 0, 1, 2,
\ldots`) and compares with expected frequencies using a chi-square test.

**How it works**:

1. Divide the sequence into :math:`N` blocks of :math:`M` bits each
2. For each block, count overlapping occurrences of the template
3. Count how many blocks have :math:`k` occurrences (:math:`k = 0, 1, 2, \ldots`)
4. Compare observed frequencies with expected frequencies using chi-square test
5. Compute p-value using chi-square distribution
6. Decision: Pass if :math:`p \geq \alpha`, fail if :math:`p < \alpha`

**Interpretation**:

- Random sequences should have template occurrences distributed according to theory
- If p-value :math:`< 0.01`, the sequence shows pattern clustering
- This test detects sequences with clustered patterns

**Parameters**:

- Template: The :math:`m`-bit pattern to search for (default: :math:`9` ones)
- Block size (:math:`M`): Typically :math:`1032` bits

Test 9: Maurer's "Universal Statistical" Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests whether the sequence can be significantly compressed without
loss of information. A random sequence should not be compressible.

**What it measures**: Compressibility of the sequence (ability to predict future
bits from past bits).

**Mathematical Foundation**:

The test divides the sequence into blocks of :math:`L` bits and uses the first
:math:`Q` blocks to initialize a table of block positions. For each subsequent
block, it computes the distance to its last occurrence. The test statistic is:

.. math::

   f_n = \frac{1}{K} \sum_{i=Q+1}^{Q+K} \log_2(\text{distance to last occurrence})

where :math:`K` is the number of blocks after initialization. For a random
sequence, :math:`f_n` should be close to the expected value. The test uses a
normal approximation to compute the p-value.

**How it works**:

1. Divide the sequence into blocks of :math:`L` bits
2. Use first :math:`Q` blocks to initialize a table of block positions
3. For each subsequent block, compute the distance to its last occurrence
4. Compute the test statistic from these distances
5. Compute p-value using normal distribution
6. Decision: Pass if :math:`p \geq \alpha`, fail if :math:`p < \alpha`

**Interpretation**:

- Random sequences should not be compressible
- If p-value :math:`< 0.01`, the sequence shows compressibility (non-random)
- This test detects sequences with predictable patterns

**Parameters**:

- Block size (:math:`L`): Typically :math:`6` bits
- Initialization blocks (:math:`Q`): Typically :math:`10` blocks

Test 10: Linear Complexity Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests whether the sequence is complex enough to be considered
random. Sequences with low linear complexity are predictable and non-random.

**What it measures**: Linear complexity of blocks using the Berlekamp-Massey
algorithm.

**Mathematical Foundation**:

The linear complexity :math:`L(s)` of a sequence :math:`s` is the length of the
shortest LFSR that can generate it. For a random sequence of length :math:`M`,
the expected linear complexity is approximately:

.. math::

   E[L(s)] \approx \frac{M}{2} + \frac{4 + \varepsilon(M)}{18}

where :math:`\varepsilon(M)` is a small correction term. The test computes
deviations from expected complexity and uses a chi-square test to compare
observed distribution with expected distribution.

**How it works**:

1. Divide the sequence into :math:`N` blocks of :math:`M` bits each
2. For each block, compute the linear complexity using Berlekamp-Massey
3. Compute deviations from expected complexity
4. Compare observed distribution with expected distribution using chi-square test
5. Compute p-value using chi-square distribution
6. Decision: Pass if :math:`p \geq \alpha`, fail if :math:`p < \alpha`

**Interpretation**:

- Random sequences should have high linear complexity
- If p-value :math:`< 0.01`, the sequence has lower complexity than expected
- This test detects sequences that are too predictable

**Parameters**:

- Block size (:math:`M`): Typically :math:`500` bits

Test 11: Serial Test
~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests whether the number of occurrences of :math:`2^m` :math:`m`-bit
overlapping patterns is approximately the same as would be expected for a random
sequence.

**What it measures**: Frequency distribution of :math:`m`-bit overlapping patterns.

**Mathematical Foundation**:

For a random sequence, all :math:`2^m` possible :math:`m`-bit patterns should
occur with approximately equal frequency. The test computes chi-square statistics
for pattern frequencies at lengths :math:`m`, :math:`m-1`, and :math:`m-2`:

.. math::

   \chi^2_m = \frac{2^m}{n} \sum_{i=0}^{2^m-1} (v_i - n/2^m)^2

where :math:`v_i` is the frequency of pattern :math:`i`. The test statistic is:

.. math::

   \Delta^2_m = \chi^2_m - \chi^2_{m-1}

**How it works**:

1. Count occurrences of all possible :math:`m`-bit patterns (overlapping)
2. Count occurrences of all possible :math:`(m-1)`-bit patterns
3. Count occurrences of all possible :math:`(m-2)`-bit patterns
4. Compute chi-square statistics for each pattern length
5. Compute test statistic :math:`\Delta^2_m = \chi^2_m - \chi^2_{m-1}`
6. Compute p-value using chi-square distribution
7. Decision: Pass if :math:`p \geq \alpha`, fail if :math:`p < \alpha`

**Interpretation**:

- Random sequences should have uniform pattern distribution
- If p-value :math:`< 0.01`, the sequence shows non-uniform pattern distribution
- This test detects sequences with pattern bias

**Parameters**:

- Pattern length (:math:`m`): Typically :math:`2` bits

**Minimum sequence length**: :math:`2^m \times 100` bits

Test 12: Approximate Entropy Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests the frequency of all possible overlapping :math:`m`-bit
patterns. Compares the frequency of overlapping blocks of two consecutive
lengths (:math:`m` and :math:`m+1`) against the expected result for a random
sequence.

**What it measures**: Entropy (randomness) of overlapping patterns.

**Mathematical Foundation**:

The approximate entropy is defined as:

.. math::

   \text{ApEn}(m) = \phi^{(m)} - \phi^{(m+1)}

where:

.. math::

   \phi^{(m)} = \frac{1}{2^m} \sum_{i=0}^{2^m-1} \frac{C_i^{(m)}}{n-m+1} \log_2\left(\frac{C_i^{(m)}}{n-m+1}\right)

and :math:`C_i^{(m)}` is the count of pattern :math:`i` of length :math:`m`. For
a random sequence, :math:`\text{ApEn}(m)` should be close to :math:`0`. The test
uses a chi-square statistic to compare observed entropy with expected entropy.

**How it works**:

1. Count occurrences of all possible :math:`m`-bit patterns
2. Count occurrences of all possible :math:`(m+1)`-bit patterns
3. Compute approximate entropy from pattern frequencies
4. Compute chi-square statistic
5. Compute p-value using chi-square distribution
6. Decision: Pass if :math:`p \geq \alpha`, fail if :math:`p < \alpha`

**Interpretation**:

- Random sequences should have high entropy (uniform pattern distribution)
- If p-value :math:`< 0.01`, the sequence shows low entropy (non-random)
- This test detects sequences with pattern bias

**Parameters**:

- Pattern length (:math:`m`): Typically :math:`2` bits

**Minimum sequence length**: :math:`2^m \times 10` bits

Test 13: Cumulative Sums (Cusum) Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests whether the cumulative sum of the partial sequences occurring
in the tested sequence is too large or too small relative to what would be
expected for a random sequence.

**What it measures**: Maximum deviation of cumulative sums from zero.

**Mathematical Foundation**:

The test converts the sequence to :math:`-1, +1` (:math:`0 \rightarrow -1`, :math:`1 \rightarrow +1`) and computes cumulative sums:

.. math::

   S_k = \sum_{i=0}^{k-1} x_i

where :math:`x_i \in \{-1, +1\}`. For a random sequence, :math:`S_k` should stay
close to zero. The test finds the maximum absolute cumulative sum:

.. math::

   z = \max_{0 \leq k \leq n} |S_k|

and uses a normal approximation to compute the p-value.

**How it works**:

1. Convert sequence to :math:`-1, +1` (:math:`0 \rightarrow -1`, :math:`1 \rightarrow +1`)
2. Compute cumulative sums :math:`S_k = \sum_{i=0}^{k-1} x_i`
3. Find maximum absolute cumulative sum :math:`z = \max_{0 \leq k \leq n} |S_k|`
4. Compute p-value using normal distribution approximation
5. Decision: Pass if :math:`p \geq \alpha`, fail if :math:`p < \alpha`

**Interpretation**:

- Random sequences should have cumulative sums that stay close to zero
- If p-value :math:`< 0.01`, the sequence shows significant bias in cumulative sums
- This test detects sequences with long runs or trends

**Parameters**:

- Mode: "forward" or "backward" (default: "forward")

**Minimum sequence length**: :math:`100` bits

Test 14: Random Excursions Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests the number of cycles having exactly :math:`K` visits in a
cumulative sum random walk. The test detects deviations from the expected number
of visits to various states in the random walk.

**What it measures**: Distribution of visits to states in a random walk.

**Mathematical Foundation**:

The test converts the sequence to :math:`-1, +1` and computes cumulative sums
(random walk). For a random walk, the expected number of visits to state
:math:`x` in a cycle (return to zero) follows a known distribution. The test
uses chi-square statistics to compare observed visit frequencies with expected
frequencies for states :math:`x \in \{-4, -3, -2, -1, +1, +2, +3, +4\}`.

**How it works**:

1. Convert sequence to :math:`-1, +1` (:math:`0 \rightarrow -1`, :math:`1 \rightarrow +1`)
2. Compute cumulative sums (random walk)
3. Identify cycles (return to zero)
4. Count visits to each state (:math:`-4, -3, -2, -1, +1, +2, +3, +4`)
5. Compute chi-square statistic for each state
6. Compute p-value using chi-square distribution
7. Decision: Pass if :math:`p \geq \alpha`, fail if :math:`p < \alpha`

**Interpretation**:

- Random sequences should have expected distribution of state visits
- If p-value :math:`< 0.01`, the sequence shows non-random state visit distribution
- This test detects sequences with bias in random walk behavior

**Minimum sequence length**: :math:`1000` bits (recommended: :math:`10000+` bits)

Test 15: Random Excursions Variant Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Tests the total number of times that a particular state is visited
in a cumulative sum random walk. This is a variant of Test 14 that focuses on
the total number of visits rather than the distribution of visits per cycle.

**What it measures**: Total number of visits to each state in a random walk.

**Mathematical Foundation**:

Similar to Test 14, but focuses on total visits rather than visits per cycle.
The test counts total visits to states :math:`x \in \{-9, -8, \ldots, -1, +1,
\ldots, +8, +9\}` (excluding :math:`0`) and compares with expected frequencies
using chi-square tests.

**How it works**:

1. Convert sequence to :math:`-1, +1` (:math:`0 \rightarrow -1`, :math:`1 \rightarrow +1`)
2. Compute cumulative sums (random walk)
3. Count total visits to each state (:math:`-9` to :math:`+9`, excluding :math:`0`)
4. Compute chi-square statistic for each state
5. Compute p-value using chi-square distribution
6. Decision: Pass if :math:`p \geq \alpha`, fail if :math:`p < \alpha`

**Interpretation**:

- Random sequences should have expected total visits to each state
- If p-value :math:`< 0.01`, the sequence shows non-random state visit counts
- This test detects sequences with bias in random walk behavior

**Minimum sequence length**: :math:`1000` bits (recommended: :math:`10000+` bits)

Mathematical Background
-----------------------

P-value Computation
~~~~~~~~~~~~~~~~~~~~

For most NIST tests, p-values are computed using standard statistical
distributions:

**Normal Distribution**: Used for tests with z-scores (e.g., frequency test,
runs test)

- Two-tailed test: :math:`p = 2 \times (1 - \Phi(|z|))`
- One-tailed test: :math:`p = 1 - \Phi(z)` or :math:`p = \Phi(z)`

where :math:`\Phi(z)` is the cumulative distribution function of the standard
normal distribution.

**Chi-square Distribution**: Used for tests comparing observed vs expected
frequencies

- :math:`p = 1 - F_{\chi^2}(\chi^2, \text{df})`

where :math:`F_{\chi^2}` is the chi-square CDF and :math:`\text{df}` is the
degrees of freedom.

**Special Distributions**: Some tests use specialized distributions (e.g., rank
test uses a distribution specific to matrix ranks over :math:`\text{GF}(2)`).

Statistical Significance
~~~~~~~~~~~~~~~~~~~~~~~~

A test **passes** if:

- p-value :math:`\geq` significance_level (typically :math:`\geq 0.01`)

A test **fails** if:

- p-value :math:`<` significance_level (typically :math:`< 0.01`)

**Note**: A single test failure does not necessarily mean the sequence is
non-random. The suite should be interpreted as a whole, not individual tests.
For cryptographic applications, sequences should pass all or nearly all tests.

Central Limit Theorem
~~~~~~~~~~~~~~~~~~~~~

Many NIST tests rely on the Central Limit Theorem (CLT), which states that the
sum of a large number of independent, identically distributed random variables
approaches a normal distribution. This allows tests to use normal approximations
for test statistics computed from sequences.

For example, in the frequency test, the test statistic:

.. math::

   S = \frac{n_1 - n_0}{\sqrt{n}}

follows approximately a standard normal distribution :math:`N(0, 1)` for large
:math:`n` by the CLT, even though the underlying distribution is binomial.

Chi-square Tests
~~~~~~~~~~~~~~~~~

Chi-square tests are used to compare observed frequencies with expected
frequencies. The chi-square statistic is:

.. math::

   \chi^2 = \sum_{i=1}^{k} \frac{(O_i - E_i)^2}{E_i}

where :math:`O_i` is the observed frequency in category :math:`i`, :math:`E_i`
is the expected frequency, and :math:`k` is the number of categories. Under
the null hypothesis, :math:`\chi^2` follows a chi-square distribution with
:math:`k-1` degrees of freedom (or fewer, depending on constraints).

Glossary
--------

**Binary Sequence**
   A sequence of bits (:math:`0` s and :math:`1` s) that should appear random.

**Chi-square Distribution**
   A statistical distribution used for testing whether observed frequencies
   match expected frequencies. Denoted :math:`\chi^2_k` where :math:`k` is the
   degrees of freedom.

**Cryptographic Randomness**
   Randomness properties required for cryptographic applications, including
   unpredictability and statistical randomness.

**Degrees of Freedom (df)**
   A parameter of statistical distributions (e.g., chi-square) that determines
   the shape of the distribution. Often related to the number of independent
   observations or categories.

**Expected Value (E[X])**
   The theoretical average value of a random variable. For a random binary
   sequence, we expect equal numbers of :math:`0` s and :math:`1` s.

**False Negative**
   See Type II Error.

**False Positive**
   See Type I Error.

**Frequency**
   The number of times a particular value (e.g., :math:`0` or :math:`1`)
   appears in a sequence.

**GF(2)**
   The Galois field of order :math:`2`, also known as the binary field.
   Arithmetic operations are performed modulo :math:`2`.

**Hypothesis Testing**
   A statistical procedure for making decisions about whether data supports a
   particular hypothesis (e.g., "the sequence is random").

**Matrix Rank**
   The maximum number of linearly independent rows (or columns) in a matrix.
   Over :math:`\text{GF}(2)`, rank indicates linear independence in binary
   space.

**Normal Distribution**
   A bell-shaped probability distribution, also called Gaussian distribution.
   Denoted :math:`N(\mu, \sigma^2)` where :math:`\mu` is the mean and
   :math:`\sigma^2` is the variance.

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
   A sequence of consecutive identical bits (e.g., "000" is a run of zeros of
   length :math:`3`).

**Significance Level (α)**
   The threshold for rejecting the null hypothesis. Common values are :math:`0.01`
   (:math:`1\%`) or :math:`0.05` (:math:`5\%`).

**Statistical Test**
   A mathematical procedure that evaluates whether a sequence exhibits
   properties expected of a random sequence.

**Test Statistic**
   A numerical value computed from the sequence that is used to make a decision
   about randomness.

**Type I Error**
   Rejecting a random sequence as non-random (false positive). Probability equals
   the significance level :math:`\alpha`.

**Type II Error**
   Accepting a non-random sequence as random (false negative). Probability
   depends on how non-random the sequence is.

**Variance**
   A measure of how spread out values are. For a random variable :math:`X`,
   variance is :math:`\text{Var}(X) = E[(X - E[X])^2]`.

**Z-score**
   A standardized value indicating how many standard deviations an observation is
   from the mean. :math:`z = \frac{X - \mu}{\sigma}`.

Further Reading
----------------

**Primary Reference**:

- **Rukhin, A., et al.** (2010). "A Statistical Test Suite for Random and
  Pseudorandom Number Generators for Cryptographic Applications" (NIST Special
  Publication 800-22 Revision 1a). National Institute of Standards and
  Technology. Available at: https://csrc.nist.gov/publications/detail/sp/800-22/rev-1a/final

**Statistical Theory**:

- **Casella, G., & Berger, R. L.** (2002). "Statistical Inference" (2nd ed.).
  Duxbury Press. Comprehensive treatment of statistical inference, including
  hypothesis testing, p-values, and test statistics.

- **Wasserman, L.** (2004). "All of Statistics: A Concise Course in Statistical
  Inference". Springer. Concise introduction to statistical theory with
  emphasis on practical applications.

- **Lehmann, E. L., & Romano, J. P.** (2005). "Testing Statistical Hypotheses"
  (3rd ed.). Springer. Advanced treatment of hypothesis testing theory.

**Probability Theory**:

- **Feller, W.** (1968). "An Introduction to Probability Theory and Its
  Applications" (3rd ed., Vol. 1). Wiley. Classic introduction to probability
  theory, including distributions used in statistical tests.

- **Billingsley, P.** (1995). "Probability and Measure" (3rd ed.). Wiley.
  Advanced treatment of probability theory and measure theory.

**Random Number Generation**:

- **Knuth, D. E.** (1997). "The Art of Computer Programming, Volume 2:
  Seminumerical Algorithms" (3rd ed.). Addison-Wesley. Comprehensive treatment
  of random number generation, including statistical testing.

- **L'Ecuyer, P.** (2012). "Random Number Generation". In "Handbook of
  Computational Statistics" (2nd ed.), Springer. Modern treatment of random
  number generation and testing.

**Cryptography**:

- **Menezes, A. J., van Oorschot, P. C., & Vanstone, S. A.** (1996). "Handbook
  of Applied Cryptography". CRC Press. Chapter 5 covers random number
  generation and testing in cryptographic context.

- **Stinson, D. R., & Paterson, M. B.** (2018). "Cryptography: Theory and
  Practice" (4th ed.). CRC Press. Modern treatment of cryptography including
  randomness requirements.

**Linear Complexity and Berlekamp-Massey**:

- **Massey, J. L.** (1969). "Shift-Register Synthesis and BCH Decoding". IEEE
  Transactions on Information Theory, 15(1), 122-127. Original paper on the
  Berlekamp-Massey algorithm.

- **Rueppel, R. A.** (1986). "Analysis and Design of Stream Ciphers".
  Springer. Treatment of linear complexity and its applications to stream
  ciphers.

**Fourier Analysis**:

- **Bracewell, R. N.** (2000). "The Fourier Transform and Its Applications"
  (3rd ed.). McGraw-Hill. Introduction to Fourier analysis, including Discrete
  Fourier Transform.

**Matrix Theory**:

- **Horn, R. A., & Johnson, C. R.** (2012). "Matrix Analysis" (2nd ed.).
  Cambridge University Press. Comprehensive treatment of matrix theory,
  including rank computation.
