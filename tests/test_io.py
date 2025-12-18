#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for I/O operations.

Tests for CSV file reading and validation functions.
"""

import csv
import os
import pytest
import tempfile
from pathlib import Path

from lfsr.io import read_and_validate_csv, validate_csv_file


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
        csv_file.write_text("\n")  # Empty line

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

