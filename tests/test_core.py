#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for LFSR core mathematics functions.

Tests for build_state_update_matrix and compute_matrix_order functions.
"""

import pytest

# Import SageMath - will be skipped if not available via conftest
try:
    from sage.all import *
except ImportError:
    pytest.skip("SageMath not available", allow_module_level=True)

from lfsr.core import build_state_update_matrix, compute_matrix_order


class TestBuildStateUpdateMatrix:
    """Tests for build_state_update_matrix function."""

    def test_simple_4bit_lfsr_gf2(self):
        """Test building state update matrix for 4-bit LFSR over GF(2)."""
        coeffs = [1, 1, 0, 1]
        C, CS = build_state_update_matrix(coeffs, 2)

        # Verify dimensions
        assert C.dimensions() == (4, 4)
        assert CS.dimensions() == (4, 4)

        # Verify matrix structure (companion matrix form)
        # First row should be [coeffs[0], 0, 0, 0] = [1, 0, 0, 0]
        assert C[0, 0] == 1
        assert C[0, 1] == 0
        assert C[0, 2] == 0
        assert C[0, 3] == 0

        # Second row should have 1 in first position: [0, 1, 0, 0]
        assert C[1, 0] == 0
        assert C[1, 1] == 1
        assert C[1, 2] == 0
        assert C[1, 3] == 0

        # Third row should have 1 in second position: [0, 0, 1, 0]
        assert C[2, 0] == 0
        assert C[2, 1] == 0
        assert C[2, 2] == 1
        assert C[2, 3] == 0

        # Fourth row should have coefficients: [coeffs[3], coeffs[2], coeffs[1], coeffs[0]]
        # = [1, 0, 1, 1] for coeffs = [1, 1, 0, 1]
        assert C[3, 0] == 1  # coeffs[3]
        assert C[3, 1] == 1  # coeffs[2]
        assert C[3, 2] == 0  # coeffs[1]
        assert C[3, 3] == 1  # coeffs[0]

    def test_3bit_lfsr_gf2(self):
        """Test building state update matrix for 3-bit LFSR over GF(2)."""
        coeffs = [1, 1, 0]
        C, CS = build_state_update_matrix(coeffs, 2)

        assert C.dimensions() == (3, 3)
        assert CS.dimensions() == (3, 3)

        # Verify companion matrix structure
        assert C[0, 0] == 1  # coeffs[0]
        assert C[0, 1] == 0
        assert C[0, 2] == 0

        assert C[1, 0] == 0
        assert C[1, 1] == 1
        assert C[1, 2] == 0

        assert C[2, 0] == 0  # coeffs[2]
        assert C[2, 1] == 1  # coeffs[1]
        assert C[2, 2] == 1  # coeffs[0]

    def test_lfsr_gf3(self):
        """Test building state update matrix over GF(3)."""
        coeffs = [1, 2, 1]
        C, CS = build_state_update_matrix(coeffs, 3)

        assert C.dimensions() == (3, 3)
        # Verify field is GF(3)
        assert C.base_ring() == GF(3)

        # Verify coefficients are in GF(3)
        assert C[2, 0] == 1  # coeffs[2]
        assert C[2, 1] == 2  # coeffs[1]
        assert C[2, 2] == 1  # coeffs[0]

    def test_state_transition(self):
        """Test that state transition works: S_i * C = S_i+1."""
        coeffs = [1, 1, 0, 1]
        C, _ = build_state_update_matrix(coeffs, 2)

        # Create initial state vector
        V = VectorSpace(GF(2), 4)
        initial_state = V([1, 0, 0, 0])

        # Compute next state
        next_state = initial_state * C

        # Verify it's a valid state vector
        assert next_state in V
        assert next_state.parent() == V

    def test_matrix_types(self):
        """Test that returned matrices have correct types."""
        coeffs = [1, 0, 1, 1]
        C, CS = build_state_update_matrix(coeffs, 2)

        # C should be over GF(2)
        assert C.base_ring() == GF(2)

        # CS should be symbolic
        assert CS.base_ring() == SR


class TestComputeMatrixOrder:
    """Tests for compute_matrix_order function."""

    def test_matrix_order_simple(self):
        """Test computing order of a simple matrix."""
        # Create a 2x2 identity matrix (order should be 1)
        M = MatrixSpace(GF(2), 2, 2)
        I = M.identity_matrix()
        C = I  # Matrix is identity, so order is 1

        order = compute_matrix_order(C, I, 4, None)
        assert order == 1

    def test_matrix_order_4bit_lfsr(self):
        """Test computing order for a 4-bit LFSR."""
        coeffs = [1, 1, 0, 1]
        C, _ = build_state_update_matrix(coeffs, 2)

        M = MatrixSpace(GF(2), 4, 4)
        I = M.identity_matrix()
        state_space_size = 2 ** 4  # 16

        order = compute_matrix_order(C, I, state_space_size, None)
        # Order should be found and should be <= state_space_size - 1
        assert order is not None
        assert 1 <= order <= state_space_size - 1

    def test_matrix_order_with_output_file(self, tmp_path):
        """Test computing order with output file."""
        coeffs = [1, 1, 0]
        C, _ = build_state_update_matrix(coeffs, 2)

        M = MatrixSpace(GF(2), 3, 3)
        I = M.identity_matrix()
        state_space_size = 2 ** 3  # 8

        output_file = tmp_path / "test_output.txt"
        with open(output_file, "w") as f:
            order = compute_matrix_order(C, I, state_space_size, f)

        assert order is not None
        assert output_file.exists()
        assert output_file.read_text().find("O(C)") != -1

    def test_matrix_order_gf3(self):
        """Test computing order over GF(3)."""
        coeffs = [1, 2, 1]
        C, _ = build_state_update_matrix(coeffs, 3)

        M = MatrixSpace(GF(3), 3, 3)
        I = M.identity_matrix()
        state_space_size = 3 ** 3  # 27

        order = compute_matrix_order(C, I, state_space_size, None)
        assert order is not None
        assert 1 <= order <= state_space_size - 1

    def test_matrix_order_maximum_search(self):
        """Test that order search respects maximum bound."""
        # Create a matrix that will have a large order
        coeffs = [1, 0, 0, 1, 0]  # 5-bit LFSR
        C, _ = build_state_update_matrix(coeffs, 2)

        M = MatrixSpace(GF(2), 5, 5)
        I = M.identity_matrix()
        state_space_size = 2 ** 5  # 32

        order = compute_matrix_order(C, I, state_space_size, None)
        # Order should be found within the search space
        assert order is not None
        assert order <= state_space_size - 1

