#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LILI-128 Stream Cipher Analysis

This module provides analysis capabilities for the LILI-128 stream cipher, which
is an academic design demonstrating clock-controlled LFSRs. LILI-128 uses two
LFSRs where one controls the clocking of the other.

**Historical Context**:

LILI-128 was designed by E. Dawson, A. Clark, J. Golic, W. Millan, L. Penna,
L. Simpson, and H. Wu as an academic stream cipher design. It demonstrates
the use of clock-controlled LFSRs, where one LFSR controls when another advances.

**Security Status**:

LILI-128 has been analyzed and has known vulnerabilities, including correlation
attacks. It serves as an educational example of clock-controlled LFSR design.

**Key Terminology**:

- **LILI-128**: Academic stream cipher design
- **Clock-Controlled LFSR**: One LFSR controls when another advances
- **Irregular Clocking**: Clocking pattern is not regular
- **Clock Control Function**: Function determining clocking behavior
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
    
    LILI-128 uses two LFSRs where one (LFSRc) controls the clocking of the other
    (LFSRd). The data LFSR (LFSRd) advances a variable number of steps based on
    the output of the clock control LFSR (LFSRc).
    
    **Cipher Structure**:
    
    - **LFSRc**: 39 bits (clock control LFSR)
    - **LFSRd**: 89 bits (data LFSR)
    - **Clock Control**: LFSRc output determines how many times LFSRd advances
    - **Output**: Output from LFSRd (filtered)
    - **Total State**: 128 bits
    
    **Key and IV**:
    
    - **Key Size**: 128 bits
    - **IV Size**: 128 bits (key and IV are the same size)
    - **Total State**: 128 bits
    
    **Example Usage**:
    
        >>> from lfsr.ciphers.lili128 import LILI128
        >>> cipher = LILI128()
        >>> key = [1] * 128
        >>> iv = [0] * 128
        >>> keystream = cipher.generate_keystream(key, iv, 100)
    """
    
    LFSRC_SIZE = 39  # Clock control LFSR
    LFSRD_SIZE = 89  # Data LFSR
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
            iv_size=128,
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
    
    def _get_clock_control_value(self) -> int:
        """
        Get clock control value from LFSRc.
        
        The clock control value determines how many times LFSRd advances.
        In LILI-128, this is based on two bits from LFSRc.
        """
        # LILI-128 uses bits 12 and 20 from LFSRc
        bit12 = self.lfsrc_state[12]
        bit20 = self.lfsrc_state[20]
        
        # Clock control value: 1 + (2*bit12 + bit20)
        # This gives values 1, 2, 3, or 4
        return 1 + (2 * bit12 + bit20)
    
    def _get_output_bit(self) -> int:
        """Get output bit from LILI-128."""
        # Output is from LFSRd (data LFSR)
        # LILI-128 uses a filter function on LFSRd output
        # Simplified: use MSB of LFSRd
        return self.lfsrd_state[0]
    
    def _clock(self):
        """Clock LILI-128 (clock control mechanism)."""
        # Clock LFSRc (clock control LFSR)
        lfsrc_taps = [38, 35, 33, 31, 27, 26, 25, 24, 23, 21, 19, 12, 11, 10, 9, 7, 5, 3, 2, 1, 0]
        self.lfsrc_state = self._clock_lfsr(
            self.lfsrc_state,
            lfsrc_taps,
            self.LFSRC_SIZE
        )
        
        # Get clock control value
        clock_steps = self._get_clock_control_value()
        
        # Clock LFSRd (data LFSR) clock_steps times
        lfsrd_taps = [88, 83, 82, 80, 78, 76, 75, 74, 73, 72, 71, 70, 69, 68, 67, 66, 65, 64, 63, 62, 61, 60, 59, 58, 57, 56, 55, 54, 53, 52, 51, 50, 49, 48, 47, 46, 45, 44, 43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
        for _ in range(clock_steps):
            self.lfsrd_state = self._clock_lfsr(
                self.lfsrd_state,
                lfsrd_taps,
                self.LFSRD_SIZE
            )
    
    def _initialize(self, key: List[int], iv: Optional[List[int]]):
        """Initialize LILI-128 with key and IV."""
        if len(key) != 128:
            raise ValueError(f"LILI-128 requires 128-bit key, got {len(key)} bits")
        
        if iv is None:
            iv = [0] * 128
        elif len(iv) != 128:
            raise ValueError(f"LILI-128 requires 128-bit IV, got {len(iv)} bits")
        
        # Initialize LFSRc (clock control): first 39 bits of key
        self.lfsrc_state = key[0:39]
        
        # Initialize LFSRd (data): next 89 bits of key
        self.lfsrd_state = key[39:128]
        
        # Mix in IV
        for i in range(128):
            if i < 39:
                self.lfsrc_state[i] ^= iv[i]
            if i < 89:
                self.lfsrd_state[i] ^= iv[i + 39] if i + 39 < 128 else 0
        
        # Warm-up phase
        for _ in range(self.WARMUP_STEPS):
            self._clock()
            self._get_output_bit()  # Discard output
    
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
            self._clock()
            output = self._get_output_bit()
            keystream.append(output)
        
        return keystream
    
    def analyze_structure(self) -> CipherStructure:
        """Analyze LILI-128 cipher structure."""
        # Build LFSR configurations
        # LFSRc: 39 bits
        lfsrc_coeffs = [1] + [0] * 38  # Simplified
        lfsrc_coeffs[0] = 1
        lfsrc_coeffs[1] = 1
        lfsrc_coeffs[2] = 1
        # ... (full polynomial is complex)
        
        # LFSRd: 89 bits
        lfsrd_coeffs = [1] + [0] * 88  # Simplified
        lfsrd_coeffs[0] = 1
        # ... (full polynomial is complex)
        
        lfsrc_config = LFSRConfig(coefficients=lfsrc_coeffs, field_order=2, degree=39)
        lfsrd_config = LFSRConfig(coefficients=lfsrd_coeffs, field_order=2, degree=89)
        
        return CipherStructure(
            lfsr_configs=[lfsrc_config, lfsrd_config],
            clock_control=(
                "LFSRc (clock control) determines how many times LFSRd advances. "
                "Clock control value = 1 + (2*LFSRc[12] + LFSRc[20]), "
                "giving values 1, 2, 3, or 4."
            ),
            combiner="Output from LFSRd (data LFSR) with filter function",
            state_size=128,
            details={
                'lfsrc_size': 39,
                'lfsrd_size': 89,
                'total_size': 128,
                'warmup_steps': self.WARMUP_STEPS,
                'clock_control_range': '1-4 steps per clock',
                'note': 'LILI-128 demonstrates clock-controlled LFSR design'
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
                'Known-plaintext attacks'
            ],
            'security_status': 'Vulnerable, educational example'
        }
