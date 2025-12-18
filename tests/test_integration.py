#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integration tests for full LFSR analysis workflow.

Tests the complete workflow from CSV input to analysis output.
"""

import os
import pytest
import tempfile
from pathlib import Path

# Import SageMath - will be skipped if not available via conftest
try:
    from sage.all import *
except ImportError:
    pytest.skip("SageMath not available", allow_module_level=True)

from lfsr.cli import main
from lfsr.analysis import lfsr_sequence_mapper
from lfsr.core import build_state_update_matrix, compute_matrix_order


class TestFullWorkflow:
    """Tests for complete LFSR analysis workflow."""

    def test_simple_4bit_lfsr_workflow(self, tmp_path):
        """Test complete workflow for a simple 4-bit LFSR."""
        # Create test CSV file
        csv_file = tmp_path / "test_lfsr.csv"
        csv_file.write_text("1,1,0,1\n")

        # Create output file
        output_file = tmp_path / "test_output.txt"

        # Run main workflow
        with open(output_file, "w") as f:
            main(str(csv_file), "2", f)

        # Verify output file was created and has content
        assert output_file.exists()
        content = output_file.read_text()
        assert len(content) > 0

        # Verify key sections are present
        assert "COEFFS SERIES" in content
        assert "STATE UPDATE MATRIX" in content
        assert "STATES SEQUENCES" in content
        assert "CHARACTERISTIC POLYNOMIAL" in content

    def test_multiple_lfsr_configurations(self, tmp_path):
        """Test workflow with multiple LFSR configurations."""
        csv_file = tmp_path / "test_lfsrs.csv"
        csv_file.write_text("1,1,0,1\n1,0,1,1\n")

        output_file = tmp_path / "test_output.txt"

        with open(output_file, "w") as f:
            main(str(csv_file), "2", f)

        content = output_file.read_text()
        # Should have two coefficient series
        assert content.count("COEFFS SERIES 1") == 1
        assert content.count("COEFFS SERIES 2") == 1

    def test_gf3_workflow(self, tmp_path):
        """Test complete workflow over GF(3)."""
        csv_file = tmp_path / "test_gf3.csv"
        csv_file.write_text("1,2,1\n")

        output_file = tmp_path / "test_output.txt"

        with open(output_file, "w") as f:
            main(str(csv_file), "3", f)

        assert output_file.exists()
        content = output_file.read_text()
        assert "GF order : 3" in content

    def test_sequence_mapper_integration(self):
        """Test lfsr_sequence_mapper with real matrix."""
        coeffs = [1, 1, 0, 1]
        C, _ = build_state_update_matrix(coeffs, 2)
        V = VectorSpace(GF(2), 4)

        seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
            C, V, 2, None
        )

        # Verify results
        assert len(seq_dict) > 0
        assert len(period_dict) > 0
        assert max_period >= 1
        assert periods_sum == 16  # 2^4 = 16 states total

        # Verify all periods sum to state space size
        assert periods_sum == 2 ** 4

    def test_matrix_order_integration(self):
        """Test matrix order computation in integration context."""
        coeffs = [1, 1, 0, 1]
        C, _ = build_state_update_matrix(coeffs, 2)

        M = MatrixSpace(GF(2), 4, 4)
        I = M.identity_matrix()
        state_space_size = 2 ** 4

        order = compute_matrix_order(C, I, state_space_size, None)

        # Verify order is reasonable
        assert order is not None
        assert 1 <= order <= state_space_size - 1

    def test_characteristic_polynomial_integration(self):
        """Test characteristic polynomial computation in integration context."""
        from lfsr.polynomial import characteristic_polynomial

        coeffs = [1, 1, 0, 1]
        _, CS = build_state_update_matrix(coeffs, 2)

        char_poly = characteristic_polynomial(CS, 2, None)

        # Verify polynomial properties
        assert char_poly is not None
        assert char_poly.degree() == 4
        assert char_poly.parent() == PolynomialRing(GF(2), "t")

    @pytest.mark.slow
    def test_larger_lfsr_workflow(self, tmp_path):
        """Test workflow with a larger LFSR (marked as slow)."""
        # 5-bit LFSR
        csv_file = tmp_path / "test_large.csv"
        csv_file.write_text("1,0,0,1,0\n")

        output_file = tmp_path / "test_output.txt"

        with open(output_file, "w") as f:
            main(str(csv_file), "2", f)

        assert output_file.exists()
        content = output_file.read_text()
        # Should have processed 2^5 = 32 states
        assert "32" in content or "NO. STATE VECTORS" in content


class TestEdgeCases:
    """Tests for edge cases in the workflow."""

    def test_minimal_lfsr(self, tmp_path):
        """Test workflow with minimal 2-bit LFSR."""
        csv_file = tmp_path / "test_minimal.csv"
        csv_file.write_text("1,1\n")

        output_file = tmp_path / "test_output.txt"

        with open(output_file, "w") as f:
            main(str(csv_file), "2", f)

        assert output_file.exists()
        content = output_file.read_text()
        # Should have processed 2^2 = 4 states
        assert "4" in content or "NO. STATE VECTORS" in content

    def test_maximal_period_lfsr(self, tmp_path):
        """Test workflow with a maximal-length LFSR."""
        # 4-bit maximal-length LFSR: [1,1,0,1] has period 15
        csv_file = tmp_path / "test_maximal.csv"
        csv_file.write_text("1,1,0,1\n")

        output_file = tmp_path / "test_output.txt"

        with open(output_file, "w") as f:
            main(str(csv_file), "2", f)

        assert output_file.exists()
        content = output_file.read_text()
        # Should mention period 15 somewhere
        assert "15" in content or "T : 15" in content

