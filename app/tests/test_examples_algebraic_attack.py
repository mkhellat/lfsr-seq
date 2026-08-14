#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Smoke tests for lfsr.examples.algebraic_attack_example.

Standalone demo/tutorial script (see src/lfsr/examples/__init__.py) --
not part of the public API, not imported by library code, not wired
into the CLI. Smoke testing only: does each ``example_*()`` function
(and ``main()``) run to completion without raising, with stdout
captured. The underlying library calls (lfsr.attacks: algebraic
immunity, Groebner basis attack, cube attack) are exercised here only
incidentally -- deep correctness of those is out of scope.

All 4 example functions and ``main()`` were run directly against this
repo's SageMath install before writing any assertion below; all
completed without raising (verified 2026-08-14).
"""

import lfsr.examples.algebraic_attack_example as example_module


class TestIndividualExamples:
    def test_example_algebraic_immunity_runs(self, capsys):
        example_module.example_algebraic_immunity()
        out = capsys.readouterr().out
        assert "Algebraic Immunity" in out

    def test_example_groebner_basis_attack_runs(self, capsys):
        example_module.example_groebner_basis_attack()
        out = capsys.readouterr().out
        assert "Gröbner Basis Attack" in out

    def test_example_cube_attack_runs(self, capsys):
        example_module.example_cube_attack()
        out = capsys.readouterr().out
        assert "Cube Attack Results" in out

    def test_example_comparison_runs(self, capsys):
        example_module.example_comparison()
        out = capsys.readouterr().out
        assert "Attack Method Comparison" in out


class TestMain:
    def test_main_runs_end_to_end(self, capsys):
        example_module.main()
        out = capsys.readouterr().out
        assert "Examples Complete!" in out
