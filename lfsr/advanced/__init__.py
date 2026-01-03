"""
Advanced LFSR Structures Module

This module provides analysis capabilities for advanced LFSR structures
beyond basic linear feedback shift registers, including non-linear
feedback, filtered LFSRs, clock-controlled LFSRs, multi-output LFSRs,
and irregular clocking patterns.

The module is organized as follows:
- base.py: Base classes and common interfaces
- nonlinear.py: Non-linear feedback LFSRs (NFSRs)
- filtered.py: Filtered LFSRs with non-linear filtering
- clock_controlled.py: Clock-controlled LFSRs
- multi_output.py: Multi-output LFSRs
- irregular_clocking.py: Irregular clocking patterns
"""

from lfsr.advanced.base import (
    AdvancedLFSR,
    AdvancedLFSRConfig,
    AdvancedLFSRAnalysisResult
)

# Import advanced structure implementations
from lfsr.advanced.nonlinear import NFSR, create_simple_nfsr
from lfsr.advanced.filtered import FilteredLFSR, create_simple_filtered_lfsr
from lfsr.advanced.clock_controlled import ClockControlledLFSR, create_stop_and_go_lfsr
from lfsr.advanced.multi_output import MultiOutputLFSR, create_simple_multi_output_lfsr
from lfsr.advanced.irregular_clocking import (
    IrregularClockingLFSR,
    create_stop_and_go_pattern,
    create_step_1_step_2_pattern
)

__all__ = [
    "AdvancedLFSR",
    "AdvancedLFSRConfig",
    "AdvancedLFSRAnalysisResult",
    "NFSR",
    "create_simple_nfsr",
    "FilteredLFSR",
    "create_simple_filtered_lfsr",
    "ClockControlledLFSR",
    "create_stop_and_go_lfsr",
    "MultiOutputLFSR",
    "create_simple_multi_output_lfsr",
    "IrregularClockingLFSR",
    "create_stop_and_go_pattern",
    "create_step_1_step_2_pattern",
]
