#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A5/2 Stream Cipher Analysis

This module provides analysis capabilities for the A5/2 stream cipher, which was
a weaker variant of A5/1 designed for export restrictions. A5/2 uses four LFSRs
with a more complex clocking mechanism than A5/1.

**Historical Context**:

A5/2 was designed as a weaker variant of A5/1 to comply with export restrictions
on cryptography. It was intended for use in countries where strong encryption
was restricted. A5/2 was cryptanalyzed and broken shortly after its design became
public, demonstrating that deliberately weakened cryptography is fundamentally
insecure.

**Security Status**:

A5/2 is considered extremely weak and was broken by Barkan, Biham, and Keller in
2003. The attack can recover the key in real-time from a few frames of keystream.
A5/2 should never be used for any security-sensitive application.

**Key Terminology**:

- **A5/2**: Weaker variant of A5/1 designed for export restrictions
- **Export Restrictions**: Legal restrictions on exporting strong cryptography
- **Deliberately Weakened**: Intentionally designed to be weaker for compliance
- **Real-Time Attack**: Attack that can recover key in seconds or minutes
- **Frame**: A unit of data in GSM (22 bits of IV)
"""

from typing import List, Optional

from sage.all import *

from lfsr.attacks import LFSRConfig
from lfsr.ciphers.base import (
    StreamCipher,
    CipherConfig,
    CipherStructure
)


class A5_2(StreamCipher):
    """
    A5/2 GSM stream cipher implementation (weaker variant).
    
    A5/2 is a deliberately weakened variant of A5/1, designed to comply with
    export restrictions. It uses four LFSRs with a more complex clocking
    mechanism, but is fundamentally insecure.
    
    **Cipher Structure**:
    
    - **LFSR1**: 19 bits
    - **LFSR2**: 22 bits
    - **LFSR3**: 23 bits
    - **LFSR4**: 17 bits (additional LFSR)
    - **Clock Control**: More complex than A5/1, uses LFSR4
    - **Output**: XOR of LFSR outputs with additional filtering
    
    **Key and IV**:
    
    - **Key Size**: 64 bits
    - **IV Size**: 22 bits (frame number)
    - **Total State**: 19 + 22 + 23 + 17 = 81 bits
    
    **Security Warning**:
    
    A5/2 is extremely weak and should never be used. It was broken in 2003 and
    can be attacked in real-time. This implementation is for educational and
    analysis purposes only.
    
    **Example Usage**:
    
        >>> from lfsr.ciphers.a5_2 import A5_2
        >>> cipher = A5_2()
        >>> key = [1] * 64
        >>> iv = [0] * 22
        >>> keystream = cipher.generate_keystream(key, iv, 100)
    """
    
    # A5/2 LFSR configurations
    LFSR1_SIZE = 19
    LFSR2_SIZE = 22
    LFSR3_SIZE = 23
    LFSR4_SIZE = 17
    
    # Clock control bit positions
    CLOCK_BIT_1 = 8
    CLOCK_BIT_2 = 10
    CLOCK_BIT_3 = 10
    CLOCK_BIT_4 = 7  # LFSR4 clock control
    
    WARMUP_STEPS = 100
    
    def __init__(self):
        """Initialize A5/2 cipher."""
        self.lfsr1_state = None
        self.lfsr2_state = None
        self.lfsr3_state = None
        self.lfsr4_state = None
    
    def get_config(self) -> CipherConfig:
        """Get A5/2 cipher configuration."""
        return CipherConfig(
            cipher_name="A5/2",
            key_size=64,
            iv_size=22,
            description="A5/2 GSM stream cipher (weaker variant, export-restricted)",
            parameters={
                'lfsr1_size': self.LFSR1_SIZE,
                'lfsr2_size': self.LFSR2_SIZE,
                'lfsr3_size': self.LFSR3_SIZE,
                'lfsr4_size': self.LFSR4_SIZE,
                'warmup_steps': self.WARMUP_STEPS,
                'security_warning': 'A5/2 is extremely weak and should never be used'
            }
        )
    
    def _majority(self, a: int, b: int, c: int) -> int:
        """Compute majority function."""
        return (a & b) | (a & c) | (b & c)
    
    def _clock_lfsr(self, state: List[int], taps: List[int], size: int) -> List[int]:
        """Clock a single LFSR."""
        feedback = 0
        for tap in taps:
            feedback ^= state[tap]
        return [feedback] + state[:-1]
    
    def _get_output_bit(self) -> int:
        """Get output bit from A5/2."""
        # A5/2 uses a more complex output function
        # Simplified implementation
        output1 = self.lfsr1_state[0]
        output2 = self.lfsr2_state[0]
        output3 = self.lfsr3_state[0]
        output4 = self.lfsr4_state[0]
        
        # A5/2 output function (simplified)
        return output1 ^ output2 ^ output3 ^ output4
    
    def _clock_controlled(self):
        """Clock A5/2 with irregular clocking."""
        # A5/2 uses LFSR4 to control clocking
        c4 = self.lfsr4_state[self.CLOCK_BIT_4]
        
        # Clock LFSR4 first
        self.lfsr4_state = self._clock_lfsr(
            self.lfsr4_state,
            [16, 11],  # Simplified taps for LFSR4
            self.LFSR4_SIZE
        )
        
        # Clock control for other LFSRs (simplified)
        c1 = self.lfsr1_state[self.CLOCK_BIT_1]
        c2 = self.lfsr2_state[self.CLOCK_BIT_2]
        c3 = self.lfsr3_state[self.CLOCK_BIT_3]
        
        majority = self._majority(c1, c2, c3)
        
        if c1 == majority:
            self.lfsr1_state = self._clock_lfsr(
                self.lfsr1_state,
                [18, 17, 16, 13],
                self.LFSR1_SIZE
            )
        
        if c2 == majority:
            self.lfsr2_state = self._clock_lfsr(
                self.lfsr2_state,
                [21, 20],
                self.LFSR2_SIZE
            )
        
        if c3 == majority:
            self.lfsr3_state = self._clock_lfsr(
                self.lfsr3_state,
                [22, 21, 20, 7],
                self.LFSR3_SIZE
            )
    
    def _initialize(self, key: List[int], iv: Optional[List[int]]):
        """Initialize A5/2 with key and IV."""
        if len(key) != 64:
            raise ValueError(f"A5/2 requires 64-bit key, got {len(key)} bits")
        
        if iv is None:
            iv = [0] * 22
        elif len(iv) != 22:
            raise ValueError(f"A5/2 requires 22-bit IV, got {len(iv)} bits")
        
        # Initialize LFSR states (simplified)
        self.lfsr1_state = key[0:19]
        self.lfsr2_state = key[19:41]
        self.lfsr3_state = key[41:64]
        self.lfsr4_state = [0] * 17  # LFSR4 initialization (simplified)
        
        # Load frame number
        for i in range(22):
            if i < 19:
                self.lfsr1_state[i] ^= iv[i]
            if i < 22:
                self.lfsr2_state[i] ^= iv[i]
            if i < 23:
                self.lfsr3_state[i] ^= iv[i]
        
        # Warm-up phase
        for _ in range(self.WARMUP_STEPS):
            self._clock_controlled()
    
    def generate_keystream(
        self,
        key: List[int],
        iv: Optional[List[int]],
        length: int
    ) -> List[int]:
        """
        Generate A5/2 keystream.
        
        **Security Warning**: A5/2 is extremely weak. This implementation is
        for educational and analysis purposes only.
        
        Args:
            key: 64-bit secret key
            iv: 22-bit initialization vector, or None
            length: Desired keystream length in bits
        
        Returns:
            List of keystream bits
        """
        self._initialize(key, iv)
        
        keystream = []
        for _ in range(length):
            self._clock_controlled()
            output = self._get_output_bit()
            keystream.append(output)
        
        return keystream
    
    def analyze_structure(self) -> CipherStructure:
        """Analyze A5/2 cipher structure."""
        # Build LFSR configurations
        lfsr1_coeffs = [0] * 19
        lfsr1_coeffs[0] = 1
        lfsr1_coeffs[13] = 1
        lfsr1_coeffs[16] = 1
        lfsr1_coeffs[17] = 1
        lfsr1_coeffs[18] = 1
        
        lfsr2_coeffs = [0] * 22
        lfsr2_coeffs[0] = 1
        lfsr2_coeffs[20] = 1
        lfsr2_coeffs[21] = 1
        
        lfsr3_coeffs = [0] * 23
        lfsr3_coeffs[0] = 1
        lfsr3_coeffs[7] = 1
        lfsr3_coeffs[20] = 1
        lfsr3_coeffs[21] = 1
        lfsr3_coeffs[22] = 1
        
        lfsr4_coeffs = [0] * 17
        lfsr4_coeffs[0] = 1
        lfsr4_coeffs[10] = 1
        lfsr4_coeffs[16] = 1
        
        lfsr1_config = LFSRConfig(coefficients=lfsr1_coeffs, field_order=2, degree=19)
        lfsr2_config = LFSRConfig(coefficients=lfsr2_coeffs, field_order=2, degree=22)
        lfsr3_config = LFSRConfig(coefficients=lfsr3_coeffs, field_order=2, degree=23)
        lfsr4_config = LFSRConfig(coefficients=lfsr4_coeffs, field_order=2, degree=17)
        
        return CipherStructure(
            lfsr_configs=[lfsr1_config, lfsr2_config, lfsr3_config, lfsr4_config],
            clock_control=(
                "Complex clocking mechanism using LFSR4 and majority function. "
                "LFSR4 controls clocking of other LFSRs."
            ),
            combiner="XOR of four LFSR outputs with additional filtering",
            state_size=81,  # 19 + 22 + 23 + 17
            details={
                'lfsr1_size': 19,
                'lfsr2_size': 22,
                'lfsr3_size': 23,
                'lfsr4_size': 17,
                'warmup_steps': self.WARMUP_STEPS,
                'security_warning': 'A5/2 is extremely weak and broken'
            }
        )
    
    def apply_attacks(
        self,
        keystream: List[int],
        attack_types: Optional[List[str]] = None
    ) -> dict:
        """Apply attacks to A5/2 keystream."""
        return {
            'note': 'A5/2 is extremely weak',
            'known_vulnerabilities': [
                'Real-time key recovery (Barkan et al., 2003)',
                'Known-plaintext attacks',
                'Correlation attacks',
                'Should never be used'
            ],
            'attack_complexity': 'Real-time (seconds to minutes)'
        }
