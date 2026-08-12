#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for lfsr.cli_nist -- CLI plumbing for the NIST SP 800-22 statistical
test suite. The underlying NIST test implementations are covered under
tests/test_nist.py (93% coverage, with bugs found/fixed there); these
tests only check file-loading and CLI dispatch/output formatting.
"""

import io

import pytest

from lfsr.cli_nist import load_sequence_from_file, perform_nist_test_cli


def make_sequence(n=200):
    """Deterministic pseudo-random-looking 0/1 sequence for smoke tests
    (not intended to be cryptographically meaningful; NIST test correctness
    is validated in test_nist.py, not here)."""
    seq = []
    x = 12345
    for _ in range(n):
        x = (1103515245 * x + 12345) % (2**31)
        seq.append(x & 1)
    return seq


class TestLoadSequenceFromFile:
    def test_one_bit_per_line(self, tmp_path):
        f = tmp_path / "seq.txt"
        f.write_text("1\n0\n1\n1\n0\n")
        seq = load_sequence_from_file(str(f))
        assert seq == [1, 0, 1, 1, 0]

    def test_space_separated(self, tmp_path):
        f = tmp_path / "seq.txt"
        f.write_text("1 0 1 1 0 0 1")
        seq = load_sequence_from_file(str(f))
        assert seq == [1, 0, 1, 1, 0, 0, 1]

    def test_missing_file_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="Sequence file not found"):
            load_sequence_from_file(str(tmp_path / "nope.txt"))

    def test_invalid_bit_value_raises_value_error(self, tmp_path):
        f = tmp_path / "seq.txt"
        f.write_text("1\n2\n0\n")
        with pytest.raises(ValueError, match="Invalid bit value"):
            load_sequence_from_file(str(f))

    def test_non_integer_token_raises_value_error(self, tmp_path):
        f = tmp_path / "seq.txt"
        f.write_text("1\nabc\n0\n")
        with pytest.raises(ValueError, match="Invalid bit value"):
            load_sequence_from_file(str(f))

    def test_blank_lines_skipped(self, tmp_path):
        f = tmp_path / "seq.txt"
        f.write_text("1\n\n0\n\n1\n")
        seq = load_sequence_from_file(str(f))
        assert seq == [1, 0, 1]


class TestPerformNistTestCli:
    def test_basic_run_produces_summary(self):
        buf = io.StringIO()
        seq = make_sequence(500)
        perform_nist_test_cli(seq, output_file=buf, significance_level=0.01, block_size=128)
        out = buf.getvalue()
        assert "NIST SP 800-22 Statistical Test Suite" in out
        assert "Tests Passed:" in out
        assert "Tests Failed:" in out
        assert "Pass Rate:" in out
        assert "Overall Assessment:" in out

    def test_sequence_stats_reported_correctly(self):
        buf = io.StringIO()
        seq = [1, 1, 1, 1, 0, 0, 0, 0]  # 4 ones, 4 zeros
        perform_nist_test_cli(seq, output_file=buf)
        out = buf.getvalue()
        assert "Length: 8 bits" in out
        assert "Ones: 4" in out
        assert "Zeros: 4" in out

    def test_significance_level_reflected_in_output(self):
        buf = io.StringIO()
        seq = make_sequence(200)
        perform_nist_test_cli(seq, output_file=buf, significance_level=0.05)
        out = buf.getvalue()
        assert "Significance Level: 0.05" in out

    def test_output_defaults_to_stdout(self, capsys):
        seq = make_sequence(200)
        perform_nist_test_cli(seq)
        captured = capsys.readouterr()
        assert "NIST SP 800-22" in captured.out

    def test_individual_test_results_listed(self):
        buf = io.StringIO()
        seq = make_sequence(500)
        perform_nist_test_cli(seq, output_file=buf)
        out = buf.getvalue()
        assert "Individual Test Results" in out
        assert "Detailed Results" in out
        assert "Interpretation" in out

    def test_json_export_writes_named_file_when_output_file_has_name(self, tmp_path):
        out_path = tmp_path / "results.txt"
        seq = make_sequence(300)
        with open(out_path, "w") as f:
            perform_nist_test_cli(
                seq, output_file=f, significance_level=0.01, output_format="json"
            )

        export_path = tmp_path / "results.json"
        assert export_path.exists()
        content = export_path.read_text()
        assert content.strip() != ""

        # Confirm the main output file notes the export
        assert "Results exported to" in out_path.read_text()

    def test_export_format_with_unnamed_output_notes_missing_filename(self):
        buf = io.StringIO()  # StringIO has no .name attribute
        seq = make_sequence(200)
        perform_nist_test_cli(seq, output_file=buf, output_format="csv")
        out = buf.getvalue()
        assert "no output file specified" in out
