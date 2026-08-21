#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for lfsr.ciphers.e0.E0.

**No official Bluetooth E0 test vectors are validated here.** The real
E0 specification (Bluetooth Core Specification, Part H) uses a 4-bit
(16-state) finite state machine derived from the summation generator of
Massey and Rueppel: the FSM's next state is computed from a 2-bit
"carry" value that is itself derived via integer division/modulo of a
weighted sum of the four LFSR output bits and the previous FSM state,
and the initial 132-bit state is built from the 128-bit key, a 48-bit
Bluetooth device address, and a 26-bit clock/counter value -- not a
64-bit generic IV XORed in directly.

``lfsr.ciphers.e0.E0`` explicitly documents its FSM as simplified (see
src/lfsr/ciphers/e0.py, class docstring "FSM: Finite state machine with
4 states (2 bits)" and ``_fsm_update``'s comment "Simplified FSM - full
E0 FSM is more complex", lines 115-139). The implemented FSM here is a
2-bit (4-state) linear-ish combiner (``(x1+x2+x3+x4+s0) % 2`` for output,
simple XOR-based state update) rather than the real carry-propagating
summation generator, and key/IV loading is a direct 128-bit key split
across four LFSRs XORed with a 64-bit IV rather than the real
key+address+clock construction. Given this structural mismatch with the
Bluetooth specification, no official E0 keystream can match this
implementation, and none is asserted here.

These tests lock in the current, deterministic behavior and the
documented (if simplified) structural properties.
"""

import pytest

from lfsr.ciphers.e0 import E0


def test_generate_keystream_length():
    cipher = E0()
    keystream = cipher.generate_keystream([0] * 128, [0] * 64, 100)
    assert len(keystream) == 100
    assert all(bit in (0, 1) for bit in keystream)


def test_generate_keystream_deterministic():
    key = [1, 0] * 64
    iv = [0, 1] * 32
    first = E0().generate_keystream(key, iv, 200)
    second = E0().generate_keystream(key, iv, 200)
    assert first == second


def test_generate_keystream_not_degenerate():
    cipher = E0()
    keystream = cipher.generate_keystream([1] * 128, [0] * 64, 300)
    assert any(bit == 1 for bit in keystream)
    assert any(bit == 0 for bit in keystream)


def test_all_zero_key_and_iv():
    cipher = E0()
    keystream = cipher.generate_keystream([0] * 128, [0] * 64, 300)
    assert len(keystream) == 300


def test_different_keys_produce_different_keystreams():
    iv = [0] * 64
    keystream_a = E0().generate_keystream([0] * 128, iv, 100)
    keystream_b = E0().generate_keystream([1] + [0] * 127, iv, 100)
    assert keystream_a != keystream_b


def test_different_ivs_produce_different_keystreams():
    key = [1, 0, 1, 1] * 32
    keystream_a = E0().generate_keystream(key, [0] * 64, 100)
    keystream_b = E0().generate_keystream(key, [1] + [0] * 63, 100)
    assert keystream_a != keystream_b


def test_none_iv_defaults_to_zero():
    key = [1, 1, 0, 0] * 32
    with_none = E0().generate_keystream(key, None, 64)
    with_zero = E0().generate_keystream(key, [0] * 64, 64)
    assert with_none == with_zero


def test_rejects_wrong_key_size():
    with pytest.raises(ValueError):
        E0().generate_keystream([0] * 127, [0] * 64, 8)


def test_rejects_wrong_iv_size():
    with pytest.raises(ValueError):
        E0().generate_keystream([0] * 128, [0] * 63, 8)


def test_fsm_update_output_and_state_formula():
    cipher = E0()
    cipher.fsm_state = [1, 0]
    output, new_state = cipher._fsm_update(1, 0, 1, 1)
    # output = (x1+x2+x3+x4+s0) % 2 = (1+0+1+1+1) % 2 = 0
    assert output == 0
    # new_s0 = (s1+x1+x2) % 2 = (0+1+0) % 2 = 1
    # new_s1 = (s0+x3+x4) % 2 = (1+1+1) % 2 = 1
    assert new_state == [1, 1]
    assert cipher.fsm_state == [1, 1]


def test_clock_lfsr_feedback_and_shift():
    cipher = E0()
    state = [0, 1, 0]
    new_state = cipher._clock_lfsr(state, [1], 3)
    assert new_state == [1, 0, 1]


def test_get_config():
    config = E0().get_config()
    assert config.cipher_name == "E0"
    assert config.key_size == 128
    assert config.iv_size == 64
    assert config.parameters["lfsr1_size"] == 25
    assert config.parameters["lfsr2_size"] == 31
    assert config.parameters["lfsr3_size"] == 33
    assert config.parameters["lfsr4_size"] == 39
    assert config.parameters["warmup_steps"] == 200


def test_analyze_structure():
    structure = E0().analyze_structure()
    assert structure.state_size == 128
    assert len(structure.lfsr_configs) == 4
    degrees = [c.degree for c in structure.lfsr_configs]
    assert degrees == [25, 31, 33, 39]
    assert "clock every step" in structure.clock_control.lower()


def test_apply_attacks_lists_known_vulnerabilities():
    cipher = E0()
    result = cipher.apply_attacks([0, 1] * 10)
    assert len(result["known_vulnerabilities"]) > 0


def test_analyze_end_to_end():
    cipher = E0()
    result = cipher.analyze(key=[0] * 128, iv=[0] * 64, keystream_length=64)
    assert result.cipher_name == "E0"
    assert result.keystream_properties["length"] == 64
    assert result.structure.state_size == 128


def test_initialize_padding_loops_are_dead_code():
    """SUSPECTED DEAD CODE: e0.py's _initialize() (lines 191-195) has
    `while len(self.lfsr3_state) < 33: ...append(0)` and the equivalent
    for lfsr4_state/39, guarding against a too-short slice. But
    lfsr3_state is set from `key[56:89]` and lfsr4_state from
    `key[89:128]` (lines 186-189), and _initialize already unconditionally
    rejects any key whose length isn't exactly 128 (lines 176-177, `if
    len(key) != 128: raise ValueError`). For any key that passes that
    check, `key[56:89]` is always exactly 33 elements and `key[89:128]`
    is always exactly 39 elements (confirmed: for a 128-length list,
    len(key[56:89]) == 33 and len(key[89:128]) == 39 always) -- so the
    padding while loops can never execute via any real call. Cover them
    directly here with a key-like object whose __getitem__ returns
    artificially short slices for exactly the [56:89]/[89:128] ranges
    (while still reporting len() == 128 so the earlier length check
    passes), forcing the padding loops to actually run, to document the
    unreachability under real list inputs rather than leave it
    uncovered."""

    class ShortSlicingKey(list):
        def __getitem__(self, item):
            result = super().__getitem__(item)
            if isinstance(item, slice) and item == slice(56, 89):
                return result[:10]  # force lfsr3_state short (< 33)
            if isinstance(item, slice) and item == slice(89, 128):
                return result[:5]  # force lfsr4_state short (< 39)
            return result

    key = ShortSlicingKey([0] * 128)
    cipher = E0()

    cipher._initialize(key, [0] * 64)

    assert len(cipher.lfsr3_state) == 33
    assert len(cipher.lfsr4_state) == 39
    # The padded tail entries are the appended zeros.
    assert cipher.lfsr3_state[-1] == 0
    assert cipher.lfsr4_state[-1] == 0
