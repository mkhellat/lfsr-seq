#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for lfsr.paper_generator (research-paper LaTeX section
generation from an analysis_results dict).

This module is pure string templating over a plain Python dict -- no
SageMath objects are required *except* for the ``include_tables=True``
branch of ``generate_results_section``, which forwards
``analysis_results['polynomial']['polynomial']`` into
``export_latex.polynomial_to_latex`` -> Sage's ``latex()``. Those tests
follow the established Sage-fixture pattern from test_export_latex.py
(``GF(2); PolynomialRing(F, "t")``) and are skipped module-wide if Sage
isn't importable, matching every other test file in this repo.

BUGS FOUND (documented via tests, NOT fixed -- per task instructions
this file must not modify any source file):

1. FIXED: ``generate_discussion_section`` (paper_generator.py line ~306)
   used to raise ZeroDivisionError when ``is_primitive`` was falsy and
   ``theoretical_max_period == 0`` (reachable via cli.py:1109's
   ``theoretical_max = gf_order_int ** len(coefficients) - 1``, which is 0
   whenever ``len(coefficients) == 0``, and trivially via
   ``generate_discussion_section({})`` / ``generate_complete_paper({})``
   since both ``max_period``/``theoretical_max_period`` default to 0).
   Now guarded: when ``theoretical_max`` is falsy, the percentage line is
   replaced with "an undefined fraction of the theoretical" instead of
   dividing by zero. See TestGenerateDiscussionSectionBugs below and
   TestGenerateCompletePaperBugs::test_empty_analysis_results_no_longer_crashes.

2. FIXED: previously-unescaped/unbalanced LaTeX special characters in
   ``generate_complete_paper`` (title/author), ``generate_abstract_section``
   (research_focus), and the ``\\item {text}`` interpolation of
   ``methods_used`` / ``key_observations`` lists in
   ``generate_methodology_section`` / ``generate_discussion_section``.
   None of these escaped LaTeX's reserved/special characters
   (``\\ { } % $ # _ & ^ ~``), so the resulting LaTeX was broken/unsafe
   to compile (``%`` silently truncated the rest of the line as a
   comment; ``_``/``&`` caused compilation errors outside math mode; a
   literal ``}`` unbalanced the enclosing brace-delimited argument).
   Fixed via a new ``escape_latex()`` helper applied at every
   user-supplied-string interpolation site. See TestEscapeLatex and the
   updated (now "*_now_escaped") tests in TestGenerateCompletePaperBugs.
"""

import io

import pytest

from lfsr.paper_generator import (
    escape_latex,
    generate_abstract_section,
    generate_complete_paper,
    generate_discussion_section,
    generate_methodology_section,
    generate_results_section,
)

# ---------------------------------------------------------------------------
# Optional SageMath fixture (only needed for include_tables=True polynomial
# path). Skipped at collection time for the affected tests only, matching
# this repo's convention of keeping non-Sage tests runnable without Sage.
# ---------------------------------------------------------------------------

try:
    from sage.all import GF, PolynomialRing

    SAGE_AVAILABLE = True
except ImportError:
    SAGE_AVAILABLE = False

requires_sage = pytest.mark.skipif(not SAGE_AVAILABLE, reason="SageMath not available")


@pytest.fixture
def sample_polynomial():
    F = GF(2)
    R = PolynomialRing(F, "t")
    return R("t^4 + t^3 + 1")


# ---------------------------------------------------------------------------
# escape_latex
# ---------------------------------------------------------------------------


class TestEscapeLatex:
    def test_percent_sign(self):
        assert escape_latex("100%") == "100\\%"

    def test_underscore(self):
        assert escape_latex("a_b") == "a\\_b"

    def test_ampersand(self):
        assert escape_latex("a & b") == "a \\& b"

    def test_braces(self):
        assert escape_latex("{x}") == "\\{x\\}"

    def test_dollar_and_hash(self):
        assert escape_latex("$x# ") == "\\$x\\# "

    def test_caret_and_tilde(self):
        assert escape_latex("a^b~c") == "a\\textasciicircum{}b\\textasciitilde{}c"

    def test_backslash(self):
        assert escape_latex("a\\b") == "a\\textbackslash{}b"

    def test_backslash_escaped_before_other_replacements_leak(self):
        # Backslash must be escaped first so that replacement text
        # inserted for other characters (which itself contains '\')
        # isn't re-escaped a second time.
        result = escape_latex("100%")
        assert result == "100\\%"
        assert "\\\\" not in result

    def test_plain_text_unchanged(self):
        assert escape_latex("Plain ASCII title") == "Plain ASCII title"

    def test_empty_string(self):
        assert escape_latex("") == ""


# ---------------------------------------------------------------------------
# generate_abstract_section
# ---------------------------------------------------------------------------


class TestGenerateAbstractSection:
    def test_wraps_in_abstract_environment(self):
        result = generate_abstract_section({})
        assert result.startswith("\\begin{abstract}")
        assert result.rstrip().endswith("\\end{abstract}")

    def test_defaults_used_for_empty_dict(self):
        # field_order defaults to 2, lfsr_degree to 0, is_primitive False,
        # max_period 0, theoretical_max 0 -- non-primitive branch is safe
        # here (no division), unlike generate_discussion_section.
        result = generate_abstract_section({})
        assert "\\mathbb{F}_{2}" in result
        assert "degree 0" in result
        assert "maximum period of 0" in result
        assert "theoretical maximum of 0" in result

    def test_primitive_branch(self):
        result = generate_abstract_section(
            {
                "field_order": 2,
                "lfsr_degree": 4,
                "is_primitive": True,
                "theoretical_max_period": 15,
            }
        )
        assert "primitive" in result
        assert "maximum period 15" in result
        # non-primitive-branch text must not appear
        assert "compared to the theoretical maximum" not in result

    def test_non_primitive_branch(self):
        result = generate_abstract_section(
            {
                "field_order": 2,
                "lfsr_degree": 4,
                "is_primitive": False,
                "max_period": 5,
                "theoretical_max_period": 15,
            }
        )
        assert "maximum period of 5" in result
        assert "theoretical maximum of 15" in result
        assert "characteristic polynomial is primitive" not in result

    def test_research_focus_included_when_given(self):
        result = generate_abstract_section({}, research_focus="stream cipher security")
        assert "The research focuses on stream cipher security." in result

    def test_research_focus_omitted_when_none(self):
        result = generate_abstract_section({}, research_focus=None)
        assert "The research focuses on" not in result

    def test_custom_field_order_and_degree_rendered(self):
        result = generate_abstract_section({"field_order": 3, "lfsr_degree": 7})
        assert "\\mathbb{F}_{3}" in result
        assert "degree 7" in result


# ---------------------------------------------------------------------------
# generate_methodology_section
# ---------------------------------------------------------------------------


class TestGenerateMethodologySection:
    def test_section_header_present(self):
        result = generate_methodology_section({})
        assert "\\section{Methodology}" in result

    def test_defaults_used_for_empty_dict(self):
        result = generate_methodology_section({})
        assert "\\mathbb{F}_{2}" in result
        assert "degree 0" in result

    def test_methods_used_branch_lists_each_method(self):
        result = generate_methodology_section({}, methods_used=["Berlekamp-Massey", "brute force"])
        assert "\\begin{itemize}" in result
        assert "\\item Berlekamp-Massey" in result
        assert "\\item brute force" in result
        assert "\\end{itemize}" in result
        # the "no methods" boilerplate must not appear
        assert "state space " not in result

    def test_methods_used_none_uses_default_text(self):
        result = generate_methodology_section({}, methods_used=None)
        assert "state space " in result
        assert "\\begin{itemize}" not in result

    def test_methods_used_empty_list_is_falsy_like_none(self):
        # [] is falsy in Python, so the `if methods_used:` branch should
        # behave the same as methods_used=None (default boilerplate path).
        result = generate_methodology_section({}, methods_used=[])
        assert "state space " in result
        assert "\\begin{itemize}" not in result

    def test_statistical_analysis_subsection_always_present(self):
        result = generate_methodology_section({})
        assert "\\subsection{Statistical Analysis}" in result


# ---------------------------------------------------------------------------
# generate_results_section
# ---------------------------------------------------------------------------


class TestGenerateResultsSectionNoOptionalKeys:
    def test_empty_dict_no_crash_no_polynomial_or_period_subsections(self):
        result = generate_results_section({})
        assert result.startswith("\\section{Results}")
        assert "Characteristic Polynomial Analysis" not in result
        assert "Period Distribution" not in result


class TestGenerateResultsSectionPolynomialKey:
    def test_missing_polynomial_object_routes_to_na(self):
        # poly_result.get('polynomial') is None -> falsy -> "N/A", and
        # polynomial_to_latex must NOT be called with None (would likely
        # blow up on str(None) inside Sage's fallback branch, or just be
        # semantically wrong). Confirmed by running: output is "N/A".
        result = generate_results_section({"polynomial": {}}, include_tables=False)
        assert "The characteristic polynomial is $N/A$." in result

    def test_is_primitive_branch(self):
        result = generate_results_section(
            {"polynomial": {"is_primitive": True}}, include_tables=False
        )
        assert "maximum period sequences" in result
        assert "irreducible but not primitive" not in result
        assert "factors into irreducible" not in result

    def test_is_irreducible_not_primitive_branch(self):
        result = generate_results_section(
            {"polynomial": {"is_primitive": False, "is_irreducible": True}},
            include_tables=False,
        )
        assert "irreducible but not primitive" in result

    def test_neither_primitive_nor_irreducible_branch(self):
        result = generate_results_section(
            {"polynomial": {"is_primitive": False, "is_irreducible": False}},
            include_tables=False,
        )
        assert "factors into irreducible components" in result

    def test_include_tables_false_omits_table(self):
        result = generate_results_section(
            {"polynomial": {"is_primitive": True}}, include_tables=False
        )
        assert "\\begin{table}" not in result

    @requires_sage
    def test_include_tables_true_with_real_polynomial_renders_table(self, sample_polynomial):
        result = generate_results_section(
            {
                "polynomial": {
                    "polynomial": sample_polynomial,
                    "is_primitive": True,
                    "order": 15,
                    "field_order": 2,
                }
            },
            include_tables=True,
        )
        assert "\\begin{table}[h]" in result
        assert "Characteristic Polynomial Analysis" in result
        # The real Sage-rendered polynomial LaTeX must show up (not "N/A").
        assert "N/A" not in result
        assert "t^{4} + t^{3} + 1" in result

    @requires_sage
    def test_include_tables_true_with_none_polynomial_object_still_safe(self):
        # poly_result['polynomial'] present as key but value None: the
        # section-text ternary routes to "N/A", but export_polynomial_
        # analysis_to_latex is still called unconditionally with
        # polynomial=None when include_tables=True. Confirm this doesn't
        # crash (export_latex's polynomial_to_latex has a broad except
        # around latex(polynomial) with a str() fallback).
        result = generate_results_section(
            {"polynomial": {"polynomial": None}}, include_tables=True
        )
        assert "$N/A$" in result
        assert "\\begin{table}[h]" in result


class TestGenerateResultsSectionPeriodDistributionKey:
    def test_missing_period_dict_defaults_to_empty_max_zero(self):
        result = generate_results_section(
            {"period_distribution": {}}, include_tables=False
        )
        assert "maximum period of 0" in result
        assert "theoretical maximum of 0" in result

    def test_period_dict_present_max_computed_from_keys(self):
        result = generate_results_section(
            {"period_distribution": {"period_dict": {3: 2, 7: 5, 15: 1}}},
            include_tables=False,
        )
        assert "maximum period of 15" in result

    def test_is_primitive_branch(self):
        result = generate_results_section(
            {
                "period_distribution": {
                    "period_dict": {15: 1},
                    "is_primitive": True,
                }
            },
            include_tables=False,
        )
        assert "all non-zero" in result
        assert "shows variation" not in result

    def test_non_primitive_branch(self):
        result = generate_results_section(
            {
                "period_distribution": {
                    "period_dict": {15: 1, 5: 3},
                    "is_primitive": False,
                }
            },
            include_tables=False,
        )
        assert "shows variation across" in result

    def test_include_tables_true_renders_period_table_no_sage_needed(self):
        # export_period_distribution_to_latex is pure Python (no Sage
        # calls) -- unlike the polynomial table path.
        result = generate_results_section(
            {
                "period_distribution": {
                    "period_dict": {15: 1, 5: 3},
                    "is_primitive": False,
                    "field_order": 2,
                    "lfsr_degree": 4,
                    "theoretical_max_period": 15,
                }
            },
            include_tables=True,
        )
        assert "Period Distribution Analysis" in result
        assert "Period Distribution Statistics" in result

    def test_both_polynomial_and_period_distribution_present(self):
        result = generate_results_section(
            {
                "polynomial": {"is_primitive": True},
                "period_distribution": {"period_dict": {15: 1}, "is_primitive": True},
            },
            include_tables=False,
        )
        assert "Characteristic Polynomial Analysis" in result
        assert "Period Distribution" in result


# ---------------------------------------------------------------------------
# generate_discussion_section
# ---------------------------------------------------------------------------


class TestGenerateDiscussionSection:
    def test_section_header(self):
        result = generate_discussion_section({"is_primitive": True})
        assert "\\section{Discussion}" in result

    def test_primitive_branch_no_division(self):
        result = generate_discussion_section({"is_primitive": True})
        assert "\\subsection{Primitive Polynomial Properties}" in result
        assert "\\subsection{Period Structure}" not in result

    def test_non_primitive_branch_with_nonzero_theoretical_max(self):
        result = generate_discussion_section(
            {"is_primitive": False, "max_period": 5, "theoretical_max_period": 15}
        )
        assert "\\subsection{Period Structure}" in result
        # 5/15*100 == 33.333... -> "33.3"
        assert "33.3\\% of the theoretical" in result

    def test_key_observations_included_when_given(self):
        result = generate_discussion_section(
            {"is_primitive": True}, key_observations=["obs one", "obs two"]
        )
        assert "\\subsection{Key Observations}" in result
        assert "\\item obs one" in result
        assert "\\item obs two" in result

    def test_key_observations_omitted_when_none(self):
        result = generate_discussion_section({"is_primitive": True}, key_observations=None)
        assert "\\subsection{Key Observations}" not in result

    def test_key_observations_empty_list_omitted(self):
        result = generate_discussion_section({"is_primitive": True}, key_observations=[])
        assert "\\subsection{Key Observations}" not in result

    def test_implications_subsection_always_present(self):
        result = generate_discussion_section({"is_primitive": True})
        assert "\\subsection{Implications}" in result


class TestGenerateDiscussionSectionBugs:
    """
    BUG 1 (fixed): the non-primitive branch used to raise ZeroDivisionError
    when theoretical_max_period == 0. See module docstring for the
    reachability argument (empty coefficients list -> theoretical_max =
    gf_order**0 - 1 = 0 at cli.py:1109). Now guarded: these cases return
    an "undefined fraction" placeholder instead of dividing by zero.
    """

    def test_zero_theoretical_max_period_no_longer_raises(self):
        result = generate_discussion_section(
            {"is_primitive": False, "max_period": 5, "theoretical_max_period": 0}
        )
        assert "undefined fraction" in result

    def test_zero_theoretical_max_period_no_longer_raises_even_with_zero_max_period_too(self):
        # Degenerate all-zero-coefficient-style input: both are 0.
        result = generate_discussion_section(
            {"is_primitive": False, "max_period": 0, "theoretical_max_period": 0}
        )
        assert "undefined fraction" in result

    def test_missing_keys_also_default_to_the_previously_crashing_case(self):
        # is_primitive defaults False, max_period defaults 0,
        # theoretical_max_period defaults 0 -> the empty dict itself
        # used to trigger the bug with zero explicit configuration.
        result = generate_discussion_section({})
        assert "undefined fraction" in result


# ---------------------------------------------------------------------------
# generate_complete_paper
# ---------------------------------------------------------------------------


# A minimal analysis_results dict that avoids BUG 1 (non-zero
# theoretical_max_period) so the "happy path" tests below can exercise
# the rest of generate_complete_paper without tripping the known crash.
SAFE_RESULTS = {
    "field_order": 2,
    "lfsr_degree": 4,
    "is_primitive": True,
    "max_period": 15,
    "theoretical_max_period": 15,
}


class TestGenerateCompletePaper:
    def test_default_title_and_author_used(self):
        result = generate_complete_paper(SAFE_RESULTS)
        assert "\\title{LFSR Analysis Results}" in result
        assert "\\author{Generated by lfsr-seq}" in result

    def test_custom_title_and_author(self):
        result = generate_complete_paper(SAFE_RESULTS, title="My Paper", author="Jane Doe")
        assert "\\title{My Paper}" in result
        assert "\\author{Jane Doe}" in result

    def test_author_none_uses_default(self):
        result = generate_complete_paper(SAFE_RESULTS, author=None)
        assert "\\author{Generated by lfsr-seq}" in result

    def test_document_structure_present(self):
        result = generate_complete_paper(SAFE_RESULTS)
        assert "\\documentclass[11pt]{article}" in result
        assert "\\begin{document}" in result
        assert "\\end{document}" in result
        assert result.rstrip().endswith("\\end{document}")
        assert "\\maketitle" in result

    def test_all_standard_sections_present(self):
        result = generate_complete_paper(SAFE_RESULTS)
        for heading in (
            "\\begin{abstract}",
            "\\section{Introduction}",
            "\\section{Methodology}",
            "\\section{Results}",
            "\\section{Discussion}",
            "\\section{Conclusion}",
        ):
            assert heading in result

    def test_research_focus_propagated_to_abstract(self):
        result = generate_complete_paper(SAFE_RESULTS, research_focus="clock-controlled LFSRs")
        assert "The research focuses on clock-controlled LFSRs." in result

    def test_methods_used_propagated_to_methodology(self):
        result = generate_complete_paper(SAFE_RESULTS, methods_used=["exhaustive search"])
        assert "\\item exhaustive search" in result

    def test_key_observations_propagated_to_discussion(self):
        result = generate_complete_paper(SAFE_RESULTS, key_observations=["high linear complexity"])
        assert "\\item high linear complexity" in result

    def test_output_file_receives_same_content_as_return_value(self, tmp_path):
        target = tmp_path / "paper.tex"
        with open(target, "w") as fh:
            returned = generate_complete_paper(SAFE_RESULTS, output_file=fh)
        written = target.read_text()
        # The function writes `result` then a trailing "\n".
        assert written == returned + "\n"

    def test_output_file_receives_content_via_stringio(self):
        buf = io.StringIO()
        returned = generate_complete_paper(SAFE_RESULTS, output_file=buf)
        assert buf.getvalue() == returned + "\n"

    def test_no_output_file_does_not_raise(self):
        # output_file=None (default) must simply skip the write branch.
        result = generate_complete_paper(SAFE_RESULTS, output_file=None)
        assert isinstance(result, str)

    def test_date_line_present_and_well_formed(self):
        result = generate_complete_paper(SAFE_RESULTS)
        date_lines = [line for line in result.splitlines() if line.startswith("\\date{")]
        assert len(date_lines) == 1
        # \date{YYYY-MM-DD}
        assert date_lines[0].count("-") == 2


class TestGenerateCompletePaperBugs:
    def test_empty_analysis_results_no_longer_crashes(self):
        # Same BUG 1 as generate_discussion_section (now fixed), reachable
        # through the top-level orchestration function too.
        result = generate_complete_paper({})
        assert "undefined fraction" in result

    def test_title_percent_sign_now_escaped(self):
        # BUG 2 (fixed): '%' is LaTeX's comment character. escape_latex
        # now converts it to '\%' so it no longer truncates the rest of
        # the line when compiled.
        result = generate_complete_paper(SAFE_RESULTS, title="100% Faster LFSR Analysis")
        title_lines = [l for l in result.splitlines() if l.startswith("\\title{")]
        assert title_lines == ["\\title{100\\% Faster LFSR Analysis}"]

    def test_title_underscore_and_ampersand_now_escaped(self):
        # '_' and '&' are catcode-special outside math mode; now escaped
        # as \_ and \& so they no longer break compilation.
        result = generate_complete_paper(SAFE_RESULTS, title="A_B & Co Analysis")
        title_lines = [l for l in result.splitlines() if l.startswith("\\title{")]
        assert title_lines == ["\\title{A\\_B \\& Co Analysis}"]

    def test_title_with_literal_closing_brace_now_balanced(self):
        # A literal '}' in the title used to close the \title{...}
        # argument early. Now escaped to '\}' so the argument stays
        # balanced.
        result = generate_complete_paper(SAFE_RESULTS, title="Weird}Title")
        title_lines = [l for l in result.splitlines() if l.startswith("\\title{")]
        assert title_lines == ["\\title{Weird\\}Title}"]
        # The outer \title{...} wrapper still balances: 2 opens (wrapper +
        # none nested), 2 closes (escaped \} counts as literal chars, not
        # a real brace pair, plus the wrapper's own close).
        assert title_lines[0].count("{") == 1

    def test_author_special_characters_now_escaped(self):
        result = generate_complete_paper(SAFE_RESULTS, author="Smith & Jones_Lab")
        author_lines = [l for l in result.splitlines() if l.startswith("\\author{")]
        assert author_lines == ["\\author{Smith \\& Jones\\_Lab}"]

    def test_research_focus_special_characters_now_escaped_in_abstract(self):
        result = generate_complete_paper(SAFE_RESULTS, research_focus="50% faster & cheaper")
        assert "The research focuses on 50\\% faster \\& cheaper." in result

    def test_key_observations_item_special_characters_now_escaped(self):
        result = generate_complete_paper(
            SAFE_RESULTS, key_observations=["period is 100% of the theoretical max & optimal"]
        )
        assert "\\item period is 100\\% of the theoretical max \\& optimal" in result

    def test_methods_used_item_special_characters_now_escaped(self):
        result = generate_complete_paper(
            SAFE_RESULTS, methods_used=["brute_force search (cost ~ O(2^n))"]
        )
        assert (
            "\\item brute\\_force search (cost \\textasciitilde{} O(2\\textasciicircum{}n))"
            in result
        )
