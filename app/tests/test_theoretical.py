#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for lfsr.theoretical (irreducible-polynomial analysis and
theoretical-bounds comparison).

BUGS found and fixed (2026-08-11, see commit history):

1. ``analyze_irreducible_properties`` (theoretical.py:54) used to crash
   on EVERY input, via two independent missing-name bugs depending on
   which branch was taken:

   a. Irreducible-polynomial branch (line 138): called the bare name
      ``polynomial_order(polynomial, state_vector_dim, field_order)``,
      meant to be ``lfsr.polynomial.polynomial_order`` but never
      imported into theoretical.py. Fixed with an explicit
      ``from lfsr.polynomial import polynomial_order`` at module level.

   b. Composite-polynomial branch: referenced the bare name ``oo``
      (SageMath's infinity constant), also not in ``sage_imports.py``'s
      curated ``__all__`` (same root cause as lfsr/export.py's bug --
      see test_export.py's module docstring). Fixed by adding ``oo`` to
      sage_imports.py's exports.

   Tests below assert the real, working output for primitive,
   irreducible-nonprimitive, and composite polynomials.

2. ``_polynomial_order_helper`` (theoretical.py:285) was never affected
   by either bug (it only ever *returns* the bare name ``oo``, never
   compares against it) -- confirmed working correctly and cross-checked
   against ``lfsr.polynomial.polynomial_order`` (an independent,
   already-tested implementation) for both a primitive and a
   non-primitive polynomial below.

3. ``compare_with_theoretical_bounds`` is pure Python (no SageMath name
   dependencies) and works correctly; verified against hand-computed
   expected values for primitive/irreducible/composite/unverifiable
   cases.

Formulas cross-checked against pure-math ground truth (not just against
the codebase's own machinery) using the standard theory of finite fields
/ LFSR periods (Golomb, "Shift Register Sequences"; Lidl & Niederreiter,
"Finite Fields"): for a degree-d polynomial over GF(q), the theoretical
maximum period is q^d - 1, achieved iff the polynomial is primitive
(irreducible with order exactly q^d - 1). t^4+t^3+1 over GF(2) is a
standard/textbook primitive polynomial (LFSR taps [1,0,0,1] elsewhere in
this project's test suite), independently confirmed irreducible with
order 15 = 2^4 - 1 via SageMath's own is_irreducible()/factor().
"""

import pytest

# Import SageMath - will be skipped if not available via conftest
try:
    from sage.all import *  # noqa: F401,F403
except ImportError:
    pytest.skip("SageMath not available", allow_module_level=True)

from lfsr.polynomial import polynomial_order as reference_polynomial_order
from lfsr.theoretical import (
    IrreduciblePolynomialAnalysis,
    _polynomial_order_helper,
    analyze_irreducible_properties,
    compare_with_theoretical_bounds,
)


@pytest.fixture
def gf2_ring():
    F = GF(2)
    return PolynomialRing(F, "t")


@pytest.fixture
def primitive_poly(gf2_ring):
    # t^4 + t^3 + 1: standard primitive polynomial for coefficients
    # [1,0,0,1] used elsewhere in this test suite. degree 4, order 15.
    return gf2_ring("t^4 + t^3 + 1")


@pytest.fixture
def composite_poly(gf2_ring):
    # t^4 + t^3 + t + 1 = (t+1)^2 * (t^2+t+1) over GF(2) -- reducible,
    # from export_latex/polynomial_to_latex docstring's own example.
    return gf2_ring("t^4 + t^3 + t + 1")


@pytest.fixture
def irreducible_nonprimitive_poly(gf2_ring):
    # Need an irreducible-but-not-primitive polynomial to exercise that
    # branch distinction. Over GF(2), degree 4, the irreducible
    # polynomials are t^4+t+1, t^4+t^3+1 (both primitive, order 15) and
    # t^4+t^3+t^2+t+1 (order 5, NOT primitive since 5 != 15).
    return gf2_ring("t^4 + t^3 + t^2 + t + 1")


# ---------------------------------------------------------------------------
# _polynomial_order_helper -- NOT affected by the NameError bugs; real
# behavioral tests, cross-checked against lfsr.polynomial.polynomial_order.
# ---------------------------------------------------------------------------


class TestPolynomialOrderHelper:
    def test_primitive_polynomial_order_matches_q_pow_d_minus_1(self, primitive_poly):
        order = _polynomial_order_helper(primitive_poly, 4, 2)
        assert order == 15
        assert order == reference_polynomial_order(primitive_poly, 4, 2)

    def test_irreducible_nonprimitive_order(self, irreducible_nonprimitive_poly):
        order = _polynomial_order_helper(irreducible_nonprimitive_poly, 4, 2)
        assert order == 5
        assert order == reference_polynomial_order(irreducible_nonprimitive_poly, 4, 2)

    def test_trivial_degree_one_polynomial_order_is_one(self, gf2_ring):
        p = gf2_ring("t + 1")
        assert _polynomial_order_helper(p, 1, 2) == 1

    def test_order_of_irreducible_quadratic_over_gf2(self, gf2_ring):
        # t^2 + t + 1 is the unique irreducible quadratic over GF(2);
        # its order must be q^2 - 1 = 3 (it's automatically primitive:
        # only one irreducible quadratic exists, and primitive quadratics
        # must exist, so it has to be this one). Cross-checked against
        # reference implementation too.
        p = gf2_ring("t^2 + t + 1")
        assert _polynomial_order_helper(p, 2, 2) == 3
        assert p.is_irreducible()
        assert reference_polynomial_order(p, 2, 2) == 3

    def test_t_divisible_polynomial_order_is_infinite(self, gf2_ring):
        """t (the bare generator) has zero constant term, so t^j mod t
        is always 0, never 1 -- no finite j in range satisfies r == 1.
        Covers both the `elif j == state_vector_space_size - 1: return
        oo` early-return (line ~321) and the final fallback `return oo`
        (line ~323) after the loop exhausts, for two different degrees
        (state_vector_dim=1 hits the elif on the loop's only iteration;
        degree=2 needs the loop to run to completion first)."""
        t = gf2_ring.gen()
        assert _polynomial_order_helper(t, 1, 2) == oo
        assert _polynomial_order_helper(t, 2, 2) == oo
        # NOTE: deliberately NOT cross-checking against
        # lfsr.polynomial.polynomial_order(t, 1, 2) here (unlike the
        # other tests in this class): degree=1 with state_vector_dim=1
        # takes that function's "fast path" (degree ==
        # state_vector_dim), which calls is_primitive_polynomial ->
        # polynomial_order again on the SAME object, and t's
        # is_primitive() apparently never resolves in a way that
        # terminates this mutual recursion -- observed to raise
        # RecursionError (maximum recursion depth exceeded) rather than
        # returning oo or crashing cleanly. This looks like a separate,
        # pre-existing edge case in lfsr.polynomial's fast-path/
        # mutual-recursion design (degree-1 t-divisible polynomials
        # specifically), outside this test file's scope (theoretical.py's
        # own _polynomial_order_helper has no such recursion and is
        # unaffected, as asserted above). Left as an observation, not
        # investigated further here since it doesn't affect this
        # module's own correctness.

    def test_empty_search_range_hits_final_fallback_return(self, gf2_ring):
        """Covers the final `return oo` after the loop (line ~323), as
        opposed to the `elif j == state_vector_space_size - 1: return oo`
        early-return inside the loop body (already covered by
        test_t_divisible_polynomial_order_is_infinite above). These are
        genuinely different lines: the elif only fires while the loop is
        running, so it can never cover the line that executes after the
        loop finishes normally. That line is only reached when
        `range(bi, ei)` is empty, i.e. bi >= ei -- here, a degree-3
        polynomial (bi=3) against state_vector_dim=1 with gf_order=2
        (ei = 2**1 = 2), so the loop body never executes at all."""
        p = gf2_ring("t^3 + t + 1")
        assert p.degree() == 3
        assert _polynomial_order_helper(p, 1, 2) == oo


# ---------------------------------------------------------------------------
# analyze_irreducible_properties -- real behavioral tests, cross-checked
# against SageMath's own is_irreducible()/factor() and against
# reference_polynomial_order.
# ---------------------------------------------------------------------------


class TestAnalyzeIrreducibleProperties:
    def test_primitive_polynomial(self, primitive_poly):
        result = analyze_irreducible_properties(primitive_poly, 2)
        assert result.is_irreducible is True
        assert result.polynomial_order == 15
        assert result.has_primitive_factors is True
        assert result.primitive_factors == [primitive_poly]
        assert result.factors == [(primitive_poly, 1)]
        assert result.factor_orders == [15]
        assert result.degree_distribution == {4: 1}
        assert result.theoretical_period == 15
        assert result.polynomial_degree == 4

    def test_irreducible_nonprimitive_polynomial(self, irreducible_nonprimitive_poly):
        result = analyze_irreducible_properties(irreducible_nonprimitive_poly, 2)
        assert result.is_irreducible is True
        assert result.polynomial_order == 5
        assert result.has_primitive_factors is False
        assert result.primitive_factors == []
        assert result.factor_orders == [5]

    def test_composite_polynomial(self, composite_poly):
        # t^4+t^3+t+1 = (t+1)^2 * (t^2+t+1) over GF(2); factor orders 1
        # (for t+1) and 3 (for the primitive quadratic t^2+t+1).
        result = analyze_irreducible_properties(composite_poly, 2)
        assert result.is_irreducible is False
        assert result.factor_orders == [1, 3]
        assert result.lcm_of_orders == 3
        assert result.has_primitive_factors is True
        assert result.degree_distribution == {1: 2, 2: 1}
        assert result.theoretical_period == 15  # q^d - 1 = 2^4 - 1

    def test_composite_polynomial_with_t_factor_has_infinite_order(self, gf2_ring):
        """t^3 + t^2 + t = t * (t^2+t+1) over GF(2): the `t` factor has
        no finite multiplicative order (it's divisible by t), so
        factor_order == oo for that factor. Covers the `else:
        factor_orders_list.append(None)` branch (line ~165) in the
        composite-polynomial loop, distinct from the finite-order
        `factor_orders_list.append(int(...))` branch already exercised
        by test_composite_polynomial above."""
        poly = gf2_ring("t^3 + t^2 + t")
        result = analyze_irreducible_properties(poly, 2)
        assert result.is_irreducible is False
        # factor order for `t` is None (infinite); for t^2+t+1 it's 3.
        assert None in result.factor_orders
        assert 3 in result.factor_orders
        # lcm_of_orders is computed only from the finite (non-None)
        # orders, so it must be 3, not affected by the infinite one.
        assert result.lcm_of_orders == 3

    def test_composite_polynomial_all_infinite_orders_gives_none_lcm(self, gf2_ring):
        """t^2 (= t * t) over GF(2) factors entirely into copies of `t`,
        every one of which has infinite order -- so valid_orders is
        empty and lcm_of_orders must be None (line ~187), the branch
        test_composite_polynomial_with_t_factor_has_infinite_order above
        can't reach since it always has one finite-order factor too."""
        poly = gf2_ring("t^2")
        result = analyze_irreducible_properties(poly, 2)
        assert result.is_irreducible is False
        assert all(o is None for o in result.factor_orders)
        assert result.lcm_of_orders is None

    def test_dataclass_itself_is_constructible_independent_of_the_bug(self):
        """The IrreduciblePolynomialAnalysis dataclass itself is fine --
        only the analyzer function that's supposed to populate it is
        broken. Verifies the dataclass's field defaults directly."""
        analysis = IrreduciblePolynomialAnalysis(polynomial=None, is_irreducible=True)
        assert analysis.factors == []
        assert analysis.factor_orders == []
        assert analysis.polynomial_order is None
        assert analysis.has_primitive_factors is False
        assert analysis.field_order == 2
        assert analysis.polynomial_degree == 0


# ---------------------------------------------------------------------------
# compare_with_theoretical_bounds -- pure Python, unaffected by the
# NameError bugs; real behavioral tests against hand-computed values.
# ---------------------------------------------------------------------------


class TestCompareWithTheoreticalBounds:
    def test_primitive_polynomial_period_matches_max_is_verified(self):
        result = compare_with_theoretical_bounds(
            computed_period=15, theoretical_max_period=15, is_primitive=True
        )
        assert result["period_equals_max"] is True
        assert result["period_ratio"] == 1.0
        assert result["verification_status"] == "verified"
        assert "matches theoretical maximum" in result["verification_message"]

    def test_primitive_polynomial_period_mismatch_is_flagged(self):
        result = compare_with_theoretical_bounds(
            computed_period=7, theoretical_max_period=15, is_primitive=True
        )
        assert result["period_equals_max"] is False
        assert result["period_ratio"] == pytest.approx(7 / 15)
        assert result["verification_status"] == "mismatch"
        assert "does not match" in result["verification_message"]

    def test_nonprimitive_with_known_polynomial_order_matching_is_verified(self):
        result = compare_with_theoretical_bounds(
            computed_period=5,
            theoretical_max_period=15,
            is_primitive=False,
            polynomial_order=5,
        )
        assert result["verification_status"] == "verified"
        assert "matches polynomial order" in result["verification_message"]

    def test_nonprimitive_with_known_polynomial_order_mismatch(self):
        result = compare_with_theoretical_bounds(
            computed_period=5,
            theoretical_max_period=15,
            is_primitive=False,
            polynomial_order=3,
        )
        assert result["verification_status"] == "mismatch"
        assert "does not match polynomial order" in result["verification_message"]

    def test_nonprimitive_without_polynomial_order_is_unverified(self):
        result = compare_with_theoretical_bounds(
            computed_period=5, theoretical_max_period=15, is_primitive=False
        )
        assert result["verification_status"] == "unverified"
        assert "Cannot verify" in result["verification_message"]

    def test_zero_theoretical_max_period_avoids_division_by_zero(self):
        """period_ratio computation guards theoretical_max_period > 0;
        degenerate all-zero-coefficient LFSR (theoretical_max_period=0)
        should yield ratio 0.0, not raise ZeroDivisionError."""
        result = compare_with_theoretical_bounds(
            computed_period=0, theoretical_max_period=0, is_primitive=False
        )
        assert result["period_ratio"] == 0.0

    def test_result_echoes_input_fields_verbatim(self):
        result = compare_with_theoretical_bounds(
            computed_period=42, theoretical_max_period=100, is_primitive=False
        )
        assert result["computed_period"] == 42
        assert result["theoretical_max_period"] == 100
        assert result["is_primitive"] is False
