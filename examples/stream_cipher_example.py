#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example: Stream Cipher Analysis

This example demonstrates how to analyze real-world stream ciphers, generate
keystreams, and compare different cipher designs.

Example Usage:
    python3 examples/stream_cipher_example.py
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

from lfsr.ciphers import (
    A5_1, A5_2, E0, Trivium, Grain128, Grain128a, LILI128
)
from lfsr.ciphers.comparison import compare_ciphers, generate_comparison_report


def example_a5_1():
    """Example of A5/1 cipher analysis."""
    print("=" * 70)
    print("Example 1: A5/1 GSM Stream Cipher")
    print("=" * 70)
    
    cipher = A5_1()
    config = cipher.get_config()
    
    print(f"\nCipher Configuration:")
    print(f"  Name: {config.cipher_name}")
    print(f"  Key size: {config.key_size} bits")
    print(f"  IV size: {config.iv_size} bits")
    print(f"  Description: {config.description}")
    
    # Analyze structure
    print(f"\nStructure Analysis:")
    structure = cipher.analyze_structure()
    print(f"  Number of LFSRs: {len(structure.lfsr_configs)}")
    print(f"  Total state size: {structure.state_size} bits")
    print(f"  Clock control: {structure.clock_control[:60]}...")
    print(f"  Combiner: {structure.combiner}")
    
    # Generate keystream
    print(f"\nKeystream Generation:")
    key = [1, 0, 1] * 21 + [1]  # 64-bit key
    iv = [0] * 22  # 22-bit IV (frame number)
    keystream = cipher.generate_keystream(key, iv, 100)
    
    print(f"  Generated {len(keystream)} bits")
    print(f"  Ones: {sum(keystream)}")
    print(f"  Zeros: {len(keystream) - sum(keystream)}")
    print(f"  Balance: {abs(sum(keystream) - (len(keystream) - sum(keystream))) / len(keystream):.4f}")
    print(f"  First 20 bits: {''.join(str(b) for b in keystream[:20])}")


def example_e0():
    """Example of E0 Bluetooth cipher analysis."""
    print("\n" + "=" * 70)
    print("Example 2: E0 Bluetooth Stream Cipher")
    print("=" * 70)
    
    cipher = E0()
    config = cipher.get_config()
    
    print(f"\nCipher Configuration:")
    print(f"  Name: {config.cipher_name}")
    print(f"  Key size: {config.key_size} bits")
    print(f"  IV size: {config.iv_size} bits")
    
    # Analyze structure
    structure = cipher.analyze_structure()
    print(f"\nStructure Analysis:")
    print(f"  Number of LFSRs: {len(structure.lfsr_configs)}")
    print(f"  Total state size: {structure.state_size} bits")
    print(f"  Combiner: {structure.combiner}")
    
    # Generate keystream
    key = [1] * 128
    iv = [0] * 64
    keystream = cipher.generate_keystream(key, iv, 100)
    print(f"\nKeystream: Generated {len(keystream)} bits")


def example_trivium():
    """Example of Trivium cipher analysis."""
    print("\n" + "=" * 70)
    print("Example 3: Trivium eSTREAM Finalist")
    print("=" * 70)
    
    cipher = Trivium()
    config = cipher.get_config()
    
    print(f"\nCipher Configuration:")
    print(f"  Name: {config.cipher_name}")
    print(f"  Key size: {config.key_size} bits")
    print(f"  IV size: {config.iv_size} bits")
    print(f"  Note: Trivium uses shift registers with non-linear feedback")
    
    # Generate keystream
    key = [1] * 80
    iv = [0] * 80
    keystream = cipher.generate_keystream(key, iv, 100)
    print(f"\nKeystream: Generated {len(keystream)} bits")


def example_grain():
    """Example of Grain family analysis."""
    print("\n" + "=" * 70)
    print("Example 4: Grain Family (Grain-128 and Grain-128a)")
    print("=" * 70)
    
    # Grain-128
    cipher128 = Grain128()
    config128 = cipher128.get_config()
    print(f"\nGrain-128:")
    print(f"  Name: {config128.cipher_name}")
    print(f"  Key size: {config128.key_size} bits")
    print(f"  IV size: {config128.iv_size} bits")
    
    # Grain-128a
    cipher128a = Grain128a()
    config128a = cipher128a.get_config()
    print(f"\nGrain-128a:")
    print(f"  Name: {config128a.cipher_name}")
    print(f"  Key size: {config128a.key_size} bits")
    print(f"  Authenticated encryption: {config128a.parameters.get('authenticated_encryption', False)}")


def example_lili128():
    """Example of LILI-128 analysis."""
    print("\n" + "=" * 70)
    print("Example 5: LILI-128 Academic Design")
    print("=" * 70)
    
    cipher = LILI128()
    config = cipher.get_config()
    
    print(f"\nCipher Configuration:")
    print(f"  Name: {config.cipher_name}")
    print(f"  Key size: {config.key_size} bits")
    print(f"  Note: Demonstrates clock-controlled LFSR design")
    
    # Analyze structure
    structure = cipher.analyze_structure()
    print(f"\nStructure Analysis:")
    print(f"  Number of LFSRs: {len(structure.lfsr_configs)}")
    print(f"  Clock control: {structure.clock_control[:60]}...")


def example_comparison():
    """Example of cipher comparison."""
    print("\n" + "=" * 70)
    print("Example 6: Cipher Comparison")
    print("=" * 70)
    
    # Compare multiple ciphers
    ciphers = [A5_1(), E0(), Trivium()]
    comparison = compare_ciphers(ciphers)
    
    print(f"\nComparing: {', '.join(comparison.ciphers)}")
    print(f"\nProperties Comparison:")
    print(f"{'Property':<20} {'A5/1':<15} {'E0':<15} {'Trivium':<15}")
    print("-" * 70)
    
    for prop in ['key_size', 'iv_size', 'state_size']:
        row = f"{prop.replace('_', ' ').title():<20}"
        for cipher_name in comparison.ciphers:
            row += f"{comparison.properties[cipher_name][prop]:<15}"
        print(row)
    
    # Generate full report
    print(f"\nFull Comparison Report:")
    print("-" * 70)
    report = generate_comparison_report(comparison)
    print(report[:500] + "...")


def example_comprehensive_analysis():
    """Example of comprehensive cipher analysis."""
    print("\n" + "=" * 70)
    print("Example 7: Comprehensive Analysis")
    print("=" * 70)
    
    cipher = A5_1()
    
    # Comprehensive analysis
    key = [1, 0, 1] * 21 + [1]
    iv = [0] * 22
    result = cipher.analyze(key=key, iv=iv, keystream_length=1000)
    
    print(f"\nComprehensive Analysis Results:")
    print(f"  Cipher: {result.cipher_name}")
    print(f"  Structure: {len(result.structure.lfsr_configs)} LFSRs")
    print(f"  Keystream properties: {result.keystream_properties}")
    print(f"  Security assessment: {result.security_assessment}")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("Stream Cipher Analysis Examples")
    print("=" * 70)
    print("\nThis script demonstrates stream cipher analysis capabilities.\n")
    
    try:
        example_a5_1()
        example_e0()
        example_trivium()
        example_grain()
        example_lili128()
        example_comparison()
        example_comprehensive_analysis()
        
        print("\n" + "=" * 70)
        print("Examples Complete!")
        print("=" * 70)
        print("\nFor more information, see:")
        print("  - Stream Ciphers Guide: docs/stream_ciphers.rst")
        print("  - API Documentation: docs/api/ciphers.rst")
        print("  - Mathematical Background: docs/mathematical_background.rst")
        
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
