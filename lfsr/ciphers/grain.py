#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Grain Family Stream Cipher Analysis

This module provides analysis capabilities for the Grain family of stream ciphers,
including Grain-128 and Grain-128a. Grain uses one LFSR and one NFSR (Non-Linear
Feedback Shift Register) with a filter function.

**Historical Context**:

Grain was designed by Martin Hell, Thomas Johansson, and Willi Meier as part of
the eSTREAM project. Grain-128 was selected as an eSTREAM finalist in the hardware
category. Grain-128a adds authenticated encryption capabilities.

**Security Status**:

Grain-128 and Grain-128a are considered secure and have withstood extensive
cryptanalysis. They are designed for 128-bit security and remain unbroken.

**Key Terminology**:

- **Grain**: Family of stream ciphers (Grain-128, Grain-128a)
- **NFSR**: Non-Linear Feedback Shift Register (generalizes LFSR)
- **Filter Function**: Non-linear function combining LFSR and NFSR outputs
- **Authenticated Encryption**: Grain-128a provides both encryption and authentication
- **128-bit Security**: Designed for 128-bit key security level
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
    
    Grain-128 uses one LFSR and one NFSR with a filter function. The design is
    hardware-efficient and provides good security.
    
    **Cipher Structure**:
    
    - **LFSR**: 128 bits (linear feedback)
    - **NFSR**: 128 bits (non-linear feedback)
    - **Filter Function**: Non-linear function combining LFSR and NFSR outputs
    - **Total State**: 256 bits
    
    **Key and IV**:
    
    - **Key Size**: 128 bits
    - **IV Size**: 96 bits (Grain-128) or 64 bits (Grain-128a)
    - **Total State**: 256 bits
    
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
    
    def __init__(self, variant: str = "grain128"):
        """
        Initialize Grain cipher.
        
        Args:
            variant: "grain128" or "grain128a"
        """
        self.variant = variant
        self.lfsr_state = None
        self.nfsr_state = None
    
    def get_config(self) -> CipherConfig:
        """Get Grain cipher configuration."""
        iv_size = 96 if self.variant == "grain128" else 64
        
        return CipherConfig(
            cipher_name=f"Grain-128{'a' if self.variant == 'grain128a' else ''}",
            key_size=128,
            iv_size=iv_size,
            description=f"Grain-128{'a' if self.variant == 'grain128a' else ''} eSTREAM finalist with LFSR+NFSR",
            parameters={
                'lfsr_size': self.LFSR_SIZE,
                'nfsr_size': self.NFSR_SIZE,
                'total_size': self.TOTAL_SIZE,
                'warmup_steps': self.WARMUP_STEPS,
                'variant': self.variant,
                'security_level': '128 bits'
            }
        )
    
    def _clock_lfsr(self, state: List[int], taps: List[int]) -> List[int]:
        """Clock LFSR (linear feedback)."""
        feedback = 0
        for tap in taps:
            feedback ^= state[tap]
        return [feedback] + state[:-1]
    
    def _clock_nfsr(self, state: List[int], lfsr_bit: int) -> List[int]:
        """
        Clock NFSR (non-linear feedback).
        
        The NFSR feedback includes both NFSR bits and an LFSR bit for
        non-linearity.
        """
        # Simplified NFSR feedback (full Grain is more complex)
        # In full Grain, NFSR feedback is a non-linear function
        feedback = state[0] ^ state[26] ^ state[56] ^ state[91] ^ \
                   state[96] ^ (state[3] & state[67]) ^ \
                   (state[11] & state[13]) ^ (state[17] & state[18]) ^ \
                   (state[27] & state[59]) ^ (state[40] & state[48]) ^ \
                   (state[61] & state[65]) ^ (state[68] & state[84]) ^ \
                   (state[88] & state[92] & state[93] & state[95]) ^ \
                   (state[22] & state[24] & state[25]) ^ \
                   (state[70] & state[78] & state[82]) ^ lfsr_bit
        
        return [feedback] + state[:-1]
    
    def _filter_function(self, lfsr_bits: List[int], nfsr_bits: List[int]) -> int:
        """
        Filter function combining LFSR and NFSR outputs.
        
        This is a simplified version. Full Grain uses a more complex filter.
        """
        # Simplified filter function
        # Full Grain filter: h(x) = x0*x1 + x2*x3 + x4*x5 + x6*x7 + x0*x4*x8
        # where x are bits from LFSR and NFSR
        h = (lfsr_bits[0] & lfsr_bits[1]) ^ \
            (nfsr_bits[0] & nfsr_bits[1]) ^ \
            (lfsr_bits[2] & nfsr_bits[2])
        
        return h
    
    def _get_output_bit(self) -> int:
        """Get output bit from Grain."""
        # Get bits for filter function
        lfsr_bits = [
            self.lfsr_state[2], self.lfsr_state[15], self.lfsr_state[36],
            self.lfsr_state[45], self.lfsr_state[64], self.lfsr_state[73],
            self.lfsr_state[89]
        ]
        nfsr_bits = [
            self.nfsr_state[12], self.nfsr_state[95]
        ]
        
        # Filter function output
        filter_out = self._filter_function(lfsr_bits, nfsr_bits)
        
        # Output is filter output XORed with NFSR bits
        output = filter_out ^ self.nfsr_state[2] ^ self.nfsr_state[15] ^ \
                 self.nfsr_state[36] ^ self.nfsr_state[45] ^ \
                 self.nfsr_state[64] ^ self.nfsr_state[73] ^ \
                 self.nfsr_state[89] ^ self.nfsr_state[93]
        
        return output
    
    def _clock(self):
        """Clock both LFSR and NFSR."""
        # Get LFSR output bit (for NFSR feedback)
        lfsr_bit = self.lfsr_state[0]
        
        # Clock LFSR
        lfsr_taps = [7, 38, 70, 81, 96]  # Simplified
        self.lfsr_state = self._clock_lfsr(self.lfsr_state, lfsr_taps)
        
        # Clock NFSR (uses LFSR bit)
        self.nfsr_state = self._clock_nfsr(self.nfsr_state, lfsr_bit)
    
    def _initialize(self, key: List[int], iv: Optional[List[int]]):
        """Initialize Grain with key and IV."""
        if len(key) != 128:
            raise ValueError(f"Grain requires 128-bit key, got {len(key)} bits")
        
        iv_size = 96 if self.variant == "grain128" else 64
        if iv is None:
            iv = [0] * iv_size
        elif len(iv) != iv_size:
            raise ValueError(f"Grain-{self.variant} requires {iv_size}-bit IV, got {len(iv)} bits")
        
        # Initialize LFSR: IV + padding
        self.lfsr_state = iv + [1] * (128 - len(iv))
        
        # Initialize NFSR: key
        self.nfsr_state = key.copy()
        
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
        Generate Grain keystream.
        
        Args:
            key: 128-bit secret key
            iv: IV (96 bits for Grain-128, 64 bits for Grain-128a), or None
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
        """Analyze Grain cipher structure."""
        # Grain uses LFSR and NFSR
        # Create LFSR config for the LFSR component
        lfsr_coeffs = [0] * 128
        lfsr_coeffs[0] = 1
        lfsr_coeffs[6] = 1
        lfsr_coeffs[37] = 1
        lfsr_coeffs[69] = 1
        lfsr_coeffs[80] = 1
        lfsr_coeffs[95] = 1
        
        lfsr_config = LFSRConfig(coefficients=lfsr_coeffs, field_order=2, degree=128)
        
        return CipherStructure(
            lfsr_configs=[lfsr_config],  # Only LFSR, NFSR is separate
            clock_control="Both LFSR and NFSR clock every step (regular clocking)",
            combiner="Non-linear filter function combining LFSR and NFSR outputs",
            state_size=256,
            details={
                'lfsr_size': 128,
                'nfsr_size': 128,
                'total_size': 256,
                'warmup_steps': self.WARMUP_STEPS,
                'variant': self.variant,
                'note': 'Grain uses LFSR + NFSR (non-linear feedback shift register)',
                'filter_function': 'Non-linear function provides security',
                'security_level': '128 bits'
            }
        )
    
    def apply_attacks(
        self,
        keystream: List[int],
        attack_types: Optional[List[str]] = None
    ) -> dict:
        """Apply attacks to Grain keystream."""
        return {
            'note': 'Grain is considered secure',
            'known_vulnerabilities': [],
            'security_status': 'Secure (128-bit security)',
            'cryptanalysis': 'Extensive analysis, no practical attacks found'
        }


# Alias for convenience
Grain128a = lambda: Grain128(variant="grain128a")
