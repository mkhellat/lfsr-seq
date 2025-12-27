#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Trivium Stream Cipher Analysis

This module provides analysis capabilities for the Trivium stream cipher, which
is an eSTREAM finalist designed for hardware efficiency. Trivium uses three
shift registers with non-linear feedback.

**Historical Context**:

Trivium was designed by De Cannière and Preneel as part of the eSTREAM project
(European stream cipher project). It was selected as a finalist in the hardware
category due to its simplicity and efficiency. Trivium uses non-linear feedback
shift registers (NFSRs) rather than pure LFSRs.

**Security Status**:

Trivium is considered secure and is widely analyzed. It provides 80-bit security
and is designed for hardware implementations.

**Key Terminology**:

- **Trivium**: eSTREAM finalist stream cipher
- **eSTREAM**: European stream cipher project
- **Shift Register**: Generalization of LFSR (allows non-linear feedback)
- **Non-Linear Feedback**: Feedback function is not linear
- **Hardware Efficiency**: Optimized for hardware implementation
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
    
    Trivium uses three shift registers (288 bits total) with non-linear feedback.
    The design is optimized for hardware efficiency.
    
    **Cipher Structure**:
    
    - **Register A**: 93 bits
    - **Register B**: 84 bits
    - **Register C**: 111 bits
    - **Total**: 288 bits
    - **Feedback**: Non-linear (AND operations)
    
    **Key and IV**:
    
    - **Key Size**: 80 bits
    - **IV Size**: 80 bits
    - **Total State**: 288 bits
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
            description="Trivium eSTREAM finalist with 3 shift registers",
            parameters={
                'reg_a_size': self.REG_A_SIZE,
                'reg_b_size': self.REG_B_SIZE,
                'reg_c_size': self.REG_C_SIZE,
                'total_size': self.TOTAL_SIZE,
                'warmup_steps': self.WARMUP_STEPS
            }
        )
    
    def _get_output_bit(self) -> int:
        """Get output bit from Trivium."""
        # Output is XOR of specific register bits
        output = (self.reg_a[65] ^ self.reg_a[92] ^
                  self.reg_b[68] ^ self.reg_b[83] ^
                  self.reg_c[65] ^ self.reg_c[110])
        return output
    
    def _update_registers(self):
        """Update all three registers with non-linear feedback."""
        # Register A feedback (non-linear)
        t1 = self.reg_a[65] ^ self.reg_a[92]
        t2 = self.reg_a[90] & self.reg_a[91]
        feedback_a = t1 ^ t2 ^ self.reg_c[108]
        
        # Register B feedback (non-linear)
        t3 = self.reg_b[68] ^ self.reg_b[83]
        t4 = self.reg_b[81] & self.reg_b[82]
        feedback_b = t3 ^ t4 ^ self.reg_a[77]
        
        # Register C feedback (non-linear)
        t5 = self.reg_c[65] ^ self.reg_c[110]
        t6 = self.reg_c[108] & self.reg_c[109]
        feedback_c = t5 ^ t6 ^ self.reg_b[86]
        
        # Shift registers
        self.reg_a = [feedback_a] + self.reg_a[:-1]
        self.reg_b = [feedback_b] + self.reg_b[:-1]
        self.reg_c = [feedback_c] + self.reg_c[:-1]
    
    def _initialize(self, key: List[int], iv: Optional[List[int]]):
        """Initialize Trivium with key and IV."""
        if len(key) != 80:
            raise ValueError(f"Trivium requires 80-bit key, got {len(key)} bits")
        
        if iv is None:
            iv = [0] * 80
        elif len(iv) != 80:
            raise ValueError(f"Trivium requires 80-bit IV, got {len(iv)} bits")
        
        # Initialize registers
        # Register A: key (80 bits) + zeros (13 bits)
        self.reg_a = key + [0] * 13
        
        # Register B: IV (80 bits) + zeros (4 bits)
        self.reg_b = iv + [0] * 4
        
        # Register C: zeros (108 bits) + ones (3 bits)
        self.reg_c = [0] * 108 + [1, 1, 1]
        
        # Warm-up phase
        for _ in range(self.WARMUP_STEPS):
            self._update_registers()
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
            output = self._get_output_bit()
            keystream.append(output)
            self._update_registers()
        return keystream
    
    def analyze_structure(self) -> CipherStructure:
        """Analyze Trivium cipher structure."""
        # Trivium doesn't use pure LFSRs, so we create placeholder configs
        # for structure analysis
        return CipherStructure(
            lfsr_configs=[],  # Trivium uses NFSRs, not LFSRs
            clock_control="All registers update on every step",
            combiner="XOR of specific register bits (non-linear feedback)",
            state_size=288,
            details={
                'reg_a_size': 93,
                'reg_b_size': 84,
                'reg_c_size': 111,
                'total_size': 288,
                'warmup_steps': self.WARMUP_STEPS,
                'note': 'Trivium uses non-linear feedback shift registers (NFSRs), not pure LFSRs'
            }
        )
