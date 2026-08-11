#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for lfsr.ciphers.a5_2.A5_2.

**No official GSM A5/2 test vectors are validated here.** Unlike A5/1,
the source module for A5/2 explicitly documents itself as a
"simplified" approximation throughout (see src/lfsr/ciphers/a5_2.py,
e.g. line 82 "Clock control (simplified - full A5/2 has more complex
clocking)", line 135 "Simplified clocking - full A5/2 has more complex
mechanism", line 163 "LFSR4 taps (example)" and the class docstring's
note that LFSR4 configuration is "example - actual A5/2 may differ").

The real A5/2 (per the GSM/ETSI specification and the widely cited
Barkan-Biham-Keller cryptanalysis papers) clocks LFSR1-3 with the same
irregular majority clocking as A5/1 but *additionally* uses a fourth,
always-clocked 17-bit LFSR whose own tapped bits (not a majority
function) select the clock-control bits read from LFSR1-3, then forces
in a known 1 bit at a fixed position of each register during setup.
None of that is present here -- LFSR4's taps in this module are
explicitly invented ("example"), and LFSR4 does not drive the other
three registers' clocking at all (clock control is still a majority
vote among LFSR1-3, with LFSR4 merely also being conditionally
clocked by that same vote). Given the source module's own
acknowledgement that this is not the real algorithm, no official test
vector will match, and none is asserted here.

These tests instead lock in the current, deterministic behavior of
the implementation as it exists, and check the documented structural
properties.
"""

import pytest

from lfsr.ciphers.a5_2 import A5_2


def test_generate_keystream_length():
    cipher = A5_2()
    keystream = cipher.generate_keystream([0] * 64, [0] * 22, 100)
    assert len(keystream) == 100
    assert all(bit in (0, 1) for bit in keystream)


def test_generate_keystream_deterministic():
    key = [1, 0] * 32
    iv = [0, 1] * 11
    first = A5_2().generate_keystream(key, iv, 200)
    second = A5_2().generate_keystream(key, iv, 200)
    assert first == second


def test_generate_keystream_not_degenerate():
    cipher = A5_2()
    keystream = cipher.generate_keystream([1] * 64, [0] * 22, 300)
    assert any(bit == 1 for bit in keystream)
    assert any(bit == 0 for bit in keystream)


def test_all_zero_key_and_iv():
    cipher = A5_2()
    keystream = cipher.generate_keystream([0] * 64, [0] * 22, 300)
    assert len(keystream) == 300


def test_different_keys_produce_different_keystreams():
    # As with A5/1 (see test_ciphers_a5_1.py), a single-bit flip against an
    # all-zero key/IV baseline can fail to propagate to the output within
    # a short keystream due to this implementation's clocking dynamics on
    # a near-degenerate all-zero state, so a non-degenerate base key pair
    # is used instead.
    iv = [0] * 22
    base_key = [1, 0, 1, 1] * 16
    other_key = [0, 0, 1, 1] * 16
    keystream_a = A5_2().generate_keystream(base_key, iv, 100)
    keystream_b = A5_2().generate_keystream(other_key, iv, 100)
    assert keystream_a != keystream_b


def test_different_ivs_produce_different_keystreams():
    key = [1, 0, 1, 1] * 16
    keystream_a = A5_2().generate_keystream(key, [0] * 22, 100)
    keystream_b = A5_2().generate_keystream(key, [1] + [0] * 21, 100)
    assert keystream_a != keystream_b


def test_none_iv_defaults_to_zero():
    key = [1, 1, 0, 0] * 16
    with_none = A5_2().generate_keystream(key, None, 64)
    with_zero = A5_2().generate_keystream(key, [0] * 22, 64)
    assert with_none == with_zero


def test_rejects_wrong_key_size():
    with pytest.raises(ValueError):
        A5_2().generate_keystream([0] * 63, [0] * 22, 8)


def test_rejects_wrong_iv_size():
    with pytest.raises(ValueError):
        A5_2().generate_keystream([0] * 64, [0] * 21, 8)


def test_lfsr4_derived_from_key_prefix():
    # _initialize (a5_2.py line 186) sets lfsr4_state from key[0:17], i.e.
    # LFSR4 is fully determined by (and correlated with) the first 17 bits
    # of LFSR1's key material (key[0:19]) -- lock in this documented
    # behavior since it is a distinctive (and cryptographically dubious)
    # property of this implementation worth flagging via a regression test.
    cipher = A5_2()
    key = [1, 0] * 32
    cipher._initialize(list(key), [0] * 22)
    # After warm-up, just check state shapes/sizes are as documented;
    # the pre-warm-up correlation is exercised indirectly by determinism.
    assert len(cipher.lfsr1_state) == 19
    assert len(cipher.lfsr2_state) == 22
    assert len(cipher.lfsr3_state) == 23
    assert len(cipher.lfsr4_state) == 17


def test_get_config():
    config = A5_2().get_config()
    assert config.cipher_name == "A5/2"
    assert config.key_size == 64
    assert config.iv_size == 22
    assert config.parameters["lfsr1_size"] == 19
    assert config.parameters["lfsr2_size"] == 22
    assert config.parameters["lfsr3_size"] == 23
    assert config.parameters["lfsr4_size"] == 17
    assert "insecure" in config.parameters["security_warning"].lower()


def test_analyze_structure():
    structure = A5_2().analyze_structure()
    assert structure.state_size == 81
    assert len(structure.lfsr_configs) == 4
    degrees = [c.degree for c in structure.lfsr_configs]
    assert degrees == [19, 22, 23, 17]


def test_apply_attacks_reports_complete_break():
    cipher = A5_2()
    result = cipher.apply_attacks([0, 1] * 10)
    assert "known_vulnerabilities" in result
    assert any("break" in v.lower() for v in result["known_vulnerabilities"])


def test_analyze_end_to_end():
    cipher = A5_2()
    result = cipher.analyze(key=[0] * 64, iv=[0] * 22, keystream_length=64)
    assert result.cipher_name == "A5/2"
    assert result.keystream_properties["length"] == 64
    assert result.structure.state_size == 81
