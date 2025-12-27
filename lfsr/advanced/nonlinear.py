#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Non-Linear Feedback Shift Register (NFSR) Analysis

This module provides analysis capabilities for Non-Linear Feedback Shift
Registers (NFSRs), which generalize LFSRs by allowing non-linear feedback
functions.

**Historical Context**:

NFSRs were developed to address the linearity weakness of LFSRs. While LFSRs
have good statistical properties, their linearity makes them vulnerable to
algebraic attacks. NFSRs introduce non-linearity through AND, OR, and other
non-linear operations in the feedback function.

**Key Terminology**:

- **Non-Linear Feedback Shift Register (NFSR)**: A shift register with a
  non-linear feedback function. Unlike LFSRs, the feedback function can use
  AND, OR, and other non-linear operations.

- **Non-Linear Feedback Function**: A function that computes the new state bit
  from the current state using non-linear operations. This function is not
  linear (cannot be expressed as a linear combination of state bits).

- **Non-Linearity**: The property of a function that cannot be expressed as a
  linear combination of its inputs. Non-linearity is essential for cryptographic
  security.

- **Feedback Function**: The function that determines the new state bit from
  the current state. In NFSRs, this function is non-linear.

- **Non-Linear Complexity**: A measure of the non-linearity in the feedback
  function. Higher non-linear complexity generally provides better security.

**Mathematical Foundation**:

An NFSR of degree d has state S = (s_0, s_1, ..., s_{d-1}) and feedback function
f: GF(q)^d → GF(q). The state update is:

.. math::

   s_{new} = f(s_0, s_1, \\ldots, s_{d-1})

where f is a non-linear function (cannot be expressed as a linear combination).

For binary NFSRs (GF(2)), common non-linear operations include:
- AND: a ∧ b
- OR: a ∨ b
- XOR: a ⊕ b (linear)
- Combinations of the above
"""

from typing import Callable, List, Optional

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
    The feedback function can use AND, OR, and other non-linear operations,
    providing increased security compared to linear LFSRs.
    
    **Cipher Structure**:
    
    - **Base LFSR**: Underlying LFSR structure (for state management)
    - **Feedback Function**: Non-linear function computing new state bit
    - **State Size**: Same as base LFSR degree
    - **Field Order**: Same as base LFSR field order
    
    **Key Terminology**:
    
    - **NFSR**: Non-Linear Feedback Shift Register
    - **Non-Linear Feedback**: Feedback function uses non-linear operations
    - **Feedback Function**: Function mapping state to new state bit
    - **Non-Linearity**: Property that function is not linear
    
    **Example Usage**:
    
        >>> from lfsr.advanced.nonlinear import NFSR
        >>> from lfsr.attacks import LFSRConfig
        >>> 
        >>> base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        >>> 
        >>> # Define non-linear feedback function: f(s0, s1, s2, s3) = s0 AND s1 XOR s2
        >>> def feedback_func(state):
        ...     return (state[0] & state[1]) ^ state[2]
        >>> 
        >>> nfsr = NFSR(base_lfsr, feedback_func)
        >>> sequence = nfsr.generate_sequence([1, 0, 1, 1], 100)
    """
    
    def __init__(
        self,
        base_lfsr_config: LFSRConfig,
        feedback_function: Callable[[List[int]], int]
    ):
        """
        Initialize NFSR.
        
        Args:
            base_lfsr_config: Base LFSR configuration (defines state size and field)
            feedback_function: Non-linear feedback function mapping state to new bit
        """
        self.base_lfsr_config = base_lfsr_config
        self.feedback_function = feedback_function
        self.state = None
    
    def get_config(self) -> AdvancedLFSRConfig:
        """Get NFSR configuration."""
        return AdvancedLFSRConfig(
            structure_type="nonlinear",
            base_lfsr_config=self.base_lfsr_config,
            parameters={
                'feedback_type': 'non-linear',
                'degree': self.base_lfsr_config.degree,
                'field_order': self.base_lfsr_config.field_order
            }
        )
    
    def _clock_nfsr(self) -> int:
        """
        Clock NFSR one step.
        
        Computes new state bit using non-linear feedback function and shifts state.
        
        Returns:
            Output bit (old MSB)
        """
        if self.state is None:
            raise ValueError("NFSR state not initialized")
        
        # Get output bit (MSB)
        output = self.state[0]
        
        # Compute new state bit using non-linear feedback function
        new_bit = self.feedback_function(self.state)
        
        # Shift state and insert new bit
        self.state = self.state[1:] + [new_bit]
        
        return output
    
    def generate_sequence(
        self,
        initial_state: List[int],
        length: int
    ) -> List[int]:
        """
        Generate sequence from initial state.
        
        This method generates a sequence of the specified length using the
        NFSR starting from the given initial state.
        
        Args:
            initial_state: Initial state as a list of field elements
            length: Desired sequence length
        
        Returns:
            List of sequence elements
        
        Example:
            >>> nfsr = NFSR(base_lfsr, feedback_func)
            >>> sequence = nfsr.generate_sequence([1, 0, 1, 1], 100)
            >>> len(sequence) == 100
            True
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
            output = self._clock_nfsr()
            sequence.append(output)
        
        return sequence
    
    def analyze_structure(self) -> dict:
        """
        Analyze NFSR structure.
        
        This method analyzes the internal structure of the NFSR, including
        base LFSR properties and non-linear feedback properties.
        
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
        
        # Analyze non-linear feedback
        # Test feedback function with sample states to determine non-linearity
        field_order = self.base_lfsr_config.field_order
        degree = self.base_lfsr_config.degree
        
        # Check if feedback is linear (simplified test)
        is_linear = self._test_linearity()
        
        return {
            'base_lfsr': base_properties,
            'feedback_type': 'non-linear',
            'is_linear': is_linear,
            'degree': degree,
            'field_order': field_order,
            'state_space_size': field_order ** degree
        }
    
    def _test_linearity(self) -> bool:
        """
        Test if feedback function is linear.
        
        A function is linear if f(a + b) = f(a) + f(b) for all a, b.
        This is a simplified test using a few sample states.
        
        Returns:
            True if function appears linear, False otherwise
        """
        # Simplified linearity test
        # Test with a few sample states
        test_states = [
            [0] * self.base_lfsr_config.degree,
            [1] * self.base_lfsr_config.degree,
            [1, 0] * (self.base_lfsr_config.degree // 2) + [1] * (self.base_lfsr_config.degree % 2)
        ]
        
        # Check if f(a + b) = f(a) + f(b) for test states
        # This is a simplified test - full test would check all pairs
        try:
            for i, state_a in enumerate(test_states):
                for state_b in test_states[i+1:]:
                    # Compute f(a + b)
                    state_sum = [(a + b) % self.base_lfsr_config.field_order 
                                for a, b in zip(state_a, state_b)]
                    f_sum = self.feedback_function(state_sum)
                    
                    # Compute f(a) + f(b)
                    f_a = self.feedback_function(state_a)
                    f_b = self.feedback_function(state_b)
                    f_ab = (f_a + f_b) % self.base_lfsr_config.field_order
                    
                    if f_sum != f_ab:
                        return False  # Non-linear
        except Exception:
            # If test fails, assume non-linear
            return False
        
        # If all tests pass, might be linear (but this is not definitive)
        return True


def create_nfsr_with_and_feedback(
    base_lfsr_config: LFSRConfig,
    tap_positions: List[int]
) -> NFSR:
    """
    Create NFSR with AND-based feedback function.
    
    This helper function creates an NFSR where the feedback is the AND
    of specified tap positions.
    
    **Key Terminology**:
    
    - **AND-based Feedback**: Feedback function using AND operations
    - **Tap Positions**: Positions in state used for feedback
    
    Args:
        base_lfsr_config: Base LFSR configuration
        tap_positions: List of tap positions (indices) to AND together
    
    Returns:
        NFSR instance with AND-based feedback
    
    Example:
        >>> base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        >>> nfsr = create_nfsr_with_and_feedback(base_lfsr, [0, 1, 2])
        >>> sequence = nfsr.generate_sequence([1, 0, 1, 1], 100)
    """
    def and_feedback(state: List[int]) -> int:
        """AND-based feedback function."""
        result = state[tap_positions[0]]
        for pos in tap_positions[1:]:
            result = result & state[pos]
        return result
    
    return NFSR(base_lfsr_config, and_feedback)


def create_nfsr_with_combined_feedback(
    base_lfsr_config: LFSRConfig,
    linear_taps: List[int],
    non_linear_taps: List[int]
) -> NFSR:
    """
    Create NFSR with combined linear and non-linear feedback.
    
    This helper function creates an NFSR where the feedback combines linear
    (XOR) and non-linear (AND) operations.
    
    Args:
        base_lfsr_config: Base LFSR configuration
        linear_taps: Tap positions for linear (XOR) part
        non_linear_taps: Tap positions for non-linear (AND) part
    
    Returns:
        NFSR instance with combined feedback
    
    Example:
        >>> base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        >>> nfsr = create_nfsr_with_combined_feedback(base_lfsr, [0, 1], [2, 3])
        >>> sequence = nfsr.generate_sequence([1, 0, 1, 1], 100)
    """
    def combined_feedback(state: List[int]) -> int:
        """Combined linear and non-linear feedback function."""
        # Linear part (XOR)
        linear_part = 0
        for pos in linear_taps:
            linear_part ^= state[pos]
        
        # Non-linear part (AND)
        if non_linear_taps:
            non_linear_part = state[non_linear_taps[0]]
            for pos in non_linear_taps[1:]:
                non_linear_part = non_linear_part & state[pos]
            return linear_part ^ non_linear_part
        else:
            return linear_part
    
    return NFSR(base_lfsr_config, combined_feedback)
