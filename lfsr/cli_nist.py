#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI functions for NIST SP 800-22 test suite functionality.

This module provides command-line interface functions for NIST statistical tests,
separated from the main CLI to keep the codebase organized.
"""

import sys
from typing import Optional, TextIO

from lfsr.nist import (
    run_nist_test_suite,
    frequency_test,
    block_frequency_test,
    runs_test,
    longest_run_of_ones_test,
    binary_matrix_rank_test,
)


def load_sequence_from_file(sequence_file: str) -> list:
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
        FileNotFoundError: If file doesn't exist
        ValueError: If file contains invalid bits
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
                    if "Invalid bit value" in str(e):
                        raise
                    raise ValueError(f"Invalid bit value: {bit} (must be 0 or 1)")
        
        return sequence
    except FileNotFoundError:
        raise FileNotFoundError(f"Sequence file not found: {sequence_file}")


def perform_nist_test_suite_cli(
    sequence_file: str,
    output_file: Optional[TextIO] = None,
    significance_level: float = 0.01,
    block_size: int = 128,
    matrix_rows: int = 32,
    matrix_cols: int = 32,
    show_individual: bool = True,
) -> None:
    """
    Perform NIST SP 800-22 test suite from CLI.
    
    Args:
        sequence_file: Path to file containing binary sequence
        output_file: Optional file for output
        significance_level: Statistical significance level (default: 0.01)
        block_size: Block size for block-based tests (default: 128)
        matrix_rows: Number of rows for matrix rank test (default: 32)
        matrix_cols: Number of columns for matrix rank test (default: 32)
        show_individual: If True, show individual test results
    """
    if output_file is None:
        output_file = sys.stdout
    
    # Load sequence
    print("Loading binary sequence...", file=output_file)
    try:
        sequence = load_sequence_from_file(sequence_file)
        print(f"  Loaded {len(sequence)} bits", file=output_file)
    except Exception as e:
        print(f"ERROR: Failed to load sequence: {e}", file=output_file)
        return
    
    # Validate sequence
    if len(sequence) < 1000:
        print(f"WARNING: Sequence is short ({len(sequence)} bits).", file=output_file)
        print(f"  Minimum recommended: 1000 bits for reliable results.", file=output_file)
        print(file=output_file)
    
    # Check balance
    ones = sum(sequence)
    zeros = len(sequence) - ones
    print(f"  Balance: {ones} ones, {zeros} zeros", file=output_file)
    print(file=output_file)
    
    # Run test suite
    print("=" * 70, file=output_file)
    print("NIST SP 800-22 Statistical Test Suite Results", file=output_file)
    print("=" * 70, file=output_file)
    print(file=output_file)
    
    suite_result = run_nist_test_suite(
        sequence,
        significance_level=significance_level,
        block_size=block_size,
        matrix_rows=matrix_rows,
        matrix_cols=matrix_cols
    )
    
    # Summary
    print("Summary:", file=output_file)
    print(f"  Sequence Length: {suite_result.sequence_length} bits", file=output_file)
    print(f"  Significance Level: {suite_result.significance_level}", file=output_file)
    print(f"  Tests Run: {suite_result.total_tests}", file=output_file)
    print(f"  Tests Passed: {suite_result.tests_passed}", file=output_file)
    print(f"  Tests Failed: {suite_result.tests_failed}", file=output_file)
    print(f"  Pass Rate: {suite_result.pass_rate:.1%}", file=output_file)
    print(f"  Overall Assessment: {suite_result.overall_assessment}", file=output_file)
    print(file=output_file)
    
    if show_individual:
        print("=" * 70, file=output_file)
        print("Individual Test Results:", file=output_file)
        print("=" * 70, file=output_file)
        print(file=output_file)
        print(f"{'Test Name':<50} {'P-value':<12} {'Status':<10}", file=output_file)
        print(f"{'─'*70}", file=output_file)
        
        for result in suite_result.results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            print(f"{result.test_name:<50} {result.p_value:>10.6f}  {status:<10}", file=output_file)
        
        print(file=output_file)
        
        # Detailed results for failed tests
        failed_tests = [r for r in suite_result.results if not r.passed]
        if failed_tests:
            print("=" * 70, file=output_file)
            print("Failed Test Details:", file=output_file)
            print("=" * 70, file=output_file)
            print(file=output_file)
            
            for result in failed_tests:
                print(f"Test: {result.test_name}", file=output_file)
                print(f"  P-value: {result.p_value:.6f} (threshold: {significance_level})", file=output_file)
                print(f"  Statistic: {result.statistic:.6f}", file=output_file)
                if result.details:
                    print(f"  Details:", file=output_file)
                    for key, value in list(result.details.items())[:5]:  # First 5 details
                        if key != 'error':
                            print(f"    {key}: {value}", file=output_file)
                print(file=output_file)
    
    # Interpretation
    print("=" * 70, file=output_file)
    print("Interpretation:", file=output_file)
    print("=" * 70, file=output_file)
    print(file=output_file)
    
    if suite_result.overall_assessment == "PASSED":
        print("✓ The sequence PASSED the NIST test suite.", file=output_file)
        print("  The sequence appears to be RANDOM.", file=output_file)
        print("  This is good for cryptographic applications.", file=output_file)
    else:
        print("✗ The sequence FAILED the NIST test suite.", file=output_file)
        print("  The sequence appears to be NON-RANDOM.", file=output_file)
        print("  This may indicate issues with the random number generator.", file=output_file)
        print("  Note: A single test failure does not necessarily mean the", file=output_file)
        print("  sequence is non-random. Consider the overall pattern.", file=output_file)
    
    print(file=output_file)
    print("=" * 70, file=output_file)
    print("Analysis Complete", file=output_file)
    print("=" * 70, file=output_file)
