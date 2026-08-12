#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for lfsr.cli_tmto -- CLI plumbing for time-memory trade-off attacks
(Hellman/Rainbow tables). The TMTO algorithms themselves are covered
under tests/test_tmto.py; these tests check dispatch, argument handling,
and output formatting, calling perform_tmto_attack_cli directly with
int field_order (as the underlying tmto.py / attacks.py functions
require -- see the separately-reported cli.py bug where the CLI wires
a raw argparse *string* gf_order into this function's field_order
parameter).
"""

import io
import json

import pytest

from lfsr.cli_tmto import perform_tmto_attack_cli

COEFFS = [1, 1, 0]  # GF(2), degree 3


class TestPerformTmtoAttackCli:
    def test_hellman_method_default_target_state(self):
        buf = io.StringIO()
        perform_tmto_attack_cli(
            lfsr_coefficients=COEFFS,
            field_order=2,
            method="hellman",
            chain_count=20,
            chain_length=5,
            output_file=buf,
        )
        out = buf.getvalue()
        assert "Time-Memory Trade-Off Attack" in out
        assert "Method: hellman" in out
        assert "Using default target state" in out
        assert "TMTO Attack Results" in out

    def test_rainbow_method_runs(self):
        buf = io.StringIO()
        perform_tmto_attack_cli(
            lfsr_coefficients=COEFFS,
            field_order=2,
            method="rainbow",
            chain_count=20,
            chain_length=5,
            output_file=buf,
        )
        out = buf.getvalue()
        assert "Method: rainbow" in out

    def test_explicit_target_state(self):
        buf = io.StringIO()
        perform_tmto_attack_cli(
            lfsr_coefficients=COEFFS,
            field_order=2,
            target_state=[1, 0, 1],
            chain_count=20,
            chain_length=5,
            output_file=buf,
        )
        out = buf.getvalue()
        assert "Target state: [1, 0, 1]" in out
        assert "Using default target state" not in out

    def test_state_space_size_and_config_printed(self):
        buf = io.StringIO()
        perform_tmto_attack_cli(
            lfsr_coefficients=COEFFS,
            field_order=2,
            chain_count=20,
            chain_length=5,
            output_file=buf,
        )
        out = buf.getvalue()
        # GF(2)^3 = 8 states
        assert "State space size: 8" in out
        assert "Coefficients: [1, 1, 0]" in out
        assert "Degree: 3" in out

    def test_bad_table_file_falls_back_to_generating_new_table(self, tmp_path, capsys):
        table_file = tmp_path / "table.json"
        table_file.write_text("{not valid json")

        buf = io.StringIO()
        perform_tmto_attack_cli(
            lfsr_coefficients=COEFFS,
            field_order=2,
            chain_count=10,
            chain_length=5,
            table_file=str(table_file),
            output_file=buf,
        )
        out = buf.getvalue()
        assert "Generating new table instead" in out
        captured = capsys.readouterr()
        assert "Failed to load table" in captured.err

    def test_valid_precomputed_hellman_table_file_loads(self, tmp_path):
        table_file = tmp_path / "table.json"
        table_data = {
            "chain_count": 3,
            "chain_length": 4,
            "chains": [[0, 1], [2, 3], [4, 5]],
        }
        table_file.write_text(json.dumps(table_data))

        buf = io.StringIO()
        perform_tmto_attack_cli(
            lfsr_coefficients=COEFFS,
            field_order=2,
            method="hellman",
            chain_count=10,
            chain_length=5,
            table_file=str(table_file),
            output_file=buf,
        )
        out = buf.getvalue()
        assert "Loaded 3 chains" in out

    def test_output_defaults_to_stdout(self, capsys):
        perform_tmto_attack_cli(
            lfsr_coefficients=COEFFS,
            field_order=2,
            chain_count=10,
            chain_length=5,
        )
        captured = capsys.readouterr()
        assert "Time-Memory Trade-Off Attack" in captured.out

    def test_optimized_parameters_printed(self):
        buf = io.StringIO()
        perform_tmto_attack_cli(
            lfsr_coefficients=COEFFS,
            field_order=2,
            chain_count=10,
            chain_length=5,
            output_file=buf,
        )
        out = buf.getvalue()
        assert "Optimal chain count:" in out
        assert "Optimal chain length:" in out
        assert "Estimated coverage:" in out
