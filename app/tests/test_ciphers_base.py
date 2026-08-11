#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for lfsr.ciphers.base: CipherConfig, CipherStructure,
CipherAnalysisResult dataclasses, and the StreamCipher abstract base
class's concrete helper methods (apply_attacks default, analyze,
_analyze_keystream_properties, _assess_security).

Exercised via a minimal concrete subclass rather than any real cipher,
so these tests are independent of any cipher-specific correctness
question (those are covered in the per-cipher test modules).
"""

import pytest

from lfsr.attacks import LFSRConfig
from lfsr.ciphers.base import (
    CipherAnalysisResult,
    CipherConfig,
    CipherStructure,
    StreamCipher,
)


class _ToyCipher(StreamCipher):
    """Minimal concrete StreamCipher: keystream is just the key repeated
    and XORed with a running counter parity, deterministic and cheap."""

    def generate_keystream(self, key, iv, length):
        if len(key) == 0:
            raise ValueError("key must be non-empty")
        if iv is not None and len(iv) == 0:
            raise ValueError("iv must be non-empty if provided")
        out = []
        for i in range(length):
            out.append(key[i % len(key)] ^ (i % 2))
        return out

    def analyze_structure(self):
        lfsr_config = LFSRConfig(coefficients=[1, 0, 1], field_order=2, degree=3)
        return CipherStructure(
            lfsr_configs=[lfsr_config],
            clock_control="regular",
            combiner="XOR",
            state_size=3,
        )

    def get_config(self):
        return CipherConfig(
            cipher_name="ToyCipher",
            key_size=8,
            iv_size=0,
            description="Test-only toy cipher",
        )


class _ToyCipherWithAttacks(_ToyCipher):
    """Toy cipher that overrides apply_attacks, to test the analyze()
    integration path where attack_results is non-empty."""

    def apply_attacks(self, keystream, attack_types=None):
        return {"toy_attack": {"success": True, "keystream_length": len(keystream)}}


def test_cipher_config_dataclass_defaults():
    config = CipherConfig(
        cipher_name="X", key_size=64, iv_size=22, description="desc"
    )
    assert config.parameters == {}


def test_cipher_config_dataclass_with_parameters():
    config = CipherConfig(
        cipher_name="X",
        key_size=64,
        iv_size=22,
        description="desc",
        parameters={"foo": 1},
    )
    assert config.parameters == {"foo": 1}


def test_cipher_structure_dataclass_defaults():
    lfsr_config = LFSRConfig(coefficients=[1, 1], field_order=2, degree=2)
    structure = CipherStructure(
        lfsr_configs=[lfsr_config],
        clock_control="regular",
        combiner="XOR",
        state_size=2,
    )
    assert structure.details == {}


def test_cipher_analysis_result_dataclass_defaults():
    lfsr_config = LFSRConfig(coefficients=[1, 1], field_order=2, degree=2)
    structure = CipherStructure(
        lfsr_configs=[lfsr_config],
        clock_control="regular",
        combiner="XOR",
        state_size=2,
    )
    result = CipherAnalysisResult(cipher_name="X", structure=structure)
    assert result.keystream_properties == {}
    assert result.attack_results == {}
    assert result.security_assessment == {}
    assert result.details == {}


def test_stream_cipher_is_abstract():
    with pytest.raises(TypeError):
        StreamCipher()  # abstract methods not implemented


def test_toy_cipher_generate_keystream():
    cipher = _ToyCipher()
    keystream = cipher.generate_keystream([1, 0, 1], None, 6)
    assert len(keystream) == 6
    assert all(bit in (0, 1) for bit in keystream)


def test_default_apply_attacks_returns_empty_dict():
    cipher = _ToyCipher()
    result = cipher.apply_attacks([0, 1, 1, 0])
    assert result == {}


def test_analyze_without_key_skips_keystream_generation():
    cipher = _ToyCipher()
    result = cipher.analyze(key=None)
    assert isinstance(result, CipherAnalysisResult)
    assert result.keystream_properties == {}
    assert result.attack_results == {}
    assert result.cipher_name == "ToyCipher"


def test_analyze_with_key_populates_keystream_properties():
    cipher = _ToyCipher()
    result = cipher.analyze(key=[1, 0, 1, 1], iv=None, keystream_length=50)
    assert result.keystream_properties["length"] == 50
    assert result.keystream_properties["ones"] + result.keystream_properties["zeros"] == 50
    assert 0.0 <= result.keystream_properties["ones_ratio"] <= 1.0
    assert 0.0 <= result.keystream_properties["balance"] <= 1.0


def test_analyze_default_apply_attacks_gives_empty_attack_results():
    cipher = _ToyCipher()
    result = cipher.analyze(key=[1, 0, 1, 1], keystream_length=20)
    assert result.attack_results == {}


def test_analyze_with_overridden_apply_attacks():
    cipher = _ToyCipherWithAttacks()
    result = cipher.analyze(key=[1, 0, 1, 1], keystream_length=20)
    assert result.attack_results == {
        "toy_attack": {"success": True, "keystream_length": 20}
    }


def test_analyze_structure_always_populated():
    cipher = _ToyCipher()
    result = cipher.analyze(key=None)
    assert result.structure.state_size == 3
    assert result.structure.combiner == "XOR"


def test_analyze_keystream_properties_helper_empty_input():
    cipher = _ToyCipher()
    assert cipher._analyze_keystream_properties([]) == {}


def test_analyze_keystream_properties_helper_all_ones():
    cipher = _ToyCipher()
    props = cipher._analyze_keystream_properties([1, 1, 1, 1])
    assert props["length"] == 4
    assert props["ones"] == 4
    assert props["zeros"] == 0
    assert props["balance"] == 1.0
    assert props["ones_ratio"] == 1.0


def test_analyze_keystream_properties_helper_balanced():
    cipher = _ToyCipher()
    props = cipher._analyze_keystream_properties([1, 0, 1, 0])
    assert props["ones"] == 2
    assert props["zeros"] == 2
    assert props["balance"] == 0.0
    assert props["ones_ratio"] == 0.5


def test_assess_security_helper_returns_placeholder_structure():
    cipher = _ToyCipher()
    structure = cipher.analyze_structure()
    assessment = cipher._assess_security(structure, {})
    assert assessment["structure_complexity"] == "medium"
    assert assessment["known_vulnerabilities"] == []
    assert assessment["recommendations"] == []


def test_get_config_roundtrip():
    cipher = _ToyCipher()
    config = cipher.get_config()
    assert config.cipher_name == "ToyCipher"
    assert config.key_size == 8
    assert config.iv_size == 0
