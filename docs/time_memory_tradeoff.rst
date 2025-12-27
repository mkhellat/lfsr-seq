Time-Memory Trade-Off Attacks
==============================

This section provides a comprehensive introduction to Time-Memory Trade-Off
(TMTO) attacks, a fundamental cryptanalytic technique for efficient state
recovery. The documentation is designed to be accessible to beginners while
providing sufficient depth for researchers and developers.

Introduction
------------

**What is a Time-Memory Trade-Off Attack?**

A **time-memory trade-off (TMTO) attack** is a cryptanalytic technique that
precomputes tables to enable faster state recovery. Instead of computing states
on-demand (which is time-intensive), we precompute and store states
(memory-intensive), then look them up during attacks.

**Why are TMTO Attacks Important?**

1. **Practical Attacks**: Enable faster state recovery after precomputation
2. **Batch Attacks**: Same table can be used to attack multiple targets
3. **Demonstrates Real-World Scenarios**: Shows how attackers might precompute
   tables for later use
4. **Theoretical Foundation**: Demonstrates the fundamental trade-off between
   time and memory in cryptanalysis

**When are TMTO Attacks Applicable?**

TMTO attacks are applicable when:
- State space is manageable for precomputation
- Multiple targets need to be attacked (amortizes precomputation cost)
- Online computation is expensive
- Precomputation time is acceptable
- Memory is available for table storage

Key Concepts
------------

Time-Memory Trade-Off
~~~~~~~~~~~~~~~~~~~~~~

**What is a Time-Memory Trade-Off?**

A **time-memory trade-off** is a fundamental principle in cryptanalysis that
allows trading memory (storage) for computation time. By precomputing and
storing information, we can reduce the time needed for online attacks.

**Key Terminology**:

- **Time-Memory Trade-Off (TMTO)**: A cryptanalytic technique that
  precomputes tables to enable faster attacks. The trade-off is between
  precomputation time/memory and online attack time. First introduced by
  Martin Hellman (1980).

- **Precomputation**: The initial phase where tables are generated. This is
  done once and can be reused for multiple attacks. Precomputation is
  time-consuming but only needs to be done once.

- **Online Attack**: The phase where the precomputed table is used to
  recover states. This is much faster than computing states on-demand.
  Online attacks can be performed quickly using the precomputed table.

- **Trade-Off Curve**: A graph showing the relationship between time and
  memory for different parameter choices. The curve demonstrates how
  increasing memory reduces attack time (and vice versa).

- **Coverage**: The fraction of the state space covered by the table.
  Coverage = (number of states in table) / (total state space size).
  Higher coverage increases success probability but requires more memory.

- **Success Probability**: The probability that a random state can be
  recovered from the table. This depends on coverage and collision rate.
  Higher coverage generally means higher success probability.

**Mathematical Foundation**:

The fundamental trade-off relationship is:

.. math::

   TM^2 = N^2

where:
- T is the time for online attack
- M is the memory (table size)
- N is the state space size (q^d for LFSR of degree d over GF(q))

This means that to reduce attack time by a factor of k, we need k^2 times
more memory (or vice versa).

Hellman Tables
~~~~~~~~~~~~~~~

**What is a Hellman Table?**

A **Hellman table** is a precomputed table that stores chains of state
transitions, allowing fast state recovery. Named after Martin Hellman (1980),
it was the first time-memory trade-off technique.

**Key Terminology**:

- **Hellman Table**: A precomputed table storing chains of state transitions.
  Each chain starts with a random state and ends with a distinguished point.
  The table enables fast state recovery by looking up chains that might
  contain the target state.

- **Chain**: A sequence of states connected by the state update function.
  Each chain has length t and represents t consecutive state transitions.
  Chains are the fundamental building blocks of Hellman tables. A chain is:
  S_0 → f(S_0) → R(f(S_0)) → f(R(f(S_0))) → ... where f is the state update
  function and R is the reduction function.

- **Distinguished Point**: A state with a special property (e.g., leading k
  bits are zero) used to mark chain endpoints. Distinguished points make chain
  endpoints easy to identify and store, reducing storage requirements. Only
  chains ending at distinguished points are stored.

- **Reduction Function**: A function R that maps states to starting points
  (keys). The reduction function creates chains by providing a way to "reduce"
  a state back to a starting point. Different reduction functions can be used
  to create different chains.

- **Table Lookup**: The process of searching precomputed tables to find a
  target state. Lookup involves: (1) applying reduction function to target,
  (2) checking if result is a chain endpoint, (3) if found, reconstructing
  chain to find target. Lookup is much faster than computing states on-demand.

- **False Alarm**: When a chain appears to contain the target state but
  doesn't. This occurs due to collisions in the reduction function (different
  states map to the same starting point). False alarms must be verified by
  reconstructing the chain.

- **Chain Collision**: When two different chains merge (have the same
  endpoint). Collisions reduce table efficiency because they cover fewer
  unique states. Hellman tables can have significant collisions.

**Mathematical Foundation**:

A Hellman table consists of m chains, each of length t. The table covers
approximately m·t states (with some overlap due to collisions). The coverage
is:

.. math::

   \\text{coverage} = \\frac{m \\cdot t}{N}

where N is the state space size.

**Algorithm**:

1. **Precomputation Phase**:
   - Generate m random starting states S_0^{(1)}, ..., S_0^{(m)}
   - For each starting state, compute a chain:
     S_0 → f(S_0) → R(f(S_0)) → f(R(f(S_0))) → ... → S_t
   - Store only (S_0, S_t) pairs where S_t is a distinguished point
   - Repeat until m chains with distinguished endpoints are created

2. **Lookup Phase**:
   - Given target state S, apply reduction function: R(S)
   - Check if R(S) is a chain endpoint in table
   - If found, reconstruct chain from start to find S
   - If not found, apply f then R repeatedly (up to t times)

**Advantages**:

- Faster state recovery after precomputation
- Can attack multiple targets using same table
- Demonstrates practical attack scenarios
- Simple to implement

**Limitations**:

- Requires significant memory for large state spaces
- Precomputation can be time-consuming
- False alarms require verification
- Coverage may be incomplete
- Chain collisions reduce efficiency

Rainbow Tables
~~~~~~~~~~~~~~~

**What is a Rainbow Table?**

A **rainbow table** is an improved version of Hellman tables that uses
different reduction functions at each step, reducing collisions. Introduced by
Philippe Oechslin (2003), rainbow tables are more efficient than Hellman
tables for the same memory usage.

**Key Terminology**:

- **Rainbow Table**: A precomputed table using different reduction functions
  at each step (like colors in a rainbow). This reduces collisions compared
  to Hellman tables, which use the same reduction function. Rainbow tables
  are named for the "rainbow" of different reduction functions used.

- **Rainbow Chain**: A chain where each step uses a different reduction
  function R_1, R_2, ..., R_t. The chain is:
  S_0 → f(S_0) → R_1(f(S_0)) → f(R_1(f(S_0))) → R_2(f(R_1(f(S_0)))) → ...
  Each step uses a different "color" (reduction function).

- **Reduction Function Family**: A set of t different reduction functions
  {R_1, R_2, ..., R_t}, one for each step in the chain. Each function maps
  states to starting points, but they differ to reduce collisions. The family
  ensures that collisions are less likely.

- **Collision Resistance**: Rainbow tables have fewer collisions than Hellman
  tables because different reduction functions are used at each step. For two
  chains to merge, they must collide at the same step with the same reduction
  function, which is less likely than in Hellman tables.

- **Table Lookup**: Similar to Hellman tables, but must try all reduction
  functions in reverse order. For target state S, we check R_t(S),
  R_{t-1}(f(S)), R_{t-2}(f^2(S)), etc. This ensures we check all possible
  positions in chains.

**Mathematical Foundation**:

Rainbow tables use t different reduction functions. A chain of length t is:

.. math::

   S_0 \\rightarrow f(S_0) \\rightarrow R_1(f(S_0)) \\rightarrow f(R_1(f(S_0))) \\rightarrow \\ldots

This reduces collisions because merging chains requires collisions at the same
step with the same reduction function, which is less likely than using the
same reduction function at all steps.

**Advantages over Hellman Tables**:

- Fewer collisions (more efficient)
- Better coverage for same memory
- Simpler lookup (no need to check all chains at each step)
- More practical for real-world attacks

**Limitations**:

- Still requires significant memory
- Precomputation can be time-consuming
- Lookup requires trying all reduction functions
- Coverage may still be incomplete for very large state spaces

Trade-Off Parameter Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**What is Parameter Optimization?**

**Parameter optimization** finds the best values for chain_count and
chain_length to maximize success probability given memory constraints.

**Key Terminology**:

- **Optimal Parameters**: Parameter values that minimize the time×memory
  product for a given success probability. These parameters provide the best
  trade-off between time and memory. Optimal parameters depend on the state
  space size and available memory.

- **Trade-Off Curve**: A graph showing the relationship between time and
  memory for different parameter choices. The curve shows how increasing
  memory reduces attack time (and vice versa). Points on the curve represent
  different parameter choices.

- **Coverage Analysis**: Determining what fraction of the state space is
  covered by a table with given parameters. Coverage analysis helps choose
  parameters that provide desired success probability.

- **Success Probability Estimation**: Estimating the probability that a
  random state can be recovered from a table. This depends on coverage,
  collision rate, and table structure.

**Optimization Strategy**:

1. Given constraints (memory, state space size, target success probability)
2. Try different parameter combinations
3. Estimate coverage and success probability for each
4. Select parameters that minimize time×memory product
5. Verify parameters meet success probability requirement

API Reference
-------------

The TMTO attacks are implemented in the :mod:`lfsr.tmto` module.
See :doc:`api/tmto` for complete API documentation.

Command-Line Usage
------------------

TMTO attacks can be performed from the command line:

**Basic Usage**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --tmto-attack --tmto-method hellman

**Rainbow Table Attack**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --tmto-attack --tmto-method rainbow \
       --chain-count 2000 --chain-length 150

**Use Precomputed Table**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --tmto-attack --tmto-table-file table.json

**CLI Options**:
- ``--tmto-attack``: Enable TMTO attack mode
- ``--tmto-method METHOD``: Choose method ("hellman" or "rainbow")
- ``--chain-count N``: Number of chains in table (default: 1000)
- ``--chain-length N``: Length of each chain (default: 100)
- ``--tmto-table-file FILE``: File with precomputed table (JSON format)

Python API Usage
----------------

Here's a simple example demonstrating TMTO attacks using the Python API:

.. code-block:: python

   from lfsr.attacks import LFSRConfig
   from lfsr.tmto import HellmanTable, RainbowTable, tmto_attack
   
   # Create LFSR configuration
   lfsr = LFSRConfig(
       coefficients=[1, 0, 0, 1],
       field_order=2,
       degree=4
   )
   
   # Target state to recover
   target_state = [1, 0, 1, 1]
   
   # Hellman table attack
   result = tmto_attack(
       lfsr_config=lfsr,
       target_state=target_state,
       method="hellman",
       chain_count=1000,
       chain_length=100
   )
   
   if result.attack_successful:
       print(f"Recovered state: {result.recovered_state}")
       print(f"Coverage: {result.coverage:.2%}")
   
   # Rainbow table attack
   result2 = tmto_attack(
       lfsr_config=lfsr,
       target_state=target_state,
       method="rainbow",
       chain_count=1000,
       chain_length=100
   )

Glossary
--------

**Chain**
   A sequence of states connected by the state update function.

**Chain Collision**
   When two different chains merge (have the same endpoint).

**Coverage**
   The fraction of state space covered by the table.

**Distinguished Point**
   A state with a special property used to mark chain endpoints.

**False Alarm**
   When a chain appears to contain the target state but doesn't.

**Hellman Table**
   A precomputed table storing chains for fast state recovery (Hellman, 1980).

**Online Attack**
   The phase where precomputed table is used to recover states.

**Optimal Parameters**
   Parameter values that minimize time×memory product.

**Precomputation**
   The initial phase where tables are generated.

**Rainbow Chain**
   A chain where each step uses a different reduction function.

**Rainbow Table**
   An improved TMTO table using multiple reduction functions (Oechslin, 2003).

**Reduction Function**
   A function that maps states to starting points.

**Reduction Function Family**
   A set of different reduction functions, one per step.

**Success Probability**
   The probability that a random state can be recovered from the table.

**Table Lookup**
   The process of searching precomputed tables to find a target state.

**Time-Memory Trade-Off (TMTO)**
   A cryptanalytic technique that precomputes tables to enable faster attacks.

**Trade-Off Curve**
   A graph showing the relationship between time and memory.

Further Reading
---------------

- Hellman, M. E. (1980). "A cryptanalytic time-memory trade-off"

- Oechslin, P. (2003). "Making a faster cryptanalytic time-memory trade-off"

- Barkan, E., Biham, E., & Shamir, A. (2003). "Rigorous bounds on cryptanalytic
  time-memory trade-offs"

- Menezes, A. J., et al. (1996). "Handbook of Applied Cryptography"
