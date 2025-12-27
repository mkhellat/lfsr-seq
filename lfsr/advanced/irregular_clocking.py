#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Irregular Clocking Patterns Analysis

This module provides analysis capabilities for common irregular clocking patterns
used in LFSR-based stream ciphers, including stop-and-go, step-1/step-2, and
other patterns.

**Historical Context**:

Irregular clocking patterns were developed to introduce complexity into LFSR
sequences without using non-linear feedback. Different patterns provide different
trade-offs between security and efficiency. These patterns are used in many
stream ciphers, including A5/1 (majority function), LILI-128 (clock control),
and others.

**Key Terminology**:

- **Irregular Clocking**: Clocking pattern that is not regular (not every step).
  The LFSR may advance 0, 1, or more times per output step.

- **Stop-and-Go**: A clocking pattern where the LFSR advances only when a control
  bit is 1, and stops (doesn't advance) when it is 0. This is one of the simplest
  irregular clocking patterns.

- **Step-1/Step-2**: A clocking pattern where the LFSR advances 1 step when a
  control bit is 0, and 2 steps when it is 1 (or vice versa).

- **Majority Function Clocking**: A clocking pattern where multiple control bits
  vote, and the LFSR advances if its control bit matches the majority. Used in A5/1.

- **Clock Control Pattern**: The specific pattern of clocking behavior. Different
  patterns provide different security and efficiency properties.

**Mathematical Foundation**:

An irregular clocking pattern is defined by a function:
c: (state, control_bits) → number_of_steps

Common patterns:
- Stop-and-go: c = control_bit (0 or 1)
- Step-1/Step-2: c = 1 + control_bit (1 or 2)
- Majority: c = 1 if control_bit == majority, else 0
"""

from typing import List, Optional

from sage.all import *

from lfsr.attacks import LFSRConfig
from lfsr.advanced.base import (
    AdvancedLFSR,
    AdvancedLFSRConfig
)
from lfsr.advanced.clock_controlled import ClockControlledLFSR


class StopAndGoLFSR(ClockControlledLFSR):
    """
    Stop-and-Go LFSR implementation.
    
    A stop-and-go LFSR advances only when a control bit is 1, and stops
    (doesn't advance) when it is 0.
    
    **Key Terminology**:
    
    - **Stop-and-Go**: Simplest irregular clocking pattern
    
    - **Control Bit**: Bit determining whether LFSR advances
    
    - **Stop**: LFSR doesn't advance (output same state bit)
    
    - **Go**: LFSR advances (output new state bit)
    
    **Example Usage**:
    
        >>> from lfsr.advanced.irregular_clocking import StopAndGoLFSR
        >>> from lfsr.attacks import LFSRConfig
        >>> 
        >>> base_config = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        >>> 
        >>> # Control bit is state[0]
        >>> def control_bit_func(state):
        ...     return state[0]
        >>> 
        >>> sglfsr = StopAndGoLFSR(base_config, control_bit_func)
        >>> sequence = sglfsr.generate_sequence([1, 0, 1, 1], 100)
    """
    
    def __init__(
        self,
        base_lfsr_config: LFSRConfig,
        control_bit_function: Callable[[List[int]], int]
    ):
        """
        Initialize stop-and-go LFSR.
        
        Args:
            base_lfsr_config: Base LFSR configuration
            control_bit_function: Function returning control bit from state
        """
        # Clock control: advance if control bit is 1
        def clock_control(state):
            return control_bit_function(state)
        
        super().__init__(base_lfsr_config, clock_control)
        self.control_bit_function = control_bit_function
    
    def get_config(self) -> AdvancedLFSRConfig:
        """Get stop-and-go LFSR configuration."""
        config = super().get_config()
        config.structure_type = "stop_and_go"
        config.parameters['clocking_pattern'] = 'stop-and-go'
        return config


class Step1Step2LFSR(ClockControlledLFSR):
    """
    Step-1/Step-2 LFSR implementation.
    
    A step-1/step-2 LFSR advances 1 step when a control bit is 0, and 2 steps
    when it is 1 (or vice versa).
    
    **Key Terminology**:
    
    - **Step-1/Step-2**: Clocking pattern with variable step size
    
    - **Control Bit**: Bit determining step size
    
    - **Variable Step Size**: LFSR advances different amounts
    
    **Example Usage**:
    
        >>> from lfsr.advanced.irregular_clocking import Step1Step2LFSR
        >>> from lfsr.attacks import LFSRConfig
        >>> 
        >>> base_config = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        >>> 
        >>> # Control bit is state[0]
        >>> def control_bit_func(state):
        ...     return state[0]
        >>> 
        >>> s12lfsr = Step1Step2LFSR(base_config, control_bit_func)
        >>> sequence = s12lfsr.generate_sequence([1, 0, 1, 1], 100)
    """
    
    def __init__(
        self,
        base_lfsr_config: LFSRConfig,
        control_bit_function: Callable[[List[int]], int],
        step_when_0: int = 1,
        step_when_1: int = 2
    ):
        """
        Initialize step-1/step-2 LFSR.
        
        Args:
            base_lfsr_config: Base LFSR configuration
            control_bit_function: Function returning control bit from state
            step_when_0: Steps to advance when control bit is 0 (default: 1)
            step_when_1: Steps to advance when control bit is 1 (default: 2)
        """
        # Clock control: step_when_0 if control bit is 0, step_when_1 if 1
        def clock_control(state):
            control = control_bit_function(state)
            return step_when_1 if control == 1 else step_when_0
        
        super().__init__(base_lfsr_config, clock_control)
        self.control_bit_function = control_bit_function
        self.step_when_0 = step_when_0
        self.step_when_1 = step_when_1
    
    def get_config(self) -> AdvancedLFSRConfig:
        """Get step-1/step-2 LFSR configuration."""
        config = super().get_config()
        config.structure_type = "step1_step2"
        config.parameters['clocking_pattern'] = 'step-1/step-2'
        config.parameters['step_when_0'] = self.step_when_0
        config.parameters['step_when_1'] = self.step_when_1
        return config
