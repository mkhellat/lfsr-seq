#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for LFSR analysis functions, including cycle detection algorithms.
"""

import pytest

# Import SageMath - will be skipped if not available via conftest
try:
    from sage.all import *
except ImportError:
    pytest.skip("SageMath not available", allow_module_level=True)

from lfsr.analysis import (
    _find_period_floyd,
    _find_period_enumeration,
    _find_period,
    _find_sequence_cycle,
    _find_sequence_cycle_floyd,
    _find_sequence_cycle_enumeration,
)
from lfsr.core import build_state_update_matrix


class TestPeriodOnlyFunctions:
    """Tests for period-only functions (--period-only mode)."""

    def test_find_period_floyd_simple(self):
        """Test Floyd period finding on simple LFSR."""
        coeffs = [1, 1, 0, 1]
        C, CS = build_state_update_matrix(coeffs, 2)
        V = VectorSpace(GF(2), 4)
        
        # Test with first non-zero state
        for state in V:
            if state != V.zero():
                period = _find_period_floyd(state, C)
                assert period > 0
                assert isinstance(period, (int, Integer))
                break

    def test_find_period_enumeration_simple(self):
        """Test enumeration period finding on simple LFSR."""
        coeffs = [1, 1, 0, 1]
        C, CS = build_state_update_matrix(coeffs, 2)
        V = VectorSpace(GF(2), 4)
        
        # Test with first non-zero state
        for state in V:
            if state != V.zero():
                period = _find_period_enumeration(state, C)
                assert period > 0
                assert isinstance(period, (int, Integer))
                break

    def test_find_period_floyd_vs_enumeration(self):
        """Test that Floyd and enumeration return same period."""
        coeffs = [1, 1, 0, 1]
        C, CS = build_state_update_matrix(coeffs, 2)
        V = VectorSpace(GF(2), 4)
        
        # Test with multiple states
        tested = 0
        for state in V:
            if state != V.zero() and tested < 5:
                floyd_period = _find_period_floyd(state, C)
                enum_period = _find_period_enumeration(state, C)
                assert floyd_period == enum_period, f"Period mismatch for state {state}: Floyd={floyd_period}, Enum={enum_period}"
                tested += 1

    def test_find_period_dispatcher(self):
        """Test _find_period dispatcher function."""
        coeffs = [1, 1, 0, 1]
        C, CS = build_state_update_matrix(coeffs, 2)
        V = VectorSpace(GF(2), 4)
        
        for state in V:
            if state != V.zero():
                # Test with different algorithms
                period_floyd = _find_period(state, C, algorithm="floyd")
                period_enum = _find_period(state, C, algorithm="enumeration")
                period_auto = _find_period(state, C, algorithm="auto")
                
                # All should return same period
                assert period_floyd == period_enum == period_auto
                break

    def test_find_period_zero_state(self):
        """Test period finding for zero state (should be period 1)."""
        coeffs = [1, 1, 0, 1]
        C, CS = build_state_update_matrix(coeffs, 2)
        V = VectorSpace(GF(2), 4)
        zero_state = V.zero()
        
        # Zero state should have period 1 (fixed point)
        floyd_period = _find_period_floyd(zero_state, C)
        enum_period = _find_period_enumeration(zero_state, C)
        
        assert floyd_period == 1
        assert enum_period == 1


class TestPeriodOnlyMode:
    """Tests for period-only mode in _find_sequence_cycle."""

    def test_period_only_mode_returns_empty_sequence(self):
        """Test that period_only=True returns empty sequence list."""
        coeffs = [1, 1, 0, 1]
        C, CS = build_state_update_matrix(coeffs, 2)
        V = VectorSpace(GF(2), 4)
        visited_set = set()
        
        for state in V:
            if state != V.zero():
                seq_lst, period = _find_sequence_cycle(
                    state, C, visited_set, algorithm="enumeration", period_only=True
                )
                assert seq_lst == []
                assert period > 0
                break

    def test_period_only_mode_floyd(self):
        """Test period-only mode with Floyd algorithm."""
        coeffs = [1, 1, 0, 1]
        C, CS = build_state_update_matrix(coeffs, 2)
        V = VectorSpace(GF(2), 4)
        visited_set = set()
        
        for state in V:
            if state != V.zero():
                seq_lst, period = _find_sequence_cycle(
                    state, C, visited_set, algorithm="floyd", period_only=True
                )
                assert seq_lst == []
                assert period > 0
                break

    def test_period_only_vs_full_mode_same_period(self):
        """Test that period-only and full mode return same period."""
        coeffs = [1, 1, 0, 1]
        C, CS = build_state_update_matrix(coeffs, 2)
        V = VectorSpace(GF(2), 4)
        
        for state in V:
            if state != V.zero():
                visited_set1 = set()
                visited_set2 = set()
                
                # Period-only mode
                seq1, period1 = _find_sequence_cycle(
                    state, C, visited_set1, algorithm="enumeration", period_only=True
                )
                
                # Full mode
                seq2, period2 = _find_sequence_cycle(
                    state, C, visited_set2, algorithm="enumeration", period_only=False
                )
                
                assert period1 == period2, f"Period mismatch: period_only={period1}, full={period2}"
                assert seq1 == []
                assert len(seq2) == period2
                break


class TestAlgorithmConsistency:
    """Tests to ensure algorithms return consistent results."""

    def test_all_algorithms_same_period(self):
        """Test that all algorithms return the same period."""
        coeffs = [1, 1, 0, 1]
        C, CS = build_state_update_matrix(coeffs, 2)
        V = VectorSpace(GF(2), 4)
        visited_set = set()
        
        for state in V:
            if state != V.zero():
                # Period-only functions
                period_floyd_po = _find_period_floyd(state, C)
                period_enum_po = _find_period_enumeration(state, C)
                
                # Full sequence functions
                visited_set1 = set()
                visited_set2 = set()
                seq1, period_floyd_full = _find_sequence_cycle_floyd(state, C, visited_set1)
                seq2, period_enum_full = _find_sequence_cycle_enumeration(state, C, visited_set2)
                
                # Period-only mode
                visited_set3 = set()
                visited_set4 = set()
                _, period_floyd_po_mode = _find_sequence_cycle(state, C, visited_set3, algorithm="floyd", period_only=True)
                _, period_enum_po_mode = _find_sequence_cycle(state, C, visited_set4, algorithm="enumeration", period_only=True)
                
                # All should match
                periods = [
                    period_floyd_po,
                    period_enum_po,
                    period_floyd_full,
                    period_enum_full,
                    period_floyd_po_mode,
                    period_enum_po_mode,
                ]
                
                assert len(set(periods)) == 1, f"Period mismatch: {periods} for state {state}"
                break
