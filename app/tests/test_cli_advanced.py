#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for lfsr.cli_advanced -- CLI plumbing for advanced LFSR structures
(NFSR, filtered, clock-controlled, multi-output, irregular clocking).
The advanced/ structures themselves are covered under
tests/test_advanced.py; these tests check dispatch and output for the
CLI wrapper.
"""

import io

import pytest

from lfsr.attacks import LFSRConfig
from lfsr.cli_advanced import (
    get_advanced_structure_instance,
    perform_advanced_structure_analysis_cli,
)


@pytest.fixture
def base_lfsr():
    return LFSRConfig(coefficients=[1, 1, 0], field_order=2, degree=3)


class TestGetAdvancedStructureInstance:
    def test_nfsr(self, base_lfsr):
        s = get_advanced_structure_instance("nfsr", base_lfsr)
        assert s is not None

    def test_filtered(self, base_lfsr):
        s = get_advanced_structure_instance("filtered", base_lfsr)
        assert s is not None

    def test_clock_controlled(self, base_lfsr):
        s = get_advanced_structure_instance("clock_controlled", base_lfsr)
        assert s is not None

    def test_multi_output(self, base_lfsr):
        s = get_advanced_structure_instance("multi_output", base_lfsr)
        assert s is not None

    def test_irregular(self, base_lfsr):
        s = get_advanced_structure_instance("irregular", base_lfsr)
        assert s is not None

    def test_unknown_type_raises(self, base_lfsr):
        with pytest.raises(ValueError, match="Unknown structure type"):
            get_advanced_structure_instance("bogus", base_lfsr)


class TestPerformAdvancedStructureAnalysisCli:
    def test_nfsr_analyze_structure(self, base_lfsr):
        buf = io.StringIO()
        perform_advanced_structure_analysis_cli(
            "nfsr", base_lfsr, analyze_structure=True, output_file=buf
        )
        out = buf.getvalue()
        assert "Advanced LFSR Structure Analysis" in out
        assert "NFSR is NOT an LFSR" in out
        assert "Structure Analysis" in out

    def test_filtered_generate_sequence(self, base_lfsr):
        buf = io.StringIO()
        perform_advanced_structure_analysis_cli(
            "filtered", base_lfsr, generate_sequence=True, sequence_length=20, output_file=buf
        )
        out = buf.getvalue()
        assert "This IS an LFSR" in out
        assert "Generated 20 sequence elements" in out
        assert "Ones:" in out  # field_order == 2 stats

    def test_clock_controlled_generate_sequence(self, base_lfsr):
        buf = io.StringIO()
        perform_advanced_structure_analysis_cli(
            "clock_controlled", base_lfsr, generate_sequence=True, sequence_length=10, output_file=buf
        )
        out = buf.getvalue()
        assert "Generated 10 sequence elements" in out

    def test_irregular_generate_sequence(self, base_lfsr):
        buf = io.StringIO()
        perform_advanced_structure_analysis_cli(
            "irregular", base_lfsr, generate_sequence=True, sequence_length=10, output_file=buf
        )
        out = buf.getvalue()
        assert "Generated 10 sequence elements" in out

    def test_multi_output_analyze_and_generate(self, base_lfsr):
        buf = io.StringIO()
        perform_advanced_structure_analysis_cli(
            "multi_output", base_lfsr,
            analyze_structure=True, generate_sequence=True, sequence_length=15,
            output_file=buf,
        )
        out = buf.getvalue()
        assert "Structure Analysis" in out
        assert "Sequence Generation" in out

    def test_output_defaults_to_stdout(self, base_lfsr, capsys):
        perform_advanced_structure_analysis_cli("nfsr", base_lfsr)
        captured = capsys.readouterr()
        assert "Advanced LFSR Structure Analysis" in captured.out

    def test_basic_info_printed(self, base_lfsr):
        buf = io.StringIO()
        perform_advanced_structure_analysis_cli("filtered", base_lfsr, output_file=buf)
        out = buf.getvalue()
        assert "Base LFSR Degree: 3" in out
        assert "Base LFSR Field Order: 2" in out
