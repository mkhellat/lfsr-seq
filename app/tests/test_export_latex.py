#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for lfsr.export_latex (LaTeX export of polynomial analysis,
period distributions, and complete-document generation).

Strategy: build small, hand-computed inputs directly, call the export
functions, and check the *exact* generated LaTeX strings/lines against
hand-computed expected content (not just "it didn't crash" and not just
"contains some substring") wherever the function's own logic is simple
enough to predict exactly (e.g. table row counts, specific numeric
values, escaping). For genuinely SageMath-generated content (e.g. what
``latex()`` itself renders for a polynomial) we can't independently
verify without a bug -- see below.

BUG found and fixed (2026-08-11, see lfsr/sage_imports.py's commit
history): ``polynomial_to_latex`` (export_latex.py line 17) calls the
bare name ``latex(polynomial)`` to get SageMath's LaTeX rendering of a
polynomial, but ``lfsr/sage_imports.py``'s curated ``__all__`` didn't
include ``latex`` -- every call raised ``NameError`` (the
``except (AttributeError, TypeError)`` fallback couldn't catch it,
since ``NameError`` isn't in that tuple). This affected
``polynomial_to_latex`` itself, ``export_polynomial_analysis_to_latex``,
and transitively ``export_complete_analysis_to_latex``/
``export_to_latex_file`` whenever ``analysis_results`` contains a
``'polynomial'`` key. Fixed by adding ``sage.misc.latex.latex`` to
sage_imports.py's exports. Tests below assert the real, working LaTeX
output. ``export_period_distribution_to_latex`` never called
``polynomial_to_latex`` and was never affected.
"""

import io
import os

import pytest

# Import SageMath - will be skipped if not available via conftest
try:
    from sage.all import *  # noqa: F401,F403
except ImportError:
    pytest.skip("SageMath not available", allow_module_level=True)

from lfsr.export_latex import (
    export_complete_analysis_to_latex,
    export_period_distribution_to_latex,
    export_polynomial_analysis_to_latex,
    export_to_latex_file,
    polynomial_to_latex,
)


@pytest.fixture
def sample_polynomial():
    F = GF(2)
    R = PolynomialRing(F, "t")
    return R("t^4 + t^3 + 1")


# ---------------------------------------------------------------------------
# polynomial_to_latex
# ---------------------------------------------------------------------------


class TestPolynomialToLatex:
    def test_default_variable_renders_sage_latex(self, sample_polynomial):
        assert polynomial_to_latex(sample_polynomial) == "t^{4} + t^{3} + 1"

    def test_custom_variable_name_substituted(self, sample_polynomial):
        assert polynomial_to_latex(sample_polynomial, variable="x") == "x^{4} + x^{3} + 1"

    def test_latex_conversion_failure_falls_back_to_str(self):
        """Regression coverage for lines 54-56: when SageMath's latex()
        raises (AttributeError or TypeError), polynomial_to_latex must
        fall back to str(polynomial).replace("t", variable) rather than
        propagating. Uses an object whose Sage `_latex_` protocol method
        raises but whose __str__ still works, so the fallback path is
        exercised with a real recoverable failure rather than a total
        crash (a broken __str__ would make both the primary path and the
        fallback raise the same error, which wouldn't isolate this
        branch)."""

        class BrokenLatexProtocol:
            def _latex_(self):
                raise TypeError("broken _latex_ protocol method")

            def __str__(self):
                return "t^4 + t + 1"

        result = polynomial_to_latex(BrokenLatexProtocol(), variable="x")
        assert result == "x^4 + x + 1"


# ---------------------------------------------------------------------------
# export_polynomial_analysis_to_latex
# ---------------------------------------------------------------------------


class TestExportPolynomialAnalysisToLatex:
    def test_table_contains_exact_property_values(self, sample_polynomial):
        result = export_polynomial_analysis_to_latex(
            polynomial=sample_polynomial,
            polynomial_order=15,
            is_primitive=True,
            is_irreducible=True,
            field_order=2,
        )
        assert "Characteristic Polynomial & $t^{4} + t^{3} + 1$" in result
        assert "Field Order & $\\mathbb{F}_{2}$" in result
        assert "Polynomial Order & $15$" in result
        assert "Primitive & Yes" in result
        assert "Irreducible & Yes" in result

    def test_no_factors_and_none_order_render_gracefully(self, sample_polynomial):
        result = export_polynomial_analysis_to_latex(
            polynomial=sample_polynomial,
            polynomial_order=None,
            is_primitive=False,
            is_irreducible=False,
            factors=None,
            field_order=2,
        )
        assert "Primitive & No" in result
        assert "Irreducible & No" in result
        assert "Polynomial Order & $\\infty$" in result

    def test_factorization_table_with_matching_factor_orders(self):
        """Regression coverage for lines 139-157: the factorization block,
        including a multiplicity > 1 factor (rendered with an exponent)
        and a matching factor_orders entry (numeric order_str branch)."""
        R = PolynomialRing(GF(2), "t")
        f1 = R("t + 1")
        f2 = R("t^3 + t + 1")
        result = export_polynomial_analysis_to_latex(
            polynomial=R("t^4 + t + 1"),
            polynomial_order=15,
            is_primitive=True,
            is_irreducible=True,
            factors=[(f1, 1), (f2, 2)],
            factor_orders=[1, 7],
            field_order=2,
        )
        assert "\\multicolumn{2}{|c|}{\\textbf{Factorization}} \\\\" in result
        assert "\\textbf{Factor} & \\textbf{Order} \\\\" in result
        # multiplicity == 1 -> no exponent notation
        assert "$t + 1$ & $1$ \\\\" in result
        # multiplicity > 1 -> wrapped with exponent
        assert "$(t^{3} + t + 1)^{2}$ & $7$ \\\\" in result

    def test_factorization_table_missing_factor_orders_uses_dashes(self):
        """When factor_orders is None (or shorter than factors), the
        order_str falls back to '---' (line 154) instead of indexing."""
        R = PolynomialRing(GF(2), "t")
        f1 = R("t + 1")
        result = export_polynomial_analysis_to_latex(
            polynomial=R("t^4 + t + 1"),
            polynomial_order=15,
            is_primitive=True,
            is_irreducible=True,
            factors=[(f1, 1)],
            factor_orders=None,
            field_order=2,
        )
        assert "$t + 1$ & $---$ \\\\" in result

    def test_factorization_table_factor_order_none_renders_infinity(self):
        """When factor_orders[i] is explicitly None, order_str becomes
        '$\\infty$' (line 152's else-branch of `if order is not None`)."""
        R = PolynomialRing(GF(2), "t")
        f1 = R("t + 1")
        result = export_polynomial_analysis_to_latex(
            polynomial=R("t^4 + t + 1"),
            polynomial_order=15,
            is_primitive=True,
            is_irreducible=True,
            factors=[(f1, 1)],
            factor_orders=[None],
            field_order=2,
        )
        assert "$t + 1$ & $$\\infty$$ \\\\" in result

    def test_empty_factors_list_skips_factorization_block(self, sample_polynomial):
        """factors=[] is falsy, so `if factors and len(factors) > 0`
        (line 138) must skip the whole factorization block, same as
        factors=None."""
        result = export_polynomial_analysis_to_latex(
            polynomial=sample_polynomial,
            polynomial_order=None,
            is_primitive=False,
            is_irreducible=False,
            factors=[],
            field_order=2,
        )
        assert "Factorization" not in result

    def test_output_file_receives_content_plus_newline(self, sample_polynomial):
        """Regression coverage for lines 164-166: output_file.write is
        called with the result plus a trailing newline."""
        buf = io.StringIO()
        result = export_polynomial_analysis_to_latex(
            polynomial=sample_polynomial,
            polynomial_order=15,
            is_primitive=True,
            is_irreducible=True,
            field_order=2,
            output_file=buf,
        )
        assert buf.getvalue() == result + "\n"


# ---------------------------------------------------------------------------
# export_period_distribution_to_latex -- NOT affected by the `latex` bug,
# so this is tested for real exact-content correctness.
# ---------------------------------------------------------------------------


class TestExportPeriodDistributionToLatex:
    def test_theoretical_max_period_defaults_to_q_pow_d_minus_1(self):
        result = export_period_distribution_to_latex(
            period_dict={15: 1, 5: 1, 3: 1, 1: 1},
            field_order=2,
            lfsr_degree=4,
            is_primitive=False,
        )
        # theoretical_max_period defaults to field_order**lfsr_degree - 1 = 15
        assert "Theoretical Maximum & $15$" in result

    def test_explicit_theoretical_max_period_overrides_default(self):
        result = export_period_distribution_to_latex(
            period_dict={15: 1},
            field_order=2,
            lfsr_degree=4,
            is_primitive=True,
            theoretical_max_period=999,
        )
        assert "Theoretical Maximum & $999$" in result

    def test_statistics_exact_values(self):
        period_dict = {15: 3, 5: 2, 1: 1}  # total_sequences = 6
        result = export_period_distribution_to_latex(
            period_dict=period_dict,
            field_order=2,
            lfsr_degree=4,
            is_primitive=True,
        )
        assert "Total Sequences & $6$" in result
        assert "Maximum Period & $15$" in result
        assert "Minimum Period & $1$" in result
        assert "Polynomial Primitive & Yes" in result

    def test_is_primitive_false_renders_no(self):
        result = export_period_distribution_to_latex(
            period_dict={1: 1},
            field_order=2,
            lfsr_degree=1,
            is_primitive=False,
        )
        assert "Polynomial Primitive & No" in result

    def test_period_rows_sorted_descending_and_percentages_exact(self):
        # total = 10, so percentages are exact round numbers
        period_dict = {10: 5, 5: 3, 1: 2}
        result = export_period_distribution_to_latex(
            period_dict=period_dict,
            field_order=2,
            lfsr_degree=4,
            is_primitive=False,
        )
        lines = result.split("\n")
        row_10_idx = next(i for i, l in enumerate(lines) if l.startswith("$10$ & $5$"))
        row_5_idx = next(i for i, l in enumerate(lines) if l.startswith("$5$ & $3$"))
        row_1_idx = next(i for i, l in enumerate(lines) if l.startswith("$1$ & $2$"))
        # descending order: 10 before 5 before 1
        assert row_10_idx < row_5_idx < row_1_idx
        assert "$10$ & $5$ & $50.00\\%$" in result
        assert "$5$ & $3$ & $30.00\\%$" in result
        assert "$1$ & $2$ & $20.00\\%$" in result

    def test_more_than_ten_periods_shows_only_top_ten_plus_note(self):
        # 12 distinct periods -> only top 10 (by value, descending) shown,
        # plus the "(showing top 10 periods)" note.
        period_dict = dict.fromkeys(range(1, 13), 1)  # periods 1..12
        result = export_period_distribution_to_latex(
            period_dict=period_dict,
            field_order=2,
            lfsr_degree=8,
            is_primitive=False,
        )
        assert "(showing top 10 periods)" in result
        # Top 10 descending: 12, 11, ..., 3. periods 1 and 2 excluded.
        for p in range(3, 13):
            assert f"${p}$ & $1$ &" in result
        for p in (1, 2):
            assert f"${p}$ & $1$ &" not in result

    def test_exactly_ten_periods_shows_no_truncation_note(self):
        period_dict = dict.fromkeys(range(1, 11), 1)  # exactly 10 periods
        result = export_period_distribution_to_latex(
            period_dict=period_dict,
            field_order=2,
            lfsr_degree=8,
            is_primitive=False,
        )
        assert "(showing top 10 periods)" not in result

    def test_empty_period_dict_handles_gracefully(self):
        """max()/min() on an empty periods list would normally raise
        ValueError; the code guards this with `if periods else 0`, so an
        empty period_dict should produce 0s, not crash."""
        result = export_period_distribution_to_latex(
            period_dict={},
            field_order=2,
            lfsr_degree=4,
            is_primitive=False,
        )
        assert "Total Sequences & $0$" in result
        assert "Maximum Period & $0$" in result
        assert "Minimum Period & $0$" in result

    def test_output_file_receives_same_content_plus_trailing_newline(self):
        buf = io.StringIO()
        result = export_period_distribution_to_latex(
            period_dict={5: 1},
            field_order=2,
            lfsr_degree=3,
            is_primitive=False,
            output_file=buf,
        )
        assert buf.getvalue() == result + "\n"

    def test_returns_two_well_formed_latex_tables(self):
        result = export_period_distribution_to_latex(
            period_dict={5: 1},
            field_order=2,
            lfsr_degree=3,
            is_primitive=False,
        )
        assert result.count("\\begin{table}") == 2
        assert result.count("\\end{table}") == 2
        assert result.count("\\begin{tabular}") == 2
        assert result.count("\\end{tabular}") == 2


# ---------------------------------------------------------------------------
# export_complete_analysis_to_latex / export_to_latex_file
# ---------------------------------------------------------------------------


class TestExportCompleteAnalysisToLatex:
    def test_polynomial_section_renders_correctly(self, sample_polynomial):
        analysis_results = {
            "polynomial": {
                "polynomial": sample_polynomial,
                "order": 15,
                "is_primitive": True,
                "is_irreducible": True,
                "field_order": 2,
            }
        }
        result = export_complete_analysis_to_latex(analysis_results)
        assert "\\section{Characteristic Polynomial Analysis}" in result
        assert "Characteristic Polynomial & $t^{4} + t^{3} + 1$" in result
        assert result.startswith("\\documentclass[11pt]{article}")
        assert "\\end{document}" in result

    def test_period_distribution_only_document_is_well_formed(self):
        """When analysis_results has no 'polynomial' key, the broken
        polynomial path is never reached, so a period-distribution-only
        document should build successfully."""
        analysis_results = {
            "period_distribution": {
                "period_dict": {15: 1, 5: 1},
                "field_order": 2,
                "lfsr_degree": 4,
                "is_primitive": True,
            }
        }
        result = export_complete_analysis_to_latex(analysis_results)
        assert result.startswith("\\documentclass[11pt]{article}")
        assert "\\begin{document}" in result
        assert "\\end{document}" in result
        assert "\\section{Period Distribution}" in result
        assert "\\section{Characteristic Polynomial Analysis}" not in result
        assert "Total Sequences & $2$" in result

    def test_no_preamble_omits_document_wrapper(self):
        analysis_results = {
            "period_distribution": {
                "period_dict": {1: 1},
                "field_order": 2,
                "lfsr_degree": 1,
                "is_primitive": False,
            }
        }
        result = export_complete_analysis_to_latex(
            analysis_results, include_preamble=False
        )
        assert "\\documentclass" not in result
        assert "\\begin{document}" not in result
        assert "\\end{document}" not in result
        assert "\\section{Period Distribution}" in result

    def test_empty_analysis_results_with_preamble_is_still_valid_shell(self):
        result = export_complete_analysis_to_latex({})
        assert "\\begin{document}" in result
        assert "\\end{document}" in result
        assert "\\section{" not in result

    def test_output_file_receives_content_plus_newline(self):
        buf = io.StringIO()
        analysis_results = {
            "period_distribution": {
                "period_dict": {1: 1},
                "field_order": 2,
                "lfsr_degree": 1,
                "is_primitive": False,
            }
        }
        result = export_complete_analysis_to_latex(analysis_results, output_file=buf)
        assert buf.getvalue() == result + "\n"


class TestExportToLatexFile:
    def test_writes_file_with_expected_content(self, tmp_path):
        analysis_results = {
            "period_distribution": {
                "period_dict": {7: 2},
                "field_order": 2,
                "lfsr_degree": 3,
                "is_primitive": True,
            }
        }
        out_path = str(tmp_path / "out.tex")
        export_to_latex_file(analysis_results, out_path, include_preamble=True)

        assert os.path.exists(out_path)
        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert content.startswith("\\documentclass[11pt]{article}")
        assert "\\section{Period Distribution}" in content
        assert "Total Sequences & $2$" in content

    def test_polynomial_section_written_to_file(self, tmp_path, sample_polynomial):
        analysis_results = {
            "polynomial": {
                "polynomial": sample_polynomial,
                "order": 15,
                "is_primitive": True,
                "is_irreducible": True,
                "field_order": 2,
            }
        }
        out_path = str(tmp_path / "out.tex")
        export_to_latex_file(analysis_results, out_path)
        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Characteristic Polynomial & $t^{4} + t^{3} + 1$" in content
