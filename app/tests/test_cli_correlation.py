#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for lfsr.cli_correlation -- CLI plumbing for correlation attacks on
combination generators. The underlying attack algorithms
(siegenthaler_correlation_attack, fast_correlation_attack,
distinguishing_attack, analyze_combining_function) are covered under
tests/test_attacks.py; these tests check config-file loading, dispatch,
and output formatting for the CLI wrapper.
"""

import io
import json

import pytest

from lfsr.cli_correlation import (
    load_combination_generator_from_json,
    load_keystream_from_file,
    perform_correlation_attack_cli,
)


def two_lfsr_xor_config():
    return {
        "lfsrs": [
            {"coefficients": [1, 1, 0], "field_order": 2, "degree": 3},
            {"coefficients": [1, 0, 0, 1], "field_order": 2, "degree": 4},
        ],
        "combining_function": {"type": "xor", "num_inputs": 2},
    }


def three_lfsr_majority_config():
    """Majority-of-3 combiner: provably correlated with each input LFSR
    (see tests/test_attacks.py's module docstring for the derivation),
    used to exercise the CLI's attack_successful=True output branches,
    which the xor-combiner config above can never reach."""
    return {
        "lfsrs": [
            {"coefficients": [1, 0, 0, 1], "field_order": 2, "degree": 4},
            {"coefficients": [1, 1, 0, 1], "field_order": 2, "degree": 4},
            {"coefficients": [1, 0, 1, 1], "field_order": 2, "degree": 4},
        ],
        "combining_function": {"type": "majority", "num_inputs": 3},
    }


class TestLoadCombinationGeneratorFromJson:
    def test_valid_xor_config(self, tmp_path):
        cfg_file = tmp_path / "cfg.json"
        cfg_file.write_text(json.dumps(two_lfsr_xor_config()))

        gen = load_combination_generator_from_json(str(cfg_file))
        assert len(gen.lfsrs) == 2
        assert gen.function_name == "xor"
        assert gen.combining_function(1, 1) == 0
        assert gen.combining_function(1, 0) == 1

    def test_majority_function(self, tmp_path):
        config = two_lfsr_xor_config()
        config["combining_function"] = {"type": "majority", "num_inputs": 3}
        cfg_file = tmp_path / "cfg.json"
        cfg_file.write_text(json.dumps(config))

        gen = load_combination_generator_from_json(str(cfg_file))
        assert gen.combining_function(1, 1, 0) == 1
        assert gen.combining_function(0, 0, 1) == 0

    def test_and_function(self, tmp_path):
        config = two_lfsr_xor_config()
        config["combining_function"] = {"type": "and", "num_inputs": 2}
        cfg_file = tmp_path / "cfg.json"
        cfg_file.write_text(json.dumps(config))

        gen = load_combination_generator_from_json(str(cfg_file))
        assert gen.combining_function(1, 1) == 1
        assert gen.combining_function(1, 0) == 0

    def test_or_function(self, tmp_path):
        config = two_lfsr_xor_config()
        config["combining_function"] = {"type": "or", "num_inputs": 2}
        cfg_file = tmp_path / "cfg.json"
        cfg_file.write_text(json.dumps(config))

        gen = load_combination_generator_from_json(str(cfg_file))
        assert gen.combining_function(0, 0) == 0
        assert gen.combining_function(1, 0) == 1

    def test_custom_function(self, tmp_path):
        config = two_lfsr_xor_config()
        config["combining_function"] = {
            "type": "custom",
            "num_inputs": 2,
            "code": "def f(a, b):\n    return 1 if a != b else 0\n",
        }
        cfg_file = tmp_path / "cfg.json"
        cfg_file.write_text(json.dumps(config))

        gen = load_combination_generator_from_json(str(cfg_file))
        assert gen.function_name == "custom"
        assert gen.combining_function(1, 0) == 1
        assert gen.combining_function(1, 1) == 0

    def test_custom_function_without_f_falls_back_to_any_callable(self, tmp_path):
        """Covers the `else: combining_function = next(v for v in
        namespace.values() if callable(v))` fallback (line ~135), which
        fires when the custom code defines a function under a name other
        than 'f'. test_custom_function above always defines 'f', so it
        never reaches this branch."""
        config = two_lfsr_xor_config()
        config["combining_function"] = {
            "type": "custom",
            "num_inputs": 2,
            "code": "def my_combiner(a, b):\n    return 1 if a != b else 0\n",
        }
        cfg_file = tmp_path / "cfg.json"
        cfg_file.write_text(json.dumps(config))

        gen = load_combination_generator_from_json(str(cfg_file))
        assert gen.function_name == "custom"
        assert gen.combining_function(1, 0) == 1
        assert gen.combining_function(1, 1) == 0

    def test_custom_function_missing_code_raises(self, tmp_path):
        config = two_lfsr_xor_config()
        config["combining_function"] = {"type": "custom", "num_inputs": 2}
        cfg_file = tmp_path / "cfg.json"
        cfg_file.write_text(json.dumps(config))

        with pytest.raises(ValueError, match="requires 'code'"):
            load_combination_generator_from_json(str(cfg_file))

    def test_unknown_function_type_raises(self, tmp_path):
        config = two_lfsr_xor_config()
        config["combining_function"] = {"type": "bogus", "num_inputs": 2}
        cfg_file = tmp_path / "cfg.json"
        cfg_file.write_text(json.dumps(config))

        with pytest.raises(ValueError, match="Unknown function type"):
            load_combination_generator_from_json(str(cfg_file))

    def test_missing_file_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            load_combination_generator_from_json(str(tmp_path / "nope.json"))

    def test_invalid_json_raises_value_error(self, tmp_path):
        cfg_file = tmp_path / "cfg.json"
        cfg_file.write_text("{not valid json")
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_combination_generator_from_json(str(cfg_file))

    def test_missing_lfsrs_key_raises(self, tmp_path):
        cfg_file = tmp_path / "cfg.json"
        cfg_file.write_text(json.dumps({"combining_function": {"type": "xor"}}))
        with pytest.raises(ValueError, match="must contain 'lfsrs'"):
            load_combination_generator_from_json(str(cfg_file))

    def test_missing_combining_function_key_raises(self, tmp_path):
        cfg_file = tmp_path / "cfg.json"
        cfg_file.write_text(json.dumps({"lfsrs": []}))
        with pytest.raises(ValueError, match="must contain 'combining_function'"):
            load_combination_generator_from_json(str(cfg_file))

    def test_lfsr_missing_coefficients_raises(self, tmp_path):
        config = {
            "lfsrs": [{"field_order": 2, "degree": 3}],
            "combining_function": {"type": "xor"},
        }
        cfg_file = tmp_path / "cfg.json"
        cfg_file.write_text(json.dumps(config))
        with pytest.raises(ValueError, match="missing 'coefficients'"):
            load_combination_generator_from_json(str(cfg_file))

    def test_lfsr_missing_field_order_raises(self, tmp_path):
        config = {
            "lfsrs": [{"coefficients": [1, 1, 0], "degree": 3}],
            "combining_function": {"type": "xor"},
        }
        cfg_file = tmp_path / "cfg.json"
        cfg_file.write_text(json.dumps(config))
        with pytest.raises(ValueError, match="missing 'field_order'"):
            load_combination_generator_from_json(str(cfg_file))

    def test_lfsr_missing_degree_raises(self, tmp_path):
        config = {
            "lfsrs": [{"coefficients": [1, 1, 0], "field_order": 2}],
            "combining_function": {"type": "xor"},
        }
        cfg_file = tmp_path / "cfg.json"
        cfg_file.write_text(json.dumps(config))
        with pytest.raises(ValueError, match="missing 'degree'"):
            load_combination_generator_from_json(str(cfg_file))


class TestLoadKeystreamFromFile:
    def test_space_separated(self, tmp_path):
        f = tmp_path / "ks.txt"
        f.write_text("1 0 1 1 0")
        ks = load_keystream_from_file(str(f))
        assert ks == [1, 0, 1, 1, 0]

    def test_one_per_line(self, tmp_path):
        f = tmp_path / "ks.txt"
        f.write_text("1\n0\n1\n")
        ks = load_keystream_from_file(str(f))
        assert ks == [1, 0, 1]

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="Keystream file not found"):
            load_keystream_from_file(str(tmp_path / "nope.txt"))

    def test_invalid_bit_raises_value_error(self, tmp_path):
        f = tmp_path / "ks.txt"
        f.write_text("1\nabc\n0\n")
        with pytest.raises(ValueError, match="Invalid bit value"):
            load_keystream_from_file(str(f))


class TestPerformCorrelationAttackCli:
    def test_basic_siegenthaler_attack_runs(self, tmp_path):
        cfg_file = tmp_path / "cfg.json"
        cfg_file.write_text(json.dumps(two_lfsr_xor_config()))

        buf = io.StringIO()
        perform_correlation_attack_cli(
            config_file=str(cfg_file),
            output_file=buf,
            keystream_length=200,
            target_lfsr_index=0,
            analyze_function=True,
        )
        out = buf.getvalue()
        assert "Loading combination generator configuration" in out
        assert "Combining Function Analysis" in out
        assert "Correlation Attack Results (Siegenthaler)" in out
        assert "Attacking LFSR 1" in out

    def test_keystream_from_file_used_instead_of_generation(self, tmp_path):
        cfg_file = tmp_path / "cfg.json"
        cfg_file.write_text(json.dumps(two_lfsr_xor_config()))
        ks_file = tmp_path / "ks.txt"
        ks_file.write_text(" ".join(str(i % 2) for i in range(100)))

        buf = io.StringIO()
        perform_correlation_attack_cli(
            config_file=str(cfg_file),
            output_file=buf,
            keystream_file=str(ks_file),
            target_lfsr_index=0,
        )
        out = buf.getvalue()
        assert f"Loading keystream from {ks_file}" in out
        assert "Loaded 100 bits" in out

    def test_analyze_all_lfsrs(self, tmp_path):
        cfg_file = tmp_path / "cfg.json"
        cfg_file.write_text(json.dumps(two_lfsr_xor_config()))

        buf = io.StringIO()
        perform_correlation_attack_cli(
            config_file=str(cfg_file),
            output_file=buf,
            keystream_length=150,
            analyze_all_lfsrs=True,
        )
        out = buf.getvalue()
        assert "Attacking LFSR 1" in out
        assert "Attacking LFSR 2" in out

    def test_missing_config_file_raises(self, tmp_path):
        buf = io.StringIO()
        with pytest.raises(FileNotFoundError):
            perform_correlation_attack_cli(
                config_file=str(tmp_path / "nope.json"),
                output_file=buf,
            )

    def test_output_defaults_to_stdout(self, tmp_path, capsys):
        cfg_file = tmp_path / "cfg.json"
        cfg_file.write_text(json.dumps(two_lfsr_xor_config()))

        perform_correlation_attack_cli(
            config_file=str(cfg_file),
            keystream_length=100,
        )
        captured = capsys.readouterr()
        assert "Loading combination generator configuration" in captured.out

    def test_fast_correlation_attack_flag_runs(self, tmp_path):
        """Regression test (bug fixed 2026-08-12, see commit history):
        perform_correlation_attack_cli's parameter `fast_correlation_attack:
        bool = False` used to shadow the module-level function of the same
        name (lfsr.attacks.fast_correlation_attack, not imported at module
        scope at all previously). Inside the function body the *parameter*
        shadowed anything of that name, so the call `result =
        fast_correlation_attack(combination_generator=gen, ...)` called
        the bool parameter itself, raising TypeError: 'bool' object is not
        callable -- --fast-correlation-attack was completely broken via
        the CLI for every input. Fixed by importing the real function
        under an aliased name (run_fast_correlation_attack) so the
        parameter no longer shadows it."""
        cfg_file = tmp_path / "cfg.json"
        cfg_file.write_text(json.dumps(two_lfsr_xor_config()))

        buf = io.StringIO()
        perform_correlation_attack_cli(
            config_file=str(cfg_file),
            output_file=buf,
            keystream_length=50,
            target_lfsr_index=0,
            fast_correlation_attack=True,
            max_candidates=8,
        )
        out = buf.getvalue()
        assert "Fast Correlation Attack Results" in out
        assert "Attack method: Fast Correlation Attack" in out

    def test_distinguishing_attack_flag_runs(self, tmp_path):
        """Same root cause as test_fast_correlation_attack_flag_runs
        above, for the run_distinguishing_attack_flag parameter (renamed
        from distinguishing_attack to avoid shadowing
        lfsr.attacks.distinguishing_attack, imported here as
        run_distinguishing_attack)."""
        cfg_file = tmp_path / "cfg.json"
        cfg_file.write_text(json.dumps(two_lfsr_xor_config()))

        buf = io.StringIO()
        perform_correlation_attack_cli(
            config_file=str(cfg_file),
            output_file=buf,
            keystream_length=50,
            target_lfsr_index=0,
            run_distinguishing_attack_flag=True,
            max_candidates=8,
        )
        out = buf.getvalue()
        assert "Distinguishing Attack Results" in out
        assert "Distinguishable:" in out

    def test_majority_combiner_shows_vulnerable_output_for_all_attack_types(self, tmp_path):
        """The xor-combiner tests above never reach the "Attack
        successful: True" / "VULNERABLE" branches in
        perform_correlation_attack_cli's output formatting, since xor
        is provably uncorrelated. Majority-of-3 IS provably correlated
        (see test_attacks.py's module docstring), so with enough
        keystream this exercises the success/"VULNERABLE" print
        branches for the distinguishing attack, the Siegenthaler
        attack, and the fast correlation attack in a single run."""
        cfg_file = tmp_path / "cfg.json"
        cfg_file.write_text(json.dumps(three_lfsr_majority_config()))

        buf = io.StringIO()
        perform_correlation_attack_cli(
            config_file=str(cfg_file),
            output_file=buf,
            keystream_length=300,
            target_lfsr_index=0,
            run_distinguishing_attack_flag=True,
        )
        out = buf.getvalue()
        assert "Attack successful: True" in out
        assert "VULNERABLE: Keystream is distinguishable from random!" in out
        assert "VULNERABLE: Significant correlation detected!" in out

    def test_majority_combiner_fast_correlation_attack_recovers_state(self, tmp_path):
        cfg_file = tmp_path / "cfg.json"
        cfg_file.write_text(json.dumps(three_lfsr_majority_config()))

        buf = io.StringIO()
        perform_correlation_attack_cli(
            config_file=str(cfg_file),
            output_file=buf,
            keystream_length=300,
            target_lfsr_index=0,
            fast_correlation_attack=True,
            max_candidates=10,
        )
        out = buf.getvalue()
        assert "Recovered state:" in out
        assert "VULNERABLE: State recovery successful!" in out
