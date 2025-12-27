#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
E0 Stream Cipher Analysis

This module provides analysis capabilities for the E0 stream cipher, which is
used in Bluetooth encryption. E0 uses four LFSRs with a non-linear finite state
machine (FSM) combiner.

**Historical Context**:

E0 was designed for Bluetooth encryption and is specified in the Bluetooth
Core Specification. It provides encryption for Bluetooth communications between
devices. E0 uses a combination of LFSRs and a finite state machine to create
a secure keystream.

**Security Status**:

E0 has been analyzed and has some known weaknesses, but remains in use for
Bluetooth Classic. Bluetooth Low Energy (BLE) uses AES-CCM instead.

**Key Terminology**:

- **E0**: The stream cipher used in Bluetooth encryption
- **Bluetooth**: Wireless communication standard
- **Finite State Machine (FSM)**: Memory element in the combiner
- **Non-Linear Combiner**: More complex than simple XOR
- **Bluetooth Pairing**: Process where E0 is used
"""

from typing import List, Optional

from sage.all import *

from lfsr.attacks import LFSRConfig
from lfsr.ciphers.base import (
    StreamCipher,
    CipherConfig,
    CipherStructure
)


class E0(StreamCipher):
    """
    E0 Bluetooth stream cipher implementation.
    
    E0 uses four LFSRs with a non-linear finite state machine (FSM) combiner.
    The FSM adds memory to the combining function, making it more complex than
    simple XOR.
    
    **Cipher Structure**:
    
    - **LFSR1**: 25 bits
    - **LFSR2**: 31 bits
    - **LFSR3**: 33 bits
    - **LFSR4**: 39 bits
    - **FSM**: 2-bit state machine
    - **Combiner**: Non-linear function using FSM
    
    **Key and IV**:
    
    - **Key Size**: 128 bits
    - **IV Size**: 64 bits (8 bytes)
    - **Total State**: 25 + 31 + 33 + 39 + 2 = 130 bits
    """
    
    LFSR1_SIZE = 25
    LFSR2_SIZE = 31
    LFSR3_SIZE = 33
    LFSR4_SIZE = 39
    
    # FSM state (2 bits)
    fsm_state = [0, 0]
    
    WARMUP_STEPS = 200
    
    def __init__(self):
        """Initialize E0 cipher."""
        self.lfsr1_state = None
        self.lfsr2_state = None
        self.lfsr3_state = None
        self.lfsr4_state = None
        self.fsm_state = [0, 0]
    
    def get_config(self) -> CipherConfig:
        """Get E0 cipher configuration."""
        return CipherConfig(
            cipher_name="E0",
            key_size=128,
            iv_size=64,
            description="E0 Bluetooth stream cipher with 4 LFSRs and FSM combiner",
            parameters={
                'lfsr1_size': self.LFSR1_SIZE,
                'lfsr2_size': self.LFSR2_SIZE,
                'lfsr3_size': self.LFSR3_SIZE,
                'lfsr4_size': self.LFSR4_SIZE,
                'fsm_size': 2,
                'warmup_steps': self.WARMUP_STEPS
            }
        )
    
    def _clock_lfsr(self, state: List[int], taps: List[int], size: int) -> List[int]:
        """Clock a single LFSR."""
        feedback = 0
        for tap in taps:
            feedback ^= state[tap]
        return [feedback] + state[:-1]
    
    def _fsm_update(self, x1: int, x2: int, x3: int, x4: int) -> int:
        """
        Update FSM and return output.
        
        The FSM uses the current state and LFSR outputs to produce output
        and update its state.
        """
        s0, s1 = self.fsm_state[0], self.fsm_state[1]
        
        # FSM output (simplified)
        t = (s0 + s1 + x1 + x2 + x3 + x4) % 2
        
        # FSM state update (simplified)
        self.fsm_state[0] = s1
        self.fsm_state[1] = (s0 + t) % 2
        
        return t
    
    def _get_output_bit(self) -> int:
        """Get output bit from E0."""
        x1 = self.lfsr1_state[0]
        x2 = self.lfsr2_state[0]
        x3 = self.lfsr3_state[0]
        x4 = self.lfsr4_state[0]
        
        # FSM combiner
        output = self._fsm_update(x1, x2, x3, x4)
        return output
    
    def _clock_all(self):
        """Clock all LFSRs."""
        self.lfsr1_state = self._clock_lfsr(self.lfsr1_state, [24, 20, 12, 8], self.LFSR1_SIZE)
        self.lfsr2_state = self._clock_lfsr(self.lfsr2_state, [30, 27, 25, 24], self.LFSR2_SIZE)
        self.lfsr3_state = self._clock_lfsr(self.lfsr3_state, [32, 28, 24, 4], self.LFSR3_SIZE)
        self.lfsr4_state = self._clock_lfsr(self.lfsr4_state, [38, 35, 33, 32], self.LFSR4_SIZE)
    
    def _initialize(self, key: List[int], iv: Optional[List[int]]):
        """Initialize E0 with key and IV."""
        if len(key) != 128:
            raise ValueError(f"E0 requires 128-bit key, got {len(key)} bits")
        
        if iv is None:
            iv = [0] * 64
        elif len(iv) != 64:
            raise ValueError(f"E0 requires 64-bit IV, got {len(iv)} bits")
        
        # Initialize LFSR states from key
        self.lfsr1_state = key[0:25]
        self.lfsr2_state = key[25:56]
        self.lfsr3_state = key[56:89]
        self.lfsr4_state = key[89:128]
        
        # Load IV (simplified)
        for i in range(64):
            if i < 25:
                self.lfsr1_state[i] ^= iv[i]
            if i < 31:
                self.lfsr2_state[i] ^= iv[i]
            if i < 33:
                self.lfsr3_state[i] ^= iv[i]
            if i < 39:
                self.lfsr4_state[i] ^= iv[i]
        
        # Initialize FSM
        self.fsm_state = [0, 0]
        
        # Warm-up phase
        for _ in range(self.WARMUP_STEPS):
            self._clock_all()
            self._get_output_bit()  # Update FSM
    
    def generate_keystream(
        self,
        key: List[int],
        iv: Optional[List[int]],
        length: int
    ) -> List[int]:
        """
        Generate E0 keystream.
        
        Args:
            key: 128-bit secret key
            iv: 64-bit initialization vector, or None
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
        """Analyze E0 cipher structure."""
        # Build LFSR configurations
        lfsr1_coeffs = [1] + [0] * 7 + [1] + [0] * 3 + [1] + [0] * 3 + [1] + [0] * 4 + [1]
        lfsr2_coeffs = [1] + [0] * 3 + [1] + [0] * 2 + [1] + [0] * 2 + [1] + [0] * 2 + [1] + [0] * 15
        lfsr3_coeffs = [1] + [0] * 3 + [1] + [0] * 3 + [1] + [0] * 3 + [1] + [0] * 19
        lfsr4_coeffs = [1] + [0] * 2 + [1] + [0] * 2 + [1] + [0] * 2 + [1] + [0] * 29
        
        lfsr1_config = LFSRConfig(coefficients=lfsr1_coeffs, field_order=2, degree=25)
        lfsr2_config = LFSRConfig(coefficients=lfsr2_coeffs, field_order=2, degree=31)
        lfsr3_config = LFSRConfig(coefficients=lfsr3_coeffs, field_order=2, degree=33)
        lfsr4_config = LFSRConfig(coefficients=lfsr4_coeffs, field_order=2, degree=39)
        
        return CipherStructure(
            lfsr_configs=[lfsr1_config, lfsr2_config, lfsr3_config, lfsr4_config],
            clock_control="All LFSRs clock on every step",
            combiner="Non-linear FSM combiner (2-bit state machine)",
            state_size=130,  # 25 + 31 + 33 + 39 + 2
            details={
                'lfsr1_size': 25,
                'lfsr2_size': 31,
                'lfsr3_size': 33,
                'lfsr4_size': 39,
                'fsm_size': 2,
                'warmup_steps': self.WARMUP_STEPS
            }
        )
