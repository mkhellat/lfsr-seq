#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Trivium Stream Cipher Analysis

This module provides analysis capabilities for the Trivium stream
cipher, which was an eSTREAM finalist in the hardware category.
Trivium uses three shift registers with non-linear feedback.

**Historical Context**:

Trivium was designed by Christophe De Cannière and Bart Preneel as
part of the eSTREAM project (2004-2008). It was selected as a
finalist in the hardware category for its simplicity and efficiency.
Trivium is designed for hardware implementation with minimal gate
count.

**Security Status**:

Trivium is considered secure and has been extensively analyzed:
- No practical attacks found
- Designed for 80-bit security
- Used in research and some applications
- Simple design makes analysis easier

**Key Terminology**:

- **Trivium**: eSTREAM finalist stream cipher
- **eSTREAM**: European stream cipher project (2004-2008)
- **Shift Register**: Generalization of LFSR (allows non-linear feedback)
- **Non-Linear Feedback**: Feedback function is not linear
- **Hardware Efficiency**: Optimized for hardware implementation
"""

from typing import List, Optional

from lfsr.sage_imports import *

from lfsr.attacks import LFSRConfig
from lfsr.ciphers.base import (
    StreamCipher,
    CipherConfig,
    CipherStructure
)


class Trivium(StreamCipher):
    """
    Trivium stream cipher implementation.
    
    Trivium uses three shift registers (not pure LFSRs) with non-linear
    feedback. The design is optimized for hardware efficiency.
    
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
    
    # Trivium register sizes
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
                'warmup_steps': self.WARMUP_STEPS
            }
        )
    
    def _clock_register(self, reg: List[int], size: int, feedback_func) -> List[int]:
        """
        Clock a register with non-linear feedback.
        
        Args:
            reg: Register state
            size: Register size
            feedback_func: Function computing feedback
        
        Returns:
            New register state
        """
        feedback = feedback_func(reg)
        return [feedback] + reg[:-1]
    
    def _get_output_bit(self) -> int:
        """Get output bit from Trivium."""
        # Output is XOR of specific register bits
        output_a = self.reg_a[65] ^ self.reg_a[92]
        output_b = self.reg_b[68] ^ self.reg_b[83]
        output_c = self.reg_c[65] ^ self.reg_c[110]
        
        return output_a ^ output_b ^ output_c
    
    def _clock_trivium(self):
        """Clock all three Trivium registers."""
        # Register A feedback (non-linear)
        t1 = self.reg_a[65] ^ self.reg_a[92]
        t2 = self.reg_a[90] & self.reg_a[91]
        feedback_a = t1 ^ t2 ^ self.reg_c[108]
        
        # Register B feedback (non-linear)
        t1 = self.reg_b[68] ^ self.reg_b[83]
        t2 = self.reg_b[81] & self.reg_b[82]
        feedback_b = t1 ^ t2 ^ self.reg_a[68]
        
        # Register C feedback (non-linear)
        t1 = self.reg_c[65] ^ self.reg_c[110]
        t2 = self.reg_c[108] & self.reg_c[109]
        feedback_c = t1 ^ t2 ^ self.reg_b[77]
        
        # Clock registers
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
        # Register A: key (80 bits) + zeros
        self.reg_a = key + [0] * (self.REG_A_SIZE - 80)
        
        # Register B: IV (80 bits) + zeros
        self.reg_b = iv + [0] * (self.REG_B_SIZE - 80)
        
        # Register C: zeros + three 1s at end
        self.reg_c = [0] * (self.REG_C_SIZE - 3) + [1, 1, 1]
        
        # Warm-up phase
        for _ in range(self.WARMUP_STEPS):
            self._clock_trivium()
    
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
            self._clock_trivium()
        
        return keystream
    
    def analyze_structure(self) -> CipherStructure:
        """Analyze Trivium cipher structure."""
        # Trivium doesn't use pure LFSRs, so we create placeholder configs
        # In practice, Trivium uses shift registers with non-linear feedback
        
        # Placeholder LFSR configs (Trivium doesn't use LFSRs)
        lfsr1_config = LFSRConfig(
            coefficients=[1] * 93,  # Placeholder
            field_order=2,
            degree=93
        )
        
        return CipherStructure(
            lfsr_configs=[lfsr1_config],  # Placeholder
            clock_control="All registers clock every step",
            combiner="Non-linear combining with AND operations in feedback",
            state_size=288,  # 93 + 84 + 111
            details={
                'reg_a_size': 93,
                'reg_b_size': 84,
                'reg_c_size': 111,
                'total_size': 288,
                'warmup_steps': self.WARMUP_STEPS,
                'note': 'Trivium uses shift registers with non-linear feedback, not pure LFSRs'
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
            'security_status': 'No practical attacks found'
        }
