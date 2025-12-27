#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Multi-Output LFSR Analysis

This module provides analysis capabilities for multi-output LFSRs, which
produce multiple output bits per step rather than a single bit.

**Historical Context**:

Multi-output LFSRs were developed to increase the output rate of LFSR-based
generators. By producing multiple bits per step, multi-output LFSRs can
generate sequences more efficiently while maintaining good statistical properties.

**Key Terminology**:

- **Multi-Output LFSR**: An LFSR that produces multiple output bits per step,
  rather than a single bit. This increases the output rate and can improve
  efficiency.

- **Output Function**: A function that maps LFSR state to multiple output bits.
  The output function determines which state bits are used and how they are
  combined.

- **Output Rate**: The number of bits output per clock step. A standard LFSR
  has output rate 1, while a multi-output LFSR may have output rate 2, 3, or more.

- **Parallel Output**: Multiple bits output simultaneously from the same state.
  This is different from clocking multiple times to get multiple bits.

- **Output Positions**: The positions in the state vector used for output.
  Multi-output LFSRs typically use multiple state positions for output.

**Mathematical Foundation**:

A multi-output LFSR has:
- Base LFSR with state S = (s_0, s_1, ..., s_{d-1})
- Output function f: GF(q)^d → GF(q)^k (maps state to k output bits)

The output at step i is:

.. math::

   Y_i = f(S_i) = (y_{i,0}, y_{i,1}, \\ldots, y_{i,k-1})

where k is the output rate (number of bits per step).

Common output functions:
- **Direct Output**: Output k consecutive state bits
- **XOR Output**: Output XOR of selected state bits
- **Non-Linear Output**: Output result of non-linear function applied to state
"""

from typing import Callable, List, Optional

from sage.all import *

from lfsr.attacks import LFSRConfig
from lfsr.advanced.base import (
    AdvancedLFSR,
    AdvancedLFSRConfig
)
from lfsr.core import build_state_update_matrix


class MultiOutputLFSR(AdvancedLFSR):
    """
    Multi-Output LFSR implementation.
    
    A multi-output LFSR produces multiple output bits per step, increasing
    the output rate compared to standard LFSRs.
    
    **Cipher Structure**:
    
    - **Base LFSR**: Underlying LFSR
    - **Output Function**: Function mapping state to multiple output bits
    - **Output Rate**: Number of bits output per step (k)
    - **State Size**: Same as base LFSR degree
    
    **Key Terminology**:
    
    - **Multi-Output LFSR**: LFSR producing multiple bits per step
    - **Output Function**: Function mapping state to output bits
    - **Output Rate**: Number of bits output per step
    
    **Example Usage**:
    
        >>> from lfsr.advanced.multi_output import MultiOutputLFSR
        >>> from lfsr.attacks import LFSRConfig
        >>> 
        >>> base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        >>> 
        >>> # Define output function: output first 2 state bits
        >>> def output_func(state):
        ...     return [state[0], state[1]]
        >>> 
        >>> molfsr = MultiOutputLFSR(base_lfsr, output_func, output_rate=2)
        >>> sequence = molfsr.generate_sequence([1, 0, 1, 1], 100)
    """
    
    def __init__(
        self,
        base_lfsr_config: LFSRConfig,
        output_function: Callable[[List[int]], List[int]],
        output_rate: int
    ):
        """
        Initialize Multi-Output LFSR.
        
        Args:
            base_lfsr_config: Base LFSR configuration
            output_function: Function mapping state to list of output bits
            output_rate: Number of bits output per step
        """
        self.base_lfsr_config = base_lfsr_config
        self.output_function = output_function
        self.output_rate = output_rate
        self.state = None
        
        # Build state update matrix
        F = GF(base_lfsr_config.field_order)
        self.C, self.CS = build_state_update_matrix(
            base_lfsr_config.coefficients,
            base_lfsr_config.field_order
        )
    
    def get_config(self) -> AdvancedLFSRConfig:
        """Get Multi-Output LFSR configuration."""
        return AdvancedLFSRConfig(
            structure_type="multi_output",
            base_lfsr_config=self.base_lfsr_config,
            parameters={
                'output_rate': self.output_rate,
                'degree': self.base_lfsr_config.degree,
                'field_order': self.base_lfsr_config.field_order
            }
        )
    
    def _clock_lfsr(self):
        """Clock base LFSR one step."""
        if self.state is None:
            raise ValueError("LFSR state not initialized")
        
        F = GF(self.base_lfsr_config.field_order)
        state_vec = vector(F, self.state)
        new_state_vec = self.C * state_vec
        self.state = [int(x) for x in new_state_vec]
    
    def _get_output(self) -> List[int]:
        """
        Get output bits from output function.
        
        Returns:
            List of output bits (length = output_rate)
        """
        if self.state is None:
            raise ValueError("LFSR state not initialized")
        
        return self.output_function(self.state)
    
    def generate_sequence(
        self,
        initial_state: List[int],
        length: int
    ) -> List[int]:
        """
        Generate sequence from initial state.
        
        Note: length is the number of output bits, not the number of steps.
        The number of steps is length / output_rate.
        
        Args:
            initial_state: Initial state as a list of field elements
            length: Desired sequence length (in bits)
        
        Returns:
            List of sequence elements (flattened output bits)
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
        num_steps = (length + self.output_rate - 1) // self.output_rate  # Ceiling division
        
        for _ in range(num_steps):
            # Get output bits
            output_bits = self._get_output()
            sequence.extend(output_bits)
            
            # Clock LFSR
            self._clock_lfsr()
        
        # Trim to desired length
        return sequence[:length]
    
    def analyze_structure(self) -> dict:
        """
        Analyze Multi-Output LFSR structure.
        
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
            'output_rate': self.output_rate,
            'degree': self.base_lfsr_config.degree,
            'field_order': self.base_lfsr_config.field_order,
            'state_space_size': self.base_lfsr_config.field_order ** self.base_lfsr_config.degree,
            'note': f'Outputs {self.output_rate} bits per step'
        }


def create_direct_output_lfsr(
    base_lfsr_config: LFSRConfig,
    output_positions: List[int]
) -> MultiOutputLFSR:
    """
    Create multi-output LFSR with direct output from state positions.
    
    The output function directly outputs the state bits at specified positions.
    
    Args:
        base_lfsr_config: Base LFSR configuration
        output_positions: List of state positions to output
    
    Returns:
        MultiOutputLFSR instance with direct output
    
    Example:
        >>> base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        >>> molfsr = create_direct_output_lfsr(base_lfsr, [0, 1])
        >>> sequence = molfsr.generate_sequence([1, 0, 1, 1], 100)
    """
    def direct_output(state: List[int]) -> List[int]:
        """Direct output from specified positions."""
        return [state[pos] for pos in output_positions]
    
    return MultiOutputLFSR(base_lfsr_config, direct_output, len(output_positions))
