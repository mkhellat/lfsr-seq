#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base classes and interfaces for advanced LFSR structures.

This module defines the base architecture for advanced LFSR structures, providing
common interfaces and data structures that all advanced structure implementations
inherit from.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from lfsr.attacks import LFSRConfig


@dataclass
class AdvancedLFSRConfig:
    """
    Configuration for an advanced LFSR structure.
    
    This class stores the configuration parameters for an advanced LFSR structure,
    including the base LFSR configuration and structure-specific parameters.
    
    Attributes:
        structure_type: Type of advanced structure (e.g., "filtered", "clock_controlled")
        base_lfsr_config: Base LFSR configuration
        parameters: Dictionary of structure-specific parameters
    """
    structure_type: str
    base_lfsr_config: LFSRConfig
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AdvancedLFSRAnalysisResult:
    """
    Results from advanced LFSR structure analysis.
    
    This class contains comprehensive analysis results for an advanced LFSR
    structure, including structure properties, sequence properties, and
    security assessment.
    
    Attributes:
        structure_type: Type of advanced structure analyzed
        structure_properties: Properties of the structure itself
        sequence_properties: Properties of generated sequences
        security_assessment: Security assessment and recommendations
        details: Additional analysis details
    """
    structure_type: str
    structure_properties: Dict[str, Any] = field(default_factory=dict)
    sequence_properties: Dict[str, Any] = field(default_factory=dict)
    security_assessment: Dict[str, Any] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)


class AdvancedLFSR(ABC):
    """
    Base class for advanced LFSR structures.
    
    This abstract base class defines the interface that all advanced LFSR
    structure implementations must follow. It provides a consistent API for
    analyzing different advanced structures.
    
    **Key Terminology**:
    
    - **Advanced LFSR Structure**: An extension of basic LFSRs that includes
      non-linear filtering, clock control, or multiple outputs. 
      
      **CRITICAL**: LFSR always means Linear Feedback Shift Register - the
      feedback is ALWAYS linear (XOR only). If feedback is non-linear, it is
      an NFSR (Non-Linear Feedback Shift Register), NOT an LFSR.
    
    - **LFSR (Linear Feedback Shift Register)**: A shift register with LINEAR
      feedback function. The feedback is always linear (XOR of state bits).
      This is the fundamental structure - if feedback is non-linear, it's not
      an LFSR, it's an NFSR.
    
    - **NFSR (Non-Linear Feedback Shift Register)**: A shift register with
      NON-LINEAR feedback function (uses AND, OR, or other non-linear operations).
      This is a generalization of LFSR where feedback is not restricted to
      linear operations. NFSRs are NOT LFSRs - they are a different structure.
    
    - **Filtered LFSR**: An LFSR (with LINEAR feedback) where a non-linear
      filtering function is applied to the state to produce output. The LFSR
      feedback is LINEAR (XOR only), but the output is filtered through a
      non-linear function. This provides non-linearity in the output while
      keeping linear feedback.
    
    - **Clock-Controlled LFSR**: An LFSR (with LINEAR feedback) with irregular
      clocking, where the LFSR doesn't always advance on each step. The feedback
      is LINEAR (XOR only), but the clocking pattern is irregular. Clocking is
      controlled by a clock control function or another LFSR.
    
    - **Multi-Output LFSR**: An LFSR (with LINEAR feedback) that produces
      multiple output bits per step, rather than a single bit. The feedback
      is LINEAR (XOR only), but multiple state bits are output simultaneously.
    
    - **Irregular Clocking**: A clocking pattern that is not regular (not every
      step). Common patterns include stop-and-go, step-1/step-2, and others.
      This affects when the LFSR advances, NOT the linearity of the feedback.
      The feedback remains LINEAR (XOR only).
    
    **Subclassing**:
    
    To implement a new advanced structure, subclass `AdvancedLFSR` and implement:
    
    1. `generate_sequence()`: Generate sequence from initial state
    2. `analyze_structure()`: Analyze and return structure properties
    3. `get_config()`: Return structure configuration
    
    Example:
        >>> class MyAdvancedLFSR(AdvancedLFSR):
        ...     def generate_sequence(self, initial_state, length):
        ...         # Implementation
        ...         pass
        ...     def analyze_structure(self):
        ...         # Implementation
        ...         pass
        ...     def get_config(self):
        ...         # Implementation
        ...         pass
    """
    
    @abstractmethod
    def generate_sequence(
        self,
        initial_state: List[int],
        length: int
    ) -> List[int]:
        """
        Generate sequence from initial state.
        
        This method generates a sequence of the specified length using the
        advanced LFSR structure starting from the given initial state.
        
        Args:
            initial_state: Initial state as a list of field elements
            length: Desired sequence length
        
        Returns:
            List of sequence elements
        """
        pass
    
    @abstractmethod
    def analyze_structure(self) -> Dict[str, Any]:
        """
        Analyze and return structure properties.
        
        This method analyzes the internal structure of the advanced LFSR,
        including base LFSR properties and structure-specific properties.
        
        Returns:
            Dictionary of structure properties
        """
        pass
    
    @abstractmethod
    def get_config(self) -> AdvancedLFSRConfig:
        """
        Get structure configuration.
        
        Returns:
            AdvancedLFSRConfig with structure parameters
        """
        pass
    
    def analyze(
        self,
        initial_state: Optional[List[int]] = None,
        sequence_length: int = 1000
    ) -> AdvancedLFSRAnalysisResult:
        """
        Perform comprehensive structure analysis.
        
        This method performs a complete analysis of the advanced LFSR structure,
        including structure analysis, sequence generation, and property analysis.
        
        Args:
            initial_state: Optional initial state (if None, uses default)
            sequence_length: Length of sequence to generate for analysis
        
        Returns:
            AdvancedLFSRAnalysisResult with comprehensive analysis
        """
        # Analyze structure
        structure_properties = self.analyze_structure()
        
        # Generate sequence if initial state provided
        sequence_properties = {}
        if initial_state is not None:
            sequence = self.generate_sequence(initial_state, sequence_length)
            
            # Analyze sequence properties
            sequence_properties = self._analyze_sequence_properties(sequence)
        
        # Security assessment
        security_assessment = self._assess_security(structure_properties)
        
        return AdvancedLFSRAnalysisResult(
            structure_type=self.get_config().structure_type,
            structure_properties=structure_properties,
            sequence_properties=sequence_properties,
            security_assessment=security_assessment
        )
    
    def _analyze_sequence_properties(
        self,
        sequence: List[int]
    ) -> Dict[str, Any]:
        """
        Analyze properties of generated sequence.
        
        This helper method analyzes statistical and cryptographic properties
        of the generated sequence.
        
        Args:
            sequence: Sequence to analyze
        
        Returns:
            Dictionary of sequence properties
        """
        if not sequence:
            return {}
        
        # Basic statistics
        field_order = self.get_config().base_lfsr_config.field_order
        element_counts = {}
        for element in sequence:
            element_counts[element] = element_counts.get(element, 0) + 1
        
        return {
            'length': len(sequence),
            'element_counts': element_counts,
            'field_order': field_order
        }
    
    def _assess_security(
        self,
        structure_properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess structure security based on properties.
        
        This helper method provides a security assessment based on the structure's
        properties.
        
        Args:
            structure_properties: Structure properties
        
        Returns:
            Dictionary with security assessment
        """
        return {
            'structure_complexity': 'medium',  # Placeholder
            'known_vulnerabilities': [],
            'recommendations': []
        }
