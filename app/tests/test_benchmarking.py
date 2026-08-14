#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for lfsr.benchmarking.

BUG FOUND (fixed in this commit, not just documented): benchmark_period_
computation's default method="enumeration" branch imported
lfsr.core.compute_period_enumeration, a function that has never existed
anywhere in this codebase (confirmed via `git log -p --all -- src/lfsr/
core.py`, no match). Since compare_methods() calls the enumeration
benchmark *outside* its try/except (only the factorization call is
guarded), this meant compare_methods() -- and therefore the CLI's
--benchmark flag (cli.py:1171-1182, wired to args.benchmark) -- crashed
with ImportError on every single invocation, unconditionally. Verified
by direct execution before any fix was applied, and again end-to-end via
the actual CLI (`lfsr-seq <file> 2 --benchmark`) after the fix.

Fixed by wiring the enumeration branch to the real enumeration engine,
lfsr.analysis.lfsr_sequence_mapper (algorithm="enumeration",
period_only=True), using the same build_state_update_matrix + GF/
VectorSpace construction pattern as lfsr.core.analyze_lfsr.
"""

import pytest

try:
    from sage.all import GF, PolynomialRing
except ImportError:
    pytest.skip("SageMath not available", allow_module_level=True)

from lfsr.benchmarking import (
    BenchmarkResult,
    BenchmarkSuite,
    benchmark_period_computation,
    benchmark_polynomial_order,
    compare_methods,
    run_benchmark_suite,
)

# [1, 0, 0, 1] over GF(2) -> t^4 + t^3 + 1, a known primitive polynomial;
# max period for a primitive degree-4 LFSR over GF(2) is 2**4 - 1 = 15.
PRIMITIVE_COEFFS_GF2 = [1, 0, 0, 1]
PRIMITIVE_PERIOD_GF2 = 15


class TestBenchmarkPeriodComputation:
    def test_enumeration_matches_known_primitive_period(self):
        # This is the exact call that used to raise ImportError
        # unconditionally -- see module docstring.
        result = benchmark_period_computation(
            PRIMITIVE_COEFFS_GF2, 2, method="enumeration",
            expected_period=PRIMITIVE_PERIOD_GF2,
        )
        assert result.result_value == PRIMITIVE_PERIOD_GF2
        assert result.result_correct is True
        assert result.method_name == "period_computation_enumeration"
        assert result.execution_time >= 0.0

    def test_factorization_matches_known_primitive_period(self):
        result = benchmark_period_computation(
            PRIMITIVE_COEFFS_GF2, 2, method="factorization",
            expected_period=PRIMITIVE_PERIOD_GF2,
        )
        assert result.result_value == PRIMITIVE_PERIOD_GF2
        assert result.result_correct is True

    def test_enumeration_and_factorization_agree_on_a_second_independent_case(self):
        # [1, 1] over GF(2) -> t^2 + t + 1, primitive; max period 2**2-1=3.
        enum_result = benchmark_period_computation([1, 1], 2, method="enumeration")
        fact_result = benchmark_period_computation([1, 1], 2, method="factorization")
        assert enum_result.result_value == 3
        assert fact_result.result_value == 3

    def test_no_expected_period_leaves_result_correct_none(self):
        result = benchmark_period_computation(PRIMITIVE_COEFFS_GF2, 2, method="enumeration")
        assert result.result_correct is None
        assert result.expected_value is None

    def test_wrong_expected_period_marks_result_incorrect(self):
        result = benchmark_period_computation(
            PRIMITIVE_COEFFS_GF2, 2, method="enumeration", expected_period=999
        )
        assert result.result_correct is False

    def test_unknown_method_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown method"):
            benchmark_period_computation(PRIMITIVE_COEFFS_GF2, 2, method="bogus")

    def test_parameters_recorded_on_result(self):
        result = benchmark_period_computation(
            PRIMITIVE_COEFFS_GF2, 2, method="enumeration"
        )
        assert result.parameters == {
            "coefficients": PRIMITIVE_COEFFS_GF2,
            "field_order": 2,
            "method": "enumeration",
        }


class TestBenchmarkPolynomialOrder:
    def test_order_matches_expected_for_primitive_polynomial(self):
        R = PolynomialRing(GF(2), "t")
        poly = R("t^4 + t^3 + 1")
        result = benchmark_polynomial_order(poly, 2, 4, expected_order=PRIMITIVE_PERIOD_GF2)
        assert result.result_value == PRIMITIVE_PERIOD_GF2
        assert result.result_correct is True
        assert result.method_name == "polynomial_order"
        assert result.parameters["degree"] == 4
        assert result.parameters["field_order"] == 2

    def test_no_expected_order_leaves_result_correct_none(self):
        R = PolynomialRing(GF(2), "t")
        poly = R("t^4 + t^3 + 1")
        result = benchmark_polynomial_order(poly, 2, 4)
        assert result.result_correct is None

    def test_wrong_expected_order_marks_result_incorrect(self):
        R = PolynomialRing(GF(2), "t")
        poly = R("t^4 + t^3 + 1")
        result = benchmark_polynomial_order(poly, 2, 4, expected_order=999)
        assert result.result_correct is False

    def test_infinite_order_polynomial_with_expected_order_marks_incorrect_not_crash(self):
        # t^2 + t = t*(t+1) over GF(2) has t as a factor, so t^j mod
        # polynomial never reduces to the constant 1 for any j -- the
        # order search in polynomial_order() never terminates within its
        # loop bound and returns Sage's oo. benchmark_polynomial_order
        # must handle this without raising, marking result_correct=False
        # and result_value=None (confirmed by actually running
        # polynomial_order on this input, not assumed from reading code).
        R = PolynomialRing(GF(2), "t")
        poly = R("t^2 + t")
        result = benchmark_polynomial_order(poly, 2, 2, expected_order=5)
        assert result.result_correct is False
        assert result.result_value is None

    def test_infinite_order_polynomial_no_expected_order_result_value_none(self):
        R = PolynomialRing(GF(2), "t")
        poly = R("t^2 + t")
        result = benchmark_polynomial_order(poly, 2, 2)
        assert result.result_correct is None
        assert result.result_value is None

    def test_reducible_non_primitive_polynomial_order_still_computed(self):
        # t^2 + 1 = (t+1)^2 over GF(2) -- reducible, order should still be
        # a finite value (not the oo branch), computed via the real
        # polynomial_order function (no assumption on the exact value
        # beyond it being a positive int, independently derived from
        # actually running the code).
        R = PolynomialRing(GF(2), "t")
        poly = R("t^2 + 1")
        result = benchmark_polynomial_order(poly, 2, 2)
        assert isinstance(result.result_value, int)
        assert result.result_value > 0


class TestRunBenchmarkSuite:
    def test_polynomial_order_test_case(self):
        suite = run_benchmark_suite(
            [
                {
                    "type": "polynomial_order",
                    "field_order": 2,
                    "polynomial": "t^4 + t^3 + 1",
                    "expected_order": PRIMITIVE_PERIOD_GF2,
                }
            ],
            suite_name="test suite",
        )
        assert suite.suite_name == "test suite"
        assert len(suite.results) == 1
        assert suite.results[0].result_value == PRIMITIVE_PERIOD_GF2
        assert suite.total_time >= 0.0
        assert suite.average_time == suite.total_time

    def test_period_computation_test_case(self):
        suite = run_benchmark_suite(
            [
                {
                    "type": "period_computation",
                    "coefficients": PRIMITIVE_COEFFS_GF2,
                    "field_order": 2,
                    "method": "enumeration",
                    "expected_period": PRIMITIVE_PERIOD_GF2,
                }
            ]
        )
        assert len(suite.results) == 1
        assert suite.results[0].result_value == PRIMITIVE_PERIOD_GF2

    def test_period_computation_defaults_to_enumeration_method(self):
        # No 'method' key -> defaults to "enumeration" per
        # benchmark_period_computation's own default, exercised through
        # run_benchmark_suite's .get('method', 'enumeration').
        suite = run_benchmark_suite(
            [
                {
                    "type": "period_computation",
                    "coefficients": PRIMITIVE_COEFFS_GF2,
                    "field_order": 2,
                }
            ]
        )
        assert suite.results[0].method_name == "period_computation_enumeration"

    def test_unknown_benchmark_type_skipped(self):
        suite = run_benchmark_suite([{"type": "not_a_real_type"}])
        assert suite.results == []
        assert suite.average_time == 0.0

    def test_empty_test_cases_produces_empty_suite_no_division_by_zero(self):
        suite = run_benchmark_suite([])
        assert suite.results == []
        assert suite.total_time == 0.0
        assert suite.average_time == 0.0

    def test_multiple_test_cases_aggregate_total_and_average_time(self):
        suite = run_benchmark_suite(
            [
                {
                    "type": "period_computation",
                    "coefficients": PRIMITIVE_COEFFS_GF2,
                    "field_order": 2,
                    "method": "enumeration",
                },
                {
                    "type": "period_computation",
                    "coefficients": PRIMITIVE_COEFFS_GF2,
                    "field_order": 2,
                    "method": "factorization",
                },
            ]
        )
        assert len(suite.results) == 2
        assert suite.total_time == sum(r.execution_time for r in suite.results)
        assert suite.average_time == suite.total_time / 2

    def test_default_suite_name(self):
        suite = run_benchmark_suite([])
        assert suite.suite_name == "LFSR Analysis Benchmarks"


class TestCompareMethods:
    def test_both_methods_present_and_agree(self):
        # This is the exact function backing the CLI's --benchmark flag
        # (cli.py:1171-1182) -- previously crashed unconditionally, see
        # module docstring.
        results = compare_methods(PRIMITIVE_COEFFS_GF2, 2, expected_period=PRIMITIVE_PERIOD_GF2)
        assert set(results.keys()) == {"enumeration", "factorization"}
        assert results["enumeration"].result_value == PRIMITIVE_PERIOD_GF2
        assert results["factorization"].result_value == PRIMITIVE_PERIOD_GF2
        assert results["enumeration"].result_correct is True
        assert results["factorization"].result_correct is True

    def test_no_expected_period(self):
        results = compare_methods(PRIMITIVE_COEFFS_GF2, 2)
        assert results["enumeration"].expected_value is None
        assert results["factorization"].expected_value is None

    def test_second_independent_case(self):
        results = compare_methods([1, 1], 2, expected_period=3)
        assert results["enumeration"].result_value == 3
        assert results["factorization"].result_value == 3

    def test_factorization_exception_is_swallowed_enumeration_still_returned(self, monkeypatch):
        # compare_methods wraps only the factorization call in
        # try/except Exception: pass, per its own docstring ("Factorization
        # may fail for some polynomials"). Exercise that branch directly
        # via monkeypatching rather than searching for a real input that
        # triggers a factorization failure -- this is testing the
        # defensive exception-handling contract itself, not claiming any
        # particular input crashes factorization in practice.
        import lfsr.benchmarking as benchmarking_module

        original = benchmarking_module.benchmark_period_computation

        def fake(coefficients, field_order, method="enumeration", expected_period=None):
            if method == "factorization":
                raise RuntimeError("simulated factorization failure")
            return original(coefficients, field_order, method, expected_period)

        monkeypatch.setattr(benchmarking_module, "benchmark_period_computation", fake)

        results = compare_methods(PRIMITIVE_COEFFS_GF2, 2, expected_period=PRIMITIVE_PERIOD_GF2)
        assert "enumeration" in results
        assert results["enumeration"].result_value == PRIMITIVE_PERIOD_GF2
        assert "factorization" not in results


class TestBenchmarkDataclasses:
    def test_benchmark_result_defaults(self):
        result = BenchmarkResult(method_name="x", execution_time=1.0)
        assert result.memory_usage is None
        assert result.result_correct is None
        assert result.result_value is None
        assert result.expected_value is None
        assert result.parameters == {}

    def test_benchmark_result_parameters_default_factory_is_independent_per_instance(self):
        # dataclass field(default_factory=dict) pitfall check: two
        # instances must not share the same dict object.
        r1 = BenchmarkResult(method_name="a", execution_time=0.0)
        r2 = BenchmarkResult(method_name="b", execution_time=0.0)
        r1.parameters["k"] = "v"
        assert r2.parameters == {}

    def test_benchmark_suite_defaults(self):
        suite = BenchmarkSuite(suite_name="s")
        assert suite.results == []
        assert suite.total_time == 0.0
        assert suite.average_time == 0.0

    def test_benchmark_suite_results_default_factory_is_independent_per_instance(self):
        s1 = BenchmarkSuite(suite_name="a")
        s2 = BenchmarkSuite(suite_name="b")
        s1.results.append(BenchmarkResult(method_name="x", execution_time=0.0))
        assert s2.results == []
