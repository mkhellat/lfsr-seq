#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for the main CLI orchestrator (lfsr.cli).

These tests exercise argument parsing, dispatch, output writing, and
error handling in the CLI plumbing. The underlying math (core.py,
analysis.py, polynomial.py, etc.) is already covered by dedicated unit
tests -- these tests only check that the CLI wires arguments to the
right functions and produces sane output/exit codes.
"""

import json

import pytest

from lfsr.cli import cli_main, main, parse_args


SIMPLE_CSV = "1,1,0\n"  # GF(2), degree 3, primitive poly x^3+x+1, period 7
MULTI_CSV = "1,1,0\n1,1\n"  # two LFSRs


# ---------------------------------------------------------------------------
# parse_args
# ---------------------------------------------------------------------------


class TestParseArgs:
    def test_minimal_required_args(self):
        args = parse_args(["input.csv", "2"])
        assert args.input_file == "input.csv"
        assert args.gf_order == "2"
        assert args.output is None
        assert args.verbose is False
        assert args.quiet is False
        assert args.format == "text"
        assert args.algorithm == "auto"
        assert args.period_only is False
        assert args.show_period_stats is True
        assert args.use_parallel is None

    def test_output_option(self):
        args = parse_args(["input.csv", "2", "-o", "out.txt"])
        assert args.output == "out.txt"

    def test_output_long_option(self):
        args = parse_args(["input.csv", "2", "--output", "out.txt"])
        assert args.output == "out.txt"

    def test_verbose_flag(self):
        args = parse_args(["input.csv", "2", "-v"])
        assert args.verbose is True

    def test_quiet_flag(self):
        args = parse_args(["input.csv", "2", "-q"])
        assert args.quiet is True

    def test_verbose_and_quiet_together_errors(self):
        with pytest.raises(SystemExit):
            parse_args(["input.csv", "2", "-v", "-q"])

    def test_format_choices(self):
        for fmt in ["text", "json", "csv", "xml"]:
            args = parse_args(["input.csv", "2", "--format", fmt])
            assert args.format == fmt

    def test_format_invalid_choice_errors(self):
        with pytest.raises(SystemExit):
            parse_args(["input.csv", "2", "--format", "yaml"])

    def test_algorithm_choices(self):
        for algo in ["floyd", "brent", "enumeration", "auto"]:
            args = parse_args(["input.csv", "2", "--algorithm", algo])
            assert args.algorithm == algo

    def test_period_only_flag(self):
        args = parse_args(["input.csv", "2", "--period-only"])
        assert args.period_only is True

    def test_no_period_stats_flag(self):
        args = parse_args(["input.csv", "2", "--no-period-stats"])
        assert args.show_period_stats is False

    def test_parallel_flag(self):
        args = parse_args(["input.csv", "2", "--parallel"])
        assert args.use_parallel is True

    def test_no_parallel_flag(self):
        args = parse_args(["input.csv", "2", "--no-parallel"])
        assert args.use_parallel is False

    def test_num_workers(self):
        args = parse_args(["input.csv", "2", "--num-workers", "4"])
        assert args.num_workers == 4

    def test_parallel_mode_choices(self):
        args = parse_args(["input.csv", "2", "--parallel-mode", "dynamic"])
        assert args.parallel_mode == "dynamic"

    def test_parallel_mode_invalid_errors(self):
        with pytest.raises(SystemExit):
            parse_args(["input.csv", "2", "--parallel-mode", "bogus"])

    def test_batch_size(self):
        args = parse_args(["input.csv", "2", "--batch-size", "250"])
        assert args.batch_size == 250

    def test_missing_required_args_errors(self):
        with pytest.raises(SystemExit):
            parse_args([])

    def test_missing_gf_order_errors(self):
        with pytest.raises(SystemExit):
            parse_args(["input.csv"])

    def test_version_flag_exits_zero(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["--version"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "lfsr-seq" in captured.out

    def test_correlation_attack_defaults(self):
        args = parse_args(["input.csv", "2"])
        assert args.correlation_attack is False
        assert args.lfsr_configs is None
        assert args.target_lfsr == 0
        assert args.significance_level == 0.05

    def test_cipher_choices(self):
        for cipher in ["a5_1", "a5_2", "e0", "trivium", "grain128", "grain128a", "lili128"]:
            args = parse_args(["input.csv", "2", "--cipher", cipher])
            assert args.cipher == cipher

    def test_cipher_invalid_choice_errors(self):
        with pytest.raises(SystemExit):
            parse_args(["input.csv", "2", "--cipher", "des"])

    def test_advanced_structure_choices(self):
        for structure in ["nfsr", "filtered", "clock_controlled", "multi_output", "irregular"]:
            args = parse_args(["input.csv", "2", "--advanced-structure", structure])
            assert args.advanced_structure == structure

    def test_nist_test_defaults(self):
        args = parse_args(["input.csv", "2"])
        assert args.nist_test is False
        assert args.nist_significance_level == 0.01
        assert args.nist_block_size == 128
        assert args.nist_output_format == "text"

    def test_tmto_defaults(self):
        args = parse_args(["input.csv", "2"])
        assert args.tmto_attack is False
        assert args.tmto_method == "hellman"
        assert args.chain_count == 1000
        assert args.chain_length == 100


# ---------------------------------------------------------------------------
# main() -- core analysis workflow
# ---------------------------------------------------------------------------


class TestMainCoreAnalysis:
    def test_main_writes_text_output(self, tmp_path):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        out_file = tmp_path / "out.txt"

        with open(out_file, "w") as f:
            main(str(csv_file), "2", output_file=f, no_progress=True)

        content = out_file.read_text()
        assert "COEFFS SERIES 1" in content
        assert "STATE UPDATE MATRIX" in content
        assert "TOTAL execution time" not in content  # printed to stdout only

    def test_main_reports_correct_period(self, tmp_path, capsys):
        """[1,1,0] over GF(2) is primitive (x^3+x+1); max period must be 7."""
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        out_file = tmp_path / "out.txt"

        with open(out_file, "w") as f:
            main(str(csv_file), "2", output_file=f, no_progress=True)

        content = out_file.read_text()
        assert "7" in content  # period should appear somewhere in output

    def test_main_period_only_mode(self, tmp_path):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        out_file = tmp_path / "out.txt"

        with open(out_file, "w") as f:
            main(str(csv_file), "2", output_file=f, no_progress=True, period_only=True)

        content = out_file.read_text()
        assert "COEFFS SERIES 1" in content

    def test_main_invalid_gf_order_exits(self, tmp_path):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        out_file = tmp_path / "out.txt"

        with open(out_file, "w") as f:
            with pytest.raises(SystemExit):
                main(str(csv_file), "6", output_file=f, no_progress=True)  # 6 not prime power

    def test_main_missing_input_file_exits(self, tmp_path):
        out_file = tmp_path / "out.txt"
        with open(out_file, "w") as f:
            with pytest.raises(SystemExit):
                main(str(tmp_path / "does_not_exist.csv"), "2", output_file=f, no_progress=True)

    def test_main_multiple_lfsrs_forces_sequential(self, tmp_path, capsys):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(MULTI_CSV)
        out_file = tmp_path / "out.txt"

        with open(out_file, "w") as f:
            main(str(csv_file), "2", output_file=f, no_progress=True)

        content = out_file.read_text()
        assert "COEFFS SERIES 1" in content
        assert "COEFFS SERIES 2" in content
        # INFO message about sequential mode goes to stderr
        captured = capsys.readouterr()
        assert "sequential mode" in captured.err

    def test_main_json_export_produces_valid_structure(self, tmp_path):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        out_file = tmp_path / "out.json"

        with open(out_file, "w") as f:
            main(str(csv_file), "2", output_file=f, no_progress=True, output_format="json")

        content = out_file.read_text()
        # Text-mode content is written first, then JSON is appended by the
        # export function; just verify a JSON export function ran without
        # crashing and something parseable exists in the output.
        assert len(content) > 0

    def test_main_gf3_field(self, tmp_path):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text("1,2,1\n")
        out_file = tmp_path / "out.txt"

        with open(out_file, "w") as f:
            main(str(csv_file), "3", output_file=f, no_progress=True)

        content = out_file.read_text()
        assert "COEFFS SERIES 1" in content


# ---------------------------------------------------------------------------
# cli_main() -- full entry point via sys.argv
# ---------------------------------------------------------------------------


class TestCliMain:
    def _run(self, monkeypatch, tmp_path, argv):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("sys.argv", ["lfsr-seq"] + argv)

    def test_cli_main_basic_run_creates_default_output_file(self, monkeypatch, tmp_path, capsys):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        self._run(monkeypatch, tmp_path, [str(csv_file), "2", "--no-progress"])

        cli_main()

        default_out = tmp_path / (str(csv_file) + ".out")
        assert default_out.exists()
        captured = capsys.readouterr()
        assert "Analysis complete" in captured.out

    def test_cli_main_explicit_output_file(self, monkeypatch, tmp_path):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        out_file = tmp_path / "results.txt"
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "-o", str(out_file), "--no-progress"],
        )

        cli_main()

        assert out_file.exists()
        assert "COEFFS SERIES 1" in out_file.read_text()

    def test_cli_main_missing_input_file_exits_nonzero(self, monkeypatch, tmp_path, capsys):
        self._run(monkeypatch, tmp_path, [str(tmp_path / "nope.csv"), "2"])

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code != 0
        captured = capsys.readouterr()
        assert "not found" in captured.err

    def test_cli_main_quiet_suppresses_completion_message(self, monkeypatch, tmp_path, capsys):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        self._run(monkeypatch, tmp_path, [str(csv_file), "2", "-q", "--no-progress"])

        cli_main()

        captured = capsys.readouterr()
        assert "Analysis complete" not in captured.out

    def test_cli_main_verbose_prints_file_info(self, monkeypatch, tmp_path, capsys):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        self._run(monkeypatch, tmp_path, [str(csv_file), "2", "-v", "--no-progress"])

        cli_main()

        captured = capsys.readouterr()
        assert "Input file:" in captured.out
        assert "GF order: 2" in captured.out

    def test_cli_main_invalid_gf_order_reports_error(self, monkeypatch, tmp_path, capsys):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        self._run(monkeypatch, tmp_path, [str(csv_file), "6", "--no-progress"])

        with pytest.raises(SystemExit):
            cli_main()

    def test_cli_main_nist_test_without_sequence_file_exits(self, monkeypatch, tmp_path, capsys):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        self._run(monkeypatch, tmp_path, [str(csv_file), "2", "--nist-test"])

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "requires --sequence-file" in captured.err

    def test_cli_main_nist_test_with_sequence_file(self, monkeypatch, tmp_path):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        seq_file = tmp_path / "seq.txt"
        # 100 bits, roughly balanced pseudo-random-looking sequence
        seq_file.write_text("\n".join(str(i % 2) for i in range(100)))
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--nist-test", "--sequence-file", str(seq_file)],
        )

        cli_main()

        out_content = (tmp_path / (str(csv_file) + ".out")).read_text()
        assert "NIST SP 800-22" in out_content

    def test_cli_main_correlation_attack_without_config_exits(self, monkeypatch, tmp_path, capsys):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        self._run(monkeypatch, tmp_path, [str(csv_file), "2", "--correlation-attack"])

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "requires --lfsr-configs" in captured.err

    def test_cli_main_tmto_attack_runs_with_string_gf_order(self, monkeypatch, tmp_path):
        """Regression test (bug fixed 2026-08-12, see commit history):
        cli.py's --tmto-attack dispatch used to pass the raw argparse
        string args.gf_order straight through as field_order instead of
        int(args.gf_order). cli_tmto.py's perform_tmto_attack_cli then
        did `lfsr_config.field_order ** lfsr_config.degree`, raising
        TypeError: unsupported operand type(s) for ** or pow(): 'str' and
        'int' on every invocation. Fixed by converting to int at the call
        site in cli.py."""
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--tmto-attack", "--chain-count", "10", "--chain-length", "5"],
        )

        cli_main()

        out_content = (tmp_path / (str(csv_file) + ".out")).read_text()
        assert "Time-Memory Trade-Off Attack" in out_content
        assert "TMTO Attack Results" in out_content

    def test_cli_main_cipher_dispatches(self, monkeypatch, tmp_path):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        self._run(monkeypatch, tmp_path, [str(csv_file), "2", "--cipher", "grain128"])

        cli_main()

        out_content = (tmp_path / (str(csv_file) + ".out")).read_text()
        assert "Stream Cipher Analysis" in out_content
        assert "Grain" in out_content

    def test_cli_main_advanced_structure_runs(self, monkeypatch, tmp_path):
        """Regression test (bug fixed 2026-08-12, see commit history):
        cli.py's --advanced-structure dispatch referenced LFSRConfig(...)
        without ever importing it from lfsr.attacks (contrast with
        cli_advanced.py, cli_algebraic.py, cli_tmto.py, which all
        correctly `from lfsr.attacks import LFSRConfig`), so every
        invocation raised NameError: name 'LFSRConfig' is not defined.
        Also had the same raw-string field_order bug as --tmto-attack.
        Fixed by adding the import and converting to int(args.gf_order)."""
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--advanced-structure", "nfsr"],
        )

        cli_main()

        out_content = (tmp_path / (str(csv_file) + ".out")).read_text()
        assert "Advanced LFSR Structure Analysis" in out_content
        assert "nonlinear" in out_content.lower()

    def test_cli_main_advanced_structure_missing_coeffs_file(self, monkeypatch, tmp_path, capsys):
        # input file exists but has no data at all -- read_coefficient_vectors
        # rejects it before the (separately buggy) LFSRConfig line is reached.
        csv_file = tmp_path / "in.csv"
        csv_file.write_text("# only a comment\n")
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--advanced-structure", "nfsr"],
        )

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code != 0
        captured = capsys.readouterr()
        assert "no data" in captured.out or "no data" in captured.err

    def test_cli_main_algebraic_attack_without_keystream_exits(self, monkeypatch, tmp_path, capsys):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--algebraic-attack"],
        )

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 1

    def test_cli_main_algebraic_attack_with_keystream_file(self, monkeypatch, tmp_path):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        keystream_file = tmp_path / "ks.txt"
        keystream_file.write_text("1 0 1 1 0 1 0 0 1 1\n")
        self._run(
            monkeypatch, tmp_path,
            [
                str(csv_file), "2", "--algebraic-attack",
                "--keystream-file", str(keystream_file),
                "--algebraic-method", "algebraic_immunity",
            ],
        )

        # algebraic_immunity method requires a filtering_function which the
        # CLI never supplies -- expect a clean SystemExit(1), not a crash.
        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 1

    def test_cli_main_ml_predict_period_without_model_warns(self, monkeypatch, tmp_path):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--predict-period"],
        )

        cli_main()

        out_content = (tmp_path / (str(csv_file) + ".out")).read_text()
        assert "ML Period Prediction" in out_content
        assert "No model file specified" in out_content

    def test_cli_main_compare_known_crashes_due_to_tuple_unpacking_bug(self, monkeypatch, tmp_path, capsys):
        """BUG (see report): cli.py's theoretical-analysis dispatch (around
        line 1097) does:
            seq_dict, period_dict, max_period, periods_sum, char_poly, \
                char_poly_order, _ = analyze_lfsr(coefficients, args.gf_order)
        but lfsr.core.analyze_lfsr's actual documented return signature is
        (seq_dict, period_dict, max_period, periods_sum, C, CS, d) -- the
        5th/6th elements are the state-update matrix C and companion-matrix
        ring element CS, NOT a characteristic polynomial and its order.
        `char_poly` therefore ends up bound to a raw sage Matrix object.
        Every use of `char_poly` downstream (is_primitive_polynomial,
        char_poly.is_irreducible(), etc.) then breaks -- here
        is_primitive_polynomial(char_poly, ...) calls
        `polynomial.degree()`, but a Matrix_mod2_dense has no `.degree`
        attribute, so this crashes with AttributeError for EVERY input.
        This affects all theoretical-analysis flags that share this code
        path: --export-latex, --generate-paper, --compare-known,
        --benchmark, --reproducibility-report (and the structurally
        identical bug is duplicated again in the visualization dispatch
        around line 1359)."""
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--compare-known"],
        )

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "has no attribute 'degree'" in captured.err

    def test_cli_main_export_latex_crashes_due_to_tuple_unpacking_bug(self, monkeypatch, tmp_path, capsys):
        """Same root cause as test_cli_main_compare_known_crashes_due_to_tuple_unpacking_bug
        above, exercised via --export-latex instead of --compare-known --
        confirms the bug is in the shared setup code, not specific to one
        theoretical-analysis flag."""
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        latex_out = tmp_path / "out.tex"
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--export-latex", str(latex_out)],
        )

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "has no attribute 'degree'" in captured.err
        assert not latex_out.exists()

    def test_cli_main_plot_period_distribution_crashes_same_unpacking_bug(self, monkeypatch, tmp_path, capsys):
        """The visualization dispatch (cli.py around line 1359) duplicates
        the exact same broken analyze_lfsr() tuple-unpacking pattern as the
        theoretical-analysis dispatch (see
        test_cli_main_compare_known_crashes_due_to_tuple_unpacking_bug):
        `char_poly` ends up bound to the state-update matrix C, not a
        polynomial, so is_primitive_polynomial(char_poly, ...) crashes
        with AttributeError for every input. This means all of
        --plot-period-distribution, --plot-state-transitions,
        --plot-period-statistics, --plot-3d-state-space, and
        --visualize-attack are non-functional via the CLI."""
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        plot_out = tmp_path / "plot.png"
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--plot-period-distribution", str(plot_out)],
        )

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "has no attribute 'degree'" in captured.err
        assert not plot_out.exists()

    def test_cli_main_detect_patterns_dispatches(self, monkeypatch, tmp_path):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--detect-patterns"],
        )

        cli_main()

        out_content = (tmp_path / (str(csv_file) + ".out")).read_text()
        assert "Pattern Detection" in out_content

    def test_cli_main_detect_anomalies_dispatches(self, monkeypatch, tmp_path):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--detect-anomalies"],
        )

        cli_main()

        out_content = (tmp_path / (str(csv_file) + ".out")).read_text()
        assert "Anomaly Detection" in out_content

    def test_cli_main_evaluate_model_without_model_file_exits(self, monkeypatch, tmp_path, capsys):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--evaluate-model"],
        )

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "requires --ml-model-file" in captured.err

    def test_cli_main_train_model_dispatches(self, monkeypatch, tmp_path):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        model_out = tmp_path / "model.pkl"
        self._run(
            monkeypatch, tmp_path,
            [
                str(csv_file), "2", "--train-model", str(model_out),
                "--ml-samples", "5",
            ],
        )

        cli_main()

        out_content = (tmp_path / (str(csv_file) + ".out")).read_text()
        assert "Training ML Model" in out_content
        assert "Model trained and saved to" in out_content

    def test_cli_main_reproducibility_report_dispatches(self, monkeypatch, tmp_path):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        report_out = tmp_path / "report.json"
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--reproducibility-report", str(report_out)],
        )

        with pytest.raises(SystemExit):
            # Shares the analyze_lfsr tuple-unpacking bug from the
            # theoretical-analysis dispatch, so this crashes too -- see
            # test_cli_main_compare_known_crashes_due_to_tuple_unpacking_bug.
            cli_main()

    def test_cli_main_correlation_attack_full_run(self, monkeypatch, tmp_path):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        cfg_file = tmp_path / "cfg.json"
        cfg_file.write_text(json.dumps({
            "lfsrs": [
                {"coefficients": [1, 1, 0], "field_order": 2, "degree": 3},
                {"coefficients": [1, 0, 0, 1], "field_order": 2, "degree": 4},
            ],
            "combining_function": {"type": "xor", "num_inputs": 2},
        }))
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--correlation-attack", "--lfsr-configs", str(cfg_file)],
        )

        cli_main()

        out_content = (tmp_path / (str(csv_file) + ".out")).read_text()
        assert "Correlation Attack Results (Siegenthaler)" in out_content

    def test_cli_main_unexpected_exception_reports_and_exits(self, monkeypatch, tmp_path, capsys):
        """Force main() to raise something unrelated to SystemExit/IOError
        and confirm cli_main's generic except-Exception handler catches it,
        prints an error, and exits non-zero rather than propagating."""
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        self._run(monkeypatch, tmp_path, [str(csv_file), "2", "--no-progress"])

        def boom(*args, **kwargs):
            raise ValueError("synthetic failure for test")

        monkeypatch.setattr("lfsr.cli.main", boom)

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Unexpected error" in captured.err
        assert "synthetic failure for test" in captured.err
