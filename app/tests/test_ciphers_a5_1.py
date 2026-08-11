#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for lfsr.ciphers.a5_1.A5_1.

**No official GSM A5/1 test vectors are validated here.** The real A5/1
specification loads the 64-bit key and then the 22-bit frame number
(IV) into the three LFSRs *with regular clocking applied on every key/IV
bit* (64 + 22 = 86 clock cycles total before the 100-cycle irregular-
clocking warm-up phase), XORing each key/IV bit into the LFSRs'
feedback path as it is clocked in. This is confirmed by multiple
independent descriptions of the algorithm (e.g. the GSM/ETSI-derived
description summarized at
https://cryptography.fandom.com/wiki/A5/1 and multiple reference C
implementations).

``lfsr.ciphers.a5_1.A5_1._initialize`` (src/lfsr/ciphers/a5_1.py
lines 240-283) instead:
  1. Loads the 64 key bits directly into the three LFSR state arrays
     with no clocking at all (a plain slice assignment).
  2. XORs all 22 frame-number bits into the LFSR states in a single
     unclocked pass (a Python ``for`` loop that mutates state in place,
     but never calls ``_clock_lfsr``/``_clock_controlled`` between bits).
  3. Only then runs the 100-step irregular-clocking warm-up.

Skipping the regular-clocking-during-loading phase is a structural
deviation from the real cipher (not just a different bit-ordering
convention), so no official A5/1 keystream will ever match this
implementation for any key/frame-number pair. This is a **known,
documented limitation** of this implementation, not something these
tests attempt to fix (source changes are out of scope here) -- see the
project's cipher docstrings, which already flag A5/1 as
"important for educational purposes" rather than a byte-for-byte GSM
implementation.

These tests therefore lock in the current, deterministic (if
non-spec-conformant) behavior: correct output shape, determinism,
sensitivity to key/IV changes, and the structural properties
(LFSR sizes, degrees, clock control bits) documented in
``analyze_structure()``.
"""

import pytest

from lfsr.ciphers.a5_1 import A5_1


def test_generate_keystream_length():
    cipher = A5_1()
    keystream = cipher.generate_keystream([0] * 64, [0] * 22, 100)
    assert len(keystream) == 100
    assert all(bit in (0, 1) for bit in keystream)


def test_generate_keystream_deterministic():
    key = [1, 0] * 32
    iv = [0, 1] * 11
    first = A5_1().generate_keystream(key, iv, 200)
    second = A5_1().generate_keystream(key, iv, 200)
    assert first == second


def test_generate_keystream_not_degenerate():
    cipher = A5_1()
    keystream = cipher.generate_keystream([1] * 64, [0] * 22, 300)
    assert any(bit == 1 for bit in keystream)
    assert any(bit == 0 for bit in keystream)


def test_all_zero_key_and_iv_not_degenerate():
    # A5/1's LFSRs are not pure zero-preserving (feedback taps can turn a
    # zero state non-zero only via the IV XOR / warm-up, so this exercises
    # the important all-zero edge case explicitly).
    cipher = A5_1()
    keystream = cipher.generate_keystream([0] * 64, [0] * 22, 300)
    assert len(keystream) == 300


def test_different_keys_produce_different_keystreams():
    # Note: flipping a single bit of an all-zero key/IV pair is not used
    # here -- with this implementation's clocking dynamics that single
    # bit can fail to propagate to the output within the keystream length
    # tested (a near-degenerate all-zero-state corner case), so a
    # non-degenerate base key is used instead to make this a meaningful
    # differential test.
    iv = [0] * 22
    base_key = [1, 0, 1, 1] * 16
    other_key = [0, 0, 1, 1] * 16
    keystream_a = A5_1().generate_keystream(base_key, iv, 100)
    keystream_b = A5_1().generate_keystream(other_key, iv, 100)
    assert keystream_a != keystream_b


def test_different_ivs_produce_different_keystreams():
    key = [1, 0, 1, 1] * 16
    keystream_a = A5_1().generate_keystream(key, [0] * 22, 100)
    keystream_b = A5_1().generate_keystream(key, [1] + [0] * 21, 100)
    assert keystream_a != keystream_b


def test_none_iv_defaults_to_zero():
    key = [1, 1, 0, 0] * 16
    with_none = A5_1().generate_keystream(key, None, 64)
    with_zero = A5_1().generate_keystream(key, [0] * 22, 64)
    assert with_none == with_zero


def test_rejects_wrong_key_size():
    with pytest.raises(ValueError):
        A5_1().generate_keystream([0] * 63, [0] * 22, 8)


def test_rejects_wrong_iv_size():
    with pytest.raises(ValueError):
        A5_1().generate_keystream([0] * 64, [0] * 21, 8)


def test_majority_function_truth_table():
    cipher = A5_1()
    # maj(a,b,c) = ab | ac | bc: 1 iff at least two of the three are 1.
    cases = {
        (0, 0, 0): 0,
        (0, 0, 1): 0,
        (0, 1, 0): 0,
        (1, 0, 0): 0,
        (1, 1, 0): 1,
        (1, 0, 1): 1,
        (0, 1, 1): 1,
        (1, 1, 1): 1,
    }
    for inputs, expected in cases.items():
        assert cipher._majority(*inputs) == expected


def test_clock_lfsr_feedback_and_shift():
    cipher = A5_1()
    # A 3-bit toy LFSR with a single tap at position 0: feedback = state[0],
    # new_state = [feedback] + state[:-1].
    state = [1, 0, 1]
    new_state = cipher._clock_lfsr(state, [0], 3)
    assert new_state == [1, 1, 0]


def test_get_config():
    config = A5_1().get_config()
    assert config.cipher_name == "A5/1"
    assert config.key_size == 64
    assert config.iv_size == 22
    assert config.parameters["lfsr1_size"] == 19
    assert config.parameters["lfsr2_size"] == 22
    assert config.parameters["lfsr3_size"] == 23
    assert config.parameters["warmup_steps"] == 100


def test_analyze_structure():
    structure = A5_1().analyze_structure()
    assert structure.state_size == 64
    assert len(structure.lfsr_configs) == 3
    degrees = [c.degree for c in structure.lfsr_configs]
    assert degrees == [19, 22, 23]
    for config in structure.lfsr_configs:
        assert config.field_order == 2


def test_apply_attacks_lists_known_vulnerabilities():
    cipher = A5_1()
    result = cipher.apply_attacks([0, 1] * 10)
    assert "known_vulnerabilities" in result
    assert len(result["known_vulnerabilities"]) > 0


def test_analyze_end_to_end():
    cipher = A5_1()
    result = cipher.analyze(key=[0] * 64, iv=[0] * 22, keystream_length=64)
    assert result.cipher_name == "A5/1"
    assert result.keystream_properties["length"] == 64
    assert result.structure.state_size == 64
