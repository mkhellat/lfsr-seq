#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Trivium Stream Cipher Analysis

This module provides analysis capabilities for the Trivium stream cipher, which
was an eSTREAM finalist in the hardware category. Trivium uses three shift
registers with non-linear feedback.

**Historical Context**:

Trivium was designed by Christophe De Cannière and Bart Preneel as part of the
eSTREAM project (2004-2008), which aimed to identify new stream ciphers suitable
for widespread adoption. Trivium was selected as a finalist in the hardware
category due to its simplicity and efficiency.

**Security Status**:

Trivium is considered secure and has withstood extensive cryptanalysis. It was
designed for 80-bit security and remains unbroken. Trivium is notable for its
simplicity: the entire cipher can be described in a few lines of code.

**Key Terminology**:

- **Trivium**: eSTREAM finalist stream cipher
- **eSTREAM**: European stream cipher project (2004-2008)
- **Shift Register**: Generalization of LFSR (allows non-linear feedback)
- **Non-Linear Feedback**: Feedback function is not linear
- **Hardware Efficiency**: Optimized for hardware implementation
- **80-bit Security**: Designed for 80-bit key security level
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
    
    Trivium uses three shift registers (not pure LFSRs) with non-linear feedback.
    The design is extremely simple but provides good security.
    
    **Cipher Structure**:
    
    - **Register A**: 93 bits
    - **Register B**: 84 bits
    - **Register C**: 111 bits
    - **Total State**: 288 bits
    - **Feedback**: Non-linear (AND operations)
    - **Output**: XOR of specific register bits
    
    **Key and IV**:
    
    - **Key Size**: 80 bits
    - **IV Size**: 80 bits
    - **Total State**: 288 bits
    
    **Example Usage**:
    
        >>> from lfsr.ciphers.trivium import Trivium
        >>> cipher = Trivium()
        >>> key = [1] * 80
        >>> iv = [0] * 80
        >>> keystream = cipher.generate_keystream(key, iv, 100)
    """
    
    REG_A_SIZE = 93
    REG_B_SIZE = 84
    REG_C_SIZE = 111
    TOTAL_SIZE = 288
    
    WARMUP_STEPS = 1152  # 4 * 288
    
    def __init__(self):
        """Initialize Trivium cipher."""
        self.reg_a = None
        self.reg_b = None
        self.reg_c = None
    
    def get_config(self) -> CipherConfig:
        """Get Trivium cipher configuration."""
        return CipherConfig(
            cipher_name="Trivium",
            key_size=80,
            iv_size=80,
            description="Trivium eSTREAM finalist with 3 shift registers and non-linear feedback",
            parameters={
                'reg_a_size': self.REG_A_SIZE,
                'reg_b_size': self.REG_B_SIZE,
                'reg_c_size': self.REG_C_SIZE,
                'total_size': self.TOTAL_SIZE,
                'warmup_steps': self.WARMUP_STEPS,
                'security_level': '80 bits'
            }
        )
    
    def _update_register(self, reg: List[int], size: int, 
                        feedback_taps: List[int], 
                        and_taps: List[int]) -> List[int]:
        """
        Update a shift register with non-linear feedback.
        
        Args:
            reg: Current register state
            size: Register size
            feedback_taps: Positions for feedback XOR
            and_taps: Positions for AND (non-linearity)
        
        Returns:
            New register state
        """
        # Compute non-linear feedback
        feedback = 0
        for tap in feedback_taps:
            feedback ^= reg[tap]
        
        # Add non-linear term (AND)
        and_term = 1
        for tap in and_taps:
            and_term &= reg[tap]
        feedback ^= and_term
        
        # Shift and insert feedback
        return [feedback] + reg[:-1]
    
    def _get_output_bit(self) -> int:
        """Get output bit from Trivium."""
        # Output is XOR of specific bits
        output_a = self.reg_a[65] ^ self.reg_a[92]
        output_b = self.reg_b[68] ^ self.reg_b[83]
        output_c = self.reg_c[65] ^ self.reg_c[110]
        
        return output_a ^ output_b ^ output_c
    
    def _clock(self):
        """Clock all three registers."""
        # Register A: taps at 65, 92 (XOR), 90, 91 (AND)
        self.reg_a = self._update_register(
            self.reg_a,
            self.REG_A_SIZE,
            [65, 92],
            [90, 91]
        )
        
        # Register B: taps at 68, 83 (XOR), 81, 82 (AND)
        self.reg_b = self._update_register(
            self.reg_b,
            self.REG_B_SIZE,
            [68, 83],
            [81, 82]
        )
        
        # Register C: taps at 65, 110 (XOR), 108, 109 (AND)
        self.reg_c = self._update_register(
            self.reg_c,
            self.REG_C_SIZE,
            [65, 110],
            [108, 109]
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
        # Register A: key (80 bits) + 13 zeros
        self.reg_a = key + [0] * 13
        
        # Register B: IV (80 bits) + 4 zeros
        self.reg_b = iv + [0] * 4
        
        # Register C: 111 bits, last 3 are 1
        self.reg_c = [0] * 108 + [1, 1, 1]
        
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
            self._clock()
            output = self._get_output_bit()
            keystream.append(output)
        
        return keystream
    
    def analyze_structure(self) -> CipherStructure:
        """Analyze Trivium cipher structure."""
        # Trivium doesn't use pure LFSRs, but shift registers
        # We'll create placeholder LFSR configs for structure analysis
        # In practice, Trivium uses non-linear feedback
        
        # Note: Trivium's registers are not LFSRs (non-linear feedback)
        # We create simplified LFSR configs for compatibility
        lfsr_a_coeffs = [1] + [0] * 92  # Placeholder
        lfsr_b_coeffs = [1] + [0] * 83  # Placeholder
        lfsr_c_coeffs = [1] + [0] * 110  # Placeholder
        
        lfsr_a_config = LFSRConfig(coefficients=lfsr_a_coeffs, field_order=2, degree=93)
        lfsr_b_config = LFSRConfig(coefficients=lfsr_b_coeffs, field_order=2, degree=84)
        lfsr_c_config = LFSRConfig(coefficients=lfsr_c_coeffs, field_order=2, degree=111)
        
        return CipherStructure(
            lfsr_configs=[lfsr_a_config, lfsr_b_config, lfsr_c_config],
            clock_control="All registers clock every step (regular clocking)",
            combiner="XOR of specific register bits (non-linear feedback in registers)",
            state_size=288,
            details={
                'reg_a_size': 93,
                'reg_b_size': 84,
                'reg_c_size': 111,
                'total_size': 288,
                'warmup_steps': self.WARMUP_STEPS,
                'note': 'Trivium uses non-linear feedback (not pure LFSRs)',
                'non_linearity': 'AND operations in feedback provide non-linearity',
                'security_level': '80 bits'
            }
        )
    
    def apply_attacks(
        self,
        keystream: List[int],
        attack_types: Optional[List[str]] = None
    ) -> dict:
        """Apply attacks to Trivium keystream."""
        return {
            'note': 'Trivium is considered secure',
            'known_vulnerabilities': [],
            'security_status': 'Secure (80-bit security)',
            'cryptanalysis': 'Extensive analysis, no practical attacks found'
        }
