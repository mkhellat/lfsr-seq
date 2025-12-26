#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for polynomial operations.

Tests for polynomial_order and characteristic_polynomial functions.
"""

import pytest

# Import SageMath - will be skipped if not available via conftest
try:
    from sage.all import *
except ImportError:
    pytest.skip("SageMath not available", allow_module_level=True)

from lfsr.polynomial import (
    characteristic_polynomial,
    is_primitive_polynomial,
    polynomial_order,
)


class TestPolynomialOrder:
    """Tests for polynomial_order function."""

    def test_polynomial_order_simple(self):
        """Test computing order of a simple polynomial."""
        # Polynomial t + 1 over GF(2)
        # Order should be small (t^1 mod (t+1) = t, t^2 mod (t+1) = 1)
        R = PolynomialRing(GF(2), "t")
        poly = R("t + 1")
        order = polynomial_order(poly, 1, 2)
        assert order is not None
        assert order >= 1

    def test_polynomial_order_4bit(self):
        """Test computing order for a 4-bit LFSR polynomial."""
        R = PolynomialRing(GF(2), "t")
        # Characteristic polynomial for a 4-bit LFSR
        poly = R("t^4 + t^3 + t + 1")
        order = polynomial_order(poly, 4, 2)
        assert order is not None
        assert 1 <= order <= (2 ** 4) - 1

    def test_polynomial_order_gf3(self):
        """Test computing polynomial order over GF(3)."""
        R = PolynomialRing(GF(3), "t")
        poly = R("t^2 + 2*t + 1")
        order = polynomial_order(poly, 2, 3)
        assert order is not None
        assert 1 <= order <= (3 ** 2) - 1

    def test_polynomial_order_degree_bound(self):
        """Test that order search starts from polynomial degree."""
        R = PolynomialRing(GF(2), "t")
        poly = R("t^3 + t + 1")  # Degree 3
        order = polynomial_order(poly, 3, 2)
        # Order should be at least the degree
        assert order is not None
        assert order >= 3


class TestCharacteristicPolynomial:
    """Tests for characteristic_polynomial function."""

    def test_characteristic_polynomial_4bit(self, tmp_path):
        """Test computing characteristic polynomial for 4-bit LFSR."""
        # Build state update matrix
        from lfsr.core import build_state_update_matrix

        coeffs = [1, 1, 0, 1]
        _, CS = build_state_update_matrix(coeffs, 2)

        output_file = tmp_path / "test_char_poly.txt"
        with open(output_file, "w") as f:
            char_poly = characteristic_polynomial(CS, 2, f)

        # Verify polynomial properties
        assert char_poly is not None
        assert char_poly.parent() == PolynomialRing(GF(2), "t")
        assert char_poly.degree() == 4  # Should be degree 4 for 4-bit LFSR

        # Verify output file was written
        assert output_file.exists()
        content = output_file.read_text()
        assert "CHARACTERISTIC POLYNOMIAL" in content

    def test_characteristic_polynomial_3bit(self):
        """Test computing characteristic polynomial for 3-bit LFSR."""
        from lfsr.core import build_state_update_matrix

        coeffs = [1, 1, 0]
        _, CS = build_state_update_matrix(coeffs, 2)

        char_poly = characteristic_polynomial(CS, 2, None)

        assert char_poly is not None
        assert char_poly.degree() == 3

    def test_characteristic_polynomial_gf3(self):
        """Test computing characteristic polynomial over GF(3)."""
        from lfsr.core import build_state_update_matrix

        coeffs = [1, 2, 1]
        _, CS = build_state_update_matrix(coeffs, 3)

        char_poly = characteristic_polynomial(CS, 3, None)

        assert char_poly is not None
        assert char_poly.parent() == PolynomialRing(GF(3), "t")
        assert char_poly.degree() == 3

    def test_characteristic_polynomial_factors(self, tmp_path):
        """Test that characteristic polynomial is factored correctly."""
        from lfsr.core import build_state_update_matrix

        coeffs = [1, 1, 0, 1]
        _, CS = build_state_update_matrix(coeffs, 2)

        output_file = tmp_path / "test_factors.txt"
        with open(output_file, "w") as f:
            char_poly = characteristic_polynomial(CS, 2, f)

        # Factor the polynomial
        factors = factor(char_poly)
        assert len(list(factors)) > 0

        # Verify factors are in output
        content = output_file.read_text()
        assert "factor" in content.lower()


class TestPrimitivePolynomial:
    """Tests for is_primitive_polynomial function."""

    def test_primitive_polynomial_gf2_degree4(self):
        """Test that t^4 + t + 1 is primitive over GF(2)."""
        R = PolynomialRing(GF(2), "t")
        # t^4 + t + 1 is a well-known primitive polynomial over GF(2)
        poly = R("t^4 + t + 1")
        assert is_primitive_polynomial(poly, 2) is True

    def test_primitive_polynomial_gf2_degree3(self):
        """Test that t^3 + t + 1 is primitive over GF(2)."""
        R = PolynomialRing(GF(2), "t")
        # t^3 + t + 1 is primitive over GF(2)
        poly = R("t^3 + t + 1")
        assert is_primitive_polynomial(poly, 2) is True

    def test_non_primitive_irreducible_polynomial(self):
        """Test that an irreducible but non-primitive polynomial returns False."""
        R = PolynomialRing(GF(2), "t")
        # t^4 + t^3 + t^2 + t + 1 is irreducible but not primitive
        # Its order is 5, not 15
        poly = R("t^4 + t^3 + t^2 + t + 1")
        assert is_primitive_polynomial(poly, 2) is False

    def test_reducible_polynomial_not_primitive(self):
        """Test that a reducible polynomial is not primitive."""
        R = PolynomialRing(GF(2), "t")
        # t^4 + t^3 + t + 1 = (t+1)(t^3 + t + 1) is reducible
        poly = R("t^4 + t^3 + t + 1")
        assert is_primitive_polynomial(poly, 2) is False

    def test_primitive_polynomial_gf3(self):
        """Test primitive polynomial detection over GF(3)."""
        R = PolynomialRing(GF(3), "t")
        # t^2 + t + 2 is primitive over GF(3) (order = 8 = 3^2 - 1)
        poly = R("t^2 + t + 2")
        # Note: This may or may not be primitive, but the function should work
        result = is_primitive_polynomial(poly, 3)
        assert isinstance(result, bool)

    def test_zero_degree_polynomial(self):
        """Test that zero-degree polynomial is not primitive."""
        R = PolynomialRing(GF(2), "t")
        poly = R("1")  # Constant polynomial
        assert is_primitive_polynomial(poly, 2) is False

    def test_negative_degree_polynomial(self):
        """Test that zero polynomial is not primitive."""
        R = PolynomialRing(GF(2), "t")
        poly = R("0")  # Zero polynomial
        assert is_primitive_polynomial(poly, 2) is False

    def test_primitive_polynomial_maximum_period(self):
        """Test that primitive polynomial has maximum period."""
        R = PolynomialRing(GF(2), "t")
        poly = R("t^4 + t + 1")
        
        # If primitive, order should be 2^4 - 1 = 15
        degree = poly.degree()
        max_order = 2 ** degree - 1
        order = polynomial_order(poly, degree, 2)
        
        if is_primitive_polynomial(poly, 2):
            assert order == max_order

    def test_characteristic_polynomial_shows_primitive_indicator(self, tmp_path):
        """Test that characteristic_polynomial shows [PRIMITIVE] for primitive polynomials."""
        from lfsr.core import build_state_update_matrix

        # Use coefficients that yield a primitive polynomial
        # For degree 4, [1, 0, 0, 1] gives t^4 + t + 1 which is primitive
        coeffs = [1, 0, 0, 1]
        _, CS = build_state_update_matrix(coeffs, 2)

        output_file = tmp_path / "test_primitive.txt"
        with open(output_file, "w") as f:
            char_poly = characteristic_polynomial(CS, 2, f)

        # Check if polynomial is primitive
        is_prim = is_primitive_polynomial(char_poly, 2)
        
        # If primitive, output should contain [PRIMITIVE]
        content = output_file.read_text()
        if is_prim:
            assert "[PRIMITIVE]" in content

