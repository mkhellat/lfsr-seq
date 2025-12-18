#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for finite field validation functions.

Tests for validate_gf_order, validate_coefficient, and validate_coefficient_vector.
"""

import pytest
import sys
from unittest.mock import patch

from lfsr.field import (
    validate_coefficient,
    validate_coefficient_vector,
    validate_gf_order,
)


class TestValidateGfOrder:
    """Tests for validate_gf_order function."""

    def test_valid_prime(self):
        """Test validation of valid prime numbers."""
        assert validate_gf_order("2") == 2
        assert validate_gf_order("3") == 3
        assert validate_gf_order("5") == 5
        assert validate_gf_order("7") == 7
        assert validate_gf_order("11") == 11
        assert validate_gf_order("97") == 97

    def test_valid_prime_power(self):
        """Test validation of valid prime powers."""
        # 4 = 2^2
        assert validate_gf_order("4") == 4
        # 8 = 2^3
        assert validate_gf_order("8") == 8
        # 9 = 3^2
        assert validate_gf_order("9") == 9

    def test_invalid_not_integer(self):
        """Test that non-integer strings are rejected."""
        with patch("sys.exit") as mock_exit:
            mock_exit.side_effect = SystemExit(1)
            with pytest.raises(SystemExit):
                validate_gf_order("abc")
            mock_exit.assert_called_once_with(1)

    def test_invalid_too_small(self):
        """Test that values less than 2 are rejected."""
        with patch("sys.exit") as mock_exit:
            mock_exit.side_effect = SystemExit(1)
            with pytest.raises(SystemExit):
                validate_gf_order("1")
            mock_exit.assert_called_once_with(1)

        with patch("sys.exit") as mock_exit:
            mock_exit.side_effect = SystemExit(1)
            with pytest.raises(SystemExit):
                validate_gf_order("0")
            mock_exit.assert_called_once_with(1)

        with patch("sys.exit") as mock_exit:
            mock_exit.side_effect = SystemExit(1)
            with pytest.raises(SystemExit):
                validate_gf_order("-1")
            mock_exit.assert_called_once_with(1)

    def test_invalid_not_prime_or_power(self):
        """Test that composite numbers that aren't prime powers are rejected."""
        with patch("sys.exit") as mock_exit:
            mock_exit.side_effect = SystemExit(1)
            with pytest.raises(SystemExit):
                validate_gf_order("6")  # 6 = 2 * 3, not a prime power
            mock_exit.assert_called_once_with(1)

        with patch("sys.exit") as mock_exit:
            mock_exit.side_effect = SystemExit(1)
            with pytest.raises(SystemExit):
                validate_gf_order("10")  # 10 = 2 * 5
            mock_exit.assert_called_once_with(1)

        with patch("sys.exit") as mock_exit:
            mock_exit.side_effect = SystemExit(1)
            with pytest.raises(SystemExit):
                validate_gf_order("12")  # 12 = 2^2 * 3
            mock_exit.assert_called_once_with(1)

    def test_large_prime_power_limit(self):
        """Test that large prime powers within limit are accepted."""
        # 16 = 2^4, should be within limit (1000)
        assert validate_gf_order("16") == 16
        # 25 = 5^2
        assert validate_gf_order("25") == 25
        # 27 = 3^3
        assert validate_gf_order("27") == 27


class TestValidateCoefficient:
    """Tests for validate_coefficient function."""

    def test_valid_coefficients_gf2(self):
        """Test validation of valid coefficients for GF(2)."""
        assert validate_coefficient("0", 2, 1, 0) == 0
        assert validate_coefficient("1", 2, 1, 0) == 1

    def test_valid_coefficients_gf3(self):
        """Test validation of valid coefficients for GF(3)."""
        assert validate_coefficient("0", 3, 1, 0) == 0
        assert validate_coefficient("1", 3, 1, 0) == 1
        assert validate_coefficient("2", 3, 1, 0) == 2

    def test_invalid_coefficient_not_integer(self):
        """Test that non-integer coefficients are rejected."""
        with patch("sys.exit") as mock_exit:
            mock_exit.side_effect = SystemExit(1)
            with pytest.raises(SystemExit):
                validate_coefficient("abc", 2, 1, 0)
            mock_exit.assert_called_once_with(1)

    def test_invalid_coefficient_too_large(self):
        """Test that coefficients >= gf_order are rejected."""
        with patch("sys.exit") as mock_exit:
            mock_exit.side_effect = SystemExit(1)
            with pytest.raises(SystemExit):
                validate_coefficient("2", 2, 1, 0)  # 2 >= 2
            mock_exit.assert_called_once_with(1)

        with patch("sys.exit") as mock_exit:
            mock_exit.side_effect = SystemExit(1)
            with pytest.raises(SystemExit):
                validate_coefficient("3", 2, 1, 0)  # 3 >= 2
            mock_exit.assert_called_once_with(1)

        with patch("sys.exit") as mock_exit:
            mock_exit.side_effect = SystemExit(1)
            with pytest.raises(SystemExit):
                validate_coefficient("5", 3, 1, 0)  # 5 >= 3
            mock_exit.assert_called_once_with(1)

    def test_invalid_coefficient_negative(self):
        """Test that negative coefficients are rejected."""
        with patch("sys.exit") as mock_exit:
            mock_exit.side_effect = SystemExit(1)
            with pytest.raises(SystemExit):
                validate_coefficient("-1", 2, 1, 0)
            mock_exit.assert_called_once_with(1)


class TestValidateCoefficientVector:
    """Tests for validate_coefficient_vector function."""

    def test_valid_vector_gf2(self):
        """Test validation of valid coefficient vector for GF(2)."""
        vector = ["1", "1", "0", "1"]
        validate_coefficient_vector(vector, 2, 1)
        # Should not raise

    def test_valid_vector_gf3(self):
        """Test validation of valid coefficient vector for GF(3)."""
        vector = ["1", "2", "1"]
        validate_coefficient_vector(vector, 3, 1)
        # Should not raise

    def test_empty_vector(self):
        """Test that empty vectors are rejected."""
        with patch("sys.exit") as mock_exit:
            mock_exit.side_effect = SystemExit(1)
            with pytest.raises(SystemExit):
                validate_coefficient_vector([], 2, 1)
            mock_exit.assert_called_once_with(1)

    def test_vector_with_invalid_coefficient(self):
        """Test that vectors with invalid coefficients are rejected."""
        with patch("sys.exit") as mock_exit:
            mock_exit.side_effect = SystemExit(1)
            with pytest.raises(SystemExit):
                validate_coefficient_vector(["1", "2", "0"], 2, 1)  # 2 >= 2
            mock_exit.assert_called_once_with(1)

    def test_vector_with_non_integer(self):
        """Test that vectors with non-integer coefficients are rejected."""
        with patch("sys.exit") as mock_exit:
            mock_exit.side_effect = SystemExit(1)
            with pytest.raises(SystemExit):
                validate_coefficient_vector(["1", "abc", "0"], 2, 1)
            mock_exit.assert_called_once_with(1)

    def test_multiple_vectors(self):
        """Test validation of multiple vectors."""
        vector1 = ["1", "0", "1"]
        vector2 = ["1", "1", "0"]
        validate_coefficient_vector(vector1, 2, 1)
        validate_coefficient_vector(vector2, 2, 2)
        # Should not raise

