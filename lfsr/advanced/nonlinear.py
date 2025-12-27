#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Non-Linear Feedback LFSR Analysis

This module provides analysis capabilities for LFSRs with non-linear feedback
functions, also known as Non-Linear Feedback Shift Registers (NFSRs).

**Historical Context**:

Non-linear feedback shift registers were developed to overcome the linearity
weakness of LFSRs. While LFSRs have good statistical properties, their linearity
makes them vulnerable to algebraic attacks. NFSRs introduce non-linearity through
non-linear feedback functions, making them more resistant to certain attacks.

**Key Terminology**:

- **Non-Linear Feedback Shift Register (NFSR)**: A shift register where the
  feedback function is not linear. The feedback function can use AND, OR, and
  other non-linear operations, not just XOR.

- **Non-Linear Feedback Function**: A function that computes the new state bit
  from the current state using non-linear operations. Unlike linear feedback
  (which only uses XOR), non-linear feedback can use AND, OR, and other operations.

- **Non-Linearity**: The property of a function that is not linear. A function
  f is non-linear if f(x ⊕ y) ≠ f(x) ⊕ f(y) for some x, y.

- **Feedback Function**: The function that computes the new state bit from
  the current state. In LFSRs, this is linear (XOR of tap bits). In NFSRs,
  this is non-linear.

- **Non-Linear Complexity**: A measure of the non-linearity in the feedback
  function. Higher non-linear complexity generally provides better security.

**Mathematical Foundation**:

A non-linear feedback shift register of degree d over GF(q) has state
S = (s_0, s_1, ..., s_{d-1}) and feedback function f: GF(q)^d → GF(q).

The state update is:
S_{t+1} = (f(S_t), s_0, s_1, ..., s_{d-2})

where f is a non-linear function (not just a linear combination).

Common non-linear operations include:
- AND (conjunction): a ∧ b
- OR (disjunction): a ∨ b
- NAND, NOR, etc.
"""

from typing import List, Callable, Optional

from sage.all import *

from lfsr.attacks import LFSRConfig
from lfsr.advanced.base import (
    AdvancedLFSR,
    AdvancedLFSRConfig,
    AdvancedLFSRAnalysisResult
)


class NonLinearLFSR(AdvancedLFSR):
    """
    Non-Linear Feedback Shift Register (NFSR) implementation.
    
    An NFSR is a generalization of an LFSR where the feedback function is
    non-linear. This introduces non-linearity into the state update, making
    the register more resistant to certain attacks.
    
    **Key Terminology**:
    
    - **NFSR**: Non-Linear Feedback Shift Register, a shift register with
      non-linear feedback function.
    
    - **Non-Linear Feedback**: Feedback function that uses non-linear operations
      (AND, OR, etc.) in addition to or instead of linear operations (XOR).
    
    - **Feedback Function**: Function f: GF(q)^d → GF(q) that computes the new
      state bit from the current state. For NFSRs, this function is non-linear.
    
    - **Non-Linearity Measure**: Quantifies how non-linear a function is. Common
      measures include algebraic degree, non-linearity (distance to linear
      functions), and Walsh-Hadamard transform.
    
    **Cipher Structure**:
    
    An NFSR of degree d has:
    - State: (s_0, s_1, ..., s_{d-1})
    - Feedback function: f(s_0, s_1, ..., s_{d-1}) → new bit
    - State update: Shift and insert feedback
    
    **Example Usage**:
    
        >>> from lfsr.advanced.nonlinear import NonLinearLFSR
        >>> from lfsr.attacks import LFSRConfig
        >>> 
        >>> base_config = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        >>> 
        >>> # Define non-linear feedback function (AND of first two bits)
        >>> def feedback_func(state):
        ...     return state[0] & state[1]  # Non-linear: AND operation
        >>> 
        >>> nfsr = NonLinearLFSR(base_config, feedback_func)
        >>> sequence = nfsr.generate_sequence([1, 0, 1, 1], 100)
    """
    
    def __init__(
        self,
        base_lfsr_config: LFSRConfig,
        feedback_function: Callable[[List[int]], int]
    ):
        """
        Initialize non-linear LFSR.
        
        Args:
            base_lfsr_config: Base LFSR configuration (defines degree, field)
            feedback_function: Non-linear feedback function mapping state to new bit
        """
        self.base_lfsr_config = base_lfsr_config
        self.feedback_function = feedback_function
        self.degree = base_lfsr_config.degree
        self.field_order = base_lfsr_config.field_order
    
    def get_config(self) -> AdvancedLFSRConfig:
        """Get NFSR configuration."""
        return AdvancedLFSRConfig(
            structure_type="nonlinear",
            base_lfsr_config=self.base_lfsr_config,
            parameters={
                'degree': self.degree,
                'field_order': self.field_order,
                'feedback_type': 'non-linear'
            }
        )
    
    def generate_sequence(
        self,
        initial_state: List[int],
        length: int
    ) -> List[int]:
        """
        Generate sequence from initial state.
        
        This method generates a sequence using the non-linear feedback function.
        The sequence is generated by repeatedly applying the feedback function
        and shifting the state.
        
        **Algorithm**:
        
        1. Initialize state with initial_state
        2. For each output bit:
           - Compute feedback: f(state)
           - Output current state bit (typically s_0)
           - Shift state: (f(state), s_0, s_1, ..., s_{d-2})
        
        Args:
            initial_state: Initial state as list of field elements
            length: Desired sequence length
        
        Returns:
            List of sequence elements
        """
        if len(initial_state) != self.degree:
            raise ValueError(
                f"Initial state must have length {self.degree}, got {len(initial_state)}"
            )
        
        state = initial_state[:]  # Copy
        sequence = []
        
        for _ in range(length):
            # Output current state bit (typically MSB)
            output = state[0]
            sequence.append(output)
            
            # Compute non-linear feedback
            feedback = self.feedback_function(state)
            
            # Update state: shift and insert feedback
            state = [feedback] + state[:-1]
        
        return sequence
    
    def analyze_structure(self) -> dict:
        """
        Analyze NFSR structure properties.
        
        This method analyzes the non-linear feedback function and structure
        properties, including non-linearity measures.
        
        Returns:
            Dictionary of structure properties
        """
        # Analyze feedback function
        # For binary case, we can analyze non-linearity
        non_linearity = self._compute_non_linearity()
        algebraic_degree = self._estimate_algebraic_degree()
        
        return {
            'structure_type': 'non-linear feedback shift register',
            'degree': self.degree,
            'field_order': self.field_order,
            'feedback_type': 'non-linear',
            'non_linearity': non_linearity,
            'estimated_algebraic_degree': algebraic_degree,
            'note': 'NFSR uses non-linear feedback function'
        }
    
    def _compute_non_linearity(self) -> float:
        """
        Compute non-linearity measure of feedback function.
        
        For binary functions, non-linearity is the minimum Hamming distance
        to any affine function. This is a simplified estimation.
        
        Returns:
            Estimated non-linearity measure
        """
        # Simplified non-linearity computation
        # Full implementation would use Walsh-Hadamard transform
        if self.field_order != 2:
            return 0.0  # Non-linearity primarily defined for binary
        
        # Estimate by testing linearity
        # A function is linear if f(x ⊕ y) = f(x) ⊕ f(y) for all x, y
        # We test a sample to estimate non-linearity
        test_count = min(100, 2 ** self.degree)
        non_linear_count = 0
        
        # Test linearity property on sample
        for _ in range(test_count):
            # Generate random states
            state1 = [random.randint(0, 1) for _ in range(self.degree)]
            state2 = [random.randint(0, 1) for _ in range(self.degree)]
            
            # Compute XOR of states
            state_xor = [(state1[i] ^ state2[i]) for i in range(self.degree)]
            
            # Check if f(x ⊕ y) = f(x) ⊕ f(y)
            f_xor = self.feedback_function(state_xor)
            f_x = self.feedback_function(state1)
            f_y = self.feedback_function(state2)
            
            if f_xor != (f_x ^ f_y):
                non_linear_count += 1
        
        # Non-linearity estimate: fraction of non-linear behavior
        return non_linear_count / test_count if test_count > 0 else 0.0
    
    def _estimate_algebraic_degree(self) -> int:
        """
        Estimate algebraic degree of feedback function.
        
        The algebraic degree is the degree of the polynomial representation
        of the function. This is a simplified estimation.
        
        Returns:
            Estimated algebraic degree
        """
        # Simplified estimation
        # Full implementation would analyze the algebraic normal form (ANF)
        # For now, return a conservative estimate
        return min(self.degree, 3)  # Most practical NFSRs have degree ≤ 3


class NFSR(NonLinearLFSR):
    """
    Alias for NonLinearLFSR.
    
    NFSR is the standard abbreviation for Non-Linear Feedback Shift Register.
    This class provides a convenient alias.
    """
    pass
