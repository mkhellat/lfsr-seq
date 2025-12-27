"""
Stream Cipher Analysis Module

This module provides analysis capabilities for real-world stream ciphers that use
LFSRs, including A5/1, A5/2, E0, Trivium, Grain family, and LILI-128.

The module is organized as follows:
- base.py: Base classes and common interfaces
- a5_1.py: A5/1 GSM encryption cipher
- a5_2.py: A5/2 GSM encryption cipher (weaker variant)
- e0.py: E0 Bluetooth encryption cipher
- trivium.py: Trivium eSTREAM finalist
- grain.py: Grain family (Grain-128, Grain-128a)
- lili128.py: LILI-128 academic design
- comparison.py: Cipher comparison framework
"""

from lfsr.ciphers.base import (
    StreamCipher,
    CipherConfig,
    CipherAnalysisResult,
    CipherStructure
)

__all__ = [
    "StreamCipher",
    "CipherConfig",
    "CipherAnalysisResult",
    "CipherStructure",
]
