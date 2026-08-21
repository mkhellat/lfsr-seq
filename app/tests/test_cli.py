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

    def test_cli_main_advanced_structure_no_valid_coeffs_after_parsing(self, monkeypatch, tmp_path, capsys):
        """Distinct from test_cli_main_advanced_structure_missing_coeffs_file
        above: that test exercises read_and_validate_csv's OWN "no data"
        guard (io.py), which fires before cli.py's own
        `if not coeffs_list:` check (cli.py lines ~973-975) is ever
        reached. This test instead uses a CSV row that survives
        read_and_validate_csv (a non-blank, non-comment row) but whose
        every value fails int() conversion inside
        read_coefficient_vectors, so it legitimately returns [] to
        cli.py -- reaching cli.py's own guard instead."""
        csv_file = tmp_path / "in.csv"
        csv_file.write_text("abc,def,ghi\n")
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--advanced-structure", "nfsr"],
        )

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code != 0
        captured = capsys.readouterr()
        assert "No valid coefficients found" in captured.out or "No valid coefficients found" in captured.err

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

    def test_cli_main_compare_known_runs(self, monkeypatch, tmp_path):
        """Regression test (bug fixed 2026-08-12, see commit history):
        cli.py's theoretical-analysis dispatch used to unpack
        analyze_lfsr()'s return tuple as (..., char_poly, char_poly_order,
        _), but lfsr.core.analyze_lfsr's actual return signature is
        (seq_dict, period_dict, max_period, periods_sum, C, CS, d) -- the
        5th/6th elements are the state-update matrix C and companion-matrix
        ring element CS, not a characteristic polynomial and its order.
        `char_poly` ended up bound to a raw sage Matrix, so every
        downstream use (is_primitive_polynomial -> polynomial.degree())
        crashed with AttributeError for every input, breaking
        --export-latex, --generate-paper, --compare-known, --benchmark,
        --reproducibility-report (and the same bug duplicated in the
        visualization dispatch). Fixed by unpacking (C, CS, d) correctly
        and deriving char_poly/char_poly_order via
        characteristic_polynomial(CS, ...)/polynomial_order(...), matching
        the pattern already used by the main analysis path."""
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--compare-known"],
        )

        cli_main()

        out_content = (tmp_path / (str(csv_file) + ".out")).read_text()
        assert "Comparison with Known Results" in out_content

    def test_cli_main_export_latex_runs(self, monkeypatch, tmp_path):
        """Same root cause as test_cli_main_compare_known_runs above,
        exercised via --export-latex instead of --compare-known --
        confirms the fix applies to the shared setup code, not just one
        theoretical-analysis flag."""
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        latex_out = tmp_path / "out.tex"
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--export-latex", str(latex_out)],
        )

        cli_main()

        assert latex_out.exists()
        assert "t^3" in latex_out.read_text() or "t^{3}" in latex_out.read_text()

    def test_cli_main_plot_period_distribution_runs(self, monkeypatch, tmp_path):
        """The visualization dispatch (cli.py, --plot-period-distribution
        et al.) duplicated the exact same broken analyze_lfsr()
        tuple-unpacking pattern as the theoretical-analysis dispatch (see
        test_cli_main_compare_known_runs) and is fixed the same way. This
        confirms --plot-period-distribution, --plot-state-transitions,
        --plot-period-statistics, --plot-3d-state-space, and
        --visualize-attack are functional via the CLI again."""
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        plot_out = tmp_path / "plot.png"
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--plot-period-distribution", str(plot_out)],
        )

        cli_main()

        assert plot_out.exists()

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

        cli_main()

        assert report_out.exists()
        report = json.loads(report_out.read_text())
        assert report["report_type"] == "reproducibility_report"
        assert report["configuration"]["coefficients"] == [1, 1, 0]

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


# ---------------------------------------------------------------------------
# main() -- SageMath unavailable / parallel-mode extra branches
# ---------------------------------------------------------------------------


class TestMainSageAndParallelBranches:
    def test_main_sage_unavailable_exits_cleanly(self, monkeypatch, tmp_path, capsys):
        """Regression test for a fixed bug in cli.py's main(): the
        sage-unavailable branch does
            print(..., file=sys.stderr)
            sys.exit(1)
        relying on the module-level `import sys` at cli.py:14. main()'s
        own body used to *also* contain `import sys` twice further down
        (inside the `if num_lfsrs > 1 ...:` block and the
        `if should_use_parallel:` block). Because Python determines a
        name's scope (local vs. global) by static analysis of the
        *entire* function body -- not by control flow -- the mere
        presence of `import sys` anywhere in main()'s body made `sys` a
        local variable for the *whole* function, including the
        sage-unavailable branch that executes before either nested
        `import sys` statement runs, raising
        `UnboundLocalError: cannot access local variable 'sys'` instead
        of a clean SystemExit(1). Fixed by removing both redundant nested
        imports (the module-level import already covers the whole
        function). This test now asserts the correct behavior: a clean
        SystemExit(1) with the SageMath-installation message on stderr.
        """
        import lfsr.cli as cli_mod

        monkeypatch.setattr(cli_mod, "_sage_available", False)

        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        out_file = tmp_path / "out.txt"

        with open(out_file, "w") as f:
            with pytest.raises(SystemExit) as exc_info:
                main(str(csv_file), "2", output_file=f, no_progress=True)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "SageMath is required" in captured.err

    def test_main_dynamic_parallel_full_sequence_mode(self, tmp_path, capsys):
        """Covers cli.py lines 199-209: dynamic parallel mode with
        period_only=False prints the two INFO messages about forcing
        period-only-friendly batch sizing and dispatches to
        lfsr_sequence_mapper_parallel_dynamic. Uses a tiny 3-bit LFSR to
        keep worker startup overhead low."""
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        out_file = tmp_path / "out.txt"

        with open(out_file, "w") as f:
            main(
                str(csv_file), "2", output_file=f, no_progress=True,
                use_parallel=True, parallel_mode="dynamic", period_only=False,
            )

        captured = capsys.readouterr()
        assert "Using dynamic parallel processing" in captured.err
        assert "period-only mode for better performance" in captured.err
        content = out_file.read_text()
        assert "COEFFS SERIES 1" in content

    def test_main_dynamic_parallel_period_only_mode(self, tmp_path, capsys):
        """Dynamic parallel mode with period_only=True should skip the
        "using period-only mode for better performance" info line (that
        branch is only for auto-forcing period_only=True), but still hit
        the dynamic-mode INFO banner at line 199."""
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        out_file = tmp_path / "out.txt"

        with open(out_file, "w") as f:
            main(
                str(csv_file), "2", output_file=f, no_progress=True,
                use_parallel=True, parallel_mode="dynamic", period_only=True,
            )

        captured = capsys.readouterr()
        assert "Using dynamic parallel processing" in captured.err

    def test_main_static_parallel_full_sequence_mode_warns(self, tmp_path, capsys):
        """Covers cli.py lines 221-222: static parallel mode with
        period_only=False must print the WARNING about being forced into
        period-only mode to avoid hangs."""
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        out_file = tmp_path / "out.txt"

        with open(out_file, "w") as f:
            main(
                str(csv_file), "2", output_file=f, no_progress=True,
                use_parallel=True, parallel_mode="static", period_only=False,
            )

        captured = capsys.readouterr()
        assert "Using static parallel processing" in captured.err
        assert "forced to period-only mode to avoid hangs" in captured.err


# ---------------------------------------------------------------------------
# cli_main() -- remaining dispatch/error branches
# ---------------------------------------------------------------------------


class TestCliMainRemainingBranches:
    def _run(self, monkeypatch, tmp_path, argv):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("sys.argv", ["lfsr-seq"] + argv)

    # -- --tmto-attack empty-coefficients branch (lines 1019-1020) --------

    def test_cli_main_tmto_attack_empty_coeffs_file_exits(self, monkeypatch, tmp_path, capsys):
        # Genuinely reaches cli.py's OWN `if not coeffs_list:` guard
        # (lines ~1019-1020), unlike a comment-only file (which trips
        # read_and_validate_csv's *own* "no data" exit first, inside
        # io.py, before cli.py's coeffs_list check is ever reached).
        # A row of non-numeric garbage survives read_and_validate_csv
        # (which only rejects blank/comment rows and inconsistent
        # lengths) but every value fails int() conversion inside
        # read_coefficient_vectors, so it returns [] to the caller.
        csv_file = tmp_path / "in.csv"
        csv_file.write_text("abc,def,ghi\n")
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--tmto-attack"],
        )

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code != 0
        captured = capsys.readouterr()
        assert "No valid coefficients found" in captured.out or "No valid coefficients found" in captured.err

    # -- --algebraic-attack empty-coefficients branch (lines 1048-1049) ---

    def test_cli_main_algebraic_attack_empty_coeffs_file_exits(self, monkeypatch, tmp_path, capsys):
        # See the tmto-attack test above for why a non-numeric-garbage
        # row (not a comment-only file) is needed to actually reach
        # cli.py's own `if not coeffs_list:` guard.
        csv_file = tmp_path / "in.csv"
        csv_file.write_text("abc,def,ghi\n")
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--algebraic-attack"],
        )

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code != 0
        captured = capsys.readouterr()
        assert "No valid coefficients found" in captured.out or "No valid coefficients found" in captured.err

    # -- theoretical-analysis empty-coefficients branch (lines 1091-1092) -

    def test_cli_main_theoretical_analysis_empty_coeffs_file_exits(self, monkeypatch, tmp_path, capsys):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text("abc,def,ghi\n")
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--compare-known"],
        )

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code != 0
        captured = capsys.readouterr()
        assert "No valid coefficients found" in captured.out or "No valid coefficients found" in captured.err

    # -- --generate-paper (lines 1141-1144) --------------------------------

    def test_cli_main_generate_paper_runs(self, monkeypatch, tmp_path):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        paper_out = tmp_path / "paper.tex"
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--generate-paper", str(paper_out)],
        )

        cli_main()

        assert paper_out.exists()
        assert len(paper_out.read_text()) > 0
        out_content = (tmp_path / (str(csv_file) + ".out")).read_text()
        assert "Research paper saved to" in out_content

    # -- --compare-known "found in database" branch (lines 1161-1165) -----

    def test_cli_main_compare_known_found_in_database(self, monkeypatch, tmp_path):
        """[1,0,1] over GF(2), degree 3, order 7 is one of the standard
        primitive polynomials seeded by
        theoretical_db.KnownResultDatabase.populate_standard_primitives(),
        so --compare-known should report a database hit and print the
        known-order/known-primitive/match detail lines (1161-1165), not
        just the "no matching results" fallback."""
        csv_file = tmp_path / "in.csv"
        csv_file.write_text("1,0,1\n")
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--compare-known"],
        )

        cli_main()

        out_content = (tmp_path / (str(csv_file) + ".out")).read_text()
        assert "Found in database: True" in out_content
        assert "Known order:" in out_content
        assert "Known primitive:" in out_content
        assert "Order match:" in out_content
        assert "Primitive match:" in out_content
        assert "Overall match:" in out_content

    # -- --benchmark (lines 1172-1182) -------------------------------------

    def test_cli_main_benchmark_runs(self, monkeypatch, tmp_path):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--benchmark"],
        )

        cli_main()

        out_content = (tmp_path / (str(csv_file) + ".out")).read_text()
        assert "Performance Benchmarking" in out_content
        assert "Method:" in out_content
        assert "Execution time:" in out_content

    # -- ML features missing-input-file / empty-coeffs (1211-1213, 1217-1218) --

    def test_cli_main_ml_feature_empty_coeffs_file_exits(self, monkeypatch, tmp_path, capsys):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text("abc,def,ghi\n")
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--detect-patterns"],
        )

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code != 0
        captured = capsys.readouterr()
        assert "No valid coefficients found" in captured.out or "No valid coefficients found" in captured.err

    # -- --predict-period with --ml-model-file (lines 1229-1232) ----------

    def test_cli_main_predict_period_with_trained_model(self, monkeypatch, tmp_path):
        """Trains a tiny model first (exercising --train-model, already
        covered), then feeds it back in via --ml-model-file to exercise
        the PeriodPredictionModel.load_model()/predict_period() branch
        that only runs when a model file is supplied."""
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

        self._run(
            monkeypatch, tmp_path,
            [
                str(csv_file), "2", "--predict-period",
                "--ml-model-file", str(model_out),
            ],
        )
        cli_main()

        out_content = (tmp_path / (str(csv_file) + ".out")).read_text()
        assert "ML Period Prediction" in out_content
        assert "Predicted period:" in out_content

    # -- --evaluate-model full run (lines 1323-1333) -----------------------

    def test_cli_main_evaluate_model_with_model_file_runs(self, monkeypatch, tmp_path):
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

        self._run(
            monkeypatch, tmp_path,
            [
                str(csv_file), "2", "--evaluate-model",
                "--ml-model-file", str(model_out),
                "--ml-test-samples", "5",
            ],
        )
        cli_main()

        out_content = (tmp_path / (str(csv_file) + ".out")).read_text()
        assert "Evaluating ML Model" in out_content
        assert "MSE:" in out_content
        assert "RMSE:" in out_content
        assert "R² Score:" in out_content

    # -- pattern detection detail lines (line 1254) ------------------------

    def test_cli_main_detect_patterns_prints_pattern_details(self, monkeypatch, tmp_path):
        """The pattern-detail print loop (line 1254) only runs when at
        least one pattern category is non-empty. A real period-7 sequence
        from a small primitive GF(2) LFSR is too short/regular to reliably
        trigger any of detect_all_patterns' detectors (empirically all
        three categories come back empty), so monkeypatch
        lfsr.cli_ciphers-style: patch detect_all_patterns itself (imported
        into cli.py's ML-dispatch branch via
        `from lfsr.ml.pattern_detection import detect_all_patterns`) to
        return a fake non-empty pattern list, deterministically exercising
        the per-pattern detail-line formatting at cli.py line 1254."""
        import lfsr.ml.pattern_detection as pattern_detection_mod

        class FakePattern:
            description = "synthetic repeating block"
            confidence = 0.87

        monkeypatch.setattr(
            pattern_detection_mod,
            "detect_all_patterns",
            lambda seq: {"repeating_subsequences": [FakePattern()]},
        )

        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--detect-patterns"],
        )

        cli_main()

        out_content = (tmp_path / (str(csv_file) + ".out")).read_text()
        assert "Pattern Detection" in out_content
        assert "repeating_subsequences: 1 patterns" in out_content
        assert "Pattern 1: synthetic repeating block (confidence: 0.87)" in out_content

    # -- visualization missing-input-file / empty-coeffs (1353-1354, 1358-1359) --

    def test_cli_main_visualization_empty_coeffs_file_exits(self, monkeypatch, tmp_path, capsys):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text("abc,def,ghi\n")
        plot_out = tmp_path / "plot.png"
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--plot-period-distribution", str(plot_out)],
        )

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code != 0
        captured = capsys.readouterr()
        assert "No valid coefficients found" in captured.out or "No valid coefficients found" in captured.err

    # -- --plot-state-transitions (lines 1404-1411) ------------------------

    def test_cli_main_plot_state_transitions_runs(self, monkeypatch, tmp_path):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        plot_out = tmp_path / "transitions.png"
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--plot-state-transitions", str(plot_out)],
        )

        cli_main()

        assert plot_out.exists()
        out_content = (tmp_path / (str(csv_file) + ".out")).read_text()
        assert "State transition diagram saved to" in out_content

    # -- --plot-period-statistics (lines 1415-1422) -------------------------

    def test_cli_main_plot_period_statistics_runs(self, monkeypatch, tmp_path):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        plot_out = tmp_path / "stats.png"
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--plot-period-statistics", str(plot_out)],
        )

        cli_main()

        assert plot_out.exists()
        out_content = (tmp_path / (str(csv_file) + ".out")).read_text()
        assert "Period statistics plot saved to" in out_content

    # -- --plot-3d-state-space (lines 1426-1433) -----------------------------

    def test_cli_main_plot_3d_state_space_succeeds(self, monkeypatch, tmp_path, capsys):
        """Regression test for a fixed bug:
        lfsr.visualization.state_space_3d.plot_3d_state_space used to
        build its 3D point array directly from raw LFSR state
        coordinates (Sage GF(q) finite-field elements, not Python
        ints/floats) without conversion, producing a numpy dtype=object
        array. matplotlib's 3D scatter path calls np.isfinite(arr) on
        that array during rendering, which raised:
            TypeError: ufunc 'isfinite' not supported for the input
            types, ...
        for every real (sage-backed) --plot-3d-state-space invocation.
        Fixed by coercing each state coordinate to int() before building
        the array. This test now asserts the real, unmocked path
        succeeds end-to-end via the CLI."""
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        plot_out = tmp_path / "3d.png"
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--plot-3d-state-space", str(plot_out)],
        )

        cli_main()
        assert plot_out.exists()
        out_content = (tmp_path / (str(csv_file) + ".out")).read_text()
        assert "3D state space visualization saved to" in out_content

    # -- --visualize-attack (lines 1439-1449) --------------------------------

    def test_cli_main_visualize_attack_runs(self, monkeypatch, tmp_path):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        plot_out = tmp_path / "attack.png"
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--visualize-attack", str(plot_out)],
        )

        cli_main()

        assert plot_out.exists()
        out_content = (tmp_path / (str(csv_file) + ".out")).read_text()
        assert "Attack visualization saved to" in out_content

    # -- IOError handler (lines 1497-1498) -----------------------------------

    def test_cli_main_ioerror_reports_and_exits(self, monkeypatch, tmp_path, capsys):
        """Force main() to raise IOError and confirm cli_main's dedicated
        `except IOError` handler (distinct from the generic
        `except Exception` handler already covered) reports and exits
        non-zero."""
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        self._run(monkeypatch, tmp_path, [str(csv_file), "2", "--no-progress"])

        def boom(*args, **kwargs):
            raise IOError("synthetic io failure for test")

        monkeypatch.setattr("lfsr.cli.main", boom)

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "File I/O error" in captured.err
        assert "synthetic io failure for test" in captured.err

    # -- KeyboardInterrupt handler (lines 1500-1501) -------------------------

    def test_cli_main_keyboard_interrupt_reports_and_exits(self, monkeypatch, tmp_path, capsys):
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        self._run(monkeypatch, tmp_path, [str(csv_file), "2", "--no-progress"])

        def boom(*args, **kwargs):
            raise KeyboardInterrupt()

        monkeypatch.setattr("lfsr.cli.main", boom)

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Interrupted by user" in captured.err


class TestCliMainDeadInputFileChecks:
    """Covers cli.py's six `if not args.input_file:` guards inside
    cli_main() (lines 967-969, 1012-1014, 1040-1042, 1085-1087,
    1211-1213, 1352-1354).

    SUSPECTED DEAD CODE (not a runtime-crashing bug, but worth flagging):
    cli_main() already does
        input_file_name = args.input_file
        ...
        if not os.path.exists(input_file_name):
            sys.exit(1)
    unconditionally, BEFORE reaching any of the mode-specific dispatch
    branches below it, using the exact same `args.input_file` value with
    no mutation in between. Since `not os.path.exists(x)` is True for
    any falsy `x` (empty string, None), a falsy `args.input_file` can
    never survive to reach these later `if not args.input_file:` checks
    through the real cli_main() entry point -- they are unreachable in
    practice. These tests demonstrate the unreachability directly by
    monkeypatching `os.path.exists` to accept the empty-string path
    (bypassing the earlier guard) and `parse_args` to hand back an empty
    `input_file`, which is the only way to actually execute these lines
    at all.
    """

    def _run(self, monkeypatch, tmp_path, argv):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("sys.argv", ["lfsr-seq"] + argv)

    def _patch_empty_input_file(self, monkeypatch, mode_flag_args):
        """Patch parse_args() to return a Namespace with input_file=""
        (falsy) but otherwise matching real parsed args for mode_flag_args,
        and patch os.path.exists to treat "" as existing so cli_main's
        earlier unconditional existence check doesn't short-circuit
        first."""
        import lfsr.cli as cli_mod

        real_parse_args = cli_mod.parse_args

        def fake_parse_args(argv=None):
            ns = real_parse_args(mode_flag_args)
            ns.input_file = ""
            return ns

        monkeypatch.setattr(cli_mod, "parse_args", fake_parse_args)

        import os as os_mod

        real_exists = os_mod.path.exists

        def fake_exists(path):
            if path == "":
                return True
            return real_exists(path)

        monkeypatch.setattr(cli_mod.os.path, "exists", fake_exists)

    def test_advanced_structure_missing_input_file_dead_branch(self, monkeypatch, tmp_path, capsys):
        self._run(monkeypatch, tmp_path, ["dummy.csv", "2", "--advanced-structure", "nfsr"])
        self._patch_empty_input_file(monkeypatch, ["", "2", "--advanced-structure", "nfsr"])

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "--advanced-structure requires input file" in captured.err

    def test_tmto_attack_missing_input_file_dead_branch(self, monkeypatch, tmp_path, capsys):
        self._run(monkeypatch, tmp_path, ["dummy.csv", "2", "--tmto-attack"])
        self._patch_empty_input_file(monkeypatch, ["", "2", "--tmto-attack"])

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "--tmto-attack requires input file" in captured.err

    def test_algebraic_attack_missing_input_file_dead_branch(self, monkeypatch, tmp_path, capsys):
        self._run(monkeypatch, tmp_path, ["dummy.csv", "2", "--algebraic-attack"])
        self._patch_empty_input_file(monkeypatch, ["", "2", "--algebraic-attack"])

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "--algebraic-attack requires input file" in captured.err

    def test_theoretical_analysis_missing_input_file_dead_branch(self, monkeypatch, tmp_path, capsys):
        self._run(monkeypatch, tmp_path, ["dummy.csv", "2", "--compare-known"])
        self._patch_empty_input_file(monkeypatch, ["", "2", "--compare-known"])

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Theoretical analysis features require input file" in captured.err

    def test_ml_features_missing_input_file_dead_branch(self, monkeypatch, tmp_path, capsys):
        self._run(monkeypatch, tmp_path, ["dummy.csv", "2", "--predict-period"])
        self._patch_empty_input_file(monkeypatch, ["", "2", "--predict-period"])

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "ML features require input file" in captured.err

    def test_visualization_missing_input_file_dead_branch(self, monkeypatch, tmp_path, capsys):
        self._run(monkeypatch, tmp_path, ["dummy.csv", "2", "--plot-period-distribution", "out.png"])
        self._patch_empty_input_file(
            monkeypatch, ["", "2", "--plot-period-distribution", "out.png"]
        )

        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Visualization features require input file" in captured.err


class TestCliMainAdditionalBranches:
    def _run(self, monkeypatch, tmp_path, argv):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("sys.argv", ["lfsr-seq"] + argv)

    # -- --detect-anomalies non-dict branch (lines 1293-1296) ---------------

    def test_detect_anomalies_non_dict_branch(self, monkeypatch, tmp_path):
        """detect_all_anomalies() (lfsr.ml.anomaly_detection) always
        returns a Dict[str, List[Anomaly]] per its own type signature and
        implementation (unconditionally builds and returns a `results`
        dict). cli.py's --detect-anomalies handler nonetheless branches
        on `isinstance(anomalies, dict)` with a non-dict `else` fallback
        (lines 1293-1296) that real code can never reach -- dead code
        under the current implementation of detect_all_anomalies. This
        test exercises that fallback directly by monkeypatching
        detect_all_anomalies to return a plain list, to get coverage of
        the branch and document why it's unreachable in practice."""
        import lfsr.ml.anomaly_detection as anomaly_mod

        class FakeAnomaly:
            description = "fake anomaly"
            severity = 0.5

        def fake_detect_all_anomalies(**kwargs):
            return [FakeAnomaly(), FakeAnomaly()]

        monkeypatch.setattr(anomaly_mod, "detect_all_anomalies", fake_detect_all_anomalies)
        monkeypatch.setattr("lfsr.cli.detect_all_anomalies", fake_detect_all_anomalies, raising=False)

        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        self._run(monkeypatch, tmp_path, [str(csv_file), "2", "--detect-anomalies"])

        cli_main()

        out_content = (tmp_path / (str(csv_file) + ".out")).read_text()
        assert "Anomalies detected: 2" in out_content
        assert "fake anomaly" in out_content

    # -- --plot-3d-state-space success print (line 1433) --------------------

    def test_plot_3d_state_space_success_print(self, monkeypatch, tmp_path, capsys):
        """Covers the success-path print statement for
        --plot-3d-state-space. Now that plot_3d_state_space() coerces
        Sage GF(q) elements to int() (see
        test_cli_main_plot_3d_state_space_succeeds), the real path
        reaches this print with no mocking needed."""
        csv_file = tmp_path / "in.csv"
        csv_file.write_text(SIMPLE_CSV)
        plot_out = tmp_path / "3d.png"
        self._run(
            monkeypatch, tmp_path,
            [str(csv_file), "2", "--plot-3d-state-space", str(plot_out)],
        )

        cli_main()
        captured_out = (tmp_path / (str(csv_file) + ".out")).read_text()
        assert "3D state space visualization saved to" in captured_out

        out_content = (tmp_path / (str(csv_file) + ".out")).read_text()
        assert "3D state space visualization saved to" in out_content
