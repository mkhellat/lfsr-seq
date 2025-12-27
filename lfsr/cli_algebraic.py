#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI functions for algebraic attacks.

This module provides command-line interface functions for performing algebraic
attacks on LFSRs, including Gröbner basis attacks, cube attacks, and algebraic
immunity computation.
"""

import sys
from typing import List, Optional, TextIO

from lfsr.attacks import (
    LFSRConfig,
    compute_algebraic_immunity,
    groebner_basis_attack,
    cube_attack,
)
from lfsr.cli_correlation import load_keystream_from_file


def perform_algebraic_attack_cli(
    lfsr_config_file: Optional[str] = None,
    lfsr_coefficients: Optional[List[int]] = None,
    field_order: int = 2,
    keystream_file: Optional[str] = None,
    keystream: Optional[List[int]] = None,
    method: str = "groebner_basis",
    max_cube_size: int = 10,
    max_equations: int = 1000,
    filtering_function: Optional[callable] = None,
    output_file: Optional[TextIO] = None,
) -> None:
    """
    Perform algebraic attack from CLI.
    
    Args:
        lfsr_config_file: Optional JSON file with LFSR configuration
        lfsr_coefficients: Optional list of LFSR coefficients
        field_order: Field order (default: 2)
        keystream_file: Optional file containing keystream
        keystream: Optional keystream list
        method: Attack method ("groebner_basis", "cube_attack", "algebraic_immunity")
        max_cube_size: Maximum cube size for cube attack
        max_equations: Maximum equations for Gröbner basis attack
        filtering_function: Optional filtering function
        output_file: Optional file for output
    """
    if output_file is None:
        output_file = sys.stdout
    
    # Load or construct LFSR configuration
    if lfsr_config_file:
        # Load from JSON (would need to extend load function)
        print("Loading LFSR configuration from file...", file=output_file)
        # For now, require coefficients directly
        if not lfsr_coefficients:
            print("ERROR: LFSR coefficients required (config file loading not yet implemented)", file=sys.stderr)
            sys.exit(1)
    elif not lfsr_coefficients:
        print("ERROR: LFSR configuration required (coefficients or config file)", file=sys.stderr)
        sys.exit(1)
    
    lfsr_config = LFSRConfig(
        coefficients=lfsr_coefficients,
        field_order=field_order,
        degree=len(lfsr_coefficients)
    )
    
    print(f"LFSR Configuration:", file=output_file)
    print(f"  Coefficients: {lfsr_config.coefficients}", file=output_file)
    print(f"  Degree: {lfsr_config.degree}", file=output_file)
    print(f"  Field order: {lfsr_config.field_order}", file=output_file)
    print(file=output_file)
    
    # Load or use keystream
    if keystream_file:
        print(f"Loading keystream from {keystream_file}...", file=output_file)
        keystream = load_keystream_from_file(keystream_file)
        print(f"  Loaded {len(keystream)} bits", file=output_file)
    elif not keystream:
        print("ERROR: Keystream required (keystream or keystream_file)", file=sys.stderr)
        sys.exit(1)
    
    print(file=output_file)
    
    # Perform attack based on method
    print("=" * 70, file=output_file)
    print("Algebraic Attack Results", file=output_file)
    print("=" * 70, file=output_file)
    print(file=output_file)
    
    if method == "algebraic_immunity":
        # Compute algebraic immunity of filtering function
        if not filtering_function:
            print("ERROR: Filtering function required for algebraic immunity computation", file=sys.stderr)
            sys.exit(1)
        
        print("Computing algebraic immunity...", file=output_file)
        result = compute_algebraic_immunity(
            function=filtering_function,
            num_inputs=lfsr_config.degree,
            field_order=field_order
        )
        
        print(f"  Algebraic immunity: {result['algebraic_immunity']}", file=output_file)
        print(f"  Maximum possible: {result['max_possible']}", file=output_file)
        print(f"  Optimal: {result['optimal']}", file=output_file)
        if result['optimal']:
            print(f"  ✓ Function achieves maximum algebraic immunity!", file=output_file)
        else:
            print(f"  ⚠ Function does not achieve maximum algebraic immunity", file=output_file)
            print(f"    (Vulnerable to algebraic attacks of degree {result['algebraic_immunity']})", file=output_file)
    
    elif method == "groebner_basis":
        print("Performing Gröbner basis attack...", file=output_file)
        result = groebner_basis_attack(
            lfsr_config=lfsr_config,
            keystream=keystream,
            filtering_function=filtering_function,
            max_equations=max_equations
        )
        
        print(f"  Method: Gröbner Basis Attack", file=output_file)
        print(f"  Attack successful: {result.attack_successful}", file=output_file)
        if result.attack_successful:
            print(f"  ✓ Recovered state: {result.recovered_state}", file=output_file)
        else:
            print(f"  ✗ Attack failed", file=output_file)
        print(f"  Equations solved: {result.equations_solved}", file=output_file)
        print(f"  Complexity estimate: {result.complexity_estimate:.0f} operations", file=output_file)
        print(f"  Algebraic immunity: {result.algebraic_immunity}", file=output_file)
        if result.details:
            print(f"  Details: {result.details}", file=output_file)
    
    elif method == "cube_attack":
        print("Performing cube attack...", file=output_file)
        result = cube_attack(
            lfsr_config=lfsr_config,
            keystream=keystream,
            filtering_function=filtering_function,
            max_cube_size=max_cube_size
        )
        
        print(f"  Method: Cube Attack", file=output_file)
        print(f"  Attack successful: {result.attack_successful}", file=output_file)
        if result.attack_successful:
            print(f"  ✓ Attack succeeded!", file=output_file)
            print(f"  Recovered bits: {result.recovered_bits}", file=output_file)
        else:
            print(f"  ✗ Attack failed", file=output_file)
        print(f"  Cubes found: {result.cubes_found}", file=output_file)
        print(f"  Superpolies computed: {result.superpolies_computed}", file=output_file)
        print(f"  Complexity estimate: {result.complexity_estimate:.0f} operations", file=output_file)
        if result.details:
            print(f"  Details: {result.details}", file=output_file)
    
    else:
        print(f"ERROR: Unknown method: {method}", file=sys.stderr)
        sys.exit(1)
    
    print(file=output_file)
    print("=" * 70, file=output_file)
    print("Analysis Complete", file=output_file)
    print("=" * 70, file=output_file)
