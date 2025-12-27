#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LILI-128 Stream Cipher Analysis

This module provides analysis capabilities for the LILI-128 stream cipher, which
is an academic design using two LFSRs with clock control.

**Historical Context**:

LILI-128 was designed by Dawson and Simpson as an academic stream cipher
demonstrating clock-controlled LFSR design. It uses one LFSR to control the
clocking of another LFSR.

**Security Status**:

LILI-128 is an academic design and has been analyzed. It demonstrates clock-
controlled LFSR design principles.

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
    
    LILI-128 uses two LFSRs where one controls the clocking of the other.
    
    **Cipher Structure**:
    
    - **LFSR1 (Clock Control)**: 39 bits
    - **LFSR2 (Data Generator)**: 89 bits
    - **Clock Control**: LFSR1 controls clocking of LFSR2
    - **Total State**: 128 bits
    
    **Key and IV**:
    
    - **Key Size**: 128 bits
    - **IV Size**: 128 bits (can be same as key)
    - **Total State**: 128 bits
    """
    
    LFSR1_SIZE = 39
    LFSR2_SIZE = 89
    
    WARMUP_STEPS = 256
    
    def __init__(self):
        """Initialize LILI-128 cipher."""
        self.lfsr1_state = None
        self.lfsr2_state = None
    
    def get_config(self) -> CipherConfig:
        """Get LILI-128 cipher configuration."""
        return CipherConfig(
            cipher_name="LILI-128",
            key_size=128,
            iv_size=128,
            description="LILI-128 academic design (2 LFSRs with clock control)",
            parameters={
                'lfsr1_size': self.LFSR1_SIZE,
                'lfsr2_size': self.LFSR2_SIZE,
                'warmup_steps': self.WARMUP_STEPS
            }
        )
    
    def _clock_lfsr1(self):
        """Clock LFSR1 (always advances)."""
        feedback = (self.lfsr1_state[0] ^ self.lfsr1_state[35] ^
                    self.lfsr1_state[36] ^ self.lfsr1_state[37] ^
                    self.lfsr1_state[38])
        self.lfsr1_state = [feedback] + self.lfsr1_state[:-1]
    
    def _clock_lfsr2(self):
        """Clock LFSR2 (data generator)."""
        feedback = (self.lfsr2_state[0] ^ self.lfsr2_state[51] ^
                    self.lfsr2_state[52] ^ self.lfsr2_state[53] ^
                    self.lfsr2_state[54] ^ self.lfsr2_state[55] ^
                    self.lfsr2_state[56] ^ self.lfsr2_state[57] ^
                    self.lfsr2_state[58] ^ self.lfsr2_state[59] ^
                    self.lfsr2_state[60] ^ self.lfsr2_state[61] ^
                    self.lfsr2_state[62] ^ self.lfsr2_state[63] ^
                    self.lfsr2_state[64] ^ self.lfsr2_state[65] ^
                    self.lfsr2_state[66] ^ self.lfsr2_state[67] ^
                    self.lfsr2_state[68] ^ self.lfsr2_state[69] ^
                    self.lfsr2_state[70] ^ self.lfsr2_state[71] ^
                    self.lfsr2_state[72] ^ self.lfsr2_state[73] ^
                    self.lfsr2_state[74] ^ self.lfsr2_state[75] ^
                    self.lfsr2_state[76] ^ self.lfsr2_state[77] ^
                    self.lfsr2_state[78] ^ self.lfsr2_state[79] ^
                    self.lfsr2_state[80] ^ self.lfsr2_state[81] ^
                    self.lfsr2_state[82] ^ self.lfsr2_state[83] ^
                    self.lfsr2_state[84] ^ self.lfsr2_state[85] ^
                    self.lfsr2_state[86] ^ self.lfsr2_state[87] ^
                    self.lfsr2_state[88])
        self.lfsr2_state = [feedback] + self.lfsr2_state[:-1]
    
    def _get_clock_control(self) -> int:
        """Get clock control value from LFSR1."""
        # Use two bits from LFSR1 to determine clocking
        return (self.lfsr1_state[12] << 1) | self.lfsr1_state[20]
    
    def _get_output_bit(self) -> int:
        """Get output bit from LILI-128."""
        return self.lfsr2_state[0]  # Output is MSB of LFSR2
    
    def _initialize(self, key: List[int], iv: Optional[List[int]]):
        """Initialize LILI-128 with key and IV."""
        if len(key) != 128:
            raise ValueError(f"LILI-128 requires 128-bit key, got {len(key)} bits")
        
        if iv is None:
            iv = key.copy()  # Use key as IV if not provided
        elif len(iv) != 128:
            raise ValueError(f"LILI-128 requires 128-bit IV, got {len(iv)} bits")
        
        # Initialize LFSR1 with first 39 bits of key
        self.lfsr1_state = key[0:39]
        
        # Initialize LFSR2 with remaining 89 bits of key
        self.lfsr2_state = key[39:128]
        
        # Warm-up phase
        for _ in range(self.WARMUP_STEPS):
            self._clock_lfsr1()
            clock_control = self._get_clock_control()
            # Clock LFSR2 based on control value
            for _ in range(clock_control + 1):
                self._clock_lfsr2()
    
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
            # Always clock LFSR1
            self._clock_lfsr1()
            
            # Clock LFSR2 based on control value
            clock_control = self._get_clock_control()
            for _ in range(clock_control + 1):
                self._clock_lfsr2()
            
            # Get output
            output = self._get_output_bit()
            keystream.append(output)
        
        return keystream
    
    def analyze_structure(self) -> CipherStructure:
        """Analyze LILI-128 cipher structure."""
        # Build LFSR configurations
        lfsr1_coeffs = [1] + [0] * 34 + [1, 1, 1, 1]
        lfsr2_coeffs = [1] + [0] * 50 + [1] * 38
        
        lfsr1_config = LFSRConfig(coefficients=lfsr1_coeffs, field_order=2, degree=39)
        lfsr2_config = LFSRConfig(coefficients=lfsr2_coeffs, field_order=2, degree=89)
        
        return CipherStructure(
            lfsr_configs=[lfsr1_config, lfsr2_config],
            clock_control="LFSR1 controls clocking of LFSR2 (irregular clocking)",
            combiner="Output is MSB of LFSR2",
            state_size=128,  # 39 + 89
            details={
                'lfsr1_size': 39,
                'lfsr2_size': 89,
                'clock_control_bits': [12, 20],
                'warmup_steps': self.WARMUP_STEPS
            }
        )
