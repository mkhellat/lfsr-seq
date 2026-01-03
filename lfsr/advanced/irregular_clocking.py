#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Irregular Clocking Patterns Analysis

This module provides analysis capabilities for LFSRs with irregular clocking
patterns.

**IMPORTANT TERMINOLOGY CLARIFICATION**:

- **LFSR (Linear Feedback Shift Register)**: Feedback is ALWAYS linear (XOR only).
  This is the definition of LFSR.

- **Irregular Clocking LFSR**: An LFSR (with LINEAR feedback) that uses an
  irregular clocking pattern. The feedback remains linear - only the clocking
  pattern is irregular (advances variable number of steps).

This module implements irregular clocking LFSRs, which ARE LFSRs (linear feedback)
with irregular clocking patterns.

**Historical Context**:

Irregular clocking patterns were developed to increase security by introducing
non-linearity through clock control. Different patterns provide different
security properties and efficiency trade-offs.

**Key Terminology**:

- **Irregular Clocking**: Clocking pattern that is not regular (not every step).
  The LFSR may advance 0, 1, or more steps per output.

- **Stop-and-Go**: Pattern where LFSR stops when control bit is 0, advances
  when control bit is 1.

- **Step-1/Step-2**: Pattern where LFSR advances 1 step when control bit is 0,
  advances 2 steps when control bit is 1.

- **Shrinking Generator**: Pattern where LFSR output is used only when control
  bit is 1, otherwise discarded.

**Mathematical Foundation**:

For irregular clocking, the number of steps advanced is determined by a
control function:

steps = f(c)

where c is the control value and f is the clocking function.
"""

from typing import List, Optional, Callable

from lfsr.sage_imports import *

from lfsr.attacks import LFSRConfig
from lfsr.advanced.base import (
    AdvancedLFSR,
    AdvancedLFSRConfig
)
from lfsr.core import build_state_update_matrix


class IrregularClockingLFSR(AdvancedLFSR):
    """
    Irregular clocking LFSR implementation.
    
    **IMPORTANT**: An Irregular Clocking LFSR IS an LFSR (Linear Feedback Shift Register).
    The feedback remains LINEAR (XOR only). The irregularity comes from the
    clocking pattern (variable steps per output), not from the feedback itself.
    
    An irregular clocking LFSR uses a clocking pattern function to determine
    how many steps to advance per output. This creates irregularity in the
    sequence generation, but the feedback is still linear.
    
    **Key Distinction**:
    - **LFSR Feedback**: LINEAR (XOR only) - this is what makes it an LFSR
    - **Clocking Pattern**: IRREGULAR (variable steps per output)
    
    **Structure**:
    
    - **Base LFSR**: Underlying LFSR with LINEAR feedback
    - **Clocking Pattern Function**: Function determining steps to advance
    - **Irregular Pattern**: Clocking is not regular (but feedback is linear)
    
    **Example Usage**:
    
        >>> from lfsr.advanced.irregular_clocking import IrregularClockingLFSR
        >>> from lfsr.attacks import LFSRConfig
        >>> 
        >>> base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        >>> 
        >>> # Step-1/Step-2 pattern: advance 1 if control=0, 2 if control=1
        >>> def step_pattern(control_bit):
        ...     return 1 if control_bit == 0 else 2
        >>> 
        >>> # Use another LFSR for control
        >>> control_lfsr = LFSRConfig(coefficients=[1, 1], field_order=2, degree=2)
        >>> 
        >>> iclfsr = IrregularClockingLFSR(base_lfsr, control_lfsr, step_pattern)
        >>> sequence = iclfsr.generate_sequence([1, 0, 0, 0], [1, 0], 100)
    """
    
    def __init__(
        self,
        base_lfsr_config: LFSRConfig,
        control_lfsr_config: Optional[LFSRConfig] = None,
        clocking_pattern_function: Optional[Callable[[int], int]] = None
    ):
        """
        Initialize Irregular Clocking LFSR.
        
        Args:
            base_lfsr_config: Base LFSR configuration
            control_lfsr_config: Optional control LFSR configuration
            clocking_pattern_function: Function taking control value and returning
                number of steps to advance
        """
        self.base_lfsr_config = base_lfsr_config
        self.control_lfsr_config = control_lfsr_config
        self.clocking_pattern_function = clocking_pattern_function
        
        # Build state update matrices
        self.base_C, _ = build_state_update_matrix(
            base_lfsr_config.coefficients,
            base_lfsr_config.field_order
        )
        
        if control_lfsr_config:
            self.control_C, _ = build_state_update_matrix(
                control_lfsr_config.coefficients,
                control_lfsr_config.field_order
            )
        else:
            self.control_C = None
        
        # Default pattern: always advance 1 step
        if clocking_pattern_function is None:
            self.clocking_pattern_function = lambda x: 1
    
    def get_config(self) -> AdvancedLFSRConfig:
        """Get Irregular Clocking LFSR configuration."""
        return AdvancedLFSRConfig(
            structure_type="irregular_clocking",
            base_lfsr_config=self.base_lfsr_config,
            parameters={
                'has_control_lfsr': self.control_lfsr_config is not None,
                'has_irregular_pattern': True
            }
        )
    
    def _clock_lfsr(self, state: List[int], C, field_order: int, steps: int = 1) -> List[int]:
        """Clock an LFSR specified number of steps."""
        F = GF(field_order)
        state_vec = vector(F, state)
        
        for _ in range(steps):
            state_vec = C * state_vec
        
        return [int(x) for x in state_vec]
    
    def generate_sequence(
        self,
        initial_state: List[int],
        length: int,
        control_initial_state: Optional[List[int]] = None
    ) -> List[int]:
        """
        Generate sequence from initial state.
        
        Args:
            initial_state: Initial state of base LFSR
            length: Desired sequence length
            control_initial_state: Optional initial state of control LFSR
        
        Returns:
            List of sequence elements
        """
        base_state = initial_state[:]
        
        if self.control_lfsr_config:
            if control_initial_state is None:
                control_state = [1] * self.control_lfsr_config.degree
            else:
                control_state = control_initial_state[:]
        else:
            control_state = None
        
        sequence = []
        
        for _ in range(length):
            # Get control output
            if control_state is not None:
                control_output = control_state[0]  # MSB
            else:
                control_output = 0  # Default
            
            # Output from base LFSR
            output = base_state[0]  # MSB
            sequence.append(output)
            
            # Determine steps to advance
            steps = self.clocking_pattern_function(control_output)
            
            # Clock base LFSR
            base_state = self._clock_lfsr(
                base_state,
                self.base_C,
                self.base_lfsr_config.field_order,
                steps
            )
            
            # Clock control LFSR (always)
            if control_state is not None:
                control_state = self._clock_lfsr(
                    control_state,
                    self.control_C,
                    self.control_lfsr_config.field_order,
                    1
                )
        
        return sequence
    
    def analyze_structure(self) -> dict:
        """Analyze Irregular Clocking LFSR structure."""
        return {
            'structure_type': 'IrregularClockingLFSR',
            'base_lfsr_degree': self.base_lfsr_config.degree,
            'has_control_lfsr': self.control_lfsr_config is not None,
            'control_lfsr_degree': (
                self.control_lfsr_config.degree
                if self.control_lfsr_config else None
            ),
            'has_irregular_pattern': True,
            'note': 'Irregular clocking LFSR uses non-regular clocking pattern'
        }
    
    def _assess_security(
        self,
        structure_properties: dict
    ) -> dict:
        """Assess Irregular Clocking LFSR security."""
        return {
            'irregularity': 'Irregular clocking provides resistance to linear analysis',
            'known_vulnerabilities': [
                'Clock control analysis',
                'Pattern analysis'
            ],
            'recommendations': [
                'Use complex clocking patterns',
                'Ensure control is independent'
            ]
        }


def create_stop_and_go_pattern() -> Callable[[int], int]:
    """
    Create stop-and-go clocking pattern function.
    
    Returns:
        Function that returns 1 if control=1, 0 if control=0
    """
    return lambda control: 1 if control == 1 else 0


def create_step_1_step_2_pattern() -> Callable[[int], int]:
    """
    Create step-1/step-2 clocking pattern function.
    
    Returns:
        Function that returns 1 if control=0, 2 if control=1
    """
    return lambda control: 1 if control == 0 else 2
