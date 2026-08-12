#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for lfsr.cli_ciphers -- the CLI plumbing for stream cipher analysis
(A5/1, A5/2, E0, Grain-128/128a, LILI-128, Trivium). The cipher
implementations themselves are already covered under
tests/test_ciphers_*.py; these tests only check argument handling,
dispatch, and output formatting of the CLI wrapper functions.
"""

import io

import pytest

from lfsr.cli_ciphers import (
    get_cipher_instance,
    load_bits_from_file,
    perform_cipher_analysis_cli,
)


class TestGetCipherInstance:
    def test_all_known_ciphers_resolve(self):
        for name in ["a5_1", "a5_2", "e0", "trivium", "grain128", "grain128a", "lili128"]:
            cipher = get_cipher_instance(name)
            assert cipher is not None

    def test_unknown_cipher_raises(self):
        with pytest.raises(ValueError, match="Unknown cipher"):
            get_cipher_instance("des")


class TestLoadBitsFromFile:
    def test_text_file_of_bits_is_parsed_as_text(self, tmp_path):
        """Regression test (bug fixed 2026-08-12, see commit history):
        load_bits_from_file's docstring claims it "Supports both binary
        files and text files with 0/1 characters" via a try/except
        fallback -- opening the file in 'rb' mode first, falling back to
        text-mode 0/1 parsing only if that raised. But
        `open(path, 'rb').read()` essentially never raises for a normal
        existing file, so the text-mode fallback was dead code. A
        plain-text file containing "101100" used to be interpreted as 6
        raw ASCII bytes and unpacked bit-by-bit, producing 48 bits of
        binary noise instead of the intended 6-bit list [1, 0, 1, 1, 0,
        0]. Fixed by detecting whether the decoded, stripped content
        consists only of '0'/'1' characters and parsing it as text-mode
        bits in that case, falling back to raw binary unpacking
        otherwise."""
        f = tmp_path / "bits.txt"
        f.write_text("101100")
        bits = load_bits_from_file(str(f))
        assert bits == [1, 0, 1, 1, 0, 0]

    def test_binary_file_produces_128_bits_for_16_bytes(self, tmp_path):
        f = tmp_path / "bits.bin"
        f.write_bytes(bytes([0xFF] * 16))
        bits = load_bits_from_file(str(f))
        assert len(bits) == 128
        assert all(b == 1 for b in bits)


class TestPerformCipherAnalysisCli:
    def test_analyze_structure_grain128(self):
        buf = io.StringIO()
        perform_cipher_analysis_cli(
            cipher_name="grain128",
            analyze_structure=True,
            output_file=buf,
        )
        out = buf.getvalue()
        assert "Grain-128" in out
        assert "Cipher Structure Analysis" in out
        assert "Number of LFSRs" in out

    def test_generate_keystream_default_key_iv(self):
        buf = io.StringIO()
        perform_cipher_analysis_cli(
            cipher_name="grain128",
            generate_keystream=True,
            keystream_length=64,
            output_file=buf,
        )
        out = buf.getvalue()
        assert "Using default key (all 1s)" in out
        assert "Using default IV (all 0s)" in out
        assert "Generated 64 keystream bits" in out

    def test_generate_keystream_with_key_and_iv_files(self, tmp_path, capsys):
        # Grain-128: key_size=128, iv_size=96. A 128-char "1"*128 and
        # 96-char "0"*96 text file now parse (post-fix) as exactly
        # 128/96 text-mode bits, matching the cipher's expected sizes
        # with no mismatch warning.
        key_file = tmp_path / "key.txt"
        key_file.write_text("1" * 128)
        iv_file = tmp_path / "iv.txt"
        iv_file.write_text("0" * 96)

        buf = io.StringIO()
        perform_cipher_analysis_cli(
            cipher_name="grain128",
            generate_keystream=True,
            keystream_length=32,
            key_file=str(key_file),
            iv_file=str(iv_file),
            output_file=buf,
        )
        out = buf.getvalue()
        assert "Using default key" not in out
        assert "Using default IV" not in out
        assert "Generated 32 keystream bits" in out
        captured = capsys.readouterr()
        assert "Key size mismatch" not in captured.err
        assert "IV size mismatch" not in captured.err

    def test_generate_keystream_key_size_mismatch_warns_and_pads(self, tmp_path, capsys):
        key_file = tmp_path / "key.txt"
        key_file.write_text("11")  # way too short for grain128 (needs 128 bits)

        buf = io.StringIO()
        perform_cipher_analysis_cli(
            cipher_name="grain128",
            generate_keystream=True,
            keystream_length=16,
            key_file=str(key_file),
            output_file=buf,
        )
        captured = capsys.readouterr()
        assert "Key size mismatch" in captured.err

    def test_compare_ciphers(self):
        buf = io.StringIO()
        perform_cipher_analysis_cli(
            cipher_name="a5_1",
            compare=True,
            output_file=buf,
        )
        out = buf.getvalue()
        assert "Comparing Multiple Ciphers" in out

    def test_output_defaults_to_stdout(self, capsys):
        perform_cipher_analysis_cli(cipher_name="a5_1")
        captured = capsys.readouterr()
        assert "A5/1" in captured.out

    def test_basic_info_always_printed(self):
        buf = io.StringIO()
        perform_cipher_analysis_cli(cipher_name="trivium", output_file=buf)
        out = buf.getvalue()
        assert "Cipher: Trivium" in out
        assert "Key size:" in out
        assert "IV size:" in out
