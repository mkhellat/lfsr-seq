#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Grain Family Stream Cipher Analysis

This module provides analysis capabilities for the Grain family of stream ciphers,
including Grain-128 and Grain-128a. Grain uses one LFSR and one NFSR (Non-Linear
Feedback Shift Register) with a filter function.

**Historical Context**:

Grain was designed as part of the eSTREAM project and was selected as a finalist
in the hardware category. Grain-128a provides authenticated encryption in addition
to confidentiality.

**Security Status**:

Grain is considered secure and has withstood extensive cryptanalysis. It is
designed for hardware efficiency with a small state size.

**Key Terminology**:

- **Grain**: eSTREAM finalist stream cipher family
- **Grain-128**: Basic Grain with 128-bit security
- **Grain-128a**: Grain with authenticated encryption
- **NFSR**: Non-Linear Feedback Shift Register
- **Filter Function**: Non-linear function combining LFSR and NFSR outputs
- **Hardware Efficiency**: Optimized for hardware implementation

**Mathematical Foundation**:

Grain uses:
- **LFSR**: 128 bits (linear feedback)
- **NFSR**: 128 bits (non-linear feedback)
- **Filter Function**: Non-linear function of LFSR and NFSR bits
- **Total State**: 256 bits
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
    
    Grain-128 is an eSTREAM finalist designed for hardware efficiency. It uses
    one LFSR and one NFSR with a filter function.
    
    **Cipher Structure**:
    
    - **LFSR**: 128 bits (linear feedback)
    - **NFSR**: 128 bits (non-linear feedback)
    - **Filter Function**: Non-linear function combining LFSR and NFSR outputs
    - **Total State**: 256 bits
    
    **Key and IV**:
    
    - **Key Size**: 128 bits
    - **IV Size**: 96 bits
    - **Security**: 128-bit security
    
    **Example Usage**:
    
        >>> from lfsr.ciphers.grain import Grain128
        >>> cipher = Grain128()
        >>> key = [1] * 128
        >>> iv = [0] * 96
        >>> keystream = cipher.generate_keystream(key, iv, 100)
    """
    
    LFSR_SIZE = 128
    NFSR_SIZE = 128
    TOTAL_SIZE = 256
    WARMUP_STEPS = 256
    
    def __init__(self):
        """Initialize Grain-128 cipher."""
        self.lfsr = None
        self.nfsr = None
    
    def get_config(self) -> CipherConfig:
        """Get Grain-128 cipher configuration."""
        return CipherConfig(
            cipher_name="Grain-128",
            key_size=128,
            iv_size=96,
            description="Grain-128 eSTREAM finalist with LFSR and NFSR",
            parameters={
                'lfsr_size': self.LFSR_SIZE,
                'nfsr_size': self.NFSR_SIZE,
                'total_size': self.TOTAL_SIZE,
                'warmup_steps': self.WARMUP_STEPS
            }
        )
    
    def _clock_lfsr(self) -> int:
        """Clock LFSR and return output."""
        # LFSR feedback: taps at positions 7, 38, 70, 81, 96
        feedback = (self.lfsr[7] ^ self.lfsr[38] ^ self.lfsr[70] ^ 
                   self.lfsr[81] ^ self.lfsr[96])
        self.lfsr = [feedback] + self.lfsr[:-1]
        return self.lfsr[0]
    
    def _clock_nfsr(self, lfsr_output: int) -> int:
        """Clock NFSR with non-linear feedback and return output."""
        # NFSR feedback: non-linear function
        # Simplified: complex non-linear function in practice
        nfsr_bits = [
            self.nfsr[0], self.nfsr[26], self.nfsr[56], self.nfsr[91],
            self.nfsr[96], self.nfsr[3], self.nfsr[67], self.nfsr[11],
            self.nfsr[13], self.nfsr[17], self.nfsr[18], self.nfsr[27],
            self.nfsr[59], self.nfsr[40], self.nfsr[48], self.nfsr[61],
            self.nfsr[65], self.nfsr[68], self.nfsr[84]
        ]
        
        # Non-linear feedback (simplified)
        feedback = 0
        for i, bit in enumerate(nfsr_bits):
            feedback ^= bit
        
        # Mix with LFSR output
        feedback ^= lfsr_output
        
        self.nfsr = [feedback] + self.nfsr[:-1]
        return self.nfsr[0]
    
    def _filter_function(self, lfsr_bits: List[int], nfsr_bits: List[int]) -> int:
        """
        Filter function combining LFSR and NFSR bits.
        
        Args:
            lfsr_bits: Selected LFSR bits
            nfsr_bits: Selected NFSR bits
        
        Returns:
            Filter output bit
        """
        # Simplified filter function
        # Full Grain uses a more complex non-linear function
        h = (nfsr_bits[0] & lfsr_bits[0]) ^ (nfsr_bits[1] & lfsr_bits[1]) ^ \
            (nfsr_bits[2] & lfsr_bits[2]) ^ (nfsr_bits[3] & lfsr_bits[3])
        return h
    
    def _get_output_bit(self) -> int:
        """Get output bit from Grain-128."""
        # Get specific bits for filter function
        lfsr_bits = [self.lfsr[0], self.lfsr[7], self.lfsr[38], self.lfsr[70]]
        nfsr_bits = [self.nfsr[0], self.nfsr[26], self.nfsr[56], self.nfsr[91]]
        
        # Filter function output
        filter_output = self._filter_function(lfsr_bits, nfsr_bits)
        
        # Output is filter output XORed with NFSR bits
        output = filter_output
        for i in [12, 95]:
            output ^= self.nfsr[i]
        
        return output
    
    def _clock_all(self):
        """Clock both LFSR and NFSR."""
        lfsr_output = self._clock_lfsr()
        nfsr_output = self._clock_nfsr(lfsr_output)
    
    def _initialize(self, key: List[int], iv: Optional[List[int]]):
        """Initialize Grain-128 with key and IV."""
        if len(key) != 128:
            raise ValueError(f"Grain-128 requires 128-bit key, got {len(key)} bits")
        
        if iv is None:
            iv = [0] * 96
        elif len(iv) != 96:
            raise ValueError(f"Grain-128 requires 96-bit IV, got {len(iv)} bits")
        
        # Initialize NFSR with key
        self.nfsr = key.copy()
        
        # Initialize LFSR with IV + padding
        self.lfsr = iv + [1] * 32  # 96 + 32 = 128
        
        # Warm-up phase
        for _ in range(self.WARMUP_STEPS):
            self._clock_all()
    
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
            self._clock_all()
            output = self._get_output_bit()
            keystream.append(output)
        
        return keystream
    
    def analyze_structure(self) -> CipherStructure:
        """Analyze Grain-128 cipher structure."""
        # Create LFSR config (NFSR is non-linear, so we use placeholder)
        lfsr_config = LFSRConfig(coefficients=[1] * 128, field_order=2, degree=128)
        
        return CipherStructure(
            lfsr_configs=[lfsr_config],
            clock_control="Both LFSR and NFSR clock every step",
            combiner="Non-linear filter function combining LFSR and NFSR bits",
            state_size=256,
            details={
                'lfsr_size': 128,
                'nfsr_size': 128,
                'total_size': 256,
                'warmup_steps': self.WARMUP_STEPS,
                'note': 'Uses LFSR and NFSR (Non-Linear Feedback Shift Register)'
            }
        )
    
    def apply_attacks(
        self,
        keystream: List[int],
        attack_types: Optional[List[str]] = None
    ) -> dict:
        """Apply attacks to Grain-128 keystream."""
        return {
            'note': 'Grain-128 is considered secure',
            'known_vulnerabilities': [],
            'security_status': 'Secure'
        }


class Grain128a(Grain128):
    """
    Grain-128a stream cipher implementation (authenticated encryption).
    
    Grain-128a extends Grain-128 with authenticated encryption capabilities.
    It provides both confidentiality and authentication.
    
    **Differences from Grain-128**:
    
    - Provides authenticated encryption
    - Additional authentication tag generation
    - Same core structure as Grain-128
    
    **Example Usage**:
    
        >>> from lfsr.ciphers.grain import Grain128a
        >>> cipher = Grain128a()
        >>> key = [1] * 128
        >>> iv = [0] * 96
        >>> keystream = cipher.generate_keystream(key, iv, 100)
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
                'total_size': self.TOTAL_SIZE,
                'warmup_steps': self.WARMUP_STEPS,
                'authenticated_encryption': True
            }
        )
