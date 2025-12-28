Advanced LFSR Structures
========================

This section provides a comprehensive guide to advanced LFSR structures that
extend beyond basic linear feedback shift registers. The documentation is
designed to be accessible to beginners while providing sufficient depth for
researchers and developers.

Introduction
------------

**What are Advanced LFSR Structures?**

**Advanced LFSR structures** extend beyond basic linear feedback shift registers
to include non-linear feedback, filtering functions, clock control, and multiple
outputs. These structures are used in real-world cryptographic applications to
increase security and complexity beyond what simple linear LFSRs can provide.

**Why Use Advanced LFSR Structures?**

1. **Increased Security**: Non-linearity breaks linearity weaknesses of LFSRs
2. **Real-World Applications**: Many cryptographic systems use advanced structures
3. **Educational Value**: Understanding how LFSRs are extended in practice
4. **Research Capability**: Enabling analysis of complex generator designs

**Advanced Structures Covered**:

This documentation covers analysis of the following advanced LFSR structures:

- **Non-Linear Feedback LFSRs (NFSRs)**: LFSRs with non-linear feedback functions
- **Filtered LFSRs**: LFSRs with non-linear filtering functions
- **Clock-Controlled LFSRs**: LFSRs with irregular clocking patterns
- **Multi-Output LFSRs**: LFSRs producing multiple output bits per step
- **Irregular Clocking Patterns**: Advanced clock control mechanisms

Key Concepts
------------

Non-Linear Feedback
~~~~~~~~~~~~~~~~~~~

**What is Non-Linear Feedback?**

**Non-linear feedback** extends LFSRs by allowing non-linear operations (AND,
OR, etc.) in the feedback function, in addition to XOR. This creates NFSRs
(Non-Linear Feedback Shift Registers).

**Key Terminology**:

- **NFSR (Non-Linear Feedback Shift Register)**: Generalization of LFSR where
  feedback function is not linear. Uses non-linear operations (AND, OR, etc.)
  in addition to XOR.

- **Non-Linear Feedback**: Feedback function that includes non-linear operations.
  Unlike linear feedback (XOR only), non-linear feedback can use AND, OR, and
  other Boolean operations.

- **Feedback Function**: Function computing the new state bit from current state.
  In LFSRs, this is linear (XOR of tap bits). In NFSRs, this includes
  non-linear operations.

- **Non-Linear Complexity**: Measure of non-linearity in the feedback function.
  Higher non-linear complexity generally provides better security.

**Mathematical Foundation**:

For an LFSR, the feedback is linear:

.. math::

   f(S) = c_0 S_0 \\oplus c_1 S_1 \\oplus \\ldots \\oplus c_{d-1} S_{d-1}

For an NFSR, the feedback includes non-linear terms:

.. math::

   f(S) = \\text{linear terms} + \\text{non-linear terms}

where non-linear terms can include products (AND operations) like
:math:`S_i \\land S_j`.

Filtered LFSRs
~~~~~~~~~~~~~~

**What is a Filtered LFSR?**

A **filtered LFSR** applies a non-linear filtering function to the LFSR state
to produce output bits. This breaks the linearity of the LFSR and provides
security against linear attacks.

**Key Terminology**:

- **Filtered LFSR**: An LFSR with a non-linear filtering function applied to
  the state. The filter function maps the LFSR state to output bits, providing
  non-linearity in the output.

- **Filter Function**: Non-linear function mapping LFSR state to output bits.
  The filter function takes state bits as input and produces output bits.

- **Algebraic Immunity**: Resistance to algebraic attacks. Higher algebraic
  immunity means the filter function is more resistant to algebraic attacks.
  The algebraic immunity of a Boolean function f is the minimum degree of a
  non-zero annihilator of f or (1+f).

- **Correlation Immunity**: Resistance to correlation attacks. A filter function
  is correlation immune of order m if the output is uncorrelated with any m
  state bits. This means that knowing m state bits provides no information
  about the output.

**Mathematical Foundation**:

For a filtered LFSR, the output is:

.. math::

   y_i = f(S_i)

where :math:`S_i` is the LFSR state at step i and :math:`f` is the filter function.

The filter function :math:`f: \\mathbb{F}_q^d \\rightarrow \\mathbb{F}_q` maps
the d-bit state to a single output bit.

Clock-Controlled LFSRs
~~~~~~~~~~~~~~~~~~~~~~~

**What is a Clock-Controlled LFSR?**

A **clock-controlled LFSR** has irregular clocking, where the LFSR doesn't always
advance on each step. Clocking is controlled by a clock control function or
another LFSR.

**Key Terminology**:

- **Clock-Controlled LFSR**: An LFSR with irregular clocking, where the LFSR
  doesn't always advance on each step. Clocking is controlled by a clock
  control function or another LFSR.

- **Clock Control Function**: Function determining when the LFSR advances. The
  function takes the current state (or control LFSR output) and returns whether
  to clock.

- **Irregular Clocking**: Clocking pattern that is not regular (not every step).
  The LFSR may advance 0, 1, or more steps per output.

- **Control LFSR**: Separate LFSR that controls the clocking of the main LFSR.
  The control LFSR output determines when the main LFSR advances.

- **Stop-and-Go**: Pattern where LFSR stops when control bit is 0, advances
  when control bit is 1.

**Mathematical Foundation**:

For a clock-controlled LFSR, the clocking is determined by a control function:

.. math::

   \\text{clock} = c(S_{\\text{control}})

where :math:`c` is the clock control function and :math:`S_{\\text{control}}`
is the control state (or control LFSR output).

The main LFSR advances only when :math:`\\text{clock} = 1`.

Multi-Output LFSRs
~~~~~~~~~~~~~~~~~~

**What is a Multi-Output LFSR?**

A **multi-output LFSR** produces multiple output bits per step, rather than a
single bit. This increases the output rate and efficiency.

**Key Terminology**:

- **Multi-Output LFSR**: An LFSR that produces multiple output bits per step,
  rather than a single bit. This increases the output rate.

- **Output Function**: Function mapping LFSR state to output bits. For
  multi-output LFSRs, this function produces multiple bits.

- **Output Rate**: Number of bits output per clock step. A multi-output LFSR
  with rate k outputs k bits per step.

- **Parallel Output**: Multiple bits output simultaneously from the same state.

**Mathematical Foundation**:

For a multi-output LFSR, the output is:

.. math::

   (y_0, y_1, \\ldots, y_{k-1}) = f(S_i)

where :math:`S_i` is the LFSR state at step i and :math:`f` is the output
function producing k bits.

Irregular Clocking Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**What are Irregular Clocking Patterns?**

**Irregular clocking patterns** determine how many steps an LFSR advances per
output, creating irregularity in the sequence generation.

**Key Terminology**:

- **Irregular Clocking**: Clocking pattern that is not regular (not every step).
  The LFSR may advance 0, 1, or more steps per output.

- **Stop-and-Go**: Pattern where LFSR stops when control bit is 0, advances
  when control bit is 1. The LFSR advances 1 step when control=1, 0 steps when
  control=0.

- **Step-1/Step-2**: Pattern where LFSR advances 1 step when control bit is 0,
  advances 2 steps when control bit is 1.

- **Shrinking Generator**: Pattern where LFSR output is used only when control
  bit is 1, otherwise discarded. This is a variant of irregular clocking.

**Mathematical Foundation**:

For irregular clocking, the number of steps advanced is determined by a
control function:

.. math::

   \\text{steps} = f(c)

where :math:`c` is the control value and :math:`f` is the clocking function.

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
- ``--sequence-length N``: Length of sequence to generate

Python API Usage
----------------

Here's a simple example demonstrating advanced LFSR structures using the Python API:

.. code-block:: python

   from lfsr.attacks import LFSRConfig
   from lfsr.advanced import (
       create_simple_nfsr,
       create_simple_filtered_lfsr,
       create_stop_and_go_lfsr
   )
   
   # Base LFSR configuration
   base = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
   
   # Non-linear feedback LFSR
   nfsr = create_simple_nfsr(base, nonlinear_terms=[(1, 2)])
   sequence = nfsr.generate_sequence([1, 0, 0, 0], 100)
   
   # Filtered LFSR
   filtered = create_simple_filtered_lfsr(
       base,
       filter_taps=[0, 1, 2],
       nonlinear_terms=[(2, 3)]
   )
   sequence2 = filtered.generate_sequence([1, 0, 0, 0], 100)
   
   # Clock-controlled LFSR
   control = LFSRConfig(coefficients=[1, 1], field_order=2, degree=2)
   cclfsr = create_stop_and_go_lfsr(base, control)
   sequence3 = cclfsr.generate_sequence([1, 0, 0, 0], 100, [1, 0])

Glossary
--------

**Advanced LFSR Structure**
   Extension of basic linear LFSRs with non-linear feedback, filtering,
   clock control, or multiple outputs.

**Algebraic Immunity**
   Resistance to algebraic attacks. Minimum degree of a non-zero annihilator.

**Clock Control Function**
   Function determining when an LFSR advances in irregular clocking.

**Clock-Controlled LFSR**
   LFSR with irregular clocking controlled by a function or another LFSR.

**Control LFSR**
   Separate LFSR controlling the clocking of the main LFSR.

**Correlation Immunity**
   Resistance to correlation attacks. Output is uncorrelated with state bits.

**Filter Function**
   Non-linear function mapping LFSR state to output bits.

**Filtered LFSR**
   LFSR with non-linear filtering function applied to state.

**Irregular Clocking**
   Clocking pattern that is not regular (not every step).

**Multi-Output LFSR**
   LFSR producing multiple output bits per step.

**NFSR (Non-Linear Feedback Shift Register)**
   Generalization of LFSR with non-linear feedback function.

**Non-Linear Feedback**
   Feedback function including non-linear operations (AND, OR, etc.).

**Output Function**
   Function mapping LFSR state to output bits.

**Output Rate**
   Number of bits output per clock step.

**Parallel Output**
   Multiple bits output simultaneously from the same state.

**Shrinking Generator**
   Pattern where LFSR output is used only when control bit is 1.

**Step-1/Step-2**
   Pattern where LFSR advances 1 step if control=0, 2 steps if control=1.

**Stop-and-Go**
   Pattern where LFSR stops if control=0, advances if control=1.

Further Reading
---------------

- Menezes, A. J., et al. (1996). "Handbook of Applied Cryptography"

- Rueppel, R. A. (1986). "Analysis and Design of Stream Ciphers"

- Golic, J. D. (1996). "On the Security of Nonlinear Filter Generators"

- Meier, W., & Staffelbach, O. (1989). "Fast Correlation Attacks on Stream Ciphers"
