#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Clock-Controlled LFSR Analysis

This module provides analysis capabilities for clock-controlled LFSRs, which
have irregular clocking patterns controlled by clock control functions or other
LFSRs.

**Historical Context**:

Clock-controlled LFSRs were developed to introduce irregularity into LFSR sequences,
making them harder to analyze. By controlling when LFSRs advance, clock control
increases the complexity of the generated sequences.

**Key Terminology**:

- **Clock-Controlled LFSR**: An LFSR with irregular clocking, where the LFSR
  doesn't always advance on each step. Clocking is controlled by a clock control
  function or another LFSR.

- **Clock Control Function**: A function that determines when the LFSR advances.
  The function may depend on the LFSR's own state or on an external control signal.

- **Irregular Clocking**: Clocking pattern that is not regular (not every step).
  The LFSR may advance 0, 1, or more steps depending on the clock control.

- **Clock Control LFSR**: A separate LFSR that controls the clocking of another
  LFSR. The output of the control LFSR determines when the data LFSR advances.

- **Stop-and-Go**: A clock control pattern where the LFSR stops when control bit
  is 0 and advances when control bit is 1.

- **Step-1/Step-2**: A clock control pattern where the LFSR advances 1 or 2 steps
  based on the control bit.

**Mathematical Foundation**:

A clock-controlled LFSR has:
- Base LFSR with state S
- Clock control function c: determines number of steps to advance

The state update is:

.. math::

   S_{i+1} = C^{c(S_i)} \\cdot S_i

where C is the state update matrix and c(S_i) is the number of steps to advance.

Common clock control patterns:
- **Stop-and-Go**: c(S) = 1 if control bit is 1, else 0
- **Step-1/Step-2**: c(S) = 1 if control bit is 0, else 2
"""

from typing import Callable, List, Optional

from sage.all import *

from lfsr.attacks import LFSRConfig
from lfsr.advanced.base import (
    AdvancedLFSR,
    AdvancedLFSRConfig
)
from lfsr.core import build_state_update_matrix


class ClockControlledLFSR(AdvancedLFSR):
    """
    Clock-Controlled LFSR implementation.
    
    A clock-controlled LFSR has irregular clocking controlled by a clock
    control function. The LFSR may advance 0, 1, or more steps depending
    on the control function.
    
    **Cipher Structure**:
    
    - **Base LFSR**: Underlying LFSR that is clock-controlled
    - **Clock Control Function**: Function determining number of steps to advance
    - **State Size**: Same as base LFSR degree
    - **Clocking Pattern**: Irregular (not every step)
    
    **Key Terminology**:
    
    - **Clock-Controlled LFSR**: LFSR with irregular clocking
    - **Clock Control Function**: Function determining clocking behavior
    - **Irregular Clocking**: Clocking pattern is not regular
    
    **Example Usage**:
    
        >>> from lfsr.advanced.clock_controlled import ClockControlledLFSR
        >>> from lfsr.attacks import LFSRConfig
        >>> 
        >>> base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        >>> 
        >>> # Define clock control: advance 1 step if state[0] == 1, else 0 steps
        >>> def clock_control(state):
        ...     return 1 if state[0] == 1 else 0
        >>> 
        >>> cclfsr = ClockControlledLFSR(base_lfsr, clock_control)
        >>> sequence = cclfsr.generate_sequence([1, 0, 1, 1], 100)
    """
    
    def __init__(
        self,
        base_lfsr_config: LFSRConfig,
        clock_control_function: Callable[[List[int]], int]
    ):
        """
        Initialize Clock-Controlled LFSR.
        
        Args:
            base_lfsr_config: Base LFSR configuration
            clock_control_function: Function returning number of steps to advance (0, 1, 2, ...)
        """
        self.base_lfsr_config = base_lfsr_config
        self.clock_control_function = clock_control_function
        self.state = None
        
        # Build state update matrix
        F = GF(base_lfsr_config.field_order)
        self.C, self.CS = build_state_update_matrix(
            base_lfsr_config.coefficients,
            base_lfsr_config.field_order
        )
    
    def get_config(self) -> AdvancedLFSRConfig:
        """Get Clock-Controlled LFSR configuration."""
        return AdvancedLFSRConfig(
            structure_type="clock_controlled",
            base_lfsr_config=self.base_lfsr_config,
            parameters={
                'clock_control_type': 'function',
                'degree': self.base_lfsr_config.degree,
                'field_order': self.base_lfsr_config.field_order
            }
        )
    
    def _advance_steps(self, num_steps: int):
        """
        Advance LFSR by specified number of steps.
        
        Args:
            num_steps: Number of steps to advance (0, 1, 2, ...)
        """
        if self.state is None:
            raise ValueError("LFSR state not initialized")
        
        if num_steps == 0:
            return
        
        F = GF(self.base_lfsr_config.field_order)
        state_vec = vector(F, self.state)
        
        # Advance num_steps times
        for _ in range(num_steps):
            state_vec = self.C * state_vec
        
        self.state = [int(x) for x in state_vec]
    
    def _get_output(self) -> int:
        """
        Get output bit from LFSR.
        
        Returns:
            Output bit (MSB of state)
        """
        if self.state is None:
            raise ValueError("LFSR state not initialized")
        
        return self.state[0]
    
    def generate_sequence(
        self,
        initial_state: List[int],
        length: int
    ) -> List[int]:
        """
        Generate sequence from initial state.
        
        Args:
            initial_state: Initial state as a list of field elements
            length: Desired sequence length
        
        Returns:
            List of sequence elements
        """
        if len(initial_state) != self.base_lfsr_config.degree:
            raise ValueError(
                f"Initial state must have length {self.base_lfsr_config.degree}, "
                f"got {len(initial_state)}"
            )
        
        # Initialize state
        self.state = initial_state.copy()
        
        # Generate sequence
        sequence = []
        for _ in range(length):
            # Get output
            output = self._get_output()
            sequence.append(output)
            
            # Determine number of steps to advance
            num_steps = self.clock_control_function(self.state)
            
            # Advance LFSR
            self._advance_steps(num_steps)
        
        return sequence
    
    def analyze_structure(self) -> dict:
        """
        Analyze Clock-Controlled LFSR structure.
        
        Returns:
            Dictionary of structure properties
        """
        base_properties = {
            'degree': self.base_lfsr_config.degree,
            'field_order': self.base_lfsr_config.field_order,
            'coefficients': self.base_lfsr_config.coefficients,
            'state_space_size': self.base_lfsr_config.field_order ** self.base_lfsr_config.degree
        }
        
        return {
            'base_lfsr': base_properties,
            'clock_control_type': 'function',
            'degree': self.base_lfsr_config.degree,
            'field_order': self.base_lfsr_config.field_order,
            'state_space_size': self.base_lfsr_config.field_order ** self.base_lfsr_config.degree,
            'note': 'Clocking is irregular (controlled by clock control function)'
        }


def create_stop_and_go_lfsr(
    base_lfsr_config: LFSRConfig,
    control_bit_position: int = 0
) -> ClockControlledLFSR:
    """
    Create stop-and-go clock-controlled LFSR.
    
    In stop-and-go, the LFSR advances 1 step if control bit is 1, else 0 steps.
    
    **Key Terminology**:
    
    - **Stop-and-Go**: Clock control pattern where LFSR stops (0 steps) when
      control bit is 0 and advances (1 step) when control bit is 1.
    
    Args:
        base_lfsr_config: Base LFSR configuration
        control_bit_position: Position of control bit in state (default: 0)
    
    Returns:
        ClockControlledLFSR instance with stop-and-go pattern
    
    Example:
        >>> base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        >>> cclfsr = create_stop_and_go_lfsr(base_lfsr, control_bit_position=0)
        >>> sequence = cclfsr.generate_sequence([1, 0, 1, 1], 100)
    """
    def stop_and_go_control(state: List[int]) -> int:
        """Stop-and-go clock control: 1 step if control bit is 1, else 0."""
        return 1 if state[control_bit_position] == 1 else 0
    
    return ClockControlledLFSR(base_lfsr_config, stop_and_go_control)


def create_step1_step2_lfsr(
    base_lfsr_config: LFSRConfig,
    control_bit_position: int = 0
) -> ClockControlledLFSR:
    """
    Create step-1/step-2 clock-controlled LFSR.
    
    In step-1/step-2, the LFSR advances 1 step if control bit is 0, else 2 steps.
    
    Args:
        base_lfsr_config: Base LFSR configuration
        control_bit_position: Position of control bit in state (default: 0)
    
    Returns:
        ClockControlledLFSR instance with step-1/step-2 pattern
    
    Example:
        >>> base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        >>> cclfsr = create_step1_step2_lfsr(base_lfsr, control_bit_position=0)
        >>> sequence = cclfsr.generate_sequence([1, 0, 1, 1], 100)
    """
    def step1_step2_control(state: List[int]) -> int:
        """Step-1/step-2 clock control: 1 step if control bit is 0, else 2."""
        return 1 if state[control_bit_position] == 0 else 2
    
    return ClockControlledLFSR(base_lfsr_config, step1_step2_control)
