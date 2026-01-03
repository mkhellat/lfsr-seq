#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI functions for stream cipher analysis.

This module provides command-line interface functions for analyzing stream
ciphers, generating keystreams, and comparing different cipher designs.
"""

import sys
from typing import List, Optional, TextIO

from lfsr.ciphers import (
    A5_1, A5_2, E0, Trivium, Grain128, Grain128a, LILI128
)
from lfsr.ciphers.comparison import compare_ciphers, generate_comparison_report


def get_cipher_instance(cipher_name: str):
    """
    Get cipher instance from name.
    
    Args:
        cipher_name: Cipher name (a5_1, a5_2, e0, trivium, grain128,
          grain128a, lili128)
    
    Returns:
        StreamCipher instance
    """
    cipher_map = {
        "a5_1": A5_1,
        "a5_2": A5_2,
        "e0": E0,
        "trivium": Trivium,
        "grain128": Grain128,
        "grain128a": Grain128a,
        "lili128": LILI128
    }
    
    if cipher_name not in cipher_map:
        raise ValueError(f"Unknown cipher: {cipher_name}")
    
    return cipher_map[cipher_name]()


def load_bits_from_file(file_path: str) -> List[int]:
    """
    Load bits from file.
    
    Supports both binary files and text files with 0/1 characters.
    
    Args:
        file_path: Path to file
    
    Returns:
        List of bits (0 or 1)
    """
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
            # Try to interpret as binary
            bits = []
            for byte in data:
                for i in range(8):
                    bits.append((byte >> (7 - i)) & 1)
            return bits
    except Exception:
        # Try as text file
        with open(file_path, 'r') as f:
            content = f.read().strip()
            bits = []
            for char in content:
                if char == '0':
                    bits.append(0)
                elif char == '1':
                    bits.append(1)
            return bits


def perform_cipher_analysis_cli(
    cipher_name: str,
    analyze_structure: bool = False,
    generate_keystream: bool = False,
    keystream_length: int = 1000,
    key_file: Optional[str] = None,
    iv_file: Optional[str] = None,
    compare: bool = False,
    output_file: Optional[TextIO] = None
) -> None:
    """
    Perform stream cipher analysis from CLI.
    
    Args:
        cipher_name: Name of cipher to analyze
        analyze_structure: Whether to analyze cipher structure
        generate_keystream: Whether to generate keystream
        keystream_length: Length of keystream to generate
        key_file: Optional file with key bits
        iv_file: Optional file with IV bits
        compare: Whether to compare multiple ciphers
        output_file: Optional file for output
    """
    if output_file is None:
        output_file = sys.stdout
    
    print("=" * 70, file=output_file)
    print("Stream Cipher Analysis", file=output_file)
    print("=" * 70, file=output_file)
    print(file=output_file)
    
    if compare:
        # Compare multiple ciphers
        print("Comparing Multiple Ciphers", file=output_file)
        print("-" * 70, file=output_file)
        print(file=output_file)
        
        # Get list of ciphers to compare
        cipher_names = ["a5_1", "e0", "trivium"]  # Default comparison
        if cipher_name:
            cipher_names = [cipher_name] + [c for c in ["a5_1", "e0", "trivium"] if c != cipher_name]
        
        ciphers = [get_cipher_instance(name) for name in cipher_names]
        comparison = compare_ciphers(ciphers)
        report = generate_comparison_report(comparison)
        print(report, file=output_file)
        return
    
    # Get cipher instance
    cipher = get_cipher_instance(cipher_name)
    config = cipher.get_config()
    
    print(f"Cipher: {config.cipher_name}", file=output_file)
    print(f"Description: {config.description}", file=output_file)
    print(f"Key size: {config.key_size} bits", file=output_file)
    print(f"IV size: {config.iv_size} bits", file=output_file)
    print(file=output_file)
    
    if analyze_structure:
        print("=" * 70, file=output_file)
        print("Cipher Structure Analysis", file=output_file)
        print("=" * 70, file=output_file)
        print(file=output_file)
        
        structure = cipher.analyze_structure()
        
        print(f"Number of LFSRs: {len(structure.lfsr_configs)}", file=output_file)
        print(f"Total state size: {structure.state_size} bits", file=output_file)
        print(f"Clock control: {structure.clock_control}", file=output_file)
        print(f"Combiner: {structure.combiner}", file=output_file)
        print(file=output_file)
        
        for i, lfsr_config in enumerate(structure.lfsr_configs, 1):
            print(f"LFSR {i}:", file=output_file)
            print(f"  Degree: {lfsr_config.degree}", file=output_file)
            print(f"  Field order: {lfsr_config.field_order}", file=output_file)
            print(file=output_file)
    
    if generate_keystream:
        print("=" * 70, file=output_file)
        print("Keystream Generation", file=output_file)
        print("=" * 70, file=output_file)
        print(file=output_file)
        
        # Load key and IV
        if key_file:
            key = load_bits_from_file(key_file)
            if len(key) != config.key_size:
                print(f"WARNING: Key size mismatch. Expected {config.key_size} bits, got {len(key)}", file=sys.stderr)
                key = key[:config.key_size] if len(key) > config.key_size else key + [0] * (config.key_size - len(key))
        else:
            # Use default key
            key = [1] * config.key_size
            print(f"Using default key (all 1s)", file=output_file)
        
        iv = None
        if iv_file:
            iv = load_bits_from_file(iv_file)
            if len(iv) != config.iv_size:
                print(f"WARNING: IV size mismatch. Expected {config.iv_size} bits, got {len(iv)}", file=sys.stderr)
                iv = iv[:config.iv_size] if len(iv) > config.iv_size else iv + [0] * (config.iv_size - len(iv))
        else:
            # Use default IV
            iv = [0] * config.iv_size
            print(f"Using default IV (all 0s)", file=output_file)
        
        print(f"Generating {keystream_length} bits of keystream...", file=output_file)
        keystream = cipher.generate_keystream(key, iv, keystream_length)
        
        print(f"✓ Generated {len(keystream)} keystream bits", file=output_file)
        print(f"  Ones: {sum(keystream)}", file=output_file)
        print(f"  Zeros: {len(keystream) - sum(keystream)}", file=output_file)
        print(f"  Balance: {abs(sum(keystream) - (len(keystream) - sum(keystream))) / len(keystream):.4f}", file=output_file)
        print(file=output_file)
        
        # Show first 100 bits
        print("First 100 bits of keystream:", file=output_file)
        keystream_str = ''.join(str(b) for b in keystream[:100])
        print(f"  {keystream_str}", file=output_file)
        print(file=output_file)
    
    print("=" * 70, file=output_file)
    print("Analysis Complete", file=output_file)
    print("=" * 70, file=output_file)
