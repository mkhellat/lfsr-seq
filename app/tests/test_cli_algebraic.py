#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for lfsr.cli_algebraic -- CLI plumbing for algebraic attacks
(Groebner basis, cube attack, algebraic immunity). The underlying attack
algorithms are covered under tests/test_attacks.py; these tests check
argument handling, dispatch, error paths, and output formatting.
"""

import io

import pytest

from lfsr.cli_algebraic import perform_algebraic_attack_cli

# Small primitive GF(2) LFSR: x^3+x+1
COEFFS = [1, 1, 0]
KEYSTREAM = [1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1]


def xor3(a, b, c):
    return a ^ b ^ c


class TestPerformAlgebraicAttackCli:
    def test_no_coefficients_and_no_config_file_exits(self):
        buf = io.StringIO()
        with pytest.raises(SystemExit):
            perform_algebraic_attack_cli(
                lfsr_coefficients=None,
                keystream=KEYSTREAM,
                output_file=buf,
            )

    def test_config_file_without_coefficients_exits(self):
        buf = io.StringIO()
        with pytest.raises(SystemExit):
            perform_algebraic_attack_cli(
                lfsr_config_file="somefile.json",
                lfsr_coefficients=None,
                keystream=KEYSTREAM,
                output_file=buf,
            )

    def test_no_keystream_exits(self):
        buf = io.StringIO()
        with pytest.raises(SystemExit):
            perform_algebraic_attack_cli(
                lfsr_coefficients=COEFFS,
                keystream=None,
                keystream_file=None,
                output_file=buf,
            )

    def test_groebner_basis_attack_runs(self):
        buf = io.StringIO()
        perform_algebraic_attack_cli(
            lfsr_coefficients=COEFFS,
            field_order=2,
            keystream=KEYSTREAM,
            method="groebner_basis",
            output_file=buf,
        )
        out = buf.getvalue()
        assert "Gröbner Basis Attack" in out
        assert "Attack successful:" in out
        assert "Equations solved:" in out

    def test_cube_attack_runs(self):
        buf = io.StringIO()
        perform_algebraic_attack_cli(
            lfsr_coefficients=COEFFS,
            field_order=2,
            keystream=KEYSTREAM,
            method="cube_attack",
            max_cube_size=3,
            output_file=buf,
        )
        out = buf.getvalue()
        assert "Cube Attack" in out
        assert "Cubes found:" in out

    def test_algebraic_immunity_without_filtering_function_exits(self):
        buf = io.StringIO()
        with pytest.raises(SystemExit):
            perform_algebraic_attack_cli(
                lfsr_coefficients=COEFFS,
                field_order=2,
                keystream=KEYSTREAM,
                method="algebraic_immunity",
                filtering_function=None,
                output_file=buf,
            )

    def test_algebraic_immunity_with_filtering_function_runs(self):
        buf = io.StringIO()
        perform_algebraic_attack_cli(
            lfsr_coefficients=COEFFS,
            field_order=2,
            keystream=KEYSTREAM,
            method="algebraic_immunity",
            filtering_function=xor3,
            output_file=buf,
        )
        out = buf.getvalue()
        assert "Algebraic immunity:" in out
        assert "Maximum possible:" in out

    def test_unknown_method_exits(self):
        buf = io.StringIO()
        with pytest.raises(SystemExit):
            perform_algebraic_attack_cli(
                lfsr_coefficients=COEFFS,
                field_order=2,
                keystream=KEYSTREAM,
                method="bogus_method",
                output_file=buf,
            )

    def test_keystream_from_file(self, tmp_path):
        ks_file = tmp_path / "ks.txt"
        ks_file.write_text(" ".join(str(b) for b in KEYSTREAM))

        buf = io.StringIO()
        perform_algebraic_attack_cli(
            lfsr_coefficients=COEFFS,
            field_order=2,
            keystream_file=str(ks_file),
            method="groebner_basis",
            output_file=buf,
        )
        out = buf.getvalue()
        assert f"Loaded {len(KEYSTREAM)} bits" in out

    def test_output_defaults_to_stdout(self, capsys):
        perform_algebraic_attack_cli(
            lfsr_coefficients=COEFFS,
            field_order=2,
            keystream=KEYSTREAM,
            method="groebner_basis",
        )
        captured = capsys.readouterr()
        assert "LFSR Configuration" in captured.out

    def test_algebraic_immunity_reports_non_optimal_for_unbalanced_function(self):
        """AND of 3 inputs is unbalanced (only [1,1,1] gives output 1),
        triggering compute_algebraic_immunity's 'not optimal' path --
        exercises the else branch in perform_algebraic_attack_cli that
        prints the 'does not achieve maximum' warning."""
        def and3(a, b, c):
            return a & b & c

        buf = io.StringIO()
        perform_algebraic_attack_cli(
            lfsr_coefficients=COEFFS,
            field_order=2,
            keystream=KEYSTREAM,
            method="algebraic_immunity",
            filtering_function=and3,
            output_file=buf,
        )
        out = buf.getvalue()
        assert "does not achieve maximum algebraic immunity" in out
        assert "Vulnerable to algebraic attacks of degree" in out

    def test_lfsr_config_info_printed(self):
        buf = io.StringIO()
        perform_algebraic_attack_cli(
            lfsr_coefficients=COEFFS,
            field_order=2,
            keystream=KEYSTREAM,
            method="groebner_basis",
            output_file=buf,
        )
        out = buf.getvalue()
        assert "Coefficients: [1, 1, 0]" in out
        assert "Degree: 3" in out
        assert "Field order: 2" in out
