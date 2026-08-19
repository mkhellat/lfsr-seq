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

    def test_pass_fail_status_markers_shown_per_test(self, monkeypatch):
        # Covers the per-test PASS/FAIL status-marker line (cli_nist.py
        # lines 125-126), which is only reached when suite_result.results
        # is non-empty. A short sequence (e.g. 500 bits) makes every
        # sub-test report "too short" and the suite returns 0 results, so
        # monkeypatch run_nist_test_suite with a fake result carrying one
        # passed and one failed test to reliably hit both status strings.
        import lfsr.cli_nist as cli_nist_mod

        class FakeResult:
            def __init__(self, name, passed):
                self.test_name = name
                self.p_value = 0.5
                self.statistic = 1.0
                self.passed = passed
                self.details = {}

        class FakeSuiteResult:
            tests_passed = 1
            total_tests = 2
            tests_failed = 1
            pass_rate = 0.5
            overall_assessment = "FAILED"
            results = [FakeResult("t_pass", True), FakeResult("t_fail", False)]

        monkeypatch.setattr(
            cli_nist_mod, "run_nist_test_suite", lambda *a, **k: FakeSuiteResult()
        )

        buf = io.StringIO()
        cli_nist_mod.perform_nist_test_cli(make_sequence(50), output_file=buf)
        out = buf.getvalue()
        assert "PASS" in out
        assert "FAIL" in out

    def test_detailed_results_section_lists_each_test_with_details(self, monkeypatch):
        # Covers the "Detailed Results" per-test loop (lines 135-144),
        # including the nested `if result.details:` branch. Using a real
        # sequence long enough to reliably populate every sub-test's
        # `details` dict would require ~6000+ bits (see test_nist.py's
        # TestRunNistTestSuite docstring on suite runtime), which is slow
        # for a CLI-plumbing test; monkeypatch run_nist_test_suite with a
        # fake result carrying a non-empty details dict instead, matching
        # the approach used in test_interpretation_passed_branch below.
        import lfsr.cli_nist as cli_nist_mod

        class FakeResult:
            def __init__(self):
                self.test_name = "fake_test"
                self.p_value = 0.5
                self.statistic = 1.23
                self.passed = True
                self.details = {"count": 5, "note": "ok"}

        class FakeSuiteResult:
            tests_passed = 1
            total_tests = 1
            tests_failed = 0
            pass_rate = 1.0
            overall_assessment = "PASSED"
            results = [FakeResult()]

        monkeypatch.setattr(
            cli_nist_mod, "run_nist_test_suite", lambda *a, **k: FakeSuiteResult()
        )

        buf = io.StringIO()
        cli_nist_mod.perform_nist_test_cli(make_sequence(50), output_file=buf)
        out = buf.getvalue()
        assert "Test 1:" in out
        assert "P-value:" in out
        assert "Statistic:" in out
        assert "Passed:" in out
        assert "Details:" in out
        assert "count: 5" in out

    def test_interpretation_passed_branch(self, monkeypatch):
        # Covers the overall_assessment == "PASSED" branch (lines 152-155).
        # Force the suite result via monkeypatching run_nist_test_suite so
        # this test doesn't depend on a specific sequence actually passing
        # every NIST sub-test (which would be slow/flaky to engineer).
        import lfsr.cli_nist as cli_nist_mod

        class FakeResult:
            def __init__(self):
                self.test_name = "fake_test"
                self.p_value = 0.5
                self.statistic = 1.23
                self.passed = True
                self.details = {"count": 5}

        class FakeSuiteResult:
            tests_passed = 1
            total_tests = 1
            tests_failed = 0
            pass_rate = 1.0
            overall_assessment = "PASSED"
            results = [FakeResult()]

        monkeypatch.setattr(
            cli_nist_mod, "run_nist_test_suite", lambda *a, **k: FakeSuiteResult()
        )

        buf = io.StringIO()
        cli_nist_mod.perform_nist_test_cli(make_sequence(50), output_file=buf)
        out = buf.getvalue()
        assert "PASSED the NIST test suite" in out
        assert "positive indicator" in out

    def test_export_value_error_reports_warning(self, monkeypatch, tmp_path):
        # Covers the `except ValueError` branch around the export call
        # (lines 187-188): get_nist_export_function/export_func raising
        # ValueError should be caught and reported as a WARNING rather
        # than propagating.
        import lfsr.cli_nist as cli_nist_mod

        def boom(*args, **kwargs):
            raise ValueError("synthetic export failure")

        monkeypatch.setattr(cli_nist_mod, "get_nist_export_function", boom, raising=False)

        # get_nist_export_function is imported locally inside the function
        # body (`from lfsr.export import get_nist_export_function`), so
        # patch it at the source module instead.
        import lfsr.export as export_mod
        monkeypatch.setattr(export_mod, "get_nist_export_function", boom)

        out_path = tmp_path / "results.txt"
        seq = make_sequence(200)
        with open(out_path, "w") as f:
            cli_nist_mod.perform_nist_test_cli(
                seq, output_file=f, output_format="json"
            )

        content = out_path.read_text()
        assert "WARNING: Export failed" in content
        assert "synthetic export failure" in content
