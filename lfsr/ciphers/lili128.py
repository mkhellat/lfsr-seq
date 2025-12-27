#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LILI-128 Stream Cipher Analysis

This module provides analysis capabilities for the LILI-128 stream cipher, which
is an academic design demonstrating clock-controlled LFSR techniques. LILI-128
uses two LFSRs where one controls the clocking of the other.

**Historical Context**:

LILI-128 was designed as an academic exercise to demonstrate clock-controlled
LFSR designs. It provides a good example of how irregular clocking can be
achieved using one LFSR to control another.

**Security Status**:

LILI-128 has been analyzed and has known weaknesses. It serves primarily as an
educational example of clock-controlled LFSR design.

**Key Terminology**:

- **LILI-128**: Academic stream cipher design
- **Clock-Controlled LFSR**: One LFSR controls when another advances
- **Irregular Clocking**: Clocking pattern is not regular
- **Clock Control Function**: Function determining clocking behavior
- **Two-Stage Design**: Clock generator + data generator

**Mathematical Foundation**:

LILI-128 uses two LFSRs:
- **LFSR1 (Clock Generator)**: 39 bits, controls clocking
- **LFSR2 (Data Generator)**: 89 bits, generates output

The clock control function determines how many times LFSR2 advances based on
LFSR1's output.
"""

from typing import List, Optional

from sage.all import *

from lfsr.attacks import LFSRConfig
from lfsr.ciphers.base import (
    StreamCipher,
    CipherConfig,
    CipherStructure
)


class LILI128(StreamCipher):
    """
    LILI-128 stream cipher implementation.
    
    LILI-128 is an academic design demonstrating clock-controlled LFSR
    techniques. It uses two LFSRs where one controls the clocking of the other.
    
    **Cipher Structure**:
    
    - **LFSR1 (Clock Generator)**: 39 bits
    - **LFSR2 (Data Generator)**: 89 bits
    - **Clock Control**: LFSR1 output determines how many times LFSR2 advances
    - **Output**: LFSR2 output bit
    
    **Key and IV**:
    
    - **Key Size**: 128 bits
    - **IV Size**: 128 bits
    - **Total State**: 39 + 89 = 128 bits
    
    **Example Usage**:
    
        >>> from lfsr.ciphers.lili128 import LILI128
        >>> cipher = LILI128()
        >>> key = [1] * 128
        >>> iv = [0] * 128
        >>> keystream = cipher.generate_keystream(key, iv, 100)
    """
    
    LFSR1_SIZE = 39  # Clock generator
    LFSR2_SIZE = 89  # Data generator
    TOTAL_SIZE = 128
    
    def __init__(self):
        """Initialize LILI-128 cipher."""
        self.lfsr1 = None  # Clock generator
        self.lfsr2 = None  # Data generator
    
    def get_config(self) -> CipherConfig:
        """Get LILI-128 cipher configuration."""
        return CipherConfig(
            cipher_name="LILI-128",
            key_size=128,
            iv_size=128,
            description="LILI-128 academic design with clock-controlled LFSRs",
            parameters={
                'lfsr1_size': self.LFSR1_SIZE,
                'lfsr2_size': self.LFSR2_SIZE,
                'total_size': self.TOTAL_SIZE
            }
        )
    
    def _clock_lfsr1(self):
        """Clock LFSR1 (clock generator)."""
        # LFSR1: polynomial x^39 + x^35 + x^33 + x^31 + x^17 + 1
        # Taps at positions: 38, 34, 32, 30, 16
        feedback = (self.lfsr1[38] ^ self.lfsr1[34] ^ self.lfsr1[32] ^ 
                   self.lfsr1[30] ^ self.lfsr1[16])
        self.lfsr1 = [feedback] + self.lfsr1[:-1]
    
    def _clock_lfsr2(self):
        """Clock LFSR2 (data generator)."""
        # LFSR2: polynomial x^89 + x^83 + x^80 + x^55 + x^53 + x^42 + x^39 + 1
        # Taps at positions: 88, 82, 79, 54, 52, 41, 38
        feedback = (self.lfsr2[88] ^ self.lfsr2[82] ^ self.lfsr2[79] ^ 
                   self.lfsr2[54] ^ self.lfsr2[52] ^ self.lfsr2[41] ^ 
                   self.lfsr2[38])
        self.lfsr2 = [feedback] + self.lfsr2[:-1]
    
    def _clock_control_function(self) -> int:
        """
        Compute clock control value from LFSR1 output.
        
        The clock control function determines how many times LFSR2 should advance.
        It uses two bits from LFSR1 to determine the clocking amount.
        
        Returns:
            Number of times LFSR2 should advance (1, 2, 3, or 4)
        """
        # Use bits 12 and 20 from LFSR1
        bit12 = self.lfsr1[12]
        bit20 = self.lfsr1[20]
        
        # Clock control: 1 + (2*bit12 + bit20)
        # This gives values 1, 2, 3, or 4
        clock_count = 1 + (2 * bit12 + bit20)
        return clock_count
    
    def _get_output_bit(self) -> int:
        """Get output bit from LILI-128."""
        # Output is MSB of LFSR2
        return self.lfsr2[0]
    
    def _initialize(self, key: List[int], iv: Optional[List[int]]):
        """Initialize LILI-128 with key and IV."""
        if len(key) != 128:
            raise ValueError(f"LILI-128 requires 128-bit key, got {len(key)} bits")
        
        if iv is None:
            iv = [0] * 128
        elif len(iv) != 128:
            raise ValueError(f"LILI-128 requires 128-bit IV, got {len(iv)} bits")
        
        # Initialize LFSR1 (clock generator) with first 39 bits of key
        self.lfsr1 = key[0:39]
        
        # Initialize LFSR2 (data generator) with remaining 89 bits
        # Use key bits 39-127 and IV bits
        self.lfsr2 = key[39:128] + iv[0:10]  # 89 + 10 = 99, pad to 89
        if len(self.lfsr2) < 89:
            self.lfsr2 = self.lfsr2 + [0] * (89 - len(self.lfsr2))
        self.lfsr2 = self.lfsr2[:89]
    
    def generate_keystream(
        self,
        key: List[int],
        iv: Optional[List[int]],
        length: int
    ) -> List[int]:
        """
        Generate LILI-128 keystream.
        
        Args:
            key: 128-bit secret key
            iv: 128-bit initialization vector, or None
            length: Desired keystream length in bits
        
        Returns:
            List of keystream bits
        """
        self._initialize(key, iv)
        
        keystream = []
        for _ in range(length):
            # Clock LFSR1 (clock generator)
            self._clock_lfsr1()
            
            # Determine how many times to clock LFSR2
            clock_count = self._clock_control_function()
            
            # Clock LFSR2 the determined number of times
            for _ in range(clock_count):
                self._clock_lfsr2()
            
            # Get output bit
            output = self._get_output_bit()
            keystream.append(output)
        
        return keystream
    
    def analyze_structure(self) -> CipherStructure:
        """Analyze LILI-128 cipher structure."""
        # LFSR1: polynomial x^39 + x^35 + x^33 + x^31 + x^17 + 1
        lfsr1_coeffs = [0] * 39
        lfsr1_coeffs[0] = 1  # x^0
        lfsr1_coeffs[16] = 1  # x^17
        lfsr1_coeffs[30] = 1  # x^31
        lfsr1_coeffs[32] = 1  # x^33
        lfsr1_coeffs[34] = 1  # x^35
        lfsr1_coeffs[38] = 1  # x^39
        
        # LFSR2: polynomial x^89 + x^83 + x^80 + x^55 + x^53 + x^42 + x^39 + 1
        lfsr2_coeffs = [0] * 89
        lfsr2_coeffs[0] = 1  # x^0
        lfsr2_coeffs[38] = 1  # x^39
        lfsr2_coeffs[41] = 1  # x^42
        lfsr2_coeffs[52] = 1  # x^53
        lfsr2_coeffs[54] = 1  # x^55
        lfsr2_coeffs[79] = 1  # x^80
        lfsr2_coeffs[82] = 1  # x^83
        lfsr2_coeffs[88] = 1  # x^89
        
        lfsr1_config = LFSRConfig(coefficients=lfsr1_coeffs, field_order=2, degree=39)
        lfsr2_config = LFSRConfig(coefficients=lfsr2_coeffs, field_order=2, degree=89)
        
        return CipherStructure(
            lfsr_configs=[lfsr1_config, lfsr2_config],
            clock_control=(
                "LFSR1 (clock generator) controls clocking of LFSR2 (data generator). "
                "Clock control function uses LFSR1 bits 12 and 20 to determine "
                "how many times LFSR2 advances (1, 2, 3, or 4 times)."
            ),
            combiner="Output is MSB of LFSR2 (data generator)",
            state_size=128,
            details={
                'lfsr1_size': 39,
                'lfsr2_size': 89,
                'total_size': 128,
                'lfsr1_role': 'Clock generator',
                'lfsr2_role': 'Data generator',
                'clock_control_bits': [12, 20],
                'clock_count_range': [1, 2, 3, 4]
            }
        )
    
    def apply_attacks(
        self,
        keystream: List[int],
        attack_types: Optional[List[str]] = None
    ) -> dict:
        """Apply attacks to LILI-128 keystream."""
        return {
            'note': 'LILI-128 has known weaknesses and serves as an educational example',
            'known_vulnerabilities': [
                'Correlation attacks',
                'Clock control analysis',
                'Known-plaintext attacks'
            ]
        }
