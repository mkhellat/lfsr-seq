#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI functions for time-memory trade-off attacks.

This module provides command-line interface functions for performing TMTO
attacks on LFSRs, including Hellman tables and Rainbow tables.
"""

import json
import sys
import time
from typing import List, Optional, TextIO

from lfsr.attacks import LFSRConfig
from lfsr.tmto import (
    HellmanTable,
    RainbowTable,
    tmto_attack,
    optimize_tmto_parameters,
    TMTOAttackResult
)


def perform_tmto_attack_cli(
    lfsr_coefficients: List[int],
    field_order: int,
    target_state: Optional[List[int]] = None,
    method: str = "hellman",
    chain_count: int = 1000,
    chain_length: int = 100,
    table_file: Optional[str] = None,
    output_file: Optional[TextIO] = None,
) -> None:
    """
    Perform TMTO attack from CLI.
    
    Args:
        lfsr_coefficients: List of LFSR coefficients
        field_order: Field order
        target_state: Target state to recover (if None, uses first state from LFSR)
        method: TMTO method ("hellman" or "rainbow")
        chain_count: Number of chains
        chain_length: Length of each chain
        table_file: Optional file with precomputed table
        output_file: Optional file for output
    """
    if output_file is None:
        output_file = sys.stdout
    
    lfsr_config = LFSRConfig(
        coefficients=lfsr_coefficients,
        field_order=field_order,
        degree=len(lfsr_coefficients)
    )
    
    print("=" * 70, file=output_file)
    print("Time-Memory Trade-Off Attack", file=output_file)
    print("=" * 70, file=output_file)
    print(file=output_file)
    
    print(f"LFSR Configuration:", file=output_file)
    print(f"  Coefficients: {lfsr_config.coefficients}", file=output_file)
    print(f"  Degree: {lfsr_config.degree}", file=output_file)
    print(f"  Field order: {lfsr_config.field_order}", file=output_file)
    print(f"  State space size: {lfsr_config.field_order ** lfsr_config.degree}", file=output_file)
    print(file=output_file)
    
    # Optimize parameters if needed
    state_space_size = lfsr_config.field_order ** lfsr_config.degree
    available_memory = chain_count * chain_length
    
    print(f"TMTO Parameters:", file=output_file)
    print(f"  Method: {method}", file=output_file)
    print(f"  Chain count: {chain_count}", file=output_file)
    print(f"  Chain length: {chain_length}", file=output_file)
    print(f"  Table size: {chain_count * chain_length} states", file=output_file)
    print(f"  Available memory: {available_memory} states", file=output_file)
    print(file=output_file)
    
    # Optimize parameters
    print("Optimizing parameters...", file=output_file)
    optimal_params = optimize_tmto_parameters(
        state_space_size=state_space_size,
        available_memory=available_memory
    )
    print(f"  Optimal chain count: {optimal_params['chain_count']}", file=output_file)
    print(f"  Optimal chain length: {optimal_params['chain_length']}", file=output_file)
    print(f"  Estimated coverage: {optimal_params['estimated_coverage']:.2%}", file=output_file)
    print(f"  Estimated success probability: {optimal_params['estimated_success_prob']:.2%}", file=output_file)
    print(file=output_file)
    
    # Load or generate target state
    if target_state is None:
        # Use a default target state (in practice, this would come from keystream)
        target_state = [1, 0, 0, 0] if len(lfsr_coefficients) >= 4 else [1] * len(lfsr_coefficients)
        print(f"Using default target state: {target_state}", file=output_file)
        print(f"  (In practice, target state would come from observed keystream)", file=output_file)
    else:
        print(f"Target state: {target_state}", file=output_file)
    print(file=output_file)
    
    # Load precomputed table or generate new
    precomputed_table = None
    if table_file:
        print(f"Loading precomputed table from {table_file}...", file=output_file)
        try:
            with open(table_file, 'r') as f:
                table_data = json.load(f)
            # Reconstruct table from data
            if method == "hellman":
                precomputed_table = HellmanTable(
                    chain_count=table_data['chain_count'],
                    chain_length=table_data['chain_length']
                )
                precomputed_table.chains = [tuple(chain) for chain in table_data['chains']]
            elif method == "rainbow":
                precomputed_table = RainbowTable(
                    chain_count=table_data['chain_count'],
                    chain_length=table_data['chain_length']
                )
                precomputed_table.chains = [tuple(chain) for chain in table_data['chains']]
            print(f"  Loaded {len(precomputed_table.chains)} chains", file=output_file)
        except (IOError, json.JSONDecodeError, KeyError) as e:
            print(f"  ERROR: Failed to load table: {e}", file=sys.stderr)
            print(f"  Generating new table instead...", file=output_file)
    
    # Perform attack
    print("Performing TMTO attack...", file=output_file)
    start_time = time.perf_counter()
    
    result = tmto_attack(
        lfsr_config=lfsr_config,
        target_state=target_state,
        method=method,
        chain_count=chain_count,
        chain_length=chain_length,
        precomputed_table=precomputed_table
    )
    
    total_time = time.perf_counter() - start_time
    
    print(file=output_file)
    print("=" * 70, file=output_file)
    print("TMTO Attack Results", file=output_file)
    print("=" * 70, file=output_file)
    print(file=output_file)
    
    print(f"  Method: {result.method_used}", file=output_file)
    print(f"  Attack successful: {result.attack_successful}", file=output_file)
    if result.attack_successful:
        print(f"  ✓ Recovered initial state: {result.recovered_state}", file=output_file)
    else:
        print(f"  ✗ State recovery failed", file=output_file)
        print(f"    (Target state may not be in table coverage)", file=output_file)
    
    print(f"  Table size: {result.table_size} chains", file=output_file)
    print(f"  Coverage: {result.coverage:.2%}", file=output_file)
    print(f"  Precomputation time: {result.precomputation_time:.2f} seconds", file=output_file)
    print(f"  Lookup time: {result.lookup_time:.4f} seconds", file=output_file)
    print(f"  Total time: {total_time:.2f} seconds", file=output_file)
    
    if result.details:
        print(f"  Details: {result.details}", file=output_file)
    
    print(file=output_file)
    print("=" * 70, file=output_file)
    print("Analysis Complete", file=output_file)
    print("=" * 70, file=output_file)
