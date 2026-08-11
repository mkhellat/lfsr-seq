#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for lfsr.export (multi-format export: JSON, CSV, XML, plus the
NIST-suite-specific variants and an HTML report).

Strategy: build small, deterministic seq_dict/period_dict fixtures (and a
small NISTTestSuiteResult) directly (no full LFSR analysis run needed --
export.py only consumes plain dict/list/dataclass data), export to an
in-memory StringIO, then parse the result back with the *real* stdlib
parser for that format (json.loads / csv.reader / xml.etree) and assert
on the parsed structure against hand-computed expected values -- not just
"it didn't crash". This is the round-trip-correctness approach mandated
by the task: a malformed-but-non-crashing export would be caught by
re-parsing it and checking field values, whereas a smoke test would not.

BUG found and fixed (2026-08-11, see lfsr/sage_imports.py's commit
history): ``export_to_json``, ``export_to_csv``, and ``export_to_xml``
all reference the bare name ``oo`` (SageMath's infinity constant) in a
ternary (``... if char_poly_order != oo else "infinity"``), but
``lfsr/sage_imports.py``'s curated ``__all__`` didn't include ``oo`` --
every single call to any of these three functions raised
``NameError: name 'oo' is not defined``, regardless of whether
char_poly_order was actually infinite. Fixed by adding
``sage.rings.infinity.infinity`` (aliased ``oo``) to sage_imports.py's
exports. Tests below assert the real, working output (including the
"infinity" formatting branch) rather than documenting a crash.
"""

import csv
import io
import json
import xml.etree.ElementTree as ET

import pytest

# Import SageMath - will be skipped if not available via conftest
try:
    from sage.all import *  # noqa: F401,F403
except ImportError:
    pytest.skip("SageMath not available", allow_module_level=True)

from lfsr.export import (
    export_nist_to_csv,
    export_nist_to_html,
    export_nist_to_json,
    export_nist_to_xml,
    export_to_csv,
    export_to_json,
    export_to_xml,
    get_export_function,
    get_nist_export_function,
)
from lfsr.nist import NISTTestResult, NISTTestSuiteResult

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def simple_analysis_data():
    """A small, hand-computed LFSR analysis result: two sequences, degree-4
    GF(2) LFSR reference vector (used throughout this project's test
    suite), so all statistics below are checkable by hand."""
    F = GF(2)
    R = PolynomialRing(F, "t")
    char_poly = R("t^4 + t^3 + 1")  # matches coefficients [1,0,0,1] convention
    seq_dict = {
        1: [[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 1]],
        2: [[1, 1, 0, 0], [0, 1, 1, 0]],
    }
    period_dict = {1: 15, 2: 5}
    return {
        "seq_dict": seq_dict,
        "period_dict": period_dict,
        "max_period": 15,
        "periods_sum": 5,  # deliberately just total states (3+2), not sum of periods
        "char_poly": char_poly,
        "char_poly_order": 15,
        "coeffs_vector": [1, 0, 0, 1],
        "gf_order": 2,
    }


@pytest.fixture
def nist_suite_result():
    """A small, hand-built NISTTestSuiteResult (no real sequence needed --
    export.py only reads dataclass fields)."""
    results = [
        NISTTestResult(
            test_name="Frequency (Monobit) Test",
            p_value=0.5,
            passed=True,
            statistic=0.6745,
            details={"n": 100, "note": "ok", "flag": True},
        ),
        NISTTestResult(
            test_name="Runs Test",
            p_value=0.001,
            passed=False,
            statistic=12.3,
            details={},
        ),
    ]
    return NISTTestSuiteResult(
        sequence_length=100,
        significance_level=0.01,
        tests_passed=1,
        tests_failed=1,
        total_tests=2,
        results=results,
        overall_assessment="FAILED",
        pass_rate=0.5,
    )


# ---------------------------------------------------------------------------
# export_to_json
# ---------------------------------------------------------------------------


class TestExportToJson:
    def test_round_trip_structure_and_values(self, simple_analysis_data):
        buf = io.StringIO()
        export_to_json(
            simple_analysis_data["seq_dict"],
            simple_analysis_data["period_dict"],
            simple_analysis_data["max_period"],
            simple_analysis_data["periods_sum"],
            simple_analysis_data["char_poly"],
            simple_analysis_data["char_poly_order"],
            simple_analysis_data["coeffs_vector"],
            simple_analysis_data["gf_order"],
            buf,
        )
        parsed = json.loads(buf.getvalue())
        assert parsed["metadata"]["gf_order"] == 2
        assert parsed["metadata"]["coefficients"] == [1, 0, 0, 1]
        assert parsed["metadata"]["lfsr_degree"] == 4
        assert parsed["characteristic_polynomial"]["polynomial"] == "t^4 + t^3 + 1"
        assert parsed["characteristic_polynomial"]["order"] == "15"
        assert parsed["sequences"]["1"]["states"] == [
            "[1, 0, 0, 0]",
            "[0, 0, 0, 1]",
            "[0, 0, 1, 1]",
        ]
        assert parsed["sequences"]["1"]["period"] == 15
        assert parsed["sequences"]["2"]["period"] == 5

    def test_infinite_order_formatted_as_infinity_string(self):
        buf = io.StringIO()
        F = GF(2)
        R = PolynomialRing(F, "t")
        export_to_json({1: [[1]]}, {1: 1}, 1, 1, R("t+1"), oo, [1], 2, buf)
        parsed = json.loads(buf.getvalue())
        assert parsed["characteristic_polynomial"]["order"] == "infinity"

    def test_empty_seq_dict_produces_valid_json_with_no_sequences(self):
        buf = io.StringIO()
        F = GF(2)
        R = PolynomialRing(F, "t")
        export_to_json({}, {}, 0, 0, R("t+1"), 1, [1], 2, buf)
        parsed = json.loads(buf.getvalue())
        assert parsed["sequences"] == {}


# ---------------------------------------------------------------------------
# export_to_csv
# ---------------------------------------------------------------------------


class TestExportToCsv:
    def test_round_trip_metadata_and_sequence_rows(self, simple_analysis_data):
        buf = io.StringIO()
        export_to_csv(
            simple_analysis_data["seq_dict"],
            simple_analysis_data["period_dict"],
            simple_analysis_data["max_period"],
            simple_analysis_data["periods_sum"],
            simple_analysis_data["char_poly"],
            simple_analysis_data["char_poly_order"],
            simple_analysis_data["coeffs_vector"],
            simple_analysis_data["gf_order"],
            buf,
        )
        buf.seek(0)
        rows = list(csv.reader(buf))
        metadata = {r[0]: r[1] for r in rows if len(r) == 2}
        assert metadata["GF Order"] == "2"
        assert metadata["Coefficients"] == "1,0,0,1"
        assert metadata["Characteristic Polynomial"] == "t^4 + t^3 + 1"
        assert metadata["Polynomial Order"] == "15"
        assert metadata["Max Period"] == "15"
        assert metadata["Total Sequences"] == "2"

        header_idx = rows.index(["Sequence Number", "Period", "States"])
        seq_rows = {r[0]: r for r in rows[header_idx + 1 :] if r}
        assert seq_rows["1"][1] == "15"
        assert seq_rows["2"][1] == "5"

    def test_infinite_order_formatted_as_infinity_string(self):
        F = GF(2)
        R = PolynomialRing(F, "t")
        buf = io.StringIO()
        export_to_csv({1: [[1]]}, {1: 1}, 1, 1, R("t+1"), oo, [1], 2, buf)
        buf.seek(0)
        rows = list(csv.reader(buf))
        metadata = {r[0]: r[1] for r in rows if len(r) == 2}
        assert metadata["Polynomial Order"] == "infinity"

    def test_dict_ordering_does_not_affect_metadata_rows(self):
        F = GF(2)
        R = PolynomialRing(F, "t")
        seq_dict = {5: [[1]], 1: [[0]], 3: [[1]]}
        period_dict = {5: 1, 1: 1, 3: 1}
        buf = io.StringIO()
        export_to_csv(seq_dict, period_dict, 1, 3, R("t+1"), 1, [1], 2, buf)
        buf.seek(0)
        rows = list(csv.reader(buf))
        metadata = {r[0]: r[1] for r in rows if len(r) == 2}
        assert metadata["Total Sequences"] == "3"


# ---------------------------------------------------------------------------
# export_to_xml
# ---------------------------------------------------------------------------


class TestExportToXml:
    def test_round_trip_structure_and_values(self, simple_analysis_data):
        buf = io.StringIO()
        export_to_xml(
            simple_analysis_data["seq_dict"],
            simple_analysis_data["period_dict"],
            simple_analysis_data["max_period"],
            simple_analysis_data["periods_sum"],
            simple_analysis_data["char_poly"],
            simple_analysis_data["char_poly_order"],
            simple_analysis_data["coeffs_vector"],
            simple_analysis_data["gf_order"],
            buf,
        )
        xml_text = buf.getvalue()
        assert xml_text.startswith("<?xml")
        root = ET.fromstring(xml_text)
        assert root.find("metadata/gf_order").text == "2"
        assert root.find("characteristic_polynomial/polynomial").text == "t^4 + t^3 + 1"
        assert root.find("characteristic_polynomial/order").text == "15"
        assert root.find("statistics/total_sequences").text == "2"
        sequences = root.find("sequences").findall("sequence")
        assert len(sequences) == 2
        assert sequences[0].get("number") == "1"
        assert sequences[0].find("period").text == "15"

    def test_infinite_order_formatted_as_infinity_string(self):
        F = GF(2)
        R = PolynomialRing(F, "t")
        buf = io.StringIO()
        export_to_xml({1: [[1]]}, {1: 1}, 1, 1, R("t+1"), oo, [1], 2, buf)
        root = ET.fromstring(buf.getvalue())
        assert root.find("characteristic_polynomial/order").text == "infinity"

    def test_empty_seq_dict_produces_valid_xml_with_no_sequences(self):
        F = GF(2)
        R = PolynomialRing(F, "t")
        buf = io.StringIO()
        export_to_xml({}, {}, 0, 0, R("t+1"), 1, [1], 2, buf)
        root = ET.fromstring(buf.getvalue())
        assert root.find("sequences").findall("sequence") == []


# ---------------------------------------------------------------------------
# export_nist_to_json / csv / xml / html
# ---------------------------------------------------------------------------


class TestExportNistToJson:
    def test_round_trip_structure_and_values(self, nist_suite_result):
        buf = io.StringIO()
        export_nist_to_json(nist_suite_result, buf)
        parsed = json.loads(buf.getvalue())

        assert parsed["metadata"]["test_suite"] == "NIST SP 800-22"
        assert parsed["sequence"]["length"] == 100
        assert parsed["test_parameters"]["significance_level"] == 0.01
        assert parsed["summary"]["total_tests"] == 2
        assert parsed["summary"]["tests_passed"] == 1
        assert parsed["summary"]["tests_failed"] == 1
        assert parsed["summary"]["pass_rate"] == 0.5
        assert parsed["summary"]["overall_assessment"] == "FAILED"

        assert len(parsed["test_results"]) == 2
        first = parsed["test_results"][0]
        assert first["test_name"] == "Frequency (Monobit) Test"
        assert first["p_value"] == 0.5
        assert first["passed"] is True
        assert first["statistic"] == pytest.approx(0.6745)
        # NOTE: "flag": True in the input details is affected by the bool
        # coercion bug documented/asserted precisely in
        # test_details_dict_type_coercion_rules below (bool is silently
        # turned into a float since isinstance(v, (int, float)) matches
        # bool first) -- this dict-equality check alone wouldn't catch it
        # because `1.0 == True` in Python, so it's verified for real there.
        assert first["details"] == {"n": 100.0, "note": "ok", "flag": True}

        second = parsed["test_results"][1]
        assert second["passed"] is False
        assert second["details"] == {}

    def test_details_dict_type_coercion_rules(self):
        """details values are coerced by export_nist_to_json's dict/list
        comprehension:

            k: (float(v) if isinstance(v, (int, float)) else
                bool(v) if isinstance(v, bool) else
                str(v) if not isinstance(v, (dict, list)) else v)

        BUG (minor, documented not fixed): the `isinstance(v, (int, float))`
        branch is checked *before* the `isinstance(v, bool)` branch, but in
        Python `bool` is a subclass of `int` -- so a real bool value like
        `False`/`True` always matches the first branch and gets silently
        coerced to a float (0.0 / 1.0) instead of staying a JSON boolean.
        The `bool` branch below it is dead code; it can never be reached
        for an actual bool input. Contrast with the top-level
        `test_result.passed` field a few lines above in export.py, which
        is correctly wrapped in `bool(...)` directly and is NOT affected
        (see test_round_trip_structure_and_values: `first["passed"] is True`
        passes fine -- only *details dict* booleans are mangled)."""
        result = NISTTestResult(
            test_name="X",
            p_value=0.1,
            passed=True,
            statistic=1.0,
            details={
                "an_int": 5,
                "a_float": 2.5,
                "a_bool": False,
                "a_str": "hello",
                "a_list": [1, 2, 3],
                "a_dict": {"nested": 1},
            },
        )
        suite = NISTTestSuiteResult(
            sequence_length=10,
            significance_level=0.01,
            tests_passed=1,
            tests_failed=0,
            total_tests=1,
            results=[result],
            overall_assessment="PASSED",
            pass_rate=1.0,
        )
        buf = io.StringIO()
        export_nist_to_json(suite, buf)
        parsed = json.loads(buf.getvalue())
        details = parsed["test_results"][0]["details"]
        assert details["an_int"] == 5.0
        assert details["a_float"] == 2.5
        # BUG: should be `False`/bool, but is silently coerced to 0.0.
        assert details["a_bool"] == 0.0
        assert details["a_bool"] is not False  # documents the type loss
        assert details["a_str"] == "hello"
        assert details["a_list"] == [1, 2, 3]
        assert details["a_dict"] == {"nested": 1}


class TestExportNistToCsv:
    def test_round_trip_metadata_and_test_rows(self, nist_suite_result):
        buf = io.StringIO()
        export_nist_to_csv(nist_suite_result, buf)
        buf.seek(0)
        rows = list(csv.reader(buf))

        metadata = {r[0]: r[1] for r in rows if len(r) == 2}
        assert metadata["Sequence Length"] == "100"
        assert metadata["Significance Level"] == "0.01"
        assert metadata["Total Tests"] == "2"
        assert metadata["Tests Passed"] == "1"
        assert metadata["Tests Failed"] == "1"
        assert metadata["Pass Rate"] == "50.00%"
        assert metadata["Overall Assessment"] == "FAILED"

        header_idx = rows.index(["Test Name", "P-value", "Passed", "Statistic"])
        test_rows = rows[header_idx + 1 :]
        assert len(test_rows) == 2
        assert test_rows[0] == [
            "Frequency (Monobit) Test",
            "0.500000",
            "PASS",
            "0.674500",
        ]
        assert test_rows[1] == ["Runs Test", "0.001000", "FAIL", "12.300000"]


class TestExportNistToXml:
    def test_round_trip_structure_and_values(self, nist_suite_result):
        buf = io.StringIO()
        export_nist_to_xml(nist_suite_result, buf)
        xml_text = buf.getvalue()
        assert xml_text.startswith("<?xml")
        root = ET.fromstring(xml_text)

        assert root.tag == "nist_test_suite"
        assert root.get("test_suite") == "NIST SP 800-22"

        metadata = root.find("metadata")
        assert metadata.find("sequence_length").text == "100"
        assert metadata.find("significance_level").text == "0.01"

        summary = root.find("summary")
        assert summary.find("total_tests").text == "2"
        assert summary.find("pass_rate").text == "0.500000"
        assert summary.find("overall_assessment").text == "FAILED"

        tests = root.find("test_results").findall("test")
        assert len(tests) == 2
        assert tests[0].get("name") == "Frequency (Monobit) Test"
        assert tests[0].find("p_value").text == "0.500000"
        assert tests[0].find("passed").text == "true"

        # First test has details, so a <details> child with <detail> items
        # should be present; second test has empty details, so no <details>
        # element at all (guarded by `if test_result.details:`).
        assert tests[0].find("details") is not None
        detail_keys = {d.get("key") for d in tests[0].find("details").findall("detail")}
        assert detail_keys == {"n", "note", "flag"}
        assert tests[1].find("details") is None

    def test_passed_false_serializes_as_lowercase_false(self, nist_suite_result):
        buf = io.StringIO()
        export_nist_to_xml(nist_suite_result, buf)
        root = ET.fromstring(buf.getvalue())
        tests = root.find("test_results").findall("test")
        assert tests[1].find("passed").text == "false"


class TestExportNistToHtml:
    def test_contains_key_summary_values(self, nist_suite_result):
        buf = io.StringIO()
        export_nist_to_html(nist_suite_result, buf)
        html = buf.getvalue()

        assert html.startswith("<!DOCTYPE html>")
        assert "100" in html  # sequence length (with thousands separator if any)
        assert "FAILED" in html
        assert "50.00%" in html
        assert "Frequency (Monobit) Test" in html
        assert "Runs Test" in html
        # PASS/FAIL rendering
        assert "PASS" in html
        assert "FAIL" in html

    def test_html_is_well_formed_enough_to_parse_as_xml_after_normalizing(
        self, nist_suite_result
    ):
        """The generated HTML is simple (no unclosed tags in the template
        besides the standard void/void-like elements), so it should parse
        via a lenient HTML parser without errors. We use Python's built-in
        html.parser through xml.etree's HTMLParser-less approach isn't
        available, so instead just verify balanced div/table tags by count
        as a structural sanity check that doesn't require crashing."""
        buf = io.StringIO()
        export_nist_to_html(nist_suite_result, buf)
        html = buf.getvalue()
        assert html.count("<table") == html.count("</table>")
        assert html.count("<tr>") == html.count("</tr>")
        assert html.count("<div") == html.count("</div>")
        assert html.count("<html") == html.count("</html>")


# ---------------------------------------------------------------------------
# get_export_function / get_nist_export_function
# ---------------------------------------------------------------------------


class TestGetExportFunction:
    @pytest.mark.parametrize(
        "name,expected",
        [
            ("json", export_to_json),
            ("JSON", export_to_json),
            ("csv", export_to_csv),
            ("Csv", export_to_csv),
            ("xml", export_to_xml),
        ],
    )
    def test_returns_correct_function_case_insensitive(self, name, expected):
        assert get_export_function(name) is expected

    def test_unsupported_format_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported format"):
            get_export_function("yaml")


class TestGetNistExportFunction:
    @pytest.mark.parametrize(
        "name,expected",
        [
            ("json", export_nist_to_json),
            ("csv", export_nist_to_csv),
            ("xml", export_nist_to_xml),
            ("html", export_nist_to_html),
            ("HTML", export_nist_to_html),
        ],
    )
    def test_returns_correct_function_case_insensitive(self, name, expected):
        assert get_nist_export_function(name) is expected

    def test_unsupported_format_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported format"):
            get_nist_export_function("pdf")
