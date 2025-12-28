#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Multi-Output LFSR Analysis

This module provides analysis capabilities for multi-output LFSRs.

**IMPORTANT TERMINOLOGY CLARIFICATION**:

- **LFSR (Linear Feedback Shift Register)**: Feedback is ALWAYS linear (XOR only).
  This is the definition of LFSR.

- **Multi-Output LFSR**: An LFSR (with LINEAR feedback) that produces multiple
  output bits per step. The feedback remains linear - only the output rate
  is increased.

This module implements multi-output LFSRs, which ARE LFSRs (linear feedback)
with multiple output bits per step.

**Historical Context**:

Multi-output LFSRs are used to increase the output rate and efficiency of
stream generators. By outputting multiple bits per step, they can generate
keystream faster than single-output LFSRs.

**Key Terminology**:

- **Multi-Output LFSR**: An LFSR that produces multiple output bits per step,
  rather than a single bit. This increases the output rate.

- **Output Function**: Function mapping LFSR state to output bits. For
  multi-output LFSRs, this function produces multiple bits.

- **Output Rate**: Number of bits output per clock step. A multi-output LFSR
  with rate k outputs k bits per step.

- **Parallel Output**: Multiple bits output simultaneously from the same state.

**Mathematical Foundation**:

For a multi-output LFSR, the output is:

.. math::

   (y_0, y_1, \\ldots, y_{k-1}) = f(S_i)

where :math:`S_i` is the LFSR state at step i and :math:`f` is the output
function producing k bits.
"""

from typing import List, Optional, Callable

from sage.all import *

from lfsr.attacks import LFSRConfig
from lfsr.advanced.base import (
    AdvancedLFSR,
    AdvancedLFSRConfig
)
from lfsr.core import build_state_update_matrix


class MultiOutputLFSR(AdvancedLFSR):
    """
    Multi-output LFSR implementation.
    
    **IMPORTANT**: A Multi-Output LFSR IS an LFSR (Linear Feedback Shift Register).
    The feedback remains LINEAR (XOR only). Multiple bits are output per step,
    but the feedback is still linear.
    
    A multi-output LFSR produces multiple output bits per step, increasing
    the output rate compared to single-output LFSRs. The feedback is still linear.
    
    **Key Distinction**:
    - **LFSR Feedback**: LINEAR (XOR only) - this is what makes it an LFSR
    - **Output Rate**: Multiple bits per step (but feedback is linear)
    
    **Structure**:
    
    - **Base LFSR**: Underlying LFSR with LINEAR feedback
    - **Output Function**: Function mapping state to multiple output bits
    - **Output Rate**: Number of bits output per step
    
    **Example Usage**:
    
        >>> from lfsr.advanced.multi_output import MultiOutputLFSR
        >>> from lfsr.attacks import LFSRConfig
        >>> 
        >>> base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        >>> 
        >>> # Output function: output first 2 bits of state
        >>> def output_func(state):
        ...     return [state[0], state[1]]  # 2 bits per step
        >>> 
        >>> molfsr = MultiOutputLFSR(base_lfsr, output_func, output_rate=2)
        >>> sequence = molfsr.generate_sequence([1, 0, 0, 0], 100)
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
            output_function: Function taking state and returning list of output bits
            output_rate: Number of bits output per step
        """
        self.base_lfsr_config = base_lfsr_config
        self.output_function = output_function
        self.output_rate = output_rate
        self.state_size = base_lfsr_config.degree
        self.field_order = base_lfsr_config.field_order
        
        # Build state update matrix
        self.C, _ = build_state_update_matrix(
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
                'state_size': self.state_size,
                'field_order': self.field_order
            }
        )
    
    def _clock_lfsr(self, state: List[int]) -> List[int]:
        """Clock base LFSR one step."""
        F = GF(self.field_order)
        state_vec = vector(F, state)
        new_state_vec = self.C * state_vec
        return [int(x) for x in new_state_vec]
    
    def generate_sequence(
        self,
        initial_state: List[int],
        length: int
    ) -> List[int]:
        """
        Generate sequence from initial state.
        
        Note: length is in output bits, not steps. The number of steps is
        length / output_rate.
        
        Args:
            initial_state: Initial state as list of field elements
            length: Desired sequence length in bits
        
        Returns:
            List of sequence elements (flattened output bits)
        """
        if len(initial_state) != self.state_size:
            raise ValueError(
                f"Multi-Output LFSR requires state of size {self.state_size}, "
                f"got {len(initial_state)}"
            )
        
        state = initial_state[:]
        sequence = []
        steps_needed = (length + self.output_rate - 1) // self.output_rate
        
        for _ in range(steps_needed):
            # Get output bits from output function
            output_bits = self.output_function(state)
            
            # Add to sequence
            sequence.extend(output_bits)
            
            # Clock base LFSR
            state = self._clock_lfsr(state)
        
        # Return only requested length
        return sequence[:length]
    
    def analyze_structure(self) -> dict:
        """Analyze Multi-Output LFSR structure."""
        return {
            'structure_type': 'MultiOutputLFSR',
            'base_lfsr_degree': self.base_lfsr_config.degree,
            'base_lfsr_field_order': self.field_order,
            'output_rate': self.output_rate,
            'state_size': self.state_size,
            'note': f'Multi-output LFSR outputs {self.output_rate} bits per step'
        }
    
    def _assess_security(
        self,
        structure_properties: dict
    ) -> dict:
        """Assess Multi-Output LFSR security."""
        return {
            'efficiency': 'Multi-output increases output rate and efficiency',
            'known_vulnerabilities': [
                'Linear attacks (if output function is linear)',
                'Correlation attacks'
            ],
            'recommendations': [
                'Use non-linear output function',
                'Ensure output function has good properties'
            ]
        }


def create_simple_multi_output_lfsr(
    base_lfsr_config: LFSRConfig,
    output_bits: List[int]
) -> MultiOutputLFSR:
    """
    Create a simple multi-output LFSR outputting specified state bits.
    
    Args:
        base_lfsr_config: Base LFSR configuration
        output_bits: List of state bit indices to output
    
    Returns:
        MultiOutputLFSR instance
    
    Example:
        >>> from lfsr.attacks import LFSRConfig
        >>> from lfsr.advanced.multi_output import create_simple_multi_output_lfsr
        >>> 
        >>> base = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        >>> # Output bits 0, 1, 2 (3 bits per step)
        >>> molfsr = create_simple_multi_output_lfsr(base, [0, 1, 2])
    """
    output_rate = len(output_bits)
    degree = base_lfsr_config.degree
    
    def output_func(state: List[int]) -> List[int]:
        return [state[i] for i in output_bits if 0 <= i < degree]
    
    return MultiOutputLFSR(base_lfsr_config, output_func, output_rate)
