#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for I/O operations.

Tests for CSV file reading and validation functions.
"""

import os

import pytest

from lfsr.constants import MAX_CSV_ROWS, MAX_FILE_SIZE
from lfsr.io import (
    read_and_validate_csv,
    read_coefficient_vectors,
    read_csv_coefficients,
    sanitize_file_path,
    validate_csv_file,
)


class TestValidateCsvFile:
    """Tests for validate_csv_file function."""

    def test_valid_file(self, tmp_path):
        """Test validation of a valid CSV file."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("1,0,1\n")
        validate_csv_file(str(csv_file))
        # Should not raise

    def test_file_not_found(self):
        """Test that non-existent files are rejected."""
        with pytest.raises(SystemExit):
            validate_csv_file("/nonexistent/file.csv")

    def test_file_not_readable(self, tmp_path):
        """Test that unreadable files are rejected."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("1,0,1\n")
        # Make file unreadable (on Unix systems)
        if os.name != "nt":  # Skip on Windows
            os.chmod(csv_file, 0o000)
            try:
                with pytest.raises(SystemExit):
                    validate_csv_file(str(csv_file))
            finally:
                os.chmod(csv_file, 0o644)

    def test_empty_file(self, tmp_path):
        """Test that empty files are rejected."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")
        with pytest.raises(SystemExit):
            validate_csv_file(str(csv_file))

    def test_directory_not_file(self, tmp_path):
        """Test that directories are rejected."""
        with pytest.raises(SystemExit):
            validate_csv_file(str(tmp_path))


class TestReadAndValidateCsv:
    """Tests for read_and_validate_csv function."""

    def test_read_single_vector(self, tmp_path):
        """Test reading a CSV file with a single coefficient vector."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("1,1,0,1\n")

        result = read_and_validate_csv(str(csv_file), 2)
        assert len(result) == 1
        assert result[0] == ["1", "1", "0", "1"]

    def test_read_multiple_vectors(self, tmp_path):
        """Test reading a CSV file with multiple coefficient vectors."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("1,1,0,1\n1,0,1,1\n")

        result = read_and_validate_csv(str(csv_file), 2)
        assert len(result) == 2
        assert result[0] == ["1", "1", "0", "1"]
        assert result[1] == ["1", "0", "1", "1"]

    def test_read_empty_csv(self, tmp_path):
        """Test that empty CSV files are rejected."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")  # Truly empty file — csv.reader yields 0 rows

        with pytest.raises(SystemExit):
            read_and_validate_csv(str(csv_file), 2)

    def test_read_csv_with_whitespace(self, tmp_path):
        """Test reading CSV with whitespace (should be handled by csv.reader)."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("1, 1, 0, 1\n")  # Spaces after commas

        result = read_and_validate_csv(str(csv_file), 2)
        # csv.reader should handle whitespace
        assert len(result) == 1

    def test_read_csv_inconsistent_lengths(self, tmp_path):
        """Test reading CSV with inconsistent vector lengths (should warn)."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("1,1,0,1\n1,0,1\n")  # Different lengths

        # Should not raise, but may warn
        result = read_and_validate_csv(str(csv_file), 2)
        assert len(result) == 2

    def test_read_csv_gf3(self, tmp_path):
        """Test reading CSV for GF(3) coefficients."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("1,2,1\n")

        result = read_and_validate_csv(str(csv_file), 3)
        assert len(result) == 1
        assert result[0] == ["1", "2", "1"]

    def test_read_csv_skips_comment_lines(self, tmp_path):
        """Lines starting with # (a coefficient vector's first field) are comments, not data."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("# a comment\n1,1,0,1\n# another comment\n1,0,0,1\n")

        result = read_and_validate_csv(str(csv_file), 2)
        assert result == [["1", "1", "0", "1"], ["1", "0", "0", "1"]]

    def test_read_csv_skips_indented_comment_lines(self, tmp_path):
        """A comment line may be preceded by whitespace before the #."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("   # indented comment\n1,1,0,1\n")

        result = read_and_validate_csv(str(csv_file), 2)
        assert result == [["1", "1", "0", "1"]]

    def test_read_csv_skips_blank_lines(self, tmp_path):
        """Blank lines between data rows are ignored, not treated as empty vectors."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("1,1,0,1\n\n1,0,0,1\n")

        result = read_and_validate_csv(str(csv_file), 2)
        assert result == [["1", "1", "0", "1"], ["1", "0", "0", "1"]]

    def test_read_csv_comments_and_blanks_dont_trigger_length_warning(
        self, tmp_path, capsys
    ):
        """Comment/blank lines must not appear in the length-consistency check."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("# note\n1,1,0,1\n\n# another note\n1,0,0,1\n")

        result = read_and_validate_csv(str(csv_file), 2)
        assert len(result) == 2
        captured = capsys.readouterr()
        assert "WARNING" not in captured.out

    def test_read_csv_comment_only_file_is_empty(self, tmp_path):
        """A file containing only comments/blank lines has no data rows."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("# just a comment\n\n# another comment\n")

        with pytest.raises(SystemExit):
            read_and_validate_csv(str(csv_file), 2)

    def test_read_csv_too_many_rows(self, tmp_path, capsys):
        """More than MAX_CSV_ROWS real data rows must be rejected with a
        clear error, covering the row-count DoS guard (lines 159-162)."""
        csv_file = tmp_path / "big.csv"
        # One row per line, all with the same short vector, one more
        # than the limit so the guard trips as soon as possible.
        lines = "\n".join("1,0" for _ in range(MAX_CSV_ROWS + 1))
        csv_file.write_text(lines + "\n")

        with pytest.raises(SystemExit):
            read_and_validate_csv(str(csv_file), 2)
        captured = capsys.readouterr()
        assert "too many rows" in captured.out


class TestSanitizeFilePath:
    """Tests for sanitize_file_path's error branches (lines 36-39, 45-47)."""

    def test_valid_relative_path_resolves(self, tmp_path):
        target = tmp_path / "file.csv"
        target.write_text("1,0\n")
        result = sanitize_file_path(str(target))
        assert result.is_absolute()

    def test_null_byte_in_path_triggers_oserror_exit(self, capsys):
        """A path containing an embedded NUL raises OSError/ValueError
        from Path.resolve(), which sanitize_file_path must catch and
        turn into a clean SystemExit rather than propagating."""
        with pytest.raises(SystemExit) as excinfo:
            sanitize_file_path("bad\x00path")
        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "ERROR: Invalid file path" in captured.out

    def test_proc_path_rejected_as_suspicious(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            sanitize_file_path("/proc/self/mem")
        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "Suspicious file path detected" in captured.out
        assert "Path traversal attempts are not allowed" in captured.out

    def test_sys_path_rejected_as_suspicious(self, capsys):
        with pytest.raises(SystemExit):
            sanitize_file_path("/sys/kernel/foo")
        captured = capsys.readouterr()
        assert "Suspicious file path detected" in captured.out


class TestValidateCsvFileTooLarge:
    """Covers the file-too-large branch (lines 91-94)."""

    def test_file_larger_than_max_is_rejected(self, tmp_path, capsys):
        csv_file = tmp_path / "huge.csv"
        # Write just over MAX_FILE_SIZE bytes efficiently via seek+write.
        with open(csv_file, "wb") as f:
            f.seek(MAX_FILE_SIZE)
            f.write(b"\n")
        assert csv_file.stat().st_size > MAX_FILE_SIZE

        with pytest.raises(SystemExit):
            validate_csv_file(str(csv_file))
        captured = capsys.readouterr()
        assert "CSV file too large" in captured.out
        assert "Maximum allowed" in captured.out


class TestReadCoefficientVectors:
    """Tests for read_coefficient_vectors (lines 214-215: ValueError skip)."""

    def test_valid_rows_converted_to_ints(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("1,1,0,1\n1,0,1,1\n")
        result = read_coefficient_vectors(str(csv_file), 2)
        assert result == [[1, 1, 0, 1], [1, 0, 1, 1]]

    def test_non_numeric_row_is_silently_skipped(self, tmp_path):
        """A row with non-numeric garbage can't be int()-converted;
        read_coefficient_vectors is documented to skip it rather than
        raise, leaving validation to the caller."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("1,1,0,1\nabc,def\n1,0,0,1\n")
        result = read_coefficient_vectors(str(csv_file), 2)
        assert result == [[1, 1, 0, 1], [1, 0, 0, 1]]

    def test_all_rows_non_numeric_returns_empty_list(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("abc,def\nghi,jkl\n")
        result = read_coefficient_vectors(str(csv_file), 2)
        assert result == []


class TestReadCsvCoefficients:
    """Tests for the unvalidated reader read_csv_coefficients (lines 246-248)."""

    def test_reads_raw_string_rows(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("1,1,0,1\n1,0,1,1\n")
        result = read_csv_coefficients(str(csv_file))
        assert result == [["1", "1", "0", "1"], ["1", "0", "1", "1"]]

    def test_does_not_validate_missing_file(self):
        with pytest.raises(FileNotFoundError):
            read_csv_coefficients("/nonexistent/file.csv")

    def test_empty_file_returns_empty_list(self, tmp_path):
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")
        result = read_csv_coefficients(str(csv_file))
        assert result == []

