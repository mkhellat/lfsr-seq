#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Grain Family Stream Cipher Analysis

This module provides analysis capabilities for the Grain family of
stream ciphers, including Grain-128 and Grain-128a. Grain uses one
LFSR and one NFSR (Non-Linear Feedback Shift Register) with a filter
function.

**Historical Context**:

Grain was designed by Martin Hell, Thomas Johansson, and Willi Meier
as part of the eSTREAM project. Grain-128 and Grain-128a were
selected as eSTREAM finalists in the hardware category. Grain-128a
provides authenticated encryption.

**Security Status**:

The original (2006) Grain-128 is considered broken and should not be
used for real-world security; Grain-128a (2011) and its successor
Grain-128AEAD are the recommended, actively-analyzed members of the
family. See "Grain-128AEAD: A lightweight AEAD stream cipher" (Hell,
Johansson, Meier, Sonnerup, Yoshida; NIST Lightweight Cryptography
submission, https://grain-128aead.github.io/), Section 3.1.

**Implementation Note**:

The ``Grain128`` class below implements the Grain-128 register sizes,
key/IV sizes (128-bit key, 96-bit IV) and the family's shared LFSR/NFSR
update mechanics (tap-index convention, permanent LFSR-bit masking into
the NFSR feedback, LFSR padding, and the 256-clock warmup with pre-output
feedback), all confirmed against the primary source above. The nonlinear
feedback function g(x) and filter function h(x), however, are those of
Grain-128a/Grain-128AEAD (verbatim from the same primary source), not the
original 2006 Grain-128 paper's weaker functions -- the exact original
AND-term list could not be confirmed against any reachable primary
source. Since original Grain-128 is deprecated in favor of Grain-128a
anyway, this substitution was judged the more defensible choice over
guessing at unverified formulas from secondary/paraphrased sources.

**Key Terminology**:

- **Grain**: Family of eSTREAM finalist stream ciphers
- **NFSR**: Non-Linear Feedback Shift Register
- **Filter Function**: Non-linear function combining LFSR and NFSR outputs
- **Authenticated Encryption**: Grain-128a provides authentication
"""

from typing import List, Optional

from lfsr.attacks import LFSRConfig
from lfsr.ciphers.base import CipherConfig, CipherStructure, StreamCipher
from lfsr.sage_imports import *


class Grain128(StreamCipher):
    """
    Grain-128 stream cipher implementation.

    Grain-128 uses one LFSR and one NFSR with a filter function for
    non-linear combining. See the module docstring for a note on the
    provenance of the g(x)/h(x) functions used here.

    **State array convention**: ``lfsr_state[0]``/``nfsr_state[0]`` hold
    the most recently shifted-in bit; ``lfsr_state[127]``/``nfsr_state[127]``
    hold the oldest bit still in the register. This is the reverse of the
    spec's ``s_i``/``b_i`` window notation (where ``s_i`` is oldest and
    ``s_{i+127}`` is newest), so a spec tap offset ``j`` corresponds to
    array index ``127 - j``.

    **Cipher Structure**:

    - **LFSR**: 128 bits (linear feedback)
    - **NFSR**: 128 bits (non-linear feedback)
    - **Filter Function**: Non-linear function combining outputs
    - **Total State**: 256 bits

    **Key and IV**:

    - **Key Size**: 128 bits
    - **IV Size**: 96 bits
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
            description="Grain-128 eSTREAM finalist with LFSR and NFSR",
            parameters={
                'lfsr_size': self.LFSR_SIZE,
                'nfsr_size': self.NFSR_SIZE,
                'total_size': self.TOTAL_SIZE,
                'warmup_steps': self.WARMUP_STEPS
            }
        )

    def _clock_lfsr(self, warmup_feedback: int = 0) -> int:
        """Clock LFSR and return feedback.

        Spec taps (offsets from window start s_i): 0, 7, 38, 70, 81, 96,
        mapped to array indices via 127 - offset.

        Args:
            warmup_feedback: during the initialization warmup, the
                pre-output bit is XORed into the LFSR feedback before
                it is shifted in (per the Grain-128a spec). Zero outside
                of warmup.
        """
        feedback = (self.lfsr_state[127] ^ self.lfsr_state[120] ^
                   self.lfsr_state[89] ^ self.lfsr_state[57] ^
                   self.lfsr_state[46] ^ self.lfsr_state[31] ^
                   warmup_feedback)
        self.lfsr_state = [feedback] + self.lfsr_state[:-1]
        return feedback

    def _clock_nfsr(self, warmup_feedback: int = 0) -> int:
        """Clock NFSR and return feedback.

        Spec taps (offsets from window start b_i): linear terms at 0, 26,
        56, 91, 96; AND terms at (3,67), (11,13), (17,18), (27,59),
        (40,48), (61,65), (68,84), (22,24,25), (70,78,82),
        (88,92,93,95); mapped to array indices via 127 - offset. The
        LFSR's current oldest bit (lfsr_state[127], i.e. spec's s_i) is
        permanently XORed in on every clock, not just during warmup.

        Args:
            warmup_feedback: during the initialization warmup, the
                pre-output bit is also XORed into the NFSR feedback
                before it is shifted in (per the Grain-128a spec). Zero
                outside of warmup.
        """
        feedback = (self.lfsr_state[127] ^
                   self.nfsr_state[127] ^ self.nfsr_state[101] ^
                   self.nfsr_state[71] ^ self.nfsr_state[36] ^
                   self.nfsr_state[31] ^
                   (self.nfsr_state[124] & self.nfsr_state[60]) ^
                   (self.nfsr_state[116] & self.nfsr_state[114]) ^
                   (self.nfsr_state[110] & self.nfsr_state[109]) ^
                   (self.nfsr_state[100] & self.nfsr_state[68]) ^
                   (self.nfsr_state[87] & self.nfsr_state[79]) ^
                   (self.nfsr_state[66] & self.nfsr_state[62]) ^
                   (self.nfsr_state[59] & self.nfsr_state[43]) ^
                   (self.nfsr_state[105] & self.nfsr_state[103] & self.nfsr_state[102]) ^
                   (self.nfsr_state[57] & self.nfsr_state[49] & self.nfsr_state[45]) ^
                   (self.nfsr_state[39] & self.nfsr_state[35] & self.nfsr_state[34] & self.nfsr_state[32]) ^
                   warmup_feedback)
        self.nfsr_state = [feedback] + self.nfsr_state[:-1]
        return feedback

    def _filter_function(self) -> int:
        """Compute filter function h(x).

        h(x) = x0x1 + x2x3 + x4x5 + x6x7 + x0x4x8, where x0..x8 are the
        spec state variables b_12, s_8, s_13, s_20, b_95, s_42, s_60,
        s_79, s_94, mapped to array indices via 127 - offset.
        """
        x0 = self.nfsr_state[115]
        x1 = self.lfsr_state[119]
        x2 = self.lfsr_state[114]
        x3 = self.lfsr_state[107]
        x4 = self.nfsr_state[32]
        x5 = self.lfsr_state[85]
        x6 = self.lfsr_state[67]
        x7 = self.lfsr_state[48]
        x8 = self.lfsr_state[33]
        return (x0 & x1) ^ (x2 & x3) ^ (x4 & x5) ^ (x6 & x7) ^ (x0 & x4 & x8)

    def _get_output_bit(self) -> int:
        """Get pre-output bit y_t from Grain-128.

        y_t = h(x) + s_93 + sum(b_j for j in {2,15,36,45,64,73,89}),
        with spec offsets mapped to array indices via 127 - offset.
        """
        linear_terms = (self.nfsr_state[125] ^ self.nfsr_state[112] ^
                        self.nfsr_state[91] ^ self.nfsr_state[82] ^
                        self.nfsr_state[63] ^ self.nfsr_state[54] ^
                        self.nfsr_state[38])
        return self.lfsr_state[34] ^ linear_terms ^ self._filter_function()

    def _initialize(self, key: List[int], iv: Optional[List[int]]):
        """Initialize Grain-128 with key and IV."""
        if len(key) != 128:
            raise ValueError(f"Grain-128 requires 128-bit key, got {len(key)} bits")

        if iv is None:
            iv = [0] * 96
        elif len(iv) != 96:
            raise ValueError(f"Grain-128 requires 96-bit IV, got {len(iv)} bits")

        # b_i = k_i for 0<=i<=127; array index k holds spec offset 127-k,
        # so array index k = key[127 - k].
        self.nfsr_state = list(reversed(key))

        # s_i = IV_i for 0<=i<=95; s_i=1 for 96<=i<=126; s_127=0.
        # Array index k holds spec offset 127-k.
        self.lfsr_state = [0] + [1] * 31 + list(reversed(iv))

        # Warm-up phase: the pre-output bit is XORed into both the LFSR and
        # NFSR feedback before it is shifted in (per the Grain-128a spec).
        for _ in range(self.WARMUP_STEPS):
            outbit = self._get_output_bit()
            self._clock_lfsr(warmup_feedback=outbit)
            self._clock_nfsr(warmup_feedback=outbit)

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
            self._clock_lfsr()
            self._clock_nfsr()

        return keystream

    def analyze_structure(self) -> CipherStructure:
        """Analyze Grain-128 cipher structure."""
        # LFSR configuration
        lfsr_coeffs = [0] * 128
        lfsr_coeffs[0] = 1
        lfsr_coeffs[7] = 1
        lfsr_coeffs[38] = 1
        lfsr_coeffs[70] = 1
        lfsr_coeffs[81] = 1
        lfsr_coeffs[96] = 1

        lfsr_config = LFSRConfig(coefficients=lfsr_coeffs, field_order=2, degree=128)

        return CipherStructure(
            lfsr_configs=[lfsr_config],
            clock_control="Both LFSR and NFSR clock every step",
            combiner="Non-linear filter function combining LFSR and NFSR outputs",
            state_size=256,  # 128 + 128
            details={
                'lfsr_size': 128,
                'nfsr_size': 128,
                'total_size': 256,
                'warmup_steps': self.WARMUP_STEPS,
                'note': 'Grain uses one LFSR and one NFSR with non-linear filter function'
            }
        )

    def apply_attacks(
        self,
        keystream: List[int],
        attack_types: Optional[List[str]] = None
    ) -> dict:
        """Apply attacks to Grain-128 keystream."""
        return {
            'note': 'Original (2006) Grain-128 is considered broken and superseded '
                    'by Grain-128a/Grain-128AEAD; see module docstring.',
            'known_vulnerabilities': ['Reduced-round cryptanalysis of the initialization phase'],
            'security_status': 'Deprecated; do not use for real-world security'
        }


class Grain128a(Grain128):
    """
    Grain-128a stream cipher implementation.

    Grain-128a extends Grain-128 with authenticated encryption capabilities.
    The structure is similar to Grain-128 but includes authentication.
    """

    def get_config(self) -> CipherConfig:
        """Get Grain-128a cipher configuration."""
        return CipherConfig(
            cipher_name="Grain-128a",
            key_size=128,
            iv_size=96,
            description="Grain-128a eSTREAM finalist with authenticated encryption",
            parameters={
                'lfsr_size': self.LFSR_SIZE,
                'nfsr_size': self.NFSR_SIZE,
                'total_size': self.TOTAL_SIZE,
                'warmup_steps': self.WARMUP_STEPS,
                'authenticated_encryption': True
            }
        )
