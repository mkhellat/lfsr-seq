#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filtered LFSR Analysis

This module provides analysis capabilities for filtered LFSRs, which apply
non-linear filtering functions to LFSR state to produce output.

**Historical Context**:

Filtered LFSRs were developed to combine the good statistical properties of
LFSRs with the security benefits of non-linearity. By applying a non-linear
filter function to the LFSR state, filtered LFSRs provide resistance to
linear cryptanalysis while maintaining efficiency.

**Key Terminology**:

- **Filtered LFSR**: An LFSR with a non-linear filtering function applied
  to the state. The filter function maps the LFSR state to output bits,
  providing non-linearity in the output.

- **Filter Function**: A non-linear function that maps LFSR state to output
  bits. The filter function determines which state bits are used and how
  they are combined.

- **Algebraic Immunity**: The minimum degree of a non-zero annihilator of
  the filter function. Higher algebraic immunity provides better resistance
  to algebraic attacks.

- **Correlation Immunity**: The property that the output is uncorrelated
  with any subset of input bits. Higher correlation immunity provides
  better resistance to correlation attacks.

- **Non-Linear Filtering**: Applying a non-linear function to state bits
  to produce output, rather than using state bits directly.

**Mathematical Foundation**:

A filtered LFSR has:
- Base LFSR with state S = (s_0, s_1, ..., s_{d-1})
- Filter function f: GF(q)^d → GF(q)

The output at step i is:

.. math::

   y_i = f(S_i)

where S_i is the LFSR state at step i.

The filter function f is typically non-linear and may use operations like:
- AND: a ∧ b
- OR: a ∨ b
- XOR: a ⊕ b
- Combinations of the above
"""

from typing import Callable, List, Optional

from sage.all import *

from lfsr.attacks import LFSRConfig
from lfsr.advanced.base import (
    AdvancedLFSR,
    AdvancedLFSRConfig
)
from lfsr.core import build_state_update_matrix


class FilteredLFSR(AdvancedLFSR):
    """
    Filtered LFSR implementation.
    
    A filtered LFSR applies a non-linear filtering function to the LFSR
    state to produce output. This provides non-linearity while maintaining
    the efficiency of LFSRs.
    
    **Cipher Structure**:
    
    - **Base LFSR**: Underlying linear LFSR
    - **Filter Function**: Non-linear function mapping state to output
    - **State Size**: Same as base LFSR degree
    - **Output**: Result of filter function applied to state
    
    **Key Terminology**:
    
    - **Filtered LFSR**: LFSR with non-linear filtering function
    - **Filter Function**: Non-linear function mapping state to output
    - **Algebraic Immunity**: Resistance to algebraic attacks
    - **Correlation Immunity**: Resistance to correlation attacks
    
    **Example Usage**:
    
        >>> from lfsr.advanced.filtered import FilteredLFSR
        >>> from lfsr.attacks import LFSRConfig
        >>> 
        >>> base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        >>> 
        >>> # Define filter function: f(s0, s1, s2, s3) = s0 AND s1 XOR s2
        >>> def filter_func(state):
        ...     return (state[0] & state[1]) ^ state[2]
        >>> 
        >>> filtered = FilteredLFSR(base_lfsr, filter_func)
        >>> sequence = filtered.generate_sequence([1, 0, 1, 1], 100)
    """
    
    def __init__(
        self,
        base_lfsr_config: LFSRConfig,
        filter_function: Callable[[List[int]], int]
    ):
        """
        Initialize Filtered LFSR.
        
        Args:
            base_lfsr_config: Base LFSR configuration
            filter_function: Non-linear filter function mapping state to output
        """
        self.base_lfsr_config = base_lfsr_config
        self.filter_function = filter_function
        self.state = None
        
        # Build state update matrix for base LFSR
        F = GF(base_lfsr_config.field_order)
        self.C, self.CS = build_state_update_matrix(
            base_lfsr_config.coefficients,
            base_lfsr_config.field_order
        )
    
    def get_config(self) -> AdvancedLFSRConfig:
        """Get Filtered LFSR configuration."""
        return AdvancedLFSRConfig(
            structure_type="filtered",
            base_lfsr_config=self.base_lfsr_config,
            parameters={
                'filter_type': 'non-linear',
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
    
    def _get_output(self) -> int:
        """
        Get output from filter function.
        
        Applies filter function to current state to produce output.
        
        Returns:
            Output bit
        """
        if self.state is None:
            raise ValueError("LFSR state not initialized")
        
        return self.filter_function(self.state)
    
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
            # Get output from filter function
            output = self._get_output()
            sequence.append(output)
            
            # Clock base LFSR
            self._clock_lfsr()
        
        return sequence
    
    def analyze_structure(self) -> dict:
        """
        Analyze Filtered LFSR structure.
        
        Returns:
            Dictionary of structure properties
        """
        # Analyze base LFSR
        base_properties = {
            'degree': self.base_lfsr_config.degree,
            'field_order': self.base_lfsr_config.field_order,
            'coefficients': self.base_lfsr_config.coefficients,
            'state_space_size': self.base_lfsr_config.field_order ** self.base_lfsr_config.degree
        }
        
        # Analyze filter function
        # Test filter function with sample states
        is_linear = self._test_filter_linearity()
        
        return {
            'base_lfsr': base_properties,
            'filter_type': 'non-linear',
            'is_linear': is_linear,
            'degree': self.base_lfsr_config.degree,
            'field_order': self.base_lfsr_config.field_order,
            'state_space_size': self.base_lfsr_config.field_order ** self.base_lfsr_config.degree
        }
    
    def _test_filter_linearity(self) -> bool:
        """
        Test if filter function is linear.
        
        Returns:
            True if function appears linear, False otherwise
        """
        # Simplified linearity test
        test_states = [
            [0] * self.base_lfsr_config.degree,
            [1] * self.base_lfsr_config.degree,
            [1, 0] * (self.base_lfsr_config.degree // 2) + [1] * (self.base_lfsr_config.degree % 2)
        ]
        
        try:
            for i, state_a in enumerate(test_states):
                for state_b in test_states[i+1:]:
                    state_sum = [(a + b) % self.base_lfsr_config.field_order 
                                for a, b in zip(state_a, state_b)]
                    f_sum = self.filter_function(state_sum)
                    
                    f_a = self.filter_function(state_a)
                    f_b = self.filter_function(state_b)
                    f_ab = (f_a + f_b) % self.base_lfsr_config.field_order
                    
                    if f_sum != f_ab:
                        return False
        except Exception:
            return False
        
        return True


def create_filtered_lfsr_with_and_filter(
    base_lfsr_config: LFSRConfig,
    tap_positions: List[int]
) -> FilteredLFSR:
    """
    Create Filtered LFSR with AND-based filter function.
    
    Args:
        base_lfsr_config: Base LFSR configuration
        tap_positions: Positions in state to AND together for filter
    
    Returns:
        FilteredLFSR instance with AND-based filter
    
    Example:
        >>> base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        >>> filtered = create_filtered_lfsr_with_and_filter(base_lfsr, [0, 1, 2])
        >>> sequence = filtered.generate_sequence([1, 0, 1, 1], 100)
    """
    def and_filter(state: List[int]) -> int:
        """AND-based filter function."""
        result = state[tap_positions[0]]
        for pos in tap_positions[1:]:
            result = result & state[pos]
        return result
    
    return FilteredLFSR(base_lfsr_config, and_filter)
