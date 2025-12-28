#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example: Advanced LFSR Structures

This example demonstrates how to analyze advanced LFSR structures, including
NFSRs, filtered LFSRs, clock-controlled LFSRs, multi-output LFSRs, and
irregular clocking patterns.

**IMPORTANT TERMINOLOGY**:
- LFSR = Linear Feedback Shift Register (feedback is ALWAYS linear/XOR only)
- NFSR = Non-Linear Feedback Shift Register (feedback is non-linear, NOT an LFSR)
- Filtered/Clock-Controlled/Multi-Output LFSRs = ARE LFSRs (linear feedback)

Example Usage:
    python3 examples/advanced_lfsr_example.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import SageMath
try:
    from sage.all import *
except ImportError:
    print("ERROR: SageMath is required for this example", file=sys.stderr)
    sys.exit(1)

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
    create_step_1_step_2_pattern
)


def example_nfsr():
    """Example of NFSR (Non-Linear Feedback Shift Register)."""
    print("=" * 70)
    print("Example 1: NFSR (Non-Linear Feedback Shift Register)")
    print("=" * 70)
    print("\n⚠️  IMPORTANT: NFSR is NOT an LFSR (non-linear feedback)\n")
    
    base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
    
    # Create NFSR with non-linear feedback
    nfsr = create_simple_nfsr(base_lfsr, nonlinear_terms=[(1, 2)])
    
    config = nfsr.get_config()
    print(f"Structure Type: {config.structure_type}")
    print(f"Note: NFSR uses non-linear feedback (NOT an LFSR)")
    
    # Analyze structure
    properties = nfsr.analyze_structure()
    print(f"\nStructure Properties:")
    for key, value in properties.items():
        print(f"  {key}: {value}")
    
    # Generate sequence
    initial_state = [1, 0, 0, 0]
    sequence = nfsr.generate_sequence(initial_state, 50)
    print(f"\nGenerated {len(sequence)} sequence elements")
    print(f"First 20: {''.join(str(b) for b in sequence[:20])}")


def example_filtered_lfsr():
    """Example of Filtered LFSR."""
    print("\n" + "=" * 70)
    print("Example 2: Filtered LFSR")
    print("=" * 70)
    print("\n✓ NOTE: Filtered LFSR IS an LFSR (linear feedback + non-linear filter)\n")
    
    base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
    
    # Create filtered LFSR
    filtered = create_simple_filtered_lfsr(
        base_lfsr,
        filter_taps=[0, 1, 2],
        nonlinear_terms=[(2, 3)]
    )
    
    config = filtered.get_config()
    print(f"Structure Type: {config.structure_type}")
    print(f"Note: Filtered LFSR has linear feedback + non-linear filter function")
    
    # Analyze structure
    properties = filtered.analyze_structure()
    print(f"\nStructure Properties:")
    for key, value in properties.items():
        print(f"  {key}: {value}")
    
    # Generate sequence
    initial_state = [1, 0, 0, 0]
    sequence = filtered.generate_sequence(initial_state, 50)
    print(f"\nGenerated {len(sequence)} sequence elements")
    print(f"First 20: {''.join(str(b) for b in sequence[:20])}")


def example_clock_controlled_lfsr():
    """Example of Clock-Controlled LFSR."""
    print("\n" + "=" * 70)
    print("Example 3: Clock-Controlled LFSR")
    print("=" * 70)
    print("\n✓ NOTE: Clock-Controlled LFSR IS an LFSR (linear feedback + irregular clocking)\n")
    
    main_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
    control_lfsr = LFSRConfig(coefficients=[1, 1], field_order=2, degree=2)
    
    # Create stop-and-go clock-controlled LFSR
    cclfsr = create_stop_and_go_lfsr(main_lfsr, control_lfsr)
    
    config = cclfsr.get_config()
    print(f"Structure Type: {config.structure_type}")
    print(f"Note: Clock-Controlled LFSR has linear feedback + irregular clocking")
    
    # Analyze structure
    properties = cclfsr.analyze_structure()
    print(f"\nStructure Properties:")
    for key, value in properties.items():
        print(f"  {key}: {value}")
    
    # Generate sequence
    main_state = [1, 0, 0, 0]
    control_state = [1, 0]
    sequence = cclfsr.generate_sequence(main_state, 50, control_state)
    print(f"\nGenerated {len(sequence)} sequence elements")
    print(f"First 20: {''.join(str(b) for b in sequence[:20])}")


def example_multi_output_lfsr():
    """Example of Multi-Output LFSR."""
    print("\n" + "=" * 70)
    print("Example 4: Multi-Output LFSR")
    print("=" * 70)
    print("\n✓ NOTE: Multi-Output LFSR IS an LFSR (linear feedback + multiple outputs)\n")
    
    base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
    
    # Create multi-output LFSR (outputs 2 bits per step)
    molfsr = create_simple_multi_output_lfsr(base_lfsr, [0, 1])
    
    config = molfsr.get_config()
    print(f"Structure Type: {config.structure_type}")
    print(f"Output Rate: {config.parameters['output_rate']} bits per step")
    print(f"Note: Multi-Output LFSR has linear feedback + multiple outputs")
    
    # Analyze structure
    properties = molfsr.analyze_structure()
    print(f"\nStructure Properties:")
    for key, value in properties.items():
        print(f"  {key}: {value}")
    
    # Generate sequence
    initial_state = [1, 0, 0, 0]
    sequence = molfsr.generate_sequence(initial_state, 50)
    print(f"\nGenerated {len(sequence)} sequence elements")
    print(f"First 20: {''.join(str(b) for b in sequence[:20])}")


def example_irregular_clocking():
    """Example of Irregular Clocking LFSR."""
    print("\n" + "=" * 70)
    print("Example 5: Irregular Clocking LFSR")
    print("=" * 70)
    print("\n✓ NOTE: Irregular Clocking LFSR IS an LFSR (linear feedback + irregular pattern)\n")
    
    base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
    control_lfsr = LFSRConfig(coefficients=[1, 1], field_order=2, degree=2)
    
    # Create irregular clocking LFSR with step-1/step-2 pattern
    pattern_func = create_step_1_step_2_pattern()
    iclfsr = IrregularClockingLFSR(base_lfsr, control_lfsr, pattern_func)
    
    config = iclfsr.get_config()
    print(f"Structure Type: {config.structure_type}")
    print(f"Note: Irregular Clocking LFSR has linear feedback + irregular clocking pattern")
    
    # Analyze structure
    properties = iclfsr.analyze_structure()
    print(f"\nStructure Properties:")
    for key, value in properties.items():
        print(f"  {key}: {value}")
    
    # Generate sequence
    base_state = [1, 0, 0, 0]
    control_state = [1, 0]
    sequence = iclfsr.generate_sequence(base_state, 50, control_state)
    print(f"\nGenerated {len(sequence)} sequence elements")
    print(f"First 20: {''.join(str(b) for b in sequence[:20])}")


def example_comprehensive_analysis():
    """Example of comprehensive analysis."""
    print("\n" + "=" * 70)
    print("Example 6: Comprehensive Analysis")
    print("=" * 70)
    
    base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
    initial_state = [1, 0, 0, 0]
    
    # Analyze filtered LFSR
    filtered = create_simple_filtered_lfsr(base_lfsr, [0, 1], [(2, 3)])
    result = filtered.analyze(initial_state=initial_state, sequence_length=1000)
    
    print(f"\nComprehensive Analysis Results:")
    print(f"  Structure Type: {result.structure_type}")
    print(f"  Structure Properties: {result.structure_properties}")
    print(f"  Sequence Properties: {result.sequence_properties}")
    print(f"  Security Assessment: {result.security_assessment}")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("Advanced LFSR Structures Examples")
    print("=" * 70)
    print("\nThis script demonstrates advanced LFSR structure analysis capabilities.")
    print("\n⚠️  CRITICAL TERMINOLOGY:")
    print("  - LFSR = Linear Feedback Shift Register (feedback is ALWAYS linear)")
    print("  - NFSR = Non-Linear Feedback Shift Register (NOT an LFSR)")
    print("  - Filtered/Clock-Controlled/Multi-Output = ARE LFSRs (linear feedback)\n")
    
    try:
        example_nfsr()
        example_filtered_lfsr()
        example_clock_controlled_lfsr()
        example_multi_output_lfsr()
        example_irregular_clocking()
        example_comprehensive_analysis()
        
        print("\n" + "=" * 70)
        print("Examples Complete!")
        print("=" * 70)
        print("\nFor more information, see:")
        print("  - Advanced LFSR Structures Guide: docs/advanced_lfsr_structures.rst")
        print("  - API Documentation: docs/api/advanced.rst")
        print("  - Mathematical Background: docs/mathematical_background.rst")
        
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
