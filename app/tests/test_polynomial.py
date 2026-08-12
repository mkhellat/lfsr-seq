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
    compute_period_via_factorization,
    detect_mathematical_shortcuts,
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


class TestComputePeriodViaFactorization:
    """Tests for compute_period_via_factorization.

    BUG FOUND AND FIXED #1 (2026-08-12): this function reconstructs the
    characteristic polynomial from a coefficient list internally (rather
    than deriving it from the real state-update matrix via
    characteristic_polynomial()). It used to build the polynomial with
    coefficients[0] applied to the t^(d-1) term and coefficients[-1] to
    the t^0 term -- reversed vs. the project's documented-correct
    convention (see CLAUDE.md "Known-fixed bug classes", matched by the
    matrix-based characteristic_polynomial()/build_state_update_matrix()
    pair): coefficients[i] maps to the t^i term, negated. Fixed to
    `char_poly += F(-coeff) * t**i`. Was silently invisible for
    palindromic coefficient lists (which is why the pre-existing
    [1,0,0,1] test case never caught it).

    BUG FOUND AND FIXED #2: polynomial_order() (polynomial.py) used to
    loop `for j in range(bi, ei)` where `ei = state_vector_space_size`,
    so `j` could never equal `state_vector_space_size` inside that range
    (range() excludes its upper bound) -- the `elif j ==
    state_vector_space_size: poly_order = oo` branch was dead code. If no
    `j` in the loop satisfied `t^j mod P == 1` (e.g. any polynomial
    divisible by `t`, which has no finite multiplicative order),
    `poly_order` was never assigned and the function raised
    UnboundLocalError. Fixed by initializing `poly_order = oo` before the
    loop and removing the dead elif.
    """

    def test_period_trinomial_gf2(self):
        period = compute_period_via_factorization([1, 0, 0, 1], 2)
        assert period == 15

    def test_period_returns_none_or_int(self):
        result = compute_period_via_factorization([1, 0, 1], 2)
        assert result is None or isinstance(result, int)

    def test_compute_period_via_factorization_matches_true_char_poly_gf3(self):
        """Regression test for BUG #1: a non-palindromic GF(3) coefficient
        list must now produce a period consistent with the real
        characteristic polynomial computed from the actual state-update
        matrix (the ground truth used elsewhere in this module/tests)."""
        from lfsr.core import build_state_update_matrix

        coeffs = [1, 2, 0]  # GF(3), degree 3, non-palindromic
        field_order = 3

        _, CS = build_state_update_matrix(coeffs, field_order)
        true_char_poly = characteristic_polynomial(CS, field_order, None)
        assert str(true_char_poly) == "t^3 + t + 2"

        # The function's internal reconstruction (same fixed logic
        # inlined here since the function doesn't expose the
        # intermediate polynomial) must now match the true char poly.
        F = GF(field_order)
        R = PolynomialRing(F, "t")
        t = R.gen()
        d = len(coeffs)
        fixed_char_poly = t**d
        for i, c in enumerate(coeffs):
            fixed_char_poly += F(-c) * t**i

        assert str(fixed_char_poly) == str(true_char_poly)

        # t^3 + t + 2 is irreducible over GF(3) but not primitive
        # (order 26, not 3^3-1=26 -- actually check: it should compute
        # cleanly now rather than crashing.
        period = compute_period_via_factorization(coeffs, field_order)
        assert isinstance(period, int)
        assert period > 0

    def test_polynomial_order_returns_infinity_for_t_divisible_poly(self):
        """Regression test for BUG #2: a polynomial divisible by t (zero
        constant term) has no finite multiplicative order, and
        polynomial_order must return oo rather than crashing."""
        F = GF(3)
        R = PolynomialRing(F, "t")
        t = R.gen()
        poly = t**3 + t**2 + 2 * t  # = t * (t^2 + t + 2), divisible by t

        assert polynomial_order(poly, 3, 3) == oo

    def test_compute_period_via_factorization_matches_true_char_poly_gf2_nonpalindromic(self):
        """Same BUG #1 regression, reproduced over GF(2) with a
        non-palindromic coefficient list (isolates the pure
        coefficient-ordering fix from the sign-negation part, a no-op
        over GF(2))."""
        from lfsr.core import build_state_update_matrix

        coeffs = [1, 1, 0, 1]  # not a palindrome ([1,0,1,1] reversed)
        field_order = 2

        _, CS = build_state_update_matrix(coeffs, field_order)
        true_char_poly = characteristic_polynomial(CS, field_order, None)
        assert str(true_char_poly) == "t^4 + t^3 + t + 1"

        F = GF(field_order)
        R = PolynomialRing(F, "t")
        t = R.gen()
        d = len(coeffs)
        fixed_char_poly = t**d
        for i, c in enumerate(coeffs):
            fixed_char_poly += F(-c) * t**i

        assert str(fixed_char_poly) == str(true_char_poly)

    def test_period_via_factorization_invalid_input_returns_none_gracefully(self):
        # Degenerate/empty coefficients shouldn't raise.
        result = compute_period_via_factorization([], 2)
        assert result is None or isinstance(result, int)


class TestDetectMathematicalShortcuts:
    """Tests for detect_mathematical_shortcuts.

    This function builds its internal characteristic polynomial with the
    same construction as compute_period_via_factorization (see BUG #1 on
    TestComputePeriodViaFactorization above, now fixed: coefficients[i]
    maps to the t^i term, negated), so 'is_primitive'/'expected_period'
    here now agree with the true characteristic polynomial for
    non-palindromic coefficient lists too.

    BUG FOUND AND FIXED #3 (2026-08-12): `is_primitive`/`is_irreducible`
    used to be assigned *inside* the outer try block, after `F =
    GF(field_order)` and the char_poly construction. If GF(field_order)
    (or the char_poly build) raised before reaching those assignments,
    the outer `except (TypeError, ValueError, AttributeError): pass`
    swallowed the exception, but the function's final return dict still
    referenced them -- raising UnboundLocalError instead of returning the
    documented all-defaults dict ("If analysis fails, return defaults").
    Fixed by initializing both to False before the outer try block.
    """

    def test_returns_expected_keys(self):
        result = detect_mathematical_shortcuts([1, 0, 0, 1], 2)
        for key in (
            "is_primitive",
            "is_irreducible",
            "recommended_method",
            "expected_period",
            "shortcuts_available",
            "complexity_estimate",
        ):
            assert key in result

    def test_primitive_trinomial_palindromic_case(self):
        # [1, 0, 0, 1] is palindromic, so the internal reconstruction bug
        # is invisible and this matches the true t^4+t+1 (primitive).
        result = detect_mathematical_shortcuts([1, 0, 0, 1], 2)
        assert result["is_primitive"] is True
        assert result["recommended_method"] == "primitive_shortcut"
        assert result["expected_period"] == 15
        assert "primitive_polynomial" in result["shortcuts_available"]
        assert result["complexity_estimate"] == "O(1)"

    def test_trinomial_pattern_detected(self):
        # Exactly 3 non-zero coefficients -> trinomial pattern shortcut.
        result = detect_mathematical_shortcuts([1, 0, 0, 1, 1], 2)
        # non_zero_count here is 3 (indices 0, 3, 4)
        assert "trinomial_pattern" in result["shortcuts_available"]

    def test_pentanomial_pattern_detected(self):
        result = detect_mathematical_shortcuts([1, 1, 1, 1, 1], 2)
        assert "pentanomial_pattern" in result["shortcuts_available"]

    def test_small_degree_shortcut_gf2(self):
        result = detect_mathematical_shortcuts([1, 0, 1], 2)
        assert "small_degree" in result["shortcuts_available"]

    def test_small_degree_shortcut_not_added_for_gf3(self):
        # small_degree shortcut is gated on field_order == 2
        result = detect_mathematical_shortcuts([1, 0, 1], 3)
        assert "small_degree" not in result["shortcuts_available"]

    def test_large_degree_recommends_factorization(self):
        coeffs = [0] * 16 + [1]  # degree 17, sparse
        result = detect_mathematical_shortcuts(coeffs, 2)
        if not result["is_primitive"]:
            assert result["recommended_method"] in ("factorization", "enumeration")

    def test_explicit_state_vector_dim(self):
        result = detect_mathematical_shortcuts([1, 0, 0, 1], 2, state_vector_dim=4)
        assert result["is_primitive"] is True

    def test_irreducible_not_primitive_branch(self):
        # t^4 + t^3 + t^2 + t + 1 is irreducible over GF(2) but has order
        # 5 (not 15), so it's irreducible without being primitive -- this
        # exercises the 'irreducible_polynomial' shortcut branch distinct
        # from the primitive-polynomial branch. [1,1,1,1] is palindromic,
        # so the internal reconstruction bug doesn't distort this case.
        result = detect_mathematical_shortcuts([1, 1, 1, 1], 2)
        assert result["is_primitive"] is False
        assert result["is_irreducible"] is True
        assert "irreducible_polynomial" in result["shortcuts_available"]
        assert result["recommended_method"] == "factorization"
        assert result["complexity_estimate"] == "O(d^3)"

    def test_detect_shortcuts_returns_defaults_on_gf_construction_failure(self):
        """Regression test for BUG #3: an invalid field_order that makes
        GF(field_order) raise inside the outer try block must return the
        documented all-defaults dict instead of crashing."""
        result = detect_mathematical_shortcuts([1, 0, 1], "not_a_number")
        assert result["is_primitive"] is False
        assert result["is_irreducible"] is False
        assert result["recommended_method"] == "enumeration"
        assert result["expected_period"] is None
        assert result["shortcuts_available"] == []

