#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Clock-Controlled LFSR Analysis

This module provides analysis capabilities for clock-controlled LFSRs.

**IMPORTANT TERMINOLOGY CLARIFICATION**:

- **LFSR (Linear Feedback Shift Register)**: Feedback is ALWAYS linear (XOR only).
  This is the definition of LFSR.

- **Clock-Controlled LFSR**: An LFSR (with LINEAR feedback) that has irregular
  clocking patterns. The feedback remains linear - only the clocking pattern
  is irregular (the LFSR doesn't always advance).

This module implements clock-controlled LFSRs, which ARE LFSRs (linear feedback)
with irregular clocking patterns.

**Historical Context**:

Clock-controlled LFSRs were developed to increase security by introducing
irregularity in the clocking pattern. This makes linear analysis more
difficult. Examples include the shrinking generator and self-shrinking generator.

**Key Terminology**:

- **Clock-Controlled LFSR**: An LFSR with irregular clocking, where the LFSR
  doesn't always advance on each step. Clocking is controlled by a clock
  control function or another LFSR.

- **Clock Control Function**: Function determining when the LFSR advances.
  The function takes the current state (or control LFSR output) and returns
  whether to clock.

- **Irregular Clocking**: Clocking pattern that is not regular (not every step).
  The LFSR may advance 0, 1, or more steps per output.

- **Control LFSR**: Separate LFSR that controls the clocking of the main LFSR.
  The control LFSR output determines when the main LFSR advances.

**Mathematical Foundation**:

For a clock-controlled LFSR, the clocking is determined by a control function:

clock = c(S_control)

where c is the clock control function and S_control is the control state
(or control LFSR output).

The main LFSR advances only when clock = 1.
"""

from typing import List, Optional, Callable

from lfsr.sage_imports import *

from lfsr.attacks import LFSRConfig
from lfsr.advanced.base import (
    AdvancedLFSR,
    AdvancedLFSRConfig
)
from lfsr.core import build_state_update_matrix


class ClockControlledLFSR(AdvancedLFSR):
    """
    Clock-controlled LFSR implementation.
    
    **IMPORTANT**: A Clock-Controlled LFSR IS an LFSR (Linear Feedback Shift Register).
    The feedback remains LINEAR (XOR only). The irregularity comes from the
    clocking pattern, not from the feedback itself.
    
    A clock-controlled LFSR has irregular clocking controlled by a clock
    control function or another LFSR. The main LFSR advances only when the
    control function indicates. The feedback is still linear.
    
    **Key Distinction**:
    - **LFSR Feedback**: LINEAR (XOR only) - this is what makes it an LFSR
    - **Clocking Pattern**: IRREGULAR (doesn't always advance)
    
    **Structure**:
    
    - **Main LFSR**: The LFSR with LINEAR feedback being clock-controlled
    - **Clock Control**: Function or LFSR determining when to clock
    - **Irregular Clocking**: Main LFSR doesn't always advance (but feedback is linear)
    
    **Example Usage**:
    
        >>> from lfsr.advanced.clock_controlled import ClockControlledLFSR
        >>> from lfsr.attacks import LFSRConfig
        >>> 
        >>> main_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        >>> 
        >>> # Simple clock control: advance if control bit is 1
        >>> def clock_control(control_bit):
        ...     return control_bit == 1
        >>> 
        >>> # Use another LFSR as control
        >>> control_lfsr = LFSRConfig(coefficients=[1, 1], field_order=2, degree=2)
        >>> 
        >>> cclfsr = ClockControlledLFSR(main_lfsr, control_lfsr, clock_control)
        >>> sequence = cclfsr.generate_sequence([1, 0, 0, 0], [1, 0], 100)
    """
    
    def __init__(
        self,
        main_lfsr_config: LFSRConfig,
        control_lfsr_config: Optional[LFSRConfig] = None,
        clock_control_function: Optional[Callable] = None
    ):
        """
        Initialize Clock-Controlled LFSR.
        
        Args:
            main_lfsr_config: Configuration of main LFSR (being controlled)
            control_lfsr_config: Optional control LFSR configuration
            clock_control_function: Function determining clocking (takes control
                state/output and returns bool)
        """
        self.main_lfsr_config = main_lfsr_config
        self.control_lfsr_config = control_lfsr_config
        self.clock_control_function = clock_control_function
        
        # Build state update matrices
        self.main_C, _ = build_state_update_matrix(
            main_lfsr_config.coefficients,
            main_lfsr_config.field_order
        )
        
        if control_lfsr_config:
            self.control_C, _ = build_state_update_matrix(
                control_lfsr_config.coefficients,
                control_lfsr_config.field_order
            )
        else:
            self.control_C = None
        
        # Default clock control: always clock
        if clock_control_function is None:
            self.clock_control_function = lambda x: True
    
    def get_config(self) -> AdvancedLFSRConfig:
        """Get Clock-Controlled LFSR configuration."""
        return AdvancedLFSRConfig(
            structure_type="clock_controlled",
            base_lfsr_config=self.main_lfsr_config,
            parameters={
                'has_control_lfsr': self.control_lfsr_config is not None,
                'has_clock_control': self.clock_control_function is not None
            }
        )
    
    def _clock_lfsr(self, state: List[int], C, field_order: int) -> List[int]:
        """Clock an LFSR one step."""
        F = GF(field_order)
        state_vec = vector(F, state)
        new_state_vec = C * state_vec
        return [int(x) for x in new_state_vec]
    
    def generate_sequence(
        self,
        initial_state: List[int],
        length: int,
        control_initial_state: Optional[List[int]] = None
    ) -> List[int]:
        """
        Generate sequence from initial state.
        
        Args:
            initial_state: Initial state of main LFSR
            length: Desired sequence length
            control_initial_state: Optional initial state of control LFSR
        
        Returns:
            List of sequence elements
        """
        main_state = initial_state[:]
        
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
                control_output = 1  # Default: always clock
            
            # Determine if main LFSR should clock
            should_clock = self.clock_control_function(control_output)
            
            # Output from main LFSR
            output = main_state[0]  # MSB
            sequence.append(output)
            
            # Clock main LFSR if control says so
            if should_clock:
                main_state = self._clock_lfsr(
                    main_state,
                    self.main_C,
                    self.main_lfsr_config.field_order
                )
            
            # Clock control LFSR (always)
            if control_state is not None:
                control_state = self._clock_lfsr(
                    control_state,
                    self.control_C,
                    self.control_lfsr_config.field_order
                )
        
        return sequence
    
    def analyze_structure(self) -> dict:
        """Analyze Clock-Controlled LFSR structure."""
        return {
            'structure_type': 'ClockControlledLFSR',
            'main_lfsr_degree': self.main_lfsr_config.degree,
            'has_control_lfsr': self.control_lfsr_config is not None,
            'control_lfsr_degree': (
                self.control_lfsr_config.degree
                if self.control_lfsr_config else None
            ),
            'has_irregular_clocking': True,
            'note': 'Clock-controlled LFSR has irregular clocking pattern'
        }
    
    def _assess_security(
        self,
        structure_properties: dict
    ) -> dict:
        """Assess Clock-Controlled LFSR security."""
        return {
            'irregularity': 'Irregular clocking provides resistance to linear analysis',
            'known_vulnerabilities': [
                'Clock control analysis',
                'Correlation attacks (if correlations exist)'
            ],
            'recommendations': [
                'Use complex clock control function',
                'Ensure control LFSR is independent'
            ]
        }


def create_stop_and_go_lfsr(
    main_lfsr_config: LFSRConfig,
    control_lfsr_config: LFSRConfig
) -> ClockControlledLFSR:
    """
    Create a stop-and-go clock-controlled LFSR.
    
    In stop-and-go, the main LFSR advances only when control LFSR output is 1.
    When control output is 0, the main LFSR stops (doesn't advance).
    
    Args:
        main_lfsr_config: Main LFSR configuration
        control_lfsr_config: Control LFSR configuration
    
    Returns:
        ClockControlledLFSR instance with stop-and-go behavior
    """
    def stop_and_go(control_output: int) -> bool:
        return control_output == 1
    
    return ClockControlledLFSR(
        main_lfsr_config,
        control_lfsr_config,
        stop_and_go
    )
