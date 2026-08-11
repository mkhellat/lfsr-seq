#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for lfsr.ciphers.trivium.Trivium.

Validated against the official eSTREAM TRIVIUM test vectors
(profile H3, 80-bit key / 80-bit IV), published at:
https://github.com/bmkessler/trivium/blob/master/trivium-80.80.test-vectors
(a checked-in copy of the reference eSTREAM test-vector file distributed
with the reference `ecrypt` test suite).

**Bit-ordering convention** (determined empirically -- see below): the
eSTREAM test vectors express key/IV/keystream as hex strings. Converting
a hex string to a bit list via "LSB-first per byte" (i.e.
``[(byte >> i) & 1 for byte in data for i in range(8)]``, matching a
verified independent reference implementation at
https://github.com/wuhanstudio/trivium/blob/master/trivium-python/trivium.py)
gives the register-loading order used by *that* reference implementation.
However, matching the official eSTREAM keystream additionally requires
**reversing** the resulting 80-bit key/IV bit list before loading, and
packing the output keystream bits back to hex MSB-first (no reversal).
This combination was found by brute-force search over the (key order,
output order) possibilities and independently confirmed against a
from-scratch reference implementation of the standard Trivium recursive
equations (De Canniere & Preneel), so it is not an artifact of one
particular reference script. See ``_hex_to_key_bits`` / ``_bits_to_hex``
below for the exact transform used in these tests.

**BUG FOUND AND FIXED** (2026-08-11, see commit history):
``lfsr.ciphers.trivium.Trivium._clock_trivium`` used to compute each
register's feedback using **its own** two tap/AND terms instead of the
**preceding** register's, i.e. the three feedback formulas were each
internally consistent but cross-wired one register short of the correct
dependency chain. The correct recursive equations (in 1-indexed spec
notation) are:

    a_i = c_(i-66) + c_(i-111) + c_(i-110)*c_(i-109) + a_(i-69)
    b_i = a_(i-66) + a_(i-93) + a_(i-92)*a_(i-91)     + b_(i-78)
    c_i = b_(i-69) + b_(i-84) + b_(i-83)*b_(i-82)     + c_(i-87)

i.e. register A's feedback must depend on register C's taps, B's on A's,
and C's on B's, with the linear-feedback tap (the non-AND term) coming
from the *same* register the AND term was one step later than the read
offset for the output function -- concretely, C's own linear feedback
term is ``reg_c[86]`` (spec offset i-87), not ``reg_c[108]`` (the output
function's read offset, which was mistakenly reused). Fixed to:

    feedback_a = (reg_c[65]^reg_c[110]) ^ (reg_c[108]&reg_c[109]) ^ reg_a[68]
    feedback_b = (reg_a[65]^reg_a[92])  ^ (reg_a[90]&reg_a[91])   ^ reg_b[77]
    feedback_c = (reg_b[68]^reg_b[83])  ^ (reg_b[81]&reg_b[82])   ^ reg_c[86]

Verified bit-for-bit against the official eSTREAM keystream for both
test vectors below (previously this cross-check -- an independent
from-scratch implementation of the correct recursion, see
``test_reference_recursion_matches_estream_vector_0`` -- was the only
thing that matched; now the real ``Trivium`` class matches it too).
"""

import pytest

from lfsr.ciphers.trivium import Trivium


def _hex_to_key_bits(hex_str):
    """Convert an eSTREAM key/IV hex string to the bit list this module's
    generate_keystream() must be fed to reproduce the official vectors.

    See the module docstring for how this convention was derived.
    """
    data = bytes.fromhex(hex_str)
    bits = [(byte >> i) & 1 for byte in data for i in range(8)]
    return bits[::-1]


def _bits_to_hex(bits):
    """Pack a keystream bit list back to a hex string.

    Uses LSB-first-per-byte packing (bit j of each 8-bit group becomes bit
    j of the output byte) -- this is the convention that reproduces the
    official eSTREAM keystream bytes given the key/IV loading convention
    in ``_hex_to_key_bits`` above (empirically confirmed, see module
    docstring).
    """
    out = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            byte |= bits[i + j] << j
        out.append(byte)
    return out.hex().upper()


# Official eSTREAM TRIVIUM test vectors (profile H3), Set 1, vector# 0 and
# vector# 9 -- see module docstring for source.
ESTREAM_VECTOR_0 = {
    "key": "80000000000000000000",
    "iv": "00000000000000000000",
    "stream_0_63": (
        "38EB86FF730D7A9CAF8DF13A4420540D"
        "BB7B651464C87501552041C249F29A64"
        "D2FBF515610921EBE06C8F92CECF7F80"
        "98FF20CCCC6A62B97BE8EF7454FC80F9"
    ),
}

ESTREAM_VECTOR_9 = {
    "key": "00400000000000000000",
    "iv": "00000000000000000000",
    "stream_0_63": (
        "61208D286BC1DC431171EDA5CAF79D95"
        "60B18ACEF26484417B651A47A3F7A803"
        "53F79AF8656DA4301A5E5A02E04265B1"
        "82C67F5891220349F8CD1CD06597B77E"
    ),
}


@pytest.mark.parametrize("vector", [ESTREAM_VECTOR_0, ESTREAM_VECTOR_9])
def test_matches_official_estream_vector(vector):
    """Bytes 0..63 of the keystream must equal the official eSTREAM
    TRIVIUM test vector (profile H3) for the given key/IV."""
    key_bits = _hex_to_key_bits(vector["key"])
    iv_bits = _hex_to_key_bits(vector["iv"])

    cipher = Trivium()
    keystream = cipher.generate_keystream(key_bits, iv_bits, 64 * 8)
    actual_hex = _bits_to_hex(keystream)

    assert actual_hex == vector["stream_0_63"]


def test_reference_recursion_matches_estream_vector_0():
    """Sanity check: an independent from-scratch implementation of the
    *correct* Trivium recursive equations (De Canniere & Preneel), fed the
    same bit-ordering convention used above, reproduces the official
    eSTREAM vector exactly. This validates the bit-ordering convention and
    test-vector transcription used in this file, independent of whatever
    bug exists in lfsr.ciphers.trivium.
    """
    key_bits = _hex_to_key_bits(ESTREAM_VECTOR_0["key"])
    iv_bits = _hex_to_key_bits(ESTREAM_VECTOR_0["iv"])

    reg_a = list(key_bits) + [0] * (93 - 80)
    reg_b = list(iv_bits) + [0] * (84 - 80)
    reg_c = [0] * (111 - 3) + [1, 1, 1]

    def step():
        nonlocal reg_a, reg_b, reg_c
        t1 = reg_a[65] ^ reg_a[92]
        t2 = reg_b[68] ^ reg_b[83]
        t3 = reg_c[65] ^ reg_c[110]
        out = t1 ^ t2 ^ t3
        feedback_a = t3 ^ (reg_c[108] & reg_c[109]) ^ reg_a[68]
        feedback_b = t1 ^ (reg_a[90] & reg_a[91]) ^ reg_b[77]
        feedback_c = t2 ^ (reg_b[81] & reg_b[82]) ^ reg_c[86]
        reg_a = [feedback_a] + reg_a[:-1]
        reg_b = [feedback_b] + reg_b[:-1]
        reg_c = [feedback_c] + reg_c[:-1]
        return out

    for _ in range(4 * 288):
        step()

    keystream = [step() for _ in range(64 * 8)]
    assert _bits_to_hex(keystream) == ESTREAM_VECTOR_0["stream_0_63"]


def test_generate_keystream_length():
    cipher = Trivium()
    keystream = cipher.generate_keystream([0] * 80, [0] * 80, 100)
    assert len(keystream) == 100
    assert all(bit in (0, 1) for bit in keystream)


def test_generate_keystream_deterministic():
    key = [1, 0] * 40
    iv = [0, 1] * 40
    first = Trivium().generate_keystream(key, iv, 200)
    second = Trivium().generate_keystream(key, iv, 200)
    assert first == second


def test_generate_keystream_not_degenerate():
    cipher = Trivium()
    keystream = cipher.generate_keystream([0] * 80, [0] * 80, 512)
    assert any(bit == 1 for bit in keystream)
    assert any(bit == 0 for bit in keystream)


def test_different_keys_produce_different_keystreams():
    iv = [0] * 80
    keystream_a = Trivium().generate_keystream([0] * 80, iv, 64)
    keystream_b = Trivium().generate_keystream([1] + [0] * 79, iv, 64)
    assert keystream_a != keystream_b


def test_different_ivs_produce_different_keystreams():
    key = [0] * 80
    keystream_a = Trivium().generate_keystream(key, [0] * 80, 64)
    keystream_b = Trivium().generate_keystream(key, [1] + [0] * 79, 64)
    assert keystream_a != keystream_b


def test_none_iv_defaults_to_zero():
    key = [0] * 80
    with_none = Trivium().generate_keystream(key, None, 32)
    with_zero = Trivium().generate_keystream(key, [0] * 80, 32)
    assert with_none == with_zero


def test_rejects_wrong_key_size():
    with pytest.raises(ValueError):
        Trivium().generate_keystream([0] * 79, [0] * 80, 8)


def test_rejects_wrong_iv_size():
    with pytest.raises(ValueError):
        Trivium().generate_keystream([0] * 80, [0] * 79, 8)


def test_get_config():
    config = Trivium().get_config()
    assert config.cipher_name == "Trivium"
    assert config.key_size == 80
    assert config.iv_size == 80
    assert config.parameters["reg_a_size"] == 93
    assert config.parameters["reg_b_size"] == 84
    assert config.parameters["reg_c_size"] == 111
    assert config.parameters["total_size"] == 288


def test_analyze_structure():
    structure = Trivium().analyze_structure()
    assert structure.state_size == 288
    assert "Non-linear" in structure.combiner or "non-linear" in structure.combiner
    assert len(structure.lfsr_configs) == 1


def test_apply_attacks_reports_secure_status():
    cipher = Trivium()
    result = cipher.apply_attacks([0, 1] * 10)
    assert result["known_vulnerabilities"] == []
    assert "no practical attacks found" == result["security_status"].lower()


def test_analyze_end_to_end():
    cipher = Trivium()
    result = cipher.analyze(key=[0] * 80, iv=[0] * 80, keystream_length=64)
    assert result.cipher_name == "Trivium"
    assert result.keystream_properties["length"] == 64
    assert result.structure.state_size == 288
