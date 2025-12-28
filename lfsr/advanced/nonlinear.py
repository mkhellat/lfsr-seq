#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Non-Linear Feedback LFSR (NFSR) Analysis

This module provides analysis capabilities for Non-Linear Feedback Shift
Registers (NFSRs), which generalize LFSRs by allowing non-linear feedback
functions.

**Historical Context**:

NFSRs were developed to address the linearity weakness of LFSRs. While LFSRs
are fast and have good statistical properties, their linearity makes them
vulnerable to algebraic attacks. NFSRs introduce non-linearity through AND,
OR, and other non-linear operations in the feedback function.

**Key Terminology**:

- **NFSR (Non-Linear Feedback Shift Register)**: Generalization of LFSR where
  feedback function is not linear. Uses non-linear operations (AND, OR, etc.)
  in addition to XOR.

- **Non-Linear Feedback**: Feedback function that includes non-linear operations.
  Unlike linear feedback (XOR only), non-linear feedback can use AND, OR,
  and other Boolean operations.

- **Feedback Function**: Function computing the new state bit from current state.
  In LFSRs, this is linear (XOR of tap bits). In NFSRs, this includes
  non-linear operations.

- **Non-Linear Complexity**: Measure of non-linearity in the feedback function.
  Higher non-linear complexity generally provides better security.

**Mathematical Foundation**:

For an LFSR, the feedback is linear:

.. math::

   f(S) = c_0 S_0 \\oplus c_1 S_1 \\oplus \\ldots \\oplus c_{d-1} S_{d-1}

For an NFSR, the feedback includes non-linear terms:

.. math::

   f(S) = \\text{linear terms} + \\text{non-linear terms}

where non-linear terms can include products (AND operations) like
:math:`S_i \\land S_j`.
"""

from typing import List, Optional, Callable

from sage.all import *

from lfsr.attacks import LFSRConfig
from lfsr.advanced.base import (
    AdvancedLFSR,
    AdvancedLFSRConfig,
    AdvancedLFSRAnalysisResult
)


class NFSR(AdvancedLFSR):
    """
    Non-Linear Feedback Shift Register (NFSR) implementation.
    
    An NFSR generalizes an LFSR by allowing non-linear feedback functions.
    The feedback can include AND, OR, and other non-linear operations in
    addition to XOR.
    
    **Cipher Structure**:
    
    - **Base LFSR**: Underlying linear structure
    - **Non-Linear Feedback**: Feedback function with non-linear terms
    - **State Size**: Same as base LFSR
    - **Output**: Typically from state (can be filtered)
    
    **Example Usage**:
    
        >>> from lfsr.advanced.nonlinear import NFSR
        >>> from lfsr.attacks import LFSRConfig
        >>> 
        >>> base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        >>> 
        >>> # Define non-linear feedback function
        >>> def nonlinear_feedback(state):
        ...     # Linear part: XOR of taps
        ...     linear = state[0] ^ state[3]
        ...     # Non-linear part: AND of state bits
        ...     nonlinear = state[1] & state[2]
        ...     return linear ^ nonlinear
        >>> 
        >>> nfsr = NFSR(base_lfsr, nonlinear_feedback)
        >>> sequence = nfsr.generate_sequence([1, 0, 0, 0], 100)
    """
    
    def __init__(
        self,
        base_lfsr_config: LFSRConfig,
        feedback_function: Callable[[List[int]], int]
    ):
        """
        Initialize NFSR.
        
        Args:
            base_lfsr_config: Base LFSR configuration
            feedback_function: Non-linear feedback function taking state and
                returning new feedback bit
        """
        self.base_lfsr_config = base_lfsr_config
        self.feedback_function = feedback_function
        self.state_size = base_lfsr_config.degree
    
    def get_config(self) -> AdvancedLFSRConfig:
        """Get NFSR configuration."""
        return AdvancedLFSRConfig(
            structure_type="nonlinear",
            base_lfsr_config=self.base_lfsr_config,
            parameters={
                'state_size': self.state_size,
                'field_order': self.base_lfsr_config.field_order
            }
        )
    
    def _clock_nfsr(self, state: List[int]) -> List[int]:
        """
        Clock NFSR one step.
        
        Args:
            state: Current state
        
        Returns:
            New state after one clock
        """
        # Compute non-linear feedback
        feedback = self.feedback_function(state)
        
        # Shift and insert feedback
        new_state = [feedback] + state[:-1]
        return new_state
    
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
            List of sequence elements (output bits)
        """
        if len(initial_state) != self.state_size:
            raise ValueError(
                f"NFSR requires state of size {self.state_size}, "
                f"got {len(initial_state)}"
            )
        
        state = initial_state[:]
        sequence = []
        
        for _ in range(length):
            # Output is typically MSB of state
            output = state[0]
            sequence.append(output)
            
            # Clock NFSR
            state = self._clock_nfsr(state)
        
        return sequence
    
    def analyze_structure(self) -> dict:
        """
        Analyze NFSR structure.
        
        Returns:
            Dictionary of structure properties
        """
        return {
            'structure_type': 'NFSR',
            'base_lfsr_degree': self.base_lfsr_config.degree,
            'base_lfsr_field_order': self.base_lfsr_config.field_order,
            'state_size': self.state_size,
            'has_nonlinear_feedback': True,
            'note': 'NFSR uses non-linear feedback function (not pure LFSR)'
        }
    
    def _assess_security(
        self,
        structure_properties: dict
    ) -> dict:
        """Assess NFSR security."""
        return {
            'nonlinearity': 'Non-linear feedback provides resistance to linear attacks',
            'known_vulnerabilities': [
                'Algebraic attacks (if non-linearity is low)',
                'Correlation attacks (if correlations exist)'
            ],
            'recommendations': [
                'Ensure sufficient non-linearity in feedback',
                'Consider filtered output for additional security'
            ]
        }


def create_simple_nfsr(
    base_lfsr_config: LFSRConfig,
    nonlinear_terms: Optional[List[tuple]] = None
) -> NFSR:
    """
    Create a simple NFSR with specified non-linear terms.
    
    This helper function creates an NFSR with a feedback function that includes
    both linear terms (from base LFSR) and non-linear terms (AND operations).
    
    Args:
        base_lfsr_config: Base LFSR configuration
        nonlinear_terms: List of (i, j) tuples for AND terms S_i & S_j
    
    Returns:
        NFSR instance
    
    Example:
        >>> from lfsr.attacks import LFSRConfig
        >>> from lfsr.advanced.nonlinear import create_simple_nfsr
        >>> 
        >>> base = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        >>> # Add non-linear term: S[1] & S[2]
        >>> nfsr = create_simple_nfsr(base, nonlinear_terms=[(1, 2)])
    """
    coeffs = base_lfsr_config.coefficients
    degree = base_lfsr_config.degree
    
    def feedback_func(state: List[int]) -> int:
        # Linear part: XOR of tap bits (from base LFSR)
        linear = 0
        for i, coeff in enumerate(coeffs):
            if coeff != 0:
                linear ^= state[i]
        
        # Non-linear part: AND of specified pairs
        nonlinear = 0
        if nonlinear_terms:
            for i, j in nonlinear_terms:
                if 0 <= i < degree and 0 <= j < degree:
                    nonlinear ^= (state[i] & state[j])
        
        return linear ^ nonlinear
    
    return NFSR(base_lfsr_config, feedback_func)
