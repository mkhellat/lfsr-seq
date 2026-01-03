#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A5/1 Stream Cipher Analysis

This module provides analysis capabilities for the A5/1 stream cipher, which was
used for GSM mobile phone encryption. A5/1 uses three LFSRs with irregular
clocking controlled by a majority function.

**Historical Context**:

A5/1 was designed in 1987 and became the standard encryption algorithm for GSM
(Global System for Mobile Communications) mobile phones. It was used to encrypt
voice and data communications between mobile phones and base stations. A5/1 was
designed to be fast in hardware and provide adequate security for the time.

**Security Status**:

A5/1 has been cryptanalyzed extensively and is now considered insecure. Known
attacks include:
- Time-memory trade-off attacks (Barkan, Biham, Keller, 2003)
- Correlation attacks
- Known-plaintext attacks
- Hardware-based attacks

Despite its weaknesses, A5/1 remains an important cipher for educational purposes
and demonstrates how LFSRs can be combined with irregular clocking.

**Key Terminology**:

- **A5/1**: The stream cipher used in GSM encryption
- **GSM**: Global System for Mobile Communications, the standard for mobile phones
- **Irregular Clocking**: LFSRs don't always advance on each step (clock control)
- **Majority Function**: A function that outputs the majority value of its inputs
- **Clock Control Bit**: A bit from each LFSR used to determine clocking
- **Frame Number**: The 22-bit IV used in GSM (represents frame number)
- **Warm-up Phase**: Initial 100 steps before keystream generation (discarded)
- **Keystream**: The pseudorandom sequence XORed with plaintext

**Mathematical Foundation**:

A5/1 uses three LFSRs:
- LFSR1: 19 bits, feedback polynomial x^19 + x^18 + x^17 + x^14 + 1
- LFSR2: 22 bits, feedback polynomial x^22 + x^21 + 1
- LFSR3: 23 bits, feedback polynomial x^23 + x^22 + x^21 + x^8 + 1

The clocking is controlled by a majority function on three clock control bits:
- Clock control bits: bit 8 of LFSR1, bit 10 of LFSR2, bit 10 of LFSR3
- Majority function: Outputs the majority value (0 or 1) of the three bits
- Clocking rule: An LFSR advances if its clock control bit matches the majority

The keystream is the XOR of the three LFSR output bits.
"""

from typing import List, Optional

from lfsr.sage_imports import *

from lfsr.attacks import LFSRConfig
from lfsr.ciphers.base import (
    StreamCipher,
    CipherConfig,
    CipherStructure,
    CipherAnalysisResult
)


class A5_1(StreamCipher):
    """
    A5/1 GSM stream cipher implementation.
    
    A5/1 is a stream cipher that uses three LFSRs with irregular clocking.
    The clocking is controlled by a majority function on clock control bits
    from each LFSR.
    
    **Cipher Structure**:
    
    - **LFSR1**: 19 bits, taps at positions 18, 17, 16, 13
    - **LFSR2**: 22 bits, taps at positions 21, 20
    - **LFSR3**: 23 bits, taps at positions 22, 21, 20, 7
    - **Clock Control**: Majority function on bits 8, 10, 10 (from LFSR1, LFSR2, LFSR3)
    - **Output**: XOR of three LFSR output bits
    
    **Key and IV**:
    
    - **Key Size**: 64 bits
    - **IV Size**: 22 bits (frame number in GSM)
    - **Total State**: 19 + 22 + 23 = 64 bits
    
    **Initialization**:
    
    1. Load 64-bit key into LFSRs (19 + 22 + 23 bits)
    2. Load 22-bit frame number (IV) into LFSRs
    3. Run 100 warm-up steps (discard output)
    4. Generate keystream
    
    **Example Usage**:
    
        >>> from lfsr.ciphers.a5_1 import A5_1
        >>> cipher = A5_1()
        >>> key = [1] * 64  # Example key
        >>> iv = [0] * 22   # Example IV (frame number)
        >>> keystream = cipher.generate_keystream(key, iv, 100)
        >>> structure = cipher.analyze_structure()
    """
    
    # A5/1 LFSR configurations
    # LFSR1: 19 bits, polynomial x^19 + x^18 + x^17 + x^14 + 1
    LFSR1_TAPS = [18, 17, 16, 13]  # Tap positions (0-indexed)
    LFSR1_SIZE = 19
    
    # LFSR2: 22 bits, polynomial x^22 + x^21 + 1
    LFSR2_TAPS = [21, 20]
    LFSR2_SIZE = 22
    
    # LFSR3: 23 bits, polynomial x^23 + x^22 + x^21 + x^8 + 1
    LFSR3_TAPS = [22, 21, 20, 7]
    LFSR3_SIZE = 23
    
    # Clock control bit positions
    CLOCK_BIT_1 = 8   # LFSR1 bit 8
    CLOCK_BIT_2 = 10  # LFSR2 bit 10
    CLOCK_BIT_3 = 10  # LFSR3 bit 10
    
    # Warm-up steps
    WARMUP_STEPS = 100
    
    def __init__(self):
        """Initialize A5/1 cipher."""
        self.lfsr1_state = None
        self.lfsr2_state = None
        self.lfsr3_state = None
    
    def get_config(self) -> CipherConfig:
        """Get A5/1 cipher configuration."""
        return CipherConfig(
            cipher_name="A5/1",
            key_size=64,
            iv_size=22,
            description="A5/1 GSM stream cipher with 3 LFSRs and irregular clocking",
            parameters={
                'lfsr1_size': self.LFSR1_SIZE,
                'lfsr2_size': self.LFSR2_SIZE,
                'lfsr3_size': self.LFSR3_SIZE,
                'warmup_steps': self.WARMUP_STEPS
            }
        )
    
    def _majority(self, a: int, b: int, c: int) -> int:
        """
        Compute majority function.
        
        The majority function returns 1 if at least two inputs are 1, otherwise 0.
        This is used to determine which LFSRs should advance.
        
        Args:
            a: First input bit
            b: Second input bit
            c: Third input bit
        
        Returns:
            Majority value (0 or 1)
        """
        return (a & b) | (a & c) | (b & c)
    
    def _clock_lfsr(self, state: List[int], taps: List[int], size: int) -> List[int]:
        """
        Clock a single LFSR (advance one step).
        
        Args:
            state: Current LFSR state (list of bits)
            taps: Tap positions for feedback
            size: LFSR size
        
        Returns:
            New LFSR state after one clock
        """
        # Compute feedback (XOR of tap bits)
        feedback = 0
        for tap in taps:
            feedback ^= state[tap]
        
        # Shift and insert feedback
        new_state = [feedback] + state[:-1]
        return new_state
    
    def _get_output_bit(self) -> int:
        """
        Get output bit from A5/1.
        
        The output is the XOR of the three LFSR output bits (MSB of each).
        
        Returns:
            Output bit (0 or 1)
        """
        output1 = self.lfsr1_state[0]  # MSB of LFSR1
        output2 = self.lfsr2_state[0]  # MSB of LFSR2
        output3 = self.lfsr3_state[0]  # MSB of LFSR3
        
        return output1 ^ output2 ^ output3
    
    def _clock_controlled(self):
        """
        Clock A5/1 with irregular clocking.
        
        The clocking is controlled by a majority function:
        - Get clock control bits from each LFSR
        - Compute majority
        - Advance LFSRs whose clock control bit matches majority
        """
        # Get clock control bits
        c1 = self.lfsr1_state[self.CLOCK_BIT_1]
        c2 = self.lfsr2_state[self.CLOCK_BIT_2]
        c3 = self.lfsr3_state[self.CLOCK_BIT_3]
        
        # Compute majority
        majority = self._majority(c1, c2, c3)
        
        # Clock LFSRs whose control bit matches majority
        if c1 == majority:
            self.lfsr1_state = self._clock_lfsr(
                self.lfsr1_state,
                self.LFSR1_TAPS,
                self.LFSR1_SIZE
            )
        
        if c2 == majority:
            self.lfsr2_state = self._clock_lfsr(
                self.lfsr2_state,
                self.LFSR2_TAPS,
                self.LFSR2_SIZE
            )
        
        if c3 == majority:
            self.lfsr3_state = self._clock_lfsr(
                self.lfsr3_state,
                self.LFSR3_TAPS,
                self.LFSR3_SIZE
            )
    
    def _initialize(self, key: List[int], iv: Optional[List[int]]):
        """
        Initialize A5/1 with key and IV.
        
        The initialization process:
        1. Load key bits into LFSRs (64 bits total)
        2. Load frame number (IV) bits into LFSRs (22 bits)
        3. Run warm-up phase (100 steps, discard output)
        
        Args:
            key: 64-bit key
            iv: 22-bit initialization vector (frame number), or None
        """
        if len(key) != 64:
            raise ValueError(f"A5/1 requires 64-bit key, got {len(key)} bits")
        
        if iv is None:
            iv = [0] * 22
        elif len(iv) != 22:
            raise ValueError(f"A5/1 requires 22-bit IV, got {len(iv)} bits")
        
        # Initialize LFSR states
        # Key bits: 64 bits total
        # LFSR1: bits 0-18 (19 bits)
        # LFSR2: bits 19-40 (22 bits)
        # LFSR3: bits 41-63 (23 bits)
        self.lfsr1_state = key[0:19]
        self.lfsr2_state = key[19:41]
        self.lfsr3_state = key[41:64]
        
        # Load frame number (IV) into LFSRs
        # XOR frame number bits into LFSR states
        for i in range(22):
            # Distribute frame number bits across LFSRs
            if i < 19:
                self.lfsr1_state[i] ^= iv[i]
            if i < 22:
                self.lfsr2_state[i] ^= iv[i]
            if i < 23:
                self.lfsr3_state[i] ^= iv[i]
        
        # Warm-up phase: run 100 steps without output
        for _ in range(self.WARMUP_STEPS):
            self._clock_controlled()
    
    def generate_keystream(
        self,
        key: List[int],
        iv: Optional[List[int]],
        length: int
    ) -> List[int]:
        """
        Generate A5/1 keystream.
        
        This method generates a keystream of the specified length using the
        provided key and initialization vector (frame number).
        
        **Algorithm**:
        
        1. Initialize LFSRs with key and IV
        2. Run warm-up phase (100 steps, discard output)
        3. For each output bit:
           - Clock LFSRs with irregular clocking (majority function)
           - Output XOR of three LFSR output bits
        
        Args:
            key: 64-bit secret key (list of 64 bits, 0 or 1)
            iv: 22-bit initialization vector (frame number), or None for zero IV
            length: Desired keystream length in bits
        
        Returns:
            List of keystream bits (0 or 1)
        
        Raises:
            ValueError: If key or IV size is incorrect
        
        Example:
            >>> cipher = A5_1()
            >>> key = [1, 0, 1] * 21 + [1]  # 64 bits
            >>> iv = [0] * 22
            >>> keystream = cipher.generate_keystream(key, iv, 100)
            >>> len(keystream) == 100
            True
        """
        # Initialize
        self._initialize(key, iv)
        
        # Generate keystream
        keystream = []
        for _ in range(length):
            # Clock with irregular clocking
            self._clock_controlled()
            
            # Get output bit
            output = self._get_output_bit()
            keystream.append(output)
        
        return keystream
    
    def analyze_structure(self) -> CipherStructure:
        """
        Analyze A5/1 cipher structure.
        
        This method analyzes the internal structure of A5/1, including LFSR
        configurations, clocking mechanism, and combining function.
        
        Returns:
            CipherStructure describing A5/1's internal structure
        """
        # Build LFSR configurations
        # Note: A5/1 uses binary LFSRs, so field_order=2
        
        # LFSR1: polynomial x^19 + x^18 + x^17 + x^14 + 1
        # Coefficients: [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 1]
        lfsr1_coeffs = [0] * 19
        lfsr1_coeffs[0] = 1  # x^0
        lfsr1_coeffs[13] = 1  # x^14
        lfsr1_coeffs[16] = 1  # x^17
        lfsr1_coeffs[17] = 1  # x^18
        lfsr1_coeffs[18] = 1  # x^19
        
        # LFSR2: polynomial x^22 + x^21 + 1
        lfsr2_coeffs = [0] * 22
        lfsr2_coeffs[0] = 1  # x^0
        lfsr2_coeffs[20] = 1  # x^21
        lfsr2_coeffs[21] = 1  # x^22
        
        # LFSR3: polynomial x^23 + x^22 + x^21 + x^8 + 1
        lfsr3_coeffs = [0] * 23
        lfsr3_coeffs[0] = 1  # x^0
        lfsr3_coeffs[7] = 1  # x^8
        lfsr3_coeffs[20] = 1  # x^21
        lfsr3_coeffs[21] = 1  # x^22
        lfsr3_coeffs[22] = 1  # x^23
        
        lfsr1_config = LFSRConfig(
            coefficients=lfsr1_coeffs,
            field_order=2,
            degree=19
        )
        
        lfsr2_config = LFSRConfig(
            coefficients=lfsr2_coeffs,
            field_order=2,
            degree=22
        )
        
        lfsr3_config = LFSRConfig(
            coefficients=lfsr3_coeffs,
            field_order=2,
            degree=23
        )
        
        return CipherStructure(
            lfsr_configs=[lfsr1_config, lfsr2_config, lfsr3_config],
            clock_control=(
                f"Majority function on clock control bits: "
                f"LFSR1[8], LFSR2[10], LFSR3[10]. "
                f"An LFSR advances if its clock control bit matches the majority."
            ),
            combiner="XOR of three LFSR output bits (MSB of each LFSR)",
            state_size=64,  # 19 + 22 + 23
            details={
                'lfsr1_size': 19,
                'lfsr2_size': 22,
                'lfsr3_size': 23,
                'clock_control_bits': [8, 10, 10],
                'warmup_steps': self.WARMUP_STEPS,
                'polynomials': {
                    'lfsr1': 'x^19 + x^18 + x^17 + x^14 + 1',
                    'lfsr2': 'x^22 + x^21 + 1',
                    'lfsr3': 'x^23 + x^22 + x^21 + x^8 + 1'
                }
            }
        )
    
    def apply_attacks(
        self,
        keystream: List[int],
        attack_types: Optional[List[str]] = None
    ) -> dict:
        """
        Apply attacks to A5/1 keystream.
        
        A5/1 is vulnerable to several attacks:
        - Time-memory trade-off attacks
        - Correlation attacks
        - Known-plaintext attacks
        
        Args:
            keystream: Observed keystream bits
            attack_types: List of attack types to apply (None = all available)
        
        Returns:
            Dictionary mapping attack names to results
        """
        # Placeholder for attack integration
        # In full implementation, this would integrate with attack frameworks
        return {
            'note': 'Attack integration pending',
            'known_vulnerabilities': [
                'Time-memory trade-off attacks (Barkan et al., 2003)',
                'Correlation attacks',
                'Known-plaintext attacks'
            ]
        }
