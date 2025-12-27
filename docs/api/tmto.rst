Time-Memory Trade-Off Module
=============================

The time-memory trade-off module provides Hellman tables and Rainbow tables
for efficient state recovery through precomputation.

.. automodule:: lfsr.tmto
   :members:
   :undoc-members:
   :show-inheritance:

Classes
-------

HellmanTable
~~~~~~~~~~~~

.. autoclass:: lfsr.tmto.HellmanTable
   :members:
   :no-index:

Hellman table for time-memory trade-off attacks.

**Key Terminology**:

- **Hellman Table**: Precomputed table storing chains of state transitions
- **Chain**: Sequence of states connected by state update function
- **Distinguished Point**: State with special property marking chain endpoints
- **Reduction Function**: Function mapping states to starting points
- **Table Lookup**: Process of searching table to find target state
- **False Alarm**: When chain appears to contain target but doesn't

**Example**:

.. code-block:: python

   from lfsr.attacks import LFSRConfig
   from lfsr.tmto import HellmanTable
   
   lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
   table = HellmanTable(chain_count=1000, chain_length=100)
   table.generate(lfsr)
   
   target = [1, 0, 1, 1]
   recovered = table.lookup(target, lfsr)
   if recovered:
       print(f"Recovered state: {recovered}")

RainbowTable
~~~~~~~~~~~~

.. autoclass:: lfsr.tmto.RainbowTable
   :members:
   :no-index:

Rainbow table for time-memory trade-off attacks.

**Key Terminology**:

- **Rainbow Table**: Improved TMTO table using multiple reduction functions
- **Rainbow Chain**: Chain with different reduction function at each step
- **Reduction Function Family**: Set of different reduction functions
- **Collision Resistance**: Fewer collisions than Hellman tables

**Example**:

.. code-block:: python

   from lfsr.attacks import LFSRConfig
   from lfsr.tmto import RainbowTable
   
   lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
   table = RainbowTable(chain_count=1000, chain_length=100)
   table.generate(lfsr)
   
   target = [1, 0, 1, 1]
   recovered = table.lookup(target, lfsr)

TMTOAttackResult
~~~~~~~~~~~~~~~~

.. autoclass:: lfsr.tmto.TMTOAttackResult
   :members:
   :no-index:

Results from a time-memory trade-off attack.

Functions
---------

tmto_attack
~~~~~~~~~~~

.. autofunction:: lfsr.tmto.tmto_attack
   :no-index:

Perform time-memory trade-off attack on LFSR.

optimize_tmto_parameters
~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: lfsr.tmto.optimize_tmto_parameters
   :no-index:

Optimize TMTO parameters for given constraints.

Important Notes
---------------

**Precomputation**: Tables must be generated before use. This can be
time-consuming but only needs to be done once. Precomputed tables can be
saved and reused.

**Memory Requirements**: TMTO tables require significant memory. For a
table with m chains of length t, memory is approximately m·t states.

**Coverage**: Success probability depends on coverage. Higher coverage
requires more memory but increases success probability.

**False Alarms**: Lookup may find false alarms (chains that appear to
contain target but don't). These are verified by reconstructing chains.

See Also
--------

* :doc:`../time_memory_tradeoff` for detailed introduction and theory
* :doc:`../mathematical_background` for mathematical foundations
