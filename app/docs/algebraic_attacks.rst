Algebraic Attacks
==================

This section provides a comprehensive introduction to algebraic
attacks, a fundamental cryptanalytic technique for analyzing
LFSR-based systems. The documentation is designed to be accessible to
beginners while providing sufficient depth for researchers and
developers. We begin with intuitive explanations and gradually build
to rigorous mathematical formulations.

Introduction
------------

**What is an Algebraic Attack?**

An **algebraic attack** is a cryptanalytic technique that exploits
algebraic relationships in cryptographic systems to recover secret
information. Unlike correlation attacks that exploit statistical
properties, algebraic attacks solve systems of polynomial equations to
recover keys or states. The fundamental idea is to model the
cryptographic system as a system of polynomial equations over a finite
field (typically :math:`\text{GF}(2)` for binary systems) and then
solve this system to recover the secret key or initial state.

**Historical Context and Motivation**

Algebraic attacks emerged as a powerful cryptanalytic tool in the
early 2000s, notably through the work of Courtois and Meier (2003) on
stream ciphers. These attacks revealed that many cryptographic
systems, previously thought secure against statistical attacks, were
vulnerable when viewed from an algebraic perspective. The attacks
exploit the fact that cryptographic operations can be expressed as
polynomial equations, and solving these equations can reveal secret
information.

**Why are Algebraic Attacks Important?**

1. **Complementary to Correlation Attacks**: Can attack systems
   resistant to correlation attacks by exploiting algebraic structure
   directly. While correlation attacks rely on statistical biases,
   algebraic attacks work even when no statistical bias exists.

2. **Theoretical Foundation**: Provides security bounds and
   theoretical analysis of cryptographic systems. The concept of
   algebraic immunity gives a precise measure of resistance to
   algebraic attacks.

3. **Research Tool**: Enables analysis of algebraic properties and
   security evaluation. Understanding algebraic immunity helps in
   designing secure cryptographic primitives.

4. **Real-World Applications**: Used in cryptanalysis of stream
   ciphers (e.g., LILI-128, Toyocrypt) and block ciphers. These
   attacks have led to the cryptanalysis of several proposed
   cryptographic systems.

5. **Design Guidance**: Understanding algebraic attacks helps
   designers create systems with high algebraic immunity, making them
   resistant to such attacks.

**When are Algebraic Attacks Applicable?**

Algebraic attacks are applicable when:

- **Polynomial Representation**: The cryptographic system can be
  expressed as a system of polynomial equations over a finite
  field. For LFSR-based systems, this means the state transitions and
  output functions can be written as polynomials.

- **Low Algebraic Immunity**: The system uses Boolean functions
  (filtering or combining functions) with low algebraic
  immunity. Functions with :math:`\text{AI}(f) < \lceil n/2 \rceil`
  are particularly vulnerable.

- **Sufficient Data**: Sufficient keystream or plaintext-ciphertext
  pairs are available to construct enough equations. The number of
  equations needed depends on the system's complexity and the attack
  method used.

- **Exploitable Structure**: The system has exploitable algebraic
  structure, such as low-degree output functions or sparse polynomial
  representations.

**Relationship to Other Attacks**

Algebraic attacks complement other cryptanalytic techniques:

- **Correlation Attacks**: Exploit statistical biases; algebraic
  attacks work even without statistical bias by exploiting algebraic
  structure.

- **Linear Attacks**: A special case of algebraic attacks where all
  equations are linear (degree 1).

- **Differential Attacks**: Exploit differences in outputs; algebraic
  attacks work with absolute values and relationships.

Understanding algebraic attacks provides a complete picture of the
security landscape for LFSR-based systems.

Key Concepts
------------

Algebraic Immunity
~~~~~~~~~~~~~~~~~~

**What is Algebraic Immunity?**

**Algebraic immunity** is a security measure for Boolean functions
that quantifies their resistance to algebraic attacks. It is defined
as the minimum degree of a non-zero annihilator of the function or its
complement.

**Key Terminology**:

- **Algebraic Immunity**: The minimum degree of a non-zero annihilator
  of a Boolean function or its complement. Denoted
  :math:`\text{AI}(f)`. Higher algebraic immunity indicates better
  resistance to algebraic attacks. The maximum possible algebraic
  immunity for a function of :math:`n` variables is :math:`\lceil n/2
  \rceil`.

- **Annihilator**: A non-zero Boolean function :math:`g` such that
  :math:`f \cdot g = 0` (:math:`g` annihilates :math:`f`) or
  :math:`(1+f) \cdot g = 0` (:math:`g` annihilates the complement of
  :math:`f`). Finding low-degree annihilators is the basis of
  algebraic attacks. If a function has a low-degree annihilator, it is
  vulnerableto algebraic attacks. The existence of a low-degree
  annihilator allows an attacker to construct low-degree equations
  that can be solved efficiently.

- **Boolean Function**: A function :math:`f: \{0,1\}^n \to \{0,1\}`
  that maps :math:`n` binary inputs to a single binary output. In
  cryptography, filtering functions and combining functions are
  Boolean functions. Every Boolean function can be uniquely
  represented in Algebraic Normal Form (ANF). The number of possible
  Boolean functions of :math:`n` variables is :math:`2^{2^n}`, making
  the space of functions exponentially large.

- **Filtering Function**: A Boolean function applied to LFSR state
  bits to produce the output keystream. The algebraic immunity of the
  filtering function determines the resistance of the LFSR to
  algebraic attacks. Functions with low algebraic immunity allow
  attackers to construct low-degree equations that can be solved
  efficiently. In practice, filtering functions are carefully designed
  to have high algebraic immunity while maintaining other desirable
  properties such as balancedness and non-linearity.

- **Algebraic Normal Form (ANF)**: A representation of Boolean
  functions as polynomials over :math:`\text{GF}(2)`. Every Boolean
  function :math:`f(x_1, \ldots, x_n)` can be uniquely written as:
  
  .. math::
  
     f(x_1, \ldots, x_n) = \bigoplus_{I \subseteq \{1,\ldots,n\}} a_I
     \prod_{i \in I} x_i
  
  where :math:`\oplus` denotes XOR and :math:`a_I`'s are coefficients in
  :math:`\{0,1\}`.

- **Degree of a Function**: The highest degree of any monomial in the
  ANF representation. For example, :math:`f(x,y,z) = x \cdot y + z`
  has degree 2 (from the term :math:`x \cdot y`). The degree determines
  the complexity of algebraic attacks: higher degree functions generally
  require more equations and computational resources to attack. The degree
  of a Boolean function of :math:`n` variables is at most :math:`n`.

- **Optimal Algebraic Immunity**: A function achieves optimal
  algebraic immunity if :math:`\text{AI}(f) = \lceil n/2 \rceil`,
  where :math:`n` is the number of variables. Functions with optimal
  algebraic immunity are most resistant to algebraic attacks.

**Mathematical Foundation**:

The algebraic immunity :math:`\text{AI}(f)` of a Boolean function
:math:`f: \{0,1\}^n \to \{0,1\}` is formally defined as:

.. math::

   \text{AI}(f) = \min\left\{d : \exists g \neq 0, \deg(g) \leq d,
   \text{ such that } f \cdot g = 0 \text{ or } (1+f) \cdot g =
   0\right\}

where:

- :math:`g: \{0,1\}^n \to \{0,1\}` is a non-zero Boolean function (the
  annihilator)
- :math:`\deg(g)` is the degree of :math:`g` in its Algebraic Normal
  Form (ANF)
- :math:`f \cdot g = 0` means :math:`g` annihilates :math:`f` (i.e.,
  :math:`g(x) = 0` whenever :math:`f(x) = 1`)
- :math:`(1+f) \cdot g = 0` means :math:`g` annihilates the complement
  of :math:`f` (i.e., :math:`g(x) = 0` whenever :math:`f(x) = 0`)

In words, :math:`\text{AI}(f)` is the minimum degree among all
non-zero annihilators of either :math:`f` or its complement
:math:`1+f`.

**Properties**:

- :math:`1 \leq \text{AI}(f) \leq \lceil n/2 \rceil` for any Boolean
  function :math:`f` of :math:`n` variables
- If :math:`\text{AI}(f) = 1`, then :math:`f` has a linear annihilator
  and is highly vulnerable
- If :math:`\text{AI}(f) = \lceil n/2 \rceil`, then :math:`f` achieves
  optimal algebraic immunity

**Security Implications**:

- Functions with low algebraic immunity (:math:`\text{AI} < \lceil n/2
  \rceil`) are vulnerable to algebraic attacks
- Maximum algebraic immunity for :math:`n` variables is :math:`\lceil
  n/2 \rceil`
- Functions achieving maximum algebraic immunity are called "optimal"
- Algebraic immunity is a key security metric for stream cipher design

**Example**:

Consider a 3-variable Boolean function :math:`f(x_1, x_2, x_3)`. The
maximum possible algebraic immunity is :math:`\lceil 3/2 \rceil = 2`.

- If a function has :math:`\text{AI}(f) = 1`, it has a linear
  annihilator (degree 1), making it highly vulnerable. For example, if
  :math:`f(x_1, x_2, x_3) = x_1`, then :math:`g(x_1, x_2, x_3) = 1 +
  x_1` is an annihilator of degree 1, since :math:`f \cdot g =
  x_1(1+x_1) = 0` over :math:`\text{GF}(2)`.

- If it has :math:`\text{AI}(f) = 2`, it achieves optimal algebraic
  immunity and is maximally resistant to algebraic attacks. An example
  of such a function is the majority function of three variables,
  which has no annihilator of degree less than 2.

This example illustrates why algebraic immunity is a critical security
parameter: functions with low algebraic immunity can be attacked using
low-degree equations, which are computationally tractable.

Gröbner Basis Attacks
~~~~~~~~~~~~~~~~~~~~~~

**What is a Gröbner Basis Attack?**

A **Gröbner basis attack** constructs a system of polynomial equations
from the cryptographic system and keystream, then solves the system
using Gröbner basis computation to recover the initial state or key.

**Key Terminology**:

- **Gröbner Basis**: A special generating set for an ideal in a
  polynomial ring that enables systematic solution of polynomial
  systems. Named after Bruno Buchberger, who developed the fundamental
  algorithm in 1965. A Gröbner basis has the property that polynomial
  division is well-defined, enabling systematic solution of polynomial
  systems. Given a Gröbner basis, one can determine whether a
  polynomial belongs to the ideal, find solutions to the system, and
  perform other algebraic operations algorithmically. The Gröbner
  basis depends on the chosen monomial ordering, and different
  orderings can lead to different computational complexity.

- **Ideal**: A subset of a ring that is closed under addition and
  multiplication by ring elements. In our context, the ideal is
  generated by the polynomial equations describing the LFSR state
  transitions and keystream observations. An ideal :math:`I` in a ring
  :math:`R` is a subset such that:
	
  (1) :math:`0 \in I`,
      
  (2) if :math:`a, b \in I` then :math:`a+b \in I`,

  (3) if :math:`a \in I` and :math:`r \in R` then :math:`r \cdot a \in
      I`. The ideal generated by polynomials :math:`f_1, \ldots, f_m`
      is denoted :math:`\langle f_1, \ldots, f_m \rangle` and consists
      of all linear combinations :math:`r_1 f_1 + \cdots + r_m f_m`
      where :math:`r_i \in R`.

- **Polynomial Ring**: A ring formed by polynomials with coefficients
  in a field. We work in polynomial rings over :math:`\text{GF}(2)`
  for binary LFSRs, where addition and multiplication are performed
  modulo 2. A polynomial ring :math:`R[x_1, \ldots, x_n]` consists of
  all polynomials in variables :math:`x_1, \ldots, x_n` with
  coefficients in :math:`R`. For binary systems, we work in
  :math:`\text{GF}(2)[x_1, \ldots, x_n]`, where the field
  :math:`\text{GF}(2)` has only two elements :math:`\{0, 1\}` with
  addition and multiplication modulo 2.

- **Buchberger's Algorithm**: The fundamental algorithm for computing
  Gröbner bases, developed by Bruno Buchberger in 1965. It
  systematically reduces polynomials using S-polynomials until a
  Gröbner basis is obtained. The algorithm works by repeatedly
  computing S-polynomials from pairs of polynomials in the current
  basis and reducing them. The algorithm terminates and produces a
  Gröbner basis for any ideal, though the computational complexity can
  be high. Modern implementations use optimizations such as the F4 and
  F5 algorithms to improve efficiency.

- **S-Polynomial**: A polynomial constructed from two polynomials in
  the ideal to eliminate leading terms. Given two polynomials
  :math:`f` and :math:`g` with leading terms :math:`\text{LT}(f)` and
  :math:`\text{LT}(g)`, the S-polynomial is :math:`S(f,g) =
  \frac{\text{LCM}(\text{LT}(f), \text{LT}(g))}{\text{LT}(f)} \cdot
  f - \frac{\text{LCM}(\text{LT}(f), \text{LT}(g))}{\text{LT}(g)}
  \cdot g`, where LCM denotes the least common multiple. S-polynomials
  are used in Buchberger's algorithm to generate new polynomials that
  may be needed for the Gröbner basis.

- **System of Equations**: A collection of polynomial equations that
  must be satisfied simultaneously. In the context of algebraic
  attacks, we construct a system where each equation represents a
  relationship between the LFSR state variables and the observed
  keystream. Solving such systems is the goal of Gröbner basis
  attacks. A system has a solution if and only if the corresponding
  ideal is not the entire ring. If the ideal equals the entire ring,
  the system is inconsistent (has no solution).

- **Monomial Ordering**: A way to order monomials that determines
  which term is considered the "leading term" of a polynomial. Common
  orderings include lexicographic (lex), degree-lexicographic
  (deglex), and degree-reverse lexicographic (degrevlex). The choice
  of ordering affects the Gröbner basis and solution
  process. Different orderings can lead to different computational
  complexity: lexicographic ordering often produces Gröbner bases that
  are easier to solve but may be larger, while degree-based orderings
  can be more efficient to compute but harder to solve.

**Mathematical Foundation**:

Given a system of polynomial equations:

.. math::

   f_1(x_1, \ldots, x_n) = 0 \\
   \vdots \\
   f_m(x_1, \ldots, x_n) = 0

A Gröbner basis :math:`G = \{g_1, \ldots, g_k\}` for the ideal
:math:`I = \langle f_1, \ldots, f_m \rangle` allows us to solve this
system systematically. The Gröbner basis has the following key
properties:

1. **Ideal Equivalence**: :math:`I = \langle G \rangle` (:math:`G`
   generates the same ideal as the original polynomials)

2. **Solution Preservation**: The solutions of the original system are
   exactly the same as solutions of the system :math:`g_1 = 0, \ldots,
   g_k = 0`

3. **Triangular Structure**: Under an appropriate monomial ordering
   (typically lexicographic), the Gröbner basis has a "triangular"
   structure that facilitates solving. This means we can solve for
   variables sequentially, starting with the last variable and working
   backwards.

4. **Uniqueness**: For a given monomial ordering, the reduced Gröbner
   basis is unique, providing a canonical representation of the ideal.

The key insight is that while the original system may be difficult to
solve directly, the Gröbner basis provides an equivalent system that
is structured in a way that makes solution extraction feasible.

**Algorithm**:

The Gröbner basis attack proceeds through the following steps:

1. **Model the System**: Express the LFSR state transitions and output
   function as polynomial equations over :math:`\text{GF}(2)`. For an
   LFSR of degree :math:`d`, we have :math:`d` state variables
   :math:`s_0, s_1, \ldots, s_{d-1}`.  Each state transition gives a
   linear equation, and each keystream bit observation gives a
   non-linear equation involving the output function.

2. **Construct Equations**: Build a system of polynomial equations
   from:
   
   - State transition equations: :math:`s_{i+d} = c_0 s_i + c_1
     s_{i+1} + \cdots + c_{d-1} s_{i+d-1}`
     
   - Keystream equations: :math:`z_i = f(s_i, s_{i+1}, \ldots,
     s_{i+d-1})` where :math:`z_i` is the observed keystream bit and
     :math:`f` is the filtering function
   
3. **Compute Gröbner Basis**: Use Buchberger's algorithm (or more
   efficient variants such as F4 or F5) to compute a Gröbner basis for
   the ideal generated by these equations. The choice of monomial
   ordering affects both the computation time and the structure of the
   resulting basis.
   
4. **Solve System**: Extract solutions from the Gröbner basis. If
   using lexicographic ordering, the basis will have a triangular
   structure allowing sequential solution. The number of solutions
   corresponds to the number of possible initial states consistent
   with the observed keystream.
   
5. **Recover State**: Determine the initial state from the
   solutions. In practice, additional constraints (such as known
   plaintext or additional keystream) may be needed to uniquely
   identify the correct initial state.

**Advantages**:

- **Broad Applicability**: Can attack systems resistant to correlation
  attacks by exploiting algebraic structure directly, even when no
  statistical bias exists.

- **Systematic Approach**: Provides a systematic, algorithmic method
  for solving polynomial systems, making it suitable for automated
  cryptanalysis.

- **Non-Linear Handling**: Can handle non-linear systems, unlike
  linear algebra attacks that require linearity.

- **Theoretical Foundation**: Based on well-established algebraic
  geometry theory, providing theoretical guarantees about when
  solutions exist.

- **Completeness**: When successful, the attack recovers the exact
  secret information, not just statistical information.

**Limitations**:

- **Computational Complexity**: Computational complexity can be high
  (exponential in worst case). The complexity depends on the number of
  variables, equations, and the degrees of polynomials involved.

- **Data Requirements**: Requires sufficient equations (keystream
  length) to construct a solvable system. The number of equations
  needed typically grows with the system complexity.

- **Memory Requirements**: Gröbner basis computation can be expensive
  for large systems, with memory requirements that can grow
  exponentially with the number of variables.

- **Monomial Explosion**: The number of monomials in intermediate
  polynomials can grow very large, making computation infeasible for
  high-degree systems.

- **Ordering Sensitivity**: The choice of monomial ordering
  significantly affects computational complexity, and choosing the
  wrong ordering can make the attack infeasible.

**Complexity Analysis**:

The complexity of Gröbner basis computation depends on several
factors:

- **Number of Variables**: The LFSR degree :math:`d` determines the
  number of state variables. Higher degree LFSRs require more
  variables and generally increase complexity.

- **Number of Equations**: The keystream length determines how many
  equations we can construct. More equations can help, but also
  increase the system size.

- **Degree of Polynomials**: The degree of the filtering function
  determines the degree of equations. Higher degree functions lead to
  higher degree polynomials in the Gröbner basis computation.

- **Monomial Ordering**: Different orderings (lex, deglex, degrevlex)
  have different computational properties. Lexicographic ordering
  often produces bases that are easier to solve but harder to compute.

In the worst case, the complexity can be doubly exponential in the
number of variables. However, for structured systems (such as LFSRs
with low-degree filtering functions), the complexity can be more
manageable, often polynomial or single exponential in practice.

Cube Attacks
~~~~~~~~~~~~

**What is a Cube Attack?**

A **cube attack** is an algebraic attack introduced by Dinur and
Shamir in 2009 that exploits low-degree relations in the output
function. Unlike Gröbner basis attacks that attempt to solve the
entire system, cube attacks work by finding special subsets of
variables (called "cubes") such that summing the output function over
all assignments to the cube variables yields a low-degree polynomial
(called the "superpoly"). This superpoly depends only on variables not
in the cube, and if it has sufficiently low degree, it can be
efficiently evaluated and used to recover key information.

The key insight is that many cryptographic systems have output
functions that, when summed over certain subsets of variables,
simplify to low-degree polynomials. This property can be exploited
even when the original function has high degree.

**Key Terminology**:

- **Cube Attack**: An algebraic attack introduced by Dinur and Shamir (2009)
  in their paper "Cube Attacks on Tweakable Black Box Polynomials". It exploits
  low-degree relations in cryptographic systems and is particularly effective
  against systems with low-degree output functions or systems where the output
  function simplifies when summed over certain variable subsets. The attack
  works by finding special subsets of variables (cubes) that yield low-degree
  polynomials (superpolies) when the output function is summed over all
  assignments to the cube variables.

- **Cube**: A set of variables :math:`\{x_{i_1}, \ldots, x_{i_k}\}`
  that are varied while other variables are fixed. The cube defines a
  subset of the input space (:math:`2^k` points) over which we sum the
  output function. A cube of size :math:`k` contains :math:`2^k`
  different assignments to those :math:`k` variables.

- **Superpoly**: The polynomial obtained by summing the output
  function over a cube. If the superpoly has low degree, it can be
  used to recover key information. The superpoly depends only on
  variables not in the cube. A low-degree superpoly means we can
  efficiently evaluate it and use it to recover key bits.

- **Cube Tester**: An algorithm or procedure to find useful cubes. A
  cube is useful if its superpoly has low degree and depends on key
  variables (or state variables in the LFSR context). The cube tester
  evaluates superpolies for different cubes to find those with
  desirable properties. This typically involves testing whether the
  superpoly is constant, linear, or has low degree by evaluating it
  for different assignments to the non-cube variables.

- **Maxterm**: A term in the Algebraic Normal Form (ANF) that can be
  used to construct a cube. If a term :math:`x_{i_1} \cdots x_{i_k}`
  appears in the ANF of the output function, then :math:`\{x_{i_1},
  \ldots, x_{i_k}\}` is a potential cube. Maxterms are the building
  blocks for cube selection because they indicate which variables
  appear together in high-degree terms. By summing over these
  variables, we can potentially isolate lower-degree components of the
  function.

- **Degree of Superpoly**: The degree of the polynomial obtained by
  summing over a cube. Lower degree superpolies are easier to
  exploit. If the superpoly has degree :math:`d`, we need at most
  :math:`2^d` evaluations to determine it completely.

- **Cube Sum**: The operation of summing the output function over all
  :math:`2^k` assignments to the cube variables while keeping non-cube
  variables fixed. This is the fundamental operation of cube
  attacks. The cube sum isolates the superpoly, which depends only on
  the non-cube variables. Mathematically, for a cube :math:`C =
  \{x_{i_1}, \ldots, x_{i_k}\}`, the cube sum is
  :math:`\sum_{(x_{i_1}, \ldots, x_{i_k}) \in \{0,1\}^k} p(x_1,
  \ldots, x_n)`.

**Mathematical Foundation**:

The cube attack is based on the observation that any polynomial
:math:`p(x_1, \ldots, x_n)` over :math:`\text{GF}(2)` can be uniquely
decomposed with respect to a subset of variables (the cube). Given an
output function :math:`p(x_1, \ldots, x_n)` and a cube :math:`C =
\{x_{i_1}, \ldots, x_{i_k}\}`, we can write:

.. math::

   p(x_1, \ldots, x_n) = x_{i_1} \cdots x_{i_k} \cdot p_S(I) + q(x_1,
   \ldots, x_n)

where:

- :math:`\{x_{i_1}, \ldots, x_{i_k}\}` is the cube (the variables we
  will sum over)
- :math:`I = \{1, \ldots, n\} \setminus \{i_1, \ldots, i_k\}` is the
  set of indices not in the cube
- :math:`p_S(I)` is the superpoly, which depends only on variables
  :math:`\{x_j : j \in I\}` (variables not in the cube)
- :math:`q(x_1, \ldots, x_n)` contains all terms that are not
  divisible by the cube monomial :math:`x_{i_1} \cdots x_{i_k}`

The key property is that when we sum :math:`p` over all :math:`2^k`
assignments to the cube variables, all terms in :math:`q` cancel out
(since they don't contain all cube variables), leaving only the
superpoly:

.. math::

   \sum_{(x_{i_1}, \ldots, x_{i_k}) \in \{0,1\}^k} p(x_1, \ldots, x_n)
   = p_S(I)

This isolates the superpoly, which depends only on variables not in
the cube.  If the superpoly has low degree :math:`d`, we can determine
it completely using at most :math:`2^d` evaluations, which is much
more efficient than dealing with the original high-degree function.

**Algorithm**:

The cube attack proceeds through the following phases:

1. **Preprocessing Phase (Offline)**:
   
   - **Analyze Output Function**: Determine the ANF representation of
     the output function to identify potential cubes (maxterms). Terms
     in the ANF suggest which variables might form useful cubes.
     
   - **Select Cubes**: Choose cubes of increasing size, starting with
     small cubes (size 1, 2, 3, ...). Smaller cubes are easier to test
     but may not yield useful superpolies. Larger cubes may yield
     lower-degree superpolies but require more evaluations.
     
   - **Test Cubes**: For each candidate cube, test whether the
     superpoly has low degree. This is done by evaluating the cube sum
     for different assignments to non-cube variables and checking if
     the result is constant, linear, or low-degree.

2. **Online Phase**:
   
   - **Compute Superpolies**: For each useful cube identified in
     preprocessing, compute the superpoly by summing the output
     function over all :math:`2^k` assignments to the cube
     variables. This requires :math:`2^k` evaluations of the
     cryptographic system.
	   
   - **Evaluate Superpolies**: If the superpoly has low degree
     :math:`d`, determine it completely by evaluating it for
     :math:`2^d` different assignments to the non-cube variables. This
     gives linear or low-degree equations in the key/state variables.
     
   - **Solve Equations**: Solve the system of equations obtained from
     multiple superpolies to recover key bits or state variables.
     
   - **Combine Information**: Use information from multiple cubes to
     recover the complete key or initial state. Different cubes may
     provide equations involving different subsets of variables, and
     combining them gives a complete system.

**Advantages**:

- **Efficiency for Low-Degree Systems**: Can attack systems with
  low-degree output functions more efficiently than full Gröbner basis
  attacks. The complexity depends on the degree of superpolies, not
  the degree of the original function.

- **Selective Evaluation**: More efficient than full Gröbner basis for
  certain systems because it only evaluates the function for specific
  variable assignments rather than solving the entire system.

- **Reduced Data Requirements**: Can work with fewer keystream bits
  than some other attacks, as it exploits structure in the output
  function rather than requiring many independent equations.

- **Systematic Process**: Provides a systematic cube selection
  process, making it suitable for automated analysis.

- **Black Box Applicability**: Can work even when the internal
  structure of the system is unknown, as long as the system can be
  queried (black box model).

**Limitations**:

- **Degree Requirement**: Requires low-degree relations. High-degree
  output functions produce high-degree superpolies, making the attack
  infeasible.

- **Cube Selection Complexity**: Finding useful cubes can be
  computationally expensive, especially for large systems. The
  preprocessing phase may require significant computational resources.

- **Success Dependency**: Success depends critically on finding useful
  cubes with low-degree superpolies. If no such cubes exist, the
  attack fails.

- **Exponential Growth**: The number of evaluations grows
  exponentially with cube size :math:`k` (:math:`2^k` evaluations per
  cube). Large cubes become computationally prohibitive.

- **Superpoly Degree**: Even if a cube is found, if the superpoly has
  high degree, evaluating it requires :math:`2^d` operations, which
  may be infeasible.

**Complexity Analysis**:

The complexity of a cube attack has several components:

- **Cube Size**: For a cube of size :math:`k`, we need :math:`2^k`
  evaluations of the cryptographic system to compute the cube
  sum. This is the dominant cost for large cubes.

- **Number of Cubes**: If we need :math:`m` cubes to obtain enough
  equations, the total number of evaluations is :math:`m \cdot 2^k`
  (assuming all cubes have the same size :math:`k`).

- **Superpoly Degree**: If each superpoly has degree :math:`d`, we
  need at most :math:`2^d` evaluations to determine it
  completely. This is typically much smaller than :math:`2^k` if
  :math:`d < k`.

- **Total Complexity**: The total complexity is roughly
  :math:`m \cdot (2^k + 2^d)`, where :math:`m` is the number of cubes,
  :math:`k` is the cube size, and :math:`d` is the superpoly degree. In
  practice, :math:`2^k` dominates when cubes are large, while :math:`2^d`
  dominates when superpolies have high degree.

The attack is most effective when :math:`k` and :math:`d` are both
small, making the total complexity manageable. For systems with
high-degree output functions, both :math:`k` and :math:`d` tend to be
large, making the attack infeasible.

API Reference
-------------

The algebraic attacks are implemented in the :mod:`lfsr.attacks`
module.  See :doc:`api/attacks` for complete API documentation.

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
   A cryptanalytic technique that exploits algebraic relationships to
   recover secret information by solving systems of polynomial
   equations.

**Algebraic Immunity**
   The minimum degree of a non-zero annihilator of a Boolean function
   or its complement. Higher algebraic immunity indicates better
   resistance to algebraic attacks.

**Algebraic Normal Form (ANF)**
   A unique representation of Boolean functions as polynomials over
   :math:`\text{GF}(2)`.

**Annihilator**
   A non-zero Boolean function :math:`g` such that :math:`f \cdot g =
   0` or :math:`(1+f) \cdot g = 0`.  Finding low-degree annihilators
   is the basis of algebraic attacks.

**Boolean Function**
   A function :math:`f: \{0,1\}^n \to \{0,1\}` that maps :math:`n`
   binary inputs to a single binary output.

**Buchberger's Algorithm**
   The fundamental algorithm for computing Gröbner bases, named after
   Bruno Buchberger.

**Cube**
   A set of variables that are varied while others are fixed, used in
   cube attacks to isolate low-degree polynomials.

**Cube Attack**
   An algebraic attack that exploits low-degree relations by finding
   useful cubes and computing superpolies.

**Degree of a Function**
   The highest degree of any monomial in the ANF representation.

**Filtering Function**
   A Boolean function applied to LFSR state bits to produce the
   output.

**Gröbner Basis**
   A special generating set for an ideal in a polynomial ring that
   enables systematic solution of polynomial systems.

**Ideal**
   A subset of a ring closed under addition and multiplication by ring
   elements.

**Maxterm**
   A term in the ANF that can be used to construct a cube.

**Monomial Ordering**
   A way to order monomials that affects Gröbner basis computation.

**Optimal Algebraic Immunity**
   A function achieves optimal algebraic immunity if
   :math:`\text{AI}(f) = \lceil n/2 \rceil`.

**Polynomial Ring**
   A ring formed by polynomials with coefficients in a field.

**S-Polynomial**
   A polynomial constructed from two polynomials to eliminate leading
   terms, used in Buchberger's algorithm.

**Superpoly**
   The polynomial obtained by summing the output function over a cube.

**System of Equations**
   A collection of polynomial equations that must be satisfied
   simultaneously.

Further Reading
---------------

- Courtois, N., & Meier, W. (2003). "Algebraic attacks on stream
  ciphers with linear feedback"

- Dinur, I., & Shamir, A. (2009). "Cube attacks on tweakable black box
  polynomials"

- Buchberger, B. (1965). "An algorithm for finding a basis for the
  residue class ring of a zero-dimensional polynomial ideal"

- Menezes, A. J., et al. (1996). "Handbook of Applied Cryptography"
