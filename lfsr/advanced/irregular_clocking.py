#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Irregular Clocking Patterns Analysis

This module provides analysis capabilities for LFSRs with irregular clocking
patterns, including stop-and-go, step-1/step-2, and other patterns.

**Historical Context**:

Irregular clocking patterns were developed to introduce unpredictability into
LFSR sequences. By making the clocking pattern irregular, these patterns
increase the complexity of the generated sequences and make cryptanalysis
more difficult.

**Key Terminology**:

- **Irregular Clocking**: Clocking pattern that is not regular (not every step).
  The LFSR may advance 0, 1, or more steps depending on the pattern.

- **Clock Control Pattern**: A specific pattern determining clocking behavior.
  Common patterns include stop-and-go, step-1/step-2, and others.

- **Stop-and-Go**: Clock control pattern where LFSR stops (0 steps) when control
  bit is 0 and advances (1 step) when control bit is 1.

- **Step-1/Step-2**: Clock control pattern where LFSR advances 1 step if control
  bit is 0, else 2 steps.

- **Shrinking Generator**: Pattern where LFSR advances only when control bit is 1,
  and output is produced only when control bit is 1.

- **Self-Shrinking Generator**: Pattern where LFSR controls its own clocking
  based on its own state.

**Mathematical Foundation**:

Irregular clocking patterns can be described by a clock control function c that
determines the number of steps to advance:

.. math::

   \\text{steps} = c(\\text{control\_bits})

Common patterns:
- **Stop-and-Go**: c(b) = b (0 or 1 step)
- **Step-1/Step-2**: c(b) = 1 if b == 0 else 2
- **Shrinking**: c(b) = b, output only when b == 1
"""

from typing import List, Optional

from sage.all import *

from lfsr.attacks import LFSRConfig
from lfsr.advanced.base import (
    AdvancedLFSR,
    AdvancedLFSRConfig
)
from lfsr.advanced.clock_controlled import (
    ClockControlledLFSR,
    create_stop_and_go_lfsr,
    create_step1_step2_lfsr
)


class IrregularClockingLFSR(ClockControlledLFSR):
    """
    LFSR with irregular clocking pattern.
    
    This class provides a convenient interface for LFSRs with common irregular
    clocking patterns.
    
    **Key Terminology**:
    
    - **Irregular Clocking Pattern**: Specific pattern determining clocking behavior
    - **Pattern Type**: Type of pattern (stop-and-go, step-1/step-2, etc.)
    
    **Example Usage**:
    
        >>> from lfsr.advanced.irregular_clocking import IrregularClockingLFSR
        >>> from lfsr.attacks import LFSRConfig
        >>> 
        >>> base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        >>> 
        >>> # Create stop-and-go LFSR
        >>> irregular = IrregularClockingLFSR.create_stop_and_go(base_lfsr)
        >>> sequence = irregular.generate_sequence([1, 0, 1, 1], 100)
    """
    
    def __init__(
        self,
        base_lfsr_config: LFSRConfig,
        pattern_type: str,
        control_bit_position: int = 0
    ):
        """
        Initialize Irregular Clocking LFSR.
        
        Args:
            base_lfsr_config: Base LFSR configuration
            pattern_type: Type of pattern ("stop_and_go", "step1_step2", etc.)
            control_bit_position: Position of control bit (default: 0)
        """
        self.pattern_type = pattern_type
        
        # Create clock control function based on pattern type
        if pattern_type == "stop_and_go":
            clock_control = lambda state: 1 if state[control_bit_position] == 1 else 0
        elif pattern_type == "step1_step2":
            clock_control = lambda state: 1 if state[control_bit_position] == 0 else 2
        else:
            raise ValueError(f"Unknown pattern type: {pattern_type}")
        
        super().__init__(base_lfsr_config, clock_control)
    
    @classmethod
    def create_stop_and_go(
        cls,
        base_lfsr_config: LFSRConfig,
        control_bit_position: int = 0
    ) -> 'IrregularClockingLFSR':
        """
        Create stop-and-go irregular clocking LFSR.
        
        Args:
            base_lfsr_config: Base LFSR configuration
            control_bit_position: Position of control bit
        
        Returns:
            IrregularClockingLFSR instance with stop-and-go pattern
        """
        return cls(base_lfsr_config, "stop_and_go", control_bit_position)
    
    @classmethod
    def create_step1_step2(
        cls,
        base_lfsr_config: LFSRConfig,
        control_bit_position: int = 0
    ) -> 'IrregularClockingLFSR':
        """
        Create step-1/step-2 irregular clocking LFSR.
        
        Args:
            base_lfsr_config: Base LFSR configuration
            control_bit_position: Position of control bit
        
        Returns:
            IrregularClockingLFSR instance with step-1/step-2 pattern
        """
        return cls(base_lfsr_config, "step1_step2", control_bit_position)
    
    def get_config(self) -> AdvancedLFSRConfig:
        """Get Irregular Clocking LFSR configuration."""
        config = super().get_config()
        config.parameters['pattern_type'] = self.pattern_type
        return config
    
    def analyze_structure(self) -> dict:
        """
        Analyze Irregular Clocking LFSR structure.
        
        Returns:
            Dictionary of structure properties
        """
        base_analysis = super().analyze_structure()
        base_analysis['pattern_type'] = self.pattern_type
        base_analysis['pattern_description'] = self._get_pattern_description()
        return base_analysis
    
    def _get_pattern_description(self) -> str:
        """Get description of clocking pattern."""
        if self.pattern_type == "stop_and_go":
            return "Stop-and-go: LFSR advances 1 step if control bit is 1, else 0 steps"
        elif self.pattern_type == "step1_step2":
            return "Step-1/step-2: LFSR advances 1 step if control bit is 0, else 2 steps"
        else:
            return f"Unknown pattern: {self.pattern_type}"
