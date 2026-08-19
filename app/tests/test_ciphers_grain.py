#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Regression tests for lfsr.ciphers.grain.Grain128.

No official Grain-128 test vectors are validated here (see the module
docstring in lfsr/ciphers/grain.py for why); these tests lock in
deterministic, non-degenerate behavior of the current implementation.
"""

import pytest

from lfsr.ciphers.grain import Grain128


def test_generate_keystream_length():
    cipher = Grain128()
    keystream = cipher.generate_keystream([0] * 128, [0] * 96, 64)
    assert len(keystream) == 64
    assert all(bit in (0, 1) for bit in keystream)


def test_generate_keystream_deterministic():
    key = [1, 0] * 64
    iv = [0, 1] * 48
    first = Grain128().generate_keystream(key, iv, 128)
    second = Grain128().generate_keystream(key, iv, 128)
    assert first == second


def test_generate_keystream_not_degenerate():
    cipher = Grain128()
    keystream = cipher.generate_keystream([0] * 128, [0] * 96, 256)
    assert any(bit == 1 for bit in keystream)
    assert any(bit == 0 for bit in keystream)


def test_different_keys_produce_different_keystreams():
    iv = [0] * 96
    keystream_a = Grain128().generate_keystream([0] * 128, iv, 64)
    keystream_b = Grain128().generate_keystream([1] + [0] * 127, iv, 64)
    assert keystream_a != keystream_b


def test_different_ivs_produce_different_keystreams():
    key = [0] * 128
    keystream_a = Grain128().generate_keystream(key, [0] * 96, 64)
    keystream_b = Grain128().generate_keystream(key, [1] + [0] * 95, 64)
    assert keystream_a != keystream_b


def test_rejects_wrong_key_size():
    with pytest.raises(ValueError):
        Grain128().generate_keystream([0] * 127, [0] * 96, 8)


def test_rejects_wrong_iv_size():
    with pytest.raises(ValueError):
        Grain128().generate_keystream([0] * 128, [0] * 95, 8)


def test_none_iv_defaults_to_zero():
    key = [0] * 128
    with_none = Grain128().generate_keystream(key, None, 32)
    with_zero = Grain128().generate_keystream(key, [0] * 96, 32)
    assert with_none == with_zero


def test_apply_attacks_reports_deprecated_status():
    cipher = Grain128()
    keystream = cipher.generate_keystream([0] * 128, [0] * 96, 32)
    result = cipher.apply_attacks(keystream)
    assert "broken" in result["note"].lower()
    assert result["known_vulnerabilities"] == [
        "Reduced-round cryptanalysis of the initialization phase"
    ]
    assert "deprecated" in result["security_status"].lower()
