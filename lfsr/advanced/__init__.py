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

__all__ = [
    "AdvancedLFSR",
    "AdvancedLFSRConfig",
    "AdvancedLFSRAnalysisResult",
]
