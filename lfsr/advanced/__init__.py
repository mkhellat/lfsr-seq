"""
Advanced LFSR Structures Module

This module provides analysis capabilities for advanced LFSR structures beyond
basic linear feedback shift registers, including non-linear feedback, filtered
LFSRs, clock-controlled LFSRs, multi-output LFSRs, and irregular clocking patterns.

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
from lfsr.advanced.nonlinear import NonLinearLFSR, NFSR
from lfsr.advanced.filtered import FilteredLFSR
from lfsr.advanced.clock_controlled import ClockControlledLFSR
from lfsr.advanced.multi_output import MultiOutputLFSR
from lfsr.advanced.irregular_clocking import StopAndGoLFSR, Step1Step2LFSR

__all__ = [
    "AdvancedLFSR",
    "AdvancedLFSRConfig",
    "AdvancedLFSRAnalysisResult",
    "NonLinearLFSR",
    "NFSR",
    "FilteredLFSR",
    "ClockControlledLFSR",
    "MultiOutputLFSR",
    "StopAndGoLFSR",
    "Step1Step2LFSR",
]
