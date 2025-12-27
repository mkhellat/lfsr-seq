#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Trivium Stream Cipher Analysis

This module provides analysis capabilities for the Trivium stream cipher, which
is an eSTREAM finalist. Trivium uses three shift registers with non-linear
feedback, making it more than just LFSRs.

**Historical Context**:

Trivium was designed as part of the eSTREAM project (European stream cipher
project) and was selected as a finalist in the hardware category. Trivium is
designed for efficient hardware implementation with a simple, elegant design.

**Security Status**:

Trivium is considered secure and is widely analyzed. It has withstood extensive
cryptanalysis and remains a strong candidate for hardware-optimized stream
ciphers.

**Key Terminology**:

- **Trivium**: eSTREAM finalist stream cipher
- **eSTREAM**: European stream cipher project
- **Shift Register**: Generalization of LFSR (allows non-linear feedback)
- **Non-Linear Feedback**: Feedback function is not linear
- **Hardware Efficiency**: Optimized for hardware implementation
- **Three Registers**: Uses three shift registers (not pure LFSRs)

**Mathematical Foundation**:

Trivium uses three shift registers:
- Register 1: 93 bits
- Register 2: 84 bits
- Register 3: 111 bits
- Total: 288 bits

The feedback is non-linear, involving AND operations between register bits,
making it more complex than simple LFSRs.
"""

from typing import List, Optional

from sage.all import *

from lfsr.attacks import LFSRConfig
from lfsr.ciphers.base import (
    StreamCipher,
    CipherConfig,
    CipherStructure
)


class Trivium(StreamCipher):
    """
    Trivium stream cipher implementation.
    
    Trivium is an eSTREAM finalist designed for efficient hardware
    implementation. It uses three shift registers with non-linear feedback.
    
    **Cipher Structure**:
    
    - **Register 1**: 93 bits
    - **Register 2**: 84 bits
    - **Register 3**: 111 bits
    - **Total State**: 288 bits
    - **Feedback**: Non-linear (AND operations)
    - **Output**: XOR of specific register bits
    
    **Key and IV**:
    
    - **Key Size**: 80 bits
    - **IV Size**: 80 bits
    - **Security**: 80-bit security
    
    **Example Usage**:
    
        >>> from lfsr.ciphers.trivium import Trivium
        >>> cipher = Trivium()
        >>> key = [1] * 80
        >>> iv = [0] * 80
        >>> keystream = cipher.generate_keystream(key, iv, 100)
    """
    
    # Trivium register sizes
    REG1_SIZE = 93
    REG2_SIZE = 84
    REG3_SIZE = 111
    TOTAL_SIZE = 288
    
    # Warm-up steps
    WARMUP_STEPS = 1152  # 4 * 288
    
    def __init__(self):
        """Initialize Trivium cipher."""
        self.reg1 = None
        self.reg2 = None
        self.reg3 = None
    
    def get_config(self) -> CipherConfig:
        """Get Trivium cipher configuration."""
        return CipherConfig(
            cipher_name="Trivium",
            key_size=80,
            iv_size=80,
            description="Trivium eSTREAM finalist with 3 shift registers and non-linear feedback",
            parameters={
                'reg1_size': self.REG1_SIZE,
                'reg2_size': self.REG2_SIZE,
                'reg3_size': self.REG3_SIZE,
                'total_size': self.TOTAL_SIZE,
                'warmup_steps': self.WARMUP_STEPS
            }
        )
    
    def _clock_register(self, reg: List[int], size: int, 
                       feedback_taps: List[int], and_taps: List[int]) -> List[int]:
        """
        Clock a Trivium register with non-linear feedback.
        
        Args:
            reg: Current register state
            size: Register size
            feedback_taps: Tap positions for feedback XOR
            and_taps: Tap positions for AND operation
        
        Returns:
            New register state
        """
        # Compute non-linear feedback (AND of specific bits)
        and_result = 1
        for tap in and_taps:
            and_result &= reg[tap]
        
        # Compute linear feedback (XOR of specific bits)
        xor_result = 0
        for tap in feedback_taps:
            xor_result ^= reg[tap]
        
        # Combine: AND result XORed with XOR result
        feedback = and_result ^ xor_result
        
        # Shift and insert feedback
        return [feedback] + reg[:-1]
    
    def _get_output_bit(self) -> int:
        """Get output bit from Trivium."""
        # Output is XOR of specific register bits
        o1 = self.reg1[65] ^ self.reg1[92]
        o2 = self.reg2[68] ^ self.reg2[83]
        o3 = self.reg3[65] ^ self.reg3[110]
        
        return o1 ^ o2 ^ o3
    
    def _clock_all(self):
        """Clock all Trivium registers."""
        # Register 1: feedback from bits 68, 65, and AND of 90, 91
        self.reg1 = self._clock_register(
            self.reg1, self.REG1_SIZE,
            feedback_taps=[68, 65],
            and_taps=[90, 91]
        )
        
        # Register 2: feedback from bits 77, 68, and AND of 81, 82
        self.reg2 = self._clock_register(
            self.reg2, self.REG2_SIZE,
            feedback_taps=[77, 68],
            and_taps=[81, 82]
        )
        
        # Register 3: feedback from bits 86, 65, and AND of 108, 109
        self.reg3 = self._clock_register(
            self.reg3, self.REG3_SIZE,
            feedback_taps=[86, 65],
            and_taps=[108, 109]
        )
    
    def _initialize(self, key: List[int], iv: Optional[List[int]]):
        """Initialize Trivium with key and IV."""
        if len(key) != 80:
            raise ValueError(f"Trivium requires 80-bit key, got {len(key)} bits")
        
        if iv is None:
            iv = [0] * 80
        elif len(iv) != 80:
            raise ValueError(f"Trivium requires 80-bit IV, got {len(iv)} bits")
        
        # Initialize registers
        # Register 1: key (80 bits) + 13 zeros
        self.reg1 = key + [0] * 13
        
        # Register 2: IV (80 bits) + 4 zeros
        self.reg2 = iv + [0] * 4
        
        # Register 3: 111 bits, last 3 are 1
        self.reg3 = [0] * 108 + [1, 1, 1]
        
        # Warm-up phase: run 1152 steps without output
        for _ in range(self.WARMUP_STEPS):
            self._clock_all()
    
    def generate_keystream(
        self,
        key: List[int],
        iv: Optional[List[int]],
        length: int
    ) -> List[int]:
        """
        Generate Trivium keystream.
        
        Args:
            key: 80-bit secret key
            iv: 80-bit initialization vector, or None
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
        """Analyze Trivium cipher structure."""
        # Note: Trivium uses shift registers, not pure LFSRs
        # We create placeholder LFSR configs for structure analysis
        reg1_config = LFSRConfig(coefficients=[1] * 93, field_order=2, degree=93)
        reg2_config = LFSRConfig(coefficients=[1] * 84, field_order=2, degree=84)
        reg3_config = LFSRConfig(coefficients=[1] * 111, field_order=2, degree=111)
        
        return CipherStructure(
            lfsr_configs=[reg1_config, reg2_config, reg3_config],
            clock_control="All registers clock every step",
            combiner="XOR of specific register bits (non-linear feedback in registers)",
            state_size=288,
            details={
                'reg1_size': 93,
                'reg2_size': 84,
                'reg3_size': 111,
                'total_size': 288,
                'warmup_steps': self.WARMUP_STEPS,
                'note': 'Uses shift registers with non-linear feedback, not pure LFSRs'
            }
        )
    
    def apply_attacks(
        self,
        keystream: List[int],
        attack_types: Optional[List[str]] = None
    ) -> dict:
        """Apply attacks to Trivium keystream."""
        return {
            'note': 'Trivium is considered secure and has withstood extensive cryptanalysis',
            'known_vulnerabilities': [],
            'security_status': 'Secure'
        }
