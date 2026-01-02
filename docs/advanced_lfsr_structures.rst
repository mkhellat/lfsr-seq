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
keystream bits (where :math:`d` is the degree). To address this, cryptographers
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

   f(S) = c_0 S_0 \\oplus c_1 S_1 \\oplus \\ldots \\oplus c_{d-1} S_{d-1}

where ⊕ is XOR (exclusive OR) and c_i are coefficients. The feedback is ALWAYS
linear - this is what makes it an LFSR.

**NFSR (Non-Linear Feedback Shift Register)**:

An NFSR has NON-LINEAR feedback. The feedback function can include non-linear
operations:

.. math::

   f(S) = \\text{linear terms} + \\text{non-linear terms}

where non-linear terms can include AND operations (S_i ∧ S_j), OR operations,
or other non-linear functions. NFSRs are NOT LFSRs - they are a different structure.

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
linear, but the output is filtered through a non-linear function.

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
- **Output**: y_i = f(S_i) where f is the non-linear filter function

The filter function f: F_q^d → F_q maps the d-bit state to a single output bit.

**Security Properties**:

- **Algebraic Immunity**: Minimum degree of non-zero annihilator
- **Correlation Immunity**: Order m if output is uncorrelated with any m state bits
- **Non-Linearity**: Measure of distance from linear functions

Clock-Controlled LFSRs
~~~~~~~~~~~~~~~~~~~~~~

**What is a Clock-Controlled LFSR?**

A **clock-controlled LFSR** is an LFSR (with LINEAR feedback) that has irregular
clocking patterns. The feedback remains linear, but the LFSR doesn't always advance
on each step.

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
- **Clock Control**: clock = c(S_control) where c is the control function
- **Advancement**: Main LFSR advances only when clock = 1

**Common Patterns**:

- **Stop-and-Go**: Advance if control bit = 1, stop if control bit = 0
- **Step-1/Step-2**: Advance 1 step if control=0, 2 steps if control=1
- **Shrinking**: Output used only when control=1, otherwise discarded

Multi-Output LFSRs
~~~~~~~~~~~~~~~~~~

**What is a Multi-Output LFSR?**

A **multi-output LFSR** is an LFSR (with LINEAR feedback) that produces multiple
output bits per step, rather than a single bit. The feedback remains linear, but
multiple state bits are output simultaneously.

**Key Terminology**:

- **Multi-Output LFSR**: An LFSR (linear feedback) with multiple outputs per step
- **Linear Feedback**: The LFSR feedback is still linear (XOR only)
- **Output Function**: Function mapping state to multiple output bits
- **Output Rate**: Number of bits output per clock step
- **Parallel Output**: Multiple bits output simultaneously from the same state

**Mathematical Foundation**:

For a multi-output LFSR:
- **LFSR State Update**: Linear (XOR of tap bits)
- **Output**: (y_0, y_1, ..., y_{k-1}) = f(S_i) where f produces k bits

**Advantages**:

- **Increased Output Rate**: k bits per step instead of 1
- **Efficiency**: Faster keystream generation
- **Flexibility**: Can output different combinations of state bits

Irregular Clocking Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**What is Irregular Clocking?**

**Irregular clocking** is a clocking pattern that is not regular (not every step).
An LFSR with irregular clocking has LINEAR feedback, but advances a variable number
of steps per output.

**Key Terminology**:

- **Irregular Clocking**: Clocking pattern that is not regular
- **Linear Feedback**: The LFSR feedback is still linear (XOR only)
- **Clocking Pattern Function**: Function determining number of steps to advance
- **Variable Steps**: LFSR may advance 0, 1, 2, or more steps per output

**Common Patterns**:

- **Stop-and-Go**: 0 steps if control=0, 1 step if control=1
- **Step-1/Step-2**: 1 step if control=0, 2 steps if control=1
- **Variable Step**: Number of steps determined by control value

NFSRs (Non-Linear Feedback Shift Registers)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**What is an NFSR?**

An **NFSR (Non-Linear Feedback Shift Register)** is a shift register with NON-LINEAR
feedback. NFSRs are NOT LFSRs - they are a different structure.

**CRITICAL**: If feedback is non-linear, it is NOT an LFSR. It is an NFSR.

**Key Terminology**:

- **NFSR**: Non-Linear Feedback Shift Register (NOT an LFSR)
- **Non-Linear Feedback**: Feedback function includes AND, OR, or other non-linear operations
- **Linear Terms**: XOR operations in feedback (like LFSR)
- **Non-Linear Terms**: AND, OR operations in feedback (not in LFSR)
- **Non-Linear Complexity**: Measure of non-linearity in feedback

**Mathematical Foundation**:

For an NFSR, the feedback includes non-linear terms:

.. math::

   f(S) = \\sum_{i} c_i S_i + \\sum_{i,j} d_{i,j} (S_i \\land S_j) + \\ldots

where the first sum is linear (XOR) and the second sum is non-linear (AND).

**Security Properties**:

- **Non-Linearity**: Provides resistance to linear attacks
- **Complexity**: Higher non-linear complexity generally provides better security
- **Analysis Difficulty**: More complex to analyze than LFSRs

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
       return state[0] ^ state[1] ^ (state[2] & state[3])
   filtered = FilteredLFSR(base_lfsr, filter_func)
   sequence = filtered.generate_sequence([1, 0, 0, 0], 100)
   
   # NFSR (NOT an LFSR - non-linear feedback)
   def nfsr_feedback(state):
       linear = state[0] ^ state[3]  # Linear part
       nonlinear = state[1] & state[2]  # Non-linear part
       return linear ^ nonlinear
   nfsr = NFSR(base_lfsr, nfsr_feedback)
   sequence2 = nfsr.generate_sequence([1, 0, 0, 0], 100)

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

- Menezes, A. J., et al. (1996). "Handbook of Applied Cryptography"

- Rueppel, R. A. (1986). "Analysis and Design of Stream Ciphers"

- Golic, J. D. (1996). "On the Security of Nonlinear Filter Generators"

- Siegenthaler, T. (1985). "Decrypting a Class of Stream Ciphers Using Ciphertext Only"
