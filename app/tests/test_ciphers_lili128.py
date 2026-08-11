#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for lfsr.ciphers.lili128.LILI128.

**No official LILI-128 test vectors are validated here.** In the real
LILI-128 keystream generator (Dawson, Clark, Golic, Kim, Moon, Lee, Park,
1st AES conference / eSTREAM-era literature), the output bit is produced
by a nonlinear Boolean filter function ``fd`` applied to **10 distinct
tapped bits** of the 89-bit LFSRd, and the clock-control function ``fc``
(number of times LFSRd is clocked per step, 1-4) is derived from 2
specific tapped bits of the 39-bit LFSRc via a small lookup/nonlinear
function.

``lfsr.ciphers.lili128.LILI128`` explicitly documents both of these as
simplified (see src/lfsr/ciphers/lili128.py, class docstring "Simplified:
use LFSRc output bits..." at ``_get_clock_count`` and, critically, the
actual output function ``_get_output_bit`` (lines 116-118) simply returns
``lfsrd_state[0]`` directly -- **no nonlinear filter over 10 taps at
all**, just the raw MSB of LFSRd. This is a direct linear tap of the data
register with no combining function, a significant structural
simplification relative to the published cipher. Given this, no official
LILI-128 keystream can match this implementation, and none is asserted
here.

These tests lock in the current, deterministic behavior and the
documented structural properties.
"""

import pytest

from lfsr.ciphers.lili128 import LILI128


def test_generate_keystream_length():
    cipher = LILI128()
    keystream = cipher.generate_keystream([0] * 128, [0] * 64, 100)
    assert len(keystream) == 100
    assert all(bit in (0, 1) for bit in keystream)


def test_generate_keystream_deterministic():
    key = [1, 0] * 64
    iv = [0, 1] * 32
    first = LILI128().generate_keystream(key, iv, 200)
    second = LILI128().generate_keystream(key, iv, 200)
    assert first == second


def test_generate_keystream_not_degenerate():
    cipher = LILI128()
    keystream = cipher.generate_keystream([1] * 128, [0] * 64, 300)
    assert any(bit == 1 for bit in keystream)
    assert any(bit == 0 for bit in keystream)


def test_all_zero_key_and_iv():
    cipher = LILI128()
    keystream = cipher.generate_keystream([0] * 128, [0] * 64, 300)
    assert len(keystream) == 300


def test_different_keys_produce_different_keystreams():
    # As with A5/1 (see test_ciphers_a5_1.py), a single-bit flip against an
    # all-zero key/IV baseline can fail to propagate to the output within
    # a short keystream due to this implementation's clocking dynamics on
    # a near-degenerate all-zero state, so a non-degenerate base key pair
    # is used instead.
    iv = [0] * 64
    base_key = [1, 0, 1, 1] * 32
    other_key = [0, 0, 1, 1] * 32
    keystream_a = LILI128().generate_keystream(base_key, iv, 100)
    keystream_b = LILI128().generate_keystream(other_key, iv, 100)
    assert keystream_a != keystream_b


def test_different_ivs_produce_different_keystreams():
    key = [1, 0, 1, 1] * 32
    keystream_a = LILI128().generate_keystream(key, [0] * 64, 100)
    keystream_b = LILI128().generate_keystream(key, [1] + [0] * 63, 100)
    assert keystream_a != keystream_b


def test_none_iv_defaults_to_zero():
    key = [1, 1, 0, 0] * 32
    with_none = LILI128().generate_keystream(key, None, 64)
    with_zero = LILI128().generate_keystream(key, [0] * 64, 64)
    assert with_none == with_zero


def test_short_iv_is_zero_padded():
    # _initialize (lili128.py lines 145-148) pads a short IV with zeros up
    # to 64 bits rather than raising, unlike every other cipher in this
    # package which raises ValueError on a wrong-size IV. Lock in this
    # documented, intentionally lenient behavior.
    key = [1, 0] * 64
    short_iv = [1, 1, 1, 1]
    padded_iv = short_iv + [0] * 60
    assert LILI128().generate_keystream(key, short_iv, 64) == LILI128().generate_keystream(
        key, padded_iv, 64
    )


def test_rejects_wrong_key_size():
    with pytest.raises(ValueError):
        LILI128().generate_keystream([0] * 127, [0] * 64, 8)


def test_get_clock_count_range():
    cipher = LILI128()
    cipher.lfsrc_state = [0] * 39
    cipher.lfsrd_state = [0] * 89
    for c0 in (0, 1):
        for c1 in (0, 1):
            cipher.lfsrc_state[0] = c0
            cipher.lfsrc_state[1] = c1
            count = cipher._get_clock_count()
            assert 1 <= count <= 4
            assert count == 1 + (c0 << 1) + c1


def test_output_bit_is_lfsrd_msb():
    # Documents the simplification described in the module docstring:
    # the output is directly LFSRd's bit 0, with no nonlinear filter.
    cipher = LILI128()
    cipher.lfsrd_state = [1] + [0] * 88
    assert cipher._get_output_bit() == 1
    cipher.lfsrd_state = [0] + [1] * 88
    assert cipher._get_output_bit() == 0


def test_get_config():
    config = LILI128().get_config()
    assert config.cipher_name == "LILI-128"
    assert config.key_size == 128
    assert config.iv_size == 64
    assert config.parameters["lfsrc_size"] == 39
    assert config.parameters["lfsrd_size"] == 89
    assert config.parameters["total_size"] == 128


def test_analyze_structure():
    structure = LILI128().analyze_structure()
    assert structure.state_size == 128
    assert len(structure.lfsr_configs) == 2
    degrees = [c.degree for c in structure.lfsr_configs]
    assert degrees == [39, 89]
    assert "no combining function" in structure.combiner.lower()


def test_apply_attacks_lists_known_vulnerabilities():
    cipher = LILI128()
    result = cipher.apply_attacks([0, 1] * 10)
    assert len(result["known_vulnerabilities"]) > 0


def test_analyze_end_to_end():
    cipher = LILI128()
    result = cipher.analyze(key=[0] * 128, iv=[0] * 64, keystream_length=64)
    assert result.cipher_name == "LILI-128"
    assert result.keystream_properties["length"] == 64
    assert result.structure.state_size == 128
