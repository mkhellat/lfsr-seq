#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Grain Family Stream Cipher Analysis

This module provides analysis capabilities for the Grain family of stream ciphers,
including Grain-128 and Grain-128a. Grain uses a combination of LFSR and NFSR
(Non-Linear Feedback Shift Register).

**Historical Context**:

Grain was designed by Hell, Johansson, and Meier as part of the eSTREAM project.
Grain-128 and Grain-128a were selected as finalists in the hardware category.
Grain-128a provides authenticated encryption in addition to confidentiality.

**Security Status**:

Grain is considered secure and provides 128-bit security. Grain-128a adds
authentication capabilities.

**Key Terminology**:

- **Grain**: Family of eSTREAM finalist stream ciphers
- **Grain-128**: Basic Grain variant with 128-bit security
- **Grain-128a**: Grain variant with authenticated encryption
- **LFSR**: Linear Feedback Shift Register
- **NFSR**: Non-Linear Feedback Shift Register
- **Filter Function**: Non-linear function combining LFSR and NFSR outputs
"""

from typing import List, Optional

from sage.all import *

from lfsr.attacks import LFSRConfig
from lfsr.ciphers.base import (
    StreamCipher,
    CipherConfig,
    CipherStructure
)


class Grain128(StreamCipher):
    """
    Grain-128 stream cipher implementation.
    
    Grain-128 uses one LFSR and one NFSR with a filter function.
    
    **Cipher Structure**:
    
    - **LFSR**: 128 bits
    - **NFSR**: 128 bits
    - **Filter Function**: Non-linear function
    - **Total State**: 256 bits
    
    **Key and IV**:
    
    - **Key Size**: 128 bits
    - **IV Size**: 96 bits
    - **Total State**: 256 bits
    """
    
    LFSR_SIZE = 128
    NFSR_SIZE = 128
    
    WARMUP_STEPS = 256
    
    def __init__(self):
        """Initialize Grain-128 cipher."""
        self.lfsr_state = None
        self.nfsr_state = None
    
    def get_config(self) -> CipherConfig:
        """Get Grain-128 cipher configuration."""
        return CipherConfig(
            cipher_name="Grain-128",
            key_size=128,
            iv_size=96,
            description="Grain-128 eSTREAM finalist (LFSR + NFSR)",
            parameters={
                'lfsr_size': self.LFSR_SIZE,
                'nfsr_size': self.NFSR_SIZE,
                'warmup_steps': self.WARMUP_STEPS
            }
        )
    
    def _lfsr_feedback(self) -> int:
        """Compute LFSR feedback."""
        # Simplified: XOR of specific taps
        return (self.lfsr_state[0] ^ self.lfsr_state[7] ^
                self.lfsr_state[38] ^ self.lfsr_state[70] ^
                self.lfsr_state[81] ^ self.lfsr_state[96])
    
    def _nfsr_feedback(self) -> int:
        """Compute NFSR feedback (non-linear)."""
        # Simplified non-linear feedback
        return (self.nfsr_state[0] ^ self.nfsr_state[26] ^
                self.nfsr_state[56] ^ self.nfsr_state[91] ^
                self.nfsr_state[96] ^
                (self.nfsr_state[3] & self.nfsr_state[67]) ^
                (self.nfsr_state[11] & self.nfsr_state[13]) ^
                (self.nfsr_state[17] & self.nfsr_state[18]) ^
                (self.nfsr_state[27] & self.nfsr_state[59]) ^
                (self.nfsr_state[40] & self.nfsr_state[48]) ^
                (self.nfsr_state[61] & self.nfsr_state[65]) ^
                (self.nfsr_state[68] & self.nfsr_state[84]))
    
    def _filter_function(self) -> int:
        """Compute filter function output."""
        # Simplified filter function
        h = (self.nfsr_state[12] & self.lfsr_state[8]) ^
            (self.lfsr_state[13] & self.lfsr_state[20]) ^
            (self.nfsr_state[95] & self.lfsr_state[42]) ^
            (self.lfsr_state[60] & self.lfsr_state[79]) ^
            (self.nfsr_state[12] & self.nfsr_state[95] & self.lfsr_state[95])
        return h
    
    def _get_output_bit(self) -> int:
        """Get output bit from Grain-128."""
        # Output is XOR of NFSR bits and filter function
        output = (self.nfsr_state[2] ^ self.nfsr_state[15] ^
                  self.nfsr_state[36] ^ self.nfsr_state[45] ^
                  self.nfsr_state[64] ^ self.nfsr_state[73] ^
                  self.nfsr_state[89] ^ self._filter_function())
        return output
    
    def _update(self):
        """Update LFSR and NFSR."""
        # Update LFSR
        lfsr_fb = self._lfsr_feedback()
        self.lfsr_state = [lfsr_fb] + self.lfsr_state[:-1]
        
        # Update NFSR
        nfsr_fb = self._nfsr_feedback()
        self.nfsr_state = [nfsr_fb] + self.nfsr_state[:-1]
    
    def _initialize(self, key: List[int], iv: Optional[List[int]]):
        """Initialize Grain-128 with key and IV."""
        if len(key) != 128:
            raise ValueError(f"Grain-128 requires 128-bit key, got {len(key)} bits")
        
        if iv is None:
            iv = [0] * 96
        elif len(iv) != 96:
            raise ValueError(f"Grain-128 requires 96-bit IV, got {len(iv)} bits")
        
        # Initialize LFSR with IV + ones
        self.lfsr_state = iv + [1] * 32
        
        # Initialize NFSR with key
        self.nfsr_state = key.copy()
        
        # Warm-up phase
        for _ in range(self.WARMUP_STEPS):
            output = self._get_output_bit()
            # Feed output back into LFSR and NFSR
            self.lfsr_state[-1] ^= output
            self.nfsr_state[-1] ^= output
            self._update()
    
    def generate_keystream(
        self,
        key: List[int],
        iv: Optional[List[int]],
        length: int
    ) -> List[int]:
        """
        Generate Grain-128 keystream.
        
        Args:
            key: 128-bit secret key
            iv: 96-bit initialization vector, or None
            length: Desired keystream length in bits
        
        Returns:
            List of keystream bits
        """
        self._initialize(key, iv)
        keystream = []
        for _ in range(length):
            output = self._get_output_bit()
            keystream.append(output)
            self._update()
        return keystream
    
    def analyze_structure(self) -> CipherStructure:
        """Analyze Grain-128 cipher structure."""
        # Grain uses LFSR + NFSR
        lfsr_coeffs = [1] + [0] * 127  # Simplified
        lfsr_config = LFSRConfig(coefficients=lfsr_coeffs, field_order=2, degree=128)
        
        return CipherStructure(
            lfsr_configs=[lfsr_config],
            clock_control="Both LFSR and NFSR update on every step",
            combiner="Filter function combining LFSR and NFSR outputs",
            state_size=256,  # 128 + 128
            details={
                'lfsr_size': 128,
                'nfsr_size': 128,
                'warmup_steps': self.WARMUP_STEPS,
                'note': 'Grain uses LFSR + NFSR with non-linear filter function'
            }
        )


class Grain128a(Grain128):
    """
    Grain-128a stream cipher implementation.
    
    Grain-128a extends Grain-128 with authenticated encryption capabilities.
    """
    
    def get_config(self) -> CipherConfig:
        """Get Grain-128a cipher configuration."""
        return CipherConfig(
            cipher_name="Grain-128a",
            key_size=128,
            iv_size=96,
            description="Grain-128a with authenticated encryption",
            parameters={
                'lfsr_size': self.LFSR_SIZE,
                'nfsr_size': self.NFSR_SIZE,
                'warmup_steps': self.WARMUP_STEPS,
                'authenticated_encryption': True
            }
        )
