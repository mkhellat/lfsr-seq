Advanced LFSR Structures
=========================

This section provides a comprehensive introduction to advanced LFSR structures,
extending beyond basic linear feedback shift registers. The documentation is
designed to be accessible to beginners while providing sufficient depth for
researchers and developers. We begin with intuitive explanations and gradually
build to rigorous mathematical formulations.

**CRITICAL TERMINOLOGY CLARIFICATION**:

Before proceeding, it is essential to understand the fundamental distinction:

- **LFSR (Linear Feedback Shift Register)**: The feedback function is ALWAYS linear
  (XOR operations only). This is the definition of LFSR. If feedback is non-linear,
  it is NOT an LFSR.

- **NFSR (Non-Linear Feedback Shift Register)**: The feedback function includes
  non-linear operations (AND, OR, etc.). NFSRs are NOT LFSRs - they are a different
  structure that generalizes LFSRs.

- **Filtered/Clock-Controlled/Multi-Output LFSRs**: These ARE LFSRs (linear feedback)
  with additional features (non-linear filtering on output, irregular clocking,
  multiple outputs). The feedback remains linear.

Introduction
------------

**What are Advanced LFSR Structures?**

Advanced LFSR structures extend beyond basic linear feedback shift registers to
include non-linear filtering, clock control, multiple outputs, and irregular
clocking patterns. These structures are used in real-world cryptographic
applications to increase security and complexity while maintaining the efficiency
benefits of LFSRs.

**Historical Context and Motivation**

Basic LFSRs have a fundamental weakness: their linearity makes them vulnerable to
the Berlekamp-Massey algorithm, which can recover the LFSR from just :math:`2d`
keystream bits, where :math:`d` is the degree of the LFSR. This vulnerability
motivated the development of advanced structures that introduce non-linearity. To address this, cryptographers
developed advanced structures that introduce non-linearity while preserving LFSR
efficiency.

Filtered LFSRs emerged in the 1980s as a way to add non-linearity through output
filtering. Clock-controlled LFSRs (like those in A5/1) use irregular clocking to
introduce non-linearity. NFSRs (Non-Linear Feedback Shift Registers) generalize
LFSRs by allowing non-linear feedback, as seen in Grain and Trivium.

**Why Use Advanced Structures?**

1. **Security**: Non-linearity breaks linearity weaknesses of basic LFSRs
   - Prevents Berlekamp-Massey algorithm from recovering the structure
   - Increases resistance to linear and algebraic attacks
   - Provides better security properties (algebraic immunity, correlation immunity)

2. **Efficiency**: Multi-output LFSRs increase output rate
   - Generate multiple bits per clock step
   - Maintain hardware efficiency of LFSRs
   - Useful for high-speed applications

3. **Irregularity**: Clock control introduces unpredictability
   - Irregular clocking patterns prevent simple analysis
   - Introduces non-linearity without changing feedback structure
   - Used in real-world ciphers (A5/1, LILI-128)

4. **Real-World Applications**: Many cryptographic systems use these structures
   - A5/1 (GSM): Clock-controlled LFSRs
   - Grain: LFSR + NFSR hybrid
   - Trivium: Non-linear feedback shift registers
   - LILI-128: Clock-controlled LFSRs

**Structure Types Covered**:

- **NFSRs**: Non-Linear Feedback Shift Registers (NOT LFSRs)
- **Filtered LFSRs**: LFSRs with non-linear output filtering (ARE LFSRs)
- **Clock-Controlled LFSRs**: LFSRs with irregular clocking (ARE LFSRs)
- **Multi-Output LFSRs**: LFSRs with multiple outputs per step (ARE LFSRs)
- **Irregular Clocking Patterns**: LFSRs with variable clocking (ARE LFSRs)

Key Concepts
------------

Fundamental Distinction: LFSR vs NFSR
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**LFSR (Linear Feedback Shift Register)**:

An LFSR has LINEAR feedback. The feedback function computes the new state bit as:

.. math::

   f(S) = c_0 S_0 \oplus c_1 S_1 \oplus \cdots \oplus c_{d-1} S_{d-1}

where :math:`\oplus` is XOR (exclusive OR), :math:`c_i \in \mathbb{F}_q` are
coefficients, :math:`S_i` are state bits, and :math:`d` is the degree. The
feedback is ALWAYS linear - this is what makes it an LFSR.

**NFSR (Non-Linear Feedback Shift Register)**:

An NFSR has NON-LINEAR feedback. The feedback function can include non-linear
operations:

.. math::

   f(S) = \text{linear terms} + \text{non-linear terms}

where linear terms are XOR operations (like LFSR) and non-linear terms can
include AND operations (:math:`S_i \land S_j`), OR operations (:math:`S_i \lor
S_j`), or other non-linear functions. NFSRs are NOT LFSRs - they are a different
structure.

**Key Terminology**:

- **Linear Feedback**: Feedback function uses only XOR operations (linear)
- **Non-Linear Feedback**: Feedback function uses AND, OR, or other non-linear operations
- **LFSR**: Shift register with LINEAR feedback (always)
- **NFSR**: Shift register with NON-LINEAR feedback (not an LFSR)

Filtered LFSRs
~~~~~~~~~~~~~~

**What is a Filtered LFSR?**

A **filtered LFSR** is an LFSR (with LINEAR feedback) where a non-linear filtering
function is applied to the state to produce output bits. The LFSR feedback remains
linear, but the output is filtered through a non-linear function. This design
pattern was introduced in the 1980s to add non-linearity while maintaining LFSR
efficiency.

**Historical Context**:

Filtered LFSRs emerged as a response to the vulnerability of basic LFSRs to the
Berlekamp-Massey algorithm. By applying a non-linear filter function to the LFSR
state, designers could break linearity while preserving the efficiency benefits
of LFSRs. This design pattern is used in many stream ciphers, including academic
designs and some deployed systems.

**Key Terminology**:

- **Filtered LFSR**: An LFSR (linear feedback) with non-linear output filtering
- **Filter Function**: Non-linear function mapping LFSR state to output bits
- **Linear Feedback**: The LFSR feedback is still linear (XOR only)
- **Non-Linear Output**: The output is filtered through a non-linear function
- **Algebraic Immunity**: Resistance to algebraic attacks (property of filter function)
- **Correlation Immunity**: Resistance to correlation attacks (property of filter function)

**Mathematical Foundation**:

For a filtered LFSR:
- **LFSR State Update**: Linear (XOR of tap bits)
- **Output**: :math:`y_i = f(S_i)` where :math:`f` is the non-linear filter function

The filter function :math:`f: \mathbb{F}_q^d \rightarrow \mathbb{F}_q` maps the
:math:`d`-bit state to a single output bit. The LFSR state update remains linear:

.. math::

   S_{i+1} = (S_{i,1}, S_{i,2}, \ldots, S_{i,d-1}, f_{\text{LFSR}}(S_i))

where :math:`f_{\text{LFSR}}` is the linear feedback function, but the output is:

.. math::

   y_i = f_{\text{filter}}(S_i)

where :math:`f_{\text{filter}}` is the non-linear filter function.

**Security Properties**:

- **Algebraic Immunity**: Minimum degree :math:`\text{AI}(f)` of non-zero
  annihilator :math:`g` such that :math:`f \cdot g = 0` or :math:`(1+f) \cdot g =
  0`. Higher algebraic immunity provides better resistance to algebraic attacks.

- **Correlation Immunity**: Order :math:`m` if output is uncorrelated with any
  :math:`m` state bits. A function is :math:`m`-th order correlation immune if
  the output is statistically independent of any :math:`m` state bits.

- **Non-Linearity**: Measure of distance from linear functions. The non-linearity
  :math:`\text{NL}(f)` is the minimum Hamming distance from :math:`f` to any
  affine function. Higher non-linearity provides better resistance to linear
  attacks.

Clock-Controlled LFSRs
~~~~~~~~~~~~~~~~~~~~~~

**What is a Clock-Controlled LFSR?**

A **clock-controlled LFSR** is an LFSR (with LINEAR feedback) that has irregular
clocking patterns. The feedback remains linear, but the LFSR doesn't always advance
on each step. This design pattern introduces non-linearity through irregular
clocking, making the output sequence non-linear even though the feedback function
itself remains linear.

**Historical Context**:

Clock-controlled LFSRs were developed to introduce non-linearity without modifying
the feedback structure. This design pattern is used in real-world ciphers like A5/1
(GSM) and LILI-128. The irregular clocking prevents simple linear analysis while
maintaining the efficiency of LFSR state updates.

**Key Terminology**:

- **Clock-Controlled LFSR**: An LFSR (linear feedback) with irregular clocking
- **Linear Feedback**: The LFSR feedback is still linear (XOR only)
- **Irregular Clocking**: The LFSR doesn't always advance (clock control)
- **Clock Control Function**: Function determining when the LFSR advances
- **Control LFSR**: Separate LFSR that controls the clocking of the main LFSR
- **Stop-and-Go**: Pattern where LFSR stops when control=0, advances when control=1

**Mathematical Foundation**:

For a clock-controlled LFSR:
- **LFSR State Update**: Linear (XOR of tap bits) - when it advances
- **Clock Control**: :math:`\text{clock} = c(S_{\text{control}})` where :math:`c`
  is the control function and :math:`S_{\text{control}}` is the control state
- **Advancement**: Main LFSR advances only when :math:`\text{clock} = 1`

The clock control mechanism introduces non-linearity through irregular clocking.
At each step, the control function determines whether the main LFSR advances:

.. math::

   S_{i+1} = \begin{cases}
     f_{\text{LFSR}}(S_i) & \text{if } c(S_{\text{control}}) = 1 \\
     S_i & \text{if } c(S_{\text{control}}) = 0
   \end{cases}

where :math:`f_{\text{LFSR}}` is the linear feedback function.

**Common Patterns**:

- **Stop-and-Go**: Advance if control bit :math:`= 1`, stop if control bit
  :math:`= 0`. This is the simplest clock control pattern.

- **Step-1/Step-2**: Advance :math:`1` step if :math:`\text{control} = 0`, :math:`2`
  steps if :math:`\text{control} = 1`. This provides more variation in clocking.

- **Shrinking**: Output used only when :math:`\text{control} = 1`, otherwise
  discarded. This creates irregular output patterns.

- **Variable Step**: Number of steps determined by control value. For example, if
  control outputs :math:`k`, the LFSR advances :math:`k` steps.

Multi-Output LFSRs
~~~~~~~~~~~~~~~~~~

**What is a Multi-Output LFSR?**

A **multi-output LFSR** is an LFSR (with LINEAR feedback) that produces multiple
output bits per step, rather than a single bit. The feedback remains linear, but
multiple state bits are output simultaneously. This design pattern increases the
output rate without changing the feedback structure.

**Historical Context**:

Multi-output LFSRs were developed for applications requiring high keystream
generation rates. By outputting multiple bits per clock step, these structures
can achieve :math:`k`-fold speedup compared to single-output LFSRs, where :math:`k`
is the number of output bits per step.

**Key Terminology**:

- **Multi-Output LFSR**: An LFSR (linear feedback) with multiple outputs per step
- **Linear Feedback**: The LFSR feedback is still linear (XOR only)
- **Output Function**: Function mapping state to multiple output bits
- **Output Rate**: Number of bits output per clock step
- **Parallel Output**: Multiple bits output simultaneously from the same state

**Mathematical Foundation**:

For a multi-output LFSR:
- **LFSR State Update**: Linear (XOR of tap bits)
- **Output**: :math:`(y_0, y_1, \ldots, y_{k-1}) = f(S_i)` where :math:`f` produces
  :math:`k` bits

The output function :math:`f: \mathbb{F}_q^d \rightarrow \mathbb{F}_q^k` maps the
:math:`d`-bit state to :math:`k` output bits. This increases the output rate from
:math:`1` bit per step to :math:`k` bits per step.

**Advantages**:

- **Increased Output Rate**: :math:`k` bits per step instead of :math:`1`, providing
  :math:`k`-fold speedup in keystream generation
- **Efficiency**: Faster keystream generation for applications requiring high
  throughput
- **Flexibility**: Can output different combinations of state bits, allowing
  customization of output patterns

Irregular Clocking Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**What is Irregular Clocking?**

**Irregular clocking** is a clocking pattern that is not regular (not every step).
An LFSR with irregular clocking has LINEAR feedback, but advances a variable number
of steps per output. This introduces non-linearity through the clocking mechanism
rather than the feedback function.

**Historical Context**:

Irregular clocking patterns were developed to address the linearity weakness of
basic LFSRs. By making the clocking pattern depend on control signals (often from
another LFSR), designers can introduce non-linearity while maintaining linear
feedback. This approach is used in ciphers like A5/1 and LILI-128.

**Key Terminology**:

- **Irregular Clocking**: Clocking pattern that is not regular
- **Linear Feedback**: The LFSR feedback is still linear (XOR only)
- **Clocking Pattern Function**: Function determining number of steps to advance
- **Variable Steps**: LFSR may advance 0, 1, 2, or more steps per output

**Common Patterns**:

- **Stop-and-Go**: :math:`0` steps if :math:`\text{control} = 0`, :math:`1` step if
  :math:`\text{control} = 1`
- **Step-1/Step-2**: :math:`1` step if :math:`\text{control} = 0`, :math:`2` steps
  if :math:`\text{control} = 1`
- **Variable Step**: Number of steps determined by control value. If control
  outputs :math:`k`, the LFSR advances :math:`k` steps.

NFSRs (Non-Linear Feedback Shift Registers)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**What is an NFSR?**

An **NFSR (Non-Linear Feedback Shift Register)** is a shift register with NON-LINEAR
feedback. NFSRs are NOT LFSRs - they are a different structure that generalizes
LFSRs by allowing non-linear operations in the feedback function.

**CRITICAL**: If feedback is non-linear, it is NOT an LFSR. It is an NFSR.

**Historical Context**:

NFSRs emerged as a generalization of LFSRs, allowing non-linear feedback to
provide better security properties. Modern stream ciphers like Grain and Trivium
use NFSRs (or hybrid LFSR/NFSR designs) to achieve high security while
maintaining hardware efficiency. NFSRs provide resistance to linear attacks but
are more complex to analyze and design than LFSRs.

**Key Terminology**:

- **NFSR**: Non-Linear Feedback Shift Register (NOT an LFSR)
- **Non-Linear Feedback**: Feedback function includes AND, OR, or other non-linear operations
- **Linear Terms**: XOR operations in feedback (like LFSR)
- **Non-Linear Terms**: AND, OR operations in feedback (not in LFSR)
- **Non-Linear Complexity**: Measure of non-linearity in feedback

**Mathematical Foundation**:

For an NFSR, the feedback includes non-linear terms:

.. math::

   f(S) = \sum_{i} c_i S_i + \sum_{i,j} d_{i,j} (S_i \land S_j) + \cdots

where the first sum is linear (XOR operations, like LFSR) and the second sum is
non-linear (AND operations). Additional non-linear terms can include higher-order
products :math:`S_i \land S_j \land S_k`, OR operations, or other non-linear
functions.

The linear part :math:`\sum_{i} c_i S_i` (where addition is XOR in
:math:`\mathbb{F}_2`) provides the efficiency of LFSRs, while the non-linear part
:math:`\sum_{i,j} d_{i,j} (S_i \land S_j) + \cdots` provides resistance to linear
attacks.

**Security Properties**:

- **Non-Linearity**: Provides resistance to linear attacks. The non-linear terms
  prevent simple linear analysis that works for LFSRs.

- **Complexity**: Higher non-linear complexity generally provides better security.
  The non-linear complexity measures the minimum number of non-linear operations
  needed to represent the feedback function.

- **Analysis Difficulty**: More complex to analyze than LFSRs. While this provides
  security benefits, it also makes design and verification more challenging.

- **Trade-offs**: NFSRs provide better security than LFSRs but may be less
  efficient in hardware due to non-linear operations (AND gates are typically
  slower than XOR gates).

API Reference
-------------

The advanced LFSR structures are implemented in the :mod:`lfsr.advanced` module.
See :doc:`api/advanced` for complete API documentation.

Command-Line Usage
------------------

Advanced LFSR structure analysis can be performed from the command line:

**Basic Usage**:

.. code-block:: bash

   lfsr-seq --advanced-structure filtered --analyze-structure

**Generate Sequence**:

.. code-block:: bash

   lfsr-seq --advanced-structure nfsr --generate-sequence --length 1000

**CLI Options**:
- ``--advanced-structure TYPE``: Select structure type (nfsr, filtered, clock_controlled, multi_output, irregular)
- ``--analyze-structure``: Analyze structure properties
- ``--generate-sequence``: Generate sequence from initial state
- ``--sequence-length N``: Length of sequence to generate

Python API Usage
----------------

Here's a simple example demonstrating advanced LFSR structures:

.. code-block:: python

   from lfsr.attacks import LFSRConfig
   from lfsr.advanced import FilteredLFSR, NFSR
   
   # Base LFSR configuration
   base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
   
   # Filtered LFSR (IS an LFSR with non-linear filter)
   def filter_func(state):
       # Non-linear filter: XOR of first two bits AND third and fourth bits
       return state[0] ^ state[1] ^ (state[2] & state[3])
   filtered = FilteredLFSR(base_lfsr, filter_func)
   sequence = filtered.generate_sequence([1, 0, 0, 0], 100)
   print(f"Filtered LFSR sequence: {sequence[:10]}...")
   
   # NFSR (NOT an LFSR - non-linear feedback)
   def nfsr_feedback(state):
       linear = state[0] ^ state[3]  # Linear part (like LFSR)
       nonlinear = state[1] & state[2]  # Non-linear part (AND operation)
       return linear ^ nonlinear
   nfsr = NFSR(base_lfsr, nfsr_feedback)
   sequence2 = nfsr.generate_sequence([1, 0, 0, 0], 100)
   print(f"NFSR sequence: {sequence2[:10]}...")
   
   # Clock-controlled LFSR (IS an LFSR with irregular clocking)
   from lfsr.advanced import ClockControlledLFSR
   def clock_control(control_state):
       return control_state[0]  # Simple stop-and-go
   clocked = ClockControlledLFSR(base_lfsr, clock_control)
   sequence3 = clocked.generate_sequence([1, 0, 0, 0], 100)
   print(f"Clock-controlled LFSR sequence: {sequence3[:10]}...")

Glossary
--------

**Algebraic Immunity**
   Resistance to algebraic attacks (property of filter functions).

**Clock Control Function**
   Function determining when an LFSR advances in clock-controlled structures.

**Clock-Controlled LFSR**
   An LFSR (linear feedback) with irregular clocking patterns.

**Control LFSR**
   Separate LFSR that controls the clocking of another LFSR.

**Correlation Immunity**
   Resistance to correlation attacks (property of filter functions).

**Filter Function**
   Non-linear function mapping LFSR state to output bits.

**Filtered LFSR**
   An LFSR (linear feedback) with non-linear output filtering.

**Irregular Clocking**
   Clocking pattern that is not regular (variable steps per output).

**LFSR (Linear Feedback Shift Register)**
   Shift register with LINEAR feedback (XOR only). This is the definition.

**Multi-Output LFSR**
   An LFSR (linear feedback) that produces multiple output bits per step.

**NFSR (Non-Linear Feedback Shift Register)**
   Shift register with NON-LINEAR feedback. NOT an LFSR - different structure.

**Non-Linear Feedback**
   Feedback function that includes non-linear operations (AND, OR, etc.).

**Output Function**
   Function mapping LFSR state to output bits (can be linear or non-linear).

**Output Rate**
   Number of bits output per clock step.

**Stop-and-Go**
   Clocking pattern where LFSR stops when control=0, advances when control=1.

**Step-1/Step-2**
   Clocking pattern where LFSR advances 1 step if control=0, 2 steps if control=1.

Further Reading
---------------

**Filtered LFSRs**:

- **Golic, J. D.** (1996). "On the Security of Nonlinear Filter Generators". Fast
  Software Encryption 1996. Analysis of filtered LFSR security properties.

- **Courtois, N. T., & Meier, W.** (2003). "Algebraic Attacks on Stream Ciphers
  with Linear Feedback". Advances in Cryptology - EUROCRYPT 2003. Algebraic
  attacks on filtered LFSRs.

**Clock-Controlled LFSRs**:

- **Siegenthaler, T.** (1985). "Decrypting a Class of Stream Ciphers Using
  Ciphertext Only". IEEE Transactions on Information Theory, 31(1), 81-85. Early
  analysis of clock-controlled LFSRs.

- **Golic, J. D.** (1996). "On the Security of Clock-Controlled Shift Registers".
  Fast Software Encryption 1995. Security analysis of clock-controlled structures.

**NFSRs and Hybrid Designs**:

- **Hell, M., Johansson, T., & Meier, W.** (2006). "Grain: A Stream Cipher for
  Constrained Environments". eSTREAM Project Report. Hybrid LFSR/NFSR design.

- **De Cannière, C., & Preneel, B.** (2006). "Trivium: A Stream Cipher
  Construction Inspired by Block Cipher Design Principles". Selected Areas in
  Cryptography 2006. NFSR-based design.

**General Theory**:

- **Menezes, A. J., van Oorschot, P. C., & Vanstone, S. A.** (1996). "Handbook
  of Applied Cryptography". CRC Press. Chapter 6 covers LFSRs and advanced
  structures.

- **Rueppel, R. A.** (1986). "Analysis and Design of Stream Ciphers". Springer.
  Comprehensive treatment of LFSR-based stream cipher design, including filtered
  and clock-controlled structures.

- **Golomb, S. W.** (1967). "Shift Register Sequences". Holden-Day. Foundational
  work on LFSR theory and sequences.
