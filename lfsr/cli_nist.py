#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI functions for NIST SP 800-22 test suite functionality.

This module provides command-line interface functions for NIST tests,
separated from the main CLI to keep the codebase organized.
"""

import sys
from typing import List, Optional, TextIO

from lfsr.nist import run_nist_test_suite, NISTTestResult


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
    
    Raises:
        ValueError: If file contains invalid bits
        FileNotFoundError: If file doesn't exist
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
                    bit_val = int(bit)
                    if bit_val not in [0, 1]:
                        raise ValueError(f"Invalid bit value: {bit_val} (must be 0 or 1)")
                    sequence.append(bit_val)
                except ValueError as e:
                    if "Invalid bit value" in str(e):
                        raise
                    raise ValueError(f"Invalid bit value: {bit} (must be 0 or 1)")
        
        return sequence
    except FileNotFoundError:
        raise FileNotFoundError(f"Sequence file not found: {sequence_file}")


def perform_nist_test_cli(
    sequence: List[int],
    output_file: Optional[TextIO] = None,
    significance_level: float = 0.01,
    block_size: int = 128
) -> None:
    """
    Perform NIST SP 800-22 test suite from CLI.
    
    Args:
        sequence: Binary sequence to test
        output_file: Optional file for output
        significance_level: Statistical significance level
        block_size: Block size for block-based tests
    """
    if output_file is None:
        output_file = sys.stdout
    
    print("=" * 70, file=output_file)
    print("NIST SP 800-22 Statistical Test Suite", file=output_file)
    print("=" * 70, file=output_file)
    print(file=output_file)
    
    print(f"Sequence Information:", file=output_file)
    print(f"  Length: {len(sequence)} bits", file=output_file)
    print(f"  Ones: {sum(sequence)} ({sum(sequence)/len(sequence)*100:.2f}%)", file=output_file)
    print(f"  Zeros: {len(sequence) - sum(sequence)} ({(len(sequence) - sum(sequence))/len(sequence)*100:.2f}%)", file=output_file)
    print(f"  Significance Level: {significance_level}", file=output_file)
    print(file=output_file)
    
    # Run test suite
    print("Running NIST SP 800-22 test suite...", file=output_file)
    suite_result = run_nist_test_suite(
        sequence,
        significance_level=significance_level,
        block_size=block_size
    )
    
    print(file=output_file)
    print("=" * 70, file=output_file)
    print("Test Suite Results", file=output_file)
    print("=" * 70, file=output_file)
    print(file=output_file)
    
    print(f"Tests Passed: {suite_result.tests_passed}/{suite_result.total_tests}", file=output_file)
    print(f"Tests Failed: {suite_result.tests_failed}", file=output_file)
    print(f"Pass Rate: {suite_result.pass_rate:.2%}", file=output_file)
    print(f"Overall Assessment: {suite_result.overall_assessment}", file=output_file)
    print(file=output_file)
    
    print("=" * 70, file=output_file)
    print("Individual Test Results", file=output_file)
    print("=" * 70, file=output_file)
    print(file=output_file)
    print(f"{'Test Name':<50} {'P-value':<12} {'Status':<10}", file=output_file)
    print("-" * 70, file=output_file)
    
    for result in suite_result.results:
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"{result.test_name:<50} {result.p_value:>10.6f}  {status:<10}", file=output_file)
    
    print(file=output_file)
    print("=" * 70, file=output_file)
    print("Detailed Results", file=output_file)
    print("=" * 70, file=output_file)
    print(file=output_file)
    
    for idx, result in enumerate(suite_result.results, 1):
        print(f"Test {idx}: {result.test_name}", file=output_file)
        print(f"  P-value: {result.p_value:.6f}", file=output_file)
        print(f"  Statistic: {result.statistic:.6f}", file=output_file)
        print(f"  Passed: {result.passed}", file=output_file)
        if result.details:
            print(f"  Details:", file=output_file)
            for key, value in list(result.details.items())[:5]:  # Show first 5 details
                if key != "error":
                    print(f"    {key}: {value}", file=output_file)
        print(file=output_file)
    
    print("=" * 70, file=output_file)
    print("Interpretation", file=output_file)
    print("=" * 70, file=output_file)
    print(file=output_file)
    
    if suite_result.overall_assessment == "PASSED":
        print("✓ The sequence PASSED the NIST test suite.", file=output_file)
        print("  The sequence appears to exhibit properties expected of", file=output_file)
        print("  a random sequence. This is a positive indicator for", file=output_file)
        print("  cryptographic applications.", file=output_file)
    else:
        print("✗ The sequence FAILED the NIST test suite.", file=output_file)
        print("  The sequence shows deviations from randomness. This may", file=output_file)
        print("  indicate non-randomness or insufficient sequence length.", file=output_file)
        print("  Review individual test results for specific issues.", file=output_file)
    
    print(file=output_file)
    print("Note: A single test failure does not necessarily mean the", file=output_file)
    print("      sequence is non-random. Consider the overall pattern", file=output_file)
    print("      of results and sequence length requirements.", file=output_file)
