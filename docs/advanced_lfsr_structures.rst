Advanced LFSR Structures
=========================

This section provides a comprehensive guide to advanced LFSR structures beyond
basic linear feedback shift registers. The documentation is designed to be
accessible to beginners while providing sufficient depth for researchers and
developers.

Introduction
------------

**What are Advanced LFSR Structures?**

**Advanced LFSR structures** extend beyond basic linear feedback shift registers
to include non-linear feedback, filtering functions, clock control, and multiple
outputs. These structures are used in real-world cryptographic applications to
increase security and complexity while maintaining the efficiency of LFSRs.

**Why Use Advanced LFSR Structures?**

1. **Increased Security**: Non-linearity and irregular clocking make cryptanalysis
   more difficult
2. **Real-World Applications**: Many cryptographic systems use advanced structures
3. **Educational Value**: Understanding how LFSRs are extended in practice
4. **Research Capability**: Enabling analysis of complex generator designs

**Advanced Structures Covered**:

This documentation covers analysis of the following advanced LFSR structures:

- **Non-Linear Feedback LFSRs (NFSRs)**: LFSRs with non-linear feedback functions
- **Filtered LFSRs**: LFSRs with non-linear filtering functions applied to state
- **Clock-Controlled LFSRs**: LFSRs with irregular clocking patterns
- **Multi-Output LFSRs**: LFSRs that produce multiple output bits per step
- **Irregular Clocking Patterns**: Advanced clock control mechanisms

Key Concepts
------------

Non-Linear Feedback
~~~~~~~~~~~~~~~~~~~

**What is Non-Linear Feedback?**

**Non-linear feedback** uses non-linear operations (AND, OR, etc.) in the feedback
function, rather than only linear operations (XOR). This generalizes LFSRs to
NFSRs (Non-Linear Feedback Shift Registers).

**Key Terminology**:

- **Non-Linear Feedback Shift Register (NFSR)**: A shift register with a
  non-linear feedback function. Unlike LFSRs, the feedback function can use AND,
  OR, and other non-linear operations.

- **Non-Linear Feedback Function**: A function that computes the new state bit
  from the current state using non-linear operations. This function is not
  linear (cannot be expressed as a linear combination of state bits).

- **Non-Linearity**: The property of a function that cannot be expressed as a
  linear combination of its inputs. Non-linearity is essential for cryptographic
  security.

- **Feedback Function**: The function that determines the new state bit from
  the current state. In NFSRs, this function is non-linear.

- **Non-Linear Complexity**: A measure of the non-linearity in the feedback
  function. Higher non-linear complexity generally provides better security.

**Mathematical Foundation**:

An NFSR of degree d has state S = (s_0, s_1, ..., s_{d-1}) and feedback function
f: GF(q)^d → GF(q). The state update is:

.. math::

   s_{new} = f(s_0, s_1, \\ldots, s_{d-1})

where f is a non-linear function.

For binary NFSRs (GF(2)), common non-linear operations include:
- AND: a ∧ b
- OR: a ∨ b
- XOR: a ⊕ b (linear)
- Combinations of the above

Filtered LFSRs
~~~~~~~~~~~~~~

**What is a Filtered LFSR?**

A **filtered LFSR** applies a non-linear filtering function to the LFSR state to
produce output. This provides non-linearity while maintaining the efficiency of
LFSRs.

**Key Terminology**:

- **Filtered LFSR**: An LFSR with a non-linear filtering function applied to the
  state. The filter function maps the LFSR state to output bits, providing
  non-linearity in the output.

- **Filter Function**: A non-linear function that maps LFSR state to output bits.
  The filter function determines which state bits are used and how they are
  combined.

- **Algebraic Immunity**: The minimum degree of a non-zero annihilator of the
  filter function. Higher algebraic immunity provides better resistance to
  algebraic attacks.

- **Correlation Immunity**: The property that the output is uncorrelated with
  any subset of input bits. Higher correlation immunity provides better
  resistance to correlation attacks.

- **Non-Linear Filtering**: Applying a non-linear function to state bits to
  produce output, rather than using state bits directly.

**Mathematical Foundation**:

A filtered LFSR has:
- Base LFSR with state S = (s_0, s_1, ..., s_{d-1})
- Filter function f: GF(q)^d → GF(q)

The output at step i is:

.. math::

   y_i = f(S_i)

where S_i is the LFSR state at step i.

Clock-Controlled LFSRs
~~~~~~~~~~~~~~~~~~~~~~

**What is a Clock-Controlled LFSR?**

A **clock-controlled LFSR** has irregular clocking, where the LFSR doesn't always
advance on each step. Clocking is controlled by a clock control function or
another LFSR.

**Key Terminology**:

- **Clock-Controlled LFSR**: An LFSR with irregular clocking, where the LFSR
  doesn't always advance on each step. Clocking is controlled by a clock control
  function or another LFSR.

- **Clock Control Function**: A function that determines when the LFSR advances.
  The function may depend on the LFSR's own state or on an external control signal.

- **Irregular Clocking**: Clocking pattern that is not regular (not every step).
  The LFSR may advance 0, 1, or more steps depending on the clock control.

- **Clock Control LFSR**: A separate LFSR that controls the clocking of another
  LFSR. The output of the control LFSR determines when the data LFSR advances.

- **Stop-and-Go**: A clock control pattern where the LFSR stops when control bit
  is 0 and advances when control bit is 1.

- **Step-1/Step-2**: A clock control pattern where the LFSR advances 1 or 2 steps
  based on the control bit.

**Mathematical Foundation**:

A clock-controlled LFSR has:
- Base LFSR with state S
- Clock control function c: determines number of steps to advance

The state update is:

.. math::

   S_{i+1} = C^{c(S_i)} \\cdot S_i

where C is the state update matrix and c(S_i) is the number of steps to advance.

Multi-Output LFSRs
~~~~~~~~~~~~~~~~~~

**What is a Multi-Output LFSR?**

A **multi-output LFSR** produces multiple output bits per step, rather than a
single bit. This increases the output rate and can improve efficiency.

**Key Terminology**:

- **Multi-Output LFSR**: An LFSR that produces multiple output bits per step,
  rather than a single bit. This increases the output rate and can improve
  efficiency.

- **Output Function**: A function that maps LFSR state to multiple output bits.
  The output function determines which state bits are used and how they are
  combined.

- **Output Rate**: The number of bits output per clock step. A standard LFSR
  has output rate 1, while a multi-output LFSR may have output rate 2, 3, or more.

- **Parallel Output**: Multiple bits output simultaneously from the same state.
  This is different from clocking multiple times to get multiple bits.

- **Output Positions**: The positions in the state vector used for output.
  Multi-output LFSRs typically use multiple state positions for output.

**Mathematical Foundation**:

A multi-output LFSR has:
- Base LFSR with state S = (s_0, s_1, ..., s_{d-1})
- Output function f: GF(q)^d → GF(q)^k (maps state to k output bits)

The output at step i is:

.. math::

   Y_i = f(S_i) = (y_{i,0}, y_{i,1}, \\ldots, y_{i,k-1})

where k is the output rate (number of bits per step).

Irregular Clocking Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**What are Irregular Clocking Patterns?**

**Irregular clocking patterns** are specific patterns that determine when and
how many steps an LFSR advances. Common patterns include stop-and-go, step-1/step-2,
and others.

**Key Terminology**:

- **Irregular Clocking Pattern**: A specific pattern determining clocking behavior.
  Common patterns include stop-and-go, step-1/step-2, and others.

- **Stop-and-Go**: Clock control pattern where LFSR stops (0 steps) when control
  bit is 0 and advances (1 step) when control bit is 1.

- **Step-1/Step-2**: Clock control pattern where LFSR advances 1 step if control
  bit is 0, else 2 steps.

- **Shrinking Generator**: Pattern where LFSR advances only when control bit is 1,
  and output is produced only when control bit is 1.

- **Self-Shrinking Generator**: Pattern where LFSR controls its own clocking based
  on its own state.

API Reference
-------------

The advanced LFSR structures are implemented in the :mod:`lfsr.advanced` module.
See :doc:`api/advanced` for complete API documentation.

Command-Line Usage
------------------

Advanced LFSR structure analysis can be performed from the command line:

**Basic Usage**:

.. code-block:: bash

   lfsr-seq --advanced-structure nonlinear --analyze-structure

**Generate Sequence**:

.. code-block:: bash

   lfsr-seq --advanced-structure filtered --generate-sequence --length 1000

**CLI Options**:
- ``--advanced-structure TYPE``: Select structure type (nonlinear, filtered, clock_controlled, multi_output, irregular_clocking)
- ``--analyze-structure``: Analyze structure properties
- ``--generate-sequence``: Generate sequence from initial state
- ``--structure-params``: Structure-specific parameters (JSON format)

Python API Usage
----------------

Here's a simple example demonstrating advanced LFSR structure analysis:

.. code-block:: python

   from lfsr.advanced import NFSR, FilteredLFSR, ClockControlledLFSR
   from lfsr.attacks import LFSRConfig
   
   # Create base LFSR
   base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
   
   # Non-linear feedback LFSR
   def nfsr_feedback(state):
       return (state[0] & state[1]) ^ state[2]
   
   nfsr = NFSR(base_lfsr, nfsr_feedback)
   sequence = nfsr.generate_sequence([1, 0, 1, 1], 100)
   
   # Filtered LFSR
   def filter_func(state):
       return (state[0] & state[1]) ^ state[2]
   
   filtered = FilteredLFSR(base_lfsr, filter_func)
   sequence2 = filtered.generate_sequence([1, 0, 1, 1], 100)
   
   # Clock-controlled LFSR
   def clock_control(state):
       return 1 if state[0] == 1 else 0
   
   cclfsr = ClockControlledLFSR(base_lfsr, clock_control)
   sequence3 = cclfsr.generate_sequence([1, 0, 1, 1], 100)

Glossary
--------

**Advanced LFSR Structure**
   Extension of basic linear LFSRs with non-linearity, filtering, clock control, or multiple outputs.

**Algebraic Immunity**
   Minimum degree of a non-zero annihilator of a function.

**Clock Control Function**
   Function determining when LFSR advances.

**Clock-Controlled LFSR**
   LFSR with irregular clocking controlled by a function.

**Correlation Immunity**
   Property that output is uncorrelated with input subsets.

**Filter Function**
   Non-linear function mapping LFSR state to output bits.

**Filtered LFSR**
   LFSR with non-linear filtering function applied to state.

**Irregular Clocking**
   Clocking pattern that is not regular (not every step).

**Multi-Output LFSR**
   LFSR producing multiple output bits per step.

**Non-Linear Feedback**
   Feedback function using non-linear operations (AND, OR, etc.).

**Non-Linear Feedback Shift Register (NFSR)**
   Shift register with non-linear feedback function.

**Non-Linearity**
   Property that function cannot be expressed as linear combination.

**Output Function**
   Function mapping LFSR state to multiple output bits.

**Output Rate**
   Number of bits output per clock step.

**Step-1/Step-2**
   Clock control pattern: 1 step if control bit is 0, else 2 steps.

**Stop-and-Go**
   Clock control pattern: 0 steps if control bit is 0, else 1 step.

Further Reading
---------------

- Menezes, A. J., et al. (1996). "Handbook of Applied Cryptography"

- Rueppel, R. A. (1986). "Analysis and Design of Stream Ciphers"

- Golomb, S. W. (1982). "Shift Register Sequences"

- Massey, J. L. (1969). "Shift-Register Synthesis and BCH Decoding"
