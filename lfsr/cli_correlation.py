#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI functions for correlation attack functionality.

This module provides command-line interface functions for correlation
attacks, separated from the main CLI to keep the codebase organized.
"""

import json
import sys
from typing import List, Optional, TextIO

from lfsr.sage_imports import *

from lfsr.attacks import (
    CombinationGenerator,
    LFSRConfig,
    siegenthaler_correlation_attack,
    fast_correlation_attack,
    distinguishing_attack,
    analyze_combining_function,
)


def load_combination_generator_from_json(config_file: str) -> CombinationGenerator:
    """
    Load combination generator configuration from JSON file.
    
    Expected JSON format::
    
        {
            "lfsrs": [
                {
                    "coefficients": [1, 0, 0, 1],
                    "field_order": 2,
                    "degree": 4,
                    "initial_state": [1, 0, 0, 0]  // optional
                },
                ...
            ],
            "combining_function": {
                "type": "majority",  // or "xor", "and", "or", "custom"
                "num_inputs": 3,
                "code": "def f(a, b, c): return 1 if (a + b + c) >= 2 else 0"  // for custom
            }
        }
    
    Args:
        config_file: Path to JSON configuration file
    
    Returns:
        CombinationGenerator instance
    
    Raises:
        ValueError: If configuration is invalid
        FileNotFoundError: If config file doesn't exist
    """
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    # Validate structure
    if 'lfsrs' not in config:
        raise ValueError("Configuration must contain 'lfsrs' key")
    if 'combining_function' not in config:
        raise ValueError("Configuration must contain 'combining_function' key")
    
    # Load LFSR configurations
    lfsr_configs = []
    for idx, lfsr_data in enumerate(config['lfsrs']):
        if 'coefficients' not in lfsr_data:
            raise ValueError(f"LFSR {idx}: missing 'coefficients'")
        if 'field_order' not in lfsr_data:
            raise ValueError(f"LFSR {idx}: missing 'field_order'")
        if 'degree' not in lfsr_data:
            raise ValueError(f"LFSR {idx}: missing 'degree'")
        
        lfsr_config = LFSRConfig(
            coefficients=lfsr_data['coefficients'],
            field_order=lfsr_data['field_order'],
            degree=lfsr_data['degree'],
            initial_state=lfsr_data.get('initial_state')
        )
        lfsr_configs.append(lfsr_config)
    
    # Load combining function
    func_config = config['combining_function']
    func_type = func_config.get('type', 'custom')
    num_inputs = func_config.get('num_inputs', len(lfsr_configs))
    
    if func_type == 'majority':
        def majority(*args):
            return 1 if sum(args) >= (len(args) + 1) // 2 else 0
        combining_function = majority
        function_name = 'majority'
    elif func_type == 'xor':
        def xor_combiner(*args):
            result = args[0]
            for arg in args[1:]:
                result ^= arg
            return result
        combining_function = xor_combiner
        function_name = 'xor'
    elif func_type == 'and':
        def and_combiner(*args):
            result = args[0]
            for arg in args[1:]:
                result &= arg
            return result
        combining_function = and_combiner
        function_name = 'and'
    elif func_type == 'or':
        def or_combiner(*args):
            result = args[0]
            for arg in args[1:]:
                result |= arg
            return result
        combining_function = or_combiner
        function_name = 'or'
    elif func_type == 'custom':
        # Execute custom function code
        if 'code' not in func_config:
            raise ValueError("Custom function requires 'code' field")
        namespace = {}
        exec(func_config['code'], namespace)
        # Find the function (should be named 'f' or similar)
        if 'f' in namespace:
            combining_function = namespace['f']
        else:
            # Try to find any callable
            combining_function = next(v for v in namespace.values() if callable(v))
        function_name = 'custom'
    else:
        raise ValueError(f"Unknown function type: {func_type}")
    
    return CombinationGenerator(
        lfsrs=lfsr_configs,
        combining_function=combining_function,
        function_name=function_name
    )


def load_keystream_from_file(keystream_file: str) -> List[int]:
    """
    Load keystream bits from file.
    
    Supports formats:
    - One bit per line
    - Space-separated bits on one or multiple lines
    
    Args:
        keystream_file: Path to keystream file
    
    Returns:
        List of keystream bits
    """
    try:
        with open(keystream_file, 'r') as f:
            content = f.read().strip()
        
        # Try space-separated first
        if ' ' in content or '\t' in content:
            bits = content.split()
        else:
            # One per line
            bits = content.splitlines()
        
        # Convert to integers
        keystream = []
        for bit in bits:
            bit = bit.strip()
            if bit:
                try:
                    keystream.append(int(bit))
                except ValueError:
                    raise ValueError(f"Invalid bit value: {bit} (must be 0 or 1)")
        
        return keystream
    except FileNotFoundError:
        raise FileNotFoundError(f"Keystream file not found: {keystream_file}")


def perform_correlation_attack_cli(
    config_file: str,
    output_file: Optional[TextIO] = None,
    keystream_file: Optional[str] = None,
    keystream_length: int = 1000,
    target_lfsr_index: int = 0,
    significance_level: float = 0.05,
    analyze_all_lfsrs: bool = False,
    analyze_function: bool = False,
    fast_correlation_attack: bool = False,
    max_candidates: int = 1000,
    distinguishing_attack: bool = False,
    distinguishing_method: str = "correlation",
) -> None:
    """
    Perform correlation attack from CLI.
    
    Args:
        config_file: Path to combination generator JSON config
        output_file: Optional file for output
        keystream_file: Optional file containing keystream (if not provided, generates it)
        keystream_length: Length of keystream to generate (if not from file)
        target_lfsr_index: Index of LFSR to attack
        significance_level: Statistical significance level
        analyze_all_lfsrs: If True, attack all LFSRs
        analyze_function: If True, also analyze combining function
          properties
    """
    if output_file is None:
        output_file = sys.stdout
    
    # Load combination generator
    print("Loading combination generator configuration...", file=output_file)
    gen = load_combination_generator_from_json(config_file)
    print(f"  Loaded {len(gen.lfsrs)} LFSRs", file=output_file)
    print(f"  Combining function: {gen.function_name}", file=output_file)
    print(file=output_file)
    
    # Analyze combining function if requested
    if analyze_function:
        print("=" * 70, file=output_file)
        print("Combining Function Analysis", file=output_file)
        print("=" * 70, file=output_file)
        analysis = analyze_combining_function(
            gen.combining_function,
            num_inputs=len(gen.lfsrs),
            field_order=gen.lfsrs[0].field_order
        )
        print(f"  Balanced: {analysis['balanced']}", file=output_file)
        print(f"  Bias: {analysis['bias']:.6f}", file=output_file)
        print(f"  Correlation immunity order: {analysis['correlation_immunity']}", file=output_file)
        print(f"  Output distribution: {analysis['output_distribution']}", file=output_file)
        print(file=output_file)
    
    # Load or generate keystream
    if keystream_file:
        print(f"Loading keystream from {keystream_file}...", file=output_file)
        keystream = load_keystream_from_file(keystream_file)
        print(f"  Loaded {len(keystream)} bits", file=output_file)
    else:
        print(f"Generating keystream (length: {keystream_length})...", file=output_file)
        keystream = gen.generate_keystream(length=keystream_length)
        print(f"  Generated {len(keystream)} bits", file=output_file)
    print(file=output_file)
    
    # Perform distinguishing attack if requested
    if distinguishing_attack:
        print("=" * 70, file=output_file)
        print("Distinguishing Attack Results", file=output_file)
        print("=" * 70, file=output_file)
        print(file=output_file)
        
        dist_result = distinguishing_attack(
            combination_generator=gen,
            keystream=keystream,
            method=distinguishing_method,
            significance_level=significance_level
        )
        
        print(f"  Method: {dist_result.method_used}", file=output_file)
        print(f"  Distinguishable: {dist_result.distinguishable}", file=output_file)
        print(f"  Distinguishing statistic: {dist_result.distinguishing_statistic:.6f}", file=output_file)
        print(f"  P-value: {dist_result.p_value:.6f}", file=output_file)
        print(f"  Attack successful: {dist_result.attack_successful}", file=output_file)
        if dist_result.attack_successful:
            print(f"  ⚠ VULNERABLE: Keystream is distinguishable from random!", file=output_file)
        print(file=output_file)
    
    # Perform correlation attacks
    print("=" * 70, file=output_file)
    if fast_correlation_attack:
        print("Fast Correlation Attack Results (Meier-Staffelbach)", file=output_file)
    else:
        print("Correlation Attack Results (Siegenthaler)", file=output_file)
    print("=" * 70, file=output_file)
    print(file=output_file)
    
    if analyze_all_lfsrs:
        lfsr_indices = range(len(gen.lfsrs))
    else:
        lfsr_indices = [target_lfsr_index]
    
    for lfsr_idx in lfsr_indices:
        print(f"Attacking LFSR {lfsr_idx + 1} (index {lfsr_idx}):", file=output_file)
        print(f"  Coefficients: {gen.lfsrs[lfsr_idx].coefficients}", file=output_file)
        print(f"  Degree: {gen.lfsrs[lfsr_idx].degree}", file=output_file)
        print(f"  Field order: {gen.lfsrs[lfsr_idx].field_order}", file=output_file)
        print(file=output_file)
        
        if fast_correlation_attack:
            # Fast correlation attack
            result = fast_correlation_attack(
                combination_generator=gen,
                keystream=keystream,
                target_lfsr_index=lfsr_idx,
                max_candidates=max_candidates,
                significance_level=significance_level
            )
            
            print(f"  Attack method: Fast Correlation Attack (Meier-Staffelbach)", file=output_file)
            print(f"  Correlation coefficient: {result.correlation_coefficient:.6f}", file=output_file)
            print(f"  Attack successful: {result.attack_successful}", file=output_file)
            if result.attack_successful:
                print(f"  ✓ Recovered state: {result.recovered_state}", file=output_file)
                print(f"  ⚠ VULNERABLE: State recovery successful!", file=output_file)
            else:
                print(f"  ✗ State recovery failed", file=output_file)
            print(f"  Best correlation: {result.best_correlation:.6f}", file=output_file)
            print(f"  Iterations performed: {result.iterations_performed}", file=output_file)
            print(f"  Candidates tested: {result.candidate_states_tested}", file=output_file)
            print(f"  Complexity estimate: {result.complexity_estimate:.0f} operations", file=output_file)
            print(f"  Keystream length used: {result.keystream_length}", file=output_file)
        else:
            # Basic Siegenthaler attack
            result = siegenthaler_correlation_attack(
                combination_generator=gen,
                keystream=keystream,
                target_lfsr_index=lfsr_idx,
                significance_level=significance_level
            )
            
            print(f"  Attack method: Basic Correlation Attack (Siegenthaler)", file=output_file)
            print(f"  Correlation coefficient: {result.correlation_coefficient:.6f}", file=output_file)
            print(f"  P-value: {result.p_value:.6f}", file=output_file)
            print(f"  Match ratio: {result.match_ratio:.4f} ({result.matches}/{result.total_bits})", file=output_file)
            print(f"  Attack successful: {result.attack_successful}", file=output_file)
            print(f"  Success probability: {result.success_probability:.2%}", file=output_file)
            if result.attack_successful:
                print(f"  ⚠ VULNERABLE: Significant correlation detected!", file=output_file)
            print(f"  Required keystream bits: {result.required_keystream_bits}", file=output_file)
            print(f"  Complexity estimate: {result.complexity_estimate:.0f} operations", file=output_file)
        print(file=output_file)
    
    print("=" * 70, file=output_file)
    print("Analysis Complete", file=output_file)
    print("=" * 70, file=output_file)
