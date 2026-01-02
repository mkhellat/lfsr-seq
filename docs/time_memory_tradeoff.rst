Time-Memory Trade-Off Attacks
==============================

This section provides a comprehensive introduction to Time-Memory Trade-Off
(TMTO) attacks, a fundamental cryptanalytic technique for efficient state
recovery. The documentation is designed to be accessible to beginners while
providing sufficient depth for researchers and developers. We begin with
intuitive explanations and gradually build to rigorous mathematical
formulations.

Introduction
------------

**What is a Time-Memory Trade-Off Attack?**

A **time-memory trade-off (TMTO) attack** is a cryptanalytic technique that
precomputes tables to enable faster state recovery. Instead of computing states
on-demand (which is time-intensive), we precompute and store states
(memory-intensive), then look them up during attacks. The fundamental idea is to
trade memory (storage) for computation time, enabling faster attacks after an
initial precomputation phase.

**Historical Context and Motivation**

Time-memory trade-off attacks were first introduced by Martin Hellman in 1980
in his seminal paper "A cryptanalytic time-memory trade-off". Hellman's work
demonstrated that it was possible to break cryptographic systems faster by
precomputing and storing information, fundamentally changing how cryptanalysts
approach state recovery problems.

The technique was later improved by Philippe Oechslin in 2003 with the
introduction of **rainbow tables**, which use different reduction functions at
each step to reduce collisions and improve efficiency. Rainbow tables are
significantly more efficient than Hellman tables for the same memory usage,
making TMTO attacks more practical for real-world applications.

**Why are TMTO Attacks Important?**

1. **Practical Attacks**: Enable faster state recovery after precomputation.
   Once tables are generated, attacks can be performed much faster than
   brute-force methods. This makes TMTO attacks practical for systems where
   online computation is expensive.

2. **Batch Attacks**: The same precomputed table can be used to attack multiple
   targets, amortizing the precomputation cost. This is particularly valuable
   when attacking many instances of the same system.

3. **Demonstrates Real-World Scenarios**: Shows how attackers might precompute
   tables for later use, even if the initial precomputation is time-consuming.
   This models realistic attack scenarios where attackers invest upfront effort.

4. **Theoretical Foundation**: Demonstrates the fundamental trade-off between
   time and memory in cryptanalysis. The relationship :math:`TM^2 = N^2` is a
   fundamental result in cryptanalysis.

5. **Design Guidance**: Understanding TMTO attacks helps designers choose
   appropriate state space sizes and understand the security implications of
   their choices.

**When are TMTO Attacks Applicable?**

TMTO attacks are applicable when:

- **State Space is Manageable**: The state space size :math:`N = q^d` is
  manageable for precomputation. Very large state spaces may require
  impractical amounts of memory or time.

- **Multiple Targets**: Multiple targets need to be attacked, which amortizes
  the precomputation cost. If only attacking a single target, brute-force may
  be more efficient.

- **Online Computation is Expensive**: Computing states on-demand is
  computationally expensive, making precomputation worthwhile.

- **Precomputation Time is Acceptable**: The time required for precomputation
  is acceptable given the number of targets to be attacked.

- **Memory is Available**: Sufficient memory is available for table storage.
  The memory requirement depends on the number of chains :math:`m` and chain length :math:`t`.

**Relationship to Other Attacks**

TMTO attacks complement other cryptanalytic techniques:

- **Brute-Force Attacks**: TMTO attacks trade memory for time, while
  brute-force attacks use minimal memory but maximum time. TMTO attacks are
  more efficient when attacking multiple targets.

- **Correlation Attacks**: Exploit statistical biases; TMTO attacks work
  regardless of statistical properties by precomputing state transitions.

- **Algebraic Attacks**: Solve systems of equations; TMTO attacks use
  precomputation to enable fast lookup, working even when algebraic structure is
  complex.

Understanding TMTO attacks provides a complete picture of the security
landscape for LFSR-based systems.

Key Concepts
------------

Time-Memory Trade-Off
~~~~~~~~~~~~~~~~~~~~~~

**What is a Time-Memory Trade-Off?**

A **time-memory trade-off** is a fundamental principle in cryptanalysis that
allows trading memory (storage) for computation time. By precomputing and
storing information, we can reduce the time needed for online attacks. The
trade-off is governed by the fundamental relationship :math:`TM^2 = N^2`, where
:math:`T` is the online attack time, :math:`M` is the memory (table size), and
:math:`N` is the state space size.

**Key Terminology**:

- **Time-Memory Trade-Off (TMTO)**: A cryptanalytic technique that
  precomputes tables to enable faster attacks. The trade-off is between
  precomputation time/memory and online attack time. First introduced by
  Martin Hellman (1980). The technique fundamentally changes the
  computational complexity of state recovery by allowing precomputation.

- **Precomputation**: The initial phase where tables are generated. This is
  done once and can be reused for multiple attacks. Precomputation is
  time-consuming but only needs to be done once. The precomputation phase
  generates chains of state transitions and stores only the endpoints.

- **Online Attack**: The phase where the precomputed table is used to
  recover states. This is much faster than computing states on-demand.
  Online attacks can be performed quickly using the precomputed table,
  typically requiring only table lookups and chain reconstruction.

- **Trade-Off Curve**: A graph showing the relationship between time and
  memory for different parameter choices. The curve demonstrates how
  increasing memory reduces attack time (and vice versa). Points on the curve
  represent different parameter choices that achieve the same trade-off.

- **Coverage**: The fraction of the state space covered by the table.
  Coverage :math:`= \frac{\text{number of unique states in table}}{\text{total state space size}}`.
  Higher coverage increases success probability but requires more memory.
  Coverage is affected by chain collisions, which reduce the number of unique
  states covered.

- **Success Probability**: The probability that a random state can be
  recovered from the table. This depends on coverage and collision rate.
  Higher coverage generally means higher success probability. The success
  probability can be estimated as approximately equal to the coverage for
  tables with low collision rates.

**Mathematical Foundation**:

The fundamental trade-off relationship is:

.. math::

   TM^2 = N^2

where:
- :math:`T` is the time for online attack (number of operations)
- :math:`M` is the memory (table size, number of stored entries)
- :math:`N` is the state space size (:math:`q^d` for LFSR of degree :math:`d` over :math:`\mathbb{F}_q`)

This means that to reduce attack time by a factor of :math:`k`, we need
:math:`k^2` times more memory (or vice versa). For example, to reduce attack
time by a factor of 10, we need 100 times more memory.

**Derivation**:

The relationship :math:`TM^2 = N^2` can be understood as follows:

1. A table with :math:`M` chains of length :math:`T` covers approximately
   :math:`M \cdot T` states (with some overlap due to collisions).

2. To cover the entire state space :math:`N`, we need :math:`M \cdot T \geq N`.

3. The optimal trade-off occurs when :math:`M \cdot T = N` and :math:`T = M` (equal
   time and memory), giving :math:`T^2 = N` or :math:`M^2 = N`.

4. More generally, for any trade-off point, we have :math:`T \cdot M^2 = N^2` or
   equivalently :math:`T^2 \cdot M = N^2`.

**Properties**:

- **Symmetric Trade-Off**: The relationship is symmetric in time and memory.
  Doubling memory :math:`M` reduces time :math:`T` by a factor of 4, and vice versa.

- **Optimal Point**: The optimal trade-off occurs when :math:`T = M = N^{1/2}`,
  requiring both time :math:`T` and memory :math:`M` proportional to the square root of the state
  space size :math:`N`.

- **Practical Considerations**: In practice, memory :math:`M` may be more constrained
  than time :math:`T`, leading to choices where :math:`M < T` (more time, less memory)
  or vice versa.

Hellman Tables
~~~~~~~~~~~~~~

**What is a Hellman Table?**

A **Hellman table** is a precomputed table that stores chains of state
transitions, allowing fast state recovery. Named after Martin Hellman (1980),
it was the first time-memory trade-off technique. Hellman tables use a single
reduction function throughout each chain, making them simpler but more prone to
collisions than rainbow tables.

**Key Terminology**:

- **Hellman Table**: A precomputed table storing chains of state transitions.
  Each chain starts with a random state and ends with a distinguished point.
  The table enables fast state recovery by looking up chains that might
  contain the target state. Only the start and end points of chains are
  stored, reducing memory requirements.

- **Chain**: A sequence of states connected by the state update function and
  reduction function. Each chain has length :math:`t` and represents :math:`t`
  consecutive state transitions. A chain is:
  :math:`S_0 \rightarrow f(S_0) \rightarrow R(f(S_0)) \rightarrow f(R(f(S_0))) \rightarrow \ldots`
  where :math:`f: \mathbb{F}_q^d \rightarrow \mathbb{F}_q^d` is the state update function and
  :math:`R: \mathbb{F}_q^d \rightarrow \mathbb{F}_q^d` is the reduction
  function. Chains are the fundamental building blocks of Hellman tables.

- **Distinguished Point**: A state with a special property (e.g., leading
  :math:`k` bits are zero) used to mark chain endpoints. Distinguished points
  make chain endpoints easy to identify and store, reducing storage
  requirements. Only chains ending at distinguished points are stored. The
  probability that a random state is distinguished is :math:`2^{-k}`, where
  :math:`k` is the number of distinguished bits. For a state space of size
  :math:`N`, the expected number of attempts to find a distinguished point is
  approximately :math:`2^k`.

- **Reduction Function**: A function :math:`R: \mathbb{F}_q^d \rightarrow \mathbb{F}_q^d`
  that maps states to starting points (keys). The reduction function creates
  chains by providing a way to "reduce" a state back to a starting point.
  Different reduction functions can be used to create different chains. The
  reduction function should be deterministic and efficiently computable.

- **Table Lookup**: The process of searching precomputed tables to find a
  target state :math:`S`. Lookup involves: (1) applying reduction function
  :math:`R(S)` to target, (2) checking if result is a chain endpoint, (3) if
  found, reconstructing chain to find target. Lookup is much faster than
  computing states on-demand, typically requiring :math:`O(t)` operations where
  :math:`t` is the chain length.

- **False Alarm**: When a chain appears to contain the target state :math:`S` but
  doesn't. This occurs due to collisions in the reduction function :math:`R`
  (different states map to the same starting point). False alarms must be
  verified by reconstructing the chain. The false alarm rate depends on the
  collision rate of the reduction function :math:`R`.

- **Chain Collision**: When two different chains merge (have the same
  endpoint). Collisions reduce table efficiency because they cover fewer
  unique states. Hellman tables can have significant collisions, especially
  when using the same reduction function :math:`R` for all chains. The
  collision rate increases with the number of chains :math:`m` and chain length
  :math:`t`.

**Mathematical Foundation**:

A Hellman table consists of :math:`m` chains, each of length :math:`t`. The
table covers approximately :math:`m \cdot t` states (with some overlap due to
collisions). The coverage is:

.. math::

   \text{coverage} = \frac{m \cdot t}{N}

where :math:`N` is the state space size. However, due to collisions, the actual
coverage is less than :math:`m \cdot t / N`. The expected number of unique
states covered is approximately:

.. math::

   E[\text{unique states}] = N \left(1 - e^{-mt/N}\right)

This follows from the birthday paradox: the probability that a random state is
not covered by any chain is :math:`e^{-m \cdot t/N}`, so the expected coverage is
:math:`1 - e^{-m \cdot t/N}`.

**Algorithm**:

1. **Precomputation Phase**:
   
   - Generate :math:`m` random starting states :math:`S_0^{(1)}, \ldots, S_0^{(m)}`
   - For each starting state, compute a chain:
     :math:`S_0 \rightarrow f(S_0) \rightarrow R(f(S_0)) \rightarrow f(R(f(S_0))) \rightarrow \ldots \rightarrow S_t`
   - Store only :math:`(S_0, S_t)` pairs where :math:`S_t` is a distinguished point
   - Repeat until :math:`m` chains with distinguished endpoints are created
   - If a chain does not reach a distinguished point within :math:`t` steps,
     store it anyway (using the final state as endpoint)

2. **Lookup Phase**:
   
   - Given target state :math:`S`, apply reduction function: :math:`R(S)`
   - Check if :math:`R(S)` is a chain endpoint in table
   - If found, reconstruct chain from start to find :math:`S`
   - If not found, apply :math:`f` then :math:`R` repeatedly (up to :math:`t` times):
     :math:`S \rightarrow f(S) \rightarrow R(f(S)) \rightarrow f(R(f(S))) \rightarrow \ldots`
   - Check each intermediate state against chain endpoints

**Complexity Analysis**:

- **Precomputation Time**: :math:`O(m \cdot t)` state transitions. Each chain
  requires :math:`t` state updates, and we generate :math:`m` chains. Total
  operations: :math:`m \cdot t`.

- **Precomputation Memory**: :math:`O(m)` storage for :math:`m` (start, end)
  pairs. Each pair requires :math:`2d` field elements, where :math:`d` is the
  LFSR degree.

- **Lookup Time**: :math:`O(t)` in the best case (immediate match), :math:`O(t^2)`
  in the worst case (checking all positions in all chains). Average case is
  :math:`O(t)` if the target is in a chain.

- **Lookup Memory**: :math:`O(1)` additional memory beyond the precomputed table.

**Advantages**:

- Faster state recovery after precomputation (typically :math:`O(t)` vs
  :math:`O(N)` for brute-force, where :math:`t` is chain length and :math:`N` is state space size)
- Can attack multiple targets using same table (amortizes precomputation cost)
- Demonstrates practical attack scenarios
- Simple to implement and understand
- Memory-efficient (only stores endpoints, not entire chains)

**Limitations**:

- Requires significant memory for large state spaces
- Precomputation can be time-consuming (must generate all chains)
- False alarms require verification (reconstructing chains)
- Coverage may be incomplete (due to collisions)
- Chain collisions reduce efficiency (fewer unique states covered)
- Success probability depends on coverage and collision rate

**Example**:

Consider an LFSR over :math:`\mathbb{F}_2` with degree :math:`d = 4`, giving
state space size :math:`N = q^d = 2^4 = 16`. We create a Hellman table with
:math:`m = 4` chains of length :math:`t = 3`.

**Precomputation**:

1. Generate random starting states: :math:`S_0^{(1)} = (1,0,0,0)`,
   :math:`S_0^{(2)} = (0,1,0,0)`, :math:`S_0^{(3)} = (1,1,0,0)`,
   :math:`S_0^{(4)} = (0,0,1,0)`

2. For each starting state, compute chain until distinguished point (leading
   bit is 0) or length :math:`t = 3`:

   - Chain 1: :math:`(1,0,0,0) \rightarrow (0,0,0,1) \rightarrow (0,0,1,0) \rightarrow (0,1,0,0)`
     (endpoint: :math:`(0,1,0,0)`, distinguished)
   - Chain 2: :math:`(0,1,0,0) \rightarrow (1,0,0,1) \rightarrow (0,0,1,1) \rightarrow (0,1,1,0)`
     (endpoint: :math:`(0,1,1,0)`, distinguished)
   - Chain 3: :math:`(1,1,0,0) \rightarrow (1,0,1,1) \rightarrow (0,1,1,1) \rightarrow (1,1,1,0)`
     (endpoint: :math:`(1,1,1,0)`, not distinguished, but stored)
   - Chain 4: :math:`(0,0,1,0) \rightarrow (0,1,0,1) \rightarrow (1,0,1,0) \rightarrow (0,1,0,1)`
     (endpoint: :math:`(0,1,0,1)`, distinguished)

3. Store table: :math:`\{(1,0,0,0), (0,1,0,0)\}`, :math:`\{(0,1,0,0), (0,1,1,0)\}`,
   :math:`\{(1,1,0,0), (1,1,1,0)\}`, :math:`\{(0,0,1,0), (0,1,0,1)\}`

**Lookup**:

Given target state :math:`S = (0,0,1,1)`:

1. Apply reduction: :math:`R(S) = (0,0,1,1)` (example reduction function :math:`R`)
2. Check if :math:`(0,0,1,1)` is an endpoint: No
3. Apply state update function :math:`f` then reduction :math:`R`:
   :math:`f(S) = (0,1,1,0)`, :math:`R(f(S)) = (0,1,1,0)`
4. Check if :math:`(0,1,1,0)` is an endpoint: Yes (Chain 2)
5. Reconstruct Chain 2 from start: :math:`(0,1,0,0) \rightarrow (1,0,0,1) \rightarrow (0,0,1,1)`
6. Found target :math:`(0,0,1,1)` at step 2, so initial state is :math:`(0,1,0,0)`

Rainbow Tables
~~~~~~~~~~~~~~~

**What is a Rainbow Table?**

A **rainbow table** is an improved version of Hellman tables that uses
different reduction functions at each step, reducing collisions. Introduced by
Philippe Oechslin (2003), rainbow tables are more efficient than Hellman
tables for the same memory usage. The name "rainbow" comes from using different
"colors" (reduction functions) at each step, like colors in a rainbow.

**Key Terminology**:

- **Rainbow Table**: A precomputed table using different reduction functions
  at each step (like colors in a rainbow). This reduces collisions compared
  to Hellman tables, which use the same reduction function. Rainbow tables
  are named for the "rainbow" of different reduction functions used. Each
  step uses a different reduction function, making collisions less likely.

- **Rainbow Chain**: A chain where each step uses a different reduction
  function :math:`R_1, R_2, \ldots, R_t`. The chain is:
  :math:`S_0 \rightarrow f(S_0) \rightarrow R_1(f(S_0)) \rightarrow f(R_1(f(S_0))) \rightarrow R_2(f(R_1(f(S_0)))) \rightarrow \ldots`
  Each step uses a different "color" (reduction function :math:`R_i` for step
  :math:`i`). This structure reduces collisions because two chains can only
  merge if they collide at the same step :math:`i` with the same reduction
  function :math:`R_i`.

- **Reduction Function Family**: A set of :math:`t` different reduction
  functions :math:`\{R_1, R_2, \ldots, R_t\}`, one for each step in the chain.
  Each function :math:`R_i: \mathbb{F}_q^d \rightarrow \mathbb{F}_q^d` maps states to starting
  points, but they differ to reduce collisions. The family ensures that
  collisions are less likely than in Hellman tables. Typically, reduction
  functions are created by incorporating the step number :math:`i` into a hash
  function.

- **Collision Resistance**: Rainbow tables have fewer collisions than Hellman
  tables because different reduction functions are used at each step. For two
  chains to merge, they must collide at the same step with the same reduction
  function, which is less likely than in Hellman tables where the same
  reduction function is used at all steps. This property makes rainbow tables
  more efficient for the same memory usage.

- **Table Lookup**: Similar to Hellman tables, but must try all reduction
  functions in reverse order. For target state :math:`S`, we check
  :math:`R_t(S)`, :math:`R_{t-1}(f(S))`, :math:`R_{t-2}(f^2(S))`, etc., where
  :math:`f^k(S)` denotes applying the state update function :math:`f` :math:`k`
  times. This ensures we check all possible positions in chains. The lookup
  process is more complex than Hellman tables but still efficient.

**Mathematical Foundation**:

Rainbow tables use :math:`t` different reduction functions :math:`R_1, R_2, \ldots, R_t`.
A chain of length :math:`t` is:

.. math::

   S_0 \rightarrow f(S_0) \rightarrow R_1(f(S_0)) \rightarrow f(R_1(f(S_0))) \rightarrow \ldots \rightarrow S_t

This reduces collisions because merging chains requires collisions at the same
step with the same reduction function, which is less likely than using the
same reduction function at all steps.

**Collision Analysis**:

In a Hellman table, two chains can merge if they collide at any step, since the
same reduction function :math:`R` is used throughout. In a rainbow table, two
chains can only merge if they collide at the same step :math:`i` with the same
reduction function :math:`R_i`. This makes collisions significantly less likely.

The expected number of collisions in a rainbow table with :math:`m` chains of
length :math:`t` is approximately:

.. math::

   E[\text{collisions}] \approx \frac{m^2}{2N} \cdot \frac{t}{t+1}

compared to approximately :math:`m^2/(2N)` for Hellman tables, where :math:`m`
is the number of chains and :math:`N` is the state space size. The factor
:math:`t/(t+1)` shows that rainbow tables have fewer collisions, especially for
long chains (as :math:`t \to \infty`, the factor approaches 1).

**Algorithm**:

1. **Precomputation Phase**:
   
   - Generate :math:`m` random starting states :math:`S_0^{(1)}, \ldots, S_0^{(m)}`
   - Create reduction function family :math:`\{R_1, R_2, \ldots, R_t\}` where
     each :math:`R_i: \mathbb{F}_q^d \rightarrow \mathbb{F}_q^d`
   - For each starting state :math:`S_0`, compute a rainbow chain:
     :math:`S_0 \rightarrow f(S_0) \rightarrow R_1(f(S_0)) \rightarrow f(R_1(f(S_0))) \rightarrow R_2(f(R_1(f(S_0)))) \rightarrow \ldots \rightarrow S_t`
   - Store only :math:`(S_0, S_t)` pairs where :math:`S_t` is a distinguished point
   - Repeat until :math:`m` chains with distinguished endpoints are created

2. **Lookup Phase**:
   
   - Given target state :math:`S`, try all reduction functions in reverse order:
     - Check :math:`R_t(S)` against chain endpoints
     - Check :math:`R_{t-1}(f(S))` against chain endpoints, where :math:`f(S)`
       is the state after one update
     - Check :math:`R_{t-2}(f^2(S))` against chain endpoints, where
       :math:`f^2(S) = f(f(S))` is the state after two updates
     - Continue until :math:`R_1(f^{t-1}(S))` is checked, where
       :math:`f^{t-1}(S)` is the state after :math:`t-1` updates
   - If a match is found, reconstruct chain from start to find :math:`S`
   - The lookup requires at most :math:`t` checks (one per reduction function
     :math:`R_i` for :math:`i = t, t-1, \ldots, 1`)

**Complexity Analysis**:

- **Precomputation Time**: :math:`O(m \cdot t)` state transitions, same as
  Hellman tables. However, rainbow tables may require fewer chains :math:`m` due
  to reduced collisions for the same coverage.

- **Precomputation Memory**: :math:`O(m)` storage for :math:`m` (start, end)
  pairs, same as Hellman tables. Each pair requires :math:`2d` field elements,
  where :math:`d` is the LFSR degree.

- **Lookup Time**: :math:`O(t)` in all cases (must check all :math:`t`
  reduction functions :math:`R_1, \ldots, R_t`). This is more predictable than
  Hellman tables, which have variable lookup time.

- **Lookup Memory**: :math:`O(1)` additional memory beyond the precomputed table.

**Advantages over Hellman Tables**:

- **Fewer Collisions**: More efficient use of memory due to reduced collisions.
  The same memory can cover more unique states.

- **Better Coverage**: For the same memory usage, rainbow tables typically
  achieve higher coverage than Hellman tables.

- **More Predictable Lookup**: Lookup time is always :math:`O(t)`, making it
  more predictable than Hellman tables.

- **More Practical**: Better suited for real-world attacks due to improved
  efficiency.

**Limitations**:

- Still requires significant memory for large state spaces
- Precomputation can be time-consuming (must generate all chains)
- Lookup requires trying all reduction functions (more complex than Hellman)
- Coverage may still be incomplete for very large state spaces
- More complex implementation than Hellman tables

**Example**:

Using the same LFSR as before (degree :math:`d = 4`, state space size
:math:`N = q^d = 2^4 = 16`), we create a rainbow table with :math:`m = 4`
chains of length :math:`t = 3`, using reduction functions
:math:`R_1, R_2, R_3`.

**Precomputation**:

1. Generate random starting states: :math:`S_0^{(1)} = (1,0,0,0)`,
   :math:`S_0^{(2)} = (0,1,0,0)`, :math:`S_0^{(3)} = (1,1,0,0)`,
   :math:`S_0^{(4)} = (0,0,1,0)`

2. For each starting state, compute rainbow chain using reduction functions
   :math:`R_1, R_2, R_3`:

   - Chain 1: :math:`(1,0,0,0) \rightarrow f \rightarrow R_1 \rightarrow f \rightarrow R_2 \rightarrow f \rightarrow R_3 \rightarrow (0,1,0,0)`
   - Chain 2: :math:`(0,1,0,0) \rightarrow f \rightarrow R_1 \rightarrow f \rightarrow R_2 \rightarrow f \rightarrow R_3 \rightarrow (0,1,1,0)`
   - Chain 3: :math:`(1,1,0,0) \rightarrow f \rightarrow R_1 \rightarrow f \rightarrow R_2 \rightarrow f \rightarrow R_3 \rightarrow (1,1,1,0)`
   - Chain 4: :math:`(0,0,1,0) \rightarrow f \rightarrow R_1 \rightarrow f \rightarrow R_2 \rightarrow f \rightarrow R_3 \rightarrow (0,1,0,1)`

3. Store table: :math:`\{(1,0,0,0), (0,1,0,0)\}`, :math:`\{(0,1,0,0), (0,1,1,0)\}`,
   :math:`\{(1,1,0,0), (1,1,1,0)\}`, :math:`\{(0,0,1,0), (0,1,0,1)\}`

**Lookup**:

Given target state :math:`S = (0,0,1,1)`:

1. Check :math:`R_3(S) = R_3(0,0,1,1) = (0,0,1,1)` against endpoints: No match
2. Check :math:`R_2(f(S)) = R_2(f(0,0,1,1)) = R_2(0,1,1,0) = (0,1,1,0)` against
   endpoints: Match (Chain 2)
3. Reconstruct Chain 2 from start using reduction functions :math:`R_1, R_2, R_3`:
   :math:`(0,1,0,0) \rightarrow f \rightarrow R_1 \rightarrow f \rightarrow (0,0,1,1)`
4. Found target :math:`(0,0,1,1)` at step 2, so initial state is :math:`(0,1,0,0)`

Trade-Off Parameter Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**What is Parameter Optimization?**

**Parameter optimization** finds the best values for :math:`m` (chain count)
and :math:`t` (chain length) to maximize success probability given memory
constraints. The optimization problem is to choose :math:`m` and :math:`t` such
that :math:`m \cdot t` (memory requirement) is fixed and coverage is maximized.

**Key Terminology**:

- **Optimal Parameters**: Parameter values that minimize the time×memory
  product :math:`T \cdot M` for a given success probability. These parameters
  provide the best trade-off between time :math:`T` and memory :math:`M`.
  Optimal parameters depend on the state space size :math:`N` and available
  memory. For the fundamental trade-off :math:`T \cdot M^2 = N^2`, optimal
  parameters satisfy :math:`T = M = N^{1/2}`, where :math:`N = q^d` for an LFSR
  of degree :math:`d` over :math:`\mathbb{F}_q`.

- **Trade-Off Curve**: A graph showing the relationship between time and
  memory for different parameter choices. The curve shows how increasing
  memory reduces attack time (and vice versa). Points on the curve represent
  different parameter choices that achieve the same trade-off. The curve
  follows :math:`TM^2 = N^2`.

- **Coverage Analysis**: Determining what fraction of the state space is
  covered by a table with given parameters. Coverage analysis helps choose
  parameters that provide desired success probability. The coverage depends on
  chain count :math:`m`, chain length :math:`t`, state space size :math:`N`, and
  the collision rate.

- **Success Probability Estimation**: Estimating the probability that a
  random state can be recovered from a table. This depends on coverage,
  collision rate, and table structure. For tables with low collision rates,
  success probability is approximately equal to coverage.

**Optimization Strategy**:

1. **Given Constraints**: Memory limit :math:`M_{\max}`, state space size
   :math:`N`, target success probability :math:`p_{\text{target}}`

2. **Try Different Parameter Combinations**: For each :math:`m` and :math:`t`
   such that :math:`m \cdot t \leq M_{\max}`:
   
   - Estimate coverage: :math:`\text{coverage} \approx 1 - e^{-m \cdot t/N}`
   - Estimate success probability: :math:`p \approx \text{coverage}` (for low
     collision rates)
   - Compute time: :math:`T = m \cdot t` (for lookup)

3. **Select Optimal Parameters**: Choose :math:`m` and :math:`t` that:
   - Maximize success probability :math:`p \geq p_{\text{target}}`
   - Minimize time :math:`T` (or time×memory product :math:`T \cdot M`)
   - Satisfy memory constraint :math:`m \cdot t \leq M_{\max}`

4. **Verify Parameters**: Test parameters on sample data to verify success
   probability meets target.

**Theoretical Bounds**:

For the fundamental trade-off :math:`T \cdot M^2 = N^2`:

- **Minimum Memory**: :math:`M_{\min} = N^{1/2}` (when :math:`T = N^{1/2}`)
- **Minimum Time**: :math:`T_{\min} = N^{1/2}` (when :math:`M = N^{1/2}`)
- **Optimal Point**: :math:`T = M = N^{1/2}` (equal time and memory)

For practical constraints, if memory is limited to :math:`M < N^{1/2}`, then
time must be :math:`T > N^2/M` to maintain the trade-off, where :math:`N` is the
state space size.

**Practical Considerations**:

- **Memory Constraints**: In practice, memory may be more constrained than
  time, leading to choices where :math:`M < T`. This means accepting longer
  lookup times to reduce memory requirements.

- **Precomputation Time**: Precomputation time is :math:`O(m \cdot t)`, where
  :math:`m` is the number of chains and :math:`t` is the chain length. This must
  be acceptable given the number of targets to be attacked.

- **Collision Rate**: Higher collision rates reduce coverage, so parameters
  should be chosen to minimize collisions. Rainbow tables typically have lower
  collision rates than Hellman tables.

- **Distinguished Point Probability**: The probability of finding a
  distinguished point is :math:`2^{-k}`, where :math:`k` is the number of
  distinguished bits. This affects precomputation time. Lower probability (more
  distinguished bits, larger :math:`k`) requires more attempts but may reduce
  storage.

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
   from lfsr.tmto import tmto_attack
   
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
       print(f"Lookup time: {result.lookup_time:.4f} seconds")
   
   # Rainbow table attack
   result2 = tmto_attack(
       lfsr_config=lfsr,
       target_state=target_state,
       method="rainbow",
       chain_count=1000,
       chain_length=100
   )
   
   if result2.attack_successful:
       print(f"Recovered state: {result2.recovered_state}")
       print(f"Coverage: {result2.coverage:.2%}")

For complete examples, see ``examples/tmto_attack_example.py``.

Glossary
--------

**Chain**
   A sequence of states connected by the state update function and reduction
   function. Each chain represents multiple consecutive state transitions.

**Chain Collision**
   When two different chains merge (have the same endpoint). Collisions reduce
   table efficiency by covering fewer unique states.

**Coverage**
   The fraction of state space covered by the table. Coverage
   :math:`= \frac{\text{number of unique states in table}}{\text{total state space size}}`.
   Higher coverage increases success probability.

**Distinguished Point**
   A state with a special property (e.g., leading bits are zero) used to mark
   chain endpoints. Only chains ending at distinguished points are stored.

**False Alarm**
   When a chain appears to contain the target state but doesn't. This occurs
   due to collisions in the reduction function and must be verified by
   reconstructing the chain.

**Hellman Table**
   A precomputed table storing chains for fast state recovery, using a single
   reduction function throughout each chain (Hellman, 1980).

**Online Attack**
   The phase where precomputed table is used to recover states. This is much
   faster than computing states on-demand.

**Optimal Parameters**
   Parameter values that minimize the time×memory product :math:`T \cdot M` for
   a given success probability. Optimal parameters satisfy :math:`T = M = N^{1/2}`
   for the fundamental trade-off :math:`T \cdot M^2 = N^2`.

**Precomputation**
   The initial phase where tables are generated. This is done once and can be
   reused for multiple attacks.

**Rainbow Chain**
   A chain where each step uses a different reduction function. Rainbow chains
   have fewer collisions than Hellman chains.

**Rainbow Table**
   An improved TMTO table using multiple reduction functions (one per step) to
   reduce collisions (Oechslin, 2003).

**Reduction Function**
   A function that maps states to starting points. The reduction function
   creates chains by providing a way to "reduce" a state back to a starting
   point.

**Reduction Function Family**
   A set of different reduction functions, one per step in a rainbow chain.
   Each function maps states to starting points, but they differ to reduce
   collisions.

**Success Probability**
   The probability that a random state can be recovered from the table. This
   depends on coverage and collision rate. For tables with low collision rates,
   success probability is approximately equal to coverage.

**Table Lookup**
   The process of searching precomputed tables to find a target state. Lookup
   involves applying reduction functions and checking chain endpoints.

**Time-Memory Trade-Off (TMTO)**
   A cryptanalytic technique that precomputes tables to enable faster attacks.
   The trade-off is governed by :math:`T \cdot M^2 = N^2`, where :math:`T` is
   time, :math:`M` is memory, and :math:`N` is state space size.

**Trade-Off Curve**
   A graph showing the relationship between time and memory for different
   parameter choices. The curve follows :math:`TM^2 = N^2` and demonstrates how
   increasing memory reduces attack time.

Further Reading
---------------

- **Hellman, M. E.** (1980). "A cryptanalytic time-memory trade-off". IEEE
  Transactions on Information Theory, 26(4), 401-406. The original paper
  introducing time-memory trade-off attacks.

- **Oechslin, P.** (2003). "Making a faster cryptanalytic time-memory
  trade-off". Advances in Cryptology - CRYPTO 2003, 617-630. Introduces
  rainbow tables as an improvement over Hellman tables.

- **Barkan, E., Biham, E., & Shamir, A.** (2003). "Rigorous bounds on
  cryptanalytic time-memory trade-offs". Advances in Cryptology - CRYPTO 2003,
  1-21. Provides rigorous theoretical analysis of time-memory trade-offs.

- **Menezes, A. J., van Oorschot, P. C., & Vanstone, S. A.** (1996).
  "Handbook of Applied Cryptography". CRC Press. Chapter 7 covers
  time-memory trade-off attacks and related techniques.

- **Stinson, D. R.** (2005). "Cryptography: Theory and Practice". CRC Press.
  Chapter 4 discusses time-memory trade-offs in the context of stream ciphers.
