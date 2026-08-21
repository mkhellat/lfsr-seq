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


class TestBranchesUnreachableViaRealCalls:
    """Covers branches (lines ~76-77, 119, 123, 164-167, 224-228) that
    this example script's own hardcoded demo inputs never actually
    trigger with the real (non-mocked) library functions:

    - example_algebraic_immunity()'s and_function(x0,x1,x2,x3)=x0&x1
      with num_inputs=4 is commented "low algebraic immunity" but
      compute_algebraic_immunity() actually reports optimal=True for
      it (independently verified: {'algebraic_immunity': 2,
      'optimal': True, 'max_possible': 2, ...}) -- so the "not
      optimal" warning branch (lines 76-77) is dead code in this
      script as written, not a bug in compute_algebraic_immunity
      itself (which is separately tested/verified correct elsewhere;
      see test_attacks.py).
    - groebner_basis_attack/cube_attack are placeholder
      implementations that always return attack_successful=False
      (see test_attacks.py's TestGroebnerBasisAttack /
      TestCubeAttack docstrings), so the attack_successful=True
      branches (lines 119, 164-167) can never be reached by this
      script's real calls either.
    - example_groebner_basis_attack()'s specific keystream/params
      combination produces a details dict without an 'error' key
      (independently verified), so line 123's `if 'error' in
      result.details` is never taken there (contrast with
      example_cube_attack(), whose keystream IS too short for
      max_cube_size=5 and does hit the analogous 'error' branch,
      already covered by test_example_cube_attack_runs above).
    - main()'s except block (lines 224-228) is unreachable with the
      script's own well-formed hardcoded inputs.

    All are exercised here via monkeypatching the underlying attack
    functions, isolating this script's print/branch logic from
    whether the real underlying functions happen to produce these
    outcomes for these particular hardcoded inputs."""

    def test_algebraic_immunity_not_optimal_branch(self, capsys, monkeypatch):
        def fake_compute_algebraic_immunity(func, num_inputs):
            return {
                "algebraic_immunity": 1,
                "annihilators_found": [],
                "optimal": False,
                "max_possible": 2,
                "num_inputs": num_inputs,
            }

        monkeypatch.setattr(
            example_module, "compute_algebraic_immunity", fake_compute_algebraic_immunity
        )
        example_module.example_algebraic_immunity()
        out = capsys.readouterr().out
        assert "VULNERABLE" in out
        assert "Vulnerable to algebraic attacks of degree" in out

    def test_groebner_basis_attack_successful_branch(self, capsys, monkeypatch):
        from dataclasses import dataclass, field
        from typing import Any, Dict, Optional

        @dataclass
        class _FakeResult:
            attack_successful: bool
            recovered_state: Optional[list]
            algebraic_immunity: int
            equations_solved: int
            complexity_estimate: float
            method_used: str
            details: Dict[str, Any] = field(default_factory=dict)

        def fake_groebner_basis_attack(**kwargs):
            return _FakeResult(
                attack_successful=True,
                recovered_state=[1, 0, 1, 1],
                algebraic_immunity=2,
                equations_solved=10,
                complexity_estimate=123.0,
                method_used="groebner_basis",
                details={},
            )

        monkeypatch.setattr(
            example_module, "groebner_basis_attack", fake_groebner_basis_attack
        )
        example_module.example_groebner_basis_attack()
        out = capsys.readouterr().out
        assert "Recovered state:" in out

    def test_groebner_basis_attack_error_detail_branch(self, capsys, monkeypatch):
        from dataclasses import dataclass, field
        from typing import Any, Dict, Optional

        @dataclass
        class _FakeResult:
            attack_successful: bool
            recovered_state: Optional[list]
            algebraic_immunity: int
            equations_solved: int
            complexity_estimate: float
            method_used: str
            details: Dict[str, Any] = field(default_factory=dict)

        def fake_groebner_basis_attack(**kwargs):
            return _FakeResult(
                attack_successful=False,
                recovered_state=None,
                algebraic_immunity=0,
                equations_solved=0,
                complexity_estimate=0.0,
                method_used="groebner_basis",
                details={"error": "simulated failure for coverage"},
            )

        monkeypatch.setattr(
            example_module, "groebner_basis_attack", fake_groebner_basis_attack
        )
        example_module.example_groebner_basis_attack()
        out = capsys.readouterr().out
        assert "Error: simulated failure for coverage" in out

    def test_cube_attack_successful_branch(self, capsys, monkeypatch):
        from dataclasses import dataclass, field
        from typing import Any, Dict

        @dataclass
        class _FakeCubeResult:
            attack_successful: bool
            cubes_found: int
            superpolies_computed: int
            recovered_bits: int
            complexity_estimate: float
            details: Dict[str, Any] = field(default_factory=dict)

        def fake_cube_attack(**kwargs):
            return _FakeCubeResult(
                attack_successful=True,
                cubes_found=3,
                superpolies_computed=5,
                recovered_bits=4,
                complexity_estimate=42.0,
                details={},
            )

        monkeypatch.setattr(example_module, "cube_attack", fake_cube_attack)
        example_module.example_cube_attack()
        out = capsys.readouterr().out
        assert "Attack succeeded!" in out
        assert "Cubes found: 3" in out
        assert "Superpolies computed: 5" in out
        assert "Recovered bits: 4" in out

    def test_main_except_block_on_unexpected_error(self, capsys, monkeypatch):
        def raiser():
            raise RuntimeError("simulated failure for coverage")

        monkeypatch.setattr(example_module, "example_algebraic_immunity", raiser)
        import pytest as _pytest

        with _pytest.raises(SystemExit) as exc_info:
            example_module.main()
        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "ERROR: simulated failure for coverage" in err

import sys


class TestSageImportGuardAlgebraic:
    """Regression coverage for the module-level
    `try: from sage.all import * / except ImportError: print(...);
    sys.exit(1)` guard in lfsr.examples.algebraic_attack_example (source lines near the
    top of the file). SageMath IS importable in this environment, so
    this branch is never hit by a normal import; force it by blocking
    only `sage.all` imports whose caller is this specific example
    module (a plain global block on "sage.all" would also break
    lfsr.cli/lfsr.sage_imports, which import it eagerly at package-init
    time via `import lfsr`)."""

    def test_missing_sage_all_prints_error_and_exits(self, capsys):
        import builtins
        import importlib

        import pytest

        real_import = builtins.__import__
        modname = "lfsr.examples.algebraic_attack_example"

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            caller = (globals or {}).get("__name__", "")
            if name == "sage.all" and caller == modname:
                raise ImportError("simulated: sage.all unavailable")
            return real_import(name, globals, locals, fromlist, level)

        if modname in sys.modules:
            del sys.modules[modname]

        builtins.__import__ = fake_import
        try:
            with pytest.raises(SystemExit) as exc_info:
                importlib.import_module(modname)
            assert exc_info.value.code == 1
        finally:
            builtins.__import__ = real_import
            if modname in sys.modules:
                del sys.modules[modname]
            importlib.import_module(modname)

        captured = capsys.readouterr()
        assert "SageMath is required" in captured.err
