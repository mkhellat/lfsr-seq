#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for lfsr.formatter.

Covers dump(), intro(), section(), subsection(), and dump_seq_row(). No
SageMath dependency -- this module only touches stdlib
datetime/platform/textwrap.

No test file previously existed for this module.
"""

import datetime

import pytest

from lfsr.formatter import dump, dump_seq_row, intro, section, subsection


class TestDump:
    def test_mode_console_prints_to_stdout(self, capsys):
        dump("hello", "mode=console")
        captured = capsys.readouterr()
        assert "hello" in captured.out

    def test_mode_file_writes_to_file(self, tmp_path):
        f = tmp_path / "out.txt"
        with open(f, "w") as fh:
            dump("hello", "mode=file", fh)
        assert f.read_text() == "hello\n"

    def test_mode_file_without_output_file_raises(self):
        with pytest.raises(ValueError, match="output_file required"):
            dump("hello", "mode=file", None)

    def test_mode_all_writes_and_prints(self, tmp_path, capsys):
        f = tmp_path / "out.txt"
        with open(f, "w") as fh:
            dump("hello", "mode=all", fh)
        captured = capsys.readouterr()
        assert "hello" in captured.out
        assert f.read_text() == "hello\n"

    def test_mode_all_without_output_file_only_prints(self, capsys):
        # output_file is None -- should still print without raising.
        dump("hello", "mode=all", None)
        captured = capsys.readouterr()
        assert "hello" in captured.out

    def test_unknown_mode_prints_error(self, capsys):
        dump("hello", "mode=bogus")
        captured = capsys.readouterr()
        assert "ERROR: unknown DUMP request" in captured.out


class TestIntro:
    def test_returns_datetime(self, capsys):
        start = intro("lfsr-seq", "1.0", "input.csv", "2")
        assert isinstance(start, datetime.datetime)

    def test_prints_expected_content(self, capsys):
        intro("lfsr-seq", "1.0", "input.csv", "2")
        captured = capsys.readouterr()
        assert "input.csv" in captured.out
        assert "GF order : 2" in captured.out
        assert "GNU GPL v3+" in captured.out

    def test_writes_to_output_file(self, tmp_path):
        f = tmp_path / "out.txt"
        with open(f, "w") as fh:
            intro("lfsr-seq", "1.0", "input.csv", "2", fh)
        content = f.read_text()
        assert "input.csv" in content


class TestSection:
    def test_prints_title_and_description(self, capsys):
        section("MY SECTION", "a description")
        captured = capsys.readouterr()
        assert "MY SECTION" in captured.out
        assert "a description" in captured.out

    def test_writes_to_output_file(self, tmp_path):
        f = tmp_path / "out.txt"
        with open(f, "w") as fh:
            section("TITLE", "desc", fh)
        content = f.read_text()
        assert "TITLE" in content
        assert "desc" in content

    def test_non_string_title_exits(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            section(123, "desc")
        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "_SECTION : title and content must be strings" in captured.out

    def test_non_string_description_exits(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            section("title", 456)
        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "_SECTION : title and content must be strings" in captured.out


class TestSubsection:
    def test_prints_title_and_description(self, capsys):
        subsection("MY SUBSECTION", "a description")
        captured = capsys.readouterr()
        assert "MY SUBSECTION" in captured.out
        assert "a description" in captured.out

    def test_writes_to_output_file(self, tmp_path):
        f = tmp_path / "out.txt"
        with open(f, "w") as fh:
            subsection("SUBTITLE", "subdesc", fh)
        content = f.read_text()
        assert "SUBTITLE" in content
        assert "subdesc" in content

    def test_non_string_title_exits(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            subsection(123, "desc")
        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "_SUBSECTION : title and content must be strings" in captured.out

    def test_non_string_description_exits(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            subsection("title", 456)
        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "_SUBSECTION : title and content must be strings" in captured.out


class TestDumpSeqRow:
    def test_single_row_prints_top_and_bottom_bars(self, capsys):
        dump_seq_row(1, ["line1", "line2"], 1, 20, "mode=console")
        captured = capsys.readouterr()
        # first (and only) row -> top bar drawn; last row -> bottom-last bar
        assert "┌" in captured.out  # top-left corner (first row)
        assert "└" in captured.out  # bottom-left corner (last row)

    def test_first_of_multiple_rows_no_bottom_last_bar(self, capsys):
        dump_seq_row(1, ["line1"], 3, 20, "mode=console")
        captured = capsys.readouterr()
        assert "┌" in captured.out  # top bar (seq_num == 1)
        assert "├" in captured.out  # open bottom bar (seq_num < no_seqs)
        assert "└" not in captured.out

    def test_middle_row_no_top_bar(self, capsys):
        dump_seq_row(2, ["line1"], 3, 20, "mode=console")
        captured = capsys.readouterr()
        assert "┌" not in captured.out  # no top bar (seq_num != 1)
        assert "├" in captured.out  # open bottom bar (seq_num < no_seqs)

    def test_last_row_of_multiple(self, capsys):
        dump_seq_row(3, ["line1"], 3, 20, "mode=console")
        captured = capsys.readouterr()
        assert "┌" not in captured.out
        assert "└" in captured.out  # closing bottom bar (last row)

    def test_writes_to_output_file(self, tmp_path):
        f = tmp_path / "out.txt"
        with open(f, "w") as fh:
            dump_seq_row(1, ["abc"], 1, 20, "mode=file", fh)
        content = f.read_text()
        assert "abc" in content

    def test_line_content_appears_padded(self, capsys):
        dump_seq_row(1, ["x"], 1, 10, "mode=console")
        captured = capsys.readouterr()
        # line should be padded to row_width then have a trailing " |"
        assert "x" in captured.out
        assert "|" in captured.out
