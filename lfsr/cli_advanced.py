#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI functions for advanced LFSR structure analysis.

This module provides command-line interface functions for analyzing advanced
LFSR structures, including NFSRs, filtered LFSRs, clock-controlled LFSRs,
multi-output LFSRs, and irregular clocking patterns.
"""

import sys
from typing import List, Optional, TextIO

from lfsr.attacks import LFSRConfig
from lfsr.advanced import (
    NFSR,
    FilteredLFSR,
    ClockControlledLFSR,
    MultiOutputLFSR,
    IrregularClockingLFSR,
    create_simple_nfsr,
    create_simple_filtered_lfsr,
    create_stop_and_go_lfsr,
    create_simple_multi_output_lfsr,
    create_stop_and_go_pattern,
    create_step_1_step_2_pattern
)


def get_advanced_structure_instance(
    structure_type: str,
    base_lfsr_config: LFSRConfig
):
    """
    Get advanced structure instance from type.
    
    Args:
        structure_type: Type of structure (nfsr, filtered, etc.)
        base_lfsr_config: Base LFSR configuration
    
    Returns:
        AdvancedLFSR instance
    """
    if structure_type == "nfsr":
        # Create simple NFSR with AND term
        return create_simple_nfsr(base_lfsr_config, nonlinear_terms=[(1, 2)])
    
    elif structure_type == "filtered":
        # Create simple filtered LFSR
        return create_simple_filtered_lfsr(
            base_lfsr_config,
            filter_taps=[0, 1],
            nonlinear_terms=[(2, 3)]
        )
    
    elif structure_type == "clock_controlled":
        # Create stop-and-go clock-controlled LFSR
        # Need control LFSR - use simple 2-bit LFSR
        control_lfsr = LFSRConfig(coefficients=[1, 1], field_order=2, degree=2)
        return create_stop_and_go_lfsr(base_lfsr_config, control_lfsr)
    
    elif structure_type == "multi_output":
        # Create multi-output LFSR outputting first 2 bits
        return create_simple_multi_output_lfsr(base_lfsr_config, [0, 1])
    
    elif structure_type == "irregular":
        # Create irregular clocking LFSR with step-1/step-2 pattern
        control_lfsr = LFSRConfig(coefficients=[1, 1], field_order=2, degree=2)
        pattern_func = create_step_1_step_2_pattern()
        return IrregularClockingLFSR(base_lfsr_config, control_lfsr, pattern_func)
    
    else:
        raise ValueError(f"Unknown structure type: {structure_type}")


def perform_advanced_structure_analysis_cli(
    structure_type: str,
    base_lfsr_config: LFSRConfig,
    analyze_structure: bool = False,
    generate_sequence: bool = False,
    sequence_length: int = 1000,
    output_file: Optional[TextIO] = None
) -> None:
    """
    Perform advanced structure analysis from CLI.
    
    Args:
        structure_type: Type of structure to analyze
        base_lfsr_config: Base LFSR configuration
        analyze_structure: Whether to analyze structure
        generate_sequence: Whether to generate sequence
        sequence_length: Length of sequence to generate
        output_file: Optional file for output
    """
    if output_file is None:
        output_file = sys.stdout
    
    print("=" * 70, file=output_file)
    print("Advanced LFSR Structure Analysis", file=output_file)
    print("=" * 70, file=output_file)
    print(file=output_file)
    
    # Get structure instance
    structure = get_advanced_structure_instance(structure_type, base_lfsr_config)
    config = structure.get_config()
    
    print(f"Structure Type: {config.structure_type}", file=output_file)
    print(f"Base LFSR Degree: {base_lfsr_config.degree}", file=output_file)
    print(f"Base LFSR Field Order: {base_lfsr_config.field_order}", file=output_file)
    print(file=output_file)
    
    # Terminology reminder
    if structure_type == "nfsr":
        print("⚠️  NOTE: NFSR is NOT an LFSR (non-linear feedback)", file=output_file)
    else:
        print("✓ NOTE: This IS an LFSR (linear feedback) with advanced features", file=output_file)
    print(file=output_file)
    
    if analyze_structure:
        print("=" * 70, file=output_file)
        print("Structure Analysis", file=output_file)
        print("=" * 70, file=output_file)
        print(file=output_file)
        
        properties = structure.analyze_structure()
        
        for key, value in properties.items():
            print(f"  {key}: {value}", file=output_file)
        print(file=output_file)
    
    if generate_sequence:
        print("=" * 70, file=output_file)
        print("Sequence Generation", file=output_file)
        print("=" * 70, file=output_file)
        print(file=output_file)
        
        # Use default initial state
        initial_state = [1] + [0] * (base_lfsr_config.degree - 1)
        
        print(f"Generating {sequence_length} bits of sequence...", file=output_file)
        print(f"Initial state: {initial_state}", file=output_file)
        
        # For clock-controlled and irregular, need control state
        if structure_type in ["clock_controlled", "irregular"]:
            control_state = [1, 0]  # Default control state
            if structure_type == "clock_controlled":
                sequence = structure.generate_sequence(initial_state, sequence_length, control_state)
            else:
                sequence = structure.generate_sequence(initial_state, sequence_length, control_state)
        else:
            sequence = structure.generate_sequence(initial_state, sequence_length)
        
        print(f"✓ Generated {len(sequence)} sequence elements", file=output_file)
        
        # Basic statistics
        if base_lfsr_config.field_order == 2:
            ones = sum(sequence)
            zeros = len(sequence) - ones
            print(f"  Ones: {ones}", file=output_file)
            print(f"  Zeros: {zeros}", file=output_file)
            print(f"  Balance: {abs(ones - zeros) / len(sequence):.4f}", file=output_file)
        
        # Show first 50 elements
        print(f"\nFirst 50 elements:", file=output_file)
        seq_str = ''.join(str(b) for b in sequence[:50])
        print(f"  {seq_str}", file=output_file)
        print(file=output_file)
    
    print("=" * 70, file=output_file)
    print("Analysis Complete", file=output_file)
    print("=" * 70, file=output_file)
