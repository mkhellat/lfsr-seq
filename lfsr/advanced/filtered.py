#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filtered LFSR Analysis

This module provides analysis capabilities for filtered LFSRs.

**IMPORTANT TERMINOLOGY CLARIFICATION**:

- **LFSR (Linear Feedback Shift Register)**: Feedback is ALWAYS linear (XOR only).
  This is the definition of LFSR.

- **Filtered LFSR**: An LFSR (with LINEAR feedback) where a non-linear filtering
  function is applied to the state to produce output. The LFSR itself remains
  linear - only the output is filtered through a non-linear function.

This module implements filtered LFSRs, which ARE LFSRs (linear feedback) with
non-linear output filtering.

**Historical Context**:

Filtered LFSRs are widely used in stream cipher design. The non-linear filter
function provides security by breaking the linearity of the LFSR. Examples
include the filtering generator used in many stream ciphers.

**Key Terminology**:

- **Filtered LFSR**: An LFSR with a non-linear filtering function applied to
  the state. The filter function maps the LFSR state to output bits, providing
  non-linearity in the output.

- **Filter Function**: Non-linear function mapping LFSR state to output bits.
  The filter function takes state bits as input and produces output bits.

- **Algebraic Immunity**: Resistance to algebraic attacks. Higher algebraic
  immunity means the filter function is more resistant to algebraic attacks.

- **Correlation Immunity**: Resistance to correlation attacks. A filter function
  is correlation immune of order m if output is uncorrelated with any m state
  bits.

**Mathematical Foundation**:

For a filtered LFSR, the output is:

y_i = f(S_i)

where S_i is the LFSR state at step i and f is the filter function.

The filter function f: F_q^d -> F_q maps the d-bit state to a single
output bit, where F_q denotes the finite field of order q.
"""

from typing import List, Optional, Callable

from lfsr.sage_imports import *

from lfsr.attacks import LFSRConfig
from lfsr.advanced.base import (
    AdvancedLFSR,
    AdvancedLFSRConfig,
    AdvancedLFSRAnalysisResult
)
from lfsr.core import build_state_update_matrix


class FilteredLFSR(AdvancedLFSR):
    """
    Filtered LFSR implementation.
    
    **IMPORTANT**: A Filtered LFSR IS an LFSR (Linear Feedback Shift Register).
    The feedback remains LINEAR (XOR only). The non-linearity comes from a
    filter function applied to the output, not from the feedback itself.
    
    A filtered LFSR applies a non-linear filtering function to the LFSR state
    to produce output bits. The LFSR feedback is still linear, but the output
    is filtered through a non-linear function, providing security against
    linear attacks.
    
    **Key Distinction**:
    - **LFSR Feedback**: LINEAR (XOR only) - this is what makes it an LFSR
    - **Filter Function**: NON-LINEAR (applied to state to produce output)
    
    **Structure**:
    
    - **Base LFSR**: Underlying LFSR with LINEAR feedback
    - **Filter Function**: Non-linear function mapping state to output
    - **State Size**: Same as base LFSR
    - **Output**: Result of filter function applied to state (non-linear)
    
    **Example Usage**:
    
        >>> from lfsr.advanced.filtered import FilteredLFSR
        >>> from lfsr.attacks import LFSRConfig
        >>> from lfsr.core import build_state_update_matrix
        >>> 
        >>> base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        >>> 
        >>> # Define filter function (non-linear)
        >>> def filter_func(state):
        ...     # Example: XOR of state bits with AND term
        ...     return state[0] ^ state[1] ^ (state[2] & state[3])
        >>> 
        >>> filtered = FilteredLFSR(base_lfsr, filter_func)
        >>> sequence = filtered.generate_sequence([1, 0, 0, 0], 100)
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
            filter_function: Filter function taking state and returning output bit
        """
        self.base_lfsr_config = base_lfsr_config
        self.filter_function = filter_function
        self.state_size = base_lfsr_config.degree
        self.field_order = base_lfsr_config.field_order
        
        # Build state update matrix
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
                'state_size': self.state_size,
                'field_order': self.field_order,
                'has_filter_function': True
            }
        )
    
    def _clock_lfsr(self, state: List[int]) -> List[int]:
        """
        Clock base LFSR one step.
        
        Args:
            state: Current state
        
        Returns:
            New state after one clock
        """
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
        
        Args:
            initial_state: Initial state as list of field elements
            length: Desired sequence length
        
        Returns:
            List of sequence elements (filter function outputs)
        """
        if len(initial_state) != self.state_size:
            raise ValueError(
                f"Filtered LFSR requires state of size {self.state_size}, "
                f"got {len(initial_state)}"
            )
        
        state = initial_state[:]
        sequence = []
        
        for _ in range(length):
            # Apply filter function to state
            output = self.filter_function(state)
            sequence.append(output)
            
            # Clock base LFSR
            state = self._clock_lfsr(state)
        
        return sequence
    
    def analyze_structure(self) -> dict:
        """
        Analyze Filtered LFSR structure.
        
        Returns:
            Dictionary of structure properties
        """
        return {
            'structure_type': 'FilteredLFSR',
            'base_lfsr_degree': self.base_lfsr_config.degree,
            'base_lfsr_field_order': self.field_order,
            'state_size': self.state_size,
            'has_filter_function': True,
            'note': 'Filtered LFSR uses non-linear filter function on LFSR state'
        }
    
    def _assess_security(
        self,
        structure_properties: dict
    ) -> dict:
        """Assess Filtered LFSR security."""
        return {
            'nonlinearity': 'Non-linear filter provides resistance to linear attacks',
            'known_vulnerabilities': [
                'Algebraic attacks (if algebraic immunity is low)',
                'Correlation attacks (if correlation immunity is low)',
                'Fast correlation attacks'
            ],
            'recommendations': [
                'Use filter function with high algebraic immunity',
                'Ensure correlation immunity is sufficient',
                'Consider combining multiple LFSRs'
            ]
        }


def create_simple_filtered_lfsr(
    base_lfsr_config: LFSRConfig,
    filter_taps: Optional[List[int]] = None,
    nonlinear_terms: Optional[List[tuple]] = None
) -> FilteredLFSR:
    """
    Create a simple filtered LFSR with specified filter function.
    
    This helper function creates a filtered LFSR with a filter function that
    includes both linear terms (XOR of tap bits) and non-linear terms (AND
    operations).
    
    Args:
        base_lfsr_config: Base LFSR configuration
        filter_taps: List of state bit indices to XOR (linear part)
        nonlinear_terms: List of (i, j) tuples for AND terms S_i & S_j
    
    Returns:
        FilteredLFSR instance
    
    Example:
        >>> from lfsr.attacks import LFSRConfig
        >>> from lfsr.advanced.filtered import create_simple_filtered_lfsr
        >>> 
        >>> base = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        >>> # Filter: XOR of bits 0, 1, 2 with AND term S[2] & S[3]
        >>> filtered = create_simple_filtered_lfsr(
        ...     base,
        ...     filter_taps=[0, 1, 2],
        ...     nonlinear_terms=[(2, 3)]
        ... )
    """
    degree = base_lfsr_config.degree
    
    if filter_taps is None:
        filter_taps = [0]  # Default: output MSB
    
    def filter_func(state: List[int]) -> int:
        # Linear part: XOR of tap bits
        linear = 0
        for tap in filter_taps:
            if 0 <= tap < degree:
                linear ^= state[tap]
        
        # Non-linear part: AND of specified pairs
        nonlinear = 0
        if nonlinear_terms:
            for i, j in nonlinear_terms:
                if 0 <= i < degree and 0 <= j < degree:
                    nonlinear ^= (state[i] & state[j])
        
        return linear ^ nonlinear
    
    return FilteredLFSR(base_lfsr_config, filter_func)
