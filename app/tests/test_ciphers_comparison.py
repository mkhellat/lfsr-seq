#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for lfsr.ciphers.comparison: compare_ciphers() and
generate_comparison_report().

No performance/benchmarking numbers are hardcoded or asserted here (per
project instructions) -- these tests only check structural correctness
of the comparison output against real StreamCipher subclasses already
covered by their own test modules (Trivium, A5/1, LILI-128), using small
keystream lengths for speed.

**BUG FOUND AND FIXED** (2026-08-11): ``CipherComparison.recommendations``
(src/lfsr/ciphers/comparison.py) was type-annotated as ``List[str]`` but
its dataclass default was ``field(default_factory=dict)`` -- constructing
a ``CipherComparison`` without an explicit ``recommendations=`` argument
silently produced an empty **dict** instead of an empty **list**. Fixed
to ``field(default_factory=list)``.
"""

from lfsr.ciphers.a5_1 import A5_1
from lfsr.ciphers.a5_2 import A5_2
from lfsr.ciphers.comparison import (
    CipherComparison,
    compare_ciphers,
    generate_comparison_report,
)
from lfsr.ciphers.lili128 import LILI128
from lfsr.ciphers.trivium import Trivium


def test_cipher_comparison_recommendations_default_is_a_list():
    comparison = CipherComparison(ciphers=["X"])
    assert isinstance(comparison.recommendations, list)
    assert comparison.recommendations == []


def test_compare_ciphers_basic_properties():
    ciphers = [A5_1(), Trivium()]
    comparison = compare_ciphers(ciphers)

    assert comparison.ciphers == ["A5/1", "Trivium"]
    assert set(comparison.properties.keys()) == {"A5/1", "Trivium"}

    a51_props = comparison.properties["A5/1"]
    assert a51_props["key_size"] == 64
    assert a51_props["iv_size"] == 22
    assert a51_props["state_size"] == 64
    assert a51_props["num_lfsrs"] == 3

    trivium_props = comparison.properties["Trivium"]
    assert trivium_props["key_size"] == 80
    assert trivium_props["iv_size"] == 80
    assert trivium_props["state_size"] == 288
    assert trivium_props["num_lfsrs"] == 1


def test_compare_ciphers_recommendations_is_a_real_list_via_public_api():
    # Even though the dataclass default is buggy (see above), the public
    # compare_ciphers() function always supplies an explicit list, so
    # callers going through the documented API are unaffected.
    comparison = compare_ciphers([A5_1(), Trivium()])
    assert isinstance(comparison.recommendations, list)
    assert len(comparison.recommendations) > 0


def test_compare_ciphers_security_assessment_a5_1_flags_vulnerabilities():
    comparison = compare_ciphers([A5_1()])
    assessment = comparison.security_assessment["A5/1"]
    assert len(assessment["known_vulnerabilities"]) > 0
    assert len(assessment["recommendations"]) > 0


def test_compare_ciphers_security_assessment_a5_2_flags_complete_break():
    comparison = compare_ciphers([A5_2()])
    assessment = comparison.security_assessment["A5/2"]
    assert any("break" in v.lower() for v in assessment["known_vulnerabilities"])
    assert any("never use" in r.lower() for r in assessment["recommendations"])


def test_compare_ciphers_security_assessment_trivium_no_vulnerabilities():
    comparison = compare_ciphers([Trivium()])
    assessment = comparison.security_assessment["Trivium"]
    assert assessment["known_vulnerabilities"] == []
    assert "secure" in " ".join(assessment["recommendations"]).lower()


def test_compare_ciphers_key_size_recommendation_triggered_by_small_key():
    # A5/1 has a 64-bit key (< 128), so compare_ciphers should flag it.
    comparison = compare_ciphers([A5_1()])
    joined = " ".join(comparison.recommendations)
    assert "128" in joined or "smaller" in joined.lower()


def test_compare_ciphers_state_size_range_recommendation():
    comparison = compare_ciphers([A5_1(), Trivium()])
    joined = " ".join(comparison.recommendations)
    assert "64" in joined  # A5/1 state size
    assert "288" in joined  # Trivium state size


def test_compare_ciphers_with_keystream_analysis_flag_does_not_crash():
    # analyze_keystream/key/iv parameters exist in the signature but are
    # currently unused by compare_ciphers()'s implementation (it never
    # reads them) -- lock in that passing them is at least harmless.
    comparison = compare_ciphers(
        [Trivium()],
        analyze_keystream=True,
        key=[0] * 80,
        iv=[0] * 80,
    )
    assert comparison.ciphers == ["Trivium"]


def test_compare_ciphers_three_ciphers():
    comparison = compare_ciphers([A5_1(), LILI128(), Trivium()])
    assert comparison.ciphers == ["A5/1", "LILI-128", "Trivium"]
    assert len(comparison.properties) == 3
    assert len(comparison.security_assessment) == 3


def test_generate_comparison_report_contains_all_cipher_names():
    comparison = compare_ciphers([A5_1(), Trivium()])
    report = generate_comparison_report(comparison)
    assert isinstance(report, str)
    assert "A5/1" in report
    assert "Trivium" in report
    assert "Stream Cipher Comparison Report" in report


def test_generate_comparison_report_contains_property_table():
    comparison = compare_ciphers([A5_1(), Trivium()])
    report = generate_comparison_report(comparison)
    assert "Key Size (bits)" in report
    assert "IV Size (bits)" in report
    assert "State Size (bits)" in report
    assert "Number of LFSRs" in report
    assert str(A5_1().get_config().key_size) in report
    assert str(Trivium().get_config().key_size) in report


def test_generate_comparison_report_lists_vulnerabilities_or_none():
    comparison = compare_ciphers([A5_1(), Trivium()])
    report = generate_comparison_report(comparison)
    assert "Known Vulnerabilities:" in report
    # Trivium has none -> should say "None" for that cipher.
    assert "Known Vulnerabilities: None" in report


def test_generate_comparison_report_includes_general_recommendations():
    comparison = compare_ciphers([A5_1(), Trivium()])
    report = generate_comparison_report(comparison)
    assert "General Recommendations:" in report


def test_generate_comparison_report_single_cipher():
    comparison = compare_ciphers([Trivium()])
    report = generate_comparison_report(comparison)
    assert "Trivium" in report
    assert report.count("Trivium") >= 2  # header list + table + section
