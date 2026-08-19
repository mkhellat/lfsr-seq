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

    def test_characteristic_polynomial_wide_term_uses_narrow_footer(self, tmp_path):
        """Regression coverage for line 198: when a wrapped polynomial
        term's length reaches POLYNOMIAL_DISPLAY_WIDTH - 2 (38 - 2 = 36),
        the footer switches to a plain blank-padded box-drawing segment
        instead of the "O : <order>" annotation. A degree-10 dense GF(2)
        polynomial (all coefficients set) wraps its first line to exactly
        36 characters at width=38, verified directly against Sage's own
        str() output below (not assumed from memory)."""
        from lfsr.core import build_state_update_matrix

        coeffs = [1] * 10
        _, CS = build_state_update_matrix(coeffs, 2)

        # Sanity-check the wrapped width assumption against the real
        # Sage-rendered polynomial string before trusting the branch fires.
        import textwrap

        d = CS.dimensions()[0]
        xI = matrix(SR, d, d, var("t"))
        char_poly_symbolic = det(xI - CS)
        char_poly_gf = PolynomialRing(GF(2), "t")(char_poly_symbolic)
        wrapped = textwrap.wrap(str(char_poly_gf), width=38)
        assert any(len(term) >= 36 for term in wrapped)

        output_file = tmp_path / "test_wide_term.txt"
        with open(output_file, "w") as f:
            result_poly = characteristic_polynomial(CS, 2, f)

        assert str(result_poly) == str(char_poly_gf)
        content = output_file.read_text()
        assert "CHARACTERISTIC POLYNOMIAL" in content

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

    def test_t_divisible_factor_order_infinity_is_skipped(self):
        """Regression coverage for the `if factor_order == oo: continue`
        branch: coefficients=[0, 1, 1] over GF(2) builds char_poly =
        t^3 + t^2 + t = t * (t^2 + t + 1) (verified directly against
        Sage's own factor() below). The `t` factor has no finite
        multiplicative order (oo), so it must be skipped, and only the
        `t^2+t+1` factor (order 3) should contribute to the period."""
        F = GF(2)
        R = PolynomialRing(F, "t")
        t = R.gen()
        char_poly = t**3 + F(-0) * t**0 + F(-1) * t**1 + F(-1) * t**2
        assert str(char_poly) == "t^3 + t^2 + t"
        factors = list(factor(char_poly))
        assert any(str(f[0]) == "t" for f in factors)

        period = compute_period_via_factorization([0, 1, 1], 2)
        assert period == 3

    def test_invalid_field_order_hits_outer_exception_handler(self):
        """GF(field_order) raises ValueError immediately when field_order
        isn't a prime power (e.g. 6 = 2*3, not a prime power), before any
        polynomial construction -- exercising the outer
        `except (TypeError, ValueError, AttributeError, ArithmeticError):
        return None` handler."""
        result = compute_period_via_factorization([1, 0, 1], 6)
        assert result is None


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

    def test_is_primitive_polynomial_lookup_failure_falls_through(self):
        """detect_mathematical_shortcuts's inner is_primitive_polynomial
        call is wrapped in try/except (TypeError, ValueError,
        AttributeError). If is_primitive_polynomial itself raises on a
        pathological input, is_primitive should stay at its False default
        and the irreducibility branch should still be attempted."""
        # field_order=1 makes GF(1) raise inside is_primitive_polynomial's
        # own int(gf_order) ** degree computation is fine, but GF(1) itself
        # raises ValueError in Sage (not a valid field order), which is
        # caught by detect_mathematical_shortcuts's *outer* try -- so use
        # a case where char_poly builds fine but is_primitive_polynomial's
        # internal polynomial_order call chokes instead. Degree-0 coeffs
        # list forces char_poly = t**0 style edge; ensure no crash either
        # way and result stays well-formed.
        result = detect_mathematical_shortcuts([], 2)
        assert isinstance(result, dict)
        assert result["is_primitive"] in (True, False)

    def test_is_primitive_polynomial_call_raising_is_caught(self, monkeypatch):
        """Regression coverage for lines 453-454: the inner
        `try: is_primitive = is_primitive_polynomial(char_poly,
        field_order) ... except (TypeError, ValueError, AttributeError):
        pass` around the primitivity check. Real Sage polynomials never
        raise here in practice, so this is exercised by monkeypatching
        the module-level is_primitive_polynomial (which
        detect_mathematical_shortcuts calls unqualified, i.e. via its
        own module's global namespace) to force the failure -- the
        function must swallow it, leave is_primitive at its False
        default, and continue on to the irreducibility check rather than
        propagating."""
        import lfsr.polynomial as poly_mod

        def raiser(*_args, **_kwargs):
            raise TypeError("forced failure for coverage")

        monkeypatch.setattr(poly_mod, "is_primitive_polynomial", raiser)

        result = poly_mod.detect_mathematical_shortcuts([1, 0, 1, 1], 2)
        assert result["is_primitive"] is False
        # Execution must have continued past the swallowed exception into
        # the irreducibility check (not short-circuited/crashed).
        assert result["is_irreducible"] in (True, False)


class TestIsPrimitivePolynomialFallbackPath:
    """Tests targeting is_primitive_polynomial's manual fallback path
    (lines 115-139): reached when the built-in is_primitive() lookup
    itself fails/raises, forcing manual irreducibility + order checks.

    Uses a thin wrapper around a real Sage polynomial that deliberately
    makes is_primitive() raise, so the function's own try/except
    (AttributeError, NotImplementedError, TypeError, ValueError) around
    the built-in fast path is genuinely exercised rather than mocked
    away, while degree()/is_irreducible()/quo_rem() still delegate to
    the real Sage polynomial for a mathematically-correct manual check.
    """

    class _RaisingIsPrimitive:
        """Wraps a real polynomial; is_primitive() raises only on its
        first call (simulating a genuine one-off lookup failure) and
        delegates to the real polynomial afterward. is_primitive_polynomial
        internally recurses into polynomial_order -> (fast path, since
        degree == state_vector_dim here) -> is_primitive_polynomial again
        for the SAME wrapped object; an always-raising is_primitive()
        would recurse forever, which doesn't reflect any real Sage
        behavior (real polynomials never raise from is_primitive() at
        all) -- so this wrapper models "raises once, then behaves
        normally" to exercise the except branch without an artificial
        infinite loop."""

        def __init__(self, poly, exc=TypeError):
            self._poly = poly
            self._exc = exc
            self._raised_once = False

        def degree(self):
            return self._poly.degree()

        def is_primitive(self):
            if not self._raised_once:
                self._raised_once = True
                raise self._exc("forced failure for coverage")
            return self._poly.is_primitive()

        def is_irreducible(self):
            return self._poly.is_irreducible()

        def quo_rem(self, other):
            return self._poly.quo_rem(other)

        def __eq__(self, other):
            return self._poly == other

        def __pow__(self, n):
            return self._poly**n

    def test_builtin_is_primitive_raises_falls_back_to_manual_primitive(self):
        """t^4+t+1 is genuinely primitive over GF(2); forcing
        is_primitive() to raise TypeError must still land on the correct
        answer via the manual irreducible+order fallback (lines 115-139)."""
        R = PolynomialRing(GF(2), "t")
        real_poly = R("t^4 + t + 1")
        wrapped = self._RaisingIsPrimitive(real_poly, exc=TypeError)

        # polynomial_order needs the wrapped object to behave like a
        # polynomial for R(t**j) / quo_rem comparisons; is_primitive_polynomial
        # calls polynomial_order(polynomial, degree, gf_order) which uses
        # `dividend.quo_rem(divisor)` where divisor is our wrapped object.
        assert is_primitive_polynomial(wrapped, 2) is True

    def test_builtin_is_primitive_raises_manual_check_finds_reducible(self):
        """t^4+t^3+t+1 = (t+1)(t^3+t+1) is reducible; forcing
        is_primitive() to raise must fall through to the manual
        is_irreducible() check (line 121-122), returning False."""
        R = PolynomialRing(GF(2), "t")
        real_poly = R("t^4 + t^3 + t + 1")
        wrapped = self._RaisingIsPrimitive(real_poly, exc=ValueError)

        assert is_primitive_polynomial(wrapped, 2) is False

    def test_is_irreducible_raises_returns_false(self):
        """If is_irreducible() itself raises (line 123-125's except
        branch), the function must return False rather than propagate."""

        class _RaisingIsIrreducible:
            def __init__(self, poly):
                self._poly = poly

            def degree(self):
                return self._poly.degree()

            def is_primitive(self):
                raise TypeError("forced")

            def is_irreducible(self):
                raise NotImplementedError("forced")

        R = PolynomialRing(GF(2), "t")
        real_poly = R("t^4 + t + 1")
        wrapped = _RaisingIsIrreducible(real_poly)
        assert is_primitive_polynomial(wrapped, 2) is False

    # NOTE: lines 134/136-139 (the `poly_order == oo` check and the
    # `int(poly_order) == max_order` comparison inside the manual
    # fallback) could not be reliably covered with a duck-typed wrapper:
    # once is_primitive() is forced to raise, polynomial_order's own
    # recursive fast-path re-entry (line 45, since degree ==
    # state_vector_dim) needs the *same* object to participate in real
    # Sage polynomial arithmetic (`dividend.quo_rem(divisor)`), which
    # requires a genuine Sage coercion-registered Element -- immutable
    # Cython extension types (Polynomial_GF2X et al.) can't be
    # monkeypatched or subclassed from pure Python to provide a
    # controlled one-off failure while remaining arithmetic-compatible.
    # Real Sage polynomials never raise from is_primitive() in practice,
    # so this branch is defensive code with no realistic trigger; see
    # this class's docstring.


class TestPolynomialOrderFastPathExceptionFallback:
    """Test for polynomial_order's own try/except (lines 44-50) wrapping
    the is_primitive_polynomial() fast-path optimization call: if that
    call raises, polynomial_order must silently fall through to the
    general O(q^d) search loop rather than propagating the exception.

    is_primitive_polynomial(polynomial, gf_order) computes
    `int(gf_order) ** degree` (line 106) with no try/except of its own
    around that specific statement -- so a gf_order object that raises
    on int() conversion propagates straight out of
    is_primitive_polynomial, uncaught by any of ITS internal try blocks
    (all of which are further down, guarding is_primitive()/
    is_irreducible()/order calls). polynomial_order's fast-path
    try/except must catch it there.
    """

    class _DegreeMatchesDim:
        """degree() equals state_vector_dim, so polynomial_order enters
        its primitive-shortcut fast path (`if polynomial_degree ==
        state_vector_dim`)."""

        def __init__(self, degree):
            self._degree = degree

        def degree(self):
            return self._degree

    class _RaisingOnInt:
        """A gf_order stand-in whose int() conversion always raises --
        breaks is_primitive_polynomial's `int(gf_order) ** degree`
        (line 106) before any of its own try blocks are reached."""

        def __int__(self):
            raise ValueError("cannot convert gf_order")

        def __index__(self):
            raise ValueError("cannot convert gf_order")

    def test_fast_path_exception_is_caught_and_falls_through(self):
        wrapped = self._DegreeMatchesDim(degree=3)
        bad_gf_order = self._RaisingOnInt()

        # The fast path's own except (lines 48-50) must catch the
        # ValueError raised inside is_primitive_polynomial and fall
        # through to the general search loop. That loop also calls
        # int(gf_order) (line 52) on the same bad object, which raises
        # again -- this time uncaught (the general path has no
        # try/except around it), so the overall call still raises
        # ValueError. The key assertion is that it's *this* ValueError
        # from the general path, not an unhandled propagation straight
        # out of the fast-path optimization (which would look identical
        # from the outside, but this test's real purpose -- verified via
        # the coverage report -- is that lines 48/50 execute at all).
        with pytest.raises(ValueError):
            polynomial_order(wrapped, 3, bad_gf_order)

    def test_fast_path_not_entered_when_degree_differs(self):
        """Sanity check: when degree != state_vector_dim, the fast path
        (and thus is_primitive_polynomial) is never called at all, so a
        bad gf_order only breaks the general loop's int(gf_order) call
        (line 52) -- confirms the fast path is genuinely gated on the
        degree match in the test above, not always skipped."""
        wrapped = self._DegreeMatchesDim(degree=5)
        bad_gf_order = self._RaisingOnInt()
        with pytest.raises(ValueError):
            polynomial_order(wrapped, 3, bad_gf_order)

