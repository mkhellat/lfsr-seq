Mathematical Background
========================

Linear Feedback Shift Registers
--------------------------------

A Linear Feedback Shift Register (LFSR) is a shift register whose input bit
is a linear function of its previous state. LFSRs are widely used in
cryptography, error detection, and pseudorandom number generation.

State Update Matrix
-------------------

The state of an LFSR can be represented as a vector, and the state transition
can be represented by a matrix multiplication:

.. math::

   S_{i+1} = S_i \cdot C

where :math:`S_i` is the current state vector and :math:`C` is the state
update matrix (companion matrix).

Characteristic Polynomial
--------------------------

The characteristic polynomial of the state update matrix determines many
properties of the LFSR, including:

- The period of the LFSR
- The number of distinct sequences
- The structure of state cycles

Period Calculation
------------------

The period of an LFSR is the smallest positive integer :math:`n` such that:

.. math::

   C^n = I

where :math:`I` is the identity matrix. This represents the length of the
cycle before the LFSR returns to its initial state.

Finite Fields
-------------

LFSRs operate over finite fields (Galois fields) GF(p) or GF(p^n), where:

- :math:`p` is a prime number
- :math:`n` is a positive integer

The field order determines the possible values for coefficients and state
elements.

Berlekamp-Massey Algorithm
---------------------------

The Berlekamp-Massey algorithm is used to find the shortest LFSR that can
generate a given sequence. It has applications in:

- Cryptanalysis
- Error correction codes
- Sequence synthesis

Linear Complexity
-----------------

The linear complexity of a sequence is the length of the shortest LFSR that
can generate it. This is an important measure of the "randomness" or
"complexity" of a sequence.

References
----------

- Tanja Lange's Cryptology Course: https://www.hyperelliptic.org/tanja/teaching/CS22/
- SageMath Documentation: https://doc.sagemath.org/
- Golomb, S. W. (1967). Shift Register Sequences

