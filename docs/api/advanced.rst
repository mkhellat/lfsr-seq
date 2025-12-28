Advanced LFSR Structures API
==============================

The advanced LFSR structures module provides analysis capabilities for
non-linear feedback, filtered, clock-controlled, multi-output, and irregular
clocking LFSRs.

.. automodule:: lfsr.advanced
   :members:
   :undoc-members:
   :show-inheritance:

Base Classes
------------

AdvancedLFSR
~~~~~~~~~~~~

.. autoclass:: lfsr.advanced.base.AdvancedLFSR
   :members:
   :no-index:

Abstract base class for advanced LFSR structures.

AdvancedLFSRConfig
~~~~~~~~~~~~~~~~~~

.. autoclass:: lfsr.advanced.base.AdvancedLFSRConfig
   :members:
   :no-index:

Configuration for an advanced LFSR structure.

AdvancedLFSRAnalysisResult
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: lfsr.advanced.base.AdvancedLFSRAnalysisResult
   :members:
   :no-index:

Results from advanced LFSR structure analysis.

Structure Implementations
--------------------------

Non-Linear Feedback LFSRs (NFSRs)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: lfsr.advanced.nonlinear.NFSR
   :members:
   :no-index:

Non-linear feedback shift register implementation.

.. autofunction:: lfsr.advanced.nonlinear.create_simple_nfsr
   :no-index:

Helper function to create a simple NFSR.

Filtered LFSRs
~~~~~~~~~~~~~~

.. autoclass:: lfsr.advanced.filtered.FilteredLFSR
   :members:
   :no-index:

Filtered LFSR implementation.

.. autofunction:: lfsr.advanced.filtered.create_simple_filtered_lfsr
   :no-index:

Helper function to create a simple filtered LFSR.

Clock-Controlled LFSRs
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: lfsr.advanced.clock_controlled.ClockControlledLFSR
   :members:
   :no-index:

Clock-controlled LFSR implementation.

.. autofunction:: lfsr.advanced.clock_controlled.create_stop_and_go_lfsr
   :no-index:

Create a stop-and-go clock-controlled LFSR.

Multi-Output LFSRs
~~~~~~~~~~~~~~~~~~

.. autoclass:: lfsr.advanced.multi_output.MultiOutputLFSR
   :members:
   :no-index:

Multi-output LFSR implementation.

.. autofunction:: lfsr.advanced.multi_output.create_simple_multi_output_lfsr
   :no-index:

Helper function to create a simple multi-output LFSR.

Irregular Clocking Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: lfsr.advanced.irregular_clocking.IrregularClockingLFSR
   :members:
   :no-index:

Irregular clocking LFSR implementation.

.. autofunction:: lfsr.advanced.irregular_clocking.create_stop_and_go_pattern
   :no-index:

Create stop-and-go clocking pattern function.

.. autofunction:: lfsr.advanced.irregular_clocking.create_step_1_step_2_pattern
   :no-index:

Create step-1/step-2 clocking pattern function.

Important Notes
---------------

**Non-Linearity**: Advanced structures introduce non-linearity to break
linearity weaknesses of basic LFSRs. This provides better security but
may make analysis more complex.

**Security Trade-offs**: Each structure type has different security properties
and trade-offs. Filtered LFSRs provide good security but require careful
filter function design. Clock-controlled LFSRs provide irregularity but
may be vulnerable to clock control analysis.

**Analysis Complexity**: Advanced structures are generally more complex to
analyze than basic LFSRs. The tool provides analysis capabilities but
full security assessment may require additional research.

See Also
--------

* :doc:`../advanced_lfsr_structures` for detailed introduction and theory
* :doc:`../mathematical_background` for mathematical foundations
