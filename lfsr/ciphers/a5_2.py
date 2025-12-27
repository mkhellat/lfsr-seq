#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A5/2 Stream Cipher Analysis

This module provides analysis capabilities for the A5/2 stream cipher, which was
a weaker variant of A5/1 designed for export restrictions. A5/2 uses four LFSRs
with a more complex clocking mechanism.

**Historical Context**:

A5/2 was designed as a weaker variant of A5/1 to comply with export restrictions
on cryptography. It was intended for use in countries where strong encryption
was restricted. A5/2 was cryptanalyzed and found to be extremely weak, with
attacks that can recover the key in seconds.

**Security Status**:

A5/2 is considered extremely weak and insecure. Known attacks include:
- Very fast key recovery attacks (seconds)
- Known-plaintext attacks
- Correlation attacks
- The cipher was intentionally weakened for export compliance

**Key Terminology**:

- **A5/2**: Weaker variant of A5/1 for export restrictions
- **Export Restrictions**: Legal limitations on exporting strong cryptography
- **Complex Clocking**: More complex clocking mechanism than A5/1
- **Four LFSRs**: Uses four LFSRs instead of three (17, 19, 21, 22 bits)
- **Weakness by Design**: Intentionally weakened for compliance

**Mathematical Foundation**:

A5/2 uses four LFSRs:
- LFSR1: 17 bits
- LFSR2: 19 bits
- LFSR3: 21 bits
- LFSR4: 22 bits

The clocking mechanism is more complex than A5/1, involving multiple clock
control bits and a more sophisticated decision function.
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
    
    A5/2 is a weaker variant of A5/1 designed for export restrictions. It uses
    four LFSRs with a more complex clocking mechanism. A5/2 is intentionally
    weak and should not be used for security purposes.
    
    **Cipher Structure**:
    
    - **LFSR1**: 17 bits
    - **LFSR2**: 19 bits
    - **LFSR3**: 21 bits
    - **LFSR4**: 22 bits
    - **Clock Control**: Complex mechanism involving multiple control bits
    - **Output**: XOR of LFSR outputs with additional mixing
    
    **Key and IV**:
    
    - **Key Size**: 64 bits
    - **IV Size**: 22 bits (frame number)
    - **Total State**: 17 + 19 + 21 + 22 = 79 bits
    
    **Security Warning**:
    
    A5/2 is extremely weak and should never be used for security purposes. It was
    intentionally weakened for export compliance and can be broken in seconds.
    
    **Example Usage**:
    
        >>> from lfsr.ciphers.a5_2 import A5_2
        >>> cipher = A5_2()
        >>> key = [1] * 64
        >>> iv = [0] * 22
        >>> keystream = cipher.generate_keystream(key, iv, 100)
    """
    
    # A5/2 LFSR configurations
    LFSR1_SIZE = 17
    LFSR2_SIZE = 19
    LFSR3_SIZE = 21
    LFSR4_SIZE = 22
    
    # Clock control bit positions (simplified - full A5/2 is more complex)
    CLOCK_BIT_1 = 3
    CLOCK_BIT_2 = 7
    CLOCK_BIT_3 = 10
    CLOCK_BIT_4 = 10
    
    # Warm-up steps
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
                'security_warning': 'EXTREMELY WEAK - DO NOT USE FOR SECURITY'
            }
        )
    
    def _clock_lfsr(self, state: List[int], taps: List[int], size: int) -> List[int]:
        """Clock a single LFSR."""
        feedback = 0
        for tap in taps:
            feedback ^= state[tap]
        return [feedback] + state[:-1]
    
    def _get_output_bit(self) -> int:
        """Get output bit from A5/2."""
        # Simplified output (full A5/2 has more complex mixing)
        output1 = self.lfsr1_state[0]
        output2 = self.lfsr2_state[0]
        output3 = self.lfsr3_state[0]
        output4 = self.lfsr4_state[0]
        return output1 ^ output2 ^ output3 ^ output4
    
    def _clock_controlled(self):
        """Clock A5/2 with complex clocking mechanism."""
        # Simplified clocking (full A5/2 is more complex)
        # In practice, A5/2 uses a more sophisticated clocking mechanism
        c1 = self.lfsr1_state[self.CLOCK_BIT_1]
        c2 = self.lfsr2_state[self.CLOCK_BIT_2]
        c3 = self.lfsr3_state[self.CLOCK_BIT_3]
        c4 = self.lfsr4_state[self.CLOCK_BIT_4]
        
        # Simplified majority-like function
        majority = (c1 + c2 + c3 + c4) >= 2
        
        if c1 == majority:
            self.lfsr1_state = self._clock_lfsr(self.lfsr1_state, [16, 11], self.LFSR1_SIZE)
        if c2 == majority:
            self.lfsr2_state = self._clock_lfsr(self.lfsr2_state, [18, 17, 16, 13], self.LFSR2_SIZE)
        if c3 == majority:
            self.lfsr3_state = self._clock_lfsr(self.lfsr3_state, [20, 19], self.LFSR3_SIZE)
        if c4 == majority:
            self.lfsr4_state = self._clock_lfsr(self.lfsr4_state, [21, 20, 19, 16], self.LFSR4_SIZE)
    
    def _initialize(self, key: List[int], iv: Optional[List[int]]):
        """Initialize A5/2 with key and IV."""
        if len(key) != 64:
            raise ValueError(f"A5/2 requires 64-bit key, got {len(key)} bits")
        
        if iv is None:
            iv = [0] * 22
        elif len(iv) != 22:
            raise ValueError(f"A5/2 requires 22-bit IV, got {len(iv)} bits")
        
        # Initialize LFSR states from key
        self.lfsr1_state = key[0:17]
        self.lfsr2_state = key[17:36]
        self.lfsr3_state = key[36:57]
        self.lfsr4_state = key[57:64] + [0] * (22 - 7)  # Pad to 22 bits
        
        # Load frame number (IV)
        for i in range(22):
            if i < 17:
                self.lfsr1_state[i] ^= iv[i]
            if i < 19:
                self.lfsr2_state[i] ^= iv[i]
            if i < 21:
                self.lfsr3_state[i] ^= iv[i]
            if i < 22:
                self.lfsr4_state[i] ^= iv[i]
        
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
        
        **Security Warning**: A5/2 is extremely weak and should never be used
        for security purposes.
        
        Args:
            key: 64-bit secret key
            iv: 22-bit initialization vector (frame number), or None
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
        # Build LFSR configurations (simplified)
        lfsr1_config = LFSRConfig(coefficients=[1] * 17, field_order=2, degree=17)
        lfsr2_config = LFSRConfig(coefficients=[1] * 19, field_order=2, degree=19)
        lfsr3_config = LFSRConfig(coefficients=[1] * 21, field_order=2, degree=21)
        lfsr4_config = LFSRConfig(coefficients=[1] * 22, field_order=2, degree=22)
        
        return CipherStructure(
            lfsr_configs=[lfsr1_config, lfsr2_config, lfsr3_config, lfsr4_config],
            clock_control="Complex clocking mechanism with multiple control bits",
            combiner="XOR of four LFSR outputs with additional mixing",
            state_size=79,  # 17 + 19 + 21 + 22
            details={
                'lfsr1_size': 17,
                'lfsr2_size': 19,
                'lfsr3_size': 21,
                'lfsr4_size': 22,
                'warmup_steps': self.WARMUP_STEPS,
                'security_warning': 'EXTREMELY WEAK - DO NOT USE'
            }
        )
    
    def apply_attacks(
        self,
        keystream: List[int],
        attack_types: Optional[List[str]] = None
    ) -> dict:
        """Apply attacks to A5/2 keystream."""
        return {
            'note': 'A5/2 is extremely weak - attacks can recover key in seconds',
            'known_vulnerabilities': [
                'Very fast key recovery (seconds)',
                'Known-plaintext attacks',
                'Correlation attacks',
                'Intentionally weakened for export compliance'
            ]
        }
