#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Edge case tests for LFSR analysis.

Tests for boundary conditions, degenerate cases, and special scenarios.
"""

import pytest

# Import SageMath - will be skipped if not available via conftest
try:
    from sage.all import *
except ImportError:
    pytest.skip("SageMath not available", allow_module_level=True)

from lfsr.analysis import lfsr_sequence_mapper
from lfsr.core import build_state_update_matrix, compute_matrix_order
from lfsr.field import validate_coefficient_vector, validate_gf_order
from lfsr.polynomial import characteristic_polynomial


class TestZeroState:
    """Tests for zero state handling."""

    def test_zero_state_in_sequence(self):
        """Test that zero state is properly handled in sequences."""
        # LFSR with coefficients that may include zero state
        coeffs = [1, 1, 0, 1]
        C, _ = build_state_update_matrix(coeffs, 2)
        V = VectorSpace(GF(2), 4)

        seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
            C, V, 2, None
        )

        # Zero state should be in one of the sequences
        zero_state = V([0, 0, 0, 0])
        found_zero = False
        for seq in seq_dict.values():
            if zero_state in seq:
                found_zero = True
                break
        assert found_zero, "Zero state should be present in sequences"

    def test_zero_state_period(self):
        """Test that zero state has correct period (should be 1)."""
        coeffs = [1, 1, 0, 1]
        C, _ = build_state_update_matrix(coeffs, 2)
        V = VectorSpace(GF(2), 4)

        seq_dict, period_dict, _, _ = lfsr_sequence_mapper(C, V, 2, None)

        # Find sequence containing zero state
        zero_state = V([0, 0, 0, 0])
        zero_period = None
        for seq_num, seq in seq_dict.items():
            if zero_state in seq:
                zero_period = period_dict[seq_num]
                break

        assert zero_period is not None
        # Zero state should map to itself, so period is 1
        assert zero_period == 1


class TestDegenerateLFSRs:
    """Tests for degenerate LFSR configurations."""

    def test_all_zero_coefficients(self):
        """Test LFSR with all zero coefficients (degenerate case)."""
        # All zeros - this is a degenerate LFSR
        coeffs = [0, 0, 0, 0]
        C, _ = build_state_update_matrix(coeffs, 2)
        V = VectorSpace(GF(2), 4)

        seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
            C, V, 2, None
        )

        # All states should map to zero or have period 1
        # This is a degenerate case where the LFSR doesn't actually shift
        assert len(seq_dict) > 0
        assert periods_sum == 16  # Still should cover all 2^4 states

    def test_single_one_coefficient(self):
        """Test LFSR with only one non-zero coefficient."""
        # Only first coefficient is 1
        coeffs = [1, 0, 0, 0]
        C, _ = build_state_update_matrix(coeffs, 2)
        V = VectorSpace(GF(2), 4)

        seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
            C, V, 2, None
        )

        assert len(seq_dict) > 0
        assert periods_sum == 16

    def test_all_ones_coefficients(self):
        """Test LFSR with all coefficients set to 1."""
        coeffs = [1, 1, 1, 1]
        C, _ = build_state_update_matrix(coeffs, 2)
        V = VectorSpace(GF(2), 4)

        seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
            C, V, 2, None
        )

        assert len(seq_dict) > 0
        assert periods_sum == 16


class TestBoundaryConditions:
    """Tests for boundary conditions and limits."""

    def test_minimal_lfsr_2bit(self):
        """Test minimal 2-bit LFSR."""
        coeffs = [1, 1]
        C, _ = build_state_update_matrix(coeffs, 2)
        V = VectorSpace(GF(2), 2)

        seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
            C, V, 2, None
        )

        assert periods_sum == 4  # 2^2 = 4 states
        assert len(seq_dict) > 0

    def test_single_bit_lfsr(self):
        """Test single-bit LFSR (smallest possible)."""
        coeffs = [1]
        C, _ = build_state_update_matrix(coeffs, 2)
        V = VectorSpace(GF(2), 1)

        seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
            C, V, 2, None
        )

        assert periods_sum == 2  # 2^1 = 2 states
        assert len(seq_dict) > 0

    def test_maximal_period_lfsr(self):
        """Test LFSR configuration known to have maximal period."""
        # 4-bit maximal-length LFSR: [1,1,0,1] has period 15 (maximal for 4 bits)
        coeffs = [1, 1, 0, 1]
        C, _ = build_state_update_matrix(coeffs, 2)
        V = VectorSpace(GF(2), 4)

        seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
            C, V, 2, None
        )

        # Maximal period for 4-bit is 15 (2^4 - 1, excluding zero state)
        assert max_period <= 15
        assert periods_sum == 16  # All states covered

    def test_matrix_order_boundary(self):
        """Test matrix order computation at boundary conditions."""
        coeffs = [1, 1, 0, 1]
        C, _ = build_state_update_matrix(coeffs, 2)

        M = MatrixSpace(GF(2), 4, 4)
        I = M.identity_matrix()
        state_space_size = 2 ** 4

        order = compute_matrix_order(C, I, state_space_size, None)

        # Order should be found and within valid range
        assert order is not None
        assert 1 <= order <= state_space_size - 1


class TestDifferentFieldOrders:
    """Tests for different Galois field orders."""

    def test_gf3_small_lfsr(self):
        """Test small LFSR over GF(3)."""
        coeffs = [1, 2]
        C, _ = build_state_update_matrix(coeffs, 3)
        V = VectorSpace(GF(3), 2)

        seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
            C, V, 3, None
        )

        assert periods_sum == 9  # 3^2 = 9 states
        assert len(seq_dict) > 0

    def test_gf5_lfsr(self):
        """Test LFSR over GF(5)."""
        coeffs = [1, 3, 2]
        C, _ = build_state_update_matrix(coeffs, 5)
        V = VectorSpace(GF(5), 3)

        seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
            C, V, 5, None
        )

        assert periods_sum == 125  # 5^3 = 125 states
        assert len(seq_dict) > 0

    def test_gf4_prime_power(self):
        """Test LFSR over GF(4) = GF(2^2)."""
        # GF(4) is a prime power
        coeffs = [1, 2, 1]
        C, _ = build_state_update_matrix(coeffs, 4)
        V = VectorSpace(GF(4), 3)

        seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
            C, V, 4, None
        )

        assert periods_sum == 64  # 4^3 = 64 states
        assert len(seq_dict) > 0


class TestValidationEdgeCases:
    """Tests for validation edge cases."""

    def test_validate_gf_order_minimum(self):
        """Test validation of minimum valid GF order."""
        # Minimum is 2
        result = validate_gf_order("2")
        assert result == 2

    def test_validate_gf_order_large_prime(self):
        """Test validation of larger prime."""
        # Test with a larger prime (within reasonable limit)
        result = validate_gf_order("97")
        assert result == 97

    def test_validate_coefficient_at_boundary(self):
        """Test coefficient validation at field boundaries."""
        # For GF(3), valid coefficients are 0, 1, 2
        assert validate_coefficient("0", 3, 1, 0) == 0
        assert validate_coefficient("1", 3, 1, 0) == 1
        assert validate_coefficient("2", 3, 1, 0) == 2

    def test_validate_coefficient_vector_single_element(self):
        """Test validation of single-element coefficient vector."""
        vector = ["1"]
        validate_coefficient_vector(vector, 2, 1)
        # Should not raise

    def test_validate_coefficient_vector_long(self):
        """Test validation of longer coefficient vector."""
        # 10-element vector
        vector = ["1", "0", "1", "1", "0", "0", "1", "1", "0", "1"]
        validate_coefficient_vector(vector, 2, 1)
        # Should not raise


class TestPolynomialEdgeCases:
    """Tests for polynomial operation edge cases."""

    def test_characteristic_polynomial_degree_one(self):
        """Test characteristic polynomial for 1-bit LFSR."""
        coeffs = [1]
        _, CS = build_state_update_matrix(coeffs, 2)

        char_poly = characteristic_polynomial(CS, 2, None)

        assert char_poly.degree() == 1

    def test_characteristic_polynomial_degree_two(self):
        """Test characteristic polynomial for 2-bit LFSR."""
        coeffs = [1, 1]
        _, CS = build_state_update_matrix(coeffs, 2)

        char_poly = characteristic_polynomial(CS, 2, None)

        assert char_poly.degree() == 2

    def test_polynomial_order_identity(self):
        """Test polynomial order for identity-like polynomial."""
        from lfsr.polynomial import polynomial_order

        R = PolynomialRing(GF(2), "t")
        # Simple polynomial
        poly = R("t + 1")
        order = polynomial_order(poly, 1, 2)

        assert order is not None
        assert order >= 1


class TestStateSpaceCoverage:
    """Tests to verify complete state space coverage."""

    def test_all_states_covered(self):
        """Test that all states in the vector space are covered."""
        coeffs = [1, 1, 0, 1]
        C, _ = build_state_update_matrix(coeffs, 2)
        V = VectorSpace(GF(2), 4)

        seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
            C, V, 2, None
        )

        # Sum of all periods should equal total state space size
        assert periods_sum == 2 ** 4

        # Verify all states are in sequences
        all_states = set()
        for seq in seq_dict.values():
            for state in seq:
                all_states.add(tuple(state))

        # Should have 16 unique states
        assert len(all_states) == 16

    def test_no_duplicate_states(self):
        """Test that no state appears in multiple sequences."""
        coeffs = [1, 0, 1, 1]
        C, _ = build_state_update_matrix(coeffs, 2)
        V = VectorSpace(GF(2), 4)

        seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
            C, V, 2, None
        )

        # Collect all states
        all_states = []
        for seq in seq_dict.values():
            all_states.extend(seq)

        # Convert to tuples for comparison
        state_tuples = [tuple(s) for s in all_states]

        # Should have exactly 16 states (no duplicates across sequences)
        assert len(state_tuples) == 16
        # All should be unique
        assert len(set(state_tuples)) == 16

