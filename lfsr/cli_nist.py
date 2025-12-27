#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI functions for NIST SP 800-22 test suite functionality.

This module provides command-line interface functions for NIST testing,
separated from the main CLI to keep the codebase organized.
"""

import sys
from typing import Optional, TextIO, List

from sage.all import *

from lfsr.nist import run_nist_test_suite


def load_sequence_from_file(sequence_file: str) -> List[int]:
    """
    Load binary sequence from file.
    
    Supports formats:
    - One bit per line
    - Space-separated bits on one or multiple lines
    
    Args:
        sequence_file: Path to sequence file
    
    Returns:
        List of binary bits (0s and 1s)
    """
    try:
        with open(sequence_file, 'r') as f:
            content = f.read().strip()
        
        # Try space-separated first
        if ' ' in content or '\t' in content:
            bits = content.split()
        else:
            # One per line
            bits = content.splitlines()
        
        # Convert to integers
        sequence = []
        for bit in bits:
            bit = bit.strip()
            if bit:
                try:
                    value = int(bit)
                    if value not in [0, 1]:
                        raise ValueError(f"Invalid bit value: {value} (must be 0 or 1)")
                    sequence.append(value)
                except ValueError as e:
                    raise ValueError(f"Invalid bit value: {bit} (must be 0 or 1): {e}")
        
        return sequence
    except FileNotFoundError:
        raise FileNotFoundError(f"Sequence file not found: {sequence_file}")


def generate_sequence_from_lfsr(
    coefficients: List[int],
    field_order: int,
    length: int
) -> List[int]:
    """
    Generate binary sequence from LFSR for NIST testing.
    
    Args:
        coefficients: LFSR feedback polynomial coefficients
        field_order: Field order (must be 2 for binary)
        length: Length of sequence to generate
    
    Returns:
        List of binary bits
    """
    if field_order != 2:
        raise ValueError("NIST tests require binary sequences (field_order=2)")
    
    from lfsr.core import build_state_update_matrix
    
    C, CS = build_state_update_matrix(coefficients, field_order)
    d = len(coefficients)
    V = VectorSpace(GF(field_order), d)
    
    # Use first state from vector space
    state = V[1]  # Skip zero state
    
    sequence = []
    for _ in range(length):
        # Output is first element of state
        output = int(state[0])
        sequence.append(output)
        
        # Update state
        state = C * state
    
    return sequence


def perform_nist_test_cli(
    sequence: Optional[List[int]] = None,
    sequence_file: Optional[str] = None,
    lfsr_coefficients: Optional[List[int]] = None,
    field_order: int = 2,
    sequence_length: int = 10000,
    output_file: Optional[TextIO] = None,
    significance_level: float = 0.01,
    block_size: int = 128,
) -> None:
    """
    Perform NIST test suite from CLI.
    
    Args:
        sequence: Optional pre-computed sequence
        sequence_file: Optional file containing sequence
        lfsr_coefficients: Optional LFSR coefficients to generate sequence
        field_order: Field order (must be 2 for binary)
        sequence_length: Length of sequence to generate (if from LFSR)
        output_file: Optional file for output
        significance_level: Statistical significance level
        block_size: Block size for block-based tests
    """
    if output_file is None:
        output_file = sys.stdout
    
    # Determine sequence source
    if sequence is not None:
        test_sequence = sequence
        source = "provided"
    elif sequence_file:
        print(f"Loading sequence from {sequence_file}...", file=output_file)
        test_sequence = load_sequence_from_file(sequence_file)
        source = f"file: {sequence_file}"
        print(f"  Loaded {len(test_sequence)} bits", file=output_file)
    elif lfsr_coefficients:
        print(f"Generating sequence from LFSR...", file=output_file)
        print(f"  Coefficients: {lfsr_coefficients}", file=output_file)
        print(f"  Field order: {field_order}", file=output_file)
        print(f"  Length: {sequence_length}", file=output_file)
        test_sequence = generate_sequence_from_lfsr(
            lfsr_coefficients, field_order, sequence_length
        )
        source = f"LFSR (generated {sequence_length} bits)"
        print(f"  Generated {len(test_sequence)} bits", file=output_file)
    else:
        raise ValueError("Must provide sequence, sequence_file, or lfsr_coefficients")
    
    print(file=output_file)
    
    # Run NIST test suite
    print("=" * 70, file=output_file)
    print("NIST SP 800-22 Statistical Test Suite Results", file=output_file)
    print("=" * 70, file=output_file)
    print(file=output_file)
    
    print(f"Sequence Information:", file=output_file)
    print(f"  Source: {source}", file=output_file)
    print(f"  Length: {len(test_sequence)} bits", file=output_file)
    print(f"  Balance: {sum(test_sequence)} ones, {len(test_sequence) - sum(test_sequence)} zeros", file=output_file)
    print(f"  Significance level: {significance_level}", file=output_file)
    print(file=output_file)
    
    suite_result = run_nist_test_suite(
        test_sequence,
        significance_level=significance_level,
        block_size=block_size
    )
    
    # Display results
    print("=" * 70, file=output_file)
    print("Test Results Summary", file=output_file)
    print("=" * 70, file=output_file)
    print(file=output_file)
    
    print(f"Tests passed: {suite_result.tests_passed}/{suite_result.total_tests}", file=output_file)
    print(f"Tests failed: {suite_result.tests_failed}", file=output_file)
    print(f"Pass rate: {suite_result.pass_rate:.2%}", file=output_file)
    print(f"Overall assessment: {suite_result.overall_assessment}", file=output_file)
    print(file=output_file)
    
    print("=" * 70, file=output_file)
    print("Individual Test Results", file=output_file)
    print("=" * 70, file=output_file)
    print(file=output_file)
    
    print(f"{'Test':<50} {'P-value':<12} {'Status':<10}", file=output_file)
    print(f"{'─'*70}", file=output_file)
    
    for test_result in suite_result.results:
        status = "✓ PASS" if test_result.passed else "✗ FAIL"
        print(f"{test_result.test_name:<50} {test_result.p_value:>10.6f}  {status:<10}", file=output_file)
    
    print(file=output_file)
    print("=" * 70, file=output_file)
    print("Interpretation", file=output_file)
    print("=" * 70, file=output_file)
    print(file=output_file)
    
    if suite_result.overall_assessment == "PASSED":
        print("✓ Sequence appears random based on NIST SP 800-22 tests.", file=output_file)
        print("  The sequence exhibits properties expected of a random sequence.", file=output_file)
    else:
        print("✗ Sequence shows evidence of non-randomness.", file=output_file)
        print("  Some tests failed, indicating the sequence may not be suitable", file=output_file)
        print("  for cryptographic applications.", file=output_file)
    
    print(file=output_file)
    print("Note: A single test failure does not necessarily mean the sequence", file=output_file)
    print("is non-random. Consider the overall pattern of results.", file=output_file)
    print(file=output_file)
    
    print("=" * 70, file=output_file)
    print("Analysis Complete", file=output_file)
    print("=" * 70, file=output_file)
