Advanced LFSR Structures API
==============================

The advanced LFSR structures module provides analysis capabilities for
non-linear feedback, filtered LFSRs, clock-controlled LFSRs, multi-output
LFSRs, and irregular clocking patterns.

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

Non-Linear Feedback LFSRs
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: lfsr.advanced.nonlinear.NFSR
   :members:
   :no-index:

Non-Linear Feedback Shift Register (NFSR) implementation.

.. autofunction:: lfsr.advanced.nonlinear.create_nfsr_with_and_feedback
   :no-index:

Create NFSR with AND-based feedback function.

.. autofunction:: lfsr.advanced.nonlinear.create_nfsr_with_combined_feedback
   :no-index:

Create NFSR with combined linear and non-linear feedback.

Filtered LFSRs
~~~~~~~~~~~~~~

.. autoclass:: lfsr.advanced.filtered.FilteredLFSR
   :members:
   :no-index:

Filtered LFSR implementation.

.. autofunction:: lfsr.advanced.filtered.create_filtered_lfsr_with_and_filter
   :no-index:

Create Filtered LFSR with AND-based filter function.

Clock-Controlled LFSRs
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: lfsr.advanced.clock_controlled.ClockControlledLFSR
   :members:
   :no-index:

Clock-Controlled LFSR implementation.

.. autofunction:: lfsr.advanced.clock_controlled.create_stop_and_go_lfsr
   :no-index:

Create stop-and-go clock-controlled LFSR.

.. autofunction:: lfsr.advanced.clock_controlled.create_step1_step2_lfsr
   :no-index:

Create step-1/step-2 clock-controlled LFSR.

Multi-Output LFSRs
~~~~~~~~~~~~~~~~~~

.. autoclass:: lfsr.advanced.multi_output.MultiOutputLFSR
   :members:
   :no-index:

Multi-Output LFSR implementation.

.. autofunction:: lfsr.advanced.multi_output.create_direct_output_lfsr
   :no-index:

Create multi-output LFSR with direct output from state positions.

Irregular Clocking Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: lfsr.advanced.irregular_clocking.IrregularClockingLFSR
   :members:
   :no-index:

LFSR with irregular clocking pattern.

**Example**:

.. code-block:: python

   from lfsr.advanced import NFSR, FilteredLFSR, ClockControlledLFSR
   from lfsr.attacks import LFSRConfig
   
   base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
   
   # NFSR
   def nfsr_feedback(state):
       return (state[0] & state[1]) ^ state[2]
   nfsr = NFSR(base_lfsr, nfsr_feedback)
   
   # Filtered LFSR
   def filter_func(state):
       return (state[0] & state[1]) ^ state[2]
   filtered = FilteredLFSR(base_lfsr, filter_func)
   
   # Clock-controlled LFSR
   def clock_control(state):
       return 1 if state[0] == 1 else 0
   cclfsr = ClockControlledLFSR(base_lfsr, clock_control)

See Also
--------

* :doc:`../advanced_lfsr_structures` for detailed introduction and theory
* :doc:`../mathematical_background` for mathematical foundations
