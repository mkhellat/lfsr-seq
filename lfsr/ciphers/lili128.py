#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LILI-128 Stream Cipher Analysis

This module provides analysis capabilities for the LILI-128 stream
cipher, which is an academic design demonstrating clock-controlled
LFSR design. LILI-128 uses two LFSRs where one controls the clocking
of the other.

**Historical Context**:

LILI-128 was designed by E. Dawson, A. Clark, J. Golić, H. J. Kim, J. Moon,
S. J. Lee, and S. J. Park as an academic stream cipher design. It demonstrates
the clock-controlled LFSR design pattern.

**Security Status**:

LILI-128 has been analyzed:
- Some attacks found (correlation attacks)
- Demonstrates clock-controlled design
- Used primarily for research and education

**Key Terminology**:

- **LILI-128**: Academic stream cipher design
- **Clock-Controlled LFSR**: One LFSR controls when another advances
- **Irregular Clocking**: Clocking pattern is not regular
- **Clock Control Function**: Function determining clocking behavior
"""

from typing import List, Optional

from lfsr.sage_imports import *

from lfsr.attacks import LFSRConfig
from lfsr.ciphers.base import (
    StreamCipher,
    CipherConfig,
    CipherStructure
)


class LILI128(StreamCipher):
    """
    LILI-128 stream cipher implementation.
    
    LILI-128 uses two LFSRs where one (LFSRc) controls the clocking of the
    other (LFSRd). This demonstrates the clock-controlled LFSR design pattern.
    
    **Cipher Structure**:
    
    - **LFSRc**: 39 bits (clock control LFSR)
    - **LFSRd**: 89 bits (data LFSR, clock-controlled)
    - **Clock Control**: LFSRc output determines how many times LFSRd advances
    - **Output**: Output from LFSRd
    
    **Key and IV**:
    
    - **Key Size**: 128 bits
    - **IV Size**: Variable (typically 64 bits)
    - **Total State**: 128 bits (39 + 89)
    
    **Example Usage**:
    
        >>> from lfsr.ciphers.lili128 import LILI128
        >>> cipher = LILI128()
        >>> key = [1] * 128
        >>> iv = [0] * 64
        >>> keystream = cipher.generate_keystream(key, iv, 100)
    """
    
    LFSRC_SIZE = 39  # Clock control LFSR
    LFSRD_SIZE = 89  # Data LFSR (clock-controlled)
    TOTAL_SIZE = 128
    
    WARMUP_STEPS = 256
    
    def __init__(self):
        """Initialize LILI-128 cipher."""
        self.lfsrc_state = None  # Clock control LFSR
        self.lfsrd_state = None  # Data LFSR
    
    def get_config(self) -> CipherConfig:
        """Get LILI-128 cipher configuration."""
        return CipherConfig(
            cipher_name="LILI-128",
            key_size=128,
            iv_size=64,
            description="LILI-128 academic design with clock-controlled LFSRs",
            parameters={
                'lfsrc_size': self.LFSRC_SIZE,
                'lfsrd_size': self.LFSRD_SIZE,
                'total_size': self.TOTAL_SIZE,
                'warmup_steps': self.WARMUP_STEPS
            }
        )
    
    def _clock_lfsr(self, state: List[int], taps: List[int], size: int) -> List[int]:
        """Clock a single LFSR."""
        feedback = 0
        for tap in taps:
            feedback ^= state[tap]
        return [feedback] + state[:-1]
    
    def _get_clock_count(self) -> int:
        """
        Get clock count from LFSRc output.
        
        LFSRc output determines how many times LFSRd should advance.
        Typically uses a function of LFSRc output bits.
        """
        # Simplified: use LFSRc output bits to determine clock count
        # In real LILI-128, this is more complex
        c0 = self.lfsrc_state[0]
        c1 = self.lfsrc_state[1]
        clock_count = 1 + (c0 << 1) + c1  # 1, 2, 3, or 4
        return min(clock_count, 4)  # Limit to reasonable value
    
    def _get_output_bit(self) -> int:
        """Get output bit from LILI-128 (from LFSRd)."""
        return self.lfsrd_state[0]  # MSB of data LFSR
    
    def _clock_controlled(self):
        """Clock LILI-128 with clock control."""
        # Clock LFSRc (always advances)
        # LFSRc: polynomial x^39 + x^35 + x^33 + x^31 + x^17 + 1
        self.lfsrc_state = self._clock_lfsr(
            self.lfsrc_state, [38, 34, 32, 30, 16], self.LFSRC_SIZE
        )
        
        # Get clock count from LFSRc
        clock_count = self._get_clock_count()
        
        # Clock LFSRd clock_count times
        # LFSRd: polynomial x^89 + x^83 + x^80 + x^55 + x^53 + x^42 + x^39 + x^6 + 1
        for _ in range(clock_count):
            self.lfsrd_state = self._clock_lfsr(
                self.lfsrd_state,
                [88, 82, 79, 54, 52, 41, 38, 5],
                self.LFSRD_SIZE
            )
    
    def _initialize(self, key: List[int], iv: Optional[List[int]]):
        """Initialize LILI-128 with key and IV."""
        if len(key) != 128:
            raise ValueError(f"LILI-128 requires 128-bit key, got {len(key)} bits")
        
        if iv is None:
            iv = [0] * 64
        elif len(iv) < 64:
            iv = iv + [0] * (64 - len(iv))
        
        # Initialize LFSRc with first 39 bits of key
        self.lfsrc_state = key[0:39]
        
        # Initialize LFSRd with remaining 89 bits of key
        self.lfsrd_state = key[39:128]
        
        # Load IV (XOR into both LFSRs)
        for i in range(min(64, len(iv))):
            if i < 39:
                self.lfsrc_state[i] ^= iv[i]
            if i < 89:
                self.lfsrd_state[i] ^= iv[i]
        
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
        Generate LILI-128 keystream.
        
        Args:
            key: 128-bit secret key
            iv: Initialization vector (typically 64 bits), or None
            length: Desired keystream length in bits
        
        Returns:
            List of keystream bits
        """
        self._initialize(key, iv)
        
        keystream = []
        for _ in range(length):
            output = self._get_output_bit()
            keystream.append(output)
            self._clock_controlled()
        
        return keystream
    
    def analyze_structure(self) -> CipherStructure:
        """Analyze LILI-128 cipher structure."""
        # LFSRc configuration
        lfsrc_coeffs = [0] * 39
        lfsrc_coeffs[0] = 1
        lfsrc_coeffs[16] = 1
        lfsrc_coeffs[30] = 1
        lfsrc_coeffs[32] = 1
        lfsrc_coeffs[34] = 1
        lfsrc_coeffs[38] = 1
        
        # LFSRd configuration
        lfsrd_coeffs = [0] * 89
        lfsrd_coeffs[0] = 1
        lfsrd_coeffs[5] = 1
        lfsrd_coeffs[38] = 1
        lfsrd_coeffs[41] = 1
        lfsrd_coeffs[52] = 1
        lfsrd_coeffs[54] = 1
        lfsrd_coeffs[79] = 1
        lfsrd_coeffs[82] = 1
        lfsrd_coeffs[88] = 1
        
        lfsrc_config = LFSRConfig(coefficients=lfsrc_coeffs, field_order=2, degree=39)
        lfsrd_config = LFSRConfig(coefficients=lfsrd_coeffs, field_order=2, degree=89)
        
        return CipherStructure(
            lfsr_configs=[lfsrc_config, lfsrd_config],
            clock_control=(
                "LFSRc (clock control) always advances. "
                "LFSRc output determines how many times LFSRd (data) advances. "
                "This creates irregular clocking of LFSRd."
            ),
            combiner="Output is directly from LFSRd (no combining function)",
            state_size=128,  # 39 + 89
            details={
                'lfsrc_size': 39,
                'lfsrd_size': 89,
                'total_size': 128,
                'warmup_steps': self.WARMUP_STEPS,
                'polynomials': {
                    'lfsrc': 'x^39 + x^35 + x^33 + x^31 + x^17 + 1',
                    'lfsrd': 'x^89 + x^83 + x^80 + x^55 + x^53 + x^42 + x^39 + x^6 + 1'
                }
            }
        )
    
    def apply_attacks(
        self,
        keystream: List[int],
        attack_types: Optional[List[str]] = None
    ) -> dict:
        """Apply attacks to LILI-128 keystream."""
        return {
            'note': 'LILI-128 has known vulnerabilities',
            'known_vulnerabilities': [
                'Correlation attacks',
                'Clock control analysis'
            ]
        }
