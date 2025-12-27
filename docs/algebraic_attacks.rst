Algebraic Attacks
==================

This section provides a comprehensive introduction to algebraic attacks, a
fundamental cryptanalytic technique for analyzing LFSR-based systems. The
documentation is designed to be accessible to beginners while providing
sufficient depth for researchers and developers.

Introduction
------------

**What is an Algebraic Attack?**

An **algebraic attack** is a cryptanalytic technique that exploits algebraic
relationships in cryptographic systems to recover secret information. Unlike
correlation attacks that exploit statistical properties, algebraic attacks
solve systems of polynomial equations to recover keys or states.

**Why are Algebraic Attacks Important?**

1. **Complementary to Correlation Attacks**: Can attack systems resistant to
   correlation attacks by exploiting algebraic structure directly

2. **Theoretical Foundation**: Provides security bounds and theoretical analysis
   of cryptographic systems

3. **Research Tool**: Enables analysis of algebraic properties and security
   evaluation

4. **Real-World Applications**: Used in cryptanalysis of stream ciphers and
   block ciphers

**When are Algebraic Attacks Applicable?**

Algebraic attacks are applicable when:
- The cryptographic system can be expressed as a system of polynomial equations
- The system has low algebraic immunity
- Sufficient keystream or plaintext-ciphertext pairs are available
- The system has exploitable algebraic structure

Key Concepts
------------

Algebraic Immunity
~~~~~~~~~~~~~~~~~~

**What is Algebraic Immunity?**

**Algebraic immunity** is a security measure for Boolean functions that
quantifies their resistance to algebraic attacks. It is defined as the minimum
degree of a non-zero annihilator of the function or its complement.

**Key Terminology**:

- **Algebraic Immunity**: The minimum degree of a non-zero annihilator of a
  Boolean function or its complement. Denoted AI(f). Higher algebraic immunity
  indicates better resistance to algebraic attacks. The maximum possible
  algebraic immunity for a function of n variables is ⌈n/2⌉.

- **Annihilator**: A non-zero Boolean function g such that f·g = 0 (g
  annihilates f) or (1+f)·g = 0 (g annihilates the complement of f). Finding
  low-degree annihilators is the basis of algebraic attacks. If a function has
  a low-degree annihilator, it is vulnerable to algebraic attacks.

- **Boolean Function**: A function f: {0,1}^n → {0,1} that maps n binary
  inputs to a single binary output. In cryptography, filtering functions and
  combining functions are Boolean functions. Every Boolean function can be
  uniquely represented in Algebraic Normal Form (ANF).

- **Filtering Function**: A Boolean function applied to LFSR state bits to
  produce the output. The algebraic immunity of the filtering function
  determines the resistance of the LFSR to algebraic attacks. Functions with
  low algebraic immunity allow attackers to construct low-degree equations.

- **Algebraic Normal Form (ANF)**: A representation of Boolean functions as
  polynomials over GF(2). Every Boolean function f(x_1, ..., x_n) can be
  uniquely written as:
  
  .. math::
  
     f(x_1, \\ldots, x_n) = \\bigoplus_{I \\subseteq \\{1,\\ldots,n\\}} a_I \\prod_{i \\in I} x_i
  
  where ⊕ denotes XOR and a_I are coefficients in {0,1}.

- **Degree of a Function**: The highest degree of any monomial in the ANF
  representation. For example, f(x,y,z) = x·y + z has degree 2. The degree
  determines the complexity of algebraic attacks.

- **Optimal Algebraic Immunity**: A function achieves optimal algebraic
  immunity if AI(f) = ⌈n/2⌉, where n is the number of variables. Functions with
  optimal algebraic immunity are most resistant to algebraic attacks.

**Mathematical Foundation**:

The algebraic immunity AI(f) of a Boolean function f is:

.. math::

   \\text{AI}(f) = \\min\\{d : \\exists g \\neq 0, \\deg(g) \\leq d, \\\\
   f \\cdot g = 0 \\text{ or } (1+f) \\cdot g = 0\\}

where deg(g) is the degree of function g.

**Security Implications**:

- Functions with low algebraic immunity (AI < ⌈n/2⌉) are vulnerable to
  algebraic attacks
- Maximum algebraic immunity for n variables is ⌈n/2⌉
- Functions achieving maximum algebraic immunity are called "optimal"
- Algebraic immunity is a key security metric for stream cipher design

**Example**:

Consider a 3-variable function. Maximum possible algebraic immunity is ⌈3/2⌉ = 2.
If a function has AI = 1, it has a linear annihilator, making it vulnerable.
If it has AI = 2, it achieves optimal algebraic immunity.

Gröbner Basis Attacks
~~~~~~~~~~~~~~~~~~~~~~

**What is a Gröbner Basis Attack?**

A **Gröbner basis attack** constructs a system of polynomial equations from
the cryptographic system and keystream, then solves the system using Gröbner
basis computation to recover the initial state or key.

**Key Terminology**:

- **Gröbner Basis**: A special generating set for an ideal in a polynomial
  ring. Gröbner bases allow systematic solution of polynomial systems. Named
  after Bruno Buchberger who developed the algorithm in 1965. A Gröbner basis
  has the property that polynomial division is well-defined, enabling
  systematic solution of polynomial systems.

- **Ideal**: A subset of a ring that is closed under addition and
  multiplication by ring elements. In our context, the ideal is generated by
  the polynomial equations describing the LFSR. An ideal I in a ring R is a
  subset such that: (1) 0 ∈ I, (2) if a, b ∈ I then a+b ∈ I, (3) if a ∈ I and
  r ∈ R then r·a ∈ I.

- **Polynomial Ring**: A ring formed by polynomials with coefficients in a
  field. We work in polynomial rings over GF(2) for binary LFSRs. A polynomial
  ring R[x_1, ..., x_n] consists of all polynomials in variables x_1, ..., x_n
  with coefficients in R.

- **Buchberger's Algorithm**: The fundamental algorithm for computing Gröbner
  bases. It systematically reduces polynomials using S-polynomials until a
  Gröbner basis is obtained. The algorithm terminates and produces a Gröbner
  basis for any ideal.

- **S-Polynomial**: A polynomial constructed from two polynomials in the ideal
  to eliminate leading terms. S-polynomials are used in Buchberger's algorithm
  to generate new polynomials that may be needed for the Gröbner basis.

- **System of Equations**: A collection of polynomial equations that must be
  satisfied simultaneously. Solving such systems is the goal of Gröbner basis
  attacks. A system has a solution if and only if the corresponding ideal is
  not the entire ring.

- **Monomial Ordering**: A way to order monomials (e.g., lexicographic,
  degree-lexicographic). The choice of ordering affects the Gröbner basis and
  solution process. Different orderings can lead to different computational
  complexity.

**Mathematical Foundation**:

Given a system of polynomial equations:

.. math::

   f_1(x_1, \\ldots, x_n) = 0 \\\\
   \\vdots \\\\
   f_m(x_1, \\ldots, x_n) = 0

A Gröbner basis G for the ideal I = ⟨f_1, ..., f_m⟩ allows us to solve this
system systematically. The Gröbner basis has the property that:

1. I = ⟨G⟩ (G generates the same ideal)
2. The solutions of the original system are the same as solutions of G
3. The Gröbner basis has a "triangular" structure that facilitates solving

**Algorithm**:

1. **Construct Equations**: Build polynomial equations from LFSR state
   transitions and keystream observations
   
2. **Compute Gröbner Basis**: Use Buchberger's algorithm (or more efficient
   variants) to compute a Gröbner basis
   
3. **Solve System**: Extract solutions from the Gröbner basis
   
4. **Recover State**: Determine initial state from solutions

**Advantages**:

- Can attack systems resistant to correlation attacks
- Exploits algebraic structure directly
- Systematic approach to solving polynomial systems
- Can handle non-linear systems

**Limitations**:

- Computational complexity can be high (exponential in worst case)
- Requires sufficient equations (keystream length)
- Gröbner basis computation can be expensive for large systems
- Memory requirements can be significant

**Complexity**:

The complexity of Gröbner basis computation depends on:
- Number of variables (LFSR degree)
- Number of equations (keystream length)
- Degree of polynomials
- Monomial ordering chosen

In worst case, complexity can be exponential, but for structured systems it
can be more efficient.

Cube Attacks
~~~~~~~~~~~~

**What is a Cube Attack?**

A **cube attack** is an algebraic attack that exploits low-degree relations in
the output function. It finds "cubes" (sets of variables) such that summing
over the cube yields a low-degree polynomial (the "superpoly").

**Key Terminology**:

- **Cube Attack**: An algebraic attack introduced by Dinur and Shamir (2009)
  that exploits low-degree relations in cryptographic systems. It is
  particularly effective against systems with low-degree output functions.
  The attack works by finding special subsets of variables (cubes) that yield
  low-degree polynomials when summed over.

- **Cube**: A set of variables {x_{i_1}, ..., x_{i_k}} that are varied while
  other variables are fixed. The cube defines a subset of the input space
  (2^k points) over which we sum the output function. A cube of size k
  contains 2^k different assignments to those k variables.

- **Superpoly**: The polynomial obtained by summing the output function over
  a cube. If the superpoly has low degree, it can be used to recover key
  information. The superpoly depends only on variables not in the cube. A
  low-degree superpoly means we can efficiently evaluate it and use it to
  recover key bits.

- **Cube Tester**: An algorithm to find useful cubes. A cube is useful if its
  superpoly has low degree and depends on key variables. The cube tester
  evaluates superpolies for different cubes to find those with desirable
  properties.

- **Maxterm**: A term in the Algebraic Normal Form (ANF) that can be used to
  construct a cube. If a term x_{i_1}·...·x_{i_k} appears in the ANF, then
  {x_{i_1}, ..., x_{i_k}} is a potential cube. Maxterms are the building blocks
  for cube selection.

- **Degree of Superpoly**: The degree of the polynomial obtained by summing
  over a cube. Lower degree superpolies are easier to exploit. If the
  superpoly has degree d, we need at most 2^d evaluations to determine it
  completely.

- **Cube Sum**: The operation of summing the output function over all
  assignments to the cube variables. This is the fundamental operation of
  cube attacks. The cube sum isolates the superpoly.

**Mathematical Foundation**:

Given an output function p(x_1, ..., x_n), we can write it as:

.. math::

   p(x_1, \\ldots, x_n) = x_{i_1} \\cdots x_{i_k} \\cdot p_S(I) + q(x_1, \\ldots, x_n)

where:
- {x_{i_1}, ..., x_{i_k}} is the cube
- I is the set of indices not in the cube
- p_S(I) is the superpoly (depends only on variables in I)
- q has no terms divisible by the cube monomial

Summing p over the cube gives:

.. math::

   \\sum_{x_{i_1}, \\ldots, x_{i_k} \\in \\{0,1\\}} p(x_1, \\ldots, x_n) = p_S(I)

This isolates the superpoly, which depends only on variables not in the cube.

**Algorithm**:

1. **Analyze Output Function**: Determine the ANF representation to identify
   potential cubes (maxterms)
   
2. **Select Cubes**: Choose cubes of increasing size, starting with small cubes
   
3. **Compute Superpolies**: For each cube, compute the superpoly by summing
   over the cube
   
4. **Evaluate Superpolies**: If superpoly has low degree, evaluate it to
   recover key bits
   
5. **Combine Information**: Use information from multiple cubes to recover
   the complete key

**Advantages**:

- Can attack systems with low-degree output functions
- More efficient than full Gröbner basis for certain systems
- Can work with fewer keystream bits than some other attacks
- Systematic cube selection process

**Limitations**:

- Requires low-degree relations (high-degree output functions are resistant)
- Cube selection can be computationally expensive
- May not work if output function has high degree
- Success depends on finding useful cubes

**Complexity**:

The complexity of a cube attack depends on:
- Size of cubes (2^k evaluations per cube of size k)
- Number of cubes needed
- Degree of superpolies
- Keystream length required

For a cube of size k, we need 2^k evaluations. If we need m cubes and each
superpoly has degree d, total complexity is roughly m·2^k·2^d.

API Reference
-------------

The algebraic attacks are implemented in the :mod:`lfsr.attacks` module.
See :doc:`api/attacks` for complete API documentation.

Command-Line Usage
------------------

Algebraic attacks can be performed from the command line:

**Basic Usage**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --algebraic-attack --algebraic-method groebner_basis

**Algebraic Immunity Computation**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --algebraic-attack --algebraic-method algebraic_immunity

**Cube Attack**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --algebraic-attack --algebraic-method cube_attack \
       --max-cube-size 8

**CLI Options**:
- ``--algebraic-attack``: Enable algebraic attack mode
- ``--algebraic-method METHOD``: Choose method (groebner_basis, cube_attack, algebraic_immunity)
- ``--max-cube-size N``: Maximum cube size for cube attack (default: 10)
- ``--max-equations N``: Maximum equations for Gröbner basis (default: 1000)

Python API Usage
----------------

Here's a simple example demonstrating algebraic attacks using the Python API:

.. code-block:: python

   from lfsr.attacks import (
       LFSRConfig,
       compute_algebraic_immunity,
       groebner_basis_attack,
       cube_attack
   )
   
   # Create LFSR configuration
   lfsr = LFSRConfig(
       coefficients=[1, 0, 0, 1],
       field_order=2,
       degree=4
   )
   
   # Generate or load keystream
   keystream = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
   
   # Compute algebraic immunity
   def filtering_function(x0, x1, x2, x3):
       return x0 & x1  # Example filtering function
   
   ai_result = compute_algebraic_immunity(filtering_function, 4)
   print(f"Algebraic immunity: {ai_result['algebraic_immunity']}")
   print(f"Optimal: {ai_result['optimal']}")
   
   # Gröbner basis attack
   gb_result = groebner_basis_attack(lfsr, keystream)
   if gb_result.attack_successful:
       print(f"Recovered state: {gb_result.recovered_state}")
   
   # Cube attack
   cube_result = cube_attack(lfsr, keystream, max_cube_size=5)
   if cube_result.attack_successful:
       print(f"Cubes found: {cube_result.cubes_found}")
       print(f"Recovered bits: {cube_result.recovered_bits}")

Glossary
--------

**Algebraic Attack**
   A cryptanalytic technique that exploits algebraic relationships to recover
   secret information by solving systems of polynomial equations.

**Algebraic Immunity**
   The minimum degree of a non-zero annihilator of a Boolean function or its
   complement. Higher algebraic immunity indicates better resistance to
   algebraic attacks.

**Algebraic Normal Form (ANF)**
   A unique representation of Boolean functions as polynomials over GF(2).

**Annihilator**
   A non-zero Boolean function g such that f·g = 0 or (1+f)·g = 0.

**Boolean Function**
   A function f: {0,1}^n → {0,1} that maps n binary inputs to a single
   binary output.

**Buchberger's Algorithm**
   The fundamental algorithm for computing Gröbner bases, named after Bruno
   Buchberger.

**Cube**
   A set of variables that are varied while others are fixed, used in cube
   attacks to isolate low-degree polynomials.

**Cube Attack**
   An algebraic attack that exploits low-degree relations by finding useful
   cubes and computing superpolies.

**Degree of a Function**
   The highest degree of any monomial in the ANF representation.

**Filtering Function**
   A Boolean function applied to LFSR state bits to produce the output.

**Gröbner Basis**
   A special generating set for an ideal in a polynomial ring that enables
   systematic solution of polynomial systems.

**Ideal**
   A subset of a ring closed under addition and multiplication by ring
   elements.

**Maxterm**
   A term in the ANF that can be used to construct a cube.

**Monomial Ordering**
   A way to order monomials that affects Gröbner basis computation.

**Optimal Algebraic Immunity**
   A function achieves optimal algebraic immunity if AI(f) = ⌈n/2⌉.

**Polynomial Ring**
   A ring formed by polynomials with coefficients in a field.

**S-Polynomial**
   A polynomial constructed from two polynomials to eliminate leading terms,
   used in Buchberger's algorithm.

**Superpoly**
   The polynomial obtained by summing the output function over a cube.

**System of Equations**
   A collection of polynomial equations that must be satisfied simultaneously.

Further Reading
---------------

- Courtois, N., & Meier, W. (2003). "Algebraic attacks on stream ciphers with
  linear feedback"

- Dinur, I., & Shamir, A. (2009). "Cube attacks on tweakable black box
  polynomials"

- Buchberger, B. (1965). "An algorithm for finding a basis for the residue
  class ring of a zero-dimensional polynomial ideal"

- Menezes, A. J., et al. (1996). "Handbook of Applied Cryptography"
